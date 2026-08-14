"""
Observatório de Preços Agroalimentar (GPP), do produtor ao consumidor.

Responde à pergunta que nenhum outro instrumento desta aplicação toca: **onde
na cadeia está o aumento**. O índice de preços mede o que o consumidor paga; as
Contas Nacionais e o IDF medem quanto se gasta. Nenhum diz se a subida nasceu na
exploração agrícola, na transformação ou na distribuição.

Os dados não vêm em direto: são recolhidos por `scripts/recolher_observatorio.py`
e lidos aqui de `dados/observatorio.csv`. A razão está documentada no script,
o Observatório não tem API, e a série completa exige uma chamada por produto.

Ressalva central, que atravessa todo este módulo
------------------------------------------------
**A diferença entre o preço no consumo e o preço na produção não é a margem de
ninguém.** Inclui transporte, transformação, embalagem, distribuição e IVA. E as
duas fases podem referir-se a formas diferentes do produto, peixe inteiro contra
posta, animal vivo contra peça desmanchada. Não é comparável entre produtos, e
não deve ser lida como lucro de nenhum operador.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
FICHEIRO = RAIZ / "dados" / "observatorio.csv"
FICHEIRO_META = RAIZ / "dados" / "observatorio_meta.json"

FASES = {"producao": "Produção", "consumo": "Consumo"}


def carregar() -> tuple[pd.DataFrame, dict]:
    """Devolve (observações, metadados). DataFrame vazio se não houver recolha."""
    if not FICHEIRO.exists():
        return pd.DataFrame(), {}
    df = pd.read_csv(FICHEIRO)
    df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce")
    df = df.dropna(subset=["inicio", "preco"])

    meta = {}
    if FICHEIRO_META.exists():
        try:
            meta = json.loads(FICHEIRO_META.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            meta = {}
    return df, meta


def variacoes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Uma linha por produto, com a variação de cada fase entre a primeira e a
    última observação **comuns às duas fases**.

    A restrição ao período comum não é um detalhe. Várias séries de produção
    terminam antes das de consumo, cebola e brócolo em 2023, por exemplo. Se
    cada fase fosse medida no seu próprio intervalo, comparar-se-iam variações
    de períodos diferentes, e a diferença entre elas não significaria nada.
    """
    if df.empty or not {"setor", "produto", "fase", "inicio", "preco"}.issubset(df.columns):
        return pd.DataFrame()

    linhas = []
    for (setor, produto), g in df.groupby(["setor", "produto"], sort=False):
        fases = {f: sub.sort_values("inicio") for f, sub in g.groupby("fase")}
        if "consumo" not in fases:
            continue

        registo = {"setor": setor, "produto": produto,
                   "unidade": g["unidade"].mode().iloc[0] if not g["unidade"].isna().all() else ""}

        if "producao" in fases:
            # Interseção dos períodos: só assim as duas variações são comparáveis.
            comuns = sorted(set(fases["consumo"]["inicio"]) & set(fases["producao"]["inicio"]))
            if len(comuns) < 2:
                continue
            ini, fim = comuns[0], comuns[-1]
            registo["inicio"], registo["fim"] = ini, fim
            registo["n_periodos"] = len(comuns)
            for fase in ("consumo", "producao"):
                serie = fases[fase].set_index("inicio")["preco"]
                p0, p1 = float(serie.loc[ini]), float(serie.loc[fim])
                registo[f"{fase}_inicial"] = p0
                registo[f"{fase}_final"] = p1
                registo[f"{fase}_var"] = (p1 / p0 - 1) * 100 if p0 else None
            d0 = registo["consumo_inicial"] - registo["producao_inicial"]
            d1 = registo["consumo_final"] - registo["producao_final"]
            registo["diferenca_inicial"] = d0
            registo["diferenca_final"] = d1
            registo["diferenca_var"] = (d1 / d0 - 1) * 100 if d0 else None
            registo["tem_producao"] = True
        else:
            serie = fases["consumo"].sort_values("inicio")
            ini = serie["inicio"].iloc[0]
            fim = serie["inicio"].iloc[-1]
            p0, p1 = float(serie["preco"].iloc[0]), float(serie["preco"].iloc[-1])
            registo.update({
                "inicio": ini, "fim": fim, "n_periodos": len(serie),
                "consumo_inicial": p0, "consumo_final": p1,
                "consumo_var": (p1 / p0 - 1) * 100 if p0 else None,
                "tem_producao": False,
            })

        linhas.append(registo)

    if not linhas:
        return pd.DataFrame()

    out = pd.DataFrame(linhas)
    out["padrao"] = out.apply(_classificar, axis=1)
    return out.sort_values("consumo_var", ascending=False).reset_index(drop=True)


def _classificar(linha: pd.Series) -> str:
    """
    Rotula o padrão de transmissão ao longo da cadeia.

    É uma leitura descritiva das duas variações, não uma inferência causal:
    diz onde os preços se moveram, não quem decidiu o quê.
    """
    if not linha.get("tem_producao"):
        return "Sem série de produção"

    cons, prod = linha.get("consumo_var"), linha.get("producao_var")
    if cons is None or prod is None:
        return "Indeterminado"

    if prod > 0 and cons > 0:
        if cons >= prod * 0.8:
            return "Choque na origem, transmitido"
        return "Absorvido pela cadeia"
    if prod <= 0 and cons > 0:
        return "Divergência"
    if prod > 0 and cons <= 0:
        return "Absorvido pela cadeia"
    return "Descida em ambas as fases"


PADROES = {
    "Choque na origem, transmitido":
        "O preço subiu na produção e a subida chegou ao consumidor em proporção "
        "semelhante ou maior.",
    "Absorvido pela cadeia":
        "O preço subiu mais na produção do que no consumo, a cadeia absorveu "
        "parte do choque, ou comprimiu a diferença.",
    "Divergência":
        "O preço **caiu** na produção e **subiu** no consumo. É o padrão que mais "
        "atenção merece, e o que a leitura agregada do cabaz esconde por completo.",
    "Descida em ambas as fases":
        "Preços em queda na produção e no consumo.",
    "Sem série de produção":
        "O Observatório só publica preço ao consumidor para este produto.",
}


def serie_produto(df: pd.DataFrame, produto: str) -> pd.DataFrame:
    """Série temporal das duas fases de um produto, em formato largo."""
    sub = df[df["produto"] == produto]
    if sub.empty:
        return pd.DataFrame()
    return (sub.pivot_table(index="inicio", columns="fase", values="preco",
                            aggfunc="last")
            .sort_index()
            .rename(columns=FASES))
