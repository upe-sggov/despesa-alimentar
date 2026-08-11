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
# Classes de produtos alimentares (COICOP 01.1, versão 2018)
# --------------------------------------------------------------------------
# `nome` é a forma curta usada nos cartões e nos gráficos, onde não cabe a
# designação completa; `oficial` é a designação **do INE**, transcrita do anexo
# «Classificação do Consumo Individual por Objetivo (COICOP, versão 2018)» do
# relatório do IDF 2022/2023. As formas curtas são as que o levantamento de
# 07.08.2026 já usava, §2.1 — não são invenção desta aplicação.
#
# Até 11.08.2026 os nomes eram os da **ECOICOP versão 1** («Pão e cereais»,
# «Carne», «Fruta», «Legumes e hortícolas», «Açúcar e doces», «Outros
# alimentos»). Os códigos CP0111–CP0119 sobreviveram à revisão da nomenclatura,
# mas o conteúdo das classes mudou, e os rótulos deixaram de o descrever
# (auditoria de 11.08.2026, E2).
#
# `iva` é a taxa **predominante** predefinida, editável na aplicação. O Código
# do IVA classifica por produto — Listas I (6 %) e II (13 %) —, não por classe
# COICOP. **Nenhuma das nove classes é homogénea**: ver `IVA_MAPA`, que assinala
# o que dentro de cada uma segue taxa diferente da predefinida.
CLASSES_FONTE = ("INE, Inquérito às Despesas das Famílias 2022/2023, anexo — "
                 "Classificação do Consumo Individual por Objetivo "
                 "(COICOP, versão 2018)")

CLASSES = [
    {"cod": "CP0111", "nome": "Cereais e derivados", "emoji": "🍞", "cor": "#C98B3A", "iva": 6,
     "oficial": "Cereais e produtos à base de cereais"},
    {"cod": "CP0112", "nome": "Carne", "emoji": "🥩", "cor": "#C0392B", "iva": 6,
     "oficial": "Animais vivos, carne e outras partes de animais terrestres abatidos"},
    {"cod": "CP0113", "nome": "Peixe e produtos do mar", "emoji": "🐟", "cor": "#2980B9", "iva": 6,
     "oficial": "Peixe e outros produtos alimentares do mar"},
    {"cod": "CP0114", "nome": "Leite, lácteos e ovos", "emoji": "🥛", "cor": "#8E9AAF", "iva": 6,
     "oficial": "Leite, outros produtos lácteos e ovos"},
    {"cod": "CP0115", "nome": "Óleos e gorduras", "emoji": "🫒", "cor": "#B8A02E", "iva": 6,
     "oficial": "Óleos e gorduras"},
    {"cod": "CP0116", "nome": "Fruta e frutos de casca rija", "emoji": "🍎", "cor": "#D35400", "iva": 6,
     "oficial": "Fruta e frutos de casca rija"},
    {"cod": "CP0117", "nome": "Hortícolas, tubérculos e leguminosas", "emoji": "🥦", "cor": "#0E7433", "iva": 6,
     "oficial": "Produtos hortícolas, tubérculos, bananas-pão, bananas para "
                "culinária e leguminosas"},
    {"cod": "CP0118", "nome": "Açúcar, confeitaria e sobremesas", "emoji": "🍬", "cor": "#A0568F", "iva": 23,
     "oficial": "Açúcar, confeitaria e sobremesas"},
    {"cod": "CP0119", "nome": "Pré-preparados e outros", "emoji": "🧺", "cor": "#6B7280", "iva": 23,
     "oficial": "Alimentos pré-preparados e outros produtos alimentares n.e."},
]

CODIGOS = [c["cod"] for c in CLASSES]
POR_CODIGO = {c["cod"]: c for c in CLASSES}

# --------------------------------------------------------------------------
# Correspondência COICOP ↔ Código do IVA
# --------------------------------------------------------------------------
# Levantamento feito sobre o texto das Listas I (taxa reduzida, 6 %) e II (taxa
# intermédia, 13 %) do Código do IVA. Fecha a lacuna D2 da auditoria de
# 10.08.2026: até aqui a aplicação limitava-se a dizer que a correspondência era
# «aproximada», sem dizer em quê.
#
# A conclusão é que **a taxa predefinida é a predominante, nunca a única**.
# O simulador continua a aplicar uma taxa por classe — é o que a decomposição
# permite, porque não há despesa aberta ao nível do produto — mas quem o usa
# tem de saber o que fica de fora. As parcelas não são quantificáveis com dados
# abertos: nenhuma fonte pública reparte a despesa da classe por taxa legal.
#
# `taxas` enumera **todas** as taxas presentes na classe, com o que cai em cada
# uma. A predefinida é assinalada pela aplicação a partir de `CLASSES`, e não
# repetida aqui — repeti-la abria a porta a que as duas divergissem em silêncio.
IVA_MAPA_FONTE = ("Código do IVA, Lista I (taxa reduzida) e Lista II "
                  "(taxa intermédia); classes da COICOP versão 2018 conforme o "
                  "anexo do IDF 2022/2023 do INE")

