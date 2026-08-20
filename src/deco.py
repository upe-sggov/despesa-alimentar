"""
Cabaz essencial da DECO PROteste, referência externa de preços.

**Não é o indicador que esta aplicação calcula.** A DECO soma o preço
absoluto de uma lista fixa de 63 produtos, sem ponderação pelo consumo real
e sem cobrir o comércio tradicional. A "despesa alimentar", que é o que os
outros separadores medem, reparte a despesa efetiva das famílias com base no
índice de preços do INE/Eurostat. Ver a comparação dos dois conceitos no
separador Metodologia.

Os dados não vêm em direto: são recolhidos por `scripts/recolher_deco.py` e
lidos aqui de `dados/deco_cabaz.csv` e `dados/deco_top10.csv`. A razão está
documentada no script — a DECO não tem API pública.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
FICHEIRO_SERIE = RAIZ / "dados" / "deco_cabaz.csv"
FICHEIRO_TOP10 = RAIZ / "dados" / "deco_top10.csv"
FICHEIRO_META = RAIZ / "dados" / "deco_meta.json"


def carregar() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Devolve (série do cabaz, tabelas top 10, metadados). Vazios se não houver recolha."""
    serie = pd.DataFrame()
    if FICHEIRO_SERIE.exists():
        serie = pd.read_csv(FICHEIRO_SERIE)
        serie["data"] = pd.to_datetime(serie["data"], errors="coerce")
        serie = serie.dropna(subset=["data", "valor"]).sort_values("data").reset_index(drop=True)

    top10 = pd.DataFrame()
    if FICHEIRO_TOP10.exists():
        top10 = pd.read_csv(FICHEIRO_TOP10)

    meta = {}
    if FICHEIRO_META.exists():
        try:
            meta = json.loads(FICHEIRO_META.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            meta = {}
    return serie, top10, meta


def variacoes(serie: pd.DataFrame) -> dict:
    """
    Três variações lidas diretamente da série: face à semana anterior, desde a
    primeira semana do ano do último ponto, e desde o início da série.

    Ler estas variações da própria série, em vez de as extrair do texto do
    artigo, é o que as torna robustas a uma reformulação da redação da DECO:
    dependem só dos pontos do gráfico.
    """
    if serie.empty or len(serie) < 2:
        return {}

    atual = serie.iloc[-1]
    anterior = serie.iloc[-2]
    do_ano = serie[serie["data"].dt.year == atual["data"].year]
    inicio_ano = do_ano.iloc[0] if not do_ano.empty else atual
    inicio_serie = serie.iloc[0]

    def _contra(base: pd.Series) -> dict:
        delta = float(atual["valor"] - base["valor"])
        pct = (delta / base["valor"] * 100) if base["valor"] else None
        return {"data": base["data"], "valor": float(base["valor"]),
                "delta": delta, "delta_pct": pct}

    return {
        "atual": {"data": atual["data"], "valor": float(atual["valor"])},
        "semana_anterior": _contra(anterior),
        "desde_ano_corrente": _contra(inicio_ano),
        "desde_inicio": _contra(inicio_serie),
    }
