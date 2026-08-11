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
   (`.../prc_hicp_minr/M.RCH_A.CP011.PT`), pelo que a seleção é
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
# Dimensão de classificação — não se chama «coicop» em todos os conjuntos
# --------------------------------------------------------------------------
# Na passagem para a ECOICOP versão 2 o Eurostat renomeou a dimensão de
# classificação de `coicop` para `coicop18`. O código antigo lia-a com
# `bruto.get("coicop", "")`: com o conjunto novo isso devolveria uma **coluna
# vazia**, as nove classes colapsariam numa só no `groupby("coicop")` e não
# haveria erro nenhum a assinalá-lo (auditoria de 11.08.2026, E1).
#
# A regra passa a ser a inversa da anterior: quem precisa da classificação
# **declara-a**, e a ausência é erro. Quem não precisa passa `None` e recebe a
# coluna vazia de propósito. É a mesma doutrina da guarda do parâmetro `extra`,
# generalizada — deixou de ser um caso especial do `ilc_mdes03`.
def _coluna_classe(dataset: str, bruto, dim: str | None, via: str):
    """Extrai a dimensão de classificação e normaliza o seu nome para `coicop`."""
    if dim is None:
        return pd.Series([""] * len(bruto), index=getattr(bruto, "index", None))
    if dim not in bruto.columns:
        raise ErroEurostat(
            f"{dataset}: dimensão de classificação «{dim}» ausente da resposta {via} "
            f"(dimensões presentes: {', '.join(map(str, bruto.columns))}). "
            "Sem ela as classes colapsam numa só, em silêncio.")
    return bruto[dim]


# --------------------------------------------------------------------------
# Via 1 — SDMX 2.1 (chave no caminho)
# --------------------------------------------------------------------------
# Registo dos endereços efetivamente usados, para rastreabilidade. É lido pela
# aplicação e apresentado no separador Metodologia.
ENDERECOS: list[tuple[str, str]] = []


def _via_sdmx(dataset: str, chave: str, inicio: str | None = None,
              extra: str | None = None,
              dim_coicop: str | None = None) -> pd.DataFrame:
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
        "coicop": _coluna_classe(dataset, bruto, dim_coicop, "SDMX"),
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
def _descodifica_jsonstat(js: dict, extra: str | None = None,
                          dim_coicop: str | None = None,
                          dataset: str = "") -> pd.DataFrame:
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
    # A dimensão de classificação chama-se `coicop18` na ECOICOP versão 2.
    # Declarada, tem de existir; normaliza-se o nome para o resto da aplicação.
    df["coicop"] = _coluna_classe(dataset, df, dim_coicop, "JSON-stat")
    for col in ("unit", "geo"):
        if col not in df.columns:
            df[col] = ""
    df["time"] = df.get("time", "").astype(str)
    if extra and extra not in df.columns:
        raise ErroEurostat(
            f"dimensão «{extra}» ausente da resposta JSON-stat "
            f"(dimensões: {', '.join(ids)}).")
    return df[colunas]


def _via_stats(dataset: str, filtros: dict, extra: str | None = None,
               dim_coicop: str | None = None) -> pd.DataFrame:
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
    return _descodifica_jsonstat(resp.json(), extra, dim_coicop, dataset)


# --------------------------------------------------------------------------
# Interface pública
# --------------------------------------------------------------------------
def obter(dataset: str, chave: str, filtros: dict,
          inicio: str | None = None,
          extra: str | None = None,
          dim_coicop: str | None = None) -> tuple[pd.DataFrame, str]:
    """
    Devolve (dados, via_utilizada). Tenta SDMX; se falhar, a API Statistics.
    Levanta ErroEurostat se ambas falharem.

    `extra` preserva uma dimensão adicional para lá de `unit`, `coicop` e `geo`.
    Sem isso, um conjunto com uma dimensão própria — como o nível de pobreza em
    `ilc_mdes03` — devolveria várias séries empilhadas e indistinguíveis.

    `dim_coicop` é o nome que a dimensão de classificação tem **neste conjunto**:
    `coicop` nas Contas Nacionais, `coicop18` na ECOICOP versão 2. Quem precisa
    dela tem de a declarar; a ausência é erro, não silêncio.
    """
    erros = []
    try:
        df = _via_sdmx(dataset, chave, inicio, extra, dim_coicop)
        if not df.empty:
            return df, "SDMX 2.1"
        erros.append("SDMX devolveu resposta vazia")
    except Exception as exc:                              # noqa: BLE001
        erros.append(f"SDMX: {exc}")

    try:
        df = _via_stats(dataset, filtros, extra, dim_coicop)
        if not df.empty:
            return df, "API Statistics"
        erros.append("API Statistics devolveu resposta vazia")
    except Exception as exc:                              # noqa: BLE001
        erros.append(f"API Statistics: {exc}")

    raise ErroEurostat(f"{dataset} — " + " | ".join(erros))


