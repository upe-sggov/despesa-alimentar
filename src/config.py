"""
Configuração da aplicação — classes de produto, países e identidade gráfica.

As nove classes correspondem à divisão 01.1 da COICOP (Classificação do Consumo
Individual por Objetivo), a nomenclatura que o INE e o Eurostat usam para
organizar a despesa das famílias.
"""

# --------------------------------------------------------------------------
# Identidade gráfica SGGov (Manual de Normas Gráficas, 2025)
# --------------------------------------------------------------------------
VERDE = "#0E7433"
AZUL = "#2B5683"
DOURADO = "#BE9C54"
VERMELHO = "#D02117"
AMARELO = "#FFD200"
CINZENTO = "#171715"

# --------------------------------------------------------------------------
# Classes de produtos alimentares (COICOP 01.1)
# --------------------------------------------------------------------------
# `iva` é a taxa predefinida, editável na aplicação. O Código do IVA classifica
# por produto (Lista I), não por classe COICOP: a correspondência é aproximada
# e deve ser afinada antes de qualquer uso em decisão.
CLASSES = [
    {"cod": "CP0111", "nome": "Pão e cereais",        "emoji": "🍞", "cor": "#C98B3A", "iva": 6},
    {"cod": "CP0112", "nome": "Carne",                "emoji": "🥩", "cor": "#C0392B", "iva": 6},
    {"cod": "CP0113", "nome": "Peixe e marisco",      "emoji": "🐟", "cor": "#2980B9", "iva": 6},
    {"cod": "CP0114", "nome": "Leite, queijo e ovos", "emoji": "🥛", "cor": "#8E9AAF", "iva": 6},
    {"cod": "CP0115", "nome": "Óleos e gorduras",     "emoji": "🫒", "cor": "#B8A02E", "iva": 6},
    {"cod": "CP0116", "nome": "Fruta",                "emoji": "🍎", "cor": "#D35400", "iva": 6},
    {"cod": "CP0117", "nome": "Legumes e hortícolas", "emoji": "🥦", "cor": "#0E7433", "iva": 6},
    {"cod": "CP0118", "nome": "Açúcar e doces",       "emoji": "🍬", "cor": "#A0568F", "iva": 23},
    {"cod": "CP0119", "nome": "Outros alimentos",     "emoji": "🧺", "cor": "#6B7280", "iva": 23},
]

CODIGOS = [c["cod"] for c in CLASSES]
POR_CODIGO = {c["cod"]: c for c in CLASSES}

# Agregado alimentar (soma das nove classes)
COICOP_ALIMENTAR = "CP011"

# --------------------------------------------------------------------------
# Agregados especiais do índice — permitem separar o que é choque conjuntural
# do que é inflação estrutural, e situar a alimentação no conjunto dos preços.
# --------------------------------------------------------------------------
AGREGADOS = [
    # --- a alimentação por dentro: são componentes do objeto do estudo ---
    {"cod": "FOOD_NP", "nome": "Alimentos não transformados", "cor": "#D02117", "larg": 2.4,
     "grupo": "alimentacao", "porque": "Frescos. Reagem a clima e sazonalidade — é aqui que "
                                       "os choques de oferta aparecem primeiro."},
    {"cod": "FOOD_P", "nome": "Alimentos transformados", "cor": "#BE9C54", "larg": 2.4,
     "grupo": "alimentacao", "porque": "Pão, laticínios, conservas. Refletem custos de "
                                       "produção e distribuição, não o tempo que fez."},
    {"cod": "FOOD", "nome": "Alimentação e bebidas (total)", "cor": "#0E7433", "larg": 2.8,
     "grupo": "alimentacao", "porque": "O agregado que o debate público chama «alimentação»."},
    # --- enquadramento: não são alimentação, servem de referência ---
    {"cod": "CP00", "nome": "Todos os produtos", "cor": "#171715", "larg": 2.2,
     "grupo": "enquadramento", "porque": "A inflação geral. Responde a «como pode a inflação "
                                         "ser baixa e o cabaz subir?»"},
    {"cod": "TOT_X_NRG_FOOD", "nome": "Subjacente (sem energia nem alimentos)",
     "cor": "#2B5683", "larg": 1.8, "grupo": "enquadramento",
     "porque": "A medida que os bancos centrais seguem. Distingue pressão estrutural "
               "de choque temporário."},
]

COD_AGREGADOS = [a["cod"] for a in AGREGADOS]

# --------------------------------------------------------------------------
# Países para comparação europeia
# --------------------------------------------------------------------------
PAISES = {
    "PT": "Portugal",
    "EU27_2020": "UE-27",
    "ES": "Espanha",
    "FR": "França",
    "IT": "Itália",
    "DE": "Alemanha",
    "EL": "Grécia",
    "IE": "Irlanda",
    "PL": "Polónia",
    "NL": "Países Baixos",
    "BE": "Bélgica",
    "AT": "Áustria",
}

PAISES_POR_DEFEITO = ["PT", "EU27_2020", "ES", "FR"]

