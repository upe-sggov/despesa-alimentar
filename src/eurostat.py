"""
Acesso aos dados oficiais do Eurostat.

Porque é que isto corre no servidor e não no navegador
------------------------------------------------------
Uma página HTML aberta no computador não consegue ler dados de outro domínio:
o navegador bloqueia-o por política de mesma origem (*same-origin policy*), e
as redes institucionais reforçam essa restrição. Ao correr em Python do lado do
servidor, essa limitação não existe — os pedidos são feitos por HTTP normal.

São usadas duas vias independentes, por ordem de preferência:

1. **SDMX 2.1** — o filtro segue no próprio caminho do endereço
   (`.../prc_hicp_manr/M.RCH_A.CP011.PT`), pelo que a seleção é
   obrigatoriamente feita no servidor do Eurostat. Devolve SDMX-CSV.
2. **API Statistics** — filtros por parâmetro, resposta em JSON-stat.

Ambas são públicas, sem chave nem registo.
"""

from __future__ import annotations

import io
from typing import Iterable

import pandas as pd
import requests

SDMX = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
STATS = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"

TEMPO_LIMITE = 45
CABECALHOS = {"User-Agent": "SGGov-UPE-CabazAlimentar/1.0 (analise estatistica)"}

COLUNAS = ["unit", "coicop", "geo", "time", "valor"]


class ErroEurostat(RuntimeError):
    """Falha na obtenção de dados do Eurostat."""


# --------------------------------------------------------------------------
# Via 1 — SDMX 2.1 (chave no caminho)
# --------------------------------------------------------------------------
# Registo dos endereços efetivamente usados, para rastreabilidade. É lido pela
# aplicação e apresentado no separador Metodologia.
ENDERECOS: list[tuple[str, str]] = []


def _via_sdmx(dataset: str, chave: str, inicio: str | None = None,
              extra: str | None = None) -> pd.DataFrame:
    url = f"{SDMX}{dataset}/{chave}"
    params = {"format": "SDMX-CSV"}
    if inicio:
        params["startPeriod"] = inicio
    _completo = url + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    ENDERECOS.append((dataset, _completo))

    resp = requests.get(url, params=params, timeout=TEMPO_LIMITE, headers=CABECALHOS)
    resp.raise_for_status()

    bruto = pd.read_csv(io.StringIO(resp.text))
    if "OBS_VALUE" not in bruto.columns:
        raise ErroEurostat(f"{dataset}: resposta SDMX sem coluna OBS_VALUE.")

    df = pd.DataFrame({
        "unit": bruto.get("unit", pd.Series([""] * len(bruto))),
        "coicop": bruto.get("coicop", pd.Series([""] * len(bruto))),
        "geo": bruto.get("geo", pd.Series([""] * len(bruto))),
        "time": bruto["TIME_PERIOD"].astype(str),
        "valor": pd.to_numeric(bruto["OBS_VALUE"], errors="coerce"),
    })
    if extra:
        if extra not in bruto.columns:
            # Sem esta guarda, várias séries colapsavam numa só coluna, sem
            # forma de as distinguir — erro silencioso e difícil de detetar.
            raise ErroEurostat(
                f"{dataset}: dimensão «{extra}» ausente da resposta SDMX "
                f"(colunas: {', '.join(bruto.columns)}).")
        df[extra] = bruto[extra]
    return df.dropna(subset=["valor"]).reset_index(drop=True)