# --------------------------------------------------------------------------
# IHPC — ECOICOP versão 2
# --------------------------------------------------------------------------
# O Eurostat encerrou a família ECOICOP ver.1 na passagem para a ECOICOP ver.2 e
# **inscreveu o fim da série no próprio título** dos conjuntos antigos:
#
#   prc_hicp_midx   «HICP - monthly data (index) (1996-2025)»          arquivado
#   prc_hicp_manr   «HICP - monthly data (annual rate of change) (…-2025)» arquivado
#   prc_hicp_inw    «HICP - item weights (1996-2025)»                   arquivado
#
# Os três continuavam a responder com HTTP 200 e dados bem formados — apenas
# tinham deixado de avançar. A aplicação apresentou dezembro de 2025 como
# «último mês disponível» durante sete meses, sem dar erro nenhum
# (auditoria de 11.08.2026, E1).
#
# Os conjuntos correntes:
#
#   prc_hicp_minr   índice **e** taxas de variação — substitui midx e manr
#   prc_hicp_iw     ponderadores por rubrica
#
# Três diferenças que quebram uma migração feita à letra:
#
#   1. a dimensão de classificação chama-se `coicop18`, não `coicop`;
#   2. índice e variação partilham o conjunto e distinguem-se pela `unit`, pelo
#      que a unidade **tem de ir explícita na chave** — sem isso a resposta traz
#      níveis e taxas misturados na mesma coluna;
#   3. `prc_hicp_iw` tem uma dimensão a mais, `statinfo`, com o valor `IW`.
HICP_MENSAL = "prc_hicp_minr"
HICP_PONDERADORES = "prc_hicp_iw"

# Bases do índice aceites, por ordem de preferência. Pedem-se as duas: a base
# muda de tempos a tempos e a aplicação escolhe depois a mais recente presente.
HICP_UNIDADES_INDICE = ("I25", "I15")
HICP_UNIDADE_VARIACAO = "RCH_A"

# Cobertura verificada a 11.08.2026 (Portugal): I25 vai de 1996-01 a 2026-06
# para CP011 e de 2019-01 a 2026-06 para as nove classes; os ponderadores vão
# de 1996 a 2026. As duas janelas de indexação das âncoras — o ano civil de 2022
# e a janela de recolha do IDF, fev/2022 a jan/2023 — ficam cobertas.


def ponderadores(codigos: Iterable[str]) -> tuple[pd.DataFrame, str]:
    """Ponderadores oficiais do IHPC português, por classe (por mil)."""
    codigos = list(codigos)
    return obter(
        HICP_PONDERADORES,
        f"A.{'+'.join(codigos)}.IW.PT",
        {"freq": "A", "coicop18": codigos, "statinfo": "IW", "geo": "PT"},
        dim_coicop="coicop18",
    )


def indice_precos(coicop: str, desde: str) -> tuple[pd.DataFrame, str]:
    """Índice de preços mensal (base 2025 = 100 quando disponível)."""
    return indice_classes([coicop], desde)


