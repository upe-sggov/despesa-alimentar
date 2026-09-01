"""
Cálculos analíticos: decomposição da despesa alimentar e simulação de alterações do IVA.

Notas metodológicas
-------------------
**Decomposição.** Não existe fonte pública com o preço dos produtos individuais.
O que se faz aqui é imputar o valor total pelas nove classes
COICOP, usando os ponderadores oficiais do IHPC, e aplicar a cada classe a sua
variação oficial. É uma reconstituição defensável e replicável, não é a
observação produto a produto.

**Contributo homólogo.** Se uma classe vale hoje Vᵢ e cresceu gᵢ %, há um ano
valia Vᵢ/(1+gᵢ). O acréscimo absoluto é Vᵢ·gᵢ/(1+gᵢ). A soma destes acréscimos
iguala exatamente a variação do total, a decomposição é aditiva.

**Simulação de IVA.** O parâmetro decisivo não é a taxa, é a repercussão: a
avaliação internacional (França 2009, Suécia) é consistentemente cética quanto
à transmissão integral das descidas de IVA para o preço final. Por isso a
repercussão é explícita e ajustável, e o resultado é sempre condicional a ela.
"""

from __future__ import annotations

import calendar as _calendar
import re as _re
from datetime import date as _date, datetime as _datetime

import numpy as np
import pandas as pd

from .config import (
    ANO_BASE_VIES, CLASSES, IVA_COMPONENTES,
    ESCALAS_TESTE_COMPOSICAO, ESCALAS_TESTE_RACIO,
    AGREGADOS_ANO, AGREGADOS_CENSOS, AGREGADOS_FONTE,
    IDF_ALIMENTAR_QUINTIL, IDF_CLASSES_QUINTIL, IDF_DESPESA_TOTAL,
    IDF_PESO_ALIMENTAR, IDF_QUINTIS,
    REPERCUSSAO_BANDA, REPERCUSSAO_ESTIMATIVAS, REPERCUSSAO_PADRAO,
)


# --------------------------------------------------------------------------
# Frescura das fontes que não vêm de API
# --------------------------------------------------------------------------
def idade_fonte(referencia, limite_dias: int, hoje=None) -> dict:
    """
    Idade de uma fonte cuja atualização é manual, e se já passou do prazo.

    O SOFI (inscrito em `config.py`) e o Observatório (em `dados/`) não têm API.
    Se ninguém os atualizar, a aplicação continua a mostrá-los sem nunca dar
    erro, envelhecem em silêncio (auditoria de 10.08.2026, D4). Esta função
    dá à interface o que ela precisa para o dizer.

    `referencia` aceita uma data (`date`/`datetime`), uma cadeia ISO
    (`'2026-08-10'`) ou um ano (`2025` ou `'2025'`, tomado como 31 de dezembro
    desse ano, a data mais favorável à fonte, para não exagerar a idade).

    Devolve `{data, dias, limite_dias, desatualizada}`; `data` é None e
    `desatualizada` é False se a referência não for interpretável, na dúvida,
    não se acusa a fonte.
    """
    hoje = hoje or _date.today()
    if isinstance(hoje, _datetime):
        hoje = hoje.date()

    data = None
    if isinstance(referencia, _datetime):
        data = referencia.date()
    elif isinstance(referencia, _date):
        data = referencia
    elif isinstance(referencia, int):
        data = _date(referencia, 12, 31)
    elif isinstance(referencia, str):
        texto = referencia.strip()
        if texto.isdigit() and len(texto) == 4:
            data = _date(int(texto), 12, 31)
        else:
            try:
                data = _date.fromisoformat(texto[:10])
            except ValueError:
                data = None

    if data is None:
        return {"data": None, "dias": None, "limite_dias": limite_dias,
                "desatualizada": False}

    dias = (hoje - data).days
    return {"data": data, "dias": dias, "limite_dias": limite_dias,
            "desatualizada": dias > limite_dias}