# --------------------------------------------------------------------------
# Via 2 — API Statistics (JSON-stat)
# --------------------------------------------------------------------------
def _descodifica_jsonstat(js: dict, extra: str | None = None) -> pd.DataFrame:
    """
    JSON-stat 2.0 guarda os valores num vetor achatado. O índice de cada
    observação decompõe-se nas coordenadas das dimensões em ordem *row-major*
    (a última dimensão varia mais depressa).
    """
    ids = js["id"]
    tamanhos = js["size"]

    categorias = []
    for dim in ids:
        indice = js["dimension"][dim]["category"]["index"]
        if isinstance(indice, list):
            categorias.append(list(indice))
        else:
            categorias.append([k for k, _ in sorted(indice.items(), key=lambda x: x[1])])

    valores = js.get("value", {})
    if isinstance(valores, list):
        pares = ((i, v) for i, v in enumerate(valores) if v is not None)
    else:
        pares = ((int(k), v) for k, v in valores.items() if v is not None)

    linhas = []
    for pos, valor in pares:
        resto, coords = pos, {}
        for d in range(len(tamanhos) - 1, -1, -1):
            coords[ids[d]] = categorias[d][resto % tamanhos[d]]
            resto //= tamanhos[d]
        coords["valor"] = valor
        linhas.append(coords)

    colunas = COLUNAS + ([extra] if extra else [])
    if not linhas:
        return pd.DataFrame(columns=colunas)

    df = pd.DataFrame(linhas)
    for col in ("unit", "coicop", "geo"):
        if col not in df.columns:
            df[col] = ""
    df["time"] = df.get("time", "").astype(str)
    if extra and extra not in df.columns:
        raise ErroEurostat(
            f"dimensão «{extra}» ausente da resposta JSON-stat "
            f"(dimensões: {', '.join(ids)}).")
    return df[colunas]


def _via_stats(dataset: str, filtros: dict, extra: str | None = None) -> pd.DataFrame:
    params: list[tuple[str, str]] = [("format", "JSON"), ("lang", "EN")]
    for chave, valor in filtros.items():
        if valor is None:
            continue
        if isinstance(valor, (list, tuple, set)):
            params.extend((chave, str(v)) for v in valor)
        else:
            params.append((chave, str(valor)))

    resp = requests.get(STATS + dataset, params=params,
                        timeout=TEMPO_LIMITE, headers=CABECALHOS)
    resp.raise_for_status()
    return _descodifica_jsonstat(resp.json(), extra)


# --------------------------------------------------------------------------
# Interface pública
# --------------------------------------------------------------------------
def obter(dataset: str, chave: str, filtros: dict,
          inicio: str | None = None,
          extra: str | None = None) -> tuple[pd.DataFrame, str]:
    """
    Devolve (dados, via_utilizada). Tenta SDMX; se falhar, a API Statistics.
    Levanta ErroEurostat se ambas falharem.

    `extra` preserva uma dimensão adicional para lá de `unit`, `coicop` e `geo`.
    Sem isso, um conjunto com uma dimensão própria — como o nível de pobreza em
    `ilc_mdes03` — devolveria várias séries empilhadas e indistinguíveis.
    """
    erros = []
    try:
        df = _via_sdmx(dataset, chave, inicio, extra)
        if not df.empty:
            return df, "SDMX 2.1"
        erros.append("SDMX devolveu resposta vazia")
    except Exception as exc:                              # noqa: BLE001
        erros.append(f"SDMX: {exc}")

    try:
        df = _via_stats(dataset, filtros, extra)
        if not df.empty:
            return df, "API Statistics"
        erros.append("API Statistics devolveu resposta vazia")
    except Exception as exc:                              # noqa: BLE001
        erros.append(f"API Statistics: {exc}")

    raise ErroEurostat(f"{dataset} — " + " | ".join(erros))


def ponderadores(codigos: Iterable[str]) -> tuple[pd.DataFrame, str]:
    """Ponderadores oficiais do IHPC português, por classe (por mil)."""
    codigos = list(codigos)
    return obter(
        "prc_hicp_inw",
        f"A..{'+'.join(codigos)}.PT",
        {"freq": "A", "coicop": codigos, "geo": "PT"},
    )


def indice_precos(coicop: str, desde: str) -> tuple[pd.DataFrame, str]:
    """Índice de preços mensal (base 2015 = 100 quando disponível)."""
    return obter(
        "prc_hicp_midx",
        f"M..{coicop}.PT",
        {"freq": "M", "coicop": coicop, "geo": "PT", "sinceTimePeriod": desde},
        inicio=desde,
    )


def indice_classes(codigos: Iterable[str], desde: str) -> tuple[pd.DataFrame, str]:
    """
    Índice de preços mensal por classe COICOP — a matéria-prima do Törnqvist.

    Difere de `indice_precos` apenas por pedir várias classes de uma vez, em vez
    do agregado. É preciso o índice em nível, e não a variação homóloga, porque
    um índice superlativo encadeia relativos de preço entre dois momentos.
    """
    codigos = list(codigos)
    return obter(
        "prc_hicp_midx",
        f"M..{'+'.join(codigos)}.PT",
        {"freq": "M", "coicop": codigos, "geo": "PT", "sinceTimePeriod": desde},
        inicio=desde,
    )