def indice_classes(codigos: Iterable[str], desde: str) -> tuple[pd.DataFrame, str]:
    """
    Índice de preços mensal por classe COICOP — a matéria-prima do Törnqvist.

    É preciso o índice em nível, e não a variação homóloga, porque um índice
    superlativo encadeia relativos de preço entre dois momentos. A unidade vai
    explícita na chave: no conjunto novo, omiti-la traria também as taxas de
    variação, indistinguíveis dos níveis depois de agregadas.
    """
    codigos = list(codigos)
    unidades = list(HICP_UNIDADES_INDICE)
    return obter(
        HICP_MENSAL,
        f"M.{'+'.join(unidades)}.{'+'.join(codigos)}.PT",
        {"freq": "M", "unit": unidades, "coicop18": codigos, "geo": "PT",
         "sinceTimePeriod": desde},
        inicio=desde,
        dim_coicop="coicop18",
    )


def variacoes(coicops: Iterable[str], geos: Iterable[str],
              desde: str) -> tuple[pd.DataFrame, str]:
    """Variação homóloga mensal (%), por classe e por país."""
    coicops, geos = list(coicops), list(geos)
    return obter(
        HICP_MENSAL,
        f"M.{HICP_UNIDADE_VARIACAO}.{'+'.join(coicops)}.{'+'.join(geos)}",
        {"freq": "M", "unit": HICP_UNIDADE_VARIACAO, "coicop18": coicops,
         "geo": geos, "sinceTimePeriod": desde},
        inicio=desde,
        dim_coicop="coicop18",
    )


# --------------------------------------------------------------------------
# Contas Nacionais — COICOP 2018
# --------------------------------------------------------------------------
# Segunda ocorrência do mesmo defeito do E1, encontrada pela verificação de
# frescura criada no E3 — que é a melhor demonstração de que a verificação
# fazia falta. O catálogo do Eurostat distingue-os pelo título:
#
#   nama_10_co3_p3  «Household final consumption expenditure by purpose
#                    (COICOP 1999)»   — parado em 2022 para todos os países
#   nama_10_cp18    «Household final consumption expenditure by purpose
#                    (COICOP 2018)»   — atualizado, série até 2024/2025
#
# O conjunto antigo continuava a responder. Todos os outros conjuntos anuais da
# aplicação estavam em 2025; só este ficara em 2022, o que não era desfasamento
# normal de publicação — era uma série que tinha parado
# (auditoria de 11.08.2026, E16).
#
# A dimensão volta a chamar-se `coicop18`, como no IHPC.
CONTAS_NACIONAIS = "nama_10_cp18"


