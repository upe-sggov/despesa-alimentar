"""
Recolha do Observatório de Preços Agroalimentar (GPP).

Porque é que isto é um script e não uma chamada da aplicação
------------------------------------------------------------
Tudo o resto na aplicação vem em direto do Eurostat, que serve uma API pública
desenhada para consumo automatizado. O Observatório não tem API: os gráficos do
sítio são alimentados por um *endpoint* AJAX do WordPress, e obter a série
completa exige uma chamada por produto — hoje, 39.

Fazer 39 pedidos POST a um sítio institucional sempre que a cache da aplicação
expira seria desproporcionado, e desnecessário: os dados são publicados em
períodos de **quatro semanas**, não continuamente. Por isso a recolha é um passo
explícito, que escreve um ficheiro versionado, e a aplicação limita-se a lê-lo.

Ganha-se ainda reprodutibilidade: o ficheiro fica no repositório com a data de
extração, e qualquer número apresentado pode ser reconstituído.

Executar:  python scripts/recolher_observatorio.py
Escreve:   dados/observatorio.csv  e  dados/observatorio_meta.json

Notas sobre a fonte
-------------------
- `fase` 1 = produção, 2 = consumo. Basta pedir a fase de consumo: a resposta
  traz também a série de produção do mesmo produto, pelo mecanismo de comparação
  do próprio sítio.
- Os períodos são de quatro semanas, treze por ano, identificados por P1..P13 e
  pela data de início.
- Nem todos os produtos têm as duas fases, e várias séries de produção terminam
  antes do fim da série de consumo.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

BASE = "https://observatorioagroalimentar.gov.pt"
AJAX = BASE + "/wp-admin/admin-ajax.php"
CABECALHOS = {
    "User-Agent": "SGGov-UPE-CabazAlimentar/1.0 (analise estatistica; contacto via SGGov)",
    "X-Requested-With": "XMLHttpRequest",
}
PAUSA = 0.4          # cortesia para com o servidor do GPP
TEMPO_LIMITE = 60

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "dados" / "observatorio.csv"
META = RAIZ / "dados" / "observatorio_meta.json"


def _sessao() -> requests.Session:
    s = requests.Session()
    s.headers.update(CABECALHOS)
    return s


def descobrir_produtos(s: requests.Session) -> list[dict]:
    """
    Percorre as páginas de setor e recolhe os produtos de cada uma.

    A lista de produtos não está publicada num sítio só: cada página `/setor/`
    tem o seu próprio `<select name="product">`.
    """
    indice = s.get(f"{BASE}/observatorio/", timeout=TEMPO_LIMITE).text
    setores = sorted(set(re.findall(r"/setor/([a-z0-9-]+)/", indice)))
    if not setores:
        raise SystemExit("Não foi encontrado nenhum setor — a estrutura do sítio mudou.")

    produtos: dict[int, dict] = {}
    for slug in setores:
        pagina = s.get(f"{BASE}/setor/{slug}/", timeout=TEMPO_LIMITE).text
        bloco = re.search(
            r'<select[^>]*name=["\']product["\'][^>]*>(.*?)</select>', pagina, re.S | re.I)
        if not bloco:
            print(f"  ! {slug}: sem seletor de produto", file=sys.stderr)
            continue
        for valor, rotulo in re.findall(
                r'<option[^>]*value=["\']([^"\']*)["\'][^>]*>(.*?)</option>',
                bloco.group(1), re.S):
            if not valor.strip().isdigit():
                continue                      # a opção «Selecione um Produto»
            pid = int(valor)
            produtos[pid] = {"id": pid, "setor": slug,
                             "nome": re.sub(r"<[^>]+>", "", rotulo).strip()}
        time.sleep(PAUSA)

    return sorted(produtos.values(), key=lambda p: (p["setor"], p["nome"]))


def _periodos(labels: list[str]) -> list[dict]:
    """«P3 (2022-02-28)» → período, data de início."""
    saida = []
    for r in labels:
        m = re.match(r"\s*P(\d+)\s*\((\d{4}-\d{2}-\d{2})\)", r)
        saida.append({"periodo": int(m.group(1)) if m else None,
                      "inicio": m.group(2) if m else None,
                      "rotulo": r})
    return saida


def obter_serie(s: requests.Session, produto: dict,
                ano_fim: int) -> list[dict]:
    """
    Uma chamada por produto. A resposta traz as duas fases — a de consumo,
    pedida, e a de produção, incluída pelo mecanismo de comparação do sítio.
    """
    resp = s.post(AJAX, timeout=TEMPO_LIMITE, data={
        "action": "get_produto_graph",
        "fase": 2,
        "product": produto["id"],
        "start_year": 2022, "start_period": 1,
        "end_year": ano_fim, "end_period": 13,
    })
    resp.raise_for_status()
    corpo = resp.json()
    if corpo.get("status") != 200:
        return []

    periodos = _periodos(json.loads(corpo["labels_grafico"]))
    linhas = []
    for serie in json.loads(corpo["produtos_graph_info"]):
        legenda = serie.get("legenda", "")
        if "Produção" in legenda:
            fase = "producao"
        elif "Consumo" in legenda:
            fase = "consumo"
        else:
            fase = "outra"
        unidade = ""
        mu = re.search(r"\(([^)]*)\)\s*$", legenda)
        if mu:
            unidade = mu.group(1)

        for p, valor in zip(periodos, serie.get("dados", [])):
            if valor is None:
                continue
            linhas.append({
                "setor": produto["setor"],
                "produto": produto["nome"],
                "produto_id": produto["id"],
                "serie_id": serie.get("id"),
                "fase": fase,
                "unidade": unidade,
                "periodo": p["periodo"],
                "inicio": p["inicio"],
                "preco": float(valor),
            })
    return linhas


def main() -> int:
    s = _sessao()
    print("A descobrir produtos…")
    produtos = descobrir_produtos(s)
    print(f"  {len(produtos)} produtos em "
          f"{len({p['setor'] for p in produtos})} setores")

    ano_fim = date.today().year
    todas, falhas = [], []
    for i, prod in enumerate(produtos, 1):
        try:
            linhas = obter_serie(s, prod, ano_fim)
            todas.extend(linhas)
            print(f"  [{i:2}/{len(produtos)}] {prod['nome'][:40]:40} {len(linhas):5} obs.")
        except Exception as exc:                              # noqa: BLE001
            falhas.append({"produto": prod["nome"], "erro": str(exc)})
            print(f"  [{i:2}/{len(produtos)}] {prod['nome'][:40]:40} FALHOU: {exc}",
                  file=sys.stderr)
        time.sleep(PAUSA)

    if not todas:
        print("Nenhuma observação recolhida — nada foi escrito.", file=sys.stderr)
        return 1

    df = pd.DataFrame(todas).sort_values(
        ["setor", "produto", "fase", "inicio"]).reset_index(drop=True)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DESTINO, index=False, encoding="utf-8")

    meta = {
        "extraido_em": date.today().isoformat(),
        "fonte": "GPP — Observatório de Preços Agroalimentar",
        "endereco": AJAX,
        "acao": "get_produto_graph",
        "produtos": int(df["produto"].nunique()),
        "setores": int(df["setor"].nunique()),
        "periodos": int(df["inicio"].nunique()),
        "primeiro_periodo": df["inicio"].min(),
        "ultimo_periodo": df["inicio"].max(),
        "observacoes": int(len(df)),
        "com_producao": sorted(df[df["fase"] == "producao"]["produto"].unique()),
        "falhas": falhas,
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{len(df)} observações · {meta['produtos']} produtos · "
          f"{meta['primeiro_periodo']} a {meta['ultimo_periodo']}")
    print(f"escrito: {DESTINO}")
    if falhas:
        print(f"ATENÇÃO: {len(falhas)} produtos falharam — ver {META.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