# --------------------------------------------------------------------------
# Número de agregados familiares — divisor da despesa nacional
# --------------------------------------------------------------------------
# Valor de referência oficial. Os Censos são a fonte autoritativa para o número
# de agregados: é um apuramento exaustivo, não uma estimativa por amostragem.
AGREGADOS_CENSOS = 4_149_096
AGREGADOS_FONTE = "INE, Censos 2021 (resultados definitivos)"
AGREGADOS_ANO = 2021

# Dimensão média do agregado — apenas usada se o Eurostat não responder.
# O valor corrente é obtido de ilc_lvph01 (EU-SILC) em cada sessão: está em
# queda em toda a Europa, pelo que uma constante desatualiza-se depressa.
DIMENSAO_RECUO = 2.4
DIMENSAO_RECUO_FONTE = "Eurostat, ilc_lvph01 (EU-SILC), 2025"

# --------------------------------------------------------------------------
# Âncoras da despesa alimentar — duas bases oficiais que não coincidem
# --------------------------------------------------------------------------
# As Contas Nacionais medem o consumo *no território*, incluindo o de não
# residentes, e são obtidas em direto do Eurostat. O IDF mede a despesa
# declarada pelos agregados *residentes*.
#
# Para 2022 as duas divergem por um fator de 2,3 na alimentação — muito acima
# do desvio geral de 1,7 entre inquérito e Contas Nacionais. A taxa de
# cobertura portuguesa da alimentação (44 %) fica abaixo do mínimo europeu
# (58 %), e não existe exercício nacional de conciliação que permita arbitrar.
#
# Nenhuma das duas é «a» resposta: as Contas Nacionais sobrestimam (conceito
# interno, possível sobre-atribuição), o inquérito subestima (sub-reporte).
# A aplicação apresenta por isso o intervalo entre ambas e deixa o utilizador
# escolher a base de trabalho. Ver docs/2026-08-07_levantamento_lacunas.md, §2.10.
IDF_ALIMENTAR_ANUAL = 2872.0          # € por agregado e por ano, COICOP 01.1
IDF_ANO_BASE = 2023                   # o IDF 2022/2023 é indexado a partir de 2023
IDF_FONTE = "INE, IDF 2022/2023 (quadro Q.2.11.a)"

BASES_ANCORA = {
    "idf": {
        "nome": "IDF 2022/2023",
        "fonte": IDF_FONTE,
        "porque": "Medição direta da despesa dos agregados residentes. Subestima, "
                  "porque os inquéritos às despesas sub-reportam sistematicamente.",
    },
    "contas": {
        "nome": "Contas Nacionais",
        "fonte": "Eurostat, nama_10_co3_p3 (Contas Nacionais, compiladas pelo INE)",
        "porque": "Agregado macroeconómico dividido pelo número de agregados. "
                  "Sobrestima, porque mede o consumo no território e inclui não residentes.",
    },
}
BASE_POR_DEFEITO = "idf"

# --------------------------------------------------------------------------
# IDF 2022/2023 por quintil de rendimento — a base estrutural
# --------------------------------------------------------------------------
# Divisão de trabalho entre as duas fontes de ponderação, decidida em 08.08.2026:
#
#   IDF   → estrutura e distribuição (quem gasta o quê, e que parte do orçamento)
#   IHPC  → movimento dos preços (como variou cada classe)
#
# A razão não é de conveniência. O Documento Metodológico do IPC (INE, 2023) é
# explícito: «O IHPC inclui a despesa realizada pelos não residentes ("turistas")
# no território económico e exclui a despesa dos residentes no exterior,
# originando uma estrutura de ponderação diferente da utilizada no IPC.» Os
# ponderadores do IHPC — os únicos que o Eurostat difunde — medem, por
# construção, um universo que inclui turistas. É a mesma contaminação que levou
# a app a abandonar as Contas Nacionais como âncora única.
#
# O INE publica ponderadores do IPC (conceito nacional, sem turistas), mas apenas
# em ine.pt. O IDF é, entre as fontes abertas, a única via para uma estrutura de
# consumo de agregados residentes — e a única que desce ao quintil.
#
# Fonte: INE, IDF 2022/2023, quadros Q.2.11.a (euros/ano) e Q.2.11.b (estrutura %).
# Quintis de rendimento *equivalente*. Atualização manual a cada vaga do IDF.
IDF_QUINTIS = {
    "total": "Média nacional",
    "q1": "1.º quintil",
    "q2": "2.º quintil",
    "q3": "3.º quintil",
    "q4": "4.º quintil",
    "q5": "5.º quintil",
}

# Despesa total anual do agregado (todas as rubricas), € por ano
IDF_DESPESA_TOTAL = {
    "total": 23_900, "q1": 16_294, "q2": 18_269,
    "q3": 22_188, "q4": 26_188, "q5": 34_994,
}

# Despesa alimentar anual (COICOP 01.1), € por ano
IDF_ALIMENTAR_QUINTIL = {
    "total": 2872, "q1": 2412, "q2": 2573,
    "q3": 3022, "q4": 3139, "q5": 3192,
}

# Peso da alimentação no orçamento total (Q.2.11.b), %
IDF_PESO_ALIMENTAR = {
    "total": 12.0, "q1": 14.8, "q2": 14.1,
    "q3": 13.6, "q4": 12.0, "q5": 9.1,
}