def despesa_alimentar(desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Despesa final das famílias em produtos alimentares (COICOP 01.1),
    a preços correntes, em milhões de euros — Contas Nacionais.

    É a âncora oficial em euros: o índice de preços dá variações, nunca níveis.
    Publicação anual, com cerca de ano e meio de desfasamento.
    """
    return obter(
        CONTAS_NACIONAIS,
        f"A.CP_MEUR.CP011.PT",
        {"freq": "A", "unit": "CP_MEUR", "coicop18": "CP011", "geo": "PT",
         "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
        dim_coicop="coicop18",
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

    Dimensões: ``freq.agechild.n_child.phhcomp.unit.geo``, unidade ``THS_HH``
    (milhares de agregados). A chave anterior — ``A.THS.TOTAL.TOTAL.PT`` — não
    correspondia a esta estrutura: a via SDMX falhava e a alternativa devolvia
    uma fatia arbitrária de 443,5 mil agregados, um décimo do valor real. Só
    não contaminou a aplicação porque a verificação de plausibilidade em
    `app.py` a rejeitava — o que, por sua vez, tornava esta função inútil
    (auditoria de 10.08.2026, B1).

    **Não é o mesmo universo dos Censos.** O EU-LFS é um inquérito por amostra e
    exclui os alojamentos coletivos; lê sistematicamente abaixo do recenseamento
    exaustivo. Em 2021, ano em que ambos existem: 3 939,9 mil contra 4 149 096
    dos Censos, menos 5,0 %. Trocar de fonte muda o nível, mesmo no mesmo ano.
    """
    return obter(
        "lfst_hhnhtych",
        "A.TOTAL.TOTAL.TOTAL.THS_HH.PT",
        {"freq": "A", "agechild": "TOTAL", "n_child": "TOTAL", "phhcomp": "TOTAL",
         "unit": "THS_HH", "geo": "PT", "sinceTimePeriod": str(desde_ano)},
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
#
# A nomenclatura das PPP não coincide com a COICOP do índice de preços, pelo
# que se tenta a categoria preferida e, se falhar, a reserva. **Todas as
# candidatas têm de ser alimentares.** A lista anterior incluía `E011` (consumo
# final das famílias, 86,6) e `A01` (consumo individual efetivo, 85,3), que não
# são alimentação: bastava a primeira falhar para a aplicação mostrar o nível
# de preços de *todo* o consumo sob o título «nível de preços dos alimentos», e
# a conclusão invertia-se de «1,4 % acima da UE-27» para «13,4 % abaixo».
# Continha ainda `CP011` e `0101`, que não existem no conjunto.
# Auditoria de 10.08.2026, B3.
#
# Rótulos e valores confirmados na API a 10.08.2026 (Portugal, 2025):
#   A010101  Food                              101,4
#   A0101    Food and non-alcoholic beverages  102,0
PPP_CATEGORIAS_ALIMENTOS = {
    "A010101": "Alimentação",
    "A0101": "Alimentação e bebidas não alcoólicas",
}

# A reserva é mais lata do que a categoria preferida: inclui águas, sumos,
# cafés e chás. Quem a usar tem de o dizer no rótulo do gráfico.
PPP_CATEGORIA_PREFERIDA = "A010101"


def nivel_precos(geos, categoria: str, desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Índice de nível de preços (EU27 = 100) — quanto custa o mesmo cabaz de bens
    em cada país, corrigido pelo câmbio. Responde à pergunta que a inflação não
    responde: *são mais caros aqui?*

    Fonte: programa de Paridades de Poder de Compra Eurostat-OCDE.

    `categoria` deve pertencer a `PPP_CATEGORIAS_ALIMENTOS` quando o resultado
    for apresentado como «nível de preços dos alimentos». O conjunto tem 64
    categorias, quase todas não alimentares, e nada na resposta assinala a
    diferença — o valor devolvido tem sempre o mesmo aspeto.
    """
    geos = list(geos)
    return obter(
        "prc_ppp_ind_1",
        f"A.PLI_EU27_2020.{categoria}.{'+'.join(geos)}",
        {"freq": "A", "na_item": "PLI_EU27_2020", "ppp_cat": categoria,
         "geo": geos, "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
    )


# Código do agregado de todos os fins no `nama_10_cp18`. Era uma lista de
# candidatos — `TOTAL`, `CP00`, `P31_S14`, `CP_TOT` — e usava-se o primeiro que
# respondesse, sem que o código efetivamente obtido chegasse a lado nenhum. Um
# só, declarado, verificado na API e nomeado na interface: é a doutrina que o B3
# fixou para as categorias das PPP e que aqui não tinha sido aplicada
# (auditoria de 11.08.2026, E7).
TOTAL_CONSUMO = "TOTAL"


def despesa_total_consumo(geos, desde_ano: int) -> tuple[pd.DataFrame, str]:
    """
    Despesa final total das famílias (todos os fins), por país.

    Combinada com a despesa alimentar (CP011), dá o **coeficiente de Engel**:
    a fração do consumo das famílias que vai para alimentação.
    """
    geos = list(geos)
    df, via = obter(
        CONTAS_NACIONAIS,
        f"A.CP_MEUR.{TOTAL_CONSUMO}.{'+'.join(geos)}",
        {"freq": "A", "unit": "CP_MEUR", "coicop18": TOTAL_CONSUMO,
         "geo": geos, "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
        dim_coicop="coicop18",
    )
    df = df.copy()
    df["coicop"] = "TOTAL"
    return df, f"{via} (código {TOTAL_CONSUMO})"


def despesa_alimentar_paises(geos, desde_ano: int) -> tuple[pd.DataFrame, str]:
    """Despesa alimentar (CP011) por país — o numerador do coeficiente de Engel."""
    geos = list(geos)
    return obter(
        CONTAS_NACIONAIS,
        f"A.CP_MEUR.CP011.{'+'.join(geos)}",
        {"freq": "A", "unit": "CP_MEUR", "coicop18": "CP011",
         "geo": geos, "sinceTimePeriod": str(desde_ano)},
        inicio=str(desde_ano),
        dim_coicop="coicop18",
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