def variacoes(coicops: Iterable[str], geos: Iterable[str],
              desde: str) -> tuple[pd.DataFrame, str]:
    """Variação homóloga mensal (%), por classe e por país."""
    coicops, geos = list(coicops), list(geos)
    return obter(
        "prc_hicp_manr",
        f"M.RCH_A.{'+'.join(coicops)}.{'+'.join(geos)}",
        {"freq": "M", "unit": "RCH_A", "coicop": coicops,
         "geo": geos, "sinceTimePeriod": desde},
        inicio=desde,
    )


def despesa_alimentar(desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Despesa final das famílias em produtos alimentares (COICOP 01.1),
    a preços correntes, em milhões de euros — Contas Nacionais.

    É a âncora oficial em euros: o índice de preços dá variações, nunca níveis.
    Publicação anual, com desfasamento de cerca de dois anos.
    """
    return obter(
        "nama_10_co3_p3",
        f"A.CP_MEUR.CP011.PT",
        {"freq": "A", "unit": "CP_MEUR", "coicop": "CP011", "geo": "PT",
         "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
    )


def dimensao_agregado(desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Dimensão média do agregado familiar (n.º de pessoas), fonte EU-SILC.

    Necessária para saber a quantas pessoas corresponde a despesa média por
    agregado e para converter entre despesa por agregado e despesa por pessoa.
    """
    return obter(
        "ilc_lvph01",
        "A.AVG.TOTAL.PT",
        {"freq": "A", "geo": "PT", "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
    )


def numero_agregados(desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Número total de agregados familiares (milhares), fonte Inquérito ao Emprego (EU-LFS).

    Complementa o valor censitário: é anual, ao passo que os Censos são decenais.
    Se não estiver disponível, a aplicação recorre ao valor dos Censos.
    """
    return obter(
        "lfst_hhnhtych",
        "A.THS.TOTAL.TOTAL.PT",
        {"freq": "A", "geo": "PT", "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
    )


def privacao_alimentar(geos, desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Percentagem que não consegue pagar uma refeição com carne, frango ou peixe
    (ou equivalente vegetariano) de dois em dois dias — EU-SILC, `ilc_mdes03`.

    É o limiar mais baixo dos três indicadores de acessibilidade da aplicação:
    mede privação **severa**, quase fome. Nunca deve ser apresentado sozinho —
    ver a nota em `config.py`.

    Devolve as três populações: total, abaixo e acima do limiar de pobreza.
    """
    geos = list(geos)
    # Dimensões: freq.hhcomp.rskpovth.unit.geo.time — `rskpovth` é o risco de
    # pobreza (limiar dos 60 % da mediana), não o grupo de rendimento.
    niveis = ["TOTAL", "B_60", "A_60"]
    return obter(
        "ilc_mdes03",
        f"A.TOTAL.{'+'.join(niveis)}.PC.{'+'.join(geos)}",
        {"freq": "A", "hhcomp": "TOTAL", "rskpovth": niveis, "unit": "PC",
         "geo": geos, "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
        extra="rskpovth",
    )


# Rótulos das três populações de `ilc_mdes03`, na ordem em que devem ser lidas.
PRIVACAO_NIVEIS = {
    "TOTAL": "População total",
    "B_60": "Em risco de pobreza",
    "A_60": "Acima do limiar",
}


# Categorias analíticas candidatas para o nível de preços dos alimentos.
# A nomenclatura das PPP não coincide com a COICOP do índice de preços e a
# codificação mudou com a COICOP 2018, pelo que se tentam várias hipóteses e
# se usa a primeira que devolva dados.
PPP_CANDIDATOS_ALIMENTOS = ["A010101", "E011", "CP011", "A01", "0101"]


def nivel_precos(geos, categoria: str, desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Índice de nível de preços (EU27 = 100) — quanto custa o mesmo cabaz de bens
    em cada país, corrigido pelo câmbio. Responde à pergunta que a inflação não
    responde: *são mais caros aqui?*

    Fonte: programa de Paridades de Poder de Compra Eurostat-OCDE.
    """
    geos = list(geos)
    return obter(
        "prc_ppp_ind_1",
        f"A.PLI_EU27_2020.{categoria}.{'+'.join(geos)}",
        {"freq": "A", "na_item": "PLI_EU27_2020", "ppp_cat": categoria,
         "geo": geos, "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
    )


# O código do agregado total varia consoante a versão do conjunto.
TOTAL_CANDIDATOS = ["TOTAL", "CP00", "P31_S14", "CP_TOT"]


def despesa_total_consumo(geos, desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Despesa final total das famílias (todos os fins), por país.

    Combinada com a despesa alimentar (CP011), dá o **coeficiente de Engel**:
    a fração do consumo das famílias que vai para alimentação.

    O código do agregado total não é o mesmo em todas as versões do conjunto,
    pelo que se tentam vários e se usa o primeiro que responda.
    """
    geos = list(geos)
    ultimo = None
    for cod in TOTAL_CANDIDATOS:
        try:
            df, via = obter(
                "nama_10_co3_p3",
                f"A.CP_MEUR.{cod}.{'+'.join(geos)}",
                {"freq": "A", "unit": "CP_MEUR", "coicop": cod,
                 "geo": geos, "sinceTimePeriod": str(desde_ano)},
                inicio=str(desde_ano),
            )
            if not df.empty:
                df = df.copy()
                df["coicop"] = "TOTAL"
                return df, f"{via} (código {cod})"
        except Exception as exc:                             # noqa: BLE001
            ultimo = exc
            continue
    raise ErroEurostat(
        f"nama_10_co3_p3 — nenhum código de total respondeu "
        f"({', '.join(TOTAL_CANDIDATOS)}): {ultimo}")


def despesa_alimentar_paises(geos, desde_ano: int) -> tuple[pd.DataFrame, str]:
    """Despesa alimentar (CP011) por país — o numerador do coeficiente de Engel."""
    geos = list(geos)
    return obter(
        "nama_10_co3_p3",
        f"A.CP_MEUR.CP011.{'+'.join(geos)}",
        {"freq": "A", "unit": "CP_MEUR", "coicop": "CP011",
         "geo": geos, "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
    )


# Códigos candidatos para o salário mínimo mensal em euros.
SM_CANDIDATOS = ["S1.EUR.MW", "S1.MW.EUR", "S1.EUR.NAT"]


def salario_minimo(geos, desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Salário mínimo nacional mensal, em euros (semestral).

    **Não é o valor legal.** O Eurostat converte o mínimo nacional em
    duodécimos do total anual, para comparar países com número diferente de
    mensalidades. Em Portugal, que paga 14, o valor difundido é o legal × 14/12
    — confirmado em toda a série: 957 → 820 (2024), 1015 → 870 (2025),
    1073 → 920 (2026). Quem precisar do valor legal divide por 14/12 e
    arredonda ao euro (auditoria de 10.08.2026, A2).
    """
    geos = list(geos)
    ultimo = None
    for chave in SM_CANDIDATOS:
        try:
            df, via = obter(
                "earn_mw_cur",
                f"{chave}.{'+'.join(geos)}",
                {"currency": "EUR", "geo": geos, "sinceTimePeriod": str(desde_ano)},
                inicio=str(desde_ano),
            )
            if not df.empty:
                return df, via
        except Exception as exc:                             # noqa: BLE001
            ultimo = exc
            continue
    raise ErroEurostat(f"earn_mw_cur — nenhuma chave respondeu ({ultimo})")


# Códigos da dimensão `statinfo` do ilc_di03. Não há chaves alternativas: uma
# lista de candidatas fazia com que um código errado falhasse em silêncio e a
# aplicação seguisse sem a série de rendimento (auditoria de 10.08.2026, A1).
RENDIMENTO_INDICADORES = {"MEAN_EI": "médio", "MED_EI": "mediano"}


def rendimento(geos, desde_ano: int, indicador: str = "MEAN_EI") -> tuple[pd.DataFrame, str]:
    """
    Rendimento monetário líquido **equivalente** das famílias, em euros (EU-SILC).

    `indicador` (dimensão ``statinfo`` do ``ilc_di03``):
      - ``MEAN_EI`` — média (*mean equivalised net income*)
      - ``MED_EI`` — mediana

    «Equivalente» significa que já vem dividido pelas unidades de consumo do
    agregado, segundo a escala OCDE modificada. Multiplicando pelas unidades
    equivalentes de um agregado obtém-se o rendimento desse agregado.

    A escolha entre média e mediana não é indiferente: a despesa alimentar
    usada nesta aplicação deriva de um **agregado nacional dividido pelo número
    de agregados**, ou seja, é uma **média**. Combiná-la com um rendimento
    mediano misturaria duas medidas de tendência central diferentes e inflaria
    o rácio, porque a mediana do rendimento é inferior à média.

    A dimensão ``age`` é ``Y_GE16`` — a população com 16 ou mais anos, que é o
    universo em que o EU-SILC publica o rendimento equivalente. Não é um
    recorte etário da despesa: o rendimento equivalente é o mesmo para todos os
    membros do agregado, por construção da escala.

    Ordem das dimensões, verificada na API a 10.08.2026:
    ``freq.age.sex.statinfo.unit.geo``.
    """
    geos = list(geos)
    if indicador not in RENDIMENTO_INDICADORES:
        raise ErroEurostat(
            f"ilc_di03 — indicador «{indicador}» não existe; "
            f"os códigos válidos são {sorted(RENDIMENTO_INDICADORES)}")
    return obter(
        "ilc_di03",
        f"A.Y_GE16.T.{indicador}.EUR.{'+'.join(geos)}",
        {"freq": "A", "age": "Y_GE16", "sex": "T", "statinfo": indicador,
         "unit": "EUR", "geo": geos, "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
    )


# Casos-tipo do conjunto de remunerações líquidas anuais. O primeiro que
# responda serve de referência para o «trabalhador médio».
def salario_medio(geos, desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Remuneração média anual dos trabalhadores por conta de outrem, **bruta**.

    Calculada a partir das Contas Nacionais: massa salarial (D11, remunerações
    e salários) dividida pelo número de trabalhadores por conta de outrem. Tem
    duas vantagens sobre as séries de remunerações líquidas: os códigos são
    estáveis, e fica na **mesma base estatística** da despesa alimentar usada
    como âncora — o que evita a mistura de universos apontada em auditoria.

    É bruta: antes de imposto e contribuições do trabalhador. Comparável com o
    salário mínimo, que também é bruto; **não** comparável com o rendimento
    líquido do EU-SILC.
    """
    geos = list(geos)
    ultimo = None
    for chave_massa, chave_emprego in [
        ("A.CP_MEUR.TOTAL.D11", "A.THS_PER.TOTAL.SAL_DC"),
        ("A.CP_MEUR.TOTAL.D1", "A.THS_PER.TOTAL.SAL_DC"),
        ("A.CP_MEUR.TOTAL.D11", "A.THS_PER.TOTAL.SAL"),
    ]:
        try:
            massa, via_m = obter(
                "nama_10_a10", f"{chave_massa}.{'+'.join(geos)}",
                {"freq": "A", "unit": "CP_MEUR", "nace_r2": "TOTAL",
                 "na_item": chave_massa.split(".")[-1], "geo": geos,
                 "sinceTimePeriod": str(desde_ano)}, inicio=str(desde_ano))
            emprego, _ = obter(
                "nama_10_a10_e", f"{chave_emprego}.{'+'.join(geos)}",
                {"freq": "A", "unit": "THS_PER", "nace_r2": "TOTAL",
                 "na_item": chave_emprego.split(".")[-1], "geo": geos,
                 "sinceTimePeriod": str(desde_ano)}, inicio=str(desde_ano))
            if massa.empty or emprego.empty:
                continue

            juncao = massa.merge(emprego, on=["geo", "time"], suffixes=("_m", "_e"))
            juncao = juncao[juncao["valor_e"] > 0]
            if juncao.empty:
                continue
            # M€ -> €  ÷  (milhares de pessoas -> pessoas)
            juncao["valor"] = juncao["valor_m"] * 1e6 / (juncao["valor_e"] * 1e3)
            resultado = juncao[["geo", "time", "valor"]].copy()
            resultado["unit"] = "EUR"
            resultado["coicop"] = ""
            return resultado, f"{via_m} (D11/emprego)"
        except Exception as exc:                             # noqa: BLE001
            ultimo = exc
            continue
    raise ErroEurostat(
        f"nama_10_a10 — não foi possível calcular a remuneração média ({ultimo})")
