"""
Despesa alimentar — ferramenta de análise
UPE · DSSD · Secretaria-Geral do Governo

Executar localmente:   streamlit run app.py
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pathlib import Path

from src import eurostat, observatorio
from src.calculos import (ESCALAS, agregados_do_ano, cabaz_quintis,
                          comparar_ponderadores, composicao_iva,
                          composicao_quintis, decompor, despesa_do_agregado,
                          escala_mais_proxima, frescura_das_series,
                          frescura_do_observatorio,
                          idade_fonte, indices_comparados,
                          intervalo_agregado, intervalo_engel,
                          pontos_de_rutura_das_escalas,
                          efeito_mecanico_pct, estimativas_repercussao,
                          repercussao_banda,
                          resumo_composicao_iva, resumo_decomposicao, resumo_iva,
                          sensibilidade_escalas, simular_iva, taxas_efetivas,
                          testar_escalas, unidades_equivalentes)
from src.config import (AGREGADOS, AGREGADOS_CENSOS, AGREGADOS_FONTE,
                        BASE_POR_DEFEITO, BASES_ANCORA, COD_AGREGADOS,
                        DIMENSAO_RECUO, DIMENSAO_RECUO_FONTE,
                        ESCALAS_TESTE_COMPOSICAO, ESCALAS_TESTE_FONTE,
                        ESCALAS_TESTE_INTERVALO, ESCALAS_TESTE_RACIO,
                        IVA_COMPONENTES, IVA_COMPONENTES_FONTE,
                        AT_FICHAS, PRINCIPIO_LISTA_TAXATIVA,
                        IVA_MAPA, IVA_MAPA_FONTE, IVA_SUBCLASSES,
                        IVA_ZERO_AFETACAO_ORCAMENTAL, IVA_ZERO_INFLACAO_QUINTIL,
                        IVA_ZERO_QUINTIS_FONTE,
                        REPERCUSSAO_BANDA, REPERCUSSAO_FONTE, REPERCUSSAO_PADRAO,
                        IDF_ALIMENTAR_ANUAL, IDF_FONTE,
                        IDF_JANELA_FONTE, IDF_JANELA_RECOLHA,
                        IDF_PESO_ALIMENTAR, IDF_QUINTIS,
                        LIMITE_ANOS_SOFI, LIMITE_DIAS_OBSERVATORIO,
                        LIMITES_FRESCURA,
                        SOFI_CUSTO, SOFI_FONTE, SOFI_INCAPACIDADE, SOFI_MILHOES,
                        ANO_BASE_VIES,
                        AZUL, CINZENTO, CLASSES, CLASSES_FONTE, CODIGOS,
                        COICOP_ALIMENTAR, DOURADO,
                        PAISES, PAISES_POR_DEFEITO, POR_CODIGO, RODAPE,
                        UNIDADE, VERDE, VERMELHO,
                        euro, mes_pt, milhoes, numero, percentagem, pontos)

LOGO = ""
try:
    LOGO = (Path(__file__).parent / "src" / "logo_b64.txt").read_text().strip()
except Exception:                                          # noqa: BLE001
    LOGO = ""

st.set_page_config(
    page_title="Despesa alimentar — UPE/SGGov",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================================================
# Estilo institucional
# ==========================================================================
st.markdown(f"""
<style>

  .barra {{
    display: flex; align-items: center; gap: 11px;
    background: linear-gradient(120deg, {AZUL} 0%, #1a3f6f 30%, {VERDE} 70%, #0a5228 100%);
    border-bottom: 2px solid {VERMELHO}; border-radius: 8px;
    padding: 9px 15px; margin-bottom: 14px; color: #fff;
  }}
  .barra .sim {{
    width: 32px; height: 32px; border-radius: 50%; background: #fff;
    padding: 1px; flex: 0 0 32px; display: block;
  }}
  .barra .bt {{ display: flex; flex-direction: column; line-height: 1.25; }}
  .barra .bt strong {{ font-size: 11.5px; font-weight: 600; letter-spacing: .45px; }}
  .barra .bt span {{ font-size: 10px; opacity: .85; }}
  .barra .bd {{
    margin-left: auto; font-size: 14px; font-weight: 600; letter-spacing: -.2px;
    padding-left: 13px; border-left: 3px solid {DOURADO};
  }}
  @media (max-width: 640px) {{ .barra .bd {{ display: none; }} }}

  .cartao {{
    background: #fff; border: 1px solid #e2e8f0; border-radius: 11px;
    padding: 13px 15px; box-shadow: 0 1px 3px rgba(23,23,21,.07);
    border-left: 4px solid var(--c); height: 100%;
  }}
  .cartao .topo {{ display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }}
  .cartao .emj {{ font-size: 21px; line-height: 1; }}
  .cartao .nm {{ font-size: 13px; font-weight: 600; line-height: 1.2; }}
  .cartao .cd {{ font-size: 9.5px; color: #6b7280; letter-spacing: .3px; }}
  .cartao .vl {{ font-size: 20px; font-weight: 600; letter-spacing: -.5px; }}
  .cartao .ln {{ display: flex; justify-content: space-between; align-items: baseline;
                 margin-top: 4px; font-size: 11.5px; }}
  .cartao .ct {{ font-size: 10.5px; color: #6b7280; margin-top: 7px;
                 border-top: 1px solid #eef1f4; padding-top: 6px; }}

  .nota {{
    border-left: 3px solid {DOURADO}; background: rgba(190,156,84,.09);
    border-radius: 0 8px 8px 0; padding: 11px 14px; font-size: 13px; margin: 12px 0;
  }}
  .nota .tt {{
    font-size: 10.5px; font-weight: 600; letter-spacing: .9px; text-transform: uppercase;
    color: {DOURADO}; margin-bottom: 4px;
  }}
  .nota.perigo {{ border-left-color: {VERMELHO}; background: rgba(208,33,23,.07); }}
  .nota.perigo .tt {{ color: {VERMELHO}; }}

  [data-testid="stMetricValue"] {{ font-size: 22px; font-weight: 600; }}
  [data-testid="stMetricLabel"] {{ font-size: 12px; }}
  .stTabs [data-baseweb="tab"] {{ font-size: 14px; font-weight: 500; }}
  footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


# ==========================================================================
# Obtenção de dados (executada no servidor — sem restrições de navegador)
# ==========================================================================
@st.cache_data(ttl=6 * 3600, show_spinner=False)
def carregar_dados(anos_historico: int = 6):
    """Obtém tudo o que a aplicação precisa. Em cache durante 6 horas."""
    ano = date.today().year
    # A janela do índice tem de cobrir o **ano-base do painel de viés**, que é
    # fixo em `config.py`. Antes era só `ano − anos_historico`, o que fazia o
    # ano-base deslizar a cada 1 de janeiro (auditoria de 11.08.2026, E14).
    primeiro_ano = min(ano - anos_historico, ANO_BASE_VIES)
    desde_indice = f"{primeiro_ano}-01"
    desde_variacao = f"{ano - 3}-01"

    # Janela generosa para as fontes anuais e semestrais. Custa pouco em volume
    # e garante que, mesmo com atraso de publicação, há sempre uma observação —
    # a aplicação usa depois a mais recente de cada série.
    JANELA = 8

    registo = []
    eurostat.ENDERECOS.clear()

    pesos_df, via1 = eurostat.ponderadores(CODIGOS)
    registo.append(("Ponderadores", via1, len(pesos_df)))

    # Ponderadores das subclasses — é o que permite dizer **quanto** de cada
    # classe segue cada taxa de IVA, e não apenas o quê. Se falhar, o painel
    # respetivo não é apresentado e a aplicação continua: não é dependência
    # de mais nada.
    try:
        sub_df, via15 = eurostat.ponderadores_subclasses(IVA_SUBCLASSES + CODIGOS)
        registo.append(("Ponderadores por subclasse", via15, len(sub_df)))
    except Exception as exc:                                   # noqa: BLE001
        sub_df, via15 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Ponderadores por subclasse", via15, 0))

    indice_df, via2 = eurostat.indice_precos(COICOP_ALIMENTAR, desde_indice)
    registo.append(("Índice de preços", via2, len(indice_df)))

    # Índice por classe — só serve o Törnqvist. Se falhar, a aplicação continua
    # sem esse painel: não é dependência de mais nada.
    try:
        idx_classes_df, via13 = eurostat.indice_classes(CODIGOS, desde_indice)
        registo.append(("Índice de preços por classe", via13, len(idx_classes_df)))
    except Exception as exc:                                   # noqa: BLE001
        idx_classes_df, via13 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Índice de preços por classe", via13, 0))

    var_df, via3 = eurostat.variacoes(
        [COICOP_ALIMENTAR] + CODIGOS, list(PAISES.keys()), desde_variacao
    )

    # Série longa de Portugal, para o gráfico do histórico acompanhar o cursor
    # em toda a janela do índice. Um grupo, um país: pedido barato. Se falhar, a
    # aplicação recorre à série curta e o gráfico continua a funcionar.
    try:
        var_pt_longo, via16 = eurostat.variacoes(
            [COICOP_ALIMENTAR], ["PT"], desde_indice)
        registo.append(("Variação homóloga PT (série longa)", via16, len(var_pt_longo)))
    except Exception as exc:                                   # noqa: BLE001
        var_pt_longo = pd.DataFrame()
        registo.append(("Variação homóloga PT (série longa)", f"indisponível ({exc})", 0))
    registo.append(("Variações e UE-27", via3, len(var_df)))

    # Agregados especiais: separam choque conjuntural de inflação estrutural.
    #
    # A janela é a **do índice**, e não `ano − anos_historico`. É o índice que
    # define as opções do cursor no separador Histórico, e este gráfico é
    # filtrado por esse cursor: pedi-lo com uma janela mais curta deixava doze
    # meses do intervalo escolhido sem dados, em silêncio. É o mesmo defeito que
    # foi corrigido ontem na linha da variação homóloga e que ficou aberto no
    # gráfico logo abaixo (auditoria de 12.08.2026, K5).
    try:
        agr_esp_df, via12 = eurostat.variacoes(
            COD_AGREGADOS, ["PT", "EU27_2020"], desde_indice)
        registo.append(("Agregados especiais do índice", via12, len(agr_esp_df)))
    except Exception as exc:                                   # noqa: BLE001
        agr_esp_df, via12 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Agregados especiais do índice", via12, 0))

    # Âncora oficial em euros — Contas Nacionais (opcional: pode não estar
    # disponível para o último ano; a aplicação funciona sem ela).
    try:
        desp_df, via4 = eurostat.despesa_alimentar(ano - JANELA)
        registo.append(("Despesa alimentar (Contas Nacionais)", via4, len(desp_df)))
    except Exception as exc:                                   # noqa: BLE001
        desp_df, via4 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Despesa alimentar (Contas Nacionais)", via4, 0))

    # Privação alimentar severa — o mais baixo dos três limiares de
    # acessibilidade. Nunca é apresentado sozinho: ver a nota em config.py.
    try:
        priv_df, via14 = eurostat.privacao_alimentar(["PT", "ES", "EU27_2020"], ano - 10)
        registo.append(("Privação alimentar (EU-SILC)", via14, len(priv_df)))
    except Exception as exc:                                   # noqa: BLE001
        priv_df, via14 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Privação alimentar (EU-SILC)", via14, 0))

    try:
        dim_df, via5 = eurostat.dimensao_agregado(ano - JANELA)
        registo.append(("Dimensão média do agregado", via5, len(dim_df)))
    except Exception as exc:                                   # noqa: BLE001
        dim_df, via5 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Dimensão média do agregado", via5, 0))

    try:
        agr_df, via6 = eurostat.numero_agregados(ano - JANELA)
        registo.append(("N.º de agregados familiares", via6, len(agr_df)))
    except Exception as exc:                                   # noqa: BLE001
        agr_df, via6 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("N.º de agregados familiares", via6, 0))

    # Nível de preços comparado — a codificação das categorias das PPP não é a
    # mesma do índice de preços, pelo que se tenta a preferida e depois a
    # reserva. Ambas são alimentares: uma reserva não alimentar invertia a
    # conclusão sem dar erro (auditoria de 10.08.2026, B3). Se nenhuma
    # responder, o painel respetivo não é apresentado.
    pli_df, pli_cat = pd.DataFrame(), None
    for candidato in eurostat.PPP_CATEGORIAS_ALIMENTOS:
        try:
            tentativa, via7 = eurostat.nivel_precos(
                list(PAISES.keys()), candidato, ano - JANELA)
            if not tentativa.empty:
                pli_df, pli_cat = tentativa, candidato
                registo.append((f"Nível de preços ({candidato})", via7, len(tentativa)))
                break
        except Exception:                                      # noqa: BLE001
            continue
    if pli_df.empty:
        registo.append(("Nível de preços comparado", "indisponível", 0))

    # Esforço alimentar — coeficiente de Engel (alimentação / consumo total)
    # Os dois lados do coeficiente de Engel são obtidos em separado: se o
    # agregado total falhar, a despesa alimentar por país continua disponível.
    partes_engel = []
    try:
        tot_df, via8a = eurostat.despesa_total_consumo(list(PAISES.keys()), ano - JANELA)
        registo.append(("Consumo total das famílias", via8a, len(tot_df)))
        partes_engel.append(tot_df)
    except Exception as exc:                                   # noqa: BLE001
        registo.append(("Consumo total das famílias", f"indisponível ({exc})", 0))
    try:
        ali_df, via8b = eurostat.despesa_alimentar_paises(list(PAISES.keys()), ano - JANELA)
        registo.append(("Despesa alimentar por país", via8b, len(ali_df)))
        partes_engel.append(ali_df)
    except Exception as exc:                                   # noqa: BLE001
        registo.append(("Despesa alimentar por país", f"indisponível ({exc})", 0))
    engel_df = pd.concat(partes_engel, ignore_index=True) if len(partes_engel) == 2 else pd.DataFrame()

    try:
        sm_df, via9 = eurostat.salario_minimo(list(PAISES.keys()), ano - JANELA)
        registo.append(("Salário mínimo nacional", via9, len(sm_df)))
    except Exception as exc:                                   # noqa: BLE001
        sm_df, via9 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Salário mínimo nacional", via9, 0))

    # Rendimento das famílias: média e mediana. A média é a coerente com a
    # despesa (que também é uma média); a mediana fica disponível para
    # caracterizar o agregado do meio da distribuição.
    try:
        sme_df, via11 = eurostat.salario_medio(list(PAISES.keys()), ano - JANELA)
        registo.append(("Salário médio líquido", via11, len(sme_df)))
    except Exception as exc:                                   # noqa: BLE001
        sme_df, via11 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Salário médio líquido", via11, 0))

    rend_por_tipo = {}
    for indic, nome_indic in eurostat.RENDIMENTO_INDICADORES.items():
        try:
            df_r, via_r = eurostat.rendimento(list(PAISES.keys()), ano - JANELA, indic)
            registo.append((f"Rendimento {nome_indic} equivalente", via_r, len(df_r)))
            rend_por_tipo[indic] = df_r
        except Exception as exc:                               # noqa: BLE001
            registo.append((f"Rendimento {nome_indic} equivalente",
                            f"indisponível ({exc})", 0))

    # --- ponderadores: ano mais recente de cada classe ---
    #
    # Cada classe contribui com a **sua** última observação, mas o rótulo que a
    # aplicação mostra é o máximo de todas. Se uma classe ficar um ano atrás, a
    # aplicação combina ponderadores de anos diferentes e anuncia um só
    # (auditoria de 12.08.2026, K13).
    #
    # **Não se filtra pelo período comum**, ao contrário do que o diagnóstico
    # recomendava — e a razão é que a alternativa é pior. Deixar cair a classe
    # tira-lhe o ponderador, e as oito restantes absorvem 100 % da despesa: cada
    # quota inflacionada em cerca de 1/8. Usar o ponderador do ano anterior para
    # uma classe introduz um erro de segunda ordem, porque os ponderadores
    # mudam pouco de ano para ano. Mantém-se o recuo, **declara-se o
    # desalinhamento**, que era o que faltava.
    pesos_df = pesos_df.sort_values("time")
    pesos = pesos_df.groupby("coicop")["valor"].last().to_dict()
    ano_pesos = pesos_df["time"].max() if not pesos_df.empty else None
    pesos_desalinhados = {
        c: str(p) for c, p in pesos_df.groupby("coicop")["time"].last().items()
        if str(p) != str(ano_pesos)
    }

    # --- ponderadores por subclasse, do mesmo ano mais recente ---
    pesos_sub, ano_pesos_sub = {}, None
    if not sub_df.empty:
        sub_df = sub_df.sort_values("time")
        ano_pesos_sub = sub_df["time"].max()
        pesos_sub = (sub_df[sub_df["time"] == ano_pesos_sub]
                     .set_index("coicop")["valor"].to_dict())

    # --- variações por classe (Portugal, mês mais recente) ---
    pt_classes = var_df[(var_df["geo"] == "PT") & (var_df["coicop"].isin(CODIGOS))]
    pt_classes = pt_classes.sort_values("time")
    variacoes_classe = pt_classes.groupby("coicop")["valor"].last().to_dict()
    mes_variacoes = pt_classes["time"].max() if not pt_classes.empty else None
    # Mesma questão dos ponderadores, e mesma decisão: uma classe que fique um
    # mês atrás entra com a taxa desse mês em vez de sair do cálculo, mas o
    # desalinhamento passa a ser declarado (auditoria de 12.08.2026, K13).
    variacoes_desalinhadas = {
        c: str(p) for c, p in pt_classes.groupby("coicop")["time"].last().items()
        if str(p) != str(mes_variacoes)
    }

    # --- séries globais de Portugal ---
    if not indice_df.empty:
        # A base do índice mudou ao longo do tempo (2015=100 → 2025=100).
        # Preferir a mais recente disponível; se nenhuma for reconhecida,
        # usar a unidade com mais observações.
        unidades = indice_df["unit"].value_counts()
        preferida = None
        for candidata in ("I25", "I15", "I05", "I96"):
            if candidata in unidades.index:
                preferida = candidata
                break
        if preferida is None:
            preferida = unidades.index[0]
        indice_pt = indice_df[indice_df["unit"] == preferida].sort_values("time")
        base_indice = preferida
    else:
        indice_pt, base_indice = indice_df, None

    # A variação de Portugal tem de cobrir **a mesma janela do índice**, porque é
    # o índice que define as opções do cursor de intervalo no separador Histórico.
    # Vinha de `var_df`, pedido para três anos e muitos países por questão de
    # volume — resultado: arrastar o cursor para trás de janeiro do ano−3 mostrava
    # a linha do índice sem a linha vermelha da variação, sem qualquer aviso
    # (relatado pela utilizadora, 12.08.2026).
    #
    # A série de PT sozinha — um grupo, um país — é barata, e é pedida à parte
    # com a janela do índice. O pedido largo continua a servir a comparação
    # europeia, onde três anos chegam.
    if not var_pt_longo.empty:
        var_pt = var_pt_longo[
            (var_pt_longo["geo"] == "PT")
            & (var_pt_longo["coicop"] == COICOP_ALIMENTAR)].sort_values("time")
    else:
        var_pt = var_df[(var_df["geo"] == "PT") &
                        (var_df["coicop"] == COICOP_ALIMENTAR)].sort_values("time")

    # --- variação homóloga **oficial** do agregado alimentar (CP011) ---
    # É o número que o INE publica e que qualquer pessoa encontra ao verificar.
    # A aplicação apresentava na capa uma taxa **reconstituída** da decomposição,
    # que difere desta em cerca de 0,15 p.p. (auditoria de 12.08.2026, K1).
    # Toma-se o mesmo mês das variações por classe, para que a comparação entre
    # as duas seja do mesmo momento.
    variacao_oficial, mes_var_oficial = None, None
    if not var_pt.empty:
        _cand = var_pt[var_pt["time"] == mes_variacoes] if mes_variacoes else var_pt
        _linha_of = (_cand if not _cand.empty else var_pt).sort_values("time").iloc[-1]
        variacao_oficial = float(_linha_of["valor"])
        mes_var_oficial = str(_linha_of["time"])

    # --- comparação europeia: todos os grupos, todos os países ---
    bench_todos = var_df.sort_values("time")
    bench = var_df[var_df["coicop"] == COICOP_ALIMENTAR].sort_values("time")

    # --- âncora oficial: despesa alimentar por agregado ---
    despesa_ano, despesa_valor = None, None
    if not desp_df.empty:
        recente = desp_df.sort_values("time").iloc[-1]
        despesa_ano, despesa_valor = str(recente["time"]), float(recente["valor"])

    # --- número de agregados: preferir os valores anuais do Eurostat ---
    # Guarda-se a **série inteira**, não só o ano mais recente, porque os dois
    # usos do número de agregados pedem anos diferentes: o denominador da âncora
    # das Contas Nacionais tem de ser do ano da despesa (2022), e a extrapolação
    # nacional do simulador de IVA tem de ser do ano mais recente. Antes havia
    # um único valor a servir os dois (auditoria de 10.08.2026, B2).
    #
    # Verificação de plausibilidade, aplicada observação a observação: um valor
    # fora deste intervalo indica que o conjunto devolvido não é o esperado
    # (dimensão errada, unidade errada, série trocada). Nesse caso recorre-se ao
    # valor censitário, que é seguro.
    agregados_serie: dict[str, int] = {}
    rejeitados = []
    if not agr_df.empty:
        for _, linha in agr_df.sort_values("time").iterrows():
            candidato = int(round(float(linha["valor"]) * 1000))      # vem em milhares
            if 3_000_000 <= candidato <= 6_500_000:
                agregados_serie[str(linha["time"])] = candidato
            else:
                rejeitados.append(candidato)
    if rejeitados:
        registo.append(
            ("N.º de agregados — verificação",
             f"{len(rejeitados)} valor(es) implausível(eis), o primeiro "
             f"{numero(rejeitados[0])}; ignorados", 0)
        )

    agregados_valor, agregados_ano, agregados_fonte = None, None, None
    if agregados_serie:
        agregados_ano = max(agregados_serie)
        agregados_valor = agregados_serie[agregados_ano]
        agregados_fonte = "Eurostat / Inquérito ao Emprego (EU-LFS)"

    dimensao_media, dimensao_ano = None, None
    if not dim_df.empty:
        rec = dim_df.sort_values("time").iloc[-1]
        dimensao_ano, dimensao_media = str(rec["time"]), float(rec["valor"])

    # --- coeficiente de Engel por país, ano mais recente comum ---
    engel = {}
    if not engel_df.empty:
        for geo in engel_df["geo"].unique():
            sub = engel_df[engel_df["geo"] == geo]
            tot = sub[sub["coicop"] == "TOTAL"].sort_values("time")
            ali = sub[sub["coicop"] == "CP011"].sort_values("time")
            if tot.empty or ali.empty:
                continue
            anos_comuns = sorted(set(tot["time"]) & set(ali["time"]))
            if not anos_comuns:
                continue
            a = anos_comuns[-1]
            t = float(tot[tot["time"] == a]["valor"].iloc[0])
            f = float(ali[ali["time"] == a]["valor"].iloc[0])
            if t > 0:
                engel[geo] = {"ano": a, "quota": f / t * 100,
                              "total": t, "alimentar": f}

    rendimento = {}
    for indic, df_r in rend_por_tipo.items():
        rendimento[indic] = {}
        for geo in df_r["geo"].unique():
            sub = df_r[df_r["geo"] == geo].sort_values("time")
            if not sub.empty:
                rendimento[indic][geo] = {"ano": str(sub["time"].iloc[-1]),
                                          "valor": float(sub["valor"].iloc[-1])}

    salario_med = {}
    if not sme_df.empty:
        for geo in sme_df["geo"].unique():
            sub = sme_df[sme_df["geo"] == geo].sort_values("time")
            if not sub.empty:
                salario_med[geo] = {"ano": str(sub["time"].iloc[-1]),
                                    "valor": float(sub["valor"].iloc[-1])}

    salario = {}
    if not sm_df.empty:
        for geo in sm_df["geo"].unique():
            sub = sm_df[sm_df["geo"] == geo].sort_values("time")
            if not sub.empty:
                salario[geo] = {"periodo": str(sub["time"].iloc[-1]),
                                "valor": float(sub["valor"].iloc[-1])}

    # --- vigilância de frescura das séries obtidas por API ---
    # Uma série arquivada responde com HTTP 200 e devolve dados bem formados;
    # apenas deixa de avançar. Foi assim que a aplicação apresentou dezembro de
    # 2025 durante sete meses (auditoria de 11.08.2026, E1 e E3). Regista-se
    # aqui o **último período de cada série**; a comparação com a data corrente
    # é feita na renderização, para não ficar congelada na cache.
    def _lim(chave):
        return LIMITES_FRESCURA[chave]

    _ult_indice = str(indice_pt["time"].max()) if not indice_pt.empty else None
    _ult_pli = str(pli_df["time"].max()) if not pli_df.empty else None
    _ult_priv = str(priv_df["time"].max()) if not priv_df.empty else None
    _ult_rend = None
    for _ind in rendimento.values():
        if _ind.get("PT"):
            _ult_rend = _ind["PT"]["ano"]
            break

    # Três séries obtidas ficavam de fora da vigilância (auditoria de 12.08.2026,
    # K12). Vêm de conjuntos já vigiados por outras séries, o que atenua o risco
    # mas não o elimina: um conjunto pode continuar a publicar um agregado e
    # parar uma classe. E a terceira é a base de todo o apuramento do IVA.
    _ult_var_longa = (str(var_pt_longo["time"].max())
                      if not var_pt_longo.empty else None)
    _ult_agr_esp = (str(agr_esp_df["time"].max())
                    if not agr_esp_df.empty else None)
    _ult_sub = str(ano_pesos_sub) if ano_pesos_sub is not None else None

    vigilancia = []
    for chave, nome, conjunto, cadencia, periodo in [
        ("indice", "Índice de preços", eurostat.HICP_MENSAL, "mensal", _ult_indice),
        ("variacoes", "Variação homóloga", eurostat.HICP_MENSAL, "mensal",
         str(mes_variacoes) if mes_variacoes is not None else None),
        ("ponderadores", "Ponderadores por classe", eurostat.HICP_PONDERADORES,
         "anual", str(ano_pesos) if ano_pesos is not None else None),
        ("contas_nacionais", "Despesa alimentar (Contas Nacionais)",
         eurostat.CONTAS_NACIONAIS, "anual", despesa_ano),
        ("agregados", "N.º de agregados familiares", "lfst_hhnhtych", "anual",
         agregados_ano),
        ("dimensao", "Dimensão média do agregado", "ilc_lvph01", "anual", dimensao_ano),
        ("rendimento", "Rendimento das famílias (EU-SILC)", "ilc_di03", "anual", _ult_rend),
        ("privacao", "Privação alimentar (EU-SILC)", "ilc_mdes03", "anual", _ult_priv),
        ("salario_minimo", "Salário mínimo nacional", "earn_mw_cur", "semestral",
         (salario.get("PT") or {}).get("periodo")),
        ("salario_medio", "Salário médio", "nama_10_a10", "anual",
         (salario_med.get("PT") or {}).get("ano")),
        ("nivel_precos", "Nível de preços comparado", "prc_ppp_ind_1", "anual", _ult_pli),
        ("variacoes", "Variação homóloga PT (série longa)", eurostat.HICP_MENSAL,
         "mensal", _ult_var_longa),
        ("variacoes", "Agregados especiais do índice", eurostat.HICP_MENSAL,
         "mensal", _ult_agr_esp),
        ("ponderadores", "Ponderadores por subclasse", eurostat.HICP_PONDERADORES,
         "anual", _ult_sub),
    ]:
        if periodo is None:
            continue                       # série indisponível — já consta do registo
        limite, porque = _lim(chave)
        vigilancia.append({"serie": nome, "conjunto": conjunto, "cadencia": cadencia,
                           "periodo": periodo, "limite_dias": limite, "porque": porque})

    return {
        "agregados_especiais": agr_esp_df,
        "vigilancia": vigilancia,
        "engel": engel,
        "rendimento": rendimento,
        "salario": salario,
        "salario_medio": salario_med,
        "pli": pli_df,
        "pli_cat": pli_cat,
        "agregados_valor": agregados_valor,
        "agregados_ano": agregados_ano,
        "agregados_fonte": agregados_fonte,
        "agregados_serie": agregados_serie,
        "base_indice": (base_indice if not indice_df.empty else None),
        "dimensao_media": dimensao_media,
        "dimensao_ano": dimensao_ano,
        "despesa_ano": despesa_ano,
        "despesa_milhoes": despesa_valor,
        "privacao": priv_df,
        "pesos": pesos,
        "pesos_subclasses": pesos_sub,
        "ano_pesos_subclasses": ano_pesos_sub,
        "pesos_por_ano": pesos_df,
        "indice_classes": idx_classes_df,
        "ano_pesos": ano_pesos,
        "pesos_desalinhados": pesos_desalinhados,
        "variacoes_classe": variacoes_classe,
        "mes_variacoes": mes_variacoes,
        "variacoes_desalinhadas": variacoes_desalinhadas,
        "variacao_oficial": variacao_oficial,
        "mes_variacao_oficial": mes_var_oficial,
        "indice_pt": indice_pt,
        "var_pt": var_pt,
        "bench": bench,
        "bench_todos": bench_todos,
        "registo": registo,
        "enderecos": list(eurostat.ENDERECOS),
        "momento": datetime.now(),
    }


def _atualizar_por_indice(mensal_base: float, ano_base: int, indice) -> tuple:
    """
    Atualiza um valor mensal do seu período de referência para o mês mais
    recente do índice de preços. Devolve (valor, mês, fator).

    `ano_base` pode ser um ano — `2022`, e usam-se os doze meses desse ano — ou
    um par `("2022-02", "2023-01")` delimitando a janela efetiva de referência.
    A segunda forma existe porque o IDF não é um instantâneo anual: a recolha
    decorreu em 26 quinzenas seguidas, de fevereiro de 2022 a fevereiro de
    2023, e o INE não corrige os valores para uma data comum. Indexar a partir
    de um ano civil, qualquer que fosse, era um pressuposto não confirmado
    (auditoria de 10.08.2026, D1).
    """
    if indice.empty:
        return mensal_base, None, 1.0

    if isinstance(ano_base, (tuple, list)) and len(ano_base) == 2:
        inicio, fim = str(ano_base[0]), str(ano_base[1])
        do_periodo = indice[(indice["time"] >= inicio) & (indice["time"] <= fim)]
    else:
        do_periodo = indice[indice["time"].str.startswith(str(ano_base))]

    if do_periodo.empty:
        return mensal_base, None, 1.0
    media_base = float(do_periodo["valor"].mean())
    ultimo = indice.sort_values("time").iloc[-1]
    fator = float(ultimo["valor"]) / media_base if media_base else 1.0
    return mensal_base * fator, str(ultimo["time"]), fator


def ancora_oficial(dados: dict, agregados: int) -> dict | None:
    """
    Calcula a despesa alimentar mensal por agregado nas **duas bases oficiais
    disponíveis**, cada uma atualizada para o mês mais recente pelo índice de
    preços a partir do seu próprio ano de referência.

    As duas não coincidem — para 2022 divergem por um fator de 2,3 — e não há
    forma de arbitrar entre elas com fontes públicas. Por isso a aplicação
    devolve ambas e apresenta o intervalo. Ver `src/config.py`, secção das
    âncoras, e docs/2026-08-07_levantamento_lacunas.md, §2.10.

    Devolve None se os dados necessários não estiverem disponíveis.
    """
    if not dados.get("despesa_milhoes") or not agregados:
        return None

    indice = dados["indice_pt"]
    bases = {}

    # --- Contas Nacionais: agregado macroeconómico ÷ agregados ÷ 12 ---
    # O denominador é o do **ano da despesa**, não o mais recente: ver
    # `agregados_do_ano`. O `agregados` recebido serve os outros usos da
    # aplicação — a extrapolação nacional do simulador —, que pedem o ano
    # corrente e não este.
    ano_cn = dados["despesa_ano"]
    denominador = agregados_do_ano(dados.get("agregados_serie") or {}, ano_cn)
    mensal_cn = dados["despesa_milhoes"] * 1e6 / denominador["valor"] / 12
    valor_cn, mes, fator_cn = _atualizar_por_indice(mensal_cn, ano_cn, indice)
    bases["contas"] = {
        "valor": valor_cn, "base_mensal": mensal_cn, "ano_base": ano_cn,
        "ano_fim": int(str(ano_cn)[:4]),
        "fator": fator_cn, "plausivel": 50.0 <= valor_cn <= 3000.0,
        "denominador": denominador,
        **BASES_ANCORA["contas"],
    }

    # --- IDF: medição direta, constante publicada ---
    # Indexado a partir da **janela de recolha**, não de um ano civil: ver
    # `IDF_JANELA_RECOLHA` em config.py.
    mensal_idf = IDF_ALIMENTAR_ANUAL / 12
    valor_idf, mes_idf, fator_idf = _atualizar_por_indice(
        mensal_idf, IDF_JANELA_RECOLHA, indice)
    bases["idf"] = {
        "valor": valor_idf, "base_mensal": mensal_idf,
        "ano_base": "2022/2023", "janela": IDF_JANELA_RECOLHA,
        "ano_fim": int(IDF_JANELA_RECOLHA[1][:4]),
        "fator": fator_idf, "plausivel": 50.0 <= valor_idf <= 3000.0,
        **BASES_ANCORA["idf"],
    }

    valores = [b["valor"] for b in bases.values()]
    return {
        "bases": bases,
        "mes": mes or mes_idf,
        "minimo": min(valores),
        "maximo": max(valores),
    }


# ==========================================================================
# Componentes visuais
# ==========================================================================
# Fonte por omissão dos ficheiros exportados. É **parâmetro obrigatório na
# prática**: o cabeçalho era fixo e dizia «Fonte dos dados: Eurostat» em todos
# os ficheiros, incluindo o do Observatório do GPP — que nunca passou pelo
# Eurostat — e o do cabaz por quintil, cujos níveis são do INE. São ficheiros
# que saem da aplicação e circulam sozinhos: o cabeçalho é a única coisa que
# resta a acompanhá-los (auditoria de 11.08.2026, E6).
FONTE_EUROSTAT = "Eurostat (indice harmonizado de precos e contas nacionais)"


def csv_com_fonte(df: pd.DataFrame, titulo: str, dados: dict, extra=None,
                  fonte: str = FONTE_EUROSTAT, conjuntos=None) -> bytes:
    """
    Exporta em CSV com cabeçalho de proveniência, para que o ficheiro seja
    autoexplicativo fora da aplicação.

    `fonte` identifica quem produziu os dados **deste ficheiro**, e não da
    aplicação em geral. `conjuntos` restringe a lista de conjuntos declarados;
    por omissão declaram-se os que responderam nesta sessão, lidos do registo
    de ligações — em vez de uma lista fixa que envelhecia sem ninguém dar por
    isso e que omitia mais de metade dos conjuntos usados.
    """
    if conjuntos is None:
        vistos = [ds for ds, _url, _via in (dados.get("enderecos") or [])]
        conjuntos = sorted(dict.fromkeys(vistos))       # únicos, ordem estável
    conjuntos_txt = ", ".join(conjuntos) if conjuntos else "-"

    linhas = [
        f"# {titulo}",
        "# Produzido por: Unidade de Pesquisa e Estatisticas (UPE) - DSSD - Secretaria-Geral do Governo",
        f"# Fonte dos dados: {fonte}",
        f"# Conjuntos consultados nesta sessao: {conjuntos_txt}",
        f"# Ultimo mes disponivel: {dados.get('mes_variacoes') or '-'}",
        f"# Ponderadores de: {dados.get('ano_pesos') or '-'}",
        f"# Ancora das Contas Nacionais: {dados.get('despesa_ano') or '-'} "
        f"(a app usa duas bases - ver a linha 'Base de calculo' quando presente)",
        f"# Extraido em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]
    for chave, valor in (extra or []):
        linhas.append(f"# {chave}: {valor}")
    linhas += [
        "# Documento de trabalho interno - nao constitui posicao oficial da Secretaria-Geral do Governo.",
        "",
    ]
    corpo = df.to_csv(index=False, sep=";", decimal=",")
    return ("\n".join(linhas) + corpo).encode("utf-8-sig")


def cartao_classe(linha: pd.Series) -> str:
    var = linha["variacao"]
    cor_var = "#6b7280" if var is None else (VERMELHO if var > 0 else VERDE)
    quota = f"{linha['quota'] * 100:.1f}".replace(".", ",")
    if linha["contributo"] is not None:
        sinal = "encareceu" if linha["contributo"] > 0 else "baixou"
        contributo = (f"{sinal} <strong>{euro(abs(linha['contributo']))}</strong> "
                      "no último ano")
    else:
        contributo = "Aguarda dados"
    var_txt = "—" if var is None else f"{percentagem(var)} num ano"
    return f"""
    <div class="cartao" style="--c:{linha['cor']}">
      <div class="topo">
        <span class="emj">{linha['emoji']}</span>
        <span><span class="nm">{linha['classe']}</span><br>
        <span class="cd">COICOP {linha['codigo'][2:4]}.{linha['codigo'][4]}.{linha['codigo'][5]}</span></span>
      </div>
      <div class="vl">{euro(linha['valor'])}</div>
      <div class="ln">
        <span style="color:#6b7280">{quota} % da despesa</span>
        <span style="color:{cor_var};font-weight:600">{var_txt}</span>
      </div>
      <div class="ct">{contributo}</div>
    </div>"""


def grafico_donut(df: pd.DataFrame) -> go.Figure:
    dados = df[df["valor"] > 0].sort_values("valor", ascending=False)
    fig = go.Figure(go.Pie(
        labels=[f"{r.emoji} {r.classe}" for r in dados.itertuples()],
        values=dados["valor"],
        hole=.58,
        marker=dict(colors=list(dados["cor"]), line=dict(color="#fff", width=2)),
        textinfo="percent",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>%{value:.2f} €<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        height=380, margin=dict(t=10, b=10, l=10, r=10),
        showlegend=True,
        legend=dict(orientation="v", x=1, y=.5, font=dict(size=11)),
        annotations=[dict(text=f"<b>{euro(dados['valor'].sum())}</b>",
                          x=.5, y=.5, font_size=17, showarrow=False)],
    )
    return fig


def grafico_historico(indice: pd.DataFrame, variacao: pd.DataFrame,
                      meses: int) -> go.Figure:
    idx = indice.tail(meses)
    var = variacao.tail(meses)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[mes_pt(t) for t in idx["time"]], y=idx["valor"],
        name="Índice de preços", line=dict(color=VERDE, width=2.6),
        hovertemplate="%{x}<br>Índice: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[mes_pt(t) for t in var["time"]], y=var["valor"],
        name="Variação homóloga (%)", yaxis="y2",
        line=dict(color=VERMELHO, width=2, dash="dot"),
        hovertemplate="%{x}<br>Variação: %{y:.1f} %<extra></extra>",
    ))
    fig.update_layout(
        height=380, margin=dict(t=20, b=40, l=10, r=10),
        yaxis=dict(title="Índice"),
        yaxis2=dict(title="Variação homóloga (%)", overlaying="y", side="right",
                    zeroline=True, zerolinecolor="#cbd5e1"),
        legend=dict(orientation="h", y=1.13, x=0),
        hovermode="x unified", plot_bgcolor="#fff",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eef1f4")
    return fig


def grafico_reparticao(sim: pd.DataFrame) -> go.Figure:
    dados = sim[sim["mecanico"].abs() > 0.001].copy()
    if dados.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[f"{r.emoji} {r.classe}" for r in dados.itertuples()],
        x=dados["efetivo"].abs(), name="Chega ao consumidor",
        orientation="h", marker_color=VERDE,
        hovertemplate="%{y}<br>Consumidor: %{x:.2f} €<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=[f"{r.emoji} {r.classe}" for r in dados.itertuples()],
        x=dados["margem"].abs(), name="Capturado na margem",
        orientation="h", marker_color=DOURADO,
        hovertemplate="%{y}<br>Margem: %{x:.2f} €<extra></extra>",
    ))
    fig.update_layout(
        barmode="stack", height=330, margin=dict(t=30, b=30, l=10, r=10),
        legend=dict(orientation="h", y=1.14, x=0),
        xaxis_title="Euros por mês", plot_bgcolor="#fff",
    )
    fig.update_xaxes(gridcolor="#eef1f4")
    return fig


# ==========================================================================
# Cabeçalho
# ==========================================================================
_logo_html = (
    f'<img class="sim" src="data:image/png;base64,{LOGO}" alt="SGGov">' if LOGO else ""
)
st.markdown(f"""
<div class="barra">
  {_logo_html}
  <div class="bt">
    <strong>SECRETARIA-GERAL DO GOVERNO</strong>
    <span>Suporte à Decisão · {UNIDADE}</span>
  </div>
  <div class="bd">Despesa alimentar das famílias</div>
</div>
""", unsafe_allow_html=True)

# ==========================================================================
# Carregamento (executado no servidor — sem restrições de navegador)
# ==========================================================================
try:
    with st.spinner("A obter dados oficiais do Eurostat…"):
        dados = carregar_dados()
    erro_carregamento = None
except Exception as exc:                                   # noqa: BLE001
    dados, erro_carregamento = None, exc

if erro_carregamento is not None:
    st.error(
        "**Não foi possível obter os dados do Eurostat.**\n\n"
        f"`{erro_carregamento}`\n\n"
        "Se esta aplicação estiver alojada no Streamlit Community Cloud, verifique o "
        "estado do serviço do Eurostat. Em execução local numa rede institucional, "
        "confirme se o acesso a `ec.europa.eu` está autorizado."
    )
    st.stop()

ultimo_mes = dados["mes_variacoes"] or (
    dados["var_pt"]["time"].max() if not dados["var_pt"].empty else "—"
)

# ==========================================================================
# Barra lateral — parâmetros
# ==========================================================================
with st.sidebar:
    st.markdown("### 🛒 Parâmetros")

    # --- número de agregados: sempre o valor oficial, no ano mais recente ---
    # Este é o valor usado para **extrapolar para o país** (simulador de IVA):
    # aí interessa quantos agregados existem hoje. O denominador da âncora das
    # Contas Nacionais é outro — o do ano da despesa —, calculado em
    # `agregados_do_ano` (auditoria de 10.08.2026, B2).
    if dados.get("agregados_valor"):
        agregados = int(dados["agregados_valor"])
        agr_fonte = f"{dados['agregados_fonte']}, {dados['agregados_ano']}"
    else:
        agregados = AGREGADOS_CENSOS
        agr_fonte = AGREGADOS_FONTE

    ancora = ancora_oficial(dados, agregados)
    if ancora is None:
        st.error(
            "Não foi possível calcular a despesa a partir das Contas Nacionais. "
            "Consulte o registo de ligações no separador Metodologia."
        )
        st.stop()

    # --- base de cálculo: as duas fontes oficiais não coincidem ---
    st.caption("**Base de cálculo**")
    base_chave = st.radio(
        "Base de cálculo",
        options=list(BASES_ANCORA.keys()),
        index=list(BASES_ANCORA.keys()).index(BASE_POR_DEFEITO),
        format_func=lambda k: BASES_ANCORA[k]["nome"],
        label_visibility="collapsed",
        help=("As duas fontes oficiais medem coisas diferentes e divergem por um fator "
              "próximo de 2. Nenhuma é a resposta certa: o valor real está entre as duas. "
              "Ver separador Metodologia."),
    )
    base_ancora = ancora["bases"][base_chave]
    outra_chave = next(k for k in ancora["bases"] if k != base_chave)
    outra_ancora = ancora["bases"][outra_chave]

    media_agregado = float(base_ancora["valor"])
    valor_medio_agregado = media_agregado
    dim_media = dados.get("dimensao_media")

    st.caption(
        f"Intervalo entre as duas bases: **{euro(ancora['minimo'])} a "
        f"{euro(ancora['maximo'])}** por mês, para o agregado médio. "
        f"O ponto central não é determinável."
    )

    # A idade da base tem de estar à vista, não só no registo de ligações: a
    # despesa é atualizada por preços, mas a estrutura de consumo é a do ano de
    # referência (auditoria de 10.08.2026, B2).
    _idade_base = date.today().year - int(base_ancora["ano_fim"])
    if _idade_base >= 2:
        st.caption(
            f"⏳ Base de **{base_ancora['ano_base']}** — {_idade_base} anos de atraso. "
            "Os preços estão atualizados ao mês corrente; a **estrutura de consumo** "
            f"é a de {base_ancora['ano_base']}."
        )

    if not base_ancora.get("plausivel", True):
        st.error(
            "⚠️ **Valor fora do intervalo plausível.** Verifique o registo de ligações "
            "no separador Metodologia. **Não use estes números.**"
        )

    st.caption("**Composição do agregado**")
    ca, cb = st.columns(2)
    adultos = ca.number_input(
        "Com 14+ anos", min_value=1, max_value=10, value=2, step=1,
        help=("Todas as pessoas com 14 ou mais anos, incluindo jovens dependentes. "
              "A partir dessa idade, a escala de equivalência atribui o mesmo peso "
              "alimentar — um jovem de 15 anos come como um adulto, mesmo que não "
              "aufira rendimento."))
    criancas = cb.number_input(
        "Menos de 14 anos", min_value=0, max_value=10, value=0, step=1,
        help=("14 anos é o limiar definido pelas próprias escalas de equivalência "
              "da OCDE e do Eurostat — não é a definição demográfica de criança. "
              "Ver separador Metodologia."))

    dim_efetiva = dim_media if dim_media else DIMENSAO_RECUO
    _escala_apurada = escala_mais_proxima()
    escala_chave = st.selectbox(
        "Escala de equivalência", options=list(ESCALAS.keys()),
        index=list(ESCALAS.keys()).index(_escala_apurada) if _escala_apurada else 1,
        format_func=lambda k: (ESCALAS[k]["nome"] + (" ✓" if k == _escala_apurada else "")),
        help=("Como se ajusta a despesa ao número de pessoas. A assinalada com ✓ é a que, "
              "no teste contra o IDF 2022/2023, fica mais perto da despesa alimentar "
              "observada. Ver separador Metodologia."),
    )
    if _escala_apurada and escala_chave != _escala_apurada:
        st.caption(
            f"A escala escolhida não é a que melhor reproduz a despesa alimentar observada "
            f"(**{ESCALAS[_escala_apurada]['nome'].split(' (')[0]}**). Ver o teste no "
            f"separador Metodologia."
        )

    despesa_mensal = despesa_do_agregado(
        media_agregado, dim_efetiva, adultos, criancas, escala_chave)
    faixa = intervalo_agregado(media_agregado, dim_efetiva, adultos, criancas)

    # O rótulo tem de refletir o que a escala mede: pessoas com 14 ou mais anos
    # pesam como adultos, tenham ou não rendimento próprio.
    if criancas:
        composicao = (f"{adultos} com 14+ anos e {criancas} "
                      + ("menores de 14" if criancas > 1 else "menor de 14"))
    else:
        composicao = f"{adultos} pessoa{'s' if adultos > 1 else ''} com 14+ anos"
    pessoas = adultos + criancas
    ue = unidades_equivalentes(adultos, criancas, escala_chave)
    origem = (f"{base_ancora['nome']} · {composicao} · "
              f"escala {ESCALAS[escala_chave]['nome']}")
    vezes_ano = 12

    st.divider()
    st.metric(f"Despesa mensal — {composicao}", euro(despesa_mensal))
    st.caption(f"{pessoas} pessoa{'s' if pessoas > 1 else ''} · "
               f"intervalo entre escalas de {euro(faixa['minimo'])} a {euro(faixa['maximo'])}")

    with st.expander("Comparar as três escalas"):
        maior_que_media = pessoas > dim_efetiva
        st.dataframe(
            pd.DataFrame([
                {"Escala": ESCALAS[k]["nome"].split(" (")[0],
                 "Coeficientes": f"{ESCALAS[k]['primeiro']:.0f} / "
                                 f"{ESCALAS[k]['adulto']:.1f} / "
                                 f"{ESCALAS[k]['crianca']:.1f}".replace(".", ","),
                 "Despesa (€)": round(faixa["por_escala"][k], 2)}
                for k in ESCALAS
            ]), width="stretch", hide_index=True)

        st.markdown(f"""
**Porque é que a escala com coeficientes menores dá aqui um valor {'menor' if maior_que_media else 'maior'}?**

O ponto de partida é sempre o **agregado médio português — {('%.2f' % dim_efetiva).replace('.', ',')} pessoas**.
A escala não serve para calcular a despesa a partir do zero: serve para **ajustar** desse
agregado médio para o seu. E é aplicada aos **dois lados** do cálculo — ao seu agregado e ao
agregado médio que serve de referência.

Daí resulta um comportamento que à primeira vista surpreende:

| O seu agregado | Escala com economias de escala mais fortes dá… |
|---|---|
| **Menor** que {('%.2f' % dim_efetiva).replace('.', ',')} pessoas | valor **mais alto** |
| **Maior** que {('%.2f' % dim_efetiva).replace('.', ',')} pessoas | valor **mais baixo** |

A razão: coeficientes menores significam que **cada pessoa a mais custa menos**. Isso
comprime as diferenças entre agregados de dimensão diferente — todos se aproximam da média.
Um casal, sendo **menor** que a média, aproxima-se dela *por cima*; um casal com três filhos,
sendo **maior**, aproxima-se dela *por baixo*.

O ponto de viragem é exatamente a dimensão média. Com {pessoas} pessoa{'s' if pessoas > 1 else ''},
está **{'acima' if maior_que_media else 'abaixo'}** dela.
        """)
        st.caption(
            "É por isto que a aplicação apresenta sempre um intervalo: nenhuma das três escalas "
            "é a resposta certa para a alimentação, e a escolha entre elas altera o resultado "
            "em sentidos diferentes consoante a dimensão do agregado."
        )

    _agr_txt = numero(agregados)
    _mes_txt = mes_pt(ancora["mes"]) if ancora["mes"] else "—"
    _den = base_ancora.get("denominador")
    # O denominador da âncora das Contas Nacionais, independentemente da base
    # escolhida: a Metodologia explica-o sempre, e o `_den` acima é None quando
    # a base ativa é a do IDF, que não passa por divisão nenhuma.
    _den_contas = ancora["bases"]["contas"].get("denominador") or {
        "valor": agregados, "ano": dados.get("agregados_ano") or "—"}
    with st.expander("De onde vem este valor"):
        if base_chave == "contas":
            _den_txt = numero(_den["valor"]) if _den else _agr_txt
            _proveniencia = (
                "Da **despesa alimentar de todas as famílias portuguesas** registada nas Contas "
                f"Nacionais, dividida pelo número de agregados desse mesmo ano ({_den_txt} em "
                f"{_den['ano'] if _den else '—'}), atualizada ao mês corrente pelo índice oficial "
                "de preços e ajustada à composição indicada acima."
            )
        else:
            _proveniencia = (
                "Da **despesa alimentar declarada pelos agregados** no Inquérito às Despesas das "
                "Famílias do INE, atualizada ao mês corrente pelo índice oficial de preços e "
                "ajustada à composição indicada acima. Não passa por divisão de nenhum agregado "
                "macroeconómico: é medição direta."
            )
        if base_chave == "contas" and _den:
            _linha_agr = (f"**Denominador:** {_den['fonte']}, {_den['ano']} — "
                          "o mesmo ano da despesa")
            if _den["desfasamento"]:
                _linha_agr = (f"**Denominador:** {_den['fonte']}, {_den['ano']} — "
                              f"⚠️ **{_den['desfasamento']} ano(s) de desfasamento** face à "
                              f"despesa, que é de {base_ancora['ano_base']}")
        else:
            _linha_agr = f"**N.º de agregados:** {agr_fonte}"
        st.markdown(
            _proveniencia + "\n\n"
            + _linha_agr + "  \n"
            + f"**Base de despesa:** {base_ancora['nome']} ({base_ancora['ano_base']}), "
            f"a preços de {_mes_txt}  \n"
            f"**Fonte:** {base_ancora['fonte']}\n\n"
            f"*{base_ancora['porque']}*\n\n"
            f"Na outra base — {outra_ancora['nome']} — o mesmo agregado médio daria "
            f"**{euro(outra_ancora['valor'])}** por mês."
        )

    st.divider()
    st.caption("**Atualização dos dados**")
    if st.button("🔄 Recarregar do Eurostat", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption(f"**{UNIDADE}**")

# --- vigilância de frescura: uma série que responde não é uma série que avança ---
# Calculada aqui, e não dentro de `carregar_dados`, para não ficar congelada na
# cache: o que envelhece é a distância à data corrente, não os dados.
_fresc = frescura_das_series(dados.get("vigilancia") or [])
_paradas = _fresc[_fresc["desatualizada"]] if not _fresc.empty else pd.DataFrame()
if not _paradas.empty:
    _linhas_p = "\n".join(
        f"- **{r.serie}** (`{r.conjunto}`, {r.cadencia}) — último período "
        f"**{r.periodo}**, há **{numero(r.dias)} dias**; o normal seria no "
        f"máximo {numero(r.limite_dias)}. {r.porque}"
        for r in _paradas.itertuples()
    )
    st.error(
        f"⛔ **{len(_paradas)} série(s) do Eurostat deixaram de avançar.** "
        "Não é falha de rede nem atraso de publicação: o pedido foi bem "
        "sucedido e os dados vieram — apenas não são recentes.\n\n"
        f"{_linhas_p}\n\n"
        "**A causa mais provável é o conjunto ter sido arquivado** e substituído "
        "por outro, como aconteceu na passagem para a ECOICOP versão 2. Confirme "
        "no catálogo do Eurostat — o título dos conjuntos arquivados costuma "
        "trazer o intervalo de anos — antes de citar estes números."
    )

# --- mensagem de estado ---
nota_ancora = ""
if dados.get("despesa_ano"):
    nota_ancora = f" · âncora de despesa de **{dados['despesa_ano']}**"
st.success(
    f"Dados oficiais carregados · último mês disponível **{mes_pt(ultimo_mes)}** · "
    f"ponderadores de **{dados['ano_pesos']}**{nota_ancora} · "
    f"atualizado às {dados['momento'].strftime('%H:%M de %d/%m/%Y')}"
)

# --- classes cujo período não é o que a mensagem acima anuncia ---
# Cada classe entra com a sua última observação, e o rótulo é o máximo de todas.
# Hoje coincidem; quando não coincidirem, tem de ser dito em vez de assumido
# (auditoria de 12.08.2026, K13).
_desal_p = dados.get("pesos_desalinhados") or {}
_desal_v = dados.get("variacoes_desalinhadas") or {}
if _desal_p or _desal_v:
    def _lista_desal(mapa, rotulo_global):
        return ", ".join(
            f"**{POR_CODIGO[c]['nome'] if c in POR_CODIGO else c}** ({p} em vez de "
            f"{rotulo_global})" for c, p in sorted(mapa.items()))

    _partes = []
    if _desal_p:
        _partes.append("Ponderadores: " + _lista_desal(_desal_p, dados["ano_pesos"]))
    if _desal_v:
        _partes.append("Variações homólogas: "
                       + _lista_desal(_desal_v, dados["mes_variacoes"]))
    st.warning(
        "**Nem todas as classes têm o mesmo período.** A mensagem acima mostra o "
        "período mais recente do conjunto, mas há classes cuja última observação é "
        "anterior — entram com essa, e não são excluídas do cálculo, porque deixá-las "
        "cair distorceria mais (as restantes absorveriam a totalidade da despesa).\n\n"
        + "\n\n".join(f"- {p}" for p in _partes)
        + "\n\nO efeito é de segunda ordem, mas os números deixam de se referir todos "
        "ao mesmo momento."
    )

# --- decomposição base, usada por vários separadores ---
df_decomp = decompor(despesa_mensal, dados["pesos"], dados["variacoes_classe"])
resumo = resumo_decomposicao(df_decomp, despesa_mensal)

# Cobertura da decomposição. Faltando um ponderador, as restantes classes
# absorvem 100 % da despesa e cada quota sai inflacionada — sem aviso nenhum
# (auditoria de 11.08.2026, E10). Declara-se, como já se fazia no Törnqvist.
_sem_peso = df_decomp.attrs.get("classes_sem_ponderador") or []
_sem_var = df_decomp.attrs.get("classes_sem_variacao") or []


def _nomes_classes(codigos):
    return ", ".join(POR_CODIGO[c]["nome"] for c in codigos if c in POR_CODIGO)


if _sem_peso:
    st.error(
        f"⚠️ **{len(_sem_peso)} das nove classes não têm ponderador nesta sessão** "
        f"— {_nomes_classes(_sem_peso)}. A despesa foi repartida apenas pelas "
        f"restantes {9 - len(_sem_peso)}, pelo que **todas as quotas e todos os "
        "valores em euros estão sobrestimados**. Consulte o registo de ligações "
        "no separador Metodologia."
    )
elif _sem_var:
    st.warning(
        f"**{len(_sem_var)} das nove classes não têm variação homóloga nesta "
        f"sessão** — {_nomes_classes(_sem_var)}. As quotas e os valores em euros "
        "não são afetados; o **agravamento dos últimos 12 meses** é o das classes "
        "com dados, e fica por isso subestimado."
    )

from contextlib import contextmanager


@contextmanager
def painel(nome: str):
    """
    Isola cada separador. Se algo falhar — um conjunto de dados com estrutura
    inesperada, um estado de sessão preso de uma versão anterior — o erro fica
    contido nesse separador, com indicação do que fazer, em vez de derrubar a
    aplicação inteira.
    """
    try:
        yield
    except Exception as exc:                                   # noqa: BLE001
        st.error(
            f"**Não foi possível apresentar «{nome}».**\n\n"
            f"`{type(exc).__name__}: {exc}`\n\n"
            "Os restantes separadores continuam a funcionar. Passos a tentar, por esta ordem:\n"
            "1. **Recarregar do Eurostat** na barra lateral — limpa a cache de dados;\n"
            "2. **Recarregar a página** com Ctrl+F5 — limpa o estado da sessão;\n"
            "3. Consultar o **registo de ligações** no separador Metodologia, para ver "
            "se algum conjunto de dados falhou."
        )


aba1, aba2, aba6, aba3, aba4, aba5 = st.tabs([
    "🛒 Despesa e composição", "📈 Histórico", "🔗 Da produção ao consumo",
    "🧾 Simulador de IVA", "🇪🇺 Comparação UE-27", "📚 Metodologia e fontes",
])

# ==========================================================================
# ABA 1 — Despesa e composição
# ==========================================================================
with aba1:
    with painel("Despesa e composição"):
        colunas = st.columns(5)
        colunas[0].metric(f"Despesa mensal — {composicao}", euro(despesa_mensal), help=origem)
        if resumo["contributo_total"] is not None:
            # A percentagem é uma **taxa de variação de preços** e não depende da
            # base de despesa: mudar de IDF para Contas Nacionais muda os euros,
            # não a taxa. Sem esta nota parece que a app ignorou a mudança de base
            # (relatado pela utilizadora, 12.08.2026).
            _nota_taxa = ("A percentagem é uma **taxa de variação de preços** — vem do índice "
                          "e dos ponderadores, não do nível de despesa. Por isso **não muda** "
                          "quando troca a base entre IDF e Contas Nacionais: o que muda é o "
                          "valor em euros, porque a mesma taxa aplicada a uma despesa maior "
                          "dá mais euros.")
            # A taxa apresentada é a **oficial** do CP011, e não a reconstituída
            # da decomposição. Decisão da Inês, 12.08.2026 (auditoria, K1): numa
            # ferramenta que vai apoiar o Gabinete em debate público, o número de
            # capa tem de ser o que qualquer pessoa pode ir verificar ao INE.
            # Um número de capa que não bate certo com o publicado é fácil de
            # atacar e difícil de neutralizar, e o risco reputacional é
            # assimétrico.
            #
            # Os euros continuam a ser a **soma dos nove contributos**, que é a
            # propriedade que a decomposição promete e que está travada por
            # teste. As duas grandezas correspondem a taxas ligeiramente
            # diferentes, e é isso que o tooltip diz — e a legenda por baixo dos
            # gráficos de decomposição.
            _var_of = dados.get("variacao_oficial")
            _taxa_capa = _var_of if _var_of is not None else resumo["variacao_implicita"]
            _nota_capa = ""
            if _var_of is not None and resumo["variacao_implicita"] is not None:
                _nota_capa = (
                    f"\n\n**A percentagem é a taxa oficial** do agregado alimentar "
                    f"(`CP011`, {mes_pt(dados.get('mes_variacao_oficial'))}) — o número "
                    "publicado pelo INE, que se pode verificar diretamente na fonte. "
                    "**Os euros são a soma dos nove contributos** apresentados abaixo, "
                    "que corresponde a "
                    f"{percentagem(resumo['variacao_implicita'], sinal=False)}: essa "
                    "agregação pondera as nove taxas pelos valores de há um ano, e a "
                    "oficial pelos do período corrente. A diferença é de décimas de "
                    "ponto — ver a nota sob os gráficos.")
            colunas[1].metric("Agravamento nos últimos 12 meses", euro(resumo["contributo_total"]),
                              percentagem(_taxa_capa),
                              help="Subida da despesa alimentar face ao mesmo mês do ano "
                                   f"anterior, à composição de consumo atual. {_nota_taxa}"
                                   f"{_nota_capa}")
            colunas[2].metric("Despesa há 12 meses", euro(resumo["valor_ha_um_ano"]),
                              help="A mesma despesa deflacionada pela variação homóloga de "
                                   "cada classe. Escala com a base escolhida.")
            if resumo["maior"]:
                maior = resumo["maior"]
                colunas[3].metric(f"{maior['emoji']} Maior contributo",
                                  euro(maior["contributo"]),
                                  percentagem(maior["variacao"]),
                                  help="A classe que mais pesou no agravamento — em euros, "
                                       "combinando a sua subida de preços com o seu peso no "
                                       f"cabaz. {_nota_taxa}")
        colunas[4].metric("Equivalente anual", euro(despesa_mensal * vezes_ano))

        st.markdown(f"""
        <div class="nota">
          <div class="tt">O valor exato não é determinável — use o intervalo</div>
          As duas fontes oficiais que medem a despesa alimentar das famílias não coincidem.
          Para o agregado médio, a despesa mensal situa-se entre
          <strong>{euro(ancora['minimo'])}</strong> e <strong>{euro(ancora['maximo'])}</strong>,
          consoante se use o inquérito às despesas ou as Contas Nacionais. O ponto central
          <strong>não é determinável</strong>: o inquérito subestima e as Contas Nacionais
          sobrestimam, e não existe exercício de conciliação que permita arbitrar.
          Os valores acima usam a base <strong>{base_ancora['nome']}</strong>, escolhida na barra
          lateral. Ver separador Metodologia.
        </div>
        """, unsafe_allow_html=True)

        dim_txt = ('%.1f' % dim_efetiva).replace('.', ',')
        r1, r2, r3 = st.columns([1, 1, 2])
        r1.metric(f"Agregado médio nacional ({dim_txt} pessoas)",
                  euro(valor_medio_agregado),
                  help=(f"Base {base_ancora['nome']}. Na outra base seria {euro(outra_ancora['valor'])}. "
                        "Valor de referência antes de qualquer ajustamento de composição."))
        r2.metric("Equivalente anual", euro(valor_medio_agregado * 12))
        eng_pt = (dados.get("engel") or {}).get("PT")
        _eng = intervalo_engel(eng_pt)

        if eng_pt:
            # Intervalo, e não ponto: as duas bases oficiais divergem, e é a
            # mesma divergência que já leva a âncora a ser apresentada como
            # intervalo. O extremo inferior é o número do INE que aparece na
            # tabela por quintil logo abaixo (auditoria de 10.08.2026, B4).
            r3.metric("Do que as famílias gastam, vai para comida",
                      f"{percentagem(_eng['minimo'], sinal=False)} a {percentagem(_eng['maximo'], sinal=False)}",
                      help=("Coeficiente de Engel nas duas bases oficiais: "
                            f"{percentagem(_eng['idf'], sinal=False)} no IDF 2022/2023 (agregados residentes) "
                            f"e {percentagem(_eng['contas'], sinal=False)} nas Contas Nacionais de "
                            f"{_eng['ano_contas']} (conceito macroeconómico). Divergem "
                            "porque a despesa alimentar por agregado difere entre bases "
                            "mais do que a despesa total — o mesmo motivo por que a "
                            "âncora é um intervalo. O limite inferior é o valor que "
                            "consta da tabela por quintil, mais abaixo. Comparação "
                            "europeia no separador UE-27, que usa as Contas Nacionais "
                            "por serem a única base comparável entre países."))
            r3.caption("IDF 2022/2023 · Contas Nacionais — ver Metodologia")
        else:
            r3.markdown(
            f"<div style='padding-top:14px;font-size:12.5px;color:#4a4a48'>"
            f"É este o ponto de partida do cálculo: a despesa alimentar de um agregado "
            f"com a dimensão média portuguesa ({dim_txt} pessoas). Os valores em cima "
            f"estão ajustados para <strong>{composicao}</strong>.</div>",
            unsafe_allow_html=True)

        st.info("""
    **Como ler os cartões.** O valor grande é quanto da despesa mensal vai para esse grupo.
    A percentagem à direita é a **variação homóloga** — de quanto os preços desse grupo subiram
    face ao **mesmo mês do ano anterior** (não face ao mês anterior). A linha de baixo mostra o
    **contributo**: quantos euros desse aumento se devem a esse grupo em concreto. A soma dos
    contributos de todos os grupos dá exatamente o agravamento total dos últimos 12 meses.
        """)

        for inicio in range(0, len(df_decomp), 3):
            cols = st.columns(3)
            for col, (_, linha) in zip(cols, df_decomp.iloc[inicio:inicio + 3].iterrows()):
                col.markdown(cartao_classe(linha), unsafe_allow_html=True)

        st.write("")
        esq, dir_ = st.columns([1, 1])
        with esq:
            st.markdown("**Peso de cada grupo na despesa**")
            st.caption("Fração da despesa alimentar mensal que vai para cada tipo de produto.")
            st.plotly_chart(grafico_donut(df_decomp), width="stretch")
        with dir_:
            st.markdown("**Quanto cada grupo pesou no agravamento**")
            st.caption("Euros de aumento nos últimos 12 meses atribuíveis a cada grupo.")
            com_dados = df_decomp.dropna(subset=["contributo"]).sort_values("contributo")
            if com_dados.empty:
                st.info("Sem variações disponíveis para o período.")
            else:
                fig = go.Figure(go.Bar(
                    y=[f"{r.emoji} {r.classe}" for r in com_dados.itertuples()],
                    x=com_dados["contributo"], orientation="h",
                    marker_color=[VERMELHO if v > 0 else VERDE for v in com_dados["contributo"]],
                    hovertemplate="%{y}<br>%{x:.2f} €<extra></extra>",
                ))
                fig.update_layout(height=380, margin=dict(t=10, b=30, l=10, r=10),
                                  xaxis_title="Euros", plot_bgcolor="#fff")
                fig.update_xaxes(gridcolor="#eef1f4", zerolinecolor="#cbd5e1")
                st.plotly_chart(fig, width="stretch")

        # A aditividade é a propriedade central da decomposição, e continua a
        # valer — mas a taxa que ela implica não é exatamente a oficial que está
        # na capa. Isso tem de estar escrito onde os contributos aparecem, e não
        # só no tooltip do indicador (auditoria de 12.08.2026, K1).
        if (resumo["contributo_total"] is not None
                and resumo["variacao_implicita"] is not None
                and dados.get("variacao_oficial") is not None):
            _dif_k1 = dados["variacao_oficial"] - resumo["variacao_implicita"]
            st.caption(
                f"**Os nove contributos somam exatamente "
                f"{euro(resumo['contributo_total'])}** — é a propriedade que esta "
                "decomposição garante, e está verificada por teste automático. Essa "
                "soma corresponde a uma subida de "
                f"**{percentagem(resumo['variacao_implicita'], sinal=False)}**, "
                f"enquanto o índice oficial do agregado alimentar (`CP011`) regista "
                f"**{percentagem(dados['variacao_oficial'], sinal=False)}** em "
                f"{mes_pt(dados.get('mes_variacao_oficial'))} — uma diferença de "
                f"{pontos(abs(_dif_k1), casas=2, sinal=False)}\n\n"
                "**Não é discrepância: são duas agregações da mesma coisa.** Para os "
                "nove contributos somarem ao total, a taxa que deles resulta pondera "
                "as nove classes pelos seus valores **de há um ano**; a oficial "
                "pondera-as pelos do **período corrente**. Verificado: ponderando "
                "pelos valores correntes obtêm-se "
                f"{percentagem(sum(r.quota * r.variacao for r in df_decomp.itertuples() if r.variacao is not None), sinal=False)}, "
                "que reproduz a oficial. Sobre 90 meses de série, a diferença tem "
                "média absoluta de 0,15 p.p. e nunca chegou a 1 p.p. **A percentagem "
                "no indicador de topo é a oficial**, para que seja verificável na "
                "fonte; os euros são os desta decomposição."
            )

        # ---- cabaz por quintil de rendimento ----
        st.divider()
        st.markdown("#### Quem está mais exposto — por quintil de rendimento")
        st.caption(
            "Ponderação do **IDF 2022/2023**, não do IHPC. Os quadros Q.2.11 do INE dão a "
            "despesa alimentar por quintil de rendimento equivalente, ao nível da classe "
            "COICOP e em euros. É a única fonte aberta que mede agregados residentes "
            "— os ponderadores do IHPC incluem a despesa de turistas."
        )

        df_quintis = cabaz_quintis(dados["variacoes_classe"])
        df_comp_q = composicao_quintis()

        tab_q = pd.DataFrame([{
            "Quintil": r.nome,
            "Despesa alimentar": euro(r.despesa_mensal, 0) + "/mês",
            "Despesa total": euro(r.despesa_total_mensal, 0) + "/mês",
            "Peso no orçamento": f"{r.peso_orcamento:.1f} %".replace(".", ","),
            "Inflação 12m": percentagem(r.inflacao, sinal=False) if r.inflacao is not None else "—",
            "Agravamento": euro(r.agravamento) + "/mês" if r.agravamento is not None else "—",
            "Agravamento / orçamento": (
                f"{r.agravamento_orcamento:.2f} %".replace(".", ",")
                if r.agravamento_orcamento is not None else "—"),
        } for r in df_quintis.itertuples()])
        st.dataframe(tab_q, width="stretch", hide_index=True)

        # O agravamento só soma as classes com variação; o orçamento é sempre o
        # total. Faltando classes, a coluna «Agravamento / orçamento»
        # subestimava sem o dizer (auditoria de 11.08.2026, E11).
        _cob_q = df_quintis.attrs.get("cobertura_minima", 1.0)
        if _cob_q < 0.999:
            _falta_q = df_quintis.attrs.get("classes_sem_variacao") or []
            st.warning(
                f"**Cobertura parcial: {percentagem(_cob_q * 100, sinal=False)} da despesa alimentar.** "
                f"{len(_falta_q)} classe(s) sem variação homóloga nesta sessão — "
                f"{_nomes_classes(_falta_q)}. As colunas **Inflação 12m** e "
                "**Agravamento** medem só as classes cobertas, mas a coluna "
                "**Agravamento / orçamento** divide pelo orçamento **total** do "
                "quintil — está por isso subestimada na mesma proporção."
            )

        if not _eng["so_idf"]:
            # `intervalo_engel` devolve min e max sem presumir qual das bases é
            # a maior — e há um teste que o exige. A prosa presumia, e invertia-se
            # sozinha se as Contas Nacionais alguma vez descessem abaixo do IDF
            # (auditoria de 12.08.2026, K14). Os rótulos derivam do intervalo.
            _idf_e_inferior = _eng["idf"] <= _eng["contas"]
            _pos_idf = "inferior" if _idf_e_inferior else "superior"
            _pos_cn = "superior" if _idf_e_inferior else "inferior"
            _mais_ou_menos = "mais" if _idf_e_inferior else "menos"
            st.caption(
                f"O **{percentagem(_eng['idf'], sinal=False)}** da média nacional, na coluna "
                f"«Peso no orçamento», é o limite **{_pos_idf}** do intervalo do coeficiente de "
                f"Engel mostrado em cima. O limite **{_pos_cn}**, "
                f"{percentagem(_eng['contas'], sinal=False)}, vem das Contas Nacionais: medem o "
                f"consumo das famílias por via macroeconómica e registam, por agregado, "
                f"**{_mais_ou_menos}** despesa alimentar do que o inquérito — e o coeficiente "
                "diverge porque **o numerador diverge mais do que o denominador**. Nenhuma das "
                "duas é a resposta certa — ver Metodologia."
            )

        _q1 = df_quintis[df_quintis["quintil"] == "q1"].iloc[0]
        _q5 = df_quintis[df_quintis["quintil"] == "q5"].iloc[0]
        _amplitude = None
        _infs = df_quintis[df_quintis["quintil"] != "total"]["inflacao"].dropna()
        if not _infs.empty:
            _amplitude = float(_infs.max() - _infs.min())

        _racio = _q1.peso_orcamento / _q5.peso_orcamento
        _frase_taxa = ""
        if _amplitude is not None:
            _mais_alto = _infs.idxmax()
            _nome_alto = df_quintis.loc[_mais_alto, "nome"]
            _frase_taxa = (
                f"A <em>taxa</em> de inflação, essa, quase não difere entre quintis: a amplitude "
                f"é de <strong>{numero(_amplitude, 2)} p.p.</strong>, e o valor mais alto está no "
                f"<strong>{_nome_alto}</strong>. "
            )

        _frase_esforco = ""
        if _q1.agravamento_orcamento is not None and _q5.agravamento_orcamento is not None:
            _frase_esforco = (
                f"Repare-se no que acontece se se olhar só para os euros: o agravamento dos "
                f"últimos 12 meses é <em>maior</em> no quintil mais rico "
                f"(<strong>{euro(_q5.agravamento)}</strong> contra "
                f"<strong>{euro(_q1.agravamento)}</strong>), simplesmente porque gasta mais em "
                f"comida. Medido contra o orçamento de cada um, inverte-se: "
                f"<strong>{numero(_q1.agravamento_orcamento, 2)} %</strong> do orçamento do "
                f"1.º quintil contra <strong>{numero(_q5.agravamento_orcamento, 2)} %</strong> "
                f"do 5.º. "
            )

        st.markdown(f"""
        <div class="nota">
          <div class="tt">O efeito regressivo está na exposição, não na taxa</div>
          A alimentação absorve <strong>{numero(_q1.peso_orcamento, 1)} %</strong> do orçamento do
          quintil mais pobre e <strong>{numero(_q5.peso_orcamento, 1)} %</strong> do mais rico — um
          rácio de <strong>{numero(_racio, 2)}</strong>. {_frase_taxa}Concluir daí que a inflação
          alimentar é distributivamente neutra seria um erro de leitura: o mesmo aumento
          percentual incide sobre uma fatia do orçamento <strong>{numero(_racio, 1)} vezes
          maior</strong> em baixo da distribuição, e sobre um orçamento total que é menos de
          metade.<br><br>{_frase_esforco}É por isto que nenhuma destas colunas deve ser lida
          isoladamente: a taxa sozinha sugere neutralidade, os euros sozinhos sugerem o
          contrário do que se passa.
        </div>
        """, unsafe_allow_html=True)

        cq1, cq2 = st.columns([3, 2])
        with cq1:
            st.markdown("**A composição muda, não só o nível**")
            st.caption("Fração da despesa alimentar de cada quintil que vai para cada grupo.")
            chaves_q = [k for k in IDF_QUINTIS if k != "total"]
            figq = go.Figure()
            for classe in CLASSES:
                sub = df_comp_q[df_comp_q["codigo"] == classe["cod"]].set_index("quintil")
                figq.add_trace(go.Bar(
                    name=f"{classe['emoji']} {classe['nome']}",
                    x=[IDF_QUINTIS[k] for k in chaves_q],
                    y=[sub.loc[k, "quota"] * 100 for k in chaves_q],
                    marker_color=classe["cor"],
                    hovertemplate="%{x}<br>" + classe["nome"] + ": %{y:.1f} %<extra></extra>",
                ))
            figq.update_layout(barmode="stack", height=420,
                               margin=dict(t=10, b=30, l=10, r=10),
                               yaxis_title="% da despesa alimentar", plot_bgcolor="#fff",
                               legend=dict(font=dict(size=10)))
            figq.update_yaxes(gridcolor="#eef1f4", range=[0, 100])
            st.plotly_chart(figq, width="stretch")
        with cq2:
            st.markdown("**Onde a diferença é maior**")
            st.caption("Variação da quota entre o 1.º e o 5.º quintil, em pontos percentuais.")
            larguras = []
            for classe in CLASSES:
                sub = df_comp_q[df_comp_q["codigo"] == classe["cod"]].set_index("quintil")
                larguras.append({
                    "classe": f"{classe['emoji']} {classe['nome']}",
                    "delta": (sub.loc["q5", "quota"] - sub.loc["q1", "quota"]) * 100,
                })
            df_delta = pd.DataFrame(larguras).sort_values("delta")
            figd = go.Figure(go.Bar(
                y=df_delta["classe"], x=df_delta["delta"], orientation="h",
                marker_color=[AZUL if v > 0 else DOURADO for v in df_delta["delta"]],
                hovertemplate="%{y}<br>%{x:+.1f} p.p.<extra></extra>",
            ))
            figd.update_layout(height=420, margin=dict(t=10, b=30, l=10, r=10),
                               xaxis_title="p.p. (Q5 − Q1)", plot_bgcolor="#fff")
            figd.update_xaxes(gridcolor="#eef1f4", zerolinecolor="#cbd5e1")
            st.plotly_chart(figd, width="stretch")

        st.caption(
            "**Níveis do IDF tal como medidos** — não são reescalados para a base de cálculo "
            "escolhida na barra lateral. Reescalá-los exigiria assumir que o sub-reporte do "
            "inquérito é uniforme entre quintis, e nada o sustenta. Os quintis são de "
            "rendimento equivalente (escala OCDE modificada), definidos pelo INE."
        )
        st.download_button(
            "⬇️ Descarregar cabaz por quintil (CSV)",
            csv_com_fonte(df_quintis, "Cabaz alimentar por quintil de rendimento", dados,
                          fonte=("INE, Inquerito as Despesas das Familias 2022/2023 "
                                 "(niveis e estrutura) + Eurostat, IHPC (variacoes de preco)"),
                          conjuntos=[eurostat.HICP_MENSAL],
                          extra=[
                              ("Niveis e ponderacao", "INE, IDF 2022/2023, quadros Q.2.11.a e Q.2.11.b"),
                              ("Variacoes de preco", "Eurostat, prc_hicp_minr (IHPC, ECOICOP v2)"),
                              ("Nota", "Niveis do IDF tal como medidos, sem reescalamento"),
                          ]),
            file_name="cabaz_por_quintil.csv", mime="text/csv")

        # ---- esforço do agregado escolhido ----
        st.divider()
        st.markdown(f"#### Quanto pesa no orçamento — {composicao}")

        rendimentos = dados.get("rendimento") or {}
        sm_pt = (dados.get("salario") or {}).get("PT")
        sme_pt = (dados.get("salario_medio") or {}).get("PT")
        tem_rend = any(rendimentos.get(k, {}).get("PT")
                       for k in eurostat.RENDIMENTO_INDICADORES)

        if not tem_rend and not sm_pt and not sme_pt:
            st.info(
                "Os indicadores de rendimento não estão disponíveis nesta sessão. "
                "Consulte o registo de ligações no separador Metodologia."
            )
        else:
            ca_, cb_ = st.columns([1, 2])
            with ca_:
                trabalhadores = st.number_input(
                    "Quantos auferem rendimento", min_value=1, max_value=int(adultos),
                    value=min(int(adultos), 2), step=1,
                    help=("Das pessoas com 14 ou mais anos, quantas auferem "
                          "efetivamente rendimento. Jovens dependentes, estudantes "
                          "e pessoas sem rendimento próprio não contam — mas "
                          "continuam a pesar na despesa alimentar."),
                )
                dependentes = int(adultos) - int(trabalhadores)
            with cb_:
                st.markdown(
                    f"<div style='padding-top:26px;font-size:12.5px;color:#4a4a48'>"
                    f"<strong>{pessoas}</strong> pessoa{'s' if pessoas > 1 else ''} a "
                    f"alimentar · <strong>{trabalhadores}</strong> "
                    + ("auferem" if trabalhadores > 1 else "aufere")
                    + " rendimento"
                    + (f" · <strong>{dependentes}</strong> com 14+ anos sem rendimento próprio"
                       if dependentes else "")
                    + (f" · <strong>{criancas}</strong> com menos de 14 anos"
                       if criancas else "")
                    + f"<br>Despesa alimentar mensal: <strong>{euro(despesa_mensal)}</strong>."
                    "</div>",
                    unsafe_allow_html=True)

                if dependentes:
                    st.warning(f"""
    **{dependentes} pessoa{'s' if dependentes > 1 else ''} com 14 ou mais anos sem rendimento
    próprio.** Adolescentes, estudantes ou outros dependentes **comem como adultos** — a escala de
    equivalência atribui-lhes o mesmo peso alimentar — mas **não trazem receita**. É a composição
    em que o esforço alimentar é mais elevado, e a que os indicadores médios menos revelam.
                    """)

            st.caption(
                "⚠️ Estes valores são **limites superiores** — despesa e rendimento vêm de "
                "fontes com bases estatísticas diferentes. Explicação em «O que estes números "
                "assumem», no fim desta secção."
            )

            # --- construir as referências disponíveis ---
            refs = []
            indic_r = None
            if tem_rend:
                disponiveis = [k for k in eurostat.RENDIMENTO_INDICADORES
                               if rendimentos.get(k, {}).get("PT")]
                indic_r = "MEAN_EI" if "MEAN_EI" in disponiveis else disponiveis[0]
                r = rendimentos[indic_r]["PT"]
                ue_ocde = unidades_equivalentes(adultos, criancas, "ocde_modificada")
                refs.append({
                    "ref": "Rendimento das famílias (EU-SILC)",
                    "detalhe": (f"{'Médio' if indic_r == 'MEAN_EI' else 'Mediano'} equivalente "
                                f"{r['ano']} × {('%.2f' % ue_ocde).replace('.', ',')} unidades"),
                    "mensal": r["valor"] * ue_ocde / 12,
                    "natureza": "líquido",
                })
            if sme_pt:
                refs.append({
                    "ref": f"{trabalhadores} × salário médio",
                    "detalhe": (f"Massa salarial ÷ trabalhadores por conta de outrem, "
                                f"{sme_pt['ano']} — **inclui tempo parcial**, pelo que fica "
                                "abaixo do salário de um trabalhador a tempo inteiro"),
                    "mensal": sme_pt["valor"] * trabalhadores / 12,
                    "natureza": "bruto",
                })
            if sm_pt:
                # O Eurostat publica a RMMG em duodécimos de 14 mensalidades:
                # o valor difundido é o legal × 14/12. Para a fatia mensal do
                # orçamento é essa a base certa — distribui os subsídios pelos
                # 12 meses. Mas não é o valor legal, e rotulá-lo como tal
                # sobrestimava o rendimento em 16,7 % (auditoria, A2). A RMMG é
                # fixada em euros inteiros, daí o arredondamento.
                rmmg_legal = round(sm_pt["valor"] * 12 / 14)
                refs.append({
                    "ref": f"{trabalhadores} × salário mínimo",
                    "detalhe": (f"Média mensal bruta de 14 mensalidades, {sm_pt['periodo']} "
                                f"— o valor legal da RMMG é de {rmmg_legal} €/mês"),
                    "mensal": sm_pt["valor"] * trabalhadores,
                    "natureza": "bruto",
                })

            for r in refs:
                r["esforco"] = despesa_mensal / r["mensal"] * 100 if r["mensal"] else None

            tab_r = pd.DataFrame([{
                "Referência": r["ref"],
                "Rendimento mensal": euro(r["mensal"]),
                "Esforço alimentar": (f"{r['esforco']:.1f} %".replace(".", ",")
                                      if r["esforco"] is not None else "—"),
                "Natureza": r["natureza"],
                "Detalhe": r["detalhe"],
            } for r in refs])
            st.dataframe(tab_r, width="stretch", hide_index=True)

            figR = go.Figure(go.Bar(
                y=[r["ref"] for r in refs],
                x=[r["esforco"] for r in refs], orientation="h",
                marker_color=[VERDE if r["natureza"] == "líquido" else DOURADO
                              for r in refs],
                text=[f"{r['esforco']:.1f} %".replace(".", ",") for r in refs],
                textposition="outside",
                hovertemplate="%{y}: %{x:.1f} % do rendimento<extra></extra>"))
            figR.update_layout(height=max(200, 60 * len(refs)),
                               margin=dict(t=20, b=40, l=10, r=70),
                               xaxis_title="Fatia do rendimento absorvida pela alimentação (%)",
                               plot_bgcolor="#fff", showlegend=False)
            figR.update_xaxes(gridcolor="#eef1f4")
            st.plotly_chart(figR, width="stretch")

            st.info(
                "**Sobre o cenário do salário mínimo.** Não é o agregado típico — é o **limiar "
                "inferior** da distribuição. Mas está longe de ser um caso extremo: em 2025 a "
                "RMMG equivalia a **91 % do salário mediano** do setor privado (índice de "
                "Kaitz), contra 87 % em 2019, e o rácio entre a mediana e o percentil 10 da "
                "distribuição salarial era de apenas **1,1**. A concentração é tal que, nos "
                "microdados da Segurança Social, **o segundo decil da distribuição salarial não "
                "chega a ter observações distintas**. Serve para dimensionar o limiar inferior, "
                "não para caracterizar a generalidade das famílias — mas esse limiar está muito "
                "mais perto do meio da distribuição do que se supõe."
            )
            st.caption(
                "Fonte: Banco de Portugal, *Boletim Económico* de junho de 2026, Caixa 5 — "
                "«A distribuição dos salários dos trabalhadores por conta de outrem», com base "
                "em microdados da Segurança Social. Abrange o **setor privado** (exclui a "
                "Administração Pública) e considera vínculos a tempo completo com 30 dias "
                "declarados e remuneração igual ou superior a 80 % da RMMG. Pelo *Structure of "
                "Earnings Survey* do Eurostat, que só inquire empresas com 10 ou mais "
                "trabalhadores, o índice de Kaitz português era de 69 % em 2024 — ainda assim o "
                "**mais elevado da área do euro**."
            )
            st.caption(
                "**Verde:** rendimento **líquido** — depois de impostos e contribuições. "
                "**Dourado:** valores **brutos** — salário médio e salário mínimo, antes de "
                "descontos. O rendimento efetivamente disponível é inferior, pelo que o esforço "
                "real sobre eles é **superior** ao apresentado. Verde e dourado não são "
                "diretamente comparáveis entre si."
            )

            with st.expander("⚠️ O que estes números assumem — leitura obrigatória"):
                if base_chave == "contas":
                    st.error("""
**São limites superiores, não estimativas.** O **numerador** — a despesa alimentar — vem das
**Contas Nacionais**; o **denominador** — o rendimento — vem do **EU-SILC**. São universos
estatísticos diferentes: as Contas Nacionais incluem rendas imputadas, consumo de instituições
sem fins lucrativos e consumo no território, incluindo o de não residentes; o EU-SILC mede
rendimento monetário líquido dos residentes.

O consumo por agregado das Contas Nacionais é estruturalmente **cerca de 1,8 vezes** o
rendimento do EU-SILC — rácio que implicaria taxa de poupança fortemente negativa.
**Combinar as duas bases sobrestima o esforço.**

Leia as **diferenças entre composições** e a **direção** como informativas; o **nível** como
majorante.

*Escolhendo a base **IDF** na barra lateral, esta incompatibilidade reduz-se substancialmente —
o IDF e o EU-SILC são ambos inquéritos a agregados residentes.*
                    """)
                else:
                    st.warning("""
**Bases estatísticas próximas, mas não idênticas.** Com a base **IDF**, o **numerador** — a
despesa alimentar — e o **denominador** — o rendimento do EU-SILC — vêm ambos de **inquéritos a
agregados residentes**, o que elimina a maior parte da incompatibilidade que afeta a base das
Contas Nacionais.

Subsistem diferenças: são inquéritos distintos, com amostras, períodos de referência e critérios
de imputação próprios, e ambos sub-reportam. O rácio continua a dever ler-se como **ordem de
grandeza**, não como medição.

Leia as **diferenças entre composições** e a **direção** como informativas; o **nível** com
reserva.
                    """)
                st.markdown(f"""
    **1 · As crianças não auferem rendimento.** O número de salários multiplica-se pelos
    **adultos com rendimento** indicados acima, nunca pelo total de pessoas. Um casal com dois
    filhos e dois salários continua a ter dois salários — mas quatro pessoas a alimentar, e é
    essa assimetria que faz o esforço subir.

    **2 · Bruto e líquido não se misturam.** Só o **rendimento do EU-SILC** é líquido — já
    descontados impostos e contribuições, e somadas as prestações. O **salário médio** e o
    **salário mínimo** são **brutos**: é o que consta do contrato ou do diploma, antes de
    qualquer desconto. Como o rendimento efetivamente disponível é inferior aos valores brutos,
    o esforço real sobre eles é **superior** ao que aqui aparece.

    **3 · O agregado está num valor central da distribuição.** Agregados abaixo dele têm esforço
    **superior** ao apresentado — e é justamente aí que a pressão alimentar mais se faz sentir.
    A medida por escalão de rendimento está na secção **«Quem está mais exposto»**, mais acima
    nesta página, a partir dos quadros Q.2.11 do IDF 2022/2023.

    **4 · As três escalas cruzam-se na dimensão média — e é isso que explica o resultado
    contraintuitivo.** Ver o gráfico logo abaixo deste bloco.

    **5 · Numerador e denominador usam escalas diferentes.** A despesa alimentar é ajustada pela
    escala que escolheu na barra lateral (**{ESCALAS[escala_chave]["nome"].split(" (")[0]}**); o
    rendimento do EU-SILC tem de usar a **OCDE modificada**, que é a que esse inquérito aplica.
    A consequência é mensurável:
                """)

                # Tabela calculada com os dados da sessão. Era um quadro de
                # valores fixos rotulado «ilustrativos», ao lado de números
                # calculados em direto: o leitor não distinguia uns dos outros
                # (auditoria de 10.08.2026, C2).
                if tem_rend and indic_r:
                    _r_anual = rendimentos[indic_r]["PT"]["valor"]
                    _casos = [("1 adulto", 1, 0), ("Casal", 2, 0), ("Casal + 2", 2, 2)]
                    _linhas_esc = []
                    for _ch, _esc in ESCALAS.items():
                        _linha = {"Escala usada na despesa": _esc["nome"].split(" (")[0]}
                        if _ch == "ocde_modificada":
                            _linha["Escala usada na despesa"] += " (igual à do rendimento)"
                        for _rot, _a, _c in _casos:
                            _desp = despesa_do_agregado(
                                media_agregado, dim_efetiva, _a, _c, _ch)
                            _ue = unidades_equivalentes(_a, _c, "ocde_modificada")
                            _rend_mes = _r_anual * _ue / 12
                            _linha[_rot] = (f"{_desp / _rend_mes * 100:.1f} %"
                                            .replace(".", ",") if _rend_mes else "—")
                        _linhas_esc.append(_linha)
                    st.dataframe(pd.DataFrame(_linhas_esc),
                                 width="stretch", hide_index=True)
                    st.caption(
                        f"Calculado com os dados desta sessão: âncora "
                        f"**{base_ancora['nome']}** ({euro(media_agregado)}/mês para o agregado "
                        f"médio) e rendimento equivalente "
                        f"{'médio' if indic_r == 'MEAN_EI' else 'mediano'} do EU-SILC de "
                        f"{rendimentos[indic_r]['PT']['ano']}. Muda com a âncora que escolher."
                    )
                else:
                    st.info(
                        "O quadro comparativo das escalas precisa do rendimento do EU-SILC, "
                        "que não está disponível nesta sessão."
                    )

                st.markdown("""
    Se as duas escalas coincidirem, **o esforço é constante** seja qual for a composição — ambos
    os lados escalam de forma idêntica. A subida com o número de pessoas resulta, portanto, da
    **diferença entre as escalas**. Isso não invalida a leitura, porque a alimentação tem
    economias de escala genuinamente mais fracas do que o consumo total; mas a **magnitude**
    depende da escala escolhida.

    **Como usar:** leia a **direção** como robusta e o **valor exato** como condicional. Teste
    sempre a sensibilidade mudando a escala na barra lateral.
                """)

            # ---- gráfico do cruzamento das escalas ----
            with st.expander("📐 Porque é que as escalas dão resultados diferentes — e cruzam"):
                st.markdown(f"""
Cada escala responde à mesma pergunta de forma diferente: **quanto custa cada pessoa a mais?**

| Escala | 1.ª pessoa | Cada pessoa a mais |
|---|---|---|
| Per capita | 1,0 | **1,0** — sem partilha |
| OCDE original | 1,0 | **0,7** — desconto moderado |
| OCDE modificada | 1,0 | **0,5** — desconto forte |

O que confunde: **todas partem do mesmo sítio** — a despesa do agregado médio português, com
**{('%.2f' % dim_efetiva).replace('.', ',')} pessoas**. A escala não calcula do zero: distribui
a partir dessa referência. Por isso **as três cruzam-se exatamente nessa dimensão**.
                """)

                tam = [1, 1.5, 2, 2.5, 3, 4, 5, 6]
                figS = go.Figure()
                cores_s = {"per_capita": "#7a5ea8", "ocde_original": VERDE,
                           "ocde_modificada": DOURADO}
                for chave in ESCALAS:
                    e_ = ESCALAS[chave]
                    eq_med = e_["primeiro"] + e_["adulto"] * (max(dim_efetiva, 1.0) - 1)
                    por_unidade = valor_medio_agregado / eq_med if eq_med else 0
                    ys = [por_unidade * (e_["primeiro"] + e_["adulto"] * (n - 1)) for n in tam]
                    figS.add_trace(go.Scatter(
                        x=tam, y=ys, name=e_["nome"].split(" (")[0],
                        line=dict(color=cores_s[chave], width=2.6),
                        hovertemplate="%{x} pessoas: %{y:.0f} €<extra>"
                                      + e_["nome"].split(" (")[0] + "</extra>"))
                figS.add_vline(
                    x=dim_efetiva, line_width=2, line_dash="dash", line_color="#64748b",
                    annotation_text=f"agregado médio: {('%.2f' % dim_efetiva).replace('.', ',')}",
                    annotation_position="top")
                figS.update_layout(height=340, margin=dict(t=46, b=40, l=10, r=10),
                                   xaxis_title="Pessoas no agregado (todas com 14+ anos)",
                                   yaxis_title="Despesa alimentar mensal (€)",
                                   legend=dict(orientation="h", y=1.22, x=0),
                                   hovermode="x unified", plot_bgcolor="#fff")
                figS.update_xaxes(gridcolor="#eef1f4")
                figS.update_yaxes(gridcolor="#eef1f4")
                st.plotly_chart(figS, width="stretch")

                st.success("""
**A leitura do gráfico — é isto que responde à dúvida.**

**À esquerda do cruzamento**, agregados **menores** que a média: a OCDE modificada dá valores
**mais altos**. Se cada pessoa a mais custa pouco (0,5), então ter menos gente do que a média
**poupa pouco** — fica-se perto do valor médio. Na per capita, em que cada pessoa vale a
totalidade, ter menos gente **desconta muito mais**.

**À direita**, agregados **maiores**: inverte-se. Se cada pessoa a mais custa pouco, acrescentar
gente **aumenta pouco** — e a OCDE modificada passa a dar os valores mais baixos.

**Em resumo:** desconto forte **comprime** as diferenças, aproximando todos os agregados da
média; desconto fraco **amplifica-as**. O cruzamento está sempre na dimensão média, porque é aí
que não há nada a descontar nem a acrescentar.
                """)


        # ---- acessibilidade alimentar: os três limiares, sempre juntos ----
        st.divider()
        st.markdown("#### Acessibilidade alimentar — três limiares, três respostas")
        st.caption(
            "«Conseguir pagar a comida» não é uma grandeza única. Consoante o limiar que se "
            "escolha, Portugal parece estar muito bem ou bastante mal — com dados oficiais em "
            "ambos os casos. Por isso os três aparecem sempre em conjunto."
        )

        _priv = dados.get("privacao", pd.DataFrame())
        _priv_pt = pd.DataFrame()
        if not _priv.empty:
            _priv_pt = _priv[(_priv["geo"] == "PT")].sort_values("time")

        _ano_sofi = max(SOFI_INCAPACIDADE["Portugal"])
        _sofi_pt = SOFI_INCAPACIDADE["Portugal"][_ano_sofi]
        _sofi_es = SOFI_INCAPACIDADE["Espanha"][_ano_sofi]
        _sofi_pessoas = SOFI_MILHOES.get(_ano_sofi)

        _sev, _ano_sev, _sev_pobres = None, None, None
        if not _priv_pt.empty:
            _tot = _priv_pt[_priv_pt["rskpovth"] == "TOTAL"]
            if not _tot.empty:
                _sev = float(_tot.iloc[-1]["valor"])
                _ano_sev = str(_tot.iloc[-1]["time"])
                _pob = _priv_pt[(_priv_pt["rskpovth"] == "B_60")
                                & (_priv_pt["time"] == _ano_sev)]
                if not _pob.empty:
                    _sev_pobres = float(_pob.iloc[0]["valor"])

        t1, t2, t3 = st.columns(3)
        t1.metric(
            "Privação severa" + (f" ({_ano_sev})" if _ano_sev else ""),
            f"{_sev:.1f} %".replace(".", ",") if _sev is not None else "—",
            help=("Não conseguir pagar uma refeição com carne, frango ou peixe — ou equivalente "
                  "vegetariano — de dois em dois dias. Eurostat, ilc_mdes03."))
        t2.metric(
            f"Não paga uma dieta saudável ({_ano_sofi})",
            f"{_sofi_pt:.1f} %".replace(".", ","),
            help=("Custo da dieta mais barata que cumpre os requisitos nutricionais. "
                  "FAO, SOFI 2026."))
        t3.metric(
            "Peso no orçamento do 1.º quintil",
            f"{IDF_PESO_ALIMENTAR['q1']:.1f} %".replace(".", ","),
            help="INE, IDF 2022/2023. Não é privação — é exposição.")

        _texto_sev = (f"**{('%.1f' % _sev).replace('.', ',')} %**" if _sev is not None
                      else "o indicador de privação severa")
        _texto_milhoes = (f", cerca de **{numero(_sofi_pessoas, 1)} milhões de pessoas**"
                          if _sofi_pessoas else "")
        st.markdown(f"""
        <div class="nota">
          <div class="tt">Porque é que estes três números não se substituem uns aos outros</div>
          Medem exigências muito diferentes. O primeiro — {_texto_sev} — é um limiar
          <strong>muito baixo</strong>: mede algo próximo da fome, e está em mínimo de série.
          O segundo é o nível intermédio, e é onde está o problema real:
          <strong>{('%.1f' % _sofi_pt).replace('.', ',')} %</strong> da população não consegue
          pagar uma dieta nutricionalmente adequada{_texto_milhoes}. O terceiro não é privação
          nenhuma — é <strong>exposição</strong>: quanto do orçamento dos 20 % mais pobres vai
          para comida.<br><br>
          Apresentar apenas o primeiro daria uma leitura indevidamente tranquilizadora: sugeriria
          um problema de <strong>{percentagem(_sev, sinal=False) if _sev is not None else '≈2 %'}</strong> da
          população, quando por um limiar nutricionalmente defensável são
          <strong>{percentagem(_sofi_pt, sinal=False)}</strong>.
          <strong>A fome severa recuou; a impossibilidade de comer bem não.</strong>
        </div>
        """, unsafe_allow_html=True)

        ca1, ca2 = st.columns(2)
        with ca1:
            st.markdown("**Privação severa — e quem a sofre**")
            st.caption("A média nacional esconde a diferença entre quem está e não está em "
                       "risco de pobreza.")
            if _priv_pt.empty:
                st.info("Série indisponível nesta sessão. Ver o registo de ligações "
                        "no separador Metodologia.")
            else:
                figp = go.Figure()
                _cores_p = {"TOTAL": CINZENTO, "B_60": VERMELHO, "A_60": AZUL}
                for nivel, rotulo in eurostat.PRIVACAO_NIVEIS.items():
                    sub = _priv_pt[_priv_pt["rskpovth"] == nivel]
                    if sub.empty:
                        continue
                    figp.add_trace(go.Scatter(
                        x=sub["time"], y=sub["valor"], name=rotulo, mode="lines+markers",
                        line=dict(color=_cores_p.get(nivel, CINZENTO),
                                  width=2.8 if nivel == "TOTAL" else 2),
                        hovertemplate="%{x}<br>%{y:.1f} %<extra>" + rotulo + "</extra>"))
                figp.update_layout(height=340, margin=dict(t=10, b=30, l=10, r=10),
                                   yaxis_title="% da população", plot_bgcolor="#fff",
                                   hovermode="x unified",
                                   legend=dict(orientation="h", y=-0.2))
                figp.update_yaxes(gridcolor="#eef1f4", rangemode="tozero")
                figp.update_xaxes(gridcolor="#eef1f4")
                st.plotly_chart(figp, width="stretch")
                if _sev_pobres is not None and _sev:
                    # O `.replace(".", ",")` aplicava-se à cadeia inteira — as
                    # f-strings adjacentes concatenam em tempo de compilação —, e
                    # não ao número. É o padrão que o C5 fechou em nove sítios e
                    # que sobreviveu neste (auditoria de 11.08.2026, E8).
                    st.caption(
                        f"Em {_ano_sev}, **{percentagem(_sev_pobres, sinal=False)}** entre quem está em risco "
                        f"de pobreza, contra **{percentagem(_sev, sinal=False)}** no total — "
                        f"**{numero(_sev_pobres / _sev, 1)}×** mais."
                    )

        with ca2:
            st.markdown("**Custo de uma dieta saudável**")
            st.caption("PPP$ por pessoa e por dia. Mínimo normativo, não despesa observada.")
            figc = go.Figure()
            _cores_c = {"Portugal": VERDE, "Europa": AZUL,
                        "Europa do Sul": DOURADO, "Espanha": "#7a5ea8"}
            for regiao, serie in SOFI_CUSTO.items():
                anos_c = sorted(serie)
                figc.add_trace(go.Scatter(
                    x=anos_c, y=[serie[a] for a in anos_c], name=regiao,
                    mode="lines+markers",
                    line=dict(color=_cores_c.get(regiao, CINZENTO),
                              width=2.8 if regiao == "Portugal" else 1.8,
                              dash=None if regiao == "Portugal" else "dot"),
                    hovertemplate="%{x}<br>%{y:.2f} PPP$<extra>" + regiao + "</extra>"))
            figc.update_layout(height=340, margin=dict(t=10, b=30, l=10, r=10),
                               yaxis_title="PPP$ por pessoa e por dia", plot_bgcolor="#fff",
                               hovermode="x unified",
                               legend=dict(orientation="h", y=-0.2))
            figc.update_yaxes(gridcolor="#eef1f4")
            figc.update_xaxes(gridcolor="#eef1f4", dtick=1)
            st.plotly_chart(figc, width="stretch")

        _custo_pt = SOFI_CUSTO["Portugal"][_ano_sofi]
        _custo_es = SOFI_CUSTO["Espanha"][_ano_sofi]
        st.success(f"""
    **O confronto com Espanha é o dado mais forte deste bloco.**

    Portugal e Espanha têm custo de uma dieta saudável praticamente igual —
    **{('%.2f' % _custo_pt).replace('.', ',')}** contra
    **{('%.2f' % _custo_es).replace('.', ',')} PPP$** por pessoa e por dia. Mas
    **{('%.1f' % _sofi_pt).replace('.', ',')} %** da população portuguesa não consegue pagá-la,
    contra **{('%.1f' % _sofi_es).replace('.', ',')} %** da espanhola.

    Com o mesmo preço e resultados tão diferentes, **a diferença não está nos preços — está nos
    rendimentos e na sua distribuição**. É a demonstração mais limpa de que um indicador de preços
    não é um indicador de acessibilidade, e vem com um par comparável em vez de uma afirmação.
        """)

        st.warning("""
    **O que estes indicadores não são.**

    **O custo da dieta saudável não é uma âncora de despesa.** É um **mínimo normativo** — o preço
    da dieta mais barata que cumpre os requisitos nutricionais —, não o que as famílias gastam.
    Compará-lo com a despesa alimentar apresentada no topo desta página seria confrontar objetos
    diferentes. Acresce que vem em **PPP$**, não em euros: converter exigiria a paridade de poder
    de compra do consumo privado, e mesmo assim não o tornaria comparável com despesa efetiva.

    **A privação severa é auto-reportada**, de inquérito por amostragem, e o Eurostat não publica
    intervalos de confiança para esta série. Variações de duas ou três décimas entre anos não
    devem ser lidas como tendência.

    **O SOFI é publicado em PDF, não em API** — ao contrário de tudo o resto nesta ferramenta, os
    seus valores estão inscritos no código e têm de ser atualizados à mão a cada edição anual.
        """)
        st.caption(f"Fontes: Eurostat `ilc_mdes03` · {SOFI_FONTE} · INE, IDF 2022/2023 (Q.2.11.b).")

        # Sendo inscrito à mão, o SOFI envelhece sem a aplicação dar erro
        # (auditoria de 10.08.2026, D4). O ano é tomado como 31 de dezembro,
        # a leitura mais favorável à fonte.
        _idade_sofi = idade_fonte(_ano_sofi, LIMITE_ANOS_SOFI * 365)
        if _idade_sofi["desatualizada"]:
            _anos_sofi = _idade_sofi["dias"] / 365.25
            st.error(
                f"⏳ **O SOFI apresentado é de {_ano_sofi}** — há cerca de "
                f"{numero(_anos_sofi, 1)} anos. Como é publicado em PDF e inscrito à mão em "
                "`src/config.py`, é provável que já exista pelo menos uma edição por "
                "incorporar. **Confirme antes de citar estes valores.**"
            )

        # ------- blocos recolhíveis lado a lado, para reduzir o deslocamento -------
        e1, e2, e3 = st.columns(3)

        with e1.expander("🧮 Como é calculado"):
            st.markdown("""
    **1 ·** Das Contas Nacionais vem a despesa anual de todas as famílias em produtos
    alimentares. Divide-se pelo número de agregados **desse mesmo ano** e por doze.

    **2 ·** O valor é trazido ao mês corrente pelo índice oficial de preços.

    **3 ·** Ajusta-se à composição do agregado pela escala de equivalência.

    **4 ·** Reparte-se pelos nove grupos com os ponderadores oficiais do índice.

    As fórmulas completas estão no separador **Metodologia**.
            """)
            st.warning(
                "**Não é um cabaz de compras.** Não há quilos nem litros: há euros e variações "
                "de preço. E os preços são médias nacionais do INE, não de uma insígnia concreta."
            )

        with e2.expander("👥 Comparar composições"):
            comps = [(1, 0, "1 adulto"), (2, 0, "Casal"), (1, 1, "Monoparental + 1"),
                     (1, 2, "Monoparental + 2"), (2, 1, "Casal + 1 criança"),
                     (2, 2, "Casal + 2 crianças"), (2, 3, "Casal + 3 crianças")]
            dm = dados.get("dimensao_media") or DIMENSAO_RECUO
            linhas_c = []
            for a, c, rot in comps:
                iv = intervalo_agregado(valor_medio_agregado, dm, a, c)
                linhas_c.append({
                    "Composição": rot, "Pessoas": a + c,
                    "Central (€)": round(despesa_do_agregado(
                        valor_medio_agregado, dm, a, c, "ocde_original"), 2),
                    "Mín. (€)": round(iv["minimo"], 2),
                    "Máx. (€)": round(iv["maximo"], 2),
                })
            st.dataframe(pd.DataFrame(linhas_c), width="stretch", hide_index=True)
            st.caption(
                f"Agregado médio nacional: {('%.2f' % dm).replace('.', ',')} pessoas. "
                "O intervalo resulta das diferentes escalas de equivalência."
            )

        with e3.expander("📋 Tabela detalhada"):
            tabela = df_decomp[["codigo", "classe", "classe_oficial", "ponderador",
                                "quota", "valor", "variacao", "contributo"]].copy()
            tabela.columns = ["Código", "Grupo", "Designação COICOP 2018",
                              "Ponderador (‰)", "Quota",
                              "Valor (€)", "Variação (%)", "Contributo (€)"]
            st.dataframe(tabela, width="stretch", hide_index=True,
                         column_config={
                             "Quota": st.column_config.ProgressColumn(
                                 "Quota", format="%.1f%%", min_value=0, max_value=1),
                             "Valor (€)": st.column_config.NumberColumn(format="%.2f"),
                             "Variação (%)": st.column_config.NumberColumn(format="%.1f"),
                             "Contributo (€)": st.column_config.NumberColumn(format="%.2f"),
                             "Ponderador (‰)": st.column_config.NumberColumn(format="%.1f"),
                         })
            st.download_button(
                "⬇️ CSV", csv_com_fonte(tabela, "Decomposicao por grupo de produto", dados,
                                        # A ancora pode ser do INE (IDF) ou do
                                        # Eurostat (Contas Nacionais): o cabecalho
                                        # segue a que estiver ativa.
                                        fonte=(f"{base_ancora['fonte']} (ancora da despesa) + "
                                               "Eurostat, IHPC (ponderadores e variacoes)"),
                                        extra=[("Base de calculo", base_ancora["nome"]),
                                               ("Composicao do agregado", composicao),
                                               ("Escala", ESCALAS[escala_chave]["nome"])]),
                f"despesa_alimentar_decomposicao_{date.today()}.csv", "text/csv",
                width="stretch")

    # ==========================================================================
    # ABA 2 — Histórico
    # ==========================================================================
with aba2:
    with painel("Histórico"):
        st.markdown("#### Índice de preços dos produtos alimentares — Portugal")

        base = dados.get("base_indice") or "—"
        st.info(f"""
    **Em que consiste o índice.** Não são euros. É um número que mede o **nível dos preços**
    relativamente a um ano de referência, ao qual se atribui o valor 100. A base atualmente em
    vigor é **{base}**: se o índice estiver em 118, os preços dos produtos alimentares estão
    18 % acima do que estavam nesse ano de referência.

    O índice **não diz quanto custa** um cabaz — diz de quanto os preços se afastaram do
    ponto de partida. É por isso que a despesa em euros do primeiro separador precisa de uma
    âncora nas Contas Nacionais: o índice sozinho nunca daria um valor em euros.

    A **variação homóloga** (linha vermelha) é derivada do índice: compara cada mês com o mesmo
    mês do ano anterior.
        """)

        if dados["indice_pt"].empty:
            st.info("Sem série de índices disponível.")
            periodos, inicio_sel, fim_sel = [], None, None
        else:
            periodos = sorted(dados["indice_pt"]["time"].unique())
            pre = periodos[-25] if len(periodos) > 25 else periodos[0]
            inicio_sel, fim_sel = st.select_slider(
                "Intervalo a apresentar",
                options=periodos, value=(pre, periodos[-1]),
                format_func=mes_pt,
            )
            st.caption(
                f"A mostrar de **{mes_pt(inicio_sel)}** a **{mes_pt(fim_sel)}** — "
                f"{periodos.index(fim_sel) - periodos.index(inicio_sel) + 1} meses. "
                "Arraste as extremidades para alterar."
            )

            idx_sel = dados["indice_pt"][
                (dados["indice_pt"]["time"] >= inicio_sel) &
                (dados["indice_pt"]["time"] <= fim_sel)]
            var_sel = dados["var_pt"][
                (dados["var_pt"]["time"] >= inicio_sel) &
                (dados["var_pt"]["time"] <= fim_sel)]

            # Se a série da variação não cobrir todo o intervalo escolhido, a linha
            # vermelha aparece truncada — e isso tem de ser dito, não descoberto.
            if not var_sel.empty and len(var_sel) < len(idx_sel):
                st.warning(
                    f"A linha da **variação homóloga** só cobre "
                    f"{mes_pt(var_sel['time'].min())} a {mes_pt(var_sel['time'].max())} — "
                    f"{len(var_sel)} dos {len(idx_sel)} meses do intervalo escolhido. O índice "
                    "recua mais do que a série de variação disponível nesta sessão."
                )
            elif var_sel.empty:
                st.warning(
                    "Não há variação homóloga publicada para o intervalo escolhido: o gráfico "
                    "mostra apenas o índice."
                )

            st.plotly_chart(
                grafico_historico(idx_sel, var_sel, len(idx_sel)),
                width="stretch",
            )

            if len(idx_sel) >= 2:
                acum = (idx_sel["valor"].iloc[-1] / idx_sel["valor"].iloc[0] - 1) * 100
                st.info(
                    f"**Variação acumulada no intervalo escolhido: {percentagem(acum)}** — "
                    f"de {mes_pt(inicio_sel)} a {mes_pt(fim_sel)}. "
                    "É frequentemente a leitura mais eloquente: a taxa homóloga de um mês "
                    "isolado diz pouco; o acumulado desde uma data de referência diz muito."
                )

        var_pt = dados["var_pt"]
        if not var_pt.empty and inicio_sel is not None:
            janela = var_pt[(var_pt["time"] >= inicio_sel) &
                            (var_pt["time"] <= fim_sel)]["valor"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Variação mais recente", percentagem(var_pt["valor"].iloc[-1]),
                      help=f"Mês de referência: {mes_pt(var_pt['time'].iloc[-1])}")
            if len(janela):
                c2.metric("Média do intervalo", percentagem(janela.mean()))
                c3.metric("Máximo do intervalo", percentagem(janela.max()))
                c4.metric("Mínimo do intervalo", percentagem(janela.min()))

        st.caption(
            "Frequência mensal — a mais fina publicada por fonte oficial. Existem séries semanais "
            "de cabazes publicadas por entidades privadas, mas não são dados oficiais nem têm "
            "acesso automático, e as variações semanais são muito voláteis por efeitos de base."
        )

        # ---------- o que está por trás da inflação alimentar ----------
        agr_esp = dados.get("agregados_especiais")
        if agr_esp is not None and not agr_esp.empty:
            st.divider()
            st.markdown("#### O que está por trás da subida")
            st.info("""
    A alimentação não é um bloco homogéneo. **Os frescos e os transformados obedecem a lógicas
    diferentes** — e distingui-los muda a resposta de política:

    - **Não transformados** (carne, peixe, fruta, legumes) reagem a clima, sazonalidade e custos de
      transporte. Uma subida aqui é tipicamente **choque de oferta**: passa, mas dói no imediato.
    - **Transformados** (pão, laticínios, conservas) refletem custos de produção e distribuição já
      incorporados. Uma subida aqui tende a ser **mais persistente**.

    Um choque de oferta em frescos não se combate com os mesmos instrumentos que uma inflação
    instalada nos transformados. Daí que a decomposição não seja um detalhe técnico.
            """)

            pt_esp = agr_esp[agr_esp["geo"] == "PT"]
            meses_esp = sorted(pt_esp["time"].unique())
            if inicio_sel is not None:
                meses_esp = [m for m in meses_esp if inicio_sel <= m <= fim_sel]
                # Se a série não cobrir todo o intervalo escolhido, isso tem de
                # ser dito — não descoberto por o gráfico começar mais tarde.
                _esperados = [p for p in periodos if inicio_sel <= p <= fim_sel]
                if meses_esp and len(meses_esp) < len(_esperados):
                    st.warning(
                        f"Estes agregados só cobrem {mes_pt(meses_esp[0])} a "
                        f"{mes_pt(meses_esp[-1])} — {len(meses_esp)} dos "
                        f"{len(_esperados)} meses do intervalo escolhido. O índice recua "
                        "mais do que a série disponível nesta sessão."
                    )
                elif not meses_esp:
                    st.warning(
                        "Não há observações destes agregados no intervalo escolhido."
                    )

            so_alim = st.toggle(
                "Mostrar também os agregados de enquadramento", value=False,
                help=("Inflação geral e subjacente. Não são alimentação — servem para situar "
                      "a subida alimentar no conjunto dos preços."))
            visiveis = [a for a in AGREGADOS
                        if so_alim or a["grupo"] == "alimentacao"]

            if visiveis and meses_esp:
                figA = go.Figure()
                for a in visiveis:
                    sub = pt_esp[pt_esp["coicop"] == a["cod"]].set_index("time")["valor"]
                    if sub.empty:
                        continue
                    figA.add_trace(go.Scatter(
                        x=[mes_pt(m) for m in meses_esp],
                        y=[sub.get(m) for m in meses_esp],
                        name=a["nome"],
                        line=dict(color=a["cor"], width=a["larg"],
                                  dash="dot" if a["grupo"] == "enquadramento" else "solid"),
                        hovertemplate="%{x}<br>%{y:.1f} %<extra>" + a["nome"] + "</extra>"))
                figA.update_layout(height=400, margin=dict(t=20, b=40, l=10, r=10),
                                   yaxis_title="Variação homóloga (%)",
                                   legend=dict(orientation="h", y=1.16, x=0),
                                   hovermode="x unified", plot_bgcolor="#fff")
                figA.update_xaxes(showgrid=False)
                figA.update_yaxes(gridcolor="#eef1f4", zerolinecolor="#cbd5e1")
                st.plotly_chart(figA, width="stretch")
                if so_alim:
                    st.caption("A tracejado, os agregados de enquadramento — não são alimentação.")

                ult_esp = meses_esp[-1]
                linhas_a = []
                for a in visiveis:
                    sub = pt_esp[(pt_esp["coicop"] == a["cod"]) & (pt_esp["time"] == ult_esp)]
                    if sub.empty:
                        continue
                    ue_sub = agr_esp[(agr_esp["geo"] == "EU27_2020") &
                                     (agr_esp["coicop"] == a["cod"]) &
                                     (agr_esp["time"] == ult_esp)]
                    linhas_a.append({
                        "": ("🍽️" if a["grupo"] == "alimentacao" else "📊"),
                        "Agregado": a["nome"],
                        "Portugal (%)": round(float(sub["valor"].iloc[0]), 1),
                        "UE-27 (%)": (round(float(ue_sub["valor"].iloc[0]), 1)
                                      if not ue_sub.empty else None),
                        "Para que serve": a["porque"],
                    })
                if linhas_a:
                    st.dataframe(pd.DataFrame(linhas_a), width="stretch", hide_index=True)
                    st.caption(
                        f"Variação homóloga em {mes_pt(ult_esp)}. 🍽️ componentes da alimentação · "
                        "📊 agregados de enquadramento, que não são alimentação."
                    )
                    st.download_button(
                        "⬇️ Descarregar (CSV com fonte)",
                        csv_com_fonte(pd.DataFrame(linhas_a).drop(columns=[""]),
                                      "Decomposicao da inflacao alimentar", dados,
                                      extra=[("Mes de referencia", ult_esp)]),
                        f"despesa_alimentar_decomposicao_{date.today()}.csv", "text/csv")

        # ---- viés de substituição: cabaz fixo contra Törnqvist ----
        _cmp_idx = indices_comparados(dados.get("indice_classes", pd.DataFrame()),
                                      dados.get("pesos_por_ano", pd.DataFrame()))
        if not _cmp_idx.empty and len(_cmp_idx) >= 3:
            st.divider()
            st.markdown("#### Cabaz fixo contra cabaz que acompanha o consumo")
            st.caption(
                "A crítica central ao cabaz de composição fixa é que não acompanha a substituição "
                "de consumo. Aqui essa crítica é medida, em vez de afirmada — comparando um índice "
                "de ponderadores congelados com um índice superlativo de Törnqvist, que usa a "
                "média dos ponderadores dos dois extremos de cada ano."
            )

            _ano_base = int(_cmp_idx["ano"].iloc[0])
            # O ano-base é fixo em `config.py`. Se não estiver disponível nos
            # dados, a série recua — e isso tem de ser dito, porque o valor do
            # viés depende do ano-base (auditoria de 11.08.2026, E14).
            if _cmp_idx.attrs.get("ano_base_pedido") != _ano_base:
                st.warning(
                    f"**Ano-base substituído.** O painel está fixado em dezembro de "
                    f"**{_cmp_idx.attrs.get('ano_base_pedido')}**, mas essa observação não está "
                    f"disponível nesta sessão. Os índices foram encadeados a partir de dezembro "
                    f"de **{_ano_base}**, pelo que o viés acumulado **não é comparável** com o "
                    "que consta de versões anteriores deste documento."
                )
            _ult = _cmp_idx.iloc[-1]
            _ano_fim = int(_ult["ano"])

            # O índice oficial do agregado, rebaseado ao mesmo dezembro. A base
            # do índice é irrelevante depois de rebasear: é um rácio interno.
            _oficial = None
            _ipt = dados["indice_pt"]
            if not _ipt.empty:
                _d = _ipt[_ipt["time"].astype(str).str.endswith("-12")].copy()
                if not _d.empty:
                    _d["ano"] = _d["time"].astype(str).str[:4].astype(int)
                    _s = _d.groupby("ano")["valor"].last()
                    if _ano_base in _s.index:
                        _oficial = _s / _s.loc[_ano_base] * 100

            _subida_fixo = _ult["laspeyres_fixo"] - 100
            _subida_torn = _ult["tornqvist"] - 100
            _vies = float(_ult["vies"])
            _anos_decorridos = max(_ano_fim - _ano_base, 1)

            k1, k2, k3 = st.columns(3)
            k1.metric(f"Cabaz fixo — subida desde dez/{str(_ano_base)[2:]}",
                      percentagem(_subida_fixo),
                      help="Ponderadores congelados no ano-base, como num cabaz de "
                           "composição fixa.")
            k2.metric("Törnqvist — a mesma subida", percentagem(_subida_torn),
                      help="Ponderadores revistos a cada ano, pela média dos dois extremos.")
            k3.metric("Viés de substituição acumulado",
                      pontos(_vies, sufixo=" pontos"),
                      pontos(_vies / _anos_decorridos, sufixo=" p.p./ano"),
                      delta_color="off",
                      help="Quanto o cabaz fixo sobrestima a subida, face ao índice superlativo.")

            figt = go.Figure()
            figt.add_trace(go.Scatter(
                x=_cmp_idx["ano"], y=_cmp_idx["laspeyres_fixo"], name="Cabaz fixo (Laspeyres)",
                mode="lines+markers", line=dict(color=VERMELHO, width=2.6),
                hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"))
            figt.add_trace(go.Scatter(
                x=_cmp_idx["ano"], y=_cmp_idx["tornqvist"], name="Törnqvist (superlativo)",
                mode="lines+markers", line=dict(color=VERDE, width=2.6),
                hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"))
            if _oficial is not None:
                _al = [a for a in _cmp_idx["ano"] if a in _oficial.index]
                figt.add_trace(go.Scatter(
                    x=_al, y=[_oficial.loc[a] for a in _al], name="IHPC oficial (publicado)",
                    mode="lines", line=dict(color=AZUL, width=1.8, dash="dot"),
                    hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"))
            figt.update_layout(height=380, margin=dict(t=10, b=30, l=10, r=10),
                               yaxis_title=f"Índice (dez/{_ano_base} = 100)",
                               plot_bgcolor="#fff", hovermode="x unified",
                               legend=dict(orientation="h", y=-0.18))
            figt.update_yaxes(gridcolor="#eef1f4")
            figt.update_xaxes(gridcolor="#eef1f4", dtick=1)
            st.plotly_chart(figt, width="stretch")

            st.info(f"""
    **O resultado não é o que a crítica ao cabaz fixo faria esperar — e isso importa.**

    Em {_anos_decorridos} anos, congelar os ponderadores das nove classes sobrestima a subida em
    **{pontos(_vies, sufixo=" pontos de índice")}**, cerca de
    **{pontos(_vies / _anos_decorridos, sufixo=" p.p. por ano")}**. Sobre uma subida
    acumulada de {percentagem(_subida_torn)}, é residual.

    A razão é que **a substituição relevante acontece dentro das classes, não entre elas**. Trocar
    novilho por frango não muda o peso da carne; trocar marca própria por marca de fabricante não
    muda o peso de nada. Nove classes COICOP são uma grelha demasiado grossa para ver o que as
    famílias efetivamente fazem.

    **A conclusão prática tem dois lados.** Primeiro: quem atacar o índice oficial invocando viés
    de substituição *entre grupos de alimentos* está a invocar um efeito que aqui se mede e é
    pequeno. Segundo, e mais importante: isto **não absolve** o cabaz de composição fixa. O problema
    de um cabaz de 63 produtos com quantidades fixas é de outra ordem — não capta a mudança de
    marca, de calibre, de embalagem nem de insígnia, e nenhuma dessas é observável nestes dados.
    O efeito que se mede aqui é o menor dos dois; o maior fica por medir.
            """)

            _excl = _cmp_idx.attrs.get("classes_excluidas") or []
            if _excl:
                _nomes_excl = ", ".join(POR_CODIGO[c]["nome"] for c in _excl
                                        if c in POR_CODIGO)
                st.warning(
                    f"**Cobertura reduzida.** {len(_excl)} das nove classes não têm série "
                    f"completa em todos os dezembros do período e ficaram de fora deste "
                    f"cálculo: **{_nomes_excl}**. Os dois índices são comparáveis entre si — "
                    "usam exatamente as mesmas classes —, mas não cobrem todo o cabaz alimentar."
                )

            with st.expander("Como estes índices são construídos"):
                st.markdown(f"""
    Todos partem de dezembro de {_ano_base} = 100 e usam o índice mensal por classe
    (`prc_hicp_minr`) e os ponderadores anuais (`prc_hicp_iw`), ambos do Eurostat.
    Entram as **{len(_cmp_idx.attrs.get('classes_usadas') or [])} classes** com série completa em
    todos os dezembros do período: uma classe sem observação num único mês eliminaria esse mês da
    comparação, e com ele o elo do índice.

    **Cabaz fixo (Laspeyres de base fixa)** — as quotas do ano-base aplicadas ao relativo de preço
    acumulado desde esse ano:
                """)
                st.latex(r"P_L(t) = \sum_i w_i(0)\,\frac{I_i(t)}{I_i(0)}")
                st.markdown(
                    "**Törnqvist** — média geométrica ponderada dos relativos de cada elo, com a "
                    "média aritmética das quotas dos dois extremos:")
                st.latex(r"\ln P_T(t\!-\!1 \to t) = \sum_i \frac{s_i(t\!-\!1)+s_i(t)}{2}"
                         r"\,\ln\frac{I_i(t)}{I_i(t\!-\!1)}")
                st.warning("""
    **Aproximação a declarar.** O Törnqvist exige as quotas de despesa observadas nos dois extremos
    de cada elo. O que existe em fonte aberta são os ponderadores do IHPC, que o Documento
    Metodológico do IPC define como referidos a **dezembro do ano n−1** e já atualizados a preços
    desse momento. A correspondência adotada decorre dessa definição: o elo de dezembro de y−1 a
    dezembro de y usa a média dos ponderadores de y e de y+1. Para o último elo, o ponderador de
    y+1 ainda não está publicado e repete-se o de y.

    Não é o Törnqvist exato. É a melhor aproximação sem microdados de despesa anuais — e o facto de
    a série resultante acompanhar de perto o IHPC oficial, que é construído por outra via, é
    indício de que a aproximação se comporta.
                """)

            st.download_button(
                "⬇️ Descarregar comparação de índices (CSV)",
                csv_com_fonte(_cmp_idx, "Vies de substituicao - cabaz fixo contra Tornqvist", dados,
                              fonte="Eurostat, IHPC (ECOICOP v2) - calculo da UPE",
                              conjuntos=[eurostat.HICP_MENSAL, eurostat.HICP_PONDERADORES],
                              extra=[
                                  ("Base", f"dezembro de {_ano_base} = 100"),
                                  ("Series", "prc_hicp_minr (indice por classe) e prc_hicp_iw"),
                                  ("Nota", "Tornqvist aproximado - ver metodologia no separador"),
                              ]),
                file_name="vies_substituicao.csv", mime="text/csv")

        serie = dados["indice_pt"][["time", "valor"]].rename(
            columns={"time": "Período", "valor": f"Índice ({base})"})
        var_tab = dados["var_pt"][["time", "valor"]].rename(
            columns={"time": "Período", "valor": "Variação homóloga (%)"})
        junto = serie.merge(var_tab, on="Período", how="outer").sort_values("Período")

        st.download_button(
            "⬇️ Descarregar série completa (CSV com fonte)",
            csv_com_fonte(junto, "Serie do indice de precos alimentares - Portugal", dados,
                          extra=[("Base do indice", base), ("Classe COICOP", "CP011")]),
            f"despesa_alimentar_serie_{date.today()}.csv", "text/csv",
        )

    # ==========================================================================
    # ABA 6 — Da produção ao consumo
    # ==========================================================================
with aba6:
    with painel("Da produção ao consumo"):
        st.markdown("#### Onde na cadeia está o aumento")
        st.caption(
            "Todos os outros indicadores desta ferramenta medem o que o consumidor paga ou "
            "quanto as famílias gastam. Nenhum diz se a subida nasceu na exploração agrícola, "
            "na transformação ou na distribuição. O Observatório de Preços Agroalimentar do GPP "
            "é a única fonte pública que segue o mesmo produto nas duas pontas da cadeia."
        )

        _obs, _obs_meta = observatorio.carregar()
        if _obs.empty:
            st.warning(
                "**Sem dados recolhidos.** O Observatório não tem API: a série é obtida por "
                "`scripts/recolher_observatorio.py`, que escreve `dados/observatorio.csv`. "
                "Execute o script para preencher este separador."
            )
        else:
            _var = observatorio.variacoes(_obs)
            _com_prod = _var[_var["tem_producao"]].copy()
            _ini = _obs["inicio"].min()
            _fim = _obs["inicio"].max()

            o1, o2, o3, o4 = st.columns(4)
            o1.metric("Produtos seguidos", f"{_obs['produto'].nunique()}")
            o2.metric("Com as duas fases", f"{len(_com_prod)}",
                      help="Só para estes é possível comparar produção e consumo.")
            o3.metric("Períodos de quatro semanas", f"{_obs['inicio'].nunique()}")
            o4.metric("Última observação", _fim.strftime("%d/%m/%Y"))

            st.caption(
                f"Série de {_ini.strftime('%d/%m/%Y')} a **{_fim.strftime('%d/%m/%Y')}** "
                f"— é esta a data que conta. Recolhido em "
                f"{_obs_meta.get('extraido_em', '—')} · {_obs_meta.get('fonte', 'GPP')}."
            )

            # O Observatório não tem API. A verificação media a data em que o
            # **script correu**, não a da última observação — e as duas divergem
            # justamente no caso que interessa: correr o script sobre uma fonte
            # que não publicou não torna os dados recentes
            # (auditoria de 10.08.2026, D4; corrigido a 12.08.2026, K2).
            _fresc_obs = frescura_do_observatorio(
                _fim, _obs_meta.get("extraido_em"), LIMITE_DIAS_OBSERVATORIO)

            if _fresc_obs["fonte_parou"]:
                # Recolha fresca, série parada: a falha não é de quem recolhe.
                st.error(
                    f"⛔ **O Observatório não publica desde "
                    f"{_fim.strftime('%d/%m/%Y')}** — há "
                    f"**{numero(_fresc_obs['serie']['dias'])} dias**, quando o normal seria no "
                    f"máximo {numero(LIMITE_DIAS_OBSERVATORIO)}. Faltam cerca de "
                    f"**{_fresc_obs['periodos_em_falta']} períodos** de quatro semanas.\n\n"
                    f"A recolha é recente — de {_obs_meta.get('extraido_em', '—')}, há "
                    f"{numero(_fresc_obs['recolha']['dias'])} dias —, pelo que **correr de novo "
                    "o script não resolve**: é a fonte que não avançou. Confirme em "
                    "observatorioagroalimentar.gov.pt antes de citar estes números como "
                    "situação corrente.\n\n"
                    "As comparações entre produtos e entre fases mantêm-se válidas — são "
                    "janelas de vários anos e não dependem do último período."
                )
            elif _fresc_obs["parada"]:
                # A série está velha e a recolha também: falta correr o script.
                st.warning(
                    f"⏳ **A última observação é de {_fim.strftime('%d/%m/%Y')}** — há "
                    f"**{numero(_fresc_obs['serie']['dias'])} dias**, cerca de "
                    f"{_fresc_obs['periodos_em_falta']} períodos. A recolha também tem "
                    f"{numero(_fresc_obs['recolha']['dias'])} dias: o Observatório publica de "
                    "quatro em quatro semanas e não tem API — a série só avança quando alguém "
                    "correr `scripts/recolher_observatorio.py`."
                )
            elif _fresc_obs["recolha_velha"]:
                st.warning(
                    f"⏳ **A recolha tem {numero(_fresc_obs['recolha']['dias'])} dias.** A série "
                    f"está em dia até {_fim.strftime('%d/%m/%Y')}, mas convém correr "
                    "`scripts/recolher_observatorio.py` para apanhar o período seguinte."
                )

            st.warning("""
    **A diferença entre o preço no consumo e o preço na produção não é a margem de ninguém.**

    Inclui transporte, transformação, embalagem, distribuição e IVA. E as duas fases podem
    referir-se a **formas diferentes do mesmo produto** — peixe inteiro contra posta, animal vivo
    contra peça desmanchada. Por isso a diferença **não é comparável entre produtos** e **não deve
    ser lida como lucro** de nenhum operador. O que estes dados mostram com segurança é *onde* os
    preços se moveram, não *quem* decidiu o quê.
            """)

            # ---- panorama dos produtos com as duas fases ----
            st.markdown("**Os dois lados da cadeia, por produto**")
            # A janela **não é a mesma para todos os produtos**: cada variação é
            # medida no período comum às duas fases desse produto, que em vários
            # casos é bem mais curto do que a série global. A legenda anterior
            # anunciava a data mínima global, e era falsa para metade dos
            # produtos (auditoria de 10.08.2026, C4).
            if not _com_prod.empty:
                _n_min, _n_max = int(_com_prod["n_periodos"].min()), int(_com_prod["n_periodos"].max())
                _cap_janela = (
                    f"Cada produto é medido **no seu próprio período comum às duas fases** — "
                    f"entre {_n_min} e {_n_max} períodos de quatro semanas, conforme o produto. "
                    "As janelas estão na tabela abaixo; **as variações não são comparáveis entre "
                    "produtos com janelas diferentes**. Só os produtos com série de produção "
                    "aparecem aqui."
                )
            else:
                _cap_janela = "Só os produtos com série de produção aparecem aqui."
            st.caption(_cap_janela)

            if _com_prod.empty:
                st.info("Nenhum produto tem as duas fases nesta recolha.")
            else:
                _ord = _com_prod.sort_values("consumo_var")
                figo = go.Figure()
                figo.add_trace(go.Bar(
                    y=_ord["produto"], x=_ord["producao_var"], orientation="h",
                    name="Produção", marker_color=DOURADO,
                    hovertemplate="%{y}<br>Produção: %{x:+.1f} %<extra></extra>"))
                figo.add_trace(go.Bar(
                    y=_ord["produto"], x=_ord["consumo_var"], orientation="h",
                    name="Consumo", marker_color=VERDE,
                    hovertemplate="%{y}<br>Consumo: %{x:+.1f} %<extra></extra>"))
                figo.update_layout(barmode="group", height=max(360, 34 * len(_ord)),
                                   margin=dict(t=10, b=40, l=10, r=10),
                                   xaxis_title="Variação desde o início da série (%)",
                                   plot_bgcolor="#fff",
                                   legend=dict(orientation="h", y=-0.08))
                figo.update_xaxes(gridcolor="#eef1f4", zerolinecolor="#cbd5e1")
                st.plotly_chart(figo, width="stretch")

                _tab_o = pd.DataFrame([{
                    "Produto": r.produto,
                    "Janela medida": (f"{r.inicio.strftime('%m/%Y')} – "
                                      f"{r.fim.strftime('%m/%Y')}"),
                    "Períodos": int(r.n_periodos),
                    "Preço na produção: variação na janela": (
                        f"{r.producao_var:+.1f} %".replace(".", ",")),
                    "Preço no consumo: variação na janela": (
                        f"{r.consumo_var:+.1f} %".replace(".", ",")),
                    "Diferença consumo−produção": (
                        f"{r.diferenca_var:+.1f} %".replace(".", ",")
                        if pd.notna(r.diferenca_var) else "—"),
                    "Padrão": r.padrao,
                } for r in _com_prod.itertuples()])
                st.dataframe(_tab_o, width="stretch", hide_index=True)
                st.caption(
                    "**De que é esta percentagem.** É a variação do **preço em euros por "
                    "unidade** em cada fase, entre o primeiro e o último período da coluna "
                    "«Janela medida» — que é a janela **comum às duas fases**, para que as duas "
                    "colunas sejam comparáveis entre si. Não é uma quota nem uma fatia de nada: "
                    "*+20 %* significa que o preço nessa fase está 20 % acima do que estava no "
                    "início da janela. A última coluna é a variação da **diferença** entre as "
                    "duas pontas — e vale a ressalva do topo do separador: essa diferença não é "
                    "a margem de ninguém."
                )

            # ---- o que os padrões significam ----
            _contagem = _var["padrao"].value_counts()
            st.markdown("**Três padrões que a leitura agregada do cabaz esconde**")
            for nome, explicacao in observatorio.PADROES.items():
                if nome not in _contagem:
                    continue
                exemplos = _var[_var["padrao"] == nome]["produto"].head(4).tolist()
                st.markdown(
                    f"- **{nome}** ({_contagem[nome]}) — {explicacao} "
                    f"*Ex.: {', '.join(exemplos)}.*"
                )

            _div = _var[_var["padrao"] == "Divergência"]
            if not _div.empty:
                _d = _div.iloc[0]
                st.error(f"""
    **{_d['produto']} é o caso mais nítido — e o que justifica este separador.**

    O preço na produção **desce {percentagem(abs(_d['producao_var']), sinal=False)}** enquanto o
    preço ao consumidor **sobe {percentagem(_d['consumo_var'], sinal=False)}**. A diferença entre
    as duas pontas passa de {euro(_d['diferenca_inicial'])} para {euro(_d['diferenca_final'])}
    por {_d['unidade'] or 'unidade'}.

    Nenhum índice de preços mostra isto: para o IHPC, é apenas mais um produto que subiu. Mantém-se
    integralmente a ressalva acima — o alargamento da diferença não é, por si, margem de ninguém, e
    pode refletir mudança de forma do produto entre as duas fases.
                """)

            # ---- detalhe por produto ----
            st.divider()
            st.markdown("**Ver um produto em detalhe**")
            _lista = sorted(_var["produto"].unique())
            _pref = next((p for p in ("Pescada", "Ovo M", "Cenoura") if p in _lista), _lista[0])
            _escolhido = st.selectbox(
                "Produto", options=_lista, index=_lista.index(_pref),
                label_visibility="collapsed")

            _serie = observatorio.serie_produto(_obs, _escolhido)
            _linha = _var[_var["produto"] == _escolhido].iloc[0]
            if _serie.empty:
                st.info("Sem série para este produto.")
            else:
                figd2 = go.Figure()
                _cores_f = {"Consumo": VERDE, "Produção": DOURADO}
                for coluna in _serie.columns:
                    figd2.add_trace(go.Scatter(
                        x=_serie.index, y=_serie[coluna], name=coluna, mode="lines",
                        line=dict(color=_cores_f.get(coluna, CINZENTO), width=2.6),
                        hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f} €<extra>" + coluna + "</extra>"))
                if {"Consumo", "Produção"}.issubset(set(_serie.columns)):
                    figd2.add_trace(go.Scatter(
                        x=_serie.index, y=_serie["Consumo"] - _serie["Produção"],
                        name="Diferença", mode="lines",
                        line=dict(color=AZUL, width=1.6, dash="dot"),
                        hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f} €<extra>Diferença</extra>"))
                figd2.update_layout(
                    height=380, margin=dict(t=10, b=30, l=10, r=10),
                    yaxis_title=f"Preço ({_linha['unidade'] or '€'})",
                    plot_bgcolor="#fff", hovermode="x unified",
                    legend=dict(orientation="h", y=-0.16))
                figd2.update_yaxes(gridcolor="#eef1f4", rangemode="tozero")
                figd2.update_xaxes(gridcolor="#eef1f4")
                st.plotly_chart(figd2, width="stretch")

                if not _linha["tem_producao"]:
                    st.info(
                        "O Observatório publica apenas o preço ao consumidor para este produto. "
                        "A comparação com a produção não é possível."
                    )

            st.download_button(
                "⬇️ Descarregar série completa do Observatório (CSV)",
                csv_com_fonte(
                    _obs.assign(inicio=_obs["inicio"].dt.strftime("%Y-%m-%d")),
                    "Observatorio de Precos Agroalimentar - producao e consumo", dados,
                    # Nao e Eurostat: estes dados nunca passaram por la.
                    fonte="GPP - Gabinete de Planeamento, Politicas e Administracao Geral",
                    conjuntos=[],
                    extra=[
                        ("Fonte", "GPP - Observatorio de Precos Agroalimentar"),
                        ("Recolha", _obs_meta.get("extraido_em", "-")),
                        ("Script", "scripts/recolher_observatorio.py"),
                        ("Nota", "A diferenca consumo-producao nao e margem de nenhum operador"),
                    ]),
                file_name="observatorio_precos.csv", mime="text/csv")

    # ==========================================================================
    # ABA 3 — Simulador de IVA
    # ==========================================================================
with aba3:
    with painel("Simulador de IVA"):
        st.markdown("#### Cenário hipotético de alteração do IVA")

        CENARIOS = {
            "manual": ("✏️ Definir manualmente", None),
            "zero": ("🧺 «Cabaz zero» — isenção total (precedente 2023-24)", 0.0),
            "seis": ("📉 Taxa reduzida (6 %) em tudo", 6.0),
            "treze": ("📊 Taxa intermédia (13 %) em tudo", 13.0),
        }
        # O estado de sessão persiste entre versões da aplicação. Se ficar com um
        # valor que já não existe nas opções atuais, o Streamlit levanta exceção —
        # por isso valida-se antes de usar.
        if st.session_state.get("cenario_iva") not in CENARIOS:
            st.session_state["cenario_iva"] = "zero"

        esq, dir_ = st.columns([2, 1])
        with dir_:
            cenario = st.radio(
                "Cenário a simular",
                options=list(CENARIOS.keys()),
                format_func=lambda k: CENARIOS[k][0],
                key="cenario_iva",
            )
        with esq:
            st.markdown("**Quanto da descida do imposto chega ao preço na prateleira?**")
            # O valor de partida é calibrado, não escolhido: vem da avaliação do
            # Banco de Portugal ao «IVA zero» de 2023. Até 12.08.2026 partia de
            # 40 %, um parâmetro de trabalho sem fonte portuguesa, que a
            # evidência contraria por um fator de 2,4 (auditoria, F1).
            repercussao = st.slider(
                "Fração que chega ao consumidor", 0, 100,
                int(round(REPERCUSSAO_PADRAO * 100)), 5,
                format="%d %%", label_visibility="collapsed",
            ) / 100

            ao_consumidor = int(round(repercussao * 100))
            na_margem = 100 - ao_consumidor
            st.markdown(f"""
    <div style="background:#f5f7f9;border-radius:8px;padding:11px 14px;font-size:13px;margin-top:2px">
    Por cada <strong>1,00 €</strong> de imposto que o Estado deixa de cobrar:
    <div style="display:flex;gap:18px;margin-top:8px">
      <div style="flex:1">
        <div style="font-size:20px;font-weight:600;color:{VERDE}">{ao_consumidor} cêntimos</div>
        <div style="font-size:11.5px;color:#4a4a48">descem o preço — poupança do consumidor</div>
      </div>
      <div style="flex:1">
        <div style="font-size:20px;font-weight:600;color:{DOURADO}">{na_margem} cêntimos</div>
        <div style="font-size:11.5px;color:#4a4a48">ficam na margem de quem vende</div>
      </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

        if cenario == "zero":
            st.markdown("""
            <div class="nota">
              <div class="tt">Precedente: o «cabaz zero» de 2023-24</div>
              Entre abril de 2023 e janeiro de 2024 vigorou em Portugal a isenção de IVA
              sobre uma lista taxativa de 46 bens alimentares essenciais (Lei n.º 17/2023,
              de 14 de abril). Duas lições ficam desse precedente. Primeira: a medição
              <strong>depende de quem mede</strong> — a ASAE apurou −10,14 % entre 18.04 e
              04.09.2023; a DECO, sobre os 41 produtos do seu cabaz abrangidos pela isenção,
              apurou −8,45 % ao fim de três meses. Listas, períodos e critérios de recolha
              diferentes dão resultados diferentes para a mesma medida. Segunda, e mais
              relevante: no balanço final do período (18.04.2023 a 04.01.2024) esse cabaz de
              41 produtos tinha <strong>subido 4,71 %</strong> (de 136,83 € para 143,28 €) —
              o efeito da isenção foi sendo erodido pela subida dos preços de base até ser
              superado. Uma descida de IVA desloca o nível de preços uma vez; não trava a
              tendência. É este tipo de leitura que o cursor de repercussão permite explorar.
            </div>
            """, unsafe_allow_html=True)

        _rho_lo, _rho_central, _rho_hi = repercussao_banda()
        _est_rho = estimativas_repercussao()

        with st.expander(
                f"📐 Porque é que este cursor parte de {numero(_rho_central * 100, 0)} % — "
                "a calibração, e o que ela corrigiu"):
            st.markdown(f"""
    Quando o Estado baixa o IVA, **não é garantido que o preço na loja desça na mesma medida**.
    Parte da descida pode ficar retida na margem de quem vende. A esse fenómeno chama-se
    *repercussão*, e é o parâmetro que decide se uma descida de IVA beneficia o consumidor ou o
    operador. **É o número que mais move o resultado desta ferramenta** — entre 0 % e 100 %, a
    poupança varia 250 %, mais do que todas as outras incertezas somadas.

    ##### Portugal já correu esta experiência

    A Lei n.º 17/2023, de 14 de abril, isentou de IVA 46 bens alimentares entre 18.04.2023 e
    04.01.2024 — a maioria com taxa anterior de 6 %. O **Banco de Portugal** avaliou a
    repercussão por quatro vias independentes. Não é um caso análogo noutro país e noutro setor:
    é **a medida idêntica, no mesmo país, no retalho alimentar**.

    ##### Como se extrai a repercussão dos números publicados

    O BdP publica a variação **observada** e a variação **mecânica** — a que haveria se a descida
    chegasse toda ao preço. A repercussão é o quociente das duas:
    """)
            st.latex(r"\rho = \frac{\text{variação observada}}{\text{variação mecânica}}"
                     r"\qquad\text{com}\qquad "
                     r"\text{mecânica} = \frac{1+t_1}{1+t_0}-1")
            st.markdown(
                "| Estimativa | Observado | Mecânico | **ρ implícito** |\n"
                "|---|---|---|---|\n"
                + "\n".join(
                    f"| {r['estimativa']} | −{numero(r['observado'], 1)} % | "
                    f"−{numero(r['mecanico'], 2)} % | **{numero(r['rho'] * 100, 1)} %** |"
                    for _, r in _est_rho.iterrows())
            )
            st.markdown(f"""
    **Nenhum destes ρ é citado — todos são calculados aqui**, a partir dos dois números que o BdP
    publica. A coluna é um cálculo desta aplicação sobre dados do Banco de Portugal.

    **Verificação de que a nossa aritmética coincide com a deles:** os óleos alimentares estavam a
    23 %, e o BdP publica um efeito mecânico de −18,7 %. A fórmula desta aplicação dá
    **{numero(efeito_mecanico_pct(23, 0), 2)} %**. Coincide, e está travado por teste — se não
    coincidisse, a derivação acima não valeria nada.

    **Porque é que a diluição não estraga o quociente:** as rubricas do IHPC incluem bens não
    abrangidos pela medida, o que atenua o observado *e* o mecânico. Como atenua os dois na mesma
    proporção, o quociente sobrevive. É por isso que esta derivação é legítima apesar da
    granularidade insuficiente que o próprio BdP assinala.

    ##### Porquê {numero(_rho_central * 100, 0)} % e não a média das quatro

    Toma-se a **mais conservadora das duas estimativas de diferença-nas-diferenças**, que são as
    únicas com contrafactual estatisticamente validado. As duas de preços online medem uma janela
    de duas semanas e dão acima de 100 %, o que reflete provavelmente concorrência e salivência
    política, não repercussão pura. A banda apresentada com os indicadores vai de
    **{numero(_rho_lo * 100, 1)} %** (área do euro) a **{numero(_rho_hi * 100, 0)} %** (integral).

    ##### Ressalvas — fazem parte da estimativa, não são rodapé

    1. O próprio BdP alerta para **desvios-padrão elevados** e recomenda cautela na interpretação.
    2. Foi uma medida **temporária, taxativa e muito mediática**, com pressões de custo a montante
       já em queda e acompanhamento público do setor. Uma alteração permanente e discreta pode
       repercutir-se menos.
    3. A janela avaliada vai até **agosto de 2023 — quatro meses**. Não há aqui evidência sobre
       erosão a prazo. Repercussão alta e efeito duradouro são coisas diferentes: no balanço de
       todo o período o cabaz da DECO tinha **subido 4,71 %**, com a inflação de base a superar a
       descida do imposto.
    4. A evidência robusta é sobre cortes **a partir de 6 %**. Para os 23 % há um único produto.
    5. Não se usa mais de 100 % por defeito, pela razão da ressalva 5 acima.

    ##### O que isto corrigiu

    Até 12.08.2026 este cursor partia de **40 %**, declarados como «parâmetro de trabalho, não
    estimativa», fundados em França 2009 (restauração) e na Suécia. Nenhuma dessas avaliações é
    sobre Portugal nem sobre alimentação em retalho. Os 40 % não eram uma hipótese conservadora —
    eram **contrariados pela única evidência portuguesa sobre a medida idêntica**, e faziam a
    aplicação subestimar a poupança por um fator de **2,4**.

    ##### E um ponto que a simulação torna visível

    **A repercussão decide sobretudo quem fica com o dinheiro** — o consumidor ou a margem — e só
    marginalmente quanto o Estado deixa de cobrar. Numa isenção total a receita cessante é
    independente da repercussão; numa redução parcial não é, porque uma repercussão menor mantém
    o preço final mais alto e, com ele, uma base tributável maior. No exemplo de 106 € com descida
    de 23 % para 6 %, a receita cessante vai de **−13,82 €** (repercussão 0 %) a **−14,65 €**
    (repercussão 100 %) — cerca de 6 % de amplitude.

    **Fonte:** {REPERCUSSAO_FONTE}.
            """)

        # ---- taxa atual de cada grupo: apurada, não predefinida ----
        # A taxa que cada grupo suporta **hoje** é um facto, não um parâmetro.
        # Até 11.08.2026 a simulação usava a taxa predefinida do grupo, o que
        # equivalia a assumir que toda a despesa do grupo a seguia — e isso
        # subestimava o IVA contido em 25 % a 36 % (auditoria, D2 reaberto).
        _comp_iva = composicao_iva(dados.get("pesos_subclasses") or {})
        _res_iva = resumo_composicao_iva(_comp_iva) if not _comp_iva.empty else {}
        _tem_apuramento = bool(_res_iva)

        if _tem_apuramento:
            _taxas_ef = taxas_efetivas(_comp_iva)
            _taxas_ef_min = taxas_efetivas(_comp_iva, indeterminado="reduzida")
            _taxas_ef_max = taxas_efetivas(_comp_iva, indeterminado="normal")
        else:
            # Sem os ponderadores por subclasse não há apuramento possível:
            # recorre-se à predefinição e diz-se que se recorreu.
            _taxas_ef = dict(zip(df_decomp["codigo"], df_decomp["iva_defeito"].astype(float)))
            _taxas_ef_min = _taxas_ef_max = _taxas_ef
            st.warning(
                "**Os ponderadores por subclasse não estão disponíveis nesta sessão.** A "
                "simulação recorre à taxa **predefinida** de cada grupo, o que subestima o IVA "
                "contido em cerca de 25 % a 36 % numa isenção total. Consulte o registo de "
                "ligações no separador Metodologia."
            )

        editor = pd.DataFrame({
            "Grupo": [f"{r.emoji} {r.classe}" for r in df_decomp.itertuples()],
            "Valor (€)": df_decomp["valor"].round(2),
            "Taxa média efetiva (%)": [
                round(float(_taxas_ef.get(c, d)), 1)
                for c, d in zip(df_decomp["codigo"], df_decomp["iva_defeito"])],
            "Taxa do cenário (%)": df_decomp["iva_defeito"].astype(float),
        })

        # O editor de taxas guarda estado por chave. Versões anteriores permitiam
        # valores fora da lista legal (era um campo numérico livre); se esse estado
        # sobreviver, o seletor rejeita-o. Limpa-se o que não seja válido.
        for _k in [k for k in list(st.session_state.keys()) if str(k).startswith("editor_iva_")]:
            try:
                _est = st.session_state[_k]
                _edicoes = (_est or {}).get("edited_rows", {}) if isinstance(_est, dict) else {}
                for _linha in list(_edicoes.values()):
                    for _col, _val in list(_linha.items()):
                        if "Taxa" in str(_col) and float(_val) not in (0.0, 6.0, 13.0, 23.0):
                            del st.session_state[_k]
                            raise StopIteration
            except StopIteration:
                continue
            except Exception:                                      # noqa: BLE001
                st.session_state.pop(_k, None)

        taxa_forcada = CENARIOS[cenario][1]
        if taxa_forcada is not None:
            editor["Taxa do cenário (%)"] = float(taxa_forcada)

        # Só as taxas que existem no Código do IVA (continente). Uma caixa de texto
        # livre permitiria valores impossíveis — 80 %, por exemplo — e produziria
        # resultados sem qualquer significado.
        TAXAS_LEGAIS = [0.0, 6.0, 13.0, 23.0]
        col_taxa = st.column_config.SelectboxColumn(
            options=TAXAS_LEGAIS, required=True,
            help="Taxas em vigor no continente: isenção, reduzida (6 %), intermédia (13 %), normal (23 %).",
        )

        # A chave do editor tem de variar com o cenário: caso contrário o Streamlit
        # mantém o estado do widget e as taxas do cenário nunca chegam à tabela.
        editado = st.data_editor(
            editor, width="stretch", hide_index=True,
            key=f"editor_iva_{cenario}",
            # A taxa atual **não é editável**: é apurada, não escolhida.
            disabled=["Grupo", "Valor (€)", "Taxa média efetiva (%)"],
            column_config={
                "Valor (€)": st.column_config.NumberColumn(format="%.2f"),
                "Taxa média efetiva (%)": st.column_config.NumberColumn(
                    format="%.1f %%",
                    help=("A taxa única que suporta o mesmo imposto que o conjunto dos "
                          "produtos do grupo. Não é uma taxa legal e ninguém a paga — é "
                          "apurada a partir da composição do grupo por subclasse.")),
                "Taxa do cenário (%)": col_taxa,
            },
        )

        st.caption(
            "**A coluna do meio é apurada, não escolhida** — por isso não é editável. Só a "
            "**taxa do cenário** é sua: é a alavanca de política. Só estão disponíveis as taxas "
            "que existem no Código do IVA — isenção, 6 %, 13 % e 23 %."
            + ("" if cenario == "manual" else
               " Escolha «Definir manualmente», acima, para as alterar grupo a grupo.")
        )

        # A taxa atual vem do apuramento e nunca do editor: mesmo que um estado
        # de sessão antigo traga a coluna antiga, é ignorada.
        taxas_atuais = {c: float(_taxas_ef.get(c, d))
                        for c, d in zip(df_decomp["codigo"], df_decomp["iva_defeito"])}
        taxas_cenario = dict(zip(df_decomp["codigo"], editado["Taxa do cenário (%)"]))

        sim = simular_iva(df_decomp, taxas_atuais, taxas_cenario, repercussao)
        res = resumo_iva(sim, despesa_mensal, vezes_ano, agregados)

        # Extrapolação nacional: parte do **agregado médio**, não da composição
        # escolhida na barra lateral. Multiplicar uma despesa ajustada a «2
        # adultos» pelos 4,1 milhões de agregados dava um total nacional que
        # mudava com quem estava a olhar para o ecrã — de −14 % a +92 % conforme
        # a composição (auditoria de 10.08.2026, A3).
        _sim_nac = simular_iva(decompor(media_agregado, dados["pesos"],
                                        dados["variacoes_classe"]),
                               taxas_atuais, taxas_cenario, repercussao)
        res_nac = resumo_iva(_sim_nac, media_agregado, vezes_ano, agregados)

        # Sensibilidade à parcela indeterminada: os dois extremos são a mesma
        # simulação com a parcela não repartível levada toda a 6 % e toda a 23 %.
        _res_band = None
        if _tem_apuramento and _res_iva["indeterminado_pct"] > 0.05:
            _band = []
            for _t in (_taxas_ef_min, _taxas_ef_max):
                _band.append(resumo_iva(
                    simular_iva(df_decomp, {c: float(_t.get(c, d)) for c, d
                                            in zip(df_decomp["codigo"], df_decomp["iva_defeito"])},
                                taxas_cenario, repercussao),
                    despesa_mensal, vezes_ano, agregados))
            _res_band = sorted(b["poupanca_mes"] for b in _band)

        # Sensibilidade à repercussão: os extremos da banda calibrada com a
        # avaliação do BdP ao «IVA zero» de 2023 (config, REPERCUSSAO_BANDA).
        # É a maior das incertezas do simulador, e por isso é a que aparece
        # primeiro — antes da parcela indeterminada, que move 3,4 vezes menos.
        _band_rho = sorted(
            (resumo_iva(simular_iva(df_decomp, taxas_atuais, taxas_cenario, _r),
                        despesa_mensal, vezes_ano, agregados)["poupanca_mes"],
             resumo_iva(simular_iva(decompor(media_agregado, dados["pesos"],
                                             dados["variacoes_classe"]),
                                    taxas_atuais, taxas_cenario, _r),
                        media_agregado, vezes_ano,
                        agregados)["poupanca_agregada_milhoes"])
            for _r in (_rho_lo, _rho_hi))

        c = st.columns(5)
        c[0].metric("Nova despesa mensal", euro(res["novo_valor"]),
                    euro(res["efetivo"]) if abs(res["efetivo"]) > 0.005 else None)
        c[1].metric("Poupança por mês", euro(res["poupanca_mes"]),
                    help=f"Efeito com repercussão integral: {euro(-res['mecanico'])}")
        c[2].metric("Poupança anual por agregado", euro(res["poupanca_ano"]))
        c[3].metric("Capturado na margem", euro(res["margem"]),
                    f"{(1 - repercussao) * 100:.0f} % do efeito")
        # O valor e a **variacao** da receita, nao o seu nivel. O rotulo dizia
        # «Receita de IVA por mês» e mostrava −22,24 €, o que sugeria uma receita
        # negativa. O cartão agregado, dois abaixo, já lhe chamava «Variação de
        # receita implícita» (auditoria de 12.08.2026, K9).
        c[4].metric("Variação da receita de IVA por mês", euro(res["receita_mes"]),
                    help=(f"Imposto contido na despesa deste agregado: "
                          f"{euro(res['iva_antes'])} → {euro(res['iva_depois'])}. "
                          "O valor apresentado é a diferença entre os dois."))

        if abs(_band_rho[1][0] - _band_rho[0][0]) > 0.005:
            st.caption(
                f"**Sensibilidade à repercussão — a maior incerteza desta ferramenta.** "
                f"O cursor parte de **{numero(_rho_central * 100, 0)} %**, calibrado com a "
                f"avaliação do Banco de Portugal ao «IVA zero» de 2023. Entre os extremos das "
                f"estimativas publicadas — {numero(_rho_lo * 100, 1)} % (contrafactual da área "
                f"do euro) e {numero(_rho_hi * 100, 0)} % (repercussão integral) — a poupança "
                f"mensal fica entre **{euro(_band_rho[0][0])}** e **{euro(_band_rho[1][0])}**, "
                f"e a agregada anual entre **{milhoes(_band_rho[0][1])}** e "
                f"**{milhoes(_band_rho[1][1])}**. Mova o cursor para ver qualquer outro valor."
            )

        # Sensibilidade às parcelas atribuídas **por predominância**. Até
        # 12.08.2026 a aplicação mostrava banda para a parcela indeterminada
        # (5,9 % do cabaz) e nenhuma para esta (20,1 %), que move o resultado
        # 3,4 vezes mais — mostrava a incerteza pequena e escondia a grande
        # (auditoria de 12.08.2026, F4).
        _res_band_pred = None
        if _tem_apuramento and _res_iva.get("por_predominancia_pct", 0) > 0.05:
            _bp = []
            for _p in ("reduzida", "normal"):
                _tp = taxas_efetivas(_comp_iva, predominancia=_p)
                _bp.append(resumo_iva(
                    simular_iva(df_decomp,
                                {c: float(_tp.get(c, d)) for c, d
                                 in zip(df_decomp["codigo"], df_decomp["iva_defeito"])},
                                taxas_cenario, repercussao),
                    despesa_mensal, vezes_ano, agregados))
            _res_band_pred = sorted(b["poupanca_mes"] for b in _bp)

        if _res_band_pred is not None and abs(_res_band_pred[1] - _res_band_pred[0]) > 0.005:
            st.caption(
                f"**Sensibilidade às atribuições por predominância — limite exterior.** "
                f"{percentagem(_res_iva['por_predominancia_pct'], sinal=False)} do cabaz está em subclasses cuja "
                "taxa foi atribuída por **juízo sobre a rubrica**, e não por leitura inequívoca "
                "das Listas — o **pão** a 6 %, onde a AT excluiu o pré-cozido congelado; o "
                "bacalhau seco a 6 %, onde o fumado fica a 23 %; os pré-preparados a 23 %. Se "
                "**todas** essas atribuições estivessem erradas ao mesmo tempo e no mesmo "
                f"sentido, a poupança mensal ficaria entre **{euro(_res_band_pred[0])}** e "
                f"**{euro(_res_band_pred[1])}**. É um **limite exterior, não um intervalo "
                "plausível**: ninguém sustenta que todo o pão vendido seja pré-cozido "
                "congelado. Serve para mostrar que esta parcela pesa mais do que a "
                "indeterminada, logo abaixo — e é por isso que passou a ter banda."
            )

        if _res_band is not None and abs(_res_band[1] - _res_band[0]) > 0.005:
            st.caption(
                f"**Sensibilidade à parcela indeterminada.** "
                f"{percentagem(_res_iva['indeterminado_pct'], sinal=False)} do cabaz está em subclasses que "
                "atravessam taxas em proporção não repartível. Levando essa parcela toda à taxa "
                f"reduzida ou toda à normal, a poupança mensal fica entre "
                f"**{euro(_res_band[0])}** e **{euro(_res_band[1])}**. Os valores acima usam, "
                "para essa parcela, a taxa predefinida do grupo **confinada ao intervalo em que "
                "a lei situa cada subclasse** — que nem sempre vai de 6 % a 23 %: os cereais de "
                "pequeno-almoço estão entre 13 % e 23 %, e nunca a 6 %."
            )

        if _res_iva:
            st.markdown("#### Quanto do cabaz segue cada taxa — apurado, não assumido")
            st.caption(
                "A simulação aplica **uma taxa por grupo**, que é o que a decomposição permite. "
                "Isso equivale a assumir que toda a despesa do grupo segue a taxa predefinida. "
                f"Os ponderadores por subclasse da COICOP 2018 (`prc_hicp_iw`, "
                f"{dados.get('ano_pesos_subclasses') or '—'}) permitem medir esse pressuposto pela "
                "primeira vez."
            )
            w1, w2, w3, w4 = st.columns(4)
            w1.metric("À taxa reduzida (6 %)", f"{percentagem(_res_iva['taxa_6_pct'], sinal=False)}",
                      help="Parcela do cabaz alimentar que está seguramente a 6 %.")
            w2.metric("À taxa intermédia (13 %)", f"{percentagem(_res_iva['taxa_13_pct'], sinal=False)}",
                      help="Os óleos vegetais que não são azeite (Lista II, 1.5.3).")
            w3.metric("À taxa normal (23 %)", f"{percentagem(_res_iva['taxa_23_pct'], sinal=False)}")
            w4.metric("Indeterminado", f"{percentagem(_res_iva['indeterminado_pct'], sinal=False)}",
                      help=("Subclasses que atravessam taxas em proporção não repartível — "
                            "marisco (moluscos a 6 %, crustáceos a 23 %), o mel dentro dos "
                            "doces, o sal dentro dos condimentos, os leites aromatizados "
                            "dentro das sobremesas lácteas. Cada uma entra com o intervalo "
                            "em que a lei a situa, e nem todas vão de 6 % a 23 %: os cereais "
                            "de pequeno-almoço estão entre 13 % e 23 %."))

            _iva_mod = _res_iva["iva_modelo_pct"] / 100 * media_agregado
            _sub_min = _res_iva["iva_apurado_min_pct"] / _res_iva["iva_modelo_pct"] * 100 - 100
            _sub_max = _res_iva["iva_apurado_max_pct"] / _res_iva["iva_modelo_pct"] * 100 - 100
            st.success(f"""
    **Porque é que a taxa atual de cada grupo não é a taxa predefinida — e o que isso mudou.**

    Até 11.08.2026 a simulação aplicava a cada grupo a sua taxa **predefinida**: 6 % a sete grupos,
    23 % a dois. Isso equivalia a assumir que **{percentagem(_res_iva['assumido_6_pct'], sinal=False)}** do cabaz está
    à taxa reduzida. O apuramento por subclasse diz que são
    **{percentagem(_res_iva['apurado_6_min_pct'], sinal=False)} a {percentagem(_res_iva['apurado_6_max_pct'], sinal=False)}**.

    A diferença não era pequena nem tinha sinal único. Medida sobre o **IVA contido** na despesa
    alimentar do agregado médio, que é o que determina a poupança:

    | | IVA contido | Efeito no simulador |
    |---|---|---|
    | Taxa predefinida (o que se fazia) | {euro(_iva_mod)}/mês | — |
    | **Taxa média efetiva** (o que se faz agora) | **{euro(_res_iva['iva_apurado_min_pct'] / 100 * media_agregado)} a {euro(_res_iva['iva_apurado_max_pct'] / 100 * media_agregado)}/mês** | numa isenção total, **{numero(_sub_min, 0)} % a {numero(_sub_max, 0)} %** mais |

    A razão é que a predefinição creditava a **pastelaria**, a **charcutaria** e os **hortícolas
    transformados** com 6 % quando eles suportam 23 %. E o erro tinha o **sinal contrário** numa
    medida dirigida apenas ao que já está a 6 %, porque aí a descida era aplicada a grupos
    inteiros. Com a taxa efetiva, os dois cenários ficam certos sem que seja preciso saber
    de antemão qual deles se está a simular.
            """)
            with st.expander("🧮 Como se calcula a taxa média efetiva — e porque é que basta"):
                st.markdown("""
    **O que é.** A taxa média efetiva de um grupo é **a taxa única que suporta o mesmo imposto que
    o conjunto dos produtos desse grupo**. Não é uma taxa legal, e ninguém a paga: é uma medida
    da carga fiscal média do grupo, tal como ele é hoje consumido.

    **Como se obtém.** Primeiro apura-se a fração do preço que é imposto, ponderando as subclasses:
                """)
                st.latex(r"c = \frac{\sum_b w_b \cdot \dfrac{t_b}{1+t_b}}{\sum_b w_b}")
                st.markdown(
                    "onde *b* percorre as subclasses do grupo, *w* é o ponderador de cada uma e "
                    "*t* a sua taxa legal. Depois inverte-se para obter a taxa equivalente:")
                st.latex(r"t_{ef} = \frac{c}{1-c}")
                st.markdown(f"""
    **Exemplo com números — Cereais e derivados.** O grupo pesa
    {numero(float(_comp_iva.set_index('codigo').loc['CP0111', 'peso']), 2)} ‰, dos quais
    {numero(float(_comp_iva.set_index('codigo').loc['CP0111', 'taxa_6']), 2)} ‰ a 6 % (cereais,
    farinhas e **pão**) e
    {numero(float(_comp_iva.set_index('codigo').loc['CP0111', 'taxa_23']), 2)} ‰ a 23 %
    (**outros produtos de padaria** — bolos, bolachas, pastelaria). A carga média resultante é de
    **{numero(float(_taxas_ef['CP0111']), 1)} %**, e não os 6 % que a predefinição indicava.

    **E porque é que uma taxa média basta.** Podia parecer que era preciso simular escalão a
    escalão. Não é — e não por aproximação, mas por **identidade algébrica**. A base sem imposto de
    um grupo é a soma das bases dos seus escalões; se a taxa efetiva for definida como acima, a
    base que ela produz é exatamente essa soma. E como a taxa do cenário é uniforme dentro do
    grupo, tudo o que se calcula a seguir — efeito mecânico, repercussão, imposto contido no preço
    novo — depende apenas da base e da taxa do cenário.

    Os dois caminhos foram confrontados numericamente em quatro cenários, incluindo a isenção
    total e um cenário misto: **coincidem até à décima quarta casa decimal**, que é o limite da
    aritmética de vírgula flutuante. Está travado por teste automático.
                """)
                st.warning("""
    **O que continua a ser aproximação.** A taxa efetiva é exata *dado* o apuramento das
    subclasses — mas o apuramento tem uma parcela indeterminada, e uma parte foi atribuída por
    predominância. E os ponderadores são do IHPC, que inclui não residentes. A sensibilidade a
    isso está declarada por baixo dos indicadores, como intervalo.

    Continua também a valer, sem alteração, a advertência de que **isto não é uma estimativa de
    custo orçamental**: a despesa de referência não é a despesa alimentar total das famílias, e
    uma estimativa de receita cessante exige a base tributável real.
                """)

            _tab_iva = pd.DataFrame([{
                "Grupo": f"{r.emoji} {r.classe}",
                "Predefinida": f"{r.iva_defeito} %",
                "Na predefinida": r.na_taxa_predefinida_pct,
                "6 %": r.taxa_6_pct,
                "13 %": r.taxa_13_pct,
                "23 %": r.taxa_23_pct,
                "Indeterminado": r.indeterminado_pct,
            } for r in _comp_iva.itertuples()])
            st.dataframe(
                _tab_iva, width="stretch", hide_index=True,
                column_config={
                    c: st.column_config.NumberColumn(format="%.1f %%")
                    for c in ("Na predefinida", "6 %", "13 %", "23 %", "Indeterminado")
                })
            st.caption(
                "**«Na predefinida»** é a fração do grupo que segue efetivamente a taxa que o "
                "simulador lhe aplica — é a medida da qualidade da aproximação, grupo a grupo. "
                f"Vai de {percentagem(float(_comp_iva['na_taxa_predefinida_pct'].min()), sinal=False)} a "
                f"{percentagem(float(_comp_iva['na_taxa_predefinida_pct'].max()), sinal=False)}. "
                f"{percentagem(_res_iva['por_predominancia_pct'], sinal=False)} do cabaz foi atribuído por "
                "**predominância** e não com certeza — ver o detalhe por subclasse abaixo."
            )
            st.warning(
                "**Ponderadores do IHPC, que incluem a despesa de não residentes.** É a única "
                "fonte aberta que desce à subclasse — o IDF fica-se pelo quarto dígito. Serve "
                "para repartir *dentro* de cada grupo, que é o uso aqui, mas o nível de cada "
                "parcela herda essa limitação."
            )
            st.download_button(
                "⬇️ Descarregar composição por taxa (CSV)",
                csv_com_fonte(_comp_iva, "Composicao do cabaz alimentar por taxa de IVA", dados,
                              fonte=("Codigo do IVA, Listas I e II (leitura da UPE) + Eurostat, "
                                     "prc_hicp_iw (ponderadores por subclasse)"),
                              conjuntos=[eurostat.HICP_PONDERADORES],
                              extra=[("Ano dos ponderadores", dados.get("ano_pesos_subclasses") or "-"),
                                     ("AVISO", "A parcela indeterminada nao e arbitrada")]),
                file_name="composicao_iva_por_taxa.csv", mime="text/csv")

        with st.expander("⚖️ O que o Código do IVA diz sobre cada grupo — e o que fica de fora"):
            st.markdown(
                "O Código do IVA classifica **por produto**, nas Listas I (6 %) e II (13 %); a "
                "aplicação classifica **por grupo COICOP**, porque não existe despesa aberta ao "
                "nível do produto. Nenhum dos nove grupos é homogéneo: a taxa predefinida é a "
                "**predominante**, nunca a única. O quadro seguinte diz, para cada grupo, o que "
                "está na taxa reduzida e o que segue taxa diferente da predefinida."
            )
            for _cl in CLASSES:
                _mapa = IVA_MAPA.get(_cl["cod"])
                if not _mapa:
                    continue
                st.markdown(
                    f"**{_cl['emoji']} {_cl['nome']}** — predefinida a "
                    f"**{_cl['iva']} %**  \n"
                    f"<span style='font-size:11.5px;color:#6b7280'>COICOP 2018 "
                    f"01.1.{_cl['cod'][5]} · {_cl['oficial']}</span>",
                    unsafe_allow_html=True,
                )
                _linhas = []
                for _t, _txt in _mapa["taxas"]:
                    _marca = " ← predefinida" if _t == _cl["iva"] else ""
                    _linhas.append(f"- **{_t} %**{_marca} · {_txt}")
                if _mapa.get("nota"):
                    _linhas.append(f"- *{_mapa['nota']}*")
                st.markdown("\n".join(_linhas))
            st.caption(f"Fonte: {IVA_MAPA_FONTE}. Levantamento de 10.08.2026, "
                       "refeito a 11.08.2026 contra as classes da COICOP 2018.")

        if not _comp_iva.empty:
            with st.expander("🔍 O apuramento, subclasse a subclasse"):
                st.markdown(
                    "Cada linha é uma subclasse da COICOP 2018, com o ponderador que o Eurostat "
                    "lhe atribui e a verba do Código do IVA que a sustenta. **É aqui que se vê "
                    "de onde vêm os números do quadro acima** — e onde se vê o que não foi "
                    "possível determinar."
                )
                _pesos_sub = dados.get("pesos_subclasses") or {}

                def _peso_comp(spec):
                    if isinstance(spec, str):
                        return float(_pesos_sub.get(spec) or 0.0), spec
                    pai, filhos = spec
                    resto = float(_pesos_sub.get(pai) or 0.0) - sum(
                        float(_pesos_sub.get(f) or 0.0) for f in filhos)
                    return max(resto, 0.0), f"{pai} menos {', '.join(filhos)}"

                _marca = {"certa": "✅", "predominante": "≈", "mista": "❔"}
                _linhas_sub = []
                for _cl in CLASSES:
                    for _c in IVA_COMPONENTES.get(_cl["cod"], []):
                        _p, _cod = _peso_comp(_c["peso"])
                        _linhas_sub.append({
                            "Grupo": f"{_cl['emoji']} {_cl['nome']}",
                            "Subclasse": _cod,
                            "Ponderador (‰)": _p,
                            # Uma parcela indeterminada não fica sem taxa: fica
                            # com o **intervalo** em que a lei a situa. Há uma —
                            # os cereais de pequeno-almoço — cujo intervalo não
                            # inclui a taxa reduzida.
                            "Taxa": (f"{_c['taxa']} %" if _c["taxa"] is not None
                                     else "{} a {} %".format(*_c.get("entre", (6, 23)))),
                            "": _marca.get(_c["certeza"], ""),
                            "O que sustenta a atribuição": _c["desc"].replace("**", ""),
                        })
                st.dataframe(
                    pd.DataFrame(_linhas_sub), width="stretch", hide_index=True,
                    column_config={"Ponderador (‰)": st.column_config.NumberColumn(format="%.2f")})
                st.caption(
                    "✅ a subclasse cai inteira numa verba · ≈ é maioritariamente de uma taxa, "
                    "mas não só · ❔ atravessa taxas em proporção **não determinável**: a coluna "
                    "mostra o **intervalo em que a lei a situa**, e o peso vai para a parcela "
                    "indeterminada — não é arbitrado.  \n"
                    f"Fonte: {IVA_COMPONENTES_FONTE}."
                )
                st.success(
                    "**Este quadro foi confrontado com o texto legal a 12.08.2026.** Até essa "
                    "data tinha sido construído por leitura indireta das Listas. A verificação "
                    "verba a verba contra o texto consolidado corrigiu quatro atribuições — a "
                    "mais consequente foi a dos **cereais de pequeno-almoço**, cujo valor "
                    "central estava a 6 % quando a lei os situa entre **13 % e 23 %**: a Lista I "
                    "não tem verba alguma para eles e a Lista II (1.12) cobre apenas os «flocos "
                    "prensados simples de cereais e leguminosas sem adições de açúcar»."
                )
                with st.expander("⚖️ O que a Autoridade Tributária já decidiu — informações "
                                 "vinculativas"):
                    st.markdown(
                        "As informações vinculativas da AT (artigo 68.º do CPPT) são a via para "
                        "fechar as atribuições que aqui aparecem como **≈ predominante**: são "
                        "questões de leitura das Listas, não de estatística. Cada ficha decide "
                        "sobre produtos concretos, e o que decide vincula a Administração.\n"
                    )
                    for _f in AT_FICHAS:
                        st.markdown(
                            f"**Processo {_f['processo']}** — despacho de {_f['despacho']}, "
                            f"{_f['orgao']}. *{_f['assunto']}.*"
                        )
                        st.dataframe(
                            pd.DataFrame(
                                [{"Subclasse": _c, "O que a ficha decide": _t}
                                 for _c, _t in _f["decide"]]),
                            width="stretch", hide_index=True)
                    st.success(
                        "**O princípio que sustenta este quadro**, na formulação da ficha "
                        f"24929: «{PRINCIPIO_LISTA_TAXATIVA}»\n\n"
                        "É a justificação do método usado aqui — percorrer as Listas e atribuir "
                        "a taxa normal a tudo o que não esteja lá de forma inequívoca. E "
                        "explica por que os **preparados** caem quase sempre fora: «as "
                        "categorias 1.3 e 1.6 não incluem qualquer tipo de preparados; quando "
                        "assim é, por exemplo a verba 1.1 da Lista I, estes são especificamente "
                        "referidos»."
                    )
                    st.caption(
                        "**Uma tensão que se regista e não se resolve.** A ficha 28176 "
                        "caracteriza a verba 1.1.1 como abrangendo os cereais «em grão, ou em "
                        "flocos», o que sugeriria 6 % para os flocos simples. Mas a verba 1.12 "
                        "da Lista II é texto legal específico para «flocos prensados simples "
                        "de cereais e leguminosas sem adições de açúcar», a 13 %. Entende-se "
                        "que o texto específico prevalece, e que a caracterização da ficha é "
                        "contextual — a decisão que ela toma é sobre *preparados*, não sobre "
                        "flocos simples. É o único ponto do quadro onde outra leitura é "
                        "defensável, e por isso está escrito."
                    )
                    st.info(
                        "**Regra geral que explica muitas atribuições à taxa normal.** O artigo "
                        "18.º, n.º 4 do Código do IVA determina que, num produto composto, se as "
                        "mercadorias mantêm a sua individualidade se aplica **a taxa mais "
                        "elevada** de entre as que lhes caberiam; se a perdem, a que "
                        "corresponder ao produto resultante. É por isso que tantos «preparados» "
                        "acabam a 23 % mesmo contendo ingredientes que, isolados, estariam a 6 %."
                    )
                st.info("""
    **O que a COICOP 2018 permitiu e a anterior não permitia.** Três cortes novos resolvem as
    maiores ambiguidades: **Pão** (`CP011131`) separado de **Outros produtos de padaria**
    (`CP011139`), o que reparte a maior classe do cabaz; **Azeite** (`CP011513`) separado dos
    restantes óleos vegetais, o que isola exatamente a verba da Lista II; e **carne seca ou
    fumada** separada da carne fresca. Na nomenclatura anterior estes produtos partilhavam
    subclasse, e a repartição era impossível — foi por isso que o levantamento de 10.08.2026
    concluiu, com razão à data, que as parcelas não eram quantificáveis.
                """)

        # --- sensibilidade à base de cálculo ---
        _despesa_outra = despesa_do_agregado(
            float(outra_ancora["valor"]), dim_efetiva, adultos, criancas, escala_chave)
        _decomp_outra = decompor(_despesa_outra, dados["pesos"], dados["variacoes_classe"])
        _sim_outra = simular_iva(_decomp_outra, taxas_atuais, taxas_cenario, repercussao)
        _res_outra = resumo_iva(_sim_outra, _despesa_outra, vezes_ano, agregados)
        # O agregado nacional da outra âncora segue a mesma regra do da âncora
        # ativa: parte do agregado médio, não da composição escolhida.
        _media_outra = float(outra_ancora["valor"])
        _res_outra_nac = resumo_iva(
            simular_iva(decompor(_media_outra, dados["pesos"], dados["variacoes_classe"]),
                        taxas_atuais, taxas_cenario, repercussao),
            _media_outra, vezes_ano, agregados)
        st.caption(
            f"**Sensibilidade à base de cálculo.** Estes valores usam a base "
            f"**{base_ancora['nome']}**. Com **{outra_ancora['nome']}**, a poupança mensal seria "
            f"{euro(_res_outra['poupanca_mes'])} em vez de {euro(res['poupanca_mes'])}, "
            f"e a poupança agregada anual {milhoes(_res_outra_nac['poupanca_agregada_milhoes'])} "
            f"em vez de {milhoes(res_nac['poupanca_agregada_milhoes'])}. "
            "Todos os resultados do simulador escalam proporcionalmente com a âncora — "
            "a repartição entre consumidor e margem não depende dela."
        )

        fig_rep = grafico_reparticao(sim)
        if fig_rep is not None:
            st.markdown("#### Como se reparte o benefício")
            st.plotly_chart(fig_rep, width="stretch")
        else:
            st.info("Defina um cenário diferente das taxas atuais para ver a repartição.")

        st.markdown("#### Ordens de grandeza a nível agregado")
        st.caption(
            f"Extrapolação para **{numero(agregados)}"
            + f"** agregados — o total mais recente ({dados.get('agregados_ano') or '—'}), "
            + "porque o que se extrapola é o efeito de uma medida sobre o país de hoje. "
            + "É por isso um número diferente do denominador da âncora das Contas Nacionais, "
            + "que tem de ser o do ano da despesa. "
            + f"Parte do **agregado médio** ({euro(media_agregado)}/mês), não da composição "
            + "escolhida na barra lateral: multiplicar uma despesa já ajustada a uma composição "
            + "específica pelo total nacional contaria o país inteiro como se fosse todo "
            + "composto dessa maneira. **Estes dois valores não mudam com a composição** — "
            + "só com a âncora e com o cenário de taxas."
        )
        if base_chave == "contas":
            # Cada passo está justificado — B2 para o denominador, A3 para o
            # multiplicador — mas o produto não é nenhum dos dois anos. Tem de
            # estar escrito ao lado do número (auditoria de 11.08.2026, E15).
            st.caption(
                f"⚠️ **O que este número é, exatamente.** Na base Contas Nacionais ele combina "
                f"três momentos: o **consumo real de {base_ancora['ano_base']}**, a **preços de "
                f"{_mes_txt}**, sobre a **população de agregados de "
                f"{dados.get('agregados_ano') or '—'}**. Cada passo está justificado — o "
                "denominador da âncora tem de ser contemporâneo da despesa, e o que se extrapola "
                "é o efeito de uma medida sobre o país de hoje —, mas o produto **não é uma "
                "medição de nenhum ano**. Leia-o como ordem de grandeza, não como estimativa."
            )
        g1, g2 = st.columns(2)
        g1.metric("Poupança agregada anual",
                  milhoes(res_nac["poupanca_agregada_milhoes"]))
        g2.metric("Variação de receita implícita",
                  milhoes(res_nac["receita_agregada_milhoes"]))

        # A ressalva antiga dizia «não é custo orçamental» sem dizer porquê nem
        # quanto. Confrontar as duas bases dá a ordem de grandeza do desvio e
        # mostra que não são uma melhor e outra pior: são bases de perguntas
        # diferentes (auditoria de 12.08.2026, F5).
        #
        # Os quatro números deste bloco estavam **inscritos à mão** — 15 400 M€,
        # 28 188 M€, 33 038 M€ e «1,8 a 2,1 vezes» —, dois deles ao lado de
        # números calculados em direto, e o valor das Contas Nacionais estava
        # escrito ao lado do sítio de onde podia vir. Deixavam de bater certo no
        # dia em que o Eurostat publicasse outro ano (auditoria, K8; é a terceira
        # ocorrência do padrão do C2 e do E9).
        _base_sim_milhoes = agregados * media_agregado * 12 / 1e6
        _cn_milhoes = dados.get("despesa_milhoes")
        _cn_ano = dados.get("despesa_ano") or "—"
        if _cn_milhoes and _base_sim_milhoes > 0:
            _racio_bases = _cn_milhoes / _base_sim_milhoes
            _frase_bases = (
                f"O consumo das famílias em produtos alimentares nas Contas Nacionais "
                f"(<code>{eurostat.CONTAS_NACIONAIS}</code>, CP011) foi de "
                f"<strong>{milhoes(_cn_milhoes, 0)} em {_cn_ano}</strong> — "
                f"<strong>{numero(_racio_bases, 1)} vezes mais</strong>."
            )
        else:
            _frase_bases = (
                "A despesa alimentar das Contas Nacionais não está disponível nesta "
                "sessão, pelo que a comparação entre as duas bases não é apresentada."
            )
        st.markdown(f"""
        <div class="nota perigo">
          <div class="tt">Isto não é uma estimativa de custo orçamental — e a diferença é grande</div>
          Esta ferramenta mede o <strong>impacto nas famílias</strong>, e mede-o na base
          própria dessa pergunta: a despesa das famílias residentes, apurada por inquérito.
          O <strong>custo orçamental</strong> é outra pergunta, e pede outra base — o IVA é
          cobrado sobre transações reais, que são o que as Contas Nacionais medem.
          <br><br>
          <strong>As duas bases não estão perto uma da outra.</strong> A base deste
          simulador — {numero(agregados)} agregados × {euro(media_agregado)}/mês — dá
          <strong>{milhoes(_base_sim_milhoes, 0)}/ano</strong> de despesa alimentar.
          {_frase_bases} Parte da diferença é conhecida (os
          inquéritos subdeclaram a despesa alimentar), parte não está explicada, e o
          conceito das Contas Nacionais é o <strong>interno</strong> — despesa no
          território, não residentes incluídos, verificado a 12.08.2026.
          <strong>Enquanto isso não estiver resolvido, não se troca a base</strong>
          — mas ninguém deve ler os valores acima como uma verba de Orçamento.
          <br><br>
          E mesmo com a base certa faltaria o resto: o cabaz alimentar doméstico
          <strong>não inclui restauração, cantinas nem instituições</strong>, não há resposta
          comportamental, e os agregados não são homogéneos.
        </div>
        """, unsafe_allow_html=True)

        # ------------------------------------------------------------------
        # Quem recebe o quê. O simulador diz **quanto**; esta secção diz **a
        # quem** — e as duas leituras apontam em sentidos opostos, ambas
        # verdadeiras. Sem isto, a ferramenta responde a metade da pergunta que
        # uma decisão de política exige (auditoria de 12.08.2026, F3).
        # ------------------------------------------------------------------
        st.markdown("#### Quem recebe o quê — a distribuição, medida em 2023")
        st.caption(
            "O simulador diz **quanto** vale a medida. Não diz **a quem** chega, e para uma "
            "decisão de política é a segunda pergunta que decide. O Banco de Portugal mediu as "
            "duas coisas no «IVA zero» de 2023, e elas apontam em sentidos opostos — sem que "
            "nenhuma esteja errada."
        )

        _q1, _q2 = st.columns(2)
        with _q1:
            st.markdown("**Alívio na inflação: maior nos mais pobres**")
            st.caption(
                "Taxa de variação em cadeia em maio de 2023, em pontos percentuais. A "
                "alimentação pesa mais no cabaz de quem tem menos rendimento, por isso a mesma "
                "descida de preços vale-lhe mais."
            )
            _inf = pd.DataFrame(
                IVA_ZERO_INFLACAO_QUINTIL,
                columns=["Quintil", "Bens alimentares afetados", "Bens alimentares", "IPC total"])
            st.dataframe(_inf, width="stretch", hide_index=True)

        with _q2:
            st.markdown("**Afetação do dinheiro público: maior nos mais ricos**")
            st.caption(
                "Fração do custo orçamental de cada medida de 2023 que chega ao quintil mais "
                "pobre e ao mais rico. Quem gasta mais em valor absoluto recebe mais de uma "
                "redução proporcional do imposto."
            )
            _afet = pd.DataFrame(IVA_ZERO_AFETACAO_ORCAMENTAL,
                                 columns=["Medida", "pobres", "ricos"])
            _fig_af = go.Figure()
            _fig_af.add_trace(go.Bar(
                y=_afet["Medida"], x=_afet["pobres"], name="Para os 20 % mais pobres",
                orientation="h", marker_color=VERDE,
                hovertemplate="%{y}<br>20 % mais pobres: %{x} %<extra></extra>"))
            _fig_af.add_trace(go.Bar(
                y=_afet["Medida"], x=_afet["ricos"], name="Para os 20 % mais ricos",
                orientation="h", marker_color=DOURADO,
                hovertemplate="%{y}<br>20 % mais ricos: %{x} %<extra></extra>"))
            _fig_af.update_layout(
                barmode="group", height=260, margin=dict(t=30, b=30, l=10, r=10),
                legend=dict(orientation="h", y=1.2, x=0),
                xaxis_title="% do custo orçamental da medida", plot_bgcolor="#fff")
            _fig_af.update_xaxes(gridcolor="#eef1f4")
            st.plotly_chart(_fig_af, width="stretch")

        _iva_pobres, _iva_ricos = next(
            (p, r) for m, p, r in IVA_ZERO_AFETACAO_ORCAMENTAL if m == "Redução do IVA")
        st.markdown(f"""
        <div class="nota perigo">
          <div class="tt">As duas leituras são verdadeiras ao mesmo tempo</div>
          A redução do IVA <strong>alivia</strong> proporcionalmente mais os agregados de menor
          rendimento — −4,4 pp no Q1 contra −3,7 pp no Q5 — porque a alimentação pesa mais no
          seu cabaz. E ao mesmo tempo <strong>entrega</strong> mais dinheiro aos de maior
          rendimento: {_iva_ricos} % do custo orçamental vai para os 20 % mais ricos e
          {_iva_pobres} % para os 20 % mais pobres. O Banco de Portugal é explícito quanto à
          consequência: as famílias do quintil mais elevado «recebem mais 20 % de recursos
          públicos do que as do quintil de menores rendimentos, <strong>não contribuindo para
          uma política focada nos agregados vulneráveis</strong>».
          <br><br>
          Das quatro medidas de 2023 avaliadas, a redução do IVA é a <strong>menos
          focalizada</strong>: o apoio a famílias vulneráveis dirigiu 71 % do seu custo ao
          quintil mais pobre, contra {_iva_pobres} % desta. Isto não diz que a medida é má —
          diz que <strong>o instrumento é largo</strong>, e que comparar só o custo total entre
          medidas ignora metade da questão.
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"**Fonte:** {IVA_ZERO_QUINTIS_FONTE}.")

        with st.expander("Ver detalhe da simulação"):
            det = sim[["classe", "valor", "taxa_atual", "taxa_cenario",
                       "base", "mecanico", "efetivo", "margem", "novo_valor"]].copy()
            det.columns = ["Classe", "Valor (€)", "Taxa média efetiva (%)", "Taxa cenário (%)",
                           "Base sem IVA (€)", "Efeito mecânico (€)",
                           "Efeito efetivo (€)", "Margem (€)", "Novo valor (€)"]
            st.dataframe(det.round(2), width="stretch", hide_index=True)
            st.download_button(
                "⬇️ Descarregar simulação (CSV com fonte)",
                csv_com_fonte(det.round(2), "Simulacao de alteracao do IVA", dados,
                              # Despesa oficial, mas taxas e repercussao sao do
                              # utilizador: o cabecalho tem de o dizer.
                              fonte=("Eurostat (despesa e precos) + parametros do utilizador "
                                     "(taxas de IVA e repercussao) - NAO e uma fonte oficial "
                                     "no seu conjunto"),
                              extra=[("Cenario", CENARIOS[cenario][0]),
                                     ("Repercussao assumida", f"{repercussao*100:.0f}%"),
                                     ("Composicao do agregado", composicao),
                                     ("Taxa de partida",
                                      "taxa media efetiva apurada por subclasse (COICOP 2018)"
                                      if _tem_apuramento else
                                      "taxa predefinida do grupo - apuramento indisponivel"),
                                     ("AVISO", "A taxa do cenario e a repercussao sao parametros do utilizador, nao dados oficiais")]),
                f"despesa_alimentar_simulacao_iva_{date.today()}.csv", "text/csv",
            )

    # ==========================================================================
    # ABA 4 — Comparação UE-27
    # ==========================================================================
with aba4:
    with painel("Comparação UE-27"):
        vista = st.radio(
            "O que quer ver",
            ["💶 Quão caros são os alimentos",
             "🧾 Que fatia do orçamento consomem",
             "📈 A que ritmo estão a subir"],
            horizontal=True, label_visibility="collapsed",
        )
        ver_precos = vista.startswith("💶")
        ver_esforco = vista.startswith("🧾")

        st.info(
            "**São três perguntas diferentes.** «Quão caros são» compara o *nível* dos preços entre "
            "países. «Que fatia do orçamento consomem» mede o *esforço* das famílias — quanto do que "
            "gastam vai para comida. «A que ritmo sobem» compara a *inflação*. Um país pode ter "
            "preços baixos e ainda assim um esforço alimentar elevado, se os rendimentos forem "
            "baixos — e é esse cruzamento que interessa à política."
        )

        pli = dados.get("pli")

        # ==================== VISTA: NÍVEL DE PREÇOS ====================
        if ver_precos:
            if pli is None or pli.empty:
                st.warning(
                    "O índice de nível de preços não está disponível nesta sessão. "
                    "Consulte o registo de ligações no separador Metodologia. "
                    "Use entretanto a vista «A que ritmo estão a subir»."
                )
            else:
                # A categoria efetivamente obtida determina o rótulo: a reserva
                # inclui bebidas não alcoólicas e não pode ser apresentada como
                # se fosse só alimentação (auditoria, B3).
                pli_cat_usada = dados.get("pli_cat")
                pli_rotulo = eurostat.PPP_CATEGORIAS_ALIMENTOS.get(
                    pli_cat_usada, "Alimentação")
                pli_e_reserva = pli_cat_usada != eurostat.PPP_CATEGORIA_PREFERIDA

                ano_pli = pli["time"].max()
                pli_ult = pli[pli["time"] == ano_pli].copy()
                pli_ult["pais"] = pli_ult["geo"].map(PAISES)
                pli_ult = pli_ult.dropna(subset=["pais"]).sort_values("valor")

                pt_pli = pli_ult.loc[pli_ult["geo"] == "PT", "valor"]
                if not pt_pli.empty:
                    v = float(pt_pli.iloc[0])
                    posicao = "mais caros" if v > 100 else "mais baratos"
                    d1, d2, d3 = st.columns(3)
                    # Uma casa decimal: a grandeza comunicada é a distância à
                    # média europeia, e arredondar 1,4 para 1 perdia quase um
                    # terço dela (auditoria de 11.08.2026, E12).
                    d1.metric(f"Portugal em {ano_pli}", numero(v, 1),
                              help="Índice: média da UE-27 = 100")
                    d2.metric("Face à média da UE-27",
                              f"{numero(abs(v - 100), 1)} % {posicao}")
                    posto = int((pli_ult["geo"] != "EU27_2020").cumsum()[
                        pli_ult["geo"] == "PT"].iloc[0])
                    total = int((pli_ult["geo"] != "EU27_2020").sum())
                    d3.metric("Posição", f"{posto}.º de {total}",
                              help="Do mais barato para o mais caro, entre os países selecionados")

                figp = go.Figure(go.Bar(
                    y=pli_ult["pais"], x=pli_ult["valor"], orientation="h",
                    marker_color=[VERDE if g == "PT" else (AZUL if g == "EU27_2020" else "#b7c2ce")
                                  for g in pli_ult["geo"]],
                    text=[numero(x, 1) for x in pli_ult["valor"]],
                    textposition="outside",
                    hovertemplate="%{y}: %{x:.0f} (UE-27 = 100)<extra></extra>",
                ))
                figp.add_vline(x=100, line_width=2, line_dash="dash", line_color="#64748b",
                               annotation_text="média UE-27", annotation_position="top")
                figp.update_layout(height=max(320, 34 * len(pli_ult)),
                                   margin=dict(t=42, b=40, l=10, r=70),
                                   xaxis_title=(f"Nível de preços — {pli_rotulo.lower()} "
                                                "(média UE-27 = 100)"),
                                   plot_bgcolor="#fff", showlegend=False)
                figp.update_xaxes(gridcolor="#eef1f4")
                st.plotly_chart(figp, width="stretch")
                st.caption(
                    "Barras à direita da linha: alimentos mais caros do que a média europeia. "
                    "À esquerda: mais baratos. Portugal a verde. Fonte: programa de Paridades de "
                    f"Poder de Compra Eurostat-OCDE (`prc_ppp_ind_1`, categoria "
                    f"`{pli_cat_usada}` — {pli_rotulo}). Publicação **anual** — indicador de "
                    "nível, não de conjuntura."
                )
                if pli_e_reserva:
                    st.warning(
                        f"A categoria de referência (`{eurostat.PPP_CATEGORIA_PREFERIDA}`, "
                        "só alimentação) não respondeu nesta sessão. Estes valores usam a "
                        f"categoria de reserva `{pli_cat_usada}`, que **inclui bebidas não "
                        "alcoólicas** — águas, sumos, cafés e chás. O nível é próximo, mas o "
                        "âmbito não é o mesmo."
                    )

        # ==================== VISTA: ESFORÇO (COEFICIENTE DE ENGEL) ====================
        elif ver_esforco:
            engel = dados.get("engel") or {}
            if not engel:
                st.warning(
                    "**O indicador de esforço não está disponível nesta sessão.**\n\n"
                    "O cálculo precisa de dois valores das Contas Nacionais — a despesa "
                    "alimentar e o consumo total das famílias. O separador **Metodologia**, "
                    "no bloco «Registo das ligações desta sessão», mostra qual dos dois "
                    "falhou e porquê."
                )
            else:
                _eng_ue = intervalo_engel((dados.get("engel") or {}).get("PT"))
                st.markdown(f"""
    **O coeficiente de Engel.** É a fração do consumo total das famílias que vai para alimentação.
    Chama-se assim por **Ernst Engel**, o estatístico que em 1857 formulou a regularidade que ainda
    hoje se verifica: *quanto menor o rendimento, maior a fatia do orçamento gasta em comida*.

    É um dos indicadores mais antigos e mais robustos de bem-estar económico — e comparável entre
    países sem conversão cambial, por ser um rácio.

    **Porque é que esta página mostra um valor e o separador «Despesa e composição» mostra um
    intervalo.** O coeficiente pode medir-se em duas bases, e elas não coincidem:
    **{percentagem(_eng_ue['idf'], sinal=False)}** no IDF 2022/2023 do INE,
    **{percentagem(_eng_ue['contas'], sinal=False) if _eng_ue['contas'] is not None else '—'}** nas Contas Nacionais
    de {_eng_ue['ano_contas'] or '—'}. As Contas Nacionais registam, por agregado, mais despesa
    alimentar do que o inquérito — e o coeficiente diverge porque **o numerador diverge mais do
    que o denominador**. É a mesma divergência entre bases que leva a aplicação a apresentar a
    despesa mensal como intervalo, e não como ponto.

    Aqui usam-se **as Contas Nacionais**, e só elas, porque são a única base construída da mesma
    maneira em todos os países da UE — o IDF não tem equivalente europeu com esta desagregação. O
    nível é discutível; a **comparação entre países** é o que este quadro serve, e essa é válida
    porque todos os países entram pela mesma via.
                """)
                st.warning("""
    **Atenção: este número não tem salários no denominador.**

    O coeficiente de Engel é **despesa sobre despesa** — não despesa sobre rendimento:

    | | Numerador | Denominador |
    |---|---|---|
    | **Coeficiente de Engel** (aqui) | O que as famílias gastam em **comida** | O que as famílias gastam em **tudo** |
    | **Esforço alimentar** (separador «Despesa e composição») | O que o agregado gasta em **comida** | O que o agregado **recebe** |

    Por isso os dois números são diferentes e não se substituem. Este mede **como se reparte o
    orçamento de consumo**; o seguinte mede **quanto do rendimento é absorvido pela comida**.

    E também por isso **este indicador não responde à composição do agregado** que escolheu na
    barra lateral: é um rácio macroeconómico nacional — a despesa alimentar de *todas* as famílias
    sobre o consumo total de *todas* elas. Não existe versão «por agregado» nas Contas Nacionais.
                """)

                linhas_e = []
                for geo, d in engel.items():
                    if geo not in PAISES:
                        continue
                    linhas_e.append({"geo": geo, "pais": PAISES[geo],
                                     "quota": d["quota"], "ano": d["ano"]})
                df_e = pd.DataFrame(linhas_e).sort_values("quota")

                pt_e = engel.get("PT")
                ue_e = engel.get("EU27_2020")
                if pt_e:
                    e1, e2, e3 = st.columns(3)
                    e1.metric(f"Portugal ({pt_e['ano']}) — do que gastam",
                              f"{pt_e['quota']:.1f} %".replace(".", ","),
                              help=("De cada 100 € que as famílias portuguesas gastam em tudo "
                                    "— casa, transportes, saúde, lazer —, esta fração vai para "
                                    "alimentação. Não envolve salários nem rendimentos."))
                    if ue_e:
                        dif = pt_e["quota"] - ue_e["quota"]
                        e2.metric("Face à média da UE-27", pontos(dif, casas=1))
                    posto = int((df_e["geo"] != "EU27_2020").cumsum()[
                        df_e["geo"] == "PT"].iloc[0])
                    total_p = int((df_e["geo"] != "EU27_2020").sum())
                    e3.metric("Posição", f"{posto}.º de {total_p}",
                              help="Do menor esforço para o maior")

                figE = go.Figure(go.Bar(
                    y=df_e["pais"], x=df_e["quota"], orientation="h",
                    marker_color=[VERDE if g == "PT" else (AZUL if g == "EU27_2020" else "#b7c2ce")
                                  for g in df_e["geo"]],
                    text=[f"{v:.1f} %".replace(".", ",") for v in df_e["quota"]],
                    textposition="outside",
                    hovertemplate="%{y}: %{x:.1f} % do consumo<extra></extra>"))
                if ue_e:
                    figE.add_vline(x=ue_e["quota"], line_width=2, line_dash="dash",
                                   line_color="#64748b", annotation_text="média UE-27",
                                   annotation_position="top")
                figE.update_layout(height=max(320, 34 * len(df_e)),
                                   margin=dict(t=42, b=40, l=10, r=80),
                                   xaxis_title="Fatia do consumo das famílias gasta em alimentação (%)",
                                   plot_bgcolor="#fff", showlegend=False)
                figE.update_xaxes(gridcolor="#eef1f4")
                st.plotly_chart(figE, width="stretch")
                st.caption(
                    "Barras mais longas significam **maior esforço alimentar**: mais do orçamento "
                    "familiar absorvido por comida, menos disponível para tudo o resto. "
                    f"Fonte: Contas Nacionais (`{eurostat.CONTAS_NACIONAIS}`, COICOP 2018), "
                    f"rácio `CP011`/`{eurostat.TOTAL_CONSUMO}` — os códigos efetivamente "
                    "pedidos. Publicação anual."
                )

                with st.expander("Descarregar dados do esforço"):
                    tab_e = df_e[["pais", "quota", "ano"]].copy()
                    tab_e.columns = ["País", "Fatia do consumo em alimentação (%)", "Ano"]
                    tab_e["Fatia do consumo em alimentação (%)"] = \
                        tab_e["Fatia do consumo em alimentação (%)"].round(1)
                    st.dataframe(tab_e.sort_values("Fatia do consumo em alimentação (%)",
                                                   ascending=False),
                                 width="stretch", hide_index=True)
                    st.download_button(
                        "⬇️ CSV com fonte",
                        csv_com_fonte(tab_e, "Coeficiente de Engel - esforco alimentar", dados,
                                      fonte="Eurostat, Contas Nacionais (COICOP 2018)",
                                      conjuntos=[eurostat.CONTAS_NACIONAIS],
                                      extra=[("Indicador", "Despesa alimentar / consumo total das familias"),
                                             ("Conjunto",
                                              f"{eurostat.CONTAS_NACIONAIS}, "
                                              f"CP011 / {eurostat.TOTAL_CONSUMO}")]),
                        f"despesa_alimentar_engel_{date.today()}.csv", "text/csv")

        # ==================== VISTA: INFLAÇÃO ====================
        else:
            cpais, cgrupo = st.columns([3, 2])
            with cpais:
                escolhidos = st.multiselect(
                    "Países", options=list(PAISES.keys()),
                    default=[p for p in PAISES_POR_DEFEITO if p in PAISES],
                    format_func=lambda g: PAISES[g],
                )
            with cgrupo:
                opcoes_grupo = [COICOP_ALIMENTAR] + CODIGOS
                rotulos = {COICOP_ALIMENTAR: "🍽️ Todos os alimentos"}
                rotulos.update({c["cod"]: f"{c['emoji']} {c['nome']}" for c in CLASSES})
                grupo_sel = st.selectbox(
                    "Grupo de produto", options=opcoes_grupo,
                    format_func=lambda g: rotulos[g],
                    help="Compare a inflação de um tipo de produto específico entre países.",
                )

            bench_todos = dados["bench_todos"]
            bench, _ts = {}, {}
            for _, lb in bench_todos[bench_todos["coicop"] == grupo_sel].iterrows():
                bench.setdefault(lb["geo"], {})[lb["time"]] = lb["valor"]
                _ts[lb["time"]] = 1
            tempos_b = sorted(_ts)

            if grupo_sel != COICOP_ALIMENTAR:
                st.caption(
                    f"A comparar **{rotulos[grupo_sel].split(' ', 1)[1]}**. Grupos individuais são "
                    "bastante mais voláteis do que o agregado alimentar — a fruta e os legumes, em "
                    "particular, sofrem efeitos sazonais e climáticos fortes."
                )

            if not escolhidos or not tempos_b:
                st.info("Selecione pelo menos um país.")
            else:
                fig = go.Figure()
                paleta = [VERDE, AZUL, DOURADO, VERMELHO, "#7a5ea8", "#c2681a",
                          "#0f8f9c", "#4a7c3f", "#8f4a6b", "#5a6b8f", "#a0568f", "#2980b9"]
                for i, geo in enumerate(escolhidos):
                    if geo not in bench:
                        continue
                    fig.add_trace(go.Scatter(
                        x=[mes_pt(t) for t in tempos_b],
                        y=[bench[geo].get(t) for t in tempos_b],
                        name=PAISES[geo],
                        line=dict(color=paleta[i % len(paleta)],
                                  width=3.2 if geo == "PT" else 1.9,
                                  dash="dot" if geo == "EU27_2020" else "solid"),
                        hovertemplate="%{x}<br>%{y:.1f} %<extra>" + PAISES[geo] + "</extra>",
                    ))
                fig.update_layout(height=400, margin=dict(t=20, b=40, l=10, r=10),
                                  yaxis_title="Variação homóloga (%)",
                                  legend=dict(orientation="h", y=1.12, x=0),
                                  hovermode="x unified", plot_bgcolor="#fff")
                fig.update_xaxes(showgrid=False)
                fig.update_yaxes(gridcolor="#eef1f4", zerolinecolor="#cbd5e1")
                st.plotly_chart(fig, width="stretch")

                ultimo = tempos_b[-1]
                # Colunas explícitas: sem observações, `pd.DataFrame([])` não
                # tem a coluna `geo` e o `.map` seguinte levantava KeyError —
                # um erro técnico onde devia estar uma explicação
                # (auditoria de 11.08.2026, E13).
                ranking = pd.DataFrame(
                    [{"geo": g, "valor": v[ultimo]}
                     for g, v in bench.items() if v.get(ultimo) is not None],
                    columns=["geo", "valor"])
                ranking["pais"] = ranking["geo"].map(PAISES)
                ranking = ranking.dropna(subset=["pais"])
                ue = ranking.loc[ranking["geo"] == "EU27_2020", "valor"]
                valor_ue = float(ue.iloc[0]) if not ue.empty else None

                if ranking.empty:
                    st.info(
                        f"Nenhum dos países selecionados tem observação em "
                        f"**{mes_pt(ultimo)}**, o mês mais recente da série. O gráfico "
                        "acima mostra o histórico disponível; a comparação de posições "
                        "precisa de um mês comum."
                    )

                st.markdown(f"#### Posição em {mes_pt(ultimo)}")
                ordenado = ranking.sort_values("valor", ascending=True)
                cores, etiquetas = [], []
                for geo, valor in zip(ordenado["geo"], ordenado["valor"]):
                    gap = (valor - valor_ue) if valor_ue is not None else None
                    if geo == "PT":
                        cores.append(VERDE)
                    elif geo == "EU27_2020":
                        cores.append(AZUL)
                    elif gap is not None and gap > 0:
                        cores.append("#e08b84")
                    else:
                        cores.append("#8fb3d0")
                    if gap is None or geo == "EU27_2020":
                        etiquetas.append(percentagem(valor, sinal=False))
                    else:
                        # Antes: `.replace(".", ",")` sobre a frase inteira, que
                        # convertia também o «p.p.» em «p,p,» (auditoria, C5).
                        etiquetas.append(f"{percentagem(valor, sinal=False)}  "
                                         f"({pontos(gap, casas=1)})")

                figc = go.Figure(go.Bar(
                    y=ordenado["pais"], x=ordenado["valor"], orientation="h",
                    marker_color=cores, text=etiquetas, textposition="outside",
                    hovertemplate="%{y}: %{x:.1f} %<extra></extra>"))
                if valor_ue is not None:
                    figc.add_vline(x=valor_ue, line_width=2, line_dash="dash",
                                   line_color="#64748b",
                                   annotation_text=("média UE-27: "
                                                    + percentagem(valor_ue, sinal=False)),
                                   annotation_position="top")
                figc.update_layout(height=max(330, 34 * len(ordenado)),
                                   margin=dict(t=42, b=40, l=10, r=120),
                                   xaxis_title="Variação homóloga dos preços alimentares (%)",
                                   plot_bgcolor="#fff", showlegend=False)
                figc.update_xaxes(gridcolor="#eef1f4", zerolinecolor="#cbd5e1")
                st.plotly_chart(figc, width="stretch")
                st.caption(
                    "A linha tracejada é a média da UE-27: à direita, inflação mais rápida do que na "
                    "UE; à esquerda, mais lenta. Entre parênteses, a distância em pontos percentuais."
                )

                if valor_ue is not None:
                    tb = ranking[["pais", "valor"]].copy()
                    tb["Face à UE-27 (p.p.)"] = (tb["valor"] - valor_ue).round(1)
                    tb.columns = ["País", "Variação homóloga (%)", "Face à UE-27 (p.p.)"]
                    tb = tb.sort_values("Variação homóloga (%)", ascending=False)
                    st.download_button(
                        "⬇️ Descarregar comparação (CSV com fonte)",
                        csv_com_fonte(tb, "Comparacao europeia da inflacao alimentar", dados,
                                      fonte="Eurostat, IHPC (ECOICOP v2)",
                                      conjuntos=[eurostat.HICP_MENSAL],
                                      extra=[("Mes de referencia", ultimo),
                                             ("Grupo", grupo_sel)]),
                        f"despesa_alimentar_ue27_{date.today()}.csv", "text/csv")

    # ==========================================================================
    # ABA 5 — Metodologia e fontes
    # ==========================================================================
with aba5:
    with painel("Metodologia e fontes"):
        st.markdown("#### Metodologia e fontes")
        st.caption(
            "Documentação completa do método. A nota metodológica em anexo à ferramenta "
            "desenvolve estes pontos com as referências legais."
        )

        with st.expander("🧭 O que é — e o que não é — «o cabaz»", expanded=True):
            st.markdown("""
    **Não existe um cabaz alimentar oficial em Portugal.** Existem pelo menos seis instrumentos,
    com naturezas e finalidades diferentes, que o debate público tende a fundir num só. A primeira
    utilidade desta ferramenta é não os confundir.
            """)
            st.markdown("""
    | Instrumento | Entidade | Natureza | O que mede | Limitação crítica |
    |---|---|---|---|---|
    | **Cabaz essencial** (63 produtos) | DECO PROteste | Privado | Preço absoluto em euros de um cabaz de **composição fixa**, recolha semanal nas principais cadeias. Série desde 05.01.2022 | Composição fixa — não acompanha substituição; sem ponderação pelo consumo real; não abrange comércio tradicional; metodologia não plenamente pública |
    | **IPC / IHPC**, classe COICOP 01 | INE / Eurostat | Oficial | **Variação** de preços, ponderada pela estrutura de despesa das famílias. Mensal | É índice, não nível: não responde a «quanto custa alimentar uma família». Média nacional |
    | **Índice de supermercados online** | DECO PROteste | Privado | Índice **relativo** entre insígnias (base 100 = a mais barata), ~250 produtos, por concelho | Mede *dispersão entre insígnias*, não nível nem evolução. Só canal online. Ponderadores de 2015/2016 |
    | **Observatório de Preços Agroalimentar** | GPP | Oficial | Preços de **39 produtos ao longo da cadeia** — da produção ao consumo — com margens por fileira | Cobertura limitada a 39 produtos e fileiras selecionadas; não mede o custo de um cabaz de consumo |
    | **Cabaz de apoio alimentar** | PO APMC / DGS | Social | Composição definida por **critério nutricional** (Roda dos Alimentos), para distribuição em espécie | Não é instrumento de preços. É a única definição pública de cabaz com critério nutricional |
    | **Cabaz «IVA zero»** (2023–24) | Governo / AT / ASAE | Administrativo | Lista taxativa de 46 tipologias com isenção temporária de IVA | Vigência encerrada. Critério nutricional/social, não estatístico. Ver o separador do simulador de IVA |
            """)

            st.markdown("**Onde se situa esta ferramenta**")
            st.markdown("""
    Esta aplicação **não é um sétimo cabaz** — não recolhe preços nem define uma lista de produtos.
    É um **instrumento de repartição e enquadramento**: parte de uma âncora oficial de despesa
    (IDF ou Contas Nacionais), reparte-a pelas nove classes COICOP e aplica a cada uma a variação
    oficial do índice. Responde a «quanto pesa a alimentação no orçamento de quem, e quanto disso é
    aumento de preço» — não a «quanto custa este cabaz hoje».

    Daí decorre o que **não** pode fazer: não dá o preço de nenhum produto, não compara insígnias,
    e não substitui a recolha da DECO como sinalizador semanal de preços no retalho.
            """)

            st.warning("""
    **Ponto central para leitura pública.** O número que domina o noticiário — «o cabaz custa X
    euros e atingiu novo máximo» — é o da DECO. É um indicador legítimo e útil enquanto
    *sinalizador de tendência de preços no retalho alimentar*, mas **não é um indicador de custo de
    vida nem de acessibilidade alimentar**. Um cabaz que sobe de preço não implica que as famílias
    estejam a gastar mais em alimentação: podem estar a substituir produtos, a mudar de insígnia ou
    a reduzir quantidades. Essa substituição é, ela própria, uma perda de bem-estar — e é
    justamente o que um cabaz de composição fixa não consegue ver.
            """)

        with st.expander("📘 O que é o IHPC — e porque não é o mesmo que o IPC"):
            st.markdown("""
    O **IHPC — Índice Harmonizado de Preços no Consumidor** é o índice de inflação construído
    segundo metodologia comum a todos os Estados-Membros, precisamente para que os valores sejam
    comparáveis entre países. Base legal: **Regulamento (UE) 2016/792**, desenvolvido pelo
    Regulamento de Execução (UE) 2020/1148. Em inglês designa-se HICP.

    Portugal produz **dois** índices, ambos calculados pelo INE a partir da mesma recolha de
    preços, mas com âmbitos distintos:
            """)
            st.dataframe(pd.DataFrame([
                {"Índice": "IPC — Índice de Preços no Consumidor",
                 "Para que serve": "Índice nacional: atualizações contratuais, indexação, leitura interna da inflação",
                 "Âmbito": "Consumo das famílias residentes; inclui rendas imputadas"},
                {"Índice": "IHPC — Índice Harmonizado",
                 "Para que serve": "Comparação entre Estados-Membros e política monetária do BCE",
                 "Âmbito": "Consumo monetário no território (inclui não residentes); exclui rendas imputadas"},
            ]), width="stretch", hide_index=True)
            st.markdown(
                "As diferenças de âmbito produzem valores próximos mas não idênticos. "
                "**Esta ferramenta usa o IHPC** por ser a única base que permite comparar Portugal "
                "com os restantes Estados-Membros com garantia de que se mede a mesma coisa."
            )

        with st.expander("🧮 Como se calcula o IHPC"):
            st.markdown("""
    O IHPC é um **índice de Laspeyres encadeado anualmente**. O cálculo tem dois níveis.

    **Nível elementar** — sem ponderadores, combinam-se os relativos de preço, em regra por
    média geométrica (fórmula de Jevons):
    """)
            st.latex(r"I = \prod_i \left( \frac{p_{i,t}}{p_{i,0}} \right)^{1/n}")
            st.markdown("""
    **Acima do nível elementar** — agregação ponderada, com encadeamento em dezembro do ano
    anterior:
    """)
            st.latex(r"I(m,y) = I(\text{Dez},y-1) \times \sum_i w_i^{\,y} \cdot \frac{I_i(m,y)}{I_i(\text{Dez},y-1)}")
            st.markdown("""
    Os ponderadores seguem uma regra precisa, fixada no Regulamento de Execução (UE) 2020/1148:

    1. Partem das **Contas Nacionais do ano y−2** — o último com dados de qualidade completa.
    2. São **revistos para representar o ano y−1**, com toda a informação disponível.
    3. São **atualizados a preços de dezembro de y−1**, para coincidir com o encadeamento.

    Daqui decorre a propriedade essencial: **os ponderadores são revistos todos os anos**. É isso
    que permite ao IHPC acompanhar alterações no padrão de consumo — quando as famílias trocam
    novilho por frango, o ponderador da carne reflete-o no ano seguinte. Um cabaz de composição
    fixa não o faz, e acumula por isso o chamado *viés de substituição*.

    A variação homóloga obtém-se diretamente do índice:
    """)
            st.latex(r"\pi(m) = \left[ \frac{I(m,y)}{I(m,y-1)} - 1 \right] \times 100")

        with st.expander("🧭 Em que conceito estão as Contas Nacionais — verificado a 12.08.2026"):
            st.markdown(f"""
    As duas bases de âncora divergem por um fator próximo de 2, e a explicação que esta aplicação
    dava para isso era **incompleta**. Dizia que as Contas Nacionais sobrestimam «porque medem o
    consumo no território e incluem não residentes». A primeira parte é verdade; a segunda não
    explica a divergência.

    ##### Primeiro: em que conceito está o conjunto

    O `nama_10_cp18` podia estar em conceito **interno** (despesa no território, turistas
    incluídos) ou **nacional** (residentes, onde quer que gastem). O conjunto não tem dimensão que
    o declare. Duas provas resolvem:

    **Identidade contabilística.** O total da desagregação por COICOP excede sistematicamente o
    `P31_S14` do `nama_10_gdp`, que é o consumo das famílias no conceito nacional:

    | Ano | COICOP (`nama_10_cp18`) | Nacional (`P31_S14`) | Diferença |
    |---|---|---|---|
    | 2019 | 146 691 M€ | 133 188 M€ | +13 503 M€ (10,1 %) |
    | **2020** | **129 986 M€** | **124 709 M€** | **+5 277 M€ (4,2 %)** |
    | 2024 | 192 796 M€ | 171 641 M€ | +21 155 M€ (12,3 %) |

    **O ano de 2020.** A diferença desabou 61 % no ano em que o turismo parou, e recuperou depois.
    Nada além do turismo produz esse padrão. **O conjunto está no conceito interno.**

    ##### Segundo: quanto é que isso contamina os alimentos

    Muito menos do que o total — e é aqui que a explicação antiga falhava. Em 2020:

    | | Variação 2020/2019 |
    |---|---|
    | 🍽️ Restauração (`CP111`) | **−36,6 %** |
    | 🛒 Alimentação em casa (`CP011`) | **+3,1 %** |

    Se a despesa alimentar em casa fosse materialmente de turistas, teria **caído** em 2020.
    Subiu. Os não residentes comem em restaurantes; não cozinham em casa.

    **Ressalva.** 2020 teve dois efeitos opostos sobre a alimentação em casa: os residentes
    substituíram restaurante por casa (a subir) e os turistas desapareceram (a descer). O saldo
    foi +3,1 %, o que **não prova que o efeito turista seja nulo** — só que é menor do que a
    substituição. O limite superior, se os não residentes consumissem alimentos em casa na
    proporção do seu peso no consumo total, seria 12,3 %; a evidência de 2020 diz que o valor real
    está bem abaixo disso.

    ##### O que isto muda

    A base **continua a não se trocar**, mas por outra razão. Não é «as Contas Nacionais estão
    contaminadas por turistas» — essa contaminação existe e é pequena nos alimentos. É que a
    divergência de cerca de 2,3× face ao IDF **continua sem explicação completa**: a
    sub-declaração dos inquéritos é conhecida e esperada, mas não desta ordem. Uma diferença
    assim não se adota sem a perceber, e é por isso que a aplicação continua a apresentar as duas
    bases como um **intervalo** em vez de escolher uma.

    Corrigiu-se também a citação da fonte, que continuava a apontar para o `nama_10_co3_p3` —
    arquivado com a passagem à COICOP 2018 e parado desde então.
            """)

        with st.expander("🔢 Os quatro passos desta ferramenta"):
            st.markdown("**1 · Âncora: quanto gasta o agregado médio em alimentação**")
            st.latex(r"\text{Contas Nacionais:}\quad \frac{D(y)}{H \times 12}"
                     r"\qquad\qquad \text{IDF:}\quad \frac{A(y)}{12}")
            st.caption(
                "D(y) = despesa alimentar nacional anual (Contas Nacionais) · H = número de "
                "agregados · A(y) = despesa alimentar anual por agregado, medida diretamente "
                "pelo IDF. As duas bases divergem por um fator próximo de 2 — a aplicação "
                "apresenta o intervalo e deixa a base à escolha."
            )

            st.markdown("**2 · Atualização ao mês corrente**")
            st.latex(r"\text{valor atual} = \text{valor da base} \times "
                     r"\frac{I(m)}{\bar{I}(R)}")
            st.caption(
                "I(m) = índice do mês · Ī(R) = média do índice no **período de referência** da "
                "base. Nas Contas Nacionais esse período é o ano civil da despesa. No IDF **não "
                "é um ano civil**: a recolha decorreu em 26 quinzenas seguidas, de fevereiro de "
                "2022 a fevereiro de 2023, e o INE não corrige os valores para uma data comum "
                "(Metainformação do IDF, V.6.1.1 e V.7.4). A média é por isso calculada sobre a "
                "janela **fevereiro de 2022 a janeiro de 2023**. Indexar a partir do ano civil "
                "de 2023 subestimava o valor atual em 21,05 €/mês — 8,3 %."
            )

            st.markdown("**3 · Ajustamento à composição do agregado**")
            st.latex(r"\text{despesa do agregado} = \text{valor atual} \times \frac{eq(A,C)}{eq(\bar{s})}")
            st.caption("A = adultos · C = crianças · s̄ = dimensão média nacional do agregado")

            st.markdown("**4 · Repartição por grupo de produto**")
            st.latex(r"V_i = \text{despesa total} \times \frac{w_i}{\sum_j w_j}")
            st.caption("wᵢ = ponderador oficial da classe i")

            st.markdown("**Contributo de cada grupo para o agravamento homólogo**")
            st.latex(r"\text{contributo}_i = V_i \cdot \frac{g_i}{1 + g_i}")
            st.markdown(
                "A soma dos contributos iguala exatamente a variação do total — a decomposição é "
                "**aditiva**, propriedade verificada por teste automático."
            )

            st.markdown("---")
            st.markdown("**5 · Taxa de IVA de partida — no simulador**")
            st.markdown("""
    O simulador precisa de saber que taxa cada grupo suporta **hoje**, antes de aplicar o cenário.
    Essa taxa não é escolhida: é apurada. Cada grupo COICOP contém produtos em taxas legais
    diferentes — pão a 6 % e pastelaria a 23 %, azeite a 6 % e óleos vegetais a 13 % —, e os
    ponderadores por subclasse da COICOP 2018 permitem medir a proporção de cada um.
                """)
            st.latex(r"c_i = \frac{\sum_b w_b \cdot \dfrac{t_b}{1+t_b}}{\sum_b w_b}"
                     r"\qquad\qquad t_i^{ef} = \frac{c_i}{1-c_i}")
            st.caption(
                "b percorre as subclasses do grupo i · w = ponderador da subclasse · "
                "t = taxa legal da subclasse · c = fração do preço que é imposto · "
                "t_ef = taxa única equivalente. **Não é uma taxa legal**: é a carga fiscal média "
                "do grupo tal como ele é hoje consumido."
            )
            st.markdown(
                "Usar esta taxa é **matematicamente idêntico** a simular escalão a escalão, não "
                "uma aproximação — a demonstração e a verificação numérica estão no separador do "
                "IVA, em «Como se calcula a taxa média efetiva»."
            )

        with st.expander("🧭 Duas bases de ponderação — qual serve para quê"):
            st.markdown("""
    A aplicação usa **duas** estruturas de ponderação, e não é indiferente qual se aplica a quê.
    A regra é simples:

    | | Ponderador | Responde a |
    |---|---|---|
    | **Estrutura e distribuição** | IDF 2022/2023, por quintil | Quem gasta o quê, e que parte do orçamento leva |
    | **Movimento dos preços** | IHPC, revisto anualmente | Quanto subiu cada grupo, e quanto contribuiu |

    A razão é conceptual, não de conveniência. O Documento Metodológico do IPC afirma que **o IHPC
    inclui a despesa de não residentes** no território económico. Para medir preços isso é
    irrelevante — um quilo de pão sobe o mesmo para quem lá vive e para quem está de passagem.
    Para medir a *estrutura de consumo das famílias portuguesas*, não é: mistura dois universos.

    O IDF não tem esse problema — mede agregados residentes, por inquérito direto — e é a única
    fonte aberta que desce ao quintil de rendimento. Em contrapartida é **quinquenal**, pelo que a
    sua estrutura envelhece entre vagas. É o IHPC, revisto todos os anos, que garante que o
    movimento dos preços acompanha a substituição de produtos.

    **O período de referência do IDF não é um ano civil.** A recolha decorreu entre **3 de
    fevereiro de 2022 e 5 de fevereiro de 2023, em 26 quinzenas seguidas**, com cada agregado
    inquirido ao longo de 14 dias; e o INE **não corrige os valores para uma data comum**
    (Metainformação do IDF, V.6.1.1 e V.7.4 — «Ajustamentos dos dados: não aplicável»). Os valores
    publicados são, portanto, uma média aos preços desses doze meses.

    Por isso a atualização ao mês corrente parte da média do índice na janela **fevereiro de 2022
    a janeiro de 2023**, e não de um ano civil. Não é um detalhe: indexar a partir de 2023
    subestimava o valor atual em **21,05 €/mês**, cerca de 8,3 %.
            """)

            _cmp = comparar_ponderadores(dados["pesos"], dados["variacoes_classe"])
            if _cmp["inflacao_idf"] is not None and _cmp["inflacao_ihpc"] is not None:
                st.markdown("**O que a escolha muda, medido**")
                m1, m2, m3 = st.columns(3)
                m1.metric("Inflação alimentar, ponderação IHPC",
                          percentagem(_cmp["inflacao_ihpc"], sinal=False))
                m2.metric("Inflação alimentar, ponderação IDF",
                          percentagem(_cmp["inflacao_idf"], sinal=False))
                m3.metric("Diferença atribuível à ponderação",
                          pontos(_cmp["diferenca"]))

                _dv = _cmp["desvios"].copy()
                _dv["Grupo"] = _dv["emoji"] + " " + _dv["classe"]
                _dv = _dv[["Grupo", "quota_ihpc", "quota_idf", "desvio"]]
                _dv.columns = ["Grupo", "Quota IHPC (%)", "Quota IDF (%)", "Desvio (p.p.)"]
                st.dataframe(
                    _dv.sort_values("Desvio (p.p.)", key=abs, ascending=False),
                    width="stretch", hide_index=True,
                    column_config={
                        "Quota IHPC (%)": st.column_config.NumberColumn(format="%.1f"),
                        "Quota IDF (%)": st.column_config.NumberColumn(format="%.1f"),
                        "Desvio (p.p.)": st.column_config.NumberColumn(format="%+.2f"),
                    })
                st.caption(
                    f"Desvio médio absoluto entre as duas estruturas: "
                    f"**{pontos(_cmp['desvio_medio'], sinal=False)}** · "
                    f"máximo: **{pontos(_cmp['desvio_maximo'], sinal=False)}** · "
                    "As quotas são calculadas dentro da alimentação, sobre a soma dos nove grupos."
                )
                st.caption(
                    "Parte deste desvio é a inclusão de turistas no IHPC, parte é a diferença de "
                    "anos de referência entre as duas fontes. Os dados abertos disponíveis não "
                    "permitem separar as duas causas — não existe exercício nacional de "
                    "conciliação entre inquérito e Contas Nacionais."
                )

            st.info("""
    **Uma terceira base foi ponderada e rejeitada.** Estudou-se acrescentar um instrumento que
    lesse a evolução dos ponderadores do IHPC deflacionados pelo índice de preços de cada grupo,
    para isolar mudanças de *quantidade* consumida das mudanças de preço. Não avançou: o
    Documento Metodológico do IPC estabelece que «a amostra e estrutura de ponderação referem-se
    sempre a dezembro do ano n−1» e que os ponderadores **já incorporam** a variação de preços
    até esse momento. Deflacioná-los pela média anual do índice desconta duas vezes uma parte do
    efeito-preço e nenhuma vez outra parte. A direção do resultado pode manter-se; a magnitude
    não é defensável. Medir alterações de quantidade exigiria dados de volume que nenhuma destas
    fontes publica.
            """)

        with st.expander("⚖️ Escalas de equivalência"):
            st.markdown(
                "Duas pessoas não gastam o dobro de uma: compra-se a granel, desperdiça-se menos, "
                "aproveitam-se sobras. As escalas traduzem essa partilha em coeficientes."
            )
            st.dataframe(pd.DataFrame([
                {"Escala": ESCALAS[k]["nome"], "1.º adulto": ESCALAS[k]["primeiro"],
                 "Adulto adicional": ESCALAS[k]["adulto"], "Criança (<14)": ESCALAS[k]["crianca"],
                 "Nota": ESCALAS[k]["nota"]}
                for k in ESCALAS
            ]), width="stretch", hide_index=True)
            st.latex(r"eq(A,C) = 1 + \alpha \cdot (A - 1) + \beta \cdot C")

            st.markdown("""
    **Como a escala é aplicada — e uma propriedade que convém ter presente.**

    O ponto de partida é a despesa do agregado médio nacional. A escala não calcula a despesa a
    partir do zero: **ajusta** desse agregado médio para o agregado em análise, e é aplicada aos
    **dois lados** do rácio — ao numerador e ao denominador.

    Daqui decorre um comportamento que à primeira vista surpreende: como o denominador também
    depende da escala, **o efeito de mudar de escala inverte-se** conforme o agregado seja maior
    ou menor do que a média nacional.

    Coeficientes menores significam que cada pessoa a mais custa menos, o que **comprime as
    diferenças** entre agregados de dimensão diferente. Um agregado menor do que a média
    aproxima-se dela por cima — o valor sobe. Um agregado maior aproxima-se dela por baixo — o
    valor desce. O ponto de viragem é exatamente a dimensão média.

    Não é um artefacto do cálculo: é o que qualquer normalização por escala de equivalência
    produz. É também a razão pela qual a aplicação apresenta sempre um intervalo, e não um valor
    único.
            """)
            st.markdown("---")
            st.markdown("**Porque não se usa a norma da UE por defeito — o teste**")
            st.markdown(f"""
    A escala OCDE modificada é a norma europeia para o *rendimento*, e foi construída para o
    consumo total, em que a partilha da habitação gera fortes economias de escala. Na alimentação
    essas economias são mais fracas — não se partilha uma refeição como se partilha um teto.

    Isto era, até aqui, uma ressalva qualitativa. **O IDF 2022/2023 permite medi-la.** O teste
    restringe-se a agregados **sem crianças dependentes**, onde a escala é mais limpa, e compara o
    rácio de despesa observado entre «2 ou mais adultos» e «1 adulto» com o rácio que cada escala
    prevê para essa mesma composição.
            """)

            _te = testar_escalas()
            if not _te.empty:
                _tab_e = pd.DataFrame([{
                    "Escala": r.nome.split(" (")[0],
                    "Rácio previsto": round(r.previsto, 3),
                    "Desvio na alimentação": r.desvio_alimentar,
                    "Desvio na despesa total": r.desvio_total,
                } for r in _te.itertuples()])
                st.dataframe(
                    _tab_e, width="stretch", hide_index=True,
                    column_config={
                        "Desvio na alimentação": st.column_config.NumberColumn(format="%+.1f %%"),
                        "Desvio na despesa total": st.column_config.NumberColumn(format="%+.1f %%"),
                    })
                _r_al = f"{ESCALAS_TESTE_RACIO['alimentar']:.3f}".replace(".", ",")
                _r_to = f"{ESCALAS_TESTE_RACIO['total']:.3f}".replace(".", ",")
                st.caption(
                    f"Rácio observado: **{_r_al}** na alimentação e **{_r_to}** na despesa total. "
                    f"Desvio positivo = a escala **subestima** o custo dos agregados maiores. "
                    f"Fonte: {ESCALAS_TESTE_FONTE}."
                )

                _mod = _te[_te["escala"] == "ocde_modificada"]
                _org = _te[_te["escala"] == "ocde_original"]
                if not _mod.empty and not _org.empty:
                    _dm = float(_mod["desvio_alimentar"].iloc[0])
                    _dmt = float(_mod["desvio_total"].iloc[0])
                    _do = float(_org["desvio_alimentar"].iloc[0])
                    st.success(f"""
    **A ressalva confirma-se, e o controlo é o que torna o teste convincente.**

    Na alimentação, a escala OCDE modificada **subestima** o custo dos agregados maiores em
    **{('%+.1f' % _dm).replace('.', ',')} %**. Na despesa total — aquilo para que a escala foi
    desenhada — o desvio **inverte-se**, para {('%+.1f' % _dmt).replace('.', ',')} %. O problema
    não é da escala em geral: é da alimentação em particular.

    Das três, a **OCDE original** é a que fica mais perto do observado
    ({('%+.1f' % _do).replace('.', ',')} % contra {('%+.1f' % _dm).replace('.', ',')} %), o que
    confirma empiricamente a escolha por defeito desta ferramenta — que até aqui se apoiava apenas
    num argumento teórico.
                    """)
                    st.caption(
                        f"**Precisão.** As duas restrições disponíveis nos quadros do IDF são "
                        f"ligeiramente inconsistentes entre si (adultos equivalentes médios "
                        f"reconstruídos: 1,435 contra 1,407 publicados). Consoante a que se "
                        f"privilegie, a subestimação fica entre **{ESCALAS_TESTE_INTERVALO[0]} % e "
                        f"{ESCALAS_TESTE_INTERVALO[1]} %**. O resultado é robusto no sinal e na "
                        f"ordem de grandeza, não no algarismo."
                    )

                # ---- circularidade do pressuposto, declarada e medida ----
                _sens = sensibilidade_escalas()
                if not _sens.empty:
                    _n_pressuposto = ESCALAS_TESTE_COMPOSICAO[1][0]
                    st.warning(f"""
    **Há uma circularidade neste teste, e é preciso dizê-lo.** O grupo «3 ou mais adultos» não tem
    contagem publicada: os **{numero(_n_pressuposto, 3)} adultos** usados no cálculo foram deduzidos
    admitindo que o quadro Q.2.8 do INE aplica a **escala OCDE modificada** — que é depois uma das
    três escalas avaliadas. O teste não é, portanto, inteiramente independente daquilo que avalia.
                    """)
                    _tab_s = pd.DataFrame([{
                        "Adultos no grupo «3 ou +»": (
                            numero(r.adultos_3mais, 3)
                            + (" ← pressuposto" if r.e_o_pressuposto else "")),
                        "Per capita": percentagem(r.desvio_per_capita),
                        "OCDE original": percentagem(r.desvio_ocde_original),
                        "OCDE modificada": percentagem(r.desvio_ocde_modificada),
                        "Mais próxima do observado": ESCALAS[r.mais_proxima]["nome"].split(" (")[0],
                        "Controlo inverte": "sim" if r.controlo_inverte else "não",
                    } for r in _sens.itertuples()])
                    st.dataframe(_tab_s, width="stretch", hide_index=True)

                    _todas_subestimam = bool(_sens["modificada_subestima"].all())
                    _todas_invertem = bool(_sens["controlo_inverte"].all())
                    _min_d = float(_sens["desvio_ocde_modificada"].min())
                    _max_d = float(_sens["desvio_ocde_modificada"].max())
                    _n_original = int((_sens["mais_proxima"] == "ocde_original").sum())
                    # Os dois pontos de rutura estavam inscritos à mão, ao lado
                    # de números calculados em direto (auditoria, E9). São
                    # bissecção sobre constantes que a aplicação já tem.
                    _rut = pontos_de_rutura_das_escalas()
                    _min_c, _max_c = float(_sens["adultos_3mais"].min()), float(_sens["adultos_3mais"].max())
                    _txt_rut = ""
                    if _rut["ultrapassagem"] is not None:
                        _txt_rut = (f"só acima de **{numero(_rut['ultrapassagem'], 2)} adultos em "
                                    f"média** é que a modificada passaria à frente")
                        if _rut["anulacao"] is not None:
                            _txt_rut += (f", e o desvio só se anularia com "
                                         f"**{numero(_rut['anulacao'], 2)} adultos** — valor sem "
                                         f"sentido para um grupo «3 ou mais»")
                        _txt_rut += ". "
                    st.caption(
                        f"**As duas conclusões sobrevivem ao pressuposto.** Em todos os cenários "
                        f"testados, de {numero(_min_c, 1)} a {numero(_max_c, 1)} adultos, a OCDE "
                        f"modificada continua a subestimar o custo alimentar "
                        f"{'(sempre)' if _todas_subestimam else '(nem sempre)'} — entre "
                        f"{percentagem(_min_d)} e {percentagem(_max_d)} — e o controlo da despesa "
                        f"total continua a inverter o sinal "
                        f"{'em todos' if _todas_invertem else 'nem sempre'}. A OCDE original é a "
                        f"mais próxima do observado em {_n_original} dos {len(_sens)} cenários; "
                        f"{_txt_rut}A direção do resultado não depende do pressuposto; a "
                        f"magnitude depende."
                    )

        with st.expander("💰 Rendimento e salários — o que é bruto, o que é líquido"):
            st.markdown("""
    Três fontes distintas alimentam os indicadores de esforço. **A diferença entre bruto e líquido
    não é um detalhe: muda o resultado de forma material** e, se ignorada, leva a subestimar a
    pressão sobre quem aufere menos.

    | Fonte | Conjunto | O que é | Natureza | Frequência |
    |---|---|---|---|---|
    | Rendimento das famílias | [`ilc_di03`](https://ec.europa.eu/eurostat/databrowser/view/ilc_di03/default/table) | Rendimento monetário do agregado, todas as fontes | **Líquido** | Anual |
    | Salário médio | [`nama_10_a10`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a10/default/table) ÷ [`nama_10_a10_e`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a10_e/default/table) | Massa salarial ÷ trabalhadores por conta de outrem | **Bruto** | Anual |
    | Salário mínimo | [`earn_mw_cur`](https://ec.europa.eu/eurostat/databrowser/view/earn_mw_cur/default/table) | RMMG em duodécimos de 14 mensalidades | **Bruto** | Semestral (janeiro e julho) |

    **Rendimento das famílias.** Vem do EU-SILC e é o mais completo: inclui salários, pensões,
    prestações sociais, rendimentos de capital e transferências, deduzidos impostos e contribuições.
    É publicado **por unidade de consumo equivalente** — já dividido pelas unidades do agregado,
    segundo a escala OCDE modificada. Para obter o rendimento de um agregado concreto, multiplica-se
    pelas suas unidades equivalentes.

    Estão disponíveis a **média** e a **mediana**. A aplicação usa a média por defeito, porque a
    despesa alimentar também é uma média — combinar média com mediana inflacionaria o rácio.

    **Salário médio.** Calculado a partir das Contas Nacionais: massa salarial (remunerações e
    salários) dividida pelo número de trabalhadores por conta de outrem. É uma remuneração **bruta**
    — antes de imposto e contribuições do trabalhador.

    **Não é «o salário médio» no sentido corrente.** O divisor conta **todos** os trabalhadores por
    conta de outrem, incluindo os que trabalham **a tempo parcial**, e o numerador exclui as
    contribuições sociais a cargo do empregador. O resultado fica portanto **abaixo** da remuneração
    de um trabalhador a tempo inteiro, e não é comparável com as estatísticas de ganho médio que
    convertem tudo a equivalentes a tempo completo.

    Duas vantagens sobre as séries de remunerações líquidas: os códigos são estáveis, e fica na
    **mesma base estatística** da despesa alimentar usada como âncora — o que evita mais uma mistura
    de universos. Sendo bruto, é comparável com o salário mínimo, mas **não** com o rendimento
    líquido do EU-SILC.

    **Salário mínimo.** O Eurostat **não** publica o valor legal. Publica a retribuição mínima
    mensal garantida convertida em **duodécimos de 14 mensalidades** — o valor legal multiplicado
    por 14/12 —, para que os países com 12, 13 ou 14 pagamentos anuais fiquem comparáveis. Em 2026, a título
    de exemplo, o valor legal era de **920 €/mês** e o Eurostat difundiu **1 073 €**.

    A aplicação usa o valor do Eurostat, e usa-o de propósito: a despesa alimentar é mensal e
    recorrente, pelo que a base correta para a fatia do orçamento é a **média mensal do rendimento
    anual**, com os subsídios distribuídos pelos 12 meses. Usar os 920 € atribuiria ao mês de
    dezembro um esforço alimentar que na prática se dilui. O que estava errado era o rótulo, não
    o número: a aplicação chamava-lhe «valor legal», e não é.

    É **bruto**: não desconta a contribuição do trabalhador para a Segurança Social nem o imposto
    retido, nem inclui prestações familiares. O rendimento efetivamente disponível de quem aufere o
    mínimo é **inferior** ao valor apresentado — logo, o esforço alimentar real é **superior** ao
    que este rácio indica.

    É por essa razão que a aplicação assinala as duas naturezas com cores distintas e adverte que
    não são diretamente comparáveis entre si.

    **Quem come e quem aufere não são o mesmo conjunto.** O multiplicador de salários é o número de
    pessoas que **efetivamente auferem rendimento**, nunca o total do agregado. E há um caso em que
    a diferença é decisiva: **os jovens entre os 14 e os 18 anos**.

    Para a escala de equivalência, uma pessoa de 15 ou 17 anos conta como adulta — come como
    adulta, e é isso que a escala mede. Mas não aufere rendimento. Um agregado de dois pais e dois
    adolescentes tem **quatro pessoas com peso alimentar de adulto e dois rendimentos**.

    É a composição em que o esforço alimentar é mais elevado, e precisamente a que os indicadores
    médios menos revelam. A aplicação assinala-a quando ocorre.
            """)

        with st.expander("🔄 Como a aplicação se mantém atualizada"):
            st.markdown("""
    **Não há dados gravados na aplicação.** Nada é fixado no código: em cada arranque, a aplicação
    pede ao Eurostat as séries de que precisa e usa **a observação mais recente de cada uma**.

    **Como escolhe o valor mais recente.** Para cada série, ordena as observações por período e fica
    com a última. Isso funciona qualquer que seja a periodicidade — mensal (`2026-06`), semestral
    (`2026S1`) ou anual (`2026`) — porque a codificação de períodos do Eurostat é ordenável.
    A consequência prática: **quando o Eurostat publicar um mês novo, a aplicação passa a usá-lo sem
    qualquer alteração ao código**.

    **Janela de pedido.** As séries anuais e semestrais são pedidas com **oito anos** de margem. É
    folgado de propósito: se uma publicação atrasar, continua a haver observações no intervalo e a
    aplicação não fica sem dados. As séries mensais usam janelas mais curtas, por serem densas.

    **Cache de seis horas.** Os dados ficam guardados em memória durante seis horas, para não repetir
    pedidos desnecessários — as séries mudam no máximo uma vez por mês. O botão **Recarregar do
    Eurostat**, na barra lateral, limpa a cache e força um pedido novo.

    **O período de cada valor está sempre visível.** Cada indicador mostra o seu período de
    referência — «Salário mínimo (2026S1)», «Contas Nacionais 2024» — para que nunca se confunda a
    data da consulta com a data do dado.
            """)
            st.info("""
    **Quando esperar dados novos**

    | Dado | Publicação |
    |---|---|
    | Estimativa rápida do índice (só agregados) | Último dia útil do mês de referência |
    | **Índice completo, com todas as classes** | **Cerca do dia 17 do mês seguinte** |
    | Ponderadores | Com os dados de janeiro, em fevereiro |
    | Salário mínimo | Janeiro e julho |
    | Rendimento e salário médio (EU-SILC) | Anual, com cerca de um ano de desfasamento |
    | Contas Nacionais (âncora em euros) | Anual, com cerca de dois anos de desfasamento |
    | Paridades de poder de compra | Junho do ano seguinte |

    O separador mostra sempre o último mês disponível no topo da aplicação. Se um valor parecer
    desatualizado, é porque a fonte ainda não publicou — não porque a aplicação não o foi buscar.
            """)
            st.warning("""
    **Alteração metodológica de fevereiro de 2026 — e o que ela custou a esta aplicação.**
    A partir dos dados de janeiro de 2026, o índice passou a ser compilado segundo a **ECOICOP
    versão 2** (alinhada com a COICOP 2018), com período de referência **2025 = 100**. As séries
    com a classificação anterior não foram apenas rebaseadas: **foram arquivadas em conjuntos
    próprios, que deixaram de avançar**. O Eurostat inscreveu-o no título — «HICP — monthly data
    (index) **(1996-2025)**».

    Os conjuntos antigos continuaram a responder normalmente, com dados bem formados, apenas
    parados em dezembro de 2025. **A aplicação apresentou-os como sendo os mais recentes durante
    sete meses, sem nunca dar erro.** Foi corrigido a 11.08.2026: passou a usar `prc_hicp_minr` e
    `prc_hicp_iw`, e as classes passaram a ter as designações da COICOP 2018.

    A lição que ficou inscrita no código: **uma série que responde não é uma série que avança**.
    A verificação de frescura, que existia apenas para as fontes sem API, tem de cobrir também as
    que têm.
            """)

        with st.expander("🗂️ Origem dos dados — conjuntos utilizados e ligações"):
            st.markdown("""
    Todos os dados quantitativos são obtidos em direto do **Eurostat**, que difunde as estatísticas
    compiladas pelos institutos nacionais — no caso português, o **INE**. As ligações abrem
    diretamente o conjunto no Data Browser do Eurostat.

    | Elemento | Conjunto | O que mede | Frequência |
    |---|---|---|---|
    | Ponderadores por grupo | [`prc_hicp_iw`](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_iw/default/table) | Fração de cada mil euros de consumo total (‰) | Anual |
    | Índice de preços | [`prc_hicp_minr`](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_minr/default/table) | Nível do índice (unidade `I25`) — não são euros | Mensal |
    | Variação homóloga | [`prc_hicp_minr`](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_minr/default/table) | Subida face ao mesmo mês do ano anterior (unidade `RCH_A`, %) | Mensal |
    | Despesa alimentar (âncora) | [`nama_10_cp18`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_cp18/default/table) | Despesa efetiva em euros (Contas Nacionais, COICOP 2018) | Anual |
    | Dimensão do agregado | [`ilc_lvph01`](https://ec.europa.eu/eurostat/databrowser/view/ilc_lvph01/default/table) | N.º médio de pessoas por agregado | Anual |
    | N.º de agregados | [`lfst_hhnhtych`](https://ec.europa.eu/eurostat/databrowser/view/lfst_hhnhtych/default/table) | Total de agregados familiares (milhares), série anual | Anual |
    | Nível de preços comparado | [`prc_ppp_ind_1`](https://ec.europa.eu/eurostat/databrowser/view/prc_ppp_ind_1/default/table) | Quão caros são os alimentos, categoria `A010101` (UE-27 = 100) | Anual |
    | Rendimento das famílias | [`ilc_di03`](https://ec.europa.eu/eurostat/databrowser/view/ilc_di03/default/table) | Rendimento líquido equivalente, médio e mediano | Anual |
    | Salário médio | [`nama_10_a10`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a10/default/table) ÷ `nama_10_a10_e` | Remuneração média **bruta** dos trabalhadores por conta de outrem | Anual |
    | Salário mínimo | [`earn_mw_cur`](https://ec.europa.eu/eurostat/databrowser/view/earn_mw_cur/default/table) | RMMG em duodécimos de 14 mensalidades, **bruta** | Semestral |

    **Parâmetros que não são dados oficiais**

    | Parâmetro | Origem | Nota |
    |---|---|---|
    | Taxa **atual** de cada grupo | **Apurada**, não editável | É a **taxa média efetiva**, calculada dos ponderadores por subclasse da COICOP 2018 e das Listas I e II. Não é um parâmetro do utilizador: é um facto medido |
    | Taxa **do cenário** | Parâmetro do utilizador | Limitada às taxas que existem no Código do IVA — isenção, 6 %, 13 % e 23 % |
    | Adultos com rendimento | Parâmetro do utilizador | Multiplicador dos salários; as crianças não entram |
    | Repercussão | **Calibrada** — @RHO@ % por defeito, ajustável | Já não é uma hipótese de trabalho: é derivada da avaliação do Banco de Portugal ao «IVA zero» de 2023, sobre a medida idêntica no mesmo país. Banda @RHO_LO@ % a @RHO_HI@ % |

    **Dois números de agregados, para dois usos diferentes.** O denominador da âncora das Contas
    Nacionais é o número de agregados **do ano da despesa** — hoje @ANO_DESPESA@, e é por isso que
    a aplicação usa @AGREG_ANCORA@ agregados nesse cálculo. A extrapolação nacional do simulador de
    IVA usa o **ano mais recente**, @ANO_AGREGADOS@, com @AGREG_RECENTE@ agregados, porque o que se
    extrapola é o efeito de uma medida sobre o país de hoje. Usar o número mais recente também no
    denominador da âncora baixá-la-ia por razão nenhuma: os agregados cresceram, e a despesa não os
    acompanhou porque é de outro ano.

    **Recuo do n.º de agregados:** se o conjunto anual do Eurostat não estiver disponível ou
    devolver um valor implausível, a aplicação usa o valor censitário — **4 149 096** agregados
    domésticos privados ([INE, Censos 2021](https://www.ine.pt)).

    As duas fontes não medem o mesmo universo: o Inquérito ao Emprego é uma amostra e exclui
    alojamentos coletivos, pelo que lê sistematicamente abaixo do recenseamento exaustivo. Em 2021,
    ano em que ambos existem, **3 939 900** contra **4 149 096** — menos 5,0 %.
            """
            # Os valores da repercussão vêm do `config` e não são escritos à mão:
            # o bloco não pode ser f-string (contém chavetas literais), por isso
            # substituem-se por marcador.
            .replace("@RHO@", numero(REPERCUSSAO_PADRAO * 100, 0))
            .replace("@RHO_LO@", numero(REPERCUSSAO_BANDA[0] * 100, 1))
            .replace("@RHO_HI@", numero(REPERCUSSAO_BANDA[1] * 100, 0))
            # O ano da despesa estava inscrito à mão — «hoje 2022» — e a migração
            # para o `nama_10_cp18` (E16) deixou-o para trás: passou a ser 2024, e
            # este parágrafo contradizia a barra de estado da própria aplicação
            # (auditoria de 12.08.2026, K7).
            # O denominador é sempre o da âncora das Contas Nacionais, seja qual
            # for a base escolhida na barra lateral: é dela que o parágrafo fala.
            .replace("@ANO_DESPESA@", str(dados.get("despesa_ano") or "—"))
            .replace("@ANO_AGREGADOS@", str(dados.get("agregados_ano") or "—"))
            .replace("@AGREG_ANCORA@", numero(_den_contas["valor"]))
            .replace("@AGREG_RECENTE@", numero(agregados)))
            st.info(
                "**Sobre os ponderadores.** Somam 1 000 ‰ sobre **todo** o cabaz do índice — não "
                "sobre a alimentação. Os nove grupos alimentares somam apenas o peso da alimentação "
                "no consumo total. Por isso o cálculo normaliza pela soma dos nove, e não pelos 1 000 ‰."
            )

        with st.expander("🔗 Ver os dados em bruto — endereços exatos desta sessão"):
            st.markdown("""
Cada número da aplicação vem de um pedido concreto ao Eurostat. Os endereços abaixo são os que
foram efetivamente usados **nesta sessão** — abrem no navegador e descarregam o ficheiro em
bruto, exatamente os mesmos dados que a aplicação leu.

Servem para **verificar qualquer valor** sem depender da aplicação, e para reproduzir o cálculo
em Excel ou noutra ferramenta.
            """)
            _end = dados.get("enderecos") or []
            if not _end:
                st.info("Sem endereços registados nesta sessão.")
            else:
                _rot = {
                    "prc_hicp_iw": "Ponderadores por grupo — coluna «Ponderador ‰»",
                    "prc_hicp_minr": ("Índice de preços e variação homóloga — "
                                      "atualiza a âncora ao mês corrente e alimenta "
                                      "a coluna «Variação %»"),
                    "nama_10_cp18": "Despesa alimentar e consumo total — âncora em euros",
                    "ilc_lvph01": "Dimensão média do agregado",
                    "lfst_hhnhtych": "Número de agregados familiares",
                    "ilc_di03": "Rendimento equivalente das famílias",
                    "earn_mw_cur": "Salário mínimo",
                    "nama_10_a10": "Massa salarial — numerador do salário médio",
                    "nama_10_a10_e": "Trabalhadores por conta de outrem — denominador",
                    "prc_ppp_ind_1": "Nível de preços comparado",
                }
                for _ds, _url, _via in _end:
                    st.markdown(
                        f"**{_rot.get(_ds, _ds)}**  \n"
                        f"`{_ds}` · via **{_via}** · [abrir os dados em bruto]({_url})")
                st.caption(
                    "Cada endereço é o do pedido que **produziu efetivamente** o número — "
                    "não o de uma tentativa. Quando a via SDMX falha, a aplicação recorre à "
                    "API Statistics e é esse o endereço que aqui aparece. Até 11.08.2026 "
                    "registava-se a tentativa em vez do resultado, e o painel chegou a "
                    "oferecer ligações que devolviam erro (auditoria, E5).  \n"
                    "Formato SDMX-CSV: uma linha por observação, com as dimensões em colunas "
                    "(`coicop18`, `geo`, `TIME_PERIOD`) e o valor em `OBS_VALUE`. A via "
                    "Statistics devolve JSON-stat."
                )

        with st.expander("🧮 Como se obtém cada coluna da tabela detalhada"):
            st.markdown("""
A tabela do primeiro separador tem cinco colunas calculadas. Cada uma vem de um sítio concreto.

**Código** — a classe COICOP, de `CP0111` a `CP0119`. Não é calculado: é a nomenclatura
oficial. `CP0111` é pão e cereais, `CP0112` carne, e assim por diante.

**Ponderador (‰)** — vem tal e qual de `prc_hicp_iw`, sem transformação. Diz quantos de cada
mil euros do consumo total das famílias vão para aquele grupo. Se pão e cereais tiver 28,1 ‰,
significa 2,81 % do consumo total — e, dentro da alimentação, 28,1 dividido pela soma dos nove.

**Quota** — o ponderador do grupo dividido pela soma dos nove ponderadores. É a fração da
despesa **alimentar** que cabe àquele grupo. A soma das nove quotas dá 100 %.

**Valor (€)** — a despesa alimentar mensal do agregado, multiplicada pela quota do grupo.
            """)
            st.latex(r"V_i = \text{despesa total} \times \frac{w_i}{\sum_j w_j}")
            st.markdown("""
**Variação (%)** — vem tal e qual de `prc_hicp_minr`, sem transformação. É a variação homóloga
oficial daquele grupo: de quanto subiram os preços face ao mesmo mês do ano anterior.

**Contributo (€)** — quantos euros do agravamento dos últimos doze meses se devem àquele grupo.
Se o grupo vale hoje *Vᵢ* e os preços subiram *gᵢ* por cento, há um ano valia *Vᵢ/(1+gᵢ)*:
            """)
            st.latex(r"\text{contributo}_i = V_i - \frac{V_i}{1+g_i} = V_i \cdot \frac{g_i}{1+g_i}")
            st.success("""
**Exemplo com números.** Suponha despesa alimentar mensal de **400 €**, e que o grupo «carne»
tem ponderador 42,3 ‰ numa soma de 195,0 ‰:

1. **Quota** = 42,3 ÷ 195,0 = **21,7 %**
2. **Valor** = 400 € × 0,217 = **86,77 €**
3. **Variação** = 4,8 % (lida diretamente do Eurostat)
4. **Contributo** = 86,77 × 0,048 ÷ 1,048 = **3,97 €**

Interpretação: dos euros a mais que a família gasta por mês face ao ano passado, **3,97 €**
devem-se à carne. Somando os nove contributos obtém-se exatamente o agravamento total — é uma
propriedade verificada por teste automático.
            """)
            st.warning("""
**O que não é calculado a partir de preços.** Nenhuma coluna resulta de observar preços de
produtos. Os ponderadores e as variações vêm prontos do Eurostat; o único cálculo é a
repartição de um valor total por essas proporções. É por isso que a tabela é uma
**reconstituição**, e não uma medição.
            """)

        with st.expander("⏱️ Estas séries ainda estão a avançar?"):
            st.markdown("""
    **Uma série que responde não é uma série que avança.** Um conjunto arquivado devolve HTTP 200
    e dados bem formados — apenas parou. Foi assim que esta aplicação apresentou dezembro de 2025
    como «último mês disponível» durante sete meses, sem dar erro nenhum.

    O prazo de cada série é o seu **desfasamento normal de publicação mais um ciclo**, e não um
    prazo uniforme: as Contas Nacionais têm dois anos de atraso por construção, e está certo que
    tenham. O que este quadro procura é a série que **parou**, não a série que é lenta.
            """)
            if _fresc.empty:
                st.info("Sem séries a vigiar nesta sessão.")
            else:
                _tab_f = pd.DataFrame([{
                    "": "⛔" if r.desatualizada else ("❔" if not r.verificada else "✅"),
                    "Série": r.serie,
                    "Conjunto": r.conjunto,
                    "Cadência": r.cadencia,
                    "Último período": r.periodo,
                    "Idade (dias)": r.dias,
                    "Prazo (dias)": r.limite_dias,
                    "Porquê este prazo": r.porque,
                } for r in _fresc.itertuples()])
                st.dataframe(_tab_f, width="stretch", hide_index=True)
                st.caption(
                    "⛔ parou · ✅ dentro do prazo · ❔ período não interpretável — não é "
                    "acusação, mas também não é confirmação. A idade conta a partir do **fim** "
                    "do período, que é a leitura mais favorável à fonte."
                )

        with st.expander("🔌 Registo das ligações desta sessão"):
            st.dataframe(pd.DataFrame(dados["registo"],
                                      columns=["Dados pedidos", "Via de acesso usada",
                                               "N.º de observações"]),
                         width="stretch", hide_index=True)
            st.info("""
    **«SDMX» não é um método de ponderação — é a via de acesso aos dados.**

    SDMX (*Statistical Data and Metadata eXchange*) é a norma internacional de troca de dados
    estatísticos, usada pelo Eurostat, INE, BCE e FMI. Aqui designa apenas **por que porta a
    aplicação foi buscar os números**:

    - **SDMX 2.1** — o filtro segue no próprio endereço, pelo que o Eurostat devolve exatamente as
      séries pedidas. É a via preferida.
    - **API Statistics** — os filtros seguem como parâmetros. Usada se a primeira falhar.

    Ambas devolvem **os mesmos números oficiais**. A via usada não afeta os resultados; consta aqui
    apenas para diagnóstico.
            """)

        with st.expander("📛 «Despesa alimentar» e não «cabaz» — porquê"):
            st.markdown("""
Os dois termos designam objetos diferentes, e a aplicação usa apenas o primeiro para o que
mede. «Cabaz» aparece só quando se fala de cabazes **de terceiros** ou do «cabaz zero» de 2023.

| | **Cabaz** | **Despesa alimentar** |
|---|---|---|
| O que é | Lista de produtos com quantidades definidas | Quanto uma família gasta em comida |
| Como se obtém | Somando os preços dos artigos da lista | Repartindo despesa efetiva por grupos |
| Unidade natural | Um ato de compra | Um mês |
| Quantidades | Fixas e conhecidas | Não existem — só euros |

Esta aplicação **não tem cabaz nenhum**: não conhece quantidades, não observa preços de
produtos, não tem lista de artigos. Tem despesa em euros e variações de preço oficiais.
Chamar-lhe cabaz seria prometer o que não entrega.

            """)
        with st.expander("🏷️ De onde vem a classificação COICOP"):
            st.markdown("""
    A **COICOP** — *Classification of Individual Consumption According to Purpose* — é uma
    classificação das **Nações Unidas** (Divisão de Estatística), não do Eurostat. Serve para
    organizar a despesa de consumo das famílias **por finalidade**, e é usada mundialmente nas
    Contas Nacionais e nos inquéritos às despesas.

    A União Europeia adota-a numa versão própria, a **ECOICOP** (*European COICOP*), tornada
    obrigatória para o índice de preços pelo Regulamento (UE) 2016/792. É por isso que os mesmos
    códigos aparecem no INE, no Eurostat e nos institutos de todos os Estados-Membros: não é uma
    convenção do Eurostat, é uma norma internacional que o Eurostat implementa.

    A hierarquia relevante aqui:

    | Nível | Código | Designação |
    |---|---|---|
    | Divisão | 01 | Produtos alimentares e bebidas não alcoólicas |
    | Grupo | 01.1 | Produtos alimentares |
    | Classes | 01.1.1 a 01.1.9 | As nove do quadro abaixo |

    Estas nove classes são usadas nesta aplicação porque são o **nível mais fino em que o Eurostat
    publica simultaneamente ponderadores e índices** para todos os Estados-Membros. Qualquer outro
    agrupamento — fresco contra processado, saudável contra não saudável — exigiria microdados que
    não existem em acesso público.

    **A aplicação usa a COICOP versão 2018 (ECOICOP ver.2)**, em vigor no índice desde janeiro de
    2026. As designações abaixo são as **do INE**, não uma tradução desta ferramenta: estão
    transcritas do anexo do relatório do IDF 2022/2023. A forma curta é a usada nos cartões e nos
    gráficos, onde não cabe a designação completa.
            """)
            st.dataframe(pd.DataFrame([
                {"Código": f"01.1.{c['cod'][5]}",
                 "Forma curta": f"{c['emoji']} {c['nome']}",
                 "Designação oficial (INE, COICOP 2018)": c["oficial"]}
                for c in CLASSES
            ]), width="stretch", hide_index=True)
            st.caption(f"Fonte das designações: {CLASSES_FONTE}.")
            st.info("""
    **A revisão mudou o conteúdo das classes, não só os nomes.** Os códigos `CP0111` a `CP0119`
    sobreviveram, mas o que está dentro deles mudou — a classe 01.1.2 passou a incluir animais
    vivos, a 01.1.6 os frutos de casca rija, a 01.1.7 os tubérculos e as leguminosas, a 01.1.9 os
    alimentos pré-preparados. Até 11.08.2026 esta aplicação mostrava os rótulos da versão
    anterior («Pão e cereais», «Fruta», «Legumes e hortícolas»), que já não descreviam o que a
    classe continha.

    Há um efeito lateral que vale a pena registar: **o IDF 2022/2023 já usava a COICOP 2018**,
    enquanto o índice ainda estava na versão 1. Durante esse período a aplicação cruzava as duas
    — estrutura de despesa numa classificação, variação de preços na outra, sob o mesmo rótulo.
    Com a migração, as duas fontes passaram a estar **na mesma classificação**.
            """)

        with st.expander("👶 Porquê «crianças com menos de 14 anos» e não outra idade"):
            st.markdown("""
    O limiar dos 14 anos **não é uma escolha desta aplicação nem a definição demográfica de
    criança**. É o limiar inscrito nas próprias escalas de equivalência:

    - **Escala OCDE modificada**, norma do Eurostat para o rendimento: 1,0 ao primeiro adulto,
      0,5 a cada pessoa adicional **com 14 ou mais anos**, 0,3 a cada pessoa **com menos de 14**.
    - **Escala OCDE original**: 1,0 / 0,7 / 0,5, com o mesmo limiar.

    Alterar o limiar para 15, 16 ou 18 anos invalidaria os coeficientes — que foram estimados com
    aquela fronteira. Para usar outra idade seria preciso outra escala, estimada em conformidade.

    Isto é distinto das definições demográficas do INE, que variam consoante o contexto: nas
    estatísticas demográficas «jovens» são frequentemente os 0-14 anos; na proteção de menores, a
    menoridade vai até aos 18. São conceitos com finalidades diferentes, e não se misturam com os
    limiares das escalas de equivalência.

    **Consequência prática que importa reter.** Entre os 14 e os 18 anos, uma pessoa conta como
    adulta para efeitos de peso alimentar — e com razão, porque come como adulta — mas não aufere
    rendimento. Por isso a aplicação separa as duas contagens: **pessoas com 14 ou mais anos**
    determina a despesa; **quantas auferem rendimento** determina o denominador do esforço. Não são
    o mesmo número, e confundi-los subestima a pressão sobre as famílias com adolescentes.
            """)

        with st.expander("⚠️ Limitações a declarar em qualquer uso"):
            st.markdown("""
    1. **A decomposição não é observação.** É uma imputação de um valor total por ponderadores
       oficiais; não substitui a recolha de preços produto a produto.
    2. **Não há quantidades físicas.** A ferramenta mede despesa e variação de preço, não quilos
       nem litros. Para raciocinar em quantidades seria necessário o IDEF/INE ou dados de transação.
    3. **A âncora parte de uma média nacional.** Não distingue escalão de rendimento nem região.
    4. **As escalas de equivalência são aproximações — e há um viés quantificável.** Construídas
       para o consumo total; além disso, o agregado médio nacional é modelado como composto **apenas
       por adultos**, porque a dimensão média é publicada sem decomposição etária. Como o agregado
       médio real inclui menores, que pesam menos na escala, o denominador fica **sobrestimado em
       cerca de 4 a 5 %** — e todos os valores por agregado saem **subestimados na mesma proporção**.
       O viés é sistemático e na mesma direção para todas as composições, pelo que não afeta as
       comparações entre elas.
    5. **Desfasamento das Contas Nacionais.** A âncora assenta num ano com cerca de dois anos de
       desfasamento, atualizado por índice de preços.
    6. **A taxa de partida de cada grupo é apurada, não predefinida.** O Código do IVA classifica
       por produto; a aplicação trabalha por grupo COICOP. A partir de 11.08.2026 cada grupo entra
       na simulação com a sua **taxa média efetiva**, apurada dos ponderadores por subclasse — e
       não com a taxa predominante. Subsiste como aproximação a parcela **indeterminada** do
       apuramento e a atribuição por predominância; a sensibilidade a ambas está apresentada como
       intervalo. Ver o painel «Quanto do cabaz segue cada taxa» no separador do IVA.
    7. **A repercussão está calibrada, mas continua a ser o parâmetro decisivo.** Desde
       12.08.2026 parte de 95 %, derivado da avaliação do Banco de Portugal ao «IVA zero» de
       2023 — a medida idêntica, no mesmo país. Antes disso partia de 40 %, um valor de
       trabalho sem fonte portuguesa, e a aplicação subestimava a poupança por um fator de 2,4.
       Mesmo calibrado, é o número que mais move o resultado: qualquer valor do simulador é
       condicional a ele e deve ser apresentado como intervalo. E a estimativa vem de uma medida
       **temporária e mediática**, avaliada ao longo de quatro meses — uma alteração permanente
       e discreta pode repercutir-se menos.
    8. **A extrapolação agregada é ilustrativa.** Não é uma estimativa de custo orçamental.
            """)
            st.warning("""
    **9 · O preço usado não é o preço que uma família concreta paga.** Há duas razões distintas,
    e ambas devem ser declaradas:

    **Dispersão entre operadores.** O índice é uma **média nacional ponderada** de uma amostra de
    estabelecimentos — grande distribuição, comércio tradicional, canais especializados —, com
    peso atribuído a cada canal e região segundo o consumo real. Mas os operadores praticam preços
    muito diferentes entre si: quem compre sempre em *discount* enfrenta níveis abaixo desta
    média; quem viva em zona de baixa densidade, acima. O índice capta bem a **variação**; o
    **nível** de cada família oscila em torno dele, e essa dispersão não é visível aqui.

    **Preço de prateleira e preço pago.** O critério do INE é preciso e vale a pena citá-lo em vez
    de o aproximar. O Documento Metodológico do IPC (2023) determina que os descontos entram no
    índice **«desde que de aplicação generalizada aos consumidores»**. Daqui decorre uma linha
    divisória nítida:

    | Tipo de desconto | Entra no índice? |
    |---|---|
    | Promoção aberta a qualquer cliente, campanha de folheto, redução de preço em loja | **Sim** |
    | Cartão de fidelização, cupão, talão, desconto em cartão | **Não** — é condicional |

    *O critério entre aspas é citação literal (INE, Documento Metodológico do IPC, 2023, pp. 26 e
    40). A arrumação dos tipos de desconto no quadro é leitura desta ferramenta: o documento fixa a
    regra, não classifica casos concretos.*

    Não é, portanto, que a recolha falhe descontos ao acaso: exclui **por regra** os que dependem
    de o consumidor aderir a um programa. O desvio entre preço registado e preço pago é o que
    resulta desses descontos condicionais, e **tende a crescer** à medida que os programas de
    fidelização se difundem — o que significa que o índice pode sobrestimar ligeiramente a
    aceleração do preço efetivamente pago.

    Só dados de transação — e-fatura ou *scanner data* — permitiriam medir o preço realmente pago
    e a sua dispersão entre operadores e territórios. O IPC **não usa scanner data**: a recolha
    automatizada é por *web scraping* em cadeias de implantação nacional.
            """)
            st.warning("""
    **Os ponderadores do IHPC incluem turistas — confirmado em fonte primária.** O Documento
    Metodológico do IPC (INE, 2023) é explícito: «O IHPC inclui a despesa realizada pelos não
    residentes ("turistas") no território económico e exclui a despesa dos residentes no exterior,
    originando uma estrutura de ponderação diferente da utilizada no IPC.»

    Em Portugal, dado o peso do turismo, a diferença não é trivial. **Não afeta as variações de
    preço** — essas medem o mesmo movimento independentemente de quem compra — mas afeta qualquer
    leitura de **estrutura de consumo** feita sobre eles, e afeta o nível de qualquer valor obtido
    por repartição.

    É por isso que a aplicação separa as duas funções: o **IHPC** dá o movimento dos preços, o
    **IDF** dá a estrutura e a distribuição. O INE publica ponderadores do IPC em conceito
    nacional, mas apenas em ine.pt; o Eurostat só difunde os do IHPC.
            """)

        with st.expander("📖 Base legal e documentação"):
            st.markdown("""
    **Quadro legal do índice**

    - [Regulamento (UE) 2016/792](https://eur-lex.europa.eu/legal-content/PT/TXT/?uri=CELEX%3A32016R0792) — quadro legal do IHPC
    - Regulamento de Execução (UE) 2020/1148 — especificações metodológicas e técnicas
    - Regulamento (CE) n.º 1445/2007 — regras comuns das Paridades de Poder de Compra

    **Documentação metodológica**

    - [Eurostat — HICP methodology](https://ec.europa.eu/eurostat/statistics-explained/index.php/HICP_methodology)
    - [Metadados do IHPC](https://ec.europa.eu/eurostat/cache/metadata/en/prc_hicp_esms.htm)
    - [Derivação dos ponderadores do IHPC](https://ec.europa.eu/eurostat/documents/10186/10693286/Derivation-of-HICP-weights-for-2022.pdf)
    - [Metadados das Paridades de Poder de Compra](https://ec.europa.eu/eurostat/cache/metadata/en/prc_ppp_esms.htm)
    - [Níveis comparativos de preços — Statistics Explained](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Comparative_price_levels_of_consumer_goods_and_services)

    **Classificação**

    - COICOP — Divisão de Estatística das Nações Unidas
    - ECOICOP — versão europeia, obrigatória por regulamento

    **Fontes nacionais**

    - [INE](https://www.ine.pt) — Índice de Preços no Consumidor, Censos 2021, Inquérito às Despesas das Famílias
            """)

st.divider()
st.caption(RODAPE)