# Despesa anual por classe COICOP e quintil, € por ano. A soma de cada coluna
# reproduz IDF_ALIMENTAR_QUINTIL a menos de arredondamento do próprio quadro.
IDF_CLASSES_QUINTIL = {
    "CP0111": {"total": 420, "q1": 380, "q2": 404, "q3": 447, "q4": 443, "q5": 426},
    "CP0112": {"total": 670, "q1": 575, "q2": 633, "q3": 767, "q4": 740, "q5": 650},
    "CP0113": {"total": 403, "q1": 313, "q2": 342, "q3": 415, "q4": 463, "q5": 476},
    "CP0114": {"total": 369, "q1": 312, "q2": 324, "q3": 376, "q4": 405, "q5": 420},
    "CP0115": {"total": 119, "q1": 102, "q2": 119, "q3": 131, "q4": 138, "q5": 108},
    "CP0116": {"total": 299, "q1": 231, "q2": 246, "q3": 275, "q4": 320, "q5": 407},
    "CP0117": {"total": 324, "q1": 294, "q2": 290, "q3": 336, "q4": 344, "q5": 354},
    "CP0118": {"total": 119, "q1": 75,  "q2": 87,  "q3": 136, "q4": 121, "q5": 169},
    "CP0119": {"total": 149, "q1": 130, "q2": 127, "q3": 139, "q4": 165, "q5": 181},
}

# --------------------------------------------------------------------------
# Teste empírico das escalas de equivalência na alimentação
# --------------------------------------------------------------------------
# A aplicação sempre declarou que a escala OCDE modificada subestima o custo
# alimentar de agregados maiores — mas como ressalva qualitativa. O IDF
# 2022/2023 permite medi-la.
#
# Método: restringir a agregados **sem crianças dependentes**, onde a escala é
# mais limpa, e comparar o rácio de despesa observado entre «2 ou mais adultos»
# e «1 adulto» com o rácio que cada escala prevê para a mesma composição.
#
# O grupo «2 ou +» reparte-se por resíduo, a partir das contagens do Q.1.3, em
# 72 % com dois adultos e 28 % com três ou mais. Os 3+ têm 2,144 adultos
# equivalentes na escala OCDE modificada, o que implica 3,288 adultos em média.
#
# O controlo é o que torna o teste convincente: repetindo a conta para a despesa
# **total** — para a qual as escalas foram desenhadas — o desvio inverte-se.
# Ou seja, o problema não é da escala em geral: é da alimentação em particular,
# onde as economias de escala são mais fracas do que na habitação.
ESCALAS_TESTE_FONTE = "INE, IDF 2022/2023, quadros Q.1.3, Q.2.6.a e Q.2.8"

# Composição do grupo «2 ou mais adultos»: (n.º de adultos, fração do grupo)
ESCALAS_TESTE_COMPOSICAO = [(2.0, 0.72), (3.288, 0.28)]

# Rácios observados de despesa entre «2 ou +» e «1 adulto», sem crianças
ESCALAS_TESTE_RACIO = {
    "alimentar": 1.854,   # 3 066 € / 1 654 € por ano, COICOP 01.1
    "total": 1.498,       # a mesma conta sobre a despesa total
}

# As duas restrições disponíveis são ligeiramente inconsistentes entre si
# (adultos equivalentes médios reconstruídos: 1,435 contra 1,407 publicados),
# pelo que a subestimação fica entre +10 % e +13 %. Robusta no sinal e na ordem
# de grandeza, não no algarismo.
ESCALAS_TESTE_INTERVALO = (10, 13)

# --------------------------------------------------------------------------
# Metadados institucionais
# --------------------------------------------------------------------------
ORGANISMO = "Secretaria-Geral do Governo"
UNIDADE = "DSSD · Unidade de Pesquisa e Estatísticas"
RODAPE = (
    "Ferramenta de trabalho interno — não constitui posição oficial da "
    "Secretaria-Geral do Governo. Os dados são obtidos em direto do Eurostat; "
    "o valor de referência do cabaz e as taxas de IVA são parâmetros do utilizador."
)

MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun",
            "jul", "ago", "set", "out", "nov", "dez"]


def mes_pt(periodo: str) -> str:
    """Converte '2026-06' em 'jun/26'."""
    try:
        ano, mes = str(periodo).split("-")[:2]
        return f"{MESES_PT[int(mes) - 1]}/{ano[2:]}"
    except (ValueError, IndexError):
        return str(periodo)


def euro(valor, casas: int = 2) -> str:
    """Formata em euros com convenção portuguesa (vírgula decimal)."""
    if valor is None:
        return "—"
    txt = f"{valor:,.{casas}f}".replace(",", "\u00a0").replace(".", ",")
    return f"{txt} €"


def percentagem(valor, casas: int = 1, sinal: bool = True) -> str:
    if valor is None:
        return "—"
    pre = "+" if (sinal and valor > 0) else ""
    return f"{pre}{valor:.{casas}f}".replace(".", ",") + " %"
