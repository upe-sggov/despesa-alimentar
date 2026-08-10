"""
Cálculos analíticos: decomposição da despesa alimentar e simulação de alterações do IVA.

Notas metodológicas
-------------------
**Decomposição.** Não existe fonte pública com o preço dos produtos individuais.
O que se faz aqui é imputar o valor total pelas nove classes
COICOP, usando os ponderadores oficiais do IHPC, e aplicar a cada classe a sua
variação oficial. É uma reconstituição defensável e replicável — não é a
observação produto a produto.

**Contributo homólogo.** Se uma classe vale hoje Vᵢ e cresceu gᵢ %, há um ano
valia Vᵢ/(1+gᵢ). O acréscimo absoluto é Vᵢ·gᵢ/(1+gᵢ). A soma destes acréscimos
iguala exatamente a variação do total — a decomposição é aditiva.

**Simulação de IVA.** O parâmetro decisivo não é a taxa, é a repercussão: a
avaliação internacional (França 2009, Suécia) é consistentemente cética quanto
à transmissão integral das descidas de IVA para o preço final. Por isso a
repercussão é explícita e ajustável, e o resultado é sempre condicional a ela.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    CLASSES, POR_CODIGO,
    ESCALAS_TESTE_COMPOSICAO, ESCALAS_TESTE_RACIO,
    AGREGADOS_ANO, AGREGADOS_CENSOS, AGREGADOS_FONTE,
    IDF_ALIMENTAR_QUINTIL, IDF_CLASSES_QUINTIL, IDF_DESPESA_TOTAL,
    IDF_PESO_ALIMENTAR, IDF_QUINTIS,
)


# --------------------------------------------------------------------------
# Denominador da âncora
# --------------------------------------------------------------------------
def agregados_do_ano(serie: dict, ano) -> dict:
    """
    Número de agregados familiares a usar como denominador para um dado ano.

    O denominador tem de ser do **mesmo ano do numerador**. A despesa das Contas
    Nacionais é de 2022; dividi-la pelos agregados de 2025 dá um valor 9,1 %
    mais baixo por razão nenhuma — a população de agregados cresceu, a despesa
    não a acompanhou porque é de outro ano (auditoria de 10.08.2026, B2).

    `serie` é um dicionário ano (texto) → número de agregados. Prefere o ano
    pedido; se não existir, o mais próximo, declarando o desfasamento. Sem série
    disponível, recorre aos Censos.

    Devolve `{valor, ano, fonte, desfasamento}` — `desfasamento` em anos, para
    que a interface o possa mostrar.
    """
    alvo = str(ano) if ano is not None else None

    if serie and alvo:
        fonte = "Eurostat / Inquérito ao Emprego (EU-LFS)"
        if alvo in serie:
            return {"valor": serie[alvo], "ano": alvo, "fonte": fonte,
                    "desfasamento": 0}
        proximo = min(serie, key=lambda a: abs(int(a) - int(alvo)))
        return {"valor": serie[proximo], "ano": proximo, "fonte": fonte,
                "desfasamento": abs(int(proximo) - int(alvo))}

    desfasamento = abs(AGREGADOS_ANO - int(alvo)) if alvo else None
    return {"valor": AGREGADOS_CENSOS, "ano": str(AGREGADOS_ANO),
            "fonte": AGREGADOS_FONTE, "desfasamento": desfasamento}


# --------------------------------------------------------------------------
# Decomposição da despesa alimentar
# --------------------------------------------------------------------------
def decompor(valor_total: float,
             pesos: dict[str, float],
             variacoes: dict[str, float]) -> pd.DataFrame:
    """
    Reparte a despesa alimentar pelas classes e calcula o contributo de cada uma
    para a variação homóloga.

    Devolve um DataFrame com uma linha por classe.
    """
    total_pesos = sum(v for v in pesos.values() if v and v > 0)

    linhas = []
    for classe in CLASSES:
        cod = classe["cod"]
        peso = float(pesos.get(cod) or 0.0)
        quota = peso / total_pesos if total_pesos > 0 else 0.0
        valor = valor_total * quota

        var = variacoes.get(cod)
        if var is not None and pd.notna(var) and (1 + var / 100) != 0:
            contributo = valor * (var / 100) / (1 + var / 100)
        else:
            var, contributo = None, None

        linhas.append({
            "codigo": cod,
            "classe": classe["nome"],
            "emoji": classe["emoji"],
            "cor": classe["cor"],
            "ponderador": peso,
            "quota": quota,
            "valor": valor,
            "variacao": var,
            "contributo": contributo,
            "iva_defeito": classe["iva"],
        })

    return pd.DataFrame(linhas)


def resumo_decomposicao(df: pd.DataFrame, valor_total: float) -> dict:
    """Indicadores agregados da decomposição."""
    contributos = df["contributo"].dropna()
    total_contributo = float(contributos.sum()) if not contributos.empty else None

    resultado = {
        "valor": valor_total,
        "contributo_total": total_contributo,
        "valor_ha_um_ano": None,
        "variacao_implicita": None,
        "maior": None,
    }

    if total_contributo is not None:
        antes = valor_total - total_contributo
        resultado["valor_ha_um_ano"] = antes
        if antes > 0:
            resultado["variacao_implicita"] = total_contributo / antes * 100

        com_dados = df.dropna(subset=["contributo"])
        if not com_dados.empty:
            resultado["maior"] = com_dados.loc[com_dados["contributo"].idxmax()].to_dict()

    return resultado


# --------------------------------------------------------------------------
# Simulação de IVA
# --------------------------------------------------------------------------
def simular_iva(df: pd.DataFrame,
                taxas_atuais: dict[str, float],
                taxas_cenario: dict[str, float],
                repercussao: float) -> pd.DataFrame:
    """
    Para cada classe:

    - `base`      preço sem IVA = valor / (1 + t₀)
    - `mecanico`  variação com repercussão integral = base·(1+t₁) − valor
    - `efetivo`   variação observada = ρ · mecanico
    - `margem`    parte capturada pelo operador = (1−ρ) · mecanico
    - `iva_antes` / `iva_depois`  imposto contido no preço

    `repercussao` é uma fração entre 0 e 1.
    """
    linhas = []
    for _, linha in df.iterrows():
        cod = linha["codigo"]
        valor = float(linha["valor"])
        t0 = float(taxas_atuais.get(cod, linha["iva_defeito"]))
        t1 = float(taxas_cenario.get(cod, t0))

        base = valor / (1 + t0 / 100)
        preco_cheio = base * (1 + t1 / 100)
        mecanico = preco_cheio - valor
        efetivo = repercussao * mecanico
        novo_valor = valor + efetivo

        iva_antes = valor - base
        iva_depois = novo_valor * (t1 / 100) / (1 + t1 / 100)

        linhas.append({
            "codigo": cod,
            "classe": linha["classe"],
            "emoji": linha["emoji"],
            "cor": linha["cor"],
            "valor": valor,
            "taxa_atual": t0,
            "taxa_cenario": t1,
            "base": base,
            "mecanico": mecanico,
            "efetivo": efetivo,
            "margem": mecanico - efetivo,
            "novo_valor": novo_valor,
            "iva_antes": iva_antes,
            "iva_depois": iva_depois,
        })

    return pd.DataFrame(linhas)


def resumo_iva(sim: pd.DataFrame, valor_total: float,
               vezes_ano: int, agregados: int) -> dict:
    """
    Agrega o resultado da simulação e extrapola ordens de grandeza.

    ⚠️ Os dois campos ``*_agregada_milhoes`` multiplicam o resultado por
    `agregados`. **Só são válidos quando `sim` foi construída sobre a despesa do
    agregado médio.** Se `sim` vier de uma despesa já ajustada a uma composição
    concreta — dois adultos, cinco adultos —, a multiplicação conta o país
    inteiro como se fosse todo composto dessa maneira, e o total nacional passa
    a depender de um parâmetro de leitura. O erro mede-se: −14 % para dois
    adultos, +92 % para cinco (auditoria de 10.08.2026, A3). Os restantes campos
    são por agregado e não têm esta restrição.
    """
    mecanico = float(sim["mecanico"].sum())
    efetivo = float(sim["efetivo"].sum())
    margem = float(sim["margem"].sum())
    iva_antes = float(sim["iva_antes"].sum())
    iva_depois = float(sim["iva_depois"].sum())

    poupanca_mes = -efetivo          # positiva quando a despesa desce
    poupanca_ano = poupanca_mes * vezes_ano
    receita_mes = iva_depois - iva_antes

    return {
        "novo_valor": valor_total + efetivo,
        "mecanico": mecanico,
        "efetivo": efetivo,
        "poupanca_mes": poupanca_mes,
        "poupanca_ano": poupanca_ano,
        "margem": -margem,
        "iva_antes": iva_antes,
        "iva_depois": iva_depois,
        "receita_mes": receita_mes,
        "poupanca_agregada_milhoes": poupanca_ano * agregados / 1e6,
        "receita_agregada_milhoes": receita_mes * vezes_ano * agregados / 1e6,
    }


# --------------------------------------------------------------------------
# Composição do agregado e escalas de equivalência
# --------------------------------------------------------------------------
# Uma despesa média por agregado esconde uma diferença que importa para
# política: um agregado de uma pessoa e um casal com dois filhos não gastam o
# mesmo. As escalas de equivalência são o instrumento oficial para comparar
# agregados de composição diferente.
#
# Ressalva importante: estas escalas foram construídas para o consumo *total*,
# em que a partilha de habitação gera fortes economias de escala. Na
# alimentação as economias de escala são bem mais fracas — não se partilha uma
# refeição como se partilha um teto. Por isso a escala OCDE modificada tende a
# **subestimar** o custo alimentar de agregados maiores, e a aplicação
# apresenta sempre um intervalo em vez de um valor único.

ESCALAS = {
    "per_capita": {
        "nome": "Per capita (sem economias de escala)",
        "primeiro": 1.0, "adulto": 1.0, "crianca": 1.0,
        "nota": "Limite superior: cada pessoa custa o mesmo.",
    },
    "ocde_original": {
        "nome": "OCDE original (1 / 0,7 / 0,5)",
        "primeiro": 1.0, "adulto": 0.7, "crianca": 0.5,
        "nota": "A que fica mais perto da despesa alimentar observada no IDF 2022/2023.",
    },
    "ocde_modificada": {
        "nome": "OCDE modificada (1 / 0,5 / 0,3)",
        "primeiro": 1.0, "adulto": 0.5, "crianca": 0.3,
        "nota": "Norma da UE para rendimento; subestima o custo alimentar em ~10 %.",
    },
}


def testar_escalas() -> pd.DataFrame:
    """
    Confronta o rácio de despesa que cada escala prevê com o observado no IDF,
    para a alimentação e — como controlo — para a despesa total.

    Uma linha por escala. `desvio_alimentar` positivo significa que a escala
    **subestima** o custo alimentar de agregados maiores: o observado é maior do
    que o previsto.
    """
    linhas = []
    for chave, e in ESCALAS.items():
        # Rácio previsto entre «2 ou +» e «1 adulto», para a composição do IDF.
        previsto = sum(
            fracao * (e["primeiro"] + e["adulto"] * (adultos - 1))
            for adultos, fracao in ESCALAS_TESTE_COMPOSICAO
        )
        if previsto <= 0:
            continue
        linhas.append({
            "escala": chave,
            "nome": e["nome"],
            "previsto": previsto,
            "observado_alimentar": ESCALAS_TESTE_RACIO["alimentar"],
            "desvio_alimentar": (ESCALAS_TESTE_RACIO["alimentar"] / previsto - 1) * 100,
            "observado_total": ESCALAS_TESTE_RACIO["total"],
            "desvio_total": (ESCALAS_TESTE_RACIO["total"] / previsto - 1) * 100,
        })

    df = pd.DataFrame(linhas)
    if not df.empty:
        df["erro_absoluto"] = df["desvio_alimentar"].abs()
    return df


def escala_mais_proxima() -> str | None:
    """A escala cuja previsão fica mais perto do observado na alimentação."""
    df = testar_escalas()
    if df.empty:
        return None
    return str(df.loc[df["erro_absoluto"].idxmin(), "escala"])


def unidades_equivalentes(adultos: int, criancas: int, escala: str) -> float:
    """Unidades de consumo equivalente de um agregado, segundo a escala."""
    e = ESCALAS[escala]
    adultos = max(int(adultos), 1)
    criancas = max(int(criancas), 0)
    return e["primeiro"] + e["adulto"] * (adultos - 1) + e["crianca"] * criancas


def despesa_do_agregado(despesa_media_agregado: float,
                        dimensao_media: float,
                        adultos: int,
                        criancas: int,
                        escala: str) -> float:
    """
    Converte a despesa média nacional por agregado na despesa estimada de um
    agregado com a composição indicada.

    O agregado médio é modelado com `dimensao_media` pessoas adultas — é uma
    aproximação, necessária porque a dimensão média é publicada sem
    decomposição por idade.
    """
    e = ESCALAS[escala]
    eq_medio = e["primeiro"] + e["adulto"] * (max(dimensao_media, 1.0) - 1)
    if eq_medio <= 0:
        return despesa_media_agregado
    por_unidade = despesa_media_agregado / eq_medio
    return por_unidade * unidades_equivalentes(adultos, criancas, escala)


def intervalo_agregado(despesa_media_agregado: float, dimensao_media: float,
                       adultos: int, criancas: int) -> dict:
    """Intervalo entre a escala mais generosa e a mais restritiva."""
    valores = {
        chave: despesa_do_agregado(despesa_media_agregado, dimensao_media,
                                   adultos, criancas, chave)
        for chave in ESCALAS
    }
    return {
        "minimo": min(valores.values()),
        "maximo": max(valores.values()),
        "por_escala": valores,
    }


# --------------------------------------------------------------------------
# Cabaz por quintil de rendimento — ponderação IDF
# --------------------------------------------------------------------------
# Aqui os ponderadores são do IDF, não do IHPC. São coisas diferentes e a
# escolha não é indiferente: entre as duas estruturas o desvio médio absoluto
# dentro da alimentação é de 1,9 p.p. e o máximo de 4,9 p.p. (pão e cereais).
# Ver a nota em `config.py` sobre a inclusão de turistas no IHPC.
#
# Regra de apresentação, deliberada: a taxa de inflação por quintil **nunca**
# deve aparecer sem a exposição orçamental ao lado. A amplitude entre quintis é
# de cerca de 0,2 p.p. — lida isolada, sugere que a inflação alimentar é
# distributivamente neutra. Não é: o efeito regressivo está na exposição
# (14,8 % do orçamento no 1.º quintil contra 9,1 % no 5.º), não na taxa. Por
# isso as duas colunas saem da mesma função e devem ser mostradas juntas.

def cabaz_quintis(variacoes: dict[str, float]) -> pd.DataFrame:
    """
    Uma linha por quintil de rendimento, com o nível da despesa alimentar, a
    exposição orçamental e a inflação que resulta da estrutura de consumo desse
    quintil.

    Os níveis são os do IDF 2022/2023 tal como medidos — não são reescalados
    para a âncora escolhida na aplicação. Reescalar exigiria assumir que o
    sub-reporte do inquérito é uniforme entre quintis, e nada o sustenta.
    """
    linhas = []
    for chave, nome in IDF_QUINTIS.items():
        alimentar_ano = float(IDF_ALIMENTAR_QUINTIL[chave])
        mensal = alimentar_ano / 12

        soma_pesos, soma_ponderada, agravamento = 0.0, 0.0, 0.0
        for classe in CLASSES:
            cod = classe["cod"]
            peso = float(IDF_CLASSES_QUINTIL[cod][chave])
            var = variacoes.get(cod)
            if var is None or pd.isna(var):
                continue
            soma_pesos += peso
            soma_ponderada += peso * float(var)
            valor_classe = mensal * peso / alimentar_ano if alimentar_ano else 0.0
            if (1 + var / 100) != 0:
                agravamento += valor_classe * (var / 100) / (1 + var / 100)

        inflacao = soma_ponderada / soma_pesos if soma_pesos > 0 else None
        total_mensal = float(IDF_DESPESA_TOTAL[chave]) / 12

        # O agravamento em euros é *maior* nos quintis de cima — gastam mais em
        # alimentação, logo o mesmo aumento percentual dá mais euros. Lido só
        # assim, inverte a leitura correta. O que mede o esforço é o agravamento
        # em fração do orçamento total, e é essa a coluna que fecha o argumento.
        esforco = (agravamento / total_mensal * 100
                   if (soma_pesos > 0 and total_mensal > 0) else None)

        linhas.append({
            "quintil": chave,
            "nome": nome,
            "despesa_mensal": mensal,
            "despesa_total_mensal": total_mensal,
            "peso_orcamento": float(IDF_PESO_ALIMENTAR[chave]),
            "inflacao": inflacao,
            "agravamento": agravamento if soma_pesos > 0 else None,
            "agravamento_orcamento": esforco,
        })

    return pd.DataFrame(linhas)


def composicao_quintis() -> pd.DataFrame:
    """
    Uma linha por classe COICOP e quintil, em euros por mês e em quota da
    despesa alimentar desse quintil. É o que mostra que a composição muda, e
    não apenas o nível.
    """
    linhas = []
    for classe in CLASSES:
        cod = classe["cod"]
        for chave, nome in IDF_QUINTIS.items():
            total = float(IDF_ALIMENTAR_QUINTIL[chave])
            valor = float(IDF_CLASSES_QUINTIL[cod][chave])
            linhas.append({
                "codigo": cod,
                "classe": classe["nome"],
                "emoji": classe["emoji"],
                "cor": classe["cor"],
                "quintil": chave,
                "quintil_nome": nome,
                "mensal": valor / 12,
                "quota": valor / total if total else 0.0,
            })

    return pd.DataFrame(linhas)


# --------------------------------------------------------------------------
# Viés de substituição — Laspeyres de cabaz fixo contra Törnqvist
# --------------------------------------------------------------------------
# A crítica central da nota de enquadramento ao cabaz de composição fixa é que
# ele não acompanha a substituição de consumo: se as famílias trocam novilho por
# frango, um cabaz que continua a pesar o novilho como antes sobrestima o que
# elas efetivamente pagam. Esta secção mede esse efeito em vez de o afirmar.
#
# Três índices, todos encadeados a partir do mesmo dezembro de base:
#
#   Laspeyres fixo   ponderadores congelados no ano-base. É a construção do
#                    cabaz da DECO, transposta para as nove classes.
#   IHPC oficial     encadeado com ponderadores revistos todos os anos. É o
#                    índice publicado.
#   Törnqvist        índice superlativo: cada elo usa a média dos ponderadores
#                    dos dois extremos. É a referência teórica contra a qual se
#                    mede o viés dos outros dois.
#
# **Aproximação a declarar.** O Törnqvist exige as quotas de despesa observadas
# nos dois extremos de cada elo. O que existe em fonte aberta são os
# ponderadores do IHPC, que o Documento Metodológico do IPC define como
# referidos a dezembro do ano n−1 e já atualizados a preços desse momento. A
# correspondência adotada é a que decorre dessa definição: o elo que vai de
# dezembro de y−1 a dezembro de y usa a média dos ponderadores de y e de y+1,
# por serem esses os que se reportam àqueles dois momentos. Não é o Törnqvist
# exato — é a melhor aproximação possível sem microdados de despesa anuais.

def _dezembros(indice_classes: pd.DataFrame) -> pd.DataFrame:
    """Índice de dezembro de cada ano, por classe, numa base única."""
    if indice_classes.empty:
        return pd.DataFrame()

    df = indice_classes.copy()
    if "unit" in df.columns:
        # A base do índice mudou ao longo do tempo (2015=100 → 2025=100).
        # Misturar bases numa razão de índices produz lixo silencioso.
        contagem = df["unit"].value_counts()
        preferida = next((u for u in ("I25", "I15", "I05", "I96")
                          if u in contagem.index), contagem.index[0])
        df = df[df["unit"] == preferida]

    df = df[df["time"].astype(str).str.endswith("-12")].copy()
    df["ano"] = df["time"].astype(str).str[:4].astype(int)
    return df.pivot_table(index="ano", columns="coicop", values="valor",
                          aggfunc="last").sort_index()


def indices_comparados(indice_classes: pd.DataFrame,
                       pesos_por_ano: pd.DataFrame) -> pd.DataFrame:
    """
    Uma linha por dezembro, com os três índices em base 100 no primeiro ano
    comum às duas fontes. Devolve DataFrame vazio se não houver anos que
    cheguem — são precisos pelo menos dois elos para haver o que comparar.
    """
    dez = _dezembros(indice_classes)
    if dez.empty or pesos_por_ano.empty:
        return pd.DataFrame()

    pesos = pesos_por_ano.copy()
    pesos["ano"] = pesos["time"].astype(str).str[:4].astype(int)
    w = pesos.pivot_table(index="ano", columns="coicop", values="valor",
                          aggfunc="last").sort_index()

    codigos = [c["cod"] for c in CLASSES
               if c["cod"] in dez.columns and c["cod"] in w.columns]
    if len(codigos) < 2:
        return pd.DataFrame()

    dez, w = dez[codigos].dropna(), w[codigos].dropna()
    if dez.empty or w.empty:
        return pd.DataFrame()

    # Quotas normalizadas dentro da alimentação — os ponderadores do IHPC somam
    # 1 000 sobre todo o cabaz do índice, não sobre as nove classes.
    quotas = w.div(w.sum(axis=1), axis=0)

    # Basta existir o ponderador do próprio ano. Para o último elo o ponderador
    # de y+1 ainda não foi publicado — nesse caso repete-se o de y, o que
    # equivale a assumir estrutura constante no último ano. É o único elo
    # afetado e o efeito é de segunda ordem.
    anos = [a for a in dez.index if a in quotas.index]
    if len(anos) < 2:
        return pd.DataFrame()

    base = anos[0]
    quotas_base = quotas.loc[base]

    linhas = [{"ano": base, "laspeyres_fixo": 100.0, "tornqvist": 100.0}]
    log_torn = 0.0
    for anterior, corrente in zip(anos, anos[1:]):
        relativos = dez.loc[corrente] / dez.loc[anterior]

        # Törnqvist: média das quotas dos dois extremos do elo.
        q_ini = quotas.loc[anterior + 1] if (anterior + 1) in quotas.index else quotas.loc[anterior]
        q_fim = quotas.loc[corrente + 1] if (corrente + 1) in quotas.index else quotas.loc[corrente]
        media = (q_ini + q_fim) / 2
        log_torn += float((media * np.log(relativos)).sum())

        # Laspeyres de cabaz fixo: sempre as quotas do ano-base, aplicadas ao
        # relativo acumulado desde o ano-base.
        acumulado = dez.loc[corrente] / dez.loc[base]
        laspeyres = float((quotas_base * acumulado).sum()) * 100

        linhas.append({"ano": corrente,
                       "laspeyres_fixo": laspeyres,
                       "tornqvist": float(np.exp(log_torn)) * 100})

    df = pd.DataFrame(linhas)
    df["vies"] = df["laspeyres_fixo"] - df["tornqvist"]
    return df


def comparar_ponderadores(pesos_ihpc: dict[str, float],
                          variacoes: dict[str, float]) -> dict:
    """
    Confronta as duas estruturas de ponderação na única grandeza em que a
    escolha é observável: a inflação alimentar nacional que cada uma produz.

    Serve de diagnóstico no separador de metodologia — quantifica o que se
    ganha e o que se perde ao trocar de base, em vez de o deixar como
    afirmação.
    """
    def _agregar(pesos: dict[str, float]) -> tuple:
        soma_pesos, soma_ponderada = 0.0, 0.0
        for classe in CLASSES:
            cod = classe["cod"]
            peso = float(pesos.get(cod) or 0.0)
            var = variacoes.get(cod)
            if peso <= 0 or var is None or pd.isna(var):
                continue
            soma_pesos += peso
            soma_ponderada += peso * float(var)
        if soma_pesos <= 0:
            return None, {}
        quotas = {c["cod"]: float(pesos.get(c["cod"]) or 0.0) / soma_pesos * 100
                  for c in CLASSES}
        return soma_ponderada / soma_pesos, quotas

    inf_ihpc, quota_ihpc = _agregar(pesos_ihpc)
    pesos_idf = {c["cod"]: float(IDF_CLASSES_QUINTIL[c["cod"]]["total"]) for c in CLASSES}
    inf_idf, quota_idf = _agregar(pesos_idf)

    desvios = [
        {"codigo": c["cod"], "classe": c["nome"], "emoji": c["emoji"],
         "quota_ihpc": quota_ihpc.get(c["cod"]), "quota_idf": quota_idf.get(c["cod"]),
         "desvio": (quota_ihpc.get(c["cod"], 0.0) - quota_idf.get(c["cod"], 0.0))}
        for c in CLASSES if quota_ihpc and quota_idf
    ]
    df = pd.DataFrame(desvios)

    return {
        "inflacao_ihpc": inf_ihpc,
        "inflacao_idf": inf_idf,
        "diferenca": (inf_idf - inf_ihpc) if (inf_idf is not None and inf_ihpc is not None) else None,
        "desvios": df,
        "desvio_medio": float(df["desvio"].abs().mean()) if not df.empty else None,
        "desvio_maximo": float(df["desvio"].abs().max()) if not df.empty else None,
    }
