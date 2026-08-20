"""
Recolha do cabaz essencial da DECO PROteste.

Porque é que isto é um script e não uma chamada da aplicação
------------------------------------------------------------
A DECO PROteste não tem API. O artigo que publica semanalmente o preço do
cabaz (63 bens alimentares essenciais, composição fixa) embute os gráficos
como infografias Infogram, e cada infografia expõe os seus próprios dados
numa variável JavaScript (`window.infographicData`) quando se pede
diretamente a página do embed. Não é um mecanismo documentado nem estável:
é o que existe.

A recolha é por isso um passo explícito, como a do Observatório GPP
(`recolher_observatorio.py`), que escreve ficheiros versionados e deixa a
aplicação limitar-se a lê-los.

Executar:  python scripts/recolher_deco.py
Escreve:   dados/deco_cabaz.csv, dados/deco_top10.csv e dados/deco_meta.json

Fragilidade desta fonte, para quem mantém o script
----------------------------------------------------
- Os identificadores dos embeds Infogram (UUID após "infogram_0_") não são
  fixos: descobrem-se a cada execução, por regex sobre o HTML do artigo,
  fazendo corresponder o título de cada infografia ("CABAZ ALIMENTAR DESDE
  2022", "TOP 10 AUMENTO SEMANAL", ...) às séries que interessam. Se a DECO
  mudar esses títulos, a recolha falha, visivelmente, e não em silêncio.
- O último ponto da série principal fica por vezes sem valor no gráfico
  (publicado no texto do artigo antes de entrar na infografia). O script
  tenta completá-lo com uma expressão regular sobre a frase "para X euros"
  do artigo; se não conseguir, descarta esse ponto em vez de escrever um
  valor incerto, e regista a falha em `deco_meta.json`.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ARTIGO = ("https://www.deco.proteste.pt/familia-consumo/supermercado/"
          "noticias/precos-estao-aumentar-alimentos")
CABECALHOS = {
    "User-Agent": "SGGov-UPE-CabazAlimentar/1.0 (analise estatistica; contacto via SGGov)",
}
TEMPO_LIMITE = 60

RAIZ = Path(__file__).resolve().parent.parent
DEST_SERIE = RAIZ / "dados" / "deco_cabaz.csv"
DEST_TOP10 = RAIZ / "dados" / "deco_top10.csv"
META = RAIZ / "dados" / "deco_meta.json"

# Correspondência entre o que aparece no atributo `title` de cada embed e a
# chave interna da tabela. Comparação sempre em maiúsculas.
MARCA_SERIE = "CABAZ ALIMENTAR DESDE"
MARCAS_TOP10 = {
    "desde_2022": "TOP 10 AUMENTO DESDE 2022",
    "desde_janeiro": "TOP 10 AUMENTO DESDE JANEIRO",
    "semanal": "TOP 10 AUMENTO SEMANAL",
}


def _sessao() -> requests.Session:
    s = requests.Session()
    s.headers.update(CABECALHOS)
    return s


def _infographic_data(embed_id: str, s: requests.Session) -> dict:
    resp = s.get(f"https://e.infogram.com/{embed_id}", timeout=TEMPO_LIMITE)
    resp.raise_for_status()
    m = re.search(r"window\.infographicData\s*=\s*(\{.*?\});", resp.text, re.S)
    if not m:
        raise ValueError("sem window.infographicData na página do embed")
    return json.loads(m.group(1))


def _folha_do_grafico(dado: dict) -> list:
    """A primeira folha de dados do único elemento CHART do embed."""
    entidades = dado["elements"]["content"]["content"]["entities"]
    for v in entidades.values():
        if isinstance(v, dict) and v.get("type") == "CHART":
            folhas = v["props"]["chartData"]["data"]
            if folhas:
                return folhas[0]
    raise ValueError("sem elemento CHART no embed")


def descobrir_embeds(s: requests.Session) -> tuple[str, list[tuple[str, str]]]:
    resp = s.get(ARTIGO, timeout=TEMPO_LIMITE)
    resp.raise_for_status()
    html = resp.text
    achados = re.findall(r'<script id="infogram_0_([a-f0-9-]+)"\s+title="([^"]+)"', html)
    if not achados:
        raise SystemExit("Não foi encontrado nenhum embed Infogram — a página mudou de estrutura.")
    return html, achados


def _numero_pt(txt: str | None) -> float | None:
    """'187,70  ' -> 187.70. Sem separador de milhares: valores sempre < 1000."""
    if not txt:
        return None
    limpo = txt.strip().replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def _preco_txt(txt: str | None) -> tuple[float | None, str]:
    """'9,98 €/kg' -> (9.98, '€/kg'); '1,59 €' -> (1.59, '€')."""
    if not txt:
        return None, ""
    m = re.match(r"\s*([\d.,]+)\s*(€(?:/kg)?)", txt)
    if not m:
        return None, ""
    return _numero_pt(m.group(1)), m.group(2)


def main() -> int:
    s = _sessao()
    print("A obter o artigo da DECO PROteste…")
    html, embeds = descobrir_embeds(s)

    falhas: list[dict] = []
    serie_df = pd.DataFrame()
    titulo_grafico = None
    tabelas: dict[str, list[dict]] = {}

    for embed_id, titulo in embeds:
        titulo_maiusc = titulo.upper()
        alvo = None
        if MARCA_SERIE in titulo_maiusc:
            alvo = "serie"
        else:
            for chave, marca in MARCAS_TOP10.items():
                if marca in titulo_maiusc:
                    alvo = chave
                    break
        if alvo is None:
            continue

        try:
            dado = _infographic_data(embed_id, s)
            folha = _folha_do_grafico(dado)
        except Exception as exc:                                  # noqa: BLE001
            falhas.append({"embed": titulo, "erro": str(exc)})
            print(f"  ! {titulo}: {exc}", file=sys.stderr)
            continue

        if alvo == "serie":
            titulo_grafico = dado.get("title")
            registos = []
            for linha in folha[1:]:
                data_cel = linha[0] if len(linha) > 0 else None
                valor_cel = linha[1] if len(linha) > 1 else None
                data_txt = data_cel.get("value") if data_cel else None
                valor_txt = valor_cel.get("value") if valor_cel else None
                if not data_txt:
                    continue
                registos.append({"data_txt": data_txt, "valor": _numero_pt(valor_txt)})
            serie_df = pd.DataFrame(registos)
            print(f"  [série] {titulo}: {len(serie_df)} pontos")
        else:
            registos = []
            for linha in folha[1:]:
                celulas = [c.get("value") if c else None for c in linha]
                if not celulas or not celulas[0]:
                    continue
                preco_valor, preco_unidade = _preco_txt(celulas[1] if len(celulas) > 1 else None)
                aumento_valor, _ = _preco_txt(celulas[2] if len(celulas) > 2 else None)
                pct_txt = celulas[3] if len(celulas) > 3 else None
                pct_valor = _numero_pt(re.sub(r"%", "", pct_txt)) if pct_txt else None
                registos.append({
                    "tabela": alvo,
                    "produto": celulas[0].strip(),
                    "preco_atual": preco_valor,
                    "unidade_preco": preco_unidade,
                    "aumento_valor": aumento_valor,
                    "aumento_pct": pct_valor,
                })
            tabelas[alvo] = registos
            print(f"  [{alvo}] {titulo}: {len(registos)} produtos")

    if serie_df.empty:
        raise SystemExit("Não foi possível obter a série do gráfico principal — nada foi escrito.")

    serie_df["data"] = pd.to_datetime(serie_df["data_txt"], format="%d/%m/%Y", errors="coerce")
    serie_df = serie_df.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)

    # O último ponto do embed vem por vezes sem valor: o gráfico ainda não foi
    # atualizado com o número que já está no texto do artigo. Tenta-se
    # completar a partir da frase "...para X euros" antes de descartar.
    if pd.isna(serie_df["valor"].iloc[-1]):
        m = re.search(r"para\s*<strong>\s*([\d.,]+)\s*euros</strong>", html, re.I)
        completado = False
        if m:
            valor = _numero_pt(m.group(1))
            if valor is not None:
                serie_df.loc[serie_df.index[-1], "valor"] = valor
                completado = True
        if not completado:
            falhas.append({"embed": "série principal",
                           "erro": "último ponto sem valor no gráfico e sem "
                                   "correspondência no texto do artigo — descartado"})
            serie_df = serie_df.iloc[:-1]

    serie_final = serie_df[["data", "valor"]].dropna().reset_index(drop=True)
    if serie_final.empty:
        raise SystemExit("Série ficou vazia depois de limpar valores em falta.")

    DEST_SERIE.parent.mkdir(parents=True, exist_ok=True)
    serie_final.to_csv(DEST_SERIE, index=False, encoding="utf-8")

    linhas_top10 = [r for regs in tabelas.values() for r in regs]
    top10_df = pd.DataFrame(linhas_top10)
    if not top10_df.empty:
        top10_df.to_csv(DEST_TOP10, index=False, encoding="utf-8")

    ultimo = serie_final.iloc[-1]
    meta = {
        "extraido_em": date.today().isoformat(),
        "fonte": "DECO PROteste, cabaz essencial de 63 bens alimentares",
        "endereco": ARTIGO,
        "titulo_grafico": titulo_grafico,
        "data_referencia": ultimo["data"].date().isoformat(),
        "valor_atual": float(ultimo["valor"]),
        "primeiro_periodo": serie_final["data"].min().date().isoformat(),
        "ultimo_periodo": serie_final["data"].max().date().isoformat(),
        "observacoes": int(len(serie_final)),
        "tabelas_top10": sorted(tabelas.keys()),
        "falhas": falhas,
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nSérie: {len(serie_final)} pontos · "
          f"{meta['primeiro_periodo']} a {meta['ultimo_periodo']}")
    print(f"Valor atual: {meta['valor_atual']:.2f} € ({meta['data_referencia']})")
    print(f"Top 10: {len(top10_df)} linhas em {len(tabelas)} tabelas")
    print(f"escrito: {DEST_SERIE}")
    if not top10_df.empty:
        print(f"escrito: {DEST_TOP10}")
    if falhas:
        print(f"ATENÇÃO: {len(falhas)} falhas — ver {META.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