# O levantamento foi **refeito a 11.08.2026 contra as subclasses da COICOP
# versão 2018**, e não contra as da ECOICOP versão 1 sobre as quais tinha sido
# construído. As verbas das Listas I e II não mudaram — mudou aquilo que cada
# classe contém, e portanto o que fica dentro e fora de cada verba. Onde a
# nomenclatura nova dá subclasse própria a um produto que antes estava diluído,
# isso está assinalado: é o que torna a divergência verificável em vez de
# afirmada.
IVA_MAPA = {
    "CP0111": {
        "taxas": [
            (6, "Cereais, arroz, farinhas, massas não recheadas, pão; seitan, "
                "tofu, tempeh e soja texturizada (Lista I, 1.1) — cobre as "
                "subclasses 01.1.1.1 a 01.1.1.3 e 01.1.1.5"),
            (13, "Flocos prensados simples de cereais e leguminosas sem adição "
                 "de açúcar (Lista II, 1.12) — parte dos cereais para "
                 "pequeno-almoço, 01.1.1.4"),
            (23, "Bolos, bolachas, biscoitos e pastelaria; massas recheadas, "
                 "expressamente excluídas da Lista I"),
        ],
        "nota": "A subclasse 01.1.1.3 chama-se «Pão e produtos de padaria» e "
                "atravessa a fronteira das verbas: o pão está na Lista I, a "
                "pastelaria não.",
    },
    "CP0112": {
        "taxas": [
            (6, "Carnes e miudezas comestíveis, frescas ou congeladas, das "
                "espécies bovina, suína, ovina, caprina, equídea, aves de "
                "capoeira, coelho e caça (Lista I, 1.2) — subclasses 01.1.2.2 "
                "e 01.1.2.4"),
            (13, "Alheiras (Lista II, 1.3.3)"),
            (23, "Carne seca, salgada, em salmoura ou fumada (01.1.2.3) e "
                 "preparações de animais abatidos (01.1.2.5) — a restante "
                 "charcutaria e enchidos, que a Lista I não abrange"),
        ],
        "nota": "A classe passou a incluir **animais terrestres vivos** "
                "(01.1.2.1), que não são carne e cuja verba não foi "
                "confirmada. É residual na despesa das famílias, mas fica "
                "por classificar.",
    },
    "CP0113": {
        "taxas": [
            (6, "Peixe fresco, refrigerado, congelado, seco ou salgado; "
                "moluscos; conservas de peixe e molusco com teor superior a "
                "50 % (Lista I, 1.3) — subclasses 01.1.3.1 a 01.1.3.3"),
            (13, "Conservas de moluscos (Lista II, 1.2.1)"),
            (23, "**Crustáceos** — camarão, lagosta, sapateira: a Lista I "
                 "refere «peixes e moluscos», não crustáceos. Também peixe "
                 "fumado, espadarte, esturjão e salmão secos, salgados ou em "
                 "conserva, caviar e pastas de atum, cavala e sardinha"),
        ],
        "nota": "A nomenclatura nova dá **três subclasses próprias ao marisco** "
                "(01.1.3.4 a 01.1.3.6), que na versão anterior estavam "
                "diluídas. A divergência com a Lista I passou a ser visível na "
                "própria estrutura da classe.",
    },
    "CP0114": {
        "taxas": [
            (6, "Leite e lacticínios, queijos, iogurtes, ovos; bebidas e "
                "iogurtes de base vegetal e substitutos de queijo à base de "
                "frutos secos, cereais, frutas ou hortícolas (Lista I, 1.4) — "
                "cobre também o «leite não animal», 01.1.4.4"),
            (23, "**Sobremesas e bebidas à base de leite** (01.1.4.7), que a "
                 "Lista I não enumera"),
        ],
        "nota": "As sobremesas lácteas passaram a ter subclasse própria "
                "(01.1.4.7); antes eram um resíduo não identificável.",
    },
    "CP0115": {
        "taxas": [
            (6, "Azeite; banha e outras gorduras de porco (Lista I, 1.5). "
                "Manteiga, margarina e creme vegetal para barrar "
                "(Lista I, 1.4.3) — subclasses 01.1.5.2 e 01.1.5.3"),
            (13, "**Óleos vegetais diretamente comestíveis e suas misturas** — "
                 "os óleos alimentares correntes (Lista II, 1.5.3)"),
        ],
        "nota": "Continua a ser a divergência mais material das nove classes, "
                "e a nomenclatura nova torna-a quase exata: «Óleos vegetais» "
                "é agora a **primeira subclasse** (01.1.5.1) e corresponde "
                "praticamente um a um à verba da Lista II, numa classe "
                "predefinida a 6 %.",
    },
    "CP0116": {
        "taxas": [
            (6, "Frutas no estado natural ou desidratadas, castanhas e frutos "
                "vermelhos congelados (Lista I, 1.6.4) — subclasses 01.1.6.1 "
                "a 01.1.6.5 e 01.1.6.7"),
            (23, "Fruta congelada que não seja frutos vermelhos (01.1.6.6); "
                 "fruta em calda, conserva e outras preparações (01.1.6.9); "
                 "frutos de casca rija que não sejam castanhas (01.1.6.8)"),
        ],
        "nota": "A classe passou a nomear os **frutos de casca rija** "
                "(01.1.6.8). A Lista I refere as castanhas nominalmente, pelo "
                "que amêndoa, noz e avelã ficam de fora da taxa reduzida.",
    },
    "CP0117": {
        "taxas": [
            (6, "Legumes e produtos hortícolas frescos, refrigerados, secos, "
                "desidratados ou congelados, ainda que previamente cozidos; "
                "leguminosas secas; algas (Lista I, 1.6) — subclasses 01.1.7.1 "
                "a 01.1.7.8"),
            (23, "Hortícolas transformados — batata frita de pacote e "
                 "preparados similares (01.1.7.9)"),
        ],
        "nota": "A classe passou a incluir explicitamente **tubérculos, "
                "bananas-pão, bananas para culinária e leguminosas**; a Lista I "
                "cobre-os enquanto frescos, secos ou congelados.",
    },
    "CP0118": {
        "taxas": [
            (6, "Mel de abelhas e mel de cana tradicional (Lista I, 1.8)"),
            (23, "Açúcar de cana e beterraba e sucedâneos (01.1.8.1 e "
                 "01.1.8.2) — a verba 1.10 da Lista I foi **revogada**; "
                 "chocolate e cacau (01.1.8.5); gelados (01.1.8.6); doces, "
                 "geleias e marmeladas; restante confeitaria"),
        ],
        "nota": "Predefinida a 23 %: aqui a exceção é o mel. E a nomenclatura "
                "nova agrega-o numa subclasse com doces, geleias e marmeladas "
                "(01.1.8.3), o que torna a parcela a 6 % **menos separável** do "
                "que era.",
    },
    "CP0119": {
        "taxas": [
            (6, "Alimentos para bebés e crianças de pouca idade (01.1.9.2), "
                "fins medicinais específicos e substitutos integrais da dieta "
                "(Lista I, 1.14); sal (Lista I, 1.9); produtos dietéticos para "
                "nutrição entérica e produtos sem glúten para doentes celíacos "
                "(Lista I, 1.12)"),
            (13, "Refeições prontas a consumir, **em pronto a comer e levar ou "
                 "com entrega ao domicílio** (Lista II, 1.8)"),
            (23, "Condimentos e molhos (01.1.9.3), especiarias, ervas "
                 "aromáticas e sementes para culinária (01.1.9.4), caldos, "
                 "sopas e preparados vários (01.1.9.9)"),
        ],
        "nota": "A classe passou a chamar-se «Alimentos pré-preparados e "
                "outros», mas **a predefinição a 23 % mantém-se**: a subclasse "
                "01.1.9.1 é pré-preparado de retalho, e a verba 1.8 da Lista II "
                "cobre o pronto a comer e levar e a entrega ao domicílio, que "
                "na COICOP caem no grupo 11.1 (restauração) e não aqui. "
                "Continua a ser a classe mais heterogénea das nove.",
    },
}

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
    # `TOTAL` e não `CP00`: na ECOICOP versão 2 o agregado de todos os produtos
    # mudou de código. `CP00` devolve HTTP 400 em `prc_hicp_minr` — e a via de
    # reserva respondia com uma fatia arbitrária em vez de erro
    # (auditoria de 11.08.2026, E1).
    {"cod": "TOTAL", "nome": "Todos os produtos", "cor": "#171715", "larg": 2.2,
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
IDF_FONTE = "INE, IDF 2022/2023 (quadro Q.2.11.a)"

# Período de referência do IDF 2022/2023, confirmado no documento metodológico
# do INE (Metainformação IDF, V.6.1.1): «O período de recolha decorrerá entre
# 3 de fevereiro de 2022 e 5 de fevereiro de 2023, correspondendo a 26
# quinzenas. Os dados de cada agregado são recolhidos ao longo de 14 dias».
#
# Duas consequências, e ambas importam:
#
# 1. A recolha é **uniforme ao longo de doze meses** — 26 quinzenas seguidas —,
#    não um instantâneo. O valor publicado é uma média desse período.
# 2. O INE **não corrige os valores para uma data comum**: V.7.4, «Ajustamentos
#    dos dados: Não aplicável». Ficam aos preços do momento em que cada
#    agregado foi inquirido.
#
# Logo, a base de indexação não é um ano civil — é a janela de recolha. A
# aplicação usava `IDF_ANO_BASE = 2023`, um pressuposto que ninguém tinha
# confirmado e que subestimava o valor atual em 21,05 €/mês, 8,3 %
# (auditoria de 10.08.2026, D1).
#
# Fevereiro de 2022 é o primeiro mês inteiro de recolha e janeiro de 2023 o
# último: doze meses, que é exatamente a duração das 26 quinzenas.
IDF_JANELA_RECOLHA = ("2022-02", "2023-01")
IDF_JANELA_FONTE = ("INE, Metainformação do IDF 2022/2023, V.6.1.1 (período de "
                    "recolha) e V.7.4 (sem ajustamento dos dados)")

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
# Acessibilidade alimentar — três limiares que medem coisas diferentes
# --------------------------------------------------------------------------
# «Acessibilidade alimentar» não é uma grandeza única. Consoante o limiar,
# Portugal parece estar muito bem ou bastante mal, com dados oficiais em ambos
# os casos. Daí a regra de apresentação: os três aparecem **sempre juntos**.
#
#   1,9 %   privação severa — não pagar uma refeição com carne ou peixe de dois
#           em dois dias. Limiar muito baixo: mede quase fome. Em mínimo de série.
#   14,4 %  não conseguir pagar uma dieta nutricionalmente adequada ao menor
#           custo. É o nível intermédio, e é onde está o problema real.
#   14,8 %  peso da alimentação no orçamento do 1.º quintil — não é privação,
#           é exposição. Vem de IDF_PESO_ALIMENTAR, acima.
#
# Apresentar só o de 1,9 % dá uma leitura indevidamente tranquilizadora: sugere
# um problema de 2 % da população, quando por um limiar nutricionalmente
# defensável são 14 %.
#
# O SOFI é publicado em PDF, não em API — os valores abaixo são transcritos dos
# anexos A1.5 e A1.6 e têm de ser atualizados à mão a cada edição.
# --------------------------------------------------------------------------
# Prazos de validade das fontes de atualização manual
# --------------------------------------------------------------------------
# Nem o SOFI nem o Observatório têm API: se ninguém os atualizar, a aplicação
# continua a apresentá-los sem nunca dar erro (auditoria de 10.08.2026, D4).
# Estes limites definem a partir de quando a interface passa a avisar.
#
# O Observatório publica períodos de quatro semanas (28 dias). Sessenta dias
# tolera um período em atraso e apanha o segundo.
LIMITE_DIAS_OBSERVATORIO = 60

# O SOFI é anual, publicado a meio do ano seguinte ao de referência. Dois anos
# de distância do último ano da série significa que houve uma edição por
# incorporar.
LIMITE_ANOS_SOFI = 2

# --------------------------------------------------------------------------
# Prazos de validade das séries obtidas por API
# --------------------------------------------------------------------------
# A auditoria de 10.08.2026 (D4) criou a verificação de frescura e apontou-a ao
# SOFI e ao Observatório, com o argumento de que são as fontes **sem** API. A
# conclusão implícita — que as séries com API não têm esse problema, porque a
# rede avisaria — estava errada, e custou sete meses de dados desatualizados:
# uma série arquivada responde com HTTP 200 e simplesmente deixa de avançar
# (auditoria de 11.08.2026, E1 e E3).
#
# O limite de cada série é o seu **desfasamento normal de publicação mais um
# ciclo**. Um prazo uniforme não serviria: acusaria de velhas as fontes que são
# lentas por construção — as Contas Nacionais têm dois anos de desfasamento e
# está certo que tenham. O que se quer apanhar é a série que **parou**, não a
# série que é lenta.
#
# Em dias, para que o cálculo não dependa da aritmética de calendário.
LIMITES_FRESCURA = {
    "indice": (60, "O índice completo, com todas as classes, sai por volta do "
                   "dia 17 do mês seguinte ao de referência. Sessenta dias "
                   "tolera um mês em atraso e apanha o segundo."),
    "variacoes": (60, "Mesma publicação do índice — sai no mesmo momento."),
    "ponderadores": (450, "Anuais, publicados com os dados de janeiro, em "
                          "fevereiro. Quinze meses tolera uma vaga em atraso."),
    "contas_nacionais": (800, "As Contas Nacionais por finalidade saem com cerca "
                              "de ano e meio de desfasamento. Foi este prazo que "
                              "apanhou o nama_10_co3_p3 parado em 2022, quando "
                              "todos os outros conjuntos anuais já estavam em 2025."),
    "agregados": (800, "Inquérito ao Emprego, anual, publicado no ano seguinte."),
    "dimensao": (800, "EU-SILC, anual, com cerca de um ano de desfasamento."),
    "rendimento": (800, "EU-SILC, anual, com cerca de um ano de desfasamento."),
    "privacao": (800, "EU-SILC, anual, com cerca de um ano de desfasamento."),
    "salario_minimo": (260, "Semestral — janeiro e julho. Oito meses e meio "
                            "tolera um semestre em atraso."),
    "salario_medio": (800, "Contas Nacionais anuais por ramo de atividade, "
                           "publicadas no ano seguinte."),
    "nivel_precos": (800, "Paridades de poder de compra, publicadas em junho do "
                          "ano seguinte ao de referência."),
}

SOFI_FONTE = ("FAO/FIDA/UNICEF/PAM/OMS, The State of Food Security and Nutrition "
              "in the World 2026, anexos A1.5 e A1.6")
SOFI_EDICAO = 2026

# Custo de uma dieta saudável, PPP$ por pessoa e por dia
SOFI_CUSTO = {
    "Portugal":      {2017: 2.64, 2019: 2.85, 2021: 2.99, 2022: 3.57, 2023: 4.10, 2024: 4.17, 2025: 4.30},
    "Europa":        {2017: 2.51, 2019: 2.72, 2021: 2.91, 2022: 3.33, 2023: 3.76, 2024: 3.84, 2025: 3.97},
    "Europa do Sul": {2017: 2.79, 2019: 3.01, 2021: 3.20, 2022: 3.73, 2023: 4.36, 2024: 4.47, 2025: 4.62},
    "Espanha":       {2017: 2.53, 2019: 2.70, 2021: 2.94, 2022: 3.45, 2023: 4.13, 2024: 4.22, 2025: 4.33},
}

# Incapacidade de pagar uma dieta saudável, % da população
SOFI_INCAPACIDADE = {
    "Portugal": {2017: 22.1, 2019: 15.1, 2020: 16.1, 2021: 15.7,
                 2022: 16.9, 2023: 15.0, 2024: 14.8, 2025: 14.4},
    "Espanha":  {2017: 12.6, 2019: 11.3, 2020: 11.7, 2021: 10.2,
                 2022: 9.5,  2023: 9.9,  2024: 9.6,  2025: 9.3},
}

# Pessoas, em milhões — Portugal
SOFI_MILHOES = {2017: 2.3, 2019: 1.6, 2020: 1.7, 2021: 1.6,
                2022: 1.8, 2023: 1.6, 2024: 1.5, 2025: 1.5}

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


# As três funções seguintes existem para que nenhuma frase volte a ser
# formatada com `.replace(",", " ")` aplicado à *frase inteira*. Esse padrão
# funcionava só enquanto não houvesse outra vírgula no texto: qualquer
# alteração de redação partia a formatação em silêncio, e já partiu neste
# projeto mais de uma vez (auditoria de 10.08.2026, C5). A regra é formatar o
# **número**, nunca o texto à volta dele.
def numero(valor, casas: int = 0) -> str:
    """Inteiro ou decimal com separador de milhares fino e vírgula decimal."""
    if valor is None:
        return "—"
    return f"{valor:,.{casas}f}".replace(",", " ").replace(".", ",")


def milhoes(valor, casas: int = 1, sufixo: str = " M€") -> str:
    """Valor já expresso em milhões."""
    if valor is None:
        return "—"
    return numero(valor, casas) + sufixo


def pontos(valor, casas: int = 2, sinal: bool = True, sufixo: str = " p.p.") -> str:
    """Pontos percentuais ou pontos de índice."""
    if valor is None:
        return "—"
    pre = "+" if (sinal and valor > 0) else ""
    return f"{pre}{valor:.{casas}f}".replace(".", ",") + sufixo