def frescura_do_observatorio(ultima_observacao, recolhido_em, limite_dias: int,
                             cadencia_dias: int = 28, hoje=None) -> dict:
    """
    Se o Observatório ainda está a avançar, e, se não está, de quem é a falha.

    A verificação anterior media **a data em que o script correu**, não a data da
    última observação. As duas coisas divergem, e a divergência é precisamente o
    caso que interessa: hoje a recolha tem 2 dias e a última observação tem 86,
    com um limite de 60. O aviso não disparava (auditoria de 12.08.2026, K2).

    É a lição do E1, “uma série que responde não é uma série que avança”,
    aplicada à fonte que deu origem à verificação, e que tinha ficado de fora.
    Correr o script sobre uma fonte que não publicou não torna os dados
    recentes.

    Distinguem-se dois casos, porque a resposta é diferente:

    - **a recolha está velha** → ninguém correu o script; correr resolve;
    - **a recolha está fresca e a série parada** → a fonte é que não publicou,
      e correr o script não resolve nada.

    Devolve `serie` e `recolha` (ambos como `idade_fonte`), `periodos_em_falta`,
    e os três sinalizadores `parada`, `recolha_velha` e `fonte_parou`.
    """
    serie = idade_fonte(ultima_observacao, limite_dias, hoje=hoje)
    recolha = idade_fonte(recolhido_em, limite_dias, hoje=hoje)

    periodos = None
    if serie["dias"] is not None and cadencia_dias > 0:
        periodos = max(int(serie["dias"] // cadencia_dias), 0)

    return {
        "serie": serie,
        "recolha": recolha,
        "periodos_em_falta": periodos,
        "cadencia_dias": cadencia_dias,
        "parada": bool(serie["desatualizada"]),
        "recolha_velha": bool(recolha["desatualizada"]),
        # A recolha é recente e a série está parada: a falha é da fonte, não de
        # quem recolhe. É o caso de hoje, e o que o aviso antigo não via.
        "fonte_parou": bool(serie["desatualizada"] and not recolha["desatualizada"]),
    }


def fim_do_periodo(periodo):
    """
    Último dia do período, na codificação do Eurostat.

    Aceita `'2026'` (anual), `'2026-06'` ou `'2026M06'` (mensal), `'2026-S1'`
    (semestral) e `'2026-Q2'` (trimestral). Devolve None se não reconhecer,
    e quem chama trata isso como “não sei”, nunca como “está velho”.

    Toma-se o **fim** do período, e não o início, por ser a leitura mais
    favorável à fonte: uma série mensal de junho não é acusada de ter trinta
    dias a mais do que tem.
    """
    texto = str(periodo).strip().upper()
    if not texto:
        return None

    if _re.fullmatch(r"\d{4}", texto):
        return _date(int(texto), 12, 31)

    for padrao, meses in ((r"(\d{4})-?M?(\d{1,2})", 1),
                          (r"(\d{4})-?Q(\d)", 3),
                          (r"(\d{4})-?S(\d)", 6)):
        m = _re.fullmatch(padrao, texto)
        if not m:
            continue
        ano, indice = int(m.group(1)), int(m.group(2))
        mes = indice * meses
        if not 1 <= mes <= 12:
            return None
        return _date(ano, mes, _calendar.monthrange(ano, mes)[1])

    return None


def frescura_das_series(series, hoje=None) -> pd.DataFrame:
    """
    Diz, para cada série obtida por API, se ela ainda está a avançar.

    O **D4** criou `idade_fonte()` e aplicou-o ao SOFI e ao Observatório, com o
    argumento de que são as fontes sem API, as que ninguém atualiza se ninguém
    se lembrar. A conclusão implícita, de que as fontes com API não têm esse
    problema porque a rede avisaria, estava errada: uma série **arquivada**
    responde com HTTP 200, devolve dados bem formados e simplesmente não avança.
    Foi assim que a aplicação apresentou dezembro de 2025 durante sete meses
    (auditoria de 11.08.2026, E1 e E3).

    `series` é uma lista de dicionários com `serie`, `periodo`, `limite_dias`,
    `cadencia` e `conjunto`. O limite de cada uma é o seu **desfasamento normal
    de publicação mais um ciclo**, não um prazo uniforme, que acusaria de velhas
    as fontes que são lentas por construção, como as Contas Nacionais.
    """
    linhas = []
    for s in series:
        data = fim_do_periodo(s.get("periodo"))
        idade = idade_fonte(data, int(s["limite_dias"]), hoje=hoje)
        linhas.append({
            "serie": s["serie"],
            "conjunto": s.get("conjunto", ""),
            "cadencia": s.get("cadencia", ""),
            "periodo": s.get("periodo"),
            "dias": idade["dias"],
            "limite_dias": idade["limite_dias"],
            "porque": s.get("porque", ""),
            "desatualizada": idade["desatualizada"],
            # Um período ilegível não é acusação de nada, mas também não é
            # confirmação: fica assinalado para não passar por verificado.
            "verificada": data is not None,
        })
    return pd.DataFrame(linhas)


# --------------------------------------------------------------------------
# Coeficiente de Engel
# --------------------------------------------------------------------------
def intervalo_engel(engel_cn: dict | None) -> dict:
    """
    Coeficiente de Engel nas duas bases oficiais, como intervalo.

    A aplicação tinha os dois valores no mesmo ecrã sem os relacionar: 16,4%
    das Contas Nacionais no cartão, 12,0% do IDF na tabela por quintil logo
    abaixo (auditoria de 10.08.2026, B4). São a mesma grandeza conceptual
    medida em duas bases que divergem, a mesma divergência que já leva a
    aplicação a apresentar a âncora como intervalo, e não como ponto.

    Não é uma discrepância pequena. Por agregado e por ano, em 2022:

    ==========================  =================  =========  ======
    ..                          Contas Nacionais         IDF   rácio
    ==========================  =================  =========  ======
    Despesa alimentar                    6 659 €    2 872 €     2,32
    Despesa total                       40 670 €   23 900 €     1,70
    ==========================  =================  =========  ======

    O Engel diverge porque o numerador diverge **mais** do que o denominador.

    O limite inferior é a constante publicada pelo INE, a mesma que alimenta a
    coluna “Peso no orçamento” da tabela por quintil, para que o número da
    tabela seja reconhecível como o extremo do intervalo em vez de o contrariar.

    `engel_cn` é a entrada de `dados["engel"]["PT"]`, ou None se a ligação
    falhou. Devolve `{minimo, maximo, so_idf, idf, contas, ano_contas}`; com
    `so_idf=True` quando só há a base do IDF.
    """
    idf = float(IDF_PESO_ALIMENTAR["total"])
    if not engel_cn or engel_cn.get("quota") is None:
        return {"minimo": idf, "maximo": idf, "so_idf": True,
                "idf": idf, "contas": None, "ano_contas": None}

    contas = float(engel_cn["quota"])
    return {"minimo": min(idf, contas), "maximo": max(idf, contas),
            "so_idf": False, "idf": idf, "contas": contas,
            "ano_contas": engel_cn.get("ano")}


# --------------------------------------------------------------------------
# Denominador da âncora
# --------------------------------------------------------------------------
def agregados_do_ano(serie: dict, ano) -> dict:
    """
    Número de agregados familiares a usar como denominador para um dado ano.

    O denominador tem de ser do **mesmo ano do numerador**. A despesa das Contas
    Nacionais é de 2022; dividi-la pelos agregados de 2025 dá um valor 9,1%
    mais baixo por razão nenhuma, a população de agregados cresceu, a despesa
    não a acompanhou porque é de outro ano (auditoria de 10.08.2026, B2).

    `serie` é um dicionário ano (texto) → número de agregados. Prefere o ano
    pedido; se não existir, o mais próximo, declarando o desfasamento. Sem série
    disponível, recorre aos Censos.

    Devolve `{valor, ano, fonte, desfasamento}`, `desfasamento` em anos, para
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

    **Cobertura declarada.** Se uma classe não vier do Eurostat, o seu peso é
    zero, sai do denominador, e as restantes absorvem 100% da despesa, cada
    uma com uma quota inflacionada, e sem aviso nenhum. É o mesmo modo de falha
    que o C3 fechou no Törnqvist, e continuava aberto no cálculo mais central da
    aplicação (auditoria de 11.08.2026, E10). As classes em falta ficam em
    `df.attrs["classes_sem_ponderador"]` e `["classes_sem_variacao"]`, para a
    interface as poder declarar.
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
            # Designação do INE para a COICOP 2018. A forma curta serve os
            # cartões; a oficial tem de acompanhar a tabela e as exportações,
            # que saem da aplicação e circulam sozinhas.
            "classe_oficial": classe["oficial"],
            "cor": classe["cor"],
            "ponderador": peso,
            "quota": quota,
            "valor": valor,
            "variacao": var,
            "contributo": contributo,
            "iva_defeito": classe["iva"],
        })

    df = pd.DataFrame(linhas)
    df.attrs["classes_sem_ponderador"] = [
        l["codigo"] for l in linhas if not l["ponderador"] > 0]
    df.attrs["classes_sem_variacao"] = [
        l["codigo"] for l in linhas if l["variacao"] is None]
    return df


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
            # A classe que **mais pesou**, em valor absoluto, e não a de maior
            # contributo com sinal. Num período de deflação alimentar todos os
            # contributos são negativos, e o `idxmax` devolvia a classe que
            # menos contribuiu para a descida, apresentada como “Maior
            # contributo” (auditoria de 12.08.2026, M2). Com todos positivos, o
            # resultado é o mesmo de antes.
            resultado["maior"] = com_dados.loc[
                com_dados["contributo"].abs().idxmax()].to_dict()

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
    concreta (dois adultos, cinco adultos), a multiplicação conta o país
    inteiro como se fosse todo composto dessa maneira, e o total nacional passa
    a depender de um parâmetro de leitura. O erro mede-se: −14% para dois
    adultos, +92% para cinco (auditoria de 10.08.2026, A3). Os restantes campos
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
# alimentação as economias de escala são bem mais fracas, não se partilha uma
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
        "nota": "Norma da UE para rendimento; subestima o custo alimentar em ~10%.",
    },
}


def _racio_previsto(escala: dict, composicao) -> float:
    """Rácio de despesa entre “2 ou +” e “1 adulto” que a escala prevê."""
    return sum(fracao * (escala["primeiro"] + escala["adulto"] * (adultos - 1))
               for adultos, fracao in composicao)


def sensibilidade_escalas(cenarios=None) -> pd.DataFrame:
    """
    Testa se as conclusões do teste das escalas dependem do pressuposto dos
    **3,288 adultos** no grupo “3 ou mais”.

    Esse número foi deduzido admitindo que o quadro Q.2.8 do IDF usa a escala
    OCDE modificada, e é depois usado para avaliar as três escalas, incluindo a
    modificada. A circularidade é real e tem de estar declarada ao lado do
    resultado, não só num comentário (auditoria de 10.08.2026, D3).

    Declará-la não basta: interessa saber **se as conclusões sobrevivem**. Esta
    função recalcula tudo para vários valores plausíveis. Uma linha por cenário,
    com o desvio de cada escala na alimentação, qual delas fica mais próxima do
    observado, e se o controlo da despesa total continua a inverter o sinal.
    """
    if cenarios is None:
        cenarios = [3.0, 3.1, 3.2, ESCALAS_TESTE_COMPOSICAO[1][0], 3.4, 3.5, 3.7]

    fracao_3mais = ESCALAS_TESTE_COMPOSICAO[1][1]
    fracao_2 = ESCALAS_TESTE_COMPOSICAO[0][1]
    linhas = []
    for n3 in cenarios:
        comp = [(ESCALAS_TESTE_COMPOSICAO[0][0], fracao_2), (n3, fracao_3mais)]
        desvios = {}
        for chave, e in ESCALAS.items():
            previsto = _racio_previsto(e, comp)
            if previsto <= 0:
                continue
            desvios[chave] = {
                "alimentar": (ESCALAS_TESTE_RACIO["alimentar"] / previsto - 1) * 100,
                "total": (ESCALAS_TESTE_RACIO["total"] / previsto - 1) * 100,
            }
        if not desvios:
            continue
        mais_proxima = min(desvios, key=lambda c: abs(desvios[c]["alimentar"]))
        mod = desvios.get("ocde_modificada", {})
        linha = {
            "adultos_3mais": n3,
            "e_o_pressuposto": abs(n3 - ESCALAS_TESTE_COMPOSICAO[1][0]) < 1e-9,
            "mais_proxima": mais_proxima,
            "modificada_subestima": mod.get("alimentar", 0) > 0,
            "controlo_inverte": (mod.get("alimentar", 0) > 0
                                 and mod.get("total", 0) < 0),
        }
        for chave, d in desvios.items():
            linha[f"desvio_{chave}"] = d["alimentar"]
        linhas.append(linha)
    return pd.DataFrame(linhas)


def pontos_de_rutura_das_escalas(limites=(2.0, 8.0)) -> dict:
    """
    Onde é que as conclusões do teste das escalas mudariam, em número de adultos
    do grupo “3 ou mais”.

    Estes dois valores apareciam **inscritos à mão** na interface, “3,58” e
    “4,5”, ao lado de números calculados em direto, sem que o leitor os
    distinguisse. São resultado de bissecção sobre constantes que a aplicação
    já tem, pelo que não há razão para os fixar (auditoria de 11.08.2026, E9).

    Devolve `{ultrapassagem, anulacao}`, em adultos:

    - `ultrapassagem`, a partir de onde a OCDE modificada passaria a estar mais
      perto do observado do que a original;
    - `anulacao`, onde o desvio da modificada se anularia.

    Cada um é None se não houver mudança de sinal dentro de `limites`.
    """
    fracao_2, fracao_3mais = (ESCALAS_TESTE_COMPOSICAO[0][1],
                              ESCALAS_TESTE_COMPOSICAO[1][1])
    n2 = ESCALAS_TESTE_COMPOSICAO[0][0]
    observado = ESCALAS_TESTE_RACIO["alimentar"]

    def _desvio(escala, n3):
        previsto = _racio_previsto(ESCALAS[escala], [(n2, fracao_2), (n3, fracao_3mais)])
        return (observado / previsto - 1) * 100 if previsto > 0 else float("nan")

    def _bisseccao(f):
        a, b = limites
        fa, fb = f(a), f(b)
        if not (fa < 0 < fb or fb < 0 < fa):
            return None
        for _ in range(80):
            m = (a + b) / 2
            if (f(a) < 0) == (f(m) < 0):
                a = m
            else:
                b = m
        return (a + b) / 2

    return {
        # a modificada passa à frente quando o seu erro absoluto iguala o da original
        "ultrapassagem": _bisseccao(
            lambda n: abs(_desvio("ocde_original", n)) - abs(_desvio("ocde_modificada", n))),
        "anulacao": _bisseccao(lambda n: _desvio("ocde_modificada", n)),
    }


def testar_escalas() -> pd.DataFrame:
    """
    Confronta o rácio de despesa que cada escala prevê com o observado no IDF,
    para a alimentação e (como controlo) para a despesa total.

    Uma linha por escala. `desvio_alimentar` positivo significa que a escala
    **subestima** o custo alimentar de agregados maiores: o observado é maior do
    que o previsto.

    O pressuposto dos 3,288 adultos no grupo “3 ou mais” é circular, ver
    `sensibilidade_escalas`, que mede se as conclusões dependem dele.
    """
    linhas = []
    for chave, e in ESCALAS.items():
        # Rácio previsto entre “2 ou +” e “1 adulto”, para a composição do IDF.
        previsto = _racio_previsto(e, ESCALAS_TESTE_COMPOSICAO)
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

    O agregado médio é modelado com `dimensao_media` pessoas adultas, é uma
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
# Cabaz por quintil de rendimento, ponderação IDF
# --------------------------------------------------------------------------
# Aqui os ponderadores são do IDF, não do IHPC. São coisas diferentes e a
# escolha não é indiferente: entre as duas estruturas o desvio médio absoluto
# dentro da alimentação é de 1,9 p.p. e o máximo de 4,9 p.p. (pão e cereais).
# Ver a nota em `config.py` sobre a inclusão de turistas no IHPC.
#
# Regra de apresentação, deliberada: a taxa de inflação por quintil **nunca**
# deve aparecer sem a exposição orçamental ao lado. A amplitude entre quintis é
# de cerca de 0,2 p.p., lida isolada, sugere que a inflação alimentar é
# distributivamente neutra. Não é: o efeito regressivo está na exposição
# (14,8% do orçamento no 1.º quintil contra 9,1% no 5.º), não na taxa. Por
# isso as duas colunas saem da mesma função e devem ser mostradas juntas.

def cabaz_quintis(variacoes: dict[str, float]) -> pd.DataFrame:
    """
    Uma linha por quintil de rendimento, com o nível da despesa alimentar, a
    exposição orçamental e a inflação que resulta da estrutura de consumo desse
    quintil.

    Os níveis são os do IDF 2022/2023 tal como medidos, não são reescalados
    para a âncora escolhida na aplicação. Reescalar exigiria assumir que o
    sub-reporte do inquérito é uniforme entre quintis, e nada o sustenta.
    """
    linhas = []
    sem_variacao = []
    for chave, nome in IDF_QUINTIS.items():
        alimentar_ano = float(IDF_ALIMENTAR_QUINTIL[chave])
        mensal = alimentar_ano / 12

        # Denominador da cobertura: a soma das nove classes, e **não** o total
        # publicado. Os dois diferem até 1 €/ano por arredondamento do próprio
        # quadro do INE, e essa diferença não é falta de cobertura.
        total_classes = sum(float(IDF_CLASSES_QUINTIL[c["cod"]][chave]) for c in CLASSES)

        soma_pesos, soma_ponderada, agravamento = 0.0, 0.0, 0.0
        for classe in CLASSES:
            cod = classe["cod"]
            peso = float(IDF_CLASSES_QUINTIL[cod][chave])
            var = variacoes.get(cod)
            if var is None or pd.isna(var):
                if cod not in sem_variacao:
                    sem_variacao.append(cod)
                continue
            soma_pesos += peso
            soma_ponderada += peso * float(var)
            valor_classe = mensal * peso / alimentar_ano if alimentar_ano else 0.0
            if (1 + var / 100) != 0:
                agravamento += valor_classe * (var / 100) / (1 + var / 100)

        inflacao = soma_ponderada / soma_pesos if soma_pesos > 0 else None
        total_mensal = float(IDF_DESPESA_TOTAL[chave]) / 12
        # Fração da despesa alimentar do quintil efetivamente coberta pelas
        # classes com variação disponível. Sem isto, um agravamento parcial era
        # dividido por um orçamento completo e a coluna “Agravamento /
        # orçamento” subestimava sem o dizer, logo na coluna que fecha o
        # argumento sobre a regressividade (auditoria de 11.08.2026, E11).
        cobertura = soma_pesos / total_classes if total_classes else 0.0

        # O agravamento em euros é *maior* nos quintis de cima, gastam mais em
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
            "cobertura": cobertura,
        })

    df = pd.DataFrame(linhas)
    df.attrs["classes_sem_variacao"] = sem_variacao
    df.attrs["cobertura_minima"] = float(df["cobertura"].min()) if not df.empty else 0.0
    return df


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
                "cor": classe["cor"],
                "quintil": chave,
                "quintil_nome": nome,
                "mensal": valor / 12,
                "quota": valor / total if total else 0.0,
            })

    return pd.DataFrame(linhas)


# --------------------------------------------------------------------------
# Viés de substituição, Laspeyres de cabaz fixo contra Törnqvist
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
# exato, é a melhor aproximação possível sem microdados de despesa anuais.

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
                       pesos_por_ano: pd.DataFrame,
                       ano_base: int | None = None) -> pd.DataFrame:
    """
    Uma linha por dezembro, com os três índices em base 100 no ano-base.
    Devolve DataFrame vazio se não houver anos que cheguem, são precisos pelo
    menos dois elos para haver o que comparar.

    `ano_base` é o dezembro a partir do qual os índices são encadeados. Por
    omissão usa `ANO_BASE_VIES`, fixado em `config.py`; se esse ano não estiver
    disponível nos dados, recorre ao primeiro que esteja. Era o primeiro ano da
    janela pedida ao Eurostat, que desliza a cada 1 de janeiro, e com ele
    deslizava o valor publicado do viés, sem que ninguém o decidisse
    (auditoria de 11.08.2026, E14).
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

    # Restringir às **classes** com série completa, não aos **anos** completos.
    # `dropna()` sem argumentos elimina a linha inteira: bastava uma das nove
    # classes não ter observação em dezembro de um ano para esse ano
    # desaparecer da série, sem aviso nenhum. Perder uma classe custa um pouco
    # de cobertura; perder um ano parte a cadeia do índice
    # (auditoria de 10.08.2026, C3).
    dez, w = dez[codigos], w[codigos]
    completas = [c for c in codigos if dez[c].notna().all() and w[c].notna().all()]
    excluidas = [c for c in codigos if c not in completas]
    if len(completas) < 2:
        return pd.DataFrame()
    dez, w = dez[completas], w[completas]
    if dez.empty or w.empty:
        return pd.DataFrame()

    # Quotas normalizadas dentro da alimentação, os ponderadores do IHPC somam
    # 1 000 sobre todo o cabaz do índice, não sobre as nove classes.
    quotas = w.div(w.sum(axis=1), axis=0)

    # Basta existir o ponderador do próprio ano. Para o último elo o ponderador
    # de y+1 ainda não foi publicado, nesse caso repete-se o de y, o que
    # equivale a assumir estrutura constante no último ano. É o único elo
    # afetado e o efeito é de segunda ordem.
    anos = [a for a in dez.index if a in quotas.index]
    if len(anos) < 2:
        return pd.DataFrame()

    # Ano-base fixo, e não o primeiro da janela pedida. Se o ano fixado não
    # estiver nos dados, recorre-se ao primeiro disponível e declara-se.
    alvo = ANO_BASE_VIES if ano_base is None else int(ano_base)
    base = alvo if alvo in anos else anos[0]
    anos = [a for a in anos if a >= base]
    if len(anos) < 2:
        return pd.DataFrame()
    # O ponderador que representa **dezembro de `base`** é o do ano `base + 1`,
    # pela mesma definição que o Törnqvist já respeitava algumas linhas abaixo:
    # o Documento Metodológico do IPC fixa que a estrutura de ponderação se
    # refere a dezembro do ano n−1.
    #
    # Usava-se aqui `quotas.loc[base]`, que se refere a dezembro de `base − 1`.
    # O mesmo dezembro-base ficava representado por dois vetores de ponderadores
    # diferentes, com um ano de intervalo, nos dois índices cuja diferença é
    # precisamente o que este painel mede. Medido sobre os dezembros de 2020 a
    # 2025: viés acumulado de 0,590 pontos com o ponderador errado contra 0,461
    # com o certo, **22% do número apresentado era o artefacto**
    # (auditoria de 11.08.2026, E4).
    quotas_base = quotas.loc[base + 1] if (base + 1) in quotas.index else quotas.loc[base]

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
    # Quais as classes deixadas de fora, para a interface o poder declarar em
    # vez de o silenciar.
    df.attrs["classes_usadas"] = completas
    df.attrs["classes_excluidas"] = excluidas
    df.attrs["ano_base"] = base
    df.attrs["ano_base_pedido"] = alvo
    return df


# --------------------------------------------------------------------------
# Quanto de cada classe segue cada taxa de IVA
# --------------------------------------------------------------------------
def composicao_iva(pesos_sub: dict[str, float]) -> pd.DataFrame:
    """
    Reparte o ponderador de cada classe pelas taxas de IVA das suas subclasses.

    Fecha a lacuna que o **D2** deixou aberta. O `IVA_MAPA` diz *o quê* dentro de
    cada classe segue taxa diferente da predefinida; isto diz *quanto*, usando os
    ponderadores a cinco e seis dígitos que a COICOP 2018 passou a publicar.

    `pesos_sub` é `{código de subclasse: ponderador}`. Uma linha por classe, com
    o peso a cada taxa e a parcela **indeterminada**, as subclasses que
    atravessam taxas em proporção não repartível. Essa parcela não é escondida
    nem arbitrada: é apresentada como tal.

    Em `df.attrs`, `cobertura` é a fração do ponderador da classe que as
    subclasses conhecidas explicam, serve para detetar componentes em falta.
    """
    def _peso(spec) -> float:
        if isinstance(spec, str):
            return float(pesos_sub.get(spec) or 0.0)
        pai, filhos = spec
        resto = float(pesos_sub.get(pai) or 0.0) - sum(
            float(pesos_sub.get(f) or 0.0) for f in filhos)
        return max(resto, 0.0)

    linhas = []
    for classe in CLASSES:
        cod = classe["cod"]
        componentes = IVA_COMPONENTES.get(cod, [])
        por_taxa = {6: 0.0, 13: 0.0, 23: 0.0}
        # `certa` é o que resiste a qualquer leitura; `predominante` é uma
        # atribuição por juízo sobre a rubrica, e tem de ser separável para que
        # a banda de sensibilidade a possa cobrir (auditoria de 12.08.2026, F4).
        certa = {6: 0.0, 13: 0.0, 23: 0.0}
        indeterminado, predominante = 0.0, 0.0
        # Imposto contido na parcela indeterminada, nos três cenários. Guardar o
        # imposto e não a taxa é o que permite que cada componente tenha o **seu**
        # intervalo legal: os cereais de pequeno-almoço estão entre 13% e 23%,
        # não entre 6% e 23% como todos os outros (auditoria de 12.08.2026, G1).
        indet_contido = {"min": 0.0, "max": 0.0, "predefinida": 0.0}
        for comp in componentes:
            p = _peso(comp["peso"])
            if p <= 0:
                continue
            if comp["taxa"] is None:
                indeterminado += p
                lo, hi = comp.get("entre", (6, 23))
                # A taxa central é a predefinida do grupo **confinada ao
                # intervalo legal**, nunca um valor que a lei não admite.
                central = min(max(int(classe["iva"]), lo), hi)
                indet_contido["min"] += p * (lo / 100) / (1 + lo / 100)
                indet_contido["max"] += p * (hi / 100) / (1 + hi / 100)
                indet_contido["predefinida"] += p * (central / 100) / (1 + central / 100)
                continue
            por_taxa[comp["taxa"]] = por_taxa.get(comp["taxa"], 0.0) + p
            if comp["certeza"] == "predominante":
                predominante += p
            else:
                certa[comp["taxa"]] = certa.get(comp["taxa"], 0.0) + p

        total = sum(por_taxa.values()) + indeterminado
        publicado = float(pesos_sub.get(cod) or 0.0)
        linhas.append({
            "codigo": cod,
            "classe": classe["nome"],
            "iva_defeito": classe["iva"],
            "peso": total,
            "peso_publicado": publicado,
            "taxa_6": por_taxa[6],
            "taxa_13": por_taxa[13],
            "taxa_23": por_taxa[23],
            "indeterminado": indeterminado,
            "por_predominancia": predominante,
            "certa_6": certa[6],
            "certa_13": certa[13],
            "certa_23": certa[23],
            "indet_contido_min": indet_contido["min"],
            "indet_contido_max": indet_contido["max"],
            "indet_contido_predef": indet_contido["predefinida"],
            # Fração da classe que segue efetivamente a taxa predefinida,
            # é o número que diz se a predefinição é boa aproximação ou não.
            "na_taxa_predefinida": por_taxa.get(classe["iva"], 0.0),
        })

    df = pd.DataFrame(linhas)
    if df.empty:
        return df
    for col in ("taxa_6", "taxa_13", "taxa_23", "indeterminado",
                "na_taxa_predefinida", "por_predominancia"):
        df[f"{col}_pct"] = np.where(df["peso"] > 0, df[col] / df["peso"] * 100, np.nan)
    df.attrs["cobertura"] = (float(df["peso"].sum() / df["peso_publicado"].sum())
                             if df["peso_publicado"].sum() > 0 else 0.0)
    return df


def resumo_composicao_iva(df: pd.DataFrame) -> dict:
    """
    Agrega a composição por taxa ao nível do cabaz alimentar, e confronta-a com
    o que a simulação por classe assume.

    O simulador aplica **uma taxa por classe**, é o que a decomposição permite.
    Isso equivale a assumir que toda a despesa da classe segue a taxa
    predefinida. Este resumo mede o erro dessa aproximação, que é o que faltava
    para se poder dizer se ela é aceitável.
    """
    if df.empty:
        return {}

    total = float(df["peso"].sum())
    if total <= 0:
        return {}

    indet = float(df["indeterminado"].sum())
    base_defeito = float(
        df.apply(lambda r: r["peso"] if r["iva_defeito"] == 6 else 0.0, axis=1).sum())

    # ------------------------------------------------------------------
    # IVA contido na despesa, em fração do preço com imposto.
    #
    # É este o número que diz em que **direção** a aproximação por classe erra,
    # e a direção não é sempre a mesma. Comparar apenas a base à taxa reduzida
    # dava a impressão de que o simulador sobrestima sempre, e não é verdade:
    # num cenário de isenção total ele **subestima**, porque credita a
    # pastelaria, a charcutaria e os hortícolas transformados com 6% quando
    # suportam 23%.
    # ------------------------------------------------------------------
    def _contido(taxa, peso):
        return peso * (taxa / 100) / (1 + taxa / 100)

    iva_modelo = sum(_contido(r["iva_defeito"], r["peso"]) for _, r in df.iterrows())
    iva_certo = sum(_contido(6, r["taxa_6"]) + _contido(13, r["taxa_13"])
                    + _contido(23, r["taxa_23"]) for _, r in df.iterrows())
    # Os extremos da parcela indeterminada respeitam o intervalo legal de cada
    # componente, não são 6% e 23% para todos.
    if "indet_contido_min" in df.columns:
        iva_indet_min = float(df["indet_contido_min"].sum())
        iva_indet_max = float(df["indet_contido_max"].sum())
    else:
        iva_indet_min = sum(_contido(6, r["indeterminado"]) for _, r in df.iterrows())
        iva_indet_max = sum(_contido(23, r["indeterminado"]) for _, r in df.iterrows())

    # Intervalo do que está à taxa reduzida: o mínimo é o apurado; o máximo
    # admite que toda a parcela indeterminada lá cai.
    minimo_6 = float(df["taxa_6"].sum())
    return {
        # --- IVA contido, em fração do preço com imposto ---
        "iva_modelo_pct": iva_modelo / total * 100,
        "iva_apurado_min_pct": (iva_certo + iva_indet_min) / total * 100,
        "iva_apurado_max_pct": (iva_certo + iva_indet_max) / total * 100,
        "total": total,
        "taxa_6": minimo_6,
        "taxa_13": float(df["taxa_13"].sum()),
        "taxa_23": float(df["taxa_23"].sum()),
        "indeterminado": indet,
        "indeterminado_pct": indet / total * 100,
        "taxa_6_pct": minimo_6 / total * 100,
        "taxa_13_pct": float(df["taxa_13"].sum()) / total * 100,
        "taxa_23_pct": float(df["taxa_23"].sum()) / total * 100,
        # O que a simulação por classe assume estar a 6%
        "assumido_6_pct": base_defeito / total * 100,
        # ... contra o intervalo apurado
        "apurado_6_min_pct": minimo_6 / total * 100,
        "apurado_6_max_pct": (minimo_6 + indet) / total * 100,
        "por_predominancia_pct": float(df["por_predominancia"].sum()) / total * 100,
    }


def taxas_efetivas(comp: pd.DataFrame, indeterminado: str = "predefinida",
                   predominancia: str = "como_apurado") -> dict:
    """
    Taxa **média efetiva** de IVA de cada classe, apurada a partir da sua
    composição por subclasse.

    Porque é que uma taxa média basta
    ---------------------------------
    Simular escalão a escalão e simular com uma taxa média efetiva dão
    **exatamente o mesmo resultado**, e não é aproximação, é identidade
    algébrica. A base sem imposto de uma classe é ``Σ_b V_b / (1 + t_b)``. Se se
    definir ``t_ef`` de modo a que ``V / (1 + t_ef)`` iguale essa soma, então:

    - a base sem imposto é a mesma, por construção;
    - o efeito mecânico, ``base · (1 + t₁) − V``, depende só da base e da taxa do
      cenário, que é uniforme na classe, logo é o mesmo;
    - o imposto contido no preço novo depende só do valor novo e de ``t₁``.

    Nada no cálculo precisa de saber quantos escalões havia. Por isso a
    aplicação não passou a simular por escalão: passou a usar a taxa que a
    composição implica, o que é o mesmo número com metade da complicação.

    A taxa efetiva **não é uma taxa legal** e ninguém a paga. É a taxa única que
    suporta o mesmo imposto que o conjunto dos produtos da classe.

    Duas hipóteses, e ambas são explícitas
    --------------------------------------
    `indeterminado` decide o destino da parcela não repartível:
    ``"predefinida"`` (o valor central), ``"reduzida"`` ou ``"normal"``.

    `predominancia` decide o destino das parcelas atribuídas **por juízo sobre a
    rubrica** e não por leitura inequívoca das Listas: ``"como_apurado"`` (o
    valor central), ``"reduzida"`` ou ``"normal"``.

    Os extremos das duas são **limites exteriores, não intervalos plausíveis**.
    Nenhuma leitura das Listas põe toda a pastelaria a 6% nem todo o bacalhau
    seco a 23%. Servem para responder à pergunta “e se estas atribuições
    estiverem todas erradas ao mesmo tempo?”, que é a única a que um limite
    exterior responde, e para tornar visível que esta parcela pesa mais do que
    a indeterminada, que já tinha banda enquanto esta não tinha.
    """
    if comp.empty:
        return {}

    destino = {"reduzida": 6, "normal": 23}
    # A parcela indeterminada entra pelo **imposto contido**, não por uma taxa
    # arbitrada: cada componente tem o seu intervalo legal, e há um, os cereais
    # de pequeno-almoço, cujo intervalo não inclui a taxa reduzida.
    coluna_indet = {"reduzida": "indet_contido_min", "normal": "indet_contido_max"}
    tem_indet_contido = "indet_contido_predef" in comp.columns
    taxas = {}
    tem_certa = "certa_6" in comp.columns
    for _, r in comp.iterrows():
        t_indet = destino.get(indeterminado, int(r["iva_defeito"]))
        if predominancia in destino and tem_certa:
            # Só as parcelas de leitura inequívoca ficam onde estão; as de
            # predominância vão todas para o extremo pedido.
            t_pred = destino[predominancia]
            base = {6: float(r["certa_6"]), 13: float(r["certa_13"]),
                    23: float(r["certa_23"])}
            base[t_pred] = base.get(t_pred, 0.0) + float(r["por_predominancia"])
            parcelas = [(t, p) for t, p in base.items()]
        else:
            parcelas = [(6, r["taxa_6"]), (13, r["taxa_13"]), (23, r["taxa_23"])]

        # Imposto contido na parcela indeterminada: pré-calculado por
        # componente, respeitando o intervalo legal de cada um.
        if tem_indet_contido:
            contido_indet = float(r[coluna_indet.get(indeterminado, "indet_contido_predef")])
        else:
            contido_indet = (float(r["indeterminado"]) * (t_indet / 100)
                             / (1 + t_indet / 100))

        peso = sum(p for _, p in parcelas) + float(r["indeterminado"])
        if peso <= 0:
            taxas[r["codigo"]] = float(r["iva_defeito"])
            continue
        # Fração do preço com imposto que é imposto.
        contido = (sum(p * (t / 100) / (1 + t / 100) for t, p in parcelas)
                   + contido_indet) / peso
        # Sem arredondar: qualquer arredondamento aqui quebra a identidade com
        # a simulação escalão a escalão, e é essa identidade que justifica o
        # método. O arredondamento pertence à apresentação, não ao cálculo.
        taxas[r["codigo"]] = contido / (1 - contido) * 100 if contido < 1 else 0.0
    return taxas


def efeito_mecanico_pct(t0: float, t1: float) -> float:
    """
    Variação percentual do preço final com **repercussão integral**, ao passar da
    taxa `t0` para a taxa `t1` (ambas em pontos percentuais).

        (1 + t₁) / (1 + t₀) − 1

    É a mesma definição que o Banco de Portugal usa para o “impacto mecânico”
    (WAPP de 22.11.2023, p. 5), e serve para dois fins: derivar a repercussão a
    partir dos valores publicados, e confirmar que a aritmética de imposto desta
    aplicação coincide com a do BdP, para os óleos alimentares (23% → 0%) tem
    de dar os −18,70% que o BdP publica.
    """
    return ((1 + t1 / 100) / (1 + t0 / 100) - 1) * 100


def estimativas_repercussao() -> pd.DataFrame:
    """
    A repercussão implícita em cada estimativa publicada pelo Banco de Portugal
    sobre o “IVA zero” de 2023.

    O BdP publica a variação **observada** e a variação **mecânica** (a que
    haveria com repercussão integral). A repercussão é o quociente:

        ρ = variação observada / variação mecânica

    Nenhum dos ρ desta tabela é citado, todos são derivados aqui, dos dois
    números publicados. A coluna `rho` é, portanto, um cálculo desta aplicação
    sobre dados do BdP, e não uma estimativa do BdP.

    Nota sobre a diluição: as rubricas do IHPC incluem bens não abrangidos pela
    medida, o que atenua tanto o observado como o mecânico. Como atenua os dois
    na mesma proporção, **o quociente sobrevive**, é a razão pela qual esta
    derivação é legítima apesar da granularidade insuficiente que o BdP assinala.
    """
    linhas = []
    for rot, obs, mec, nota in REPERCUSSAO_ESTIMATIVAS:
        linhas.append({
            "estimativa": rot,
            "observado": obs,
            "mecanico": mec,
            "rho": obs / mec if mec else float("nan"),
            "nota": nota,
        })
    return pd.DataFrame(linhas)


def repercussao_banda() -> tuple[float, float, float]:
    """`(mínimo, central, máximo)` da repercussão, tal como calibrada no config."""
    lo, hi = REPERCUSSAO_BANDA
    return float(lo), float(REPERCUSSAO_PADRAO), float(hi)


def comparar_ponderadores(pesos_ihpc: dict[str, float],
                          variacoes: dict[str, float]) -> dict:
    """
    Confronta as duas estruturas de ponderação na única grandeza em que a
    escolha é observável: a inflação alimentar nacional que cada uma produz.

    Serve de diagnóstico no separador de metodologia, quantifica o que se
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
        {"codigo": c["cod"], "classe": c["nome"],
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
