"""
Configuração da aplicação, classes de produto, países e identidade gráfica.

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
# “Classificação do Consumo Individual por Objetivo (COICOP, versão 2018)” do
# relatório do IDF 2022/2023. As formas curtas são as que o levantamento de
# 07.08.2026 já usava, §2.1, não são invenção desta aplicação.
#
# Até 11.08.2026 os nomes eram os da **ECOICOP versão 1** (“Pão e cereais”,
# “Carne”, “Fruta”, “Legumes e hortícolas”, “Açúcar e doces”, “Outros
# alimentos”). Os códigos CP0111–CP0119 sobreviveram à revisão da nomenclatura,
# mas o conteúdo das classes mudou, e os rótulos deixaram de o descrever
# (auditoria de 11.08.2026, E2).
#
# `iva` é a taxa **predominante** predefinida, editável na aplicação. O Código
# do IVA classifica por produto (Listas I (6%) e II (13%)), não por classe
# COICOP. **Nenhuma das nove classes é homogénea**: ver `IVA_MAPA`, que assinala
# o que dentro de cada uma segue taxa diferente da predefinida.
CLASSES_FONTE = ("INE, Inquérito às Despesas das Famílias 2022/2023, anexo, "
                 "Classificação do Consumo Individual por Objetivo "
                 "(COICOP, versão 2018)")

# A `cor` e a **cor de apresentação** da classe, e e a unica que existe: ate
# 31.08.2026 havia duas paletas, esta e uma segunda no `app.py`, que a
# substituia so no desenho. A daqui nunca chegava ao ecra, e as duas divergiam
# em sete das nove classes. Ficou a contida, que e a que estava a ser desenhada:
# tons alinhados com a identidade, e nenhum deles o vermelho de alerta, que numa
# paleta categorica sinalizaria um problema onde so ha uma categoria (decisao da
# Ines, 31.08.2026).
#
# O campo `emoji` saiu na mesma passagem. Os emojis tinham sido retirados da
# interface ha muito, mas o campo continuava a ser arrastado pelo `calculos.py`
# para dentro dos DataFrames, a um passo de aparecer numa exportacao. Quem
# identifica a classe agora e o `icone`, que e geometria e nao caractere.
CLASSES = [
    {"cod": "CP0111", "nome": "Cereais e derivados", "cor": "#2B5683", "iva": 6,
     "oficial": "Cereais e produtos à base de cereais"},
    {"cod": "CP0112", "nome": "Carne", "cor": "#A8574B", "iva": 6,
     "oficial": "Animais vivos, carne e outras partes de animais terrestres abatidos"},
    {"cod": "CP0113", "nome": "Peixe e produtos do mar", "cor": "#4E86B8", "iva": 6,
     "oficial": "Peixe e outros produtos alimentares do mar"},
    {"cod": "CP0114", "nome": "Leite, lácteos e ovos", "cor": "#8E9AAF", "iva": 6,
     "oficial": "Leite, outros produtos lácteos e ovos"},
    {"cod": "CP0115", "nome": "Óleos e gorduras", "cor": "#BE9C54", "iva": 6,
     "oficial": "Óleos e gorduras"},
    {"cod": "CP0116", "nome": "Fruta e frutos de casca rija", "cor": "#C97B3C", "iva": 6,
     "oficial": "Fruta e frutos de casca rija"},
    {"cod": "CP0117", "nome": "Hortícolas, tubérculos e leguminosas", "cor": "#0E7433", "iva": 6,
     "oficial": "Produtos hortícolas, tubérculos, bananas-pão, bananas para "
                "culinária e leguminosas"},
    {"cod": "CP0118", "nome": "Açúcar, confeitaria e sobremesas", "cor": "#7A5E8A", "iva": 23,
     "oficial": "Açúcar, confeitaria e sobremesas"},
    {"cod": "CP0119", "nome": "Pré-preparados e outros", "cor": "#9AA5AE", "iva": 23,
     "oficial": "Alimentos pré-preparados e outros produtos alimentares n.e."},
]

CODIGOS = [c["cod"] for c in CLASSES]
POR_CODIGO = {c["cod"]: c for c in CLASSES}

# --------------------------------------------------------------------------
# Iconografia das categorias
# --------------------------------------------------------------------------
# Fonte unica dos simbolos. Nao ha biblioteca externa nem caracteres: cada icone
# e o atributo `d` de um `<path>` SVG, desenhado numa grelha de 24x24, so com
# tracado e sem preenchimento. O `app.py` monta o SVG a volta destes caminhos e
# aplica-lhes a cor da classe; a geometria vive aqui para que grupos e produtos
# tenham um sitio unico onde mudar.
#
# Regras do desenho, para quem acrescentar um simbolo: poucas linhas, formas
# reconheciveis a 14 pixeis de altura, nenhum detalhe que so se veja em grande,
# e a mesma espessura de traco em todos. Um ponto desenha-se com um segmento de
# comprimento quase nulo (`h.01`), que a terminacao redonda transforma em disco.
ICONES_CLASSE = {
    # Espiga: haste e tres pares de graos.
    "CP0111": "M12 21V6M12 11 8 8M12 11 16 8M12 15.5 8 12.5M12 15.5 16 12.5"
              "M12 6.5 9 4.5M12 6.5 15 4.5",
    # Peca de carne com o osso ao centro.
    "CP0112": "M7.5 7.5h6.5a4.5 4.5 0 0 1 0 9H7.5a4.5 4.5 0 0 1 0-9z"
              "M10 12h.01",
    # Peixe: corpo em lente, cauda e olho.
    "CP0113": "M3.5 12c3.2-4.6 9.3-4.6 12.5 0-3.2 4.6-9.3 4.6-12.5 0z"
              "M16 12l4.5-3.2v6.4zM12.6 10.6h.01",
    # Garrafa de leite.
    "CP0114": "M10 3.8h4v2.6l2 3.2v9.9a.5.5 0 0 1-.5.5h-7a.5.5 0 0 1-.5-.5V9.6z",
    # Gota.
    "CP0115": "M12 3.5s5.5 6 5.5 9.5a5.5 5.5 0 0 1-11 0C6.5 9.5 12 3.5 12 3.5z",
    # Fruto redondo, com pe e folha.
    "CP0116": "M12 20.5a6 6 0 1 1 0-12 6 6 0 0 1 0 12zM12 8.5V5.4"
              "M12 6.4c1.6-2.1 4.3-1.8 4.3-1.8s.2 2.7-2.5 3.1",
    # Folha com nervura.
    "CP0117": "M5 19.5c-.8-8.5 5.5-14 14.5-15 1 9-4.5 15-14.5 15zM5 19.5 14.5 10",
    # Rebucado embrulhado.
    "CP0118": "M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM8 12 4 8.8v6.4zM16 12l4-3.2v6.4z",
    # Tabuleiro de refeicao preparada.
    "CP0119": "M4 10h16v9.5a.5.5 0 0 1-.5.5h-15a.5.5 0 0 1-.5-.5zM4 10l2.2-4h11.6L20 10",
}

# --------------------------------------------------------------------------
# Setores do Observatório: cada um herda a cor do seu grupo COICOP
# --------------------------------------------------------------------------
# O Observatorio publica 39 produtos repartidos por 20 setores, e o setor e que
# e a familia do produto: `carne-de-frango` traz quatro cortes, `trigo` traz tres
# farinhas. O simbolo esta ao nivel do setor e nao do produto, porque distinguir
# graficamente o Ovo M do Ovo L a 14 pixeis nao e sinalizacao, e ruido (decisao
# da Ines, 31.08.2026).
#
# `grupo` e o codigo COICOP de onde vem a cor. E daqui que sai a leitura que o
# separador precisa de tornar evidente: o icone diz o produto, a cor diz a
# familia.
SETORES_OBSERVATORIO = {
    "alface": {"nome": "Alface", "grupo": "CP0117",
               "icone": "M12 19.5a7 7 0 1 1 0-14 7 7 0 0 1 0 14z"
                        "M8.2 8.4c1.6 3 1.6 6.6 0 9.6M15.8 8.4c-1.6 3-1.6 6.6 0 9.6"},
    "arroz": {"nome": "Arroz", "grupo": "CP0111",
              "icone": "M7.5 10.5 9.5 7M12.5 13.5 14.5 10M9.5 17 11.5 13.5"},
    "azeite-3": {"nome": "Azeite", "grupo": "CP0115",
                 "icone": "M10.5 3.8h3v2.4l2.2 2.9v10.4a.5.5 0 0 1-.5.5H8.8"
                          "a.5.5 0 0 1-.5-.5V9.1z"},
    "banana": {"nome": "Banana", "grupo": "CP0116",
               "icone": "M6 7c0 6.6 5.1 11.2 11.7 11.2.5-1.5.5-3.1 0-4.2"
                        "C12.1 14 8.6 11 8.1 7z"},
    "batata": {"nome": "Batata", "grupo": "CP0117",
               "icone": "M12 18.6c-3.9 0-6.6-2.9-6.6-6.6S8.6 5.4 12.5 5.4"
                        "s6.6 2.9 6.6 6.6-3.2 6.6-7.1 6.6zM10.4 10.6h.01M13.9 13.4h.01"},
    "carne-de-frango": {"nome": "Carne de frango", "grupo": "CP0112",
                        "icone": "M16 4.5a4.5 4.5 0 0 1 0 9 4.5 4.5 0 0 1-3.6-1.8l-5 5"
                                 "M7.4 16.7l-1.7 1.7M9.1 18.4l-1.7 1.7"},
    "carne-de-porco": {"nome": "Carne de porco", "grupo": "CP0112",
                       "icone": "M6.5 8h7.5a4 4 0 0 1 0 8H6.5a4 4 0 0 1 0-8z"
                                "M10.5 12h.01"},
    "cebola": {"nome": "Cebola", "grupo": "CP0117",
               "icone": "M12 20c-3.6 0-6-2.4-6-5.5C6 10 9 7 12 4c3 3 6 6 6 10.5"
                        "0 3.1-2.4 5.5-6 5.5zM9.6 13.6c0 3 .8 5 2.4 6.4"
                        "M14.4 13.6c0 3-.8 5-2.4 6.4"},
    "cenoura": {"nome": "Cenoura", "grupo": "CP0117",
                "icone": "M11.8 20 6.8 10c2.2-1.4 5-1.4 7.2 0L11.8 20zM11.8 9.4V5.6"
                         "M11.8 6.6 15 4.4M11.8 6.6 8.6 4.4"},
    "couve": {"nome": "Couve", "grupo": "CP0117",
              "icone": "M12 20v-5M8.5 15h7M9 15a2.5 2.5 0 1 1 .6-4.9 3 3 0 0 1 5.4-.6"
                       "A2.5 2.5 0 1 1 15.6 15z"},
    "curgete": {"nome": "Curgete", "grupo": "CP0117",
                "icone": "M7 17.5c-1.5-1.5-1.5-4 1.5-7s5.5-3 7-1.5 1.5 4-1.5 7-5.5 3-7 1.5z"
                         "M15.5 8.5 17 5.5"},
    "laranja": {"nome": "Laranja", "grupo": "CP0116",
                "icone": "M12 19.5a6.5 6.5 0 1 1 0-13 6.5 6.5 0 0 1 0 13z"
                         "M12 6.5v13M5.5 13h13"},
    "laticinios-de-vaca": {"nome": "Lacticínios de vaca", "grupo": "CP0114",
                           "icone": "M10 3.8h4v2.6l2 3.2v9.9a.5.5 0 0 1-.5.5h-7"
                                    "a.5.5 0 0 1-.5-.5V9.6z"},
    "maca": {"nome": "Maçã", "grupo": "CP0116",
             "icone": "M12 20.5a6 6 0 1 1 0-12 6 6 0 0 1 0 12zM12 8.5V5.4"
                      "M12 6.4c1.6-2.1 4.3-1.8 4.3-1.8s.2 2.7-2.5 3.1"},
    "ovos-de-galinha": {"nome": "Ovos de galinha", "grupo": "CP0114",
                        "icone": "M12 20c-3 0-5.5-2.2-5.5-5.2C6.5 10.5 9 4.5 12 4.5"
                                 "s5.5 6 5.5 10.3c0 3-2.5 5.2-5.5 5.2z"},
    "peixes": {"nome": "Peixes", "grupo": "CP0113",
               "icone": "M3.5 12c3.2-4.6 9.3-4.6 12.5 0-3.2 4.6-9.3 4.6-12.5 0z"
                        "M16 12l4.5-3.2v6.4zM12.6 10.6h.01"},
    "pera": {"nome": "Pera", "grupo": "CP0116",
             "icone": "M12 4.5c1.5 0 2 1.5 1.5 3 2 1.2 3 3.4 3 5.8 0 3.6-2 6.2-4.5 6.2"
                      "S7.5 16.9 7.5 13.3c0-2.4 1-4.6 3-5.8-.5-1.5 0-3 1.5-3z"},
    "pessego": {"nome": "Pêssego", "grupo": "CP0116",
                "icone": "M12 19.5a6.5 6.5 0 1 1 0-13 6.5 6.5 0 0 1 0 13z"
                         "M12 6.5c-1.5 3-1.5 9.5 0 13"},
    "tomate": {"nome": "Tomate", "grupo": "CP0117",
               "icone": "M12 20a6.5 6.5 0 1 1 0-13 6.5 6.5 0 0 1 0 13zM12 7V5"
                        "M9 6l3 1.5L15 6"},
    "trigo": {"nome": "Trigo", "grupo": "CP0111",
              "icone": "M12 21V6M12 11 8 8M12 11 16 8M12 15.5 8 12.5M12 15.5 16 12.5"
                       "M12 6.5 9 4.5M12 6.5 15 4.5"},
}

# --------------------------------------------------------------------------
# Correspondência COICOP ↔ Código do IVA
# --------------------------------------------------------------------------
# Levantamento feito sobre o texto das Listas I (taxa reduzida, 6%) e II (taxa
# intermédia, 13%) do Código do IVA. Fecha a lacuna D2 da auditoria de
# 10.08.2026: até aqui a aplicação limitava-se a dizer que a correspondência era
# “aproximada”, sem dizer em quê.
#
# A conclusão é que **a taxa predefinida é a predominante, nunca a única**.
# O simulador continua a aplicar uma taxa por classe, é o que a decomposição
# permite, porque não há despesa aberta ao nível do produto, mas quem o usa
# tem de saber o que fica de fora. **Quanto** fica de fora está apurado em
# `IVA_COMPONENTES`, mais abaixo, a partir dos ponderadores por subclasse da
# COICOP 2018, o que a nomenclatura anterior não permitia.
#
# `taxas` enumera **todas** as taxas presentes na classe, com o que cai em cada
# uma. A predefinida é assinalada pela aplicação a partir de `CLASSES`, e não
# repetida aqui, repeti-la abria a porta a que as duas divergissem em silêncio.
IVA_MAPA_FONTE = ("Código do IVA, Lista I (taxa reduzida) e Lista II "
                  "(taxa intermédia); classes da COICOP versão 2018 conforme o "
                  "anexo do IDF 2022/2023 do INE")

# O levantamento foi **refeito a 11.08.2026 contra as subclasses da COICOP
# versão 2018**, e não contra as da ECOICOP versão 1 sobre as quais tinha sido
# construído. As verbas das Listas I e II não mudaram, mudou aquilo que cada
# classe contém, e portanto o que fica dentro e fora de cada verba. Onde a
# nomenclatura nova dá subclasse própria a um produto que antes estava diluído,
# isso está assinalado: é o que torna a divergência verificável em vez de
# afirmada.
IVA_MAPA = {
    "CP0111": {
        "taxas": [
            (6, "Cereais, arroz, farinhas, massas não recheadas, pão; seitan, "
                "tofu, tempeh e soja texturizada (Lista I, 1.1), cobre as "
                "subclasses 01.1.1.1 a 01.1.1.3 e 01.1.1.5"),
            (13, "Flocos prensados simples de cereais e leguminosas sem adição "
                 "de açúcar (Lista II, 1.12), parte dos cereais para "
                 "pequeno-almoço, 01.1.1.4"),
            (23, "Bolos, bolachas, biscoitos e pastelaria; massas recheadas, "
                 "expressamente excluídas da Lista I"),
        ],
        "nota": "A subclasse 01.1.1.3 chama-se “Pão e produtos de padaria” e "
                "atravessa a fronteira das verbas: o pão está na Lista I, a "
                "pastelaria não.",
    },
    "CP0112": {
        "taxas": [
            (6, "Carnes e miudezas comestíveis, frescas ou congeladas, das "
                "espécies bovina, suína, ovina, caprina, equídea, aves de "
                "capoeira, coelho e caça (Lista I, 1.2), subclasses 01.1.2.2 "
                "e 01.1.2.4"),
            (13, "Alheiras (Lista II, 1.3.3)"),
            (23, "Carne seca, salgada, em salmoura ou fumada (01.1.2.3) e "
                 "preparações de animais abatidos (01.1.2.5), a restante "
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
                "50% (Lista I, 1.3), subclasses 01.1.3.1 a 01.1.3.3"),
            (13, "Conservas de moluscos (Lista II, 1.2.1)"),
            (23, "**Crustáceos**, camarão, lagosta, sapateira: a Lista I "
                 "refere “peixes e moluscos”, não crustáceos. Também peixe "
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
                "frutos secos, cereais, frutas ou hortícolas (Lista I, 1.4), "
                "cobre também o “leite não animal”, 01.1.4.4"),
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
                "(Lista I, 1.4.3), subclasses 01.1.5.2 e 01.1.5.3"),
            (13, "**Óleos vegetais diretamente comestíveis e suas misturas**, "
                 "os óleos alimentares correntes (Lista II, 1.5.3)"),
        ],
        "nota": "Continua a ser a divergência mais material das nove classes, "
                "e a nomenclatura nova torna-a quase exata: “Óleos vegetais” "
                "é agora a **primeira subclasse** (01.1.5.1) e corresponde "
                "praticamente um a um à verba da Lista II, numa classe "
                "predefinida a 6%.",
    },
    "CP0116": {
        "taxas": [
            (6, "Frutas no estado natural ou desidratadas, castanhas e frutos "
                "vermelhos congelados (Lista I, 1.6.4), subclasses 01.1.6.1 "
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
                "leguminosas secas; algas (Lista I, 1.6), subclasses 01.1.7.1 "
                "a 01.1.7.8"),
            (23, "Hortícolas transformados, batata frita de pacote e "
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
                 "01.1.8.2), a verba 1.10 da Lista I foi **revogada**; "
                 "chocolate e cacau (01.1.8.5); gelados (01.1.8.6); doces, "
                 "geleias e marmeladas; restante confeitaria"),
        ],
        "nota": "Predefinida a 23%: aqui a exceção é o mel. E a nomenclatura "
                "nova agrega-o numa subclasse com doces, geleias e marmeladas "
                "(01.1.8.3), o que torna a parcela a 6% **menos separável** do "
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
        "nota": "A classe passou a chamar-se “Alimentos pré-preparados e "
                "outros”, mas **a predefinição a 23% mantém-se**: a subclasse "
                "01.1.9.1 é pré-preparado de retalho, e a verba 1.8 da Lista II "
                "cobre o pronto a comer e levar e a entrega ao domicílio, que "
                "na COICOP caem no grupo 11.1 (restauração) e não aqui. "
                "Continua a ser a classe mais heterogénea das nove.",
    },
}

# --------------------------------------------------------------------------
# Quanto de cada classe segue cada taxa, ao nível da subclasse
# --------------------------------------------------------------------------
# O `IVA_MAPA`, acima, diz **o quê** dentro de cada classe segue taxa diferente
# da predefinida. Não diz **quanto**, e a auditoria de 10.08.2026 (D2)
# concluiu, com razão à data, que “nenhuma fonte pública reparte a despesa da
# classe por taxa legal”.
#
# A COICOP 2018 mudou isso. O `prc_hicp_iw` publica ponderadores a **cinco e
# seis dígitos**, e três desses cortes resolvem as maiores ambiguidades:
#
#   CP011131  Pão                     contra  CP011139  Outros produtos de padaria
#   CP011513  Azeite                  dentro de CP01151  Óleos vegetais
#   CP01123   Carne seca/salgada      separada de CP01122 Carne fresca
#
# `certeza` é o que impede este quadro de prometer mais do que entrega:
#
#   “certa”         a subclasse cai inteira numa verba;
#   “predominante”  a subclasse é maioritariamente de uma taxa, mas não só;
#   “mista”         a subclasse atravessa taxas em proporção não determinável,
#                   e o seu peso vai para a parcela **indeterminada**.
#
# Um componente é `peso: "CODIGO"` ou `peso: ("PAI", ["FILHO", ...])`, neste
# caso o peso do pai menos o dos filhos listados, que é como se isola o que não
# tem código próprio (os óleos vegetais que não são azeite).
#
# ---- `entre`: o intervalo legal de uma parcela indeterminada ----------------
# Um componente “mista” declara em `entre` as **taxas entre as quais a lei o
# situa**. O valor por defeito, (6, 23), é o caso comum: parte na Lista I e
# parte na taxa normal.
#
# Não é uma formalidade. Até 12.08.2026 a parcela indeterminada era sempre
# arbitrada, no valor central, à **taxa predefinida do grupo**, e para os
# cereais de pequeno-almoço isso punha 6% numa subclasse que a lei situa entre
# **13% e 23%**: a verba 1.12 da Lista II cobre os “flocos prensados simples
# de cereais e leguminosas sem adições de açúcar”, e não existe verba alguma na
# Lista I para cereais de pequeno-almoço. O valor central estava **fora do
# intervalo legal** (auditoria de 12.08.2026, G1).
#
# A taxa central de uma parcela indeterminada passa a ser a predefinida do
# grupo **confinada a este intervalo**.
#
# ---- Verificação de 12.08.2026 ---------------------------------------------
# Todo este quadro foi confrontado, verba a verba, com o texto consolidado do
# Código do IVA. Antes disso tinha sido construído por leitura indireta.
CIVA_FONTE = ("Código do IVA, Listas I e II, texto consolidado, versão a "
              "20.05.2026 (Listas em vigor desde 25.05.2026, redação do "
              "Decreto-Lei n.º 97/2026, de 20 de maio)")

# --------------------------------------------------------------------------
# Doutrina da Autoridade Tributária, informações vinculativas
# --------------------------------------------------------------------------
# A auditoria de 12.08.2026 (F4) concluiu que o que faltava para fechar as
# parcelas atribuídas “por predominância” não era estatística, era **leitura
# jurídica**, e que a resposta estaria nas informações vinculativas da AT.
#
# A ficha do Processo 28176 é a primeira que se pôde confrontar com o quadro.
# Vincula a AT nos termos do artigo 68.º do CPPT e decide, sobre produtos
# concretos, questões que estavam em aberto aqui.
#
# ---- O que decide, e que importa a este trabalho --------------------------
# 1. **“Preparados” não cabem na verba 1.1.1.** Papas de aveia, granolas e
#    cereais de arroz infantis são “preparados” ou “snacks” e “não reúnem
#    condições de enquadramento na verba 1.1.1 da lista I, nem em qualquer
#    outra verba das Listas”, **taxa normal**. São o grosso do que se vende
#    como cereais de pequeno-almoço.
# 2. **Refeições pré-preparadas de retalho** (risotto ao qual se junta água)
#    também não cabem em verba alguma, **taxa normal**. Não são o “pronto a
#    comer e levar” da verba 1.8 da Lista II.
# 3. **Verba 1.6.4** cobre a fruta que não sofra transformação além da secagem;
#    exclui expressamente “a moagem, ou laminação em palitos, ou cubos,
#    cobertura”. Frutas desidratadas sem preparação ficam a **6%**; farinhas
#    de fruta e de hortícolas ficam a **23%**.
# 4. **Verba 1.12 é muito mais estreita do que o seu texto sugere.** Só cobre
#    géneros comercializados com a menção “isento de glúten” que **na sua
#    formulação original tinham glúten** e foram reduzidos ou substituídos. Os
#    produtos **naturalmente** sem glúten não cabem lá, foi o que a AT decidiu
#    quanto às barras de fruta e frutos secos.
# 5. **Artigo 18.º, n.º 4**: num produto composto, se as mercadorias mantêm a
#    sua individualidade aplica-se **a taxa mais elevada** de entre as que lhes
#    caberiam; se a perdem, a que corresponder ao produto resultante. É a regra
#    que explica por que tantos preparados acabam na taxa normal.
#
# ---- O princípio que sustenta todo este quadro ----------------------------
# A ficha 24929 enuncia-o de forma que vale a pena citar literalmente:
#
#   “A Lista I prevê taxativamente os produtos que podem beneficiar da taxa
#   reduzida do IVA, não sendo passível de uma interpretação extensiva, pelo que
#   todo o produto que não seja ali contemplado, de forma inequívoca, não pode
#   beneficiar da taxa reduzida de IVA.”
#
# É a justificação doutrinária do método usado aqui: percorrer as Listas e
# atribuir a taxa normal a tudo o que não esteja lá de forma inequívoca. E a
# mesma ficha acrescenta a razão pela qual os preparados caem quase sempre fora:
# “as categorias 1.3 e 1.6 não incluem qualquer tipo de preparados. Quando assim
# é, por exemplo a verba 1.1 da Lista I, estes são especificamente referidos”.
PRINCIPIO_LISTA_TAXATIVA = (
    "A Lista I prevê taxativamente os produtos que podem beneficiar da taxa "
    "reduzida do IVA, não sendo passível de uma interpretação extensiva, pelo "
    "que todo o produto que não seja ali contemplado, de forma inequívoca, não "
    "pode beneficiar da taxa reduzida de IVA."
)
PRINCIPIO_LISTA_TAXATIVA_FONTE = ("Autoridade Tributária, ficha doutrinária do "
                                  "processo 24929, despacho de 2024-01-25")
#
# ---- Uma tensão que se regista e não se resolve --------------------------
# A ficha caracteriza a verba 1.1.1 como abrangendo os cereais “em grão, ou em
# flocos (grão inteiro prensado)”, o que sugeriria 6% para os flocos simples.
# Mas a verba **1.12 da Lista II** é texto legal específico para “flocos
# prensados simples de cereais e leguminosas sem adições de açúcar”, a 13%.
# Entende-se que o texto específico prevalece, e que a caracterização da ficha é
# contextual, a decisão que ela toma é sobre *preparados*, não sobre flocos
# simples. Fica registada porque é o único ponto do quadro onde uma leitura
# diferente é defensável.
AT_FICHAS = [
    {
        "processo": "16563",
        "despacho": "2020-01-30",
        "orgao": "Diretora de Serviços do IVA, por subdelegação",
        "assunto": "Taxas, revenda de artigos de pastelaria",
        "decide": [
            ("CP011139", "A verba 1.1.5 cobre os tipos de “pão” definidos na Portaria "
                         "n.º 52/2015, de 26.02, e **não abrange “quaisquer outros "
                         "produtos afins do pão, ou de pastelaria fina”**. Na revenda "
                         "de produtos de pastelaria aplica-se a taxa normal “por falta "
                         "de enquadramento nas citadas verbas ou em quaisquer outras”."),
            ("CP011131", "A mesma verba **exclui os produtos congelados, intermédios ou "
                         "em processo de fabrico, designadamente o “pão pré-cozido "
                         "congelado” e a “massa de pão congelada”**, tributados à taxa "
                         "normal. A subclasse do pão não é, por isso, homogénea."),
        ],
    },
    {
        "processo": "24929",
        "despacho": "2024-01-25",
        "orgao": "Diretor de Serviços da DSIVA, por subdelegação",
        "assunto": "Preparados de bacalhau, de lulas, mariscada e cocktail de marisco",
        "decide": [
            ("CP01136", "Os preparados de marisco, combinações de ingredientes que "
                        "constituem um produto novo, ficam à taxa normal. As "
                        "categorias 1.3 e 1.6 da Lista I **não incluem qualquer tipo "
                        "de preparados**; quando o legislador os quis abranger, "
                        "referiu-os expressamente."),
            ("CP01179", "Pela mesma razão, as preparações de hortícolas não têm "
                        "enquadramento na categoria 1.6: taxa normal."),
        ],
    },
    {
        "processo": "27368",
        "despacho": "2025-01-30",
        "orgao": "Diretor de Serviços da DSIVA, por subdelegação",
        "assunto": "Carne de bovino e preparados de carne de bovino",
        "decide": [
            ("CP01122", "Carne fresca, miudezas e **carne picada sem qualquer outro "
                        "ingrediente** ficam na verba 1.2, à taxa reduzida, mesmo "
                        "ultracongeladas (ofício-circulado n.º 30170, de 2015-04-10)."),
            ("CP01125", "Os “preparados de carne” (carne com adição de outros géneros, "
                        "condimentos ou aditivos) e os “produtos à base de carne” "
                        "ficam à **taxa normal**, conceitos do Decreto-Lei n.º "
                        "147/2006. Um hambúrguer com água e amido é preparado; um de "
                        "100% carne não é."),
        ],
    },
    {
        "processo": "28176",
        "despacho": "2025-06-27",
        "orgao": "Diretor de Serviços da DSIVA, por subdelegação",
        "assunto": "IVA, Diversos produtos para alimentação humana",
        "decide": [
            ("CP01114", "Papas de aveia, granolas e cereais de arroz infantis são "
                        "“preparados” ou “snacks”: não cabem na verba 1.1.1 nem em "
                        "qualquer outra. Taxa normal."),
            ("CP01191", "Refeições pré-preparadas de retalho (risotto a que se junta "
                        "água) não cabem em verba alguma. Taxa normal, não são o "
                        "“pronto a comer e levar” da verba 1.8 da Lista II."),
            ("CP01167", "Frutas desidratadas sem qualquer preparação enquadram-se na "
                        "verba 1.6.4. Taxa reduzida."),
            ("CP01169", "A verba 1.6.4 exclui expressamente a moagem, a laminação em "
                        "palitos ou cubos e a cobertura. Fruta moída e preparações "
                        "ficam à taxa normal."),
            ("CP01112", "A verba 1.1.3 cobre farinha **de cereais**; farinhas obtidas "
                        "de fruta ou de hortícolas ficam à taxa normal."),
            ("CP01199", "A verba 1.12 só cobre produtos que tinham glúten na "
                        "formulação original e do qual foi removido ou substituído. "
                        "Os naturalmente sem glúten ficam à taxa normal."),
        ],
    },
]
AT_FICHAS_FONTE = ("Autoridade Tributária e Aduaneira, informações vinculativas "
                   "(fichas doutrinárias), artigo 68.º do CPPT")
#
# **Limitação a declarar:** os ponderadores são do IHPC, que inclui a despesa de
# não residentes. É a única fonte aberta que desce a este nível, o IDF fica-se
# pelo quarto dígito. Vale para repartir *dentro* da classe, que é o uso aqui.
IVA_COMPONENTES_FONTE = (
    CIVA_FONTE + " · " + AT_FICHAS_FONTE + ": "
    + ", ".join(f"processo {f['processo']} ({f['despacho']})" for f in AT_FICHAS)
    + " · ponderadores por subclasse do Eurostat, prc_hicp_iw (COICOP 2018)")

IVA_COMPONENTES = {
    "CP0111": [
        {"peso": "CP01111", "taxa": 6, "certeza": "certa",
         "desc": "Cereais (Lista I, 1.1)"},
        {"peso": "CP01112", "taxa": 6, "certeza": "certa",
         "desc": "Farinhas **de cereais** (Lista I, 1.1.3), a AT precisou o "
                 "âmbito: cobre farinha de cereais estreme, mistura, composta, "
                 "corrigida ou autolevedante, e as lácteas e não lácteas; as "
                 "farinhas obtidas de fruta ou de hortícolas ficam a 23% "
                 "(ficha 28176). A subclasse é a das farinhas de cereais"},
        {"peso": "CP011131", "taxa": 6, "certeza": "predominante",
         "desc": "Pão (Lista I, 1.1.5), os tipos definidos na Portaria n.º "
                 "52/2015. **Não é homogénea:** a AT excluiu da verba “os "
                 "produtos congelados, intermédios ou em processo de fabrico, "
                 "designadamente o pão pré-cozido congelado e a massa de pão "
                 "congelada”, que ficam a 23% (ficha 16563). O pão fresco é o "
                 "grosso, mas a subclasse inclui o congelado de retalho"},
        {"peso": "CP011139", "taxa": 23, "certeza": "certa",
         "desc": "Outros produtos de padaria, bolos, bolachas e pastelaria. **A "
                 "AT fechou esta questão:** a verba 1.1.5 cobre os tipos de pão "
                 "definidos na Portaria n.º 52/2015 e “não se enquadram nesta "
                 "verba quaisquer outros produtos afins do pão, ou de pastelaria "
                 "fina”, aplicando-se a taxa normal “por falta de enquadramento "
                 "nas citadas verbas ou em quaisquer outras” (ficha 16563). Era "
                 "a maior parcela por predominância do cabaz"},
        {"peso": "CP01114", "taxa": None, "certeza": "mista", "entre": (13, 23),
         "desc": "Cereais para pequeno-almoço, **nunca a 6%**. A Lista I não "
                 "tem verba para eles; a Lista II (1.12) cobre os “flocos "
                 "prensados simples de cereais e leguminosas sem adições de "
                 "açúcar” a 13%, e os restantes ficam a 23%. A AT confirmou o "
                 "extremo superior: papas de aveia, granolas e cereais infantis "
                 "são “preparados” e não cabem em verba alguma (ficha 28176), o "
                 "que põe o grosso da subclasse a 23%"},
        {"peso": "CP01115", "taxa": 6, "certeza": "predominante",
         "desc": "Massas alimentícias, a Lista I cobre as **não recheadas**; "
                 "as recheadas ficam a 23%"},
        {"peso": "CP01119", "taxa": None, "certeza": "mista",
         "desc": "Outros produtos da transformação de cereais e leguminosas"},
    ],
    "CP0112": [
        {"peso": "CP01121", "taxa": 23, "certeza": "certa",
         "desc": "Animais terrestres vivos, a verba 1.2 da Lista I cobre "
                 "“carnes e miudezas comestíveis, frescas ou congeladas”, e não "
                 "o animal vivo. Não há verba que os abranja"},
        {"peso": "CP01122", "taxa": 6, "certeza": "certa",
         "desc": "Carne fresca, refrigerada ou congelada (Lista I, 1.2), as "
                 "espécies presentes (bovina, suína, ovina, caprina, aves, "
                 "coelho) estão todas na verba. A AT confirmou que abrange a "
                 "**carne picada sem qualquer outro ingrediente**, mesmo "
                 "ultracongelada (ficha 27368, ofício-circulado n.º 30170 de "
                 "2015-04-10); com aditivos passa a “preparado” e sai desta "
                 "subclasse para a CP01125"},
        {"peso": "CP01123", "taxa": 23, "certeza": "certa",
         "desc": "Carne seca, salgada, em salmoura ou fumada, a Lista I só "
                 "cobre fresca ou congelada"},
        {"peso": "CP01124", "taxa": 6, "certeza": "certa",
         "desc": "Miudezas frescas, refrigeradas ou congeladas (Lista I, 1.2)"},
        {"peso": "CP01125", "taxa": 23, "certeza": "predominante",
         "desc": "Preparações de carne, a AT decidiu que os “preparados de "
                 "carne” (carne com adição de outros géneros, condimentos ou "
                 "aditivos) e os “produtos à base de carne” ficam à **taxa "
                 "normal**, conceitos do Decreto-Lei n.º 147/2006 (ficha 27368). "
                 "Fica “predominante” e não “certa” porque as **alheiras** estão "
                 "na verba 1.3.3 da Lista II, a 13%"},
    ],
    "CP0113": [
        {"peso": "CP01131", "taxa": 6, "certeza": "certa",
         "desc": "Peixe vivo, fresco, refrigerado ou congelado (Lista I, 1.3)"},
        {"peso": "CP01132", "taxa": 6, "certeza": "predominante",
         "desc": "Peixe seco ou salgado (Lista I, 1.3.1), o bacalhau é o grosso; "
                 "o peixe fumado e o salmão, espadarte e esturjão salgados "
                 "ficam a 23%"},
        {"peso": "CP01133", "taxa": 6, "certeza": "predominante",
         "desc": "Conservas de peixe com teor superior a 50% (Lista I, 1.3); "
                 "as pastas de atum, cavala e sardinha ficam a 23%"},
        {"peso": "CP01134", "taxa": None, "certeza": "mista",
         "desc": "Marisco fresco ou congelado: **moluscos a 6%, crustáceos a "
                 "23%**. A verba 1.3.3 da Lista I diz “moluscos, ainda que "
                 "secos ou congelados” e não menciona crustáceos, a leitura "
                 "legal é inequívoca; o que falta é a repartição do peso"},
        {"peso": "CP01135", "taxa": None, "certeza": "mista",
         "desc": "Marisco seco ou salgado, a verba 1.3.3 da Lista I cobre os "
                 "moluscos “ainda que secos”; os crustáceos ficam a 23%"},
        {"peso": "CP01136", "taxa": None, "certeza": "mista",
         "desc": "Preparações de marisco, atravessa **as três taxas**: as "
                 "conservas de moluscos com teor superior a 50% caem na verba "
                 "1.3.2 da Lista I (6%), as restantes conservas de moluscos na "
                 "verba 1.2.1 da Lista II (13%), e as de crustáceos a 23%. Os "
                 "**preparados** (mariscadas, cocktails, caldeiradas) ficam a "
                 "23%: a AT decidiu que “as categorias 1.3 e 1.6 não incluem "
                 "qualquer tipo de preparados” (ficha 24929)"},
        {"peso": "CP01137", "taxa": None, "certeza": "mista",
         "desc": "Fígados, ovas e miudezas de peixe e marisco, o caviar fica a 23%"},
    ],
    "CP0114": [
        {"peso": "CP01141", "taxa": 6, "certeza": "certa", "desc": "Leite cru e inteiro (Lista I, 1.4)"},
        {"peso": "CP01142", "taxa": 6, "certeza": "certa", "desc": "Leite desnatado (Lista I, 1.4)"},
        {"peso": "CP01143", "taxa": 6, "certeza": "certa", "desc": "Outro leite e nata (Lista I, 1.4)"},
        {"peso": "CP01144", "taxa": 6, "certeza": "certa",
         "desc": "Leite não animal, bebidas de base vegetal (Lista I, 1.4)"},
        {"peso": "CP01145", "taxa": 6, "certeza": "certa", "desc": "Queijo (Lista I, 1.4)"},
        {"peso": "CP01146", "taxa": 6, "certeza": "certa", "desc": "Iogurtes (Lista I, 1.4)"},
        {"peso": "CP01147", "taxa": None, "certeza": "mista",
         "desc": "Sobremesas **e bebidas** à base de leite, a subclasse junta "
                 "duas coisas com taxas diferentes: a verba 1.4.7 da Lista I "
                 "cobre os “leites chocolatados, aromatizados, vitaminados ou "
                 "enriquecidos” a 6%, e as sobremesas lácteas não têm verba, "
                 "ficando a 23%"},
        {"peso": "CP01148", "taxa": 6, "certeza": "certa", "desc": "Ovos (Lista I, 1.4)"},
        {"peso": "CP01149", "taxa": None, "certeza": "mista", "desc": "Outros produtos lácteos"},
    ],
    "CP0115": [
        {"peso": "CP011513", "taxa": 6, "certeza": "certa",
         "desc": "**Azeite** (Lista I, 1.5), tem código próprio na COICOP 2018"},
        {"peso": ("CP01151", ["CP011513"]), "taxa": 13, "certeza": "certa",
         "desc": "**Óleos vegetais que não o azeite**, os óleos alimentares "
                 "correntes, diretamente comestíveis (Lista II, 1.5.3)"},
        {"peso": "CP01152", "taxa": 6, "certeza": "certa",
         "desc": "Manteiga e gorduras derivadas do leite (Lista I, 1.4.3)"},
        {"peso": "CP01153", "taxa": 6, "certeza": "certa",
         "desc": "Margarina e creme vegetal para barrar (Lista I, 1.4.3)"},
        {"peso": "CP01159", "taxa": 6, "certeza": "predominante",
         "desc": "Outras gorduras animais, a verba 1.5.2 da Lista I cobre a "
                 "“banha e outras gorduras **de porco**”, que é o grosso; as "
                 "gorduras de outras espécies não têm verba e ficam a 23%"},
    ],
    "CP0116": [
        {"peso": "CP01161", "taxa": 6, "certeza": "certa", "desc": "Frutos tropicais frescos (Lista I, 1.6.4)"},
        {"peso": "CP01162", "taxa": 6, "certeza": "certa", "desc": "Citrinos frescos (Lista I, 1.6.4)"},
        {"peso": "CP01163", "taxa": 6, "certeza": "certa", "desc": "Frutas de caroço e de pevide frescas (Lista I, 1.6.4)"},
        {"peso": "CP01164", "taxa": 6, "certeza": "certa", "desc": "Bagas frescas (Lista I, 1.6.4)"},
        {"peso": "CP01165", "taxa": 6, "certeza": "certa", "desc": "Outras frutas frescas (Lista I, 1.6.4)"},
        {"peso": "CP01166", "taxa": None, "certeza": "mista",
         "desc": "Fruta congelada, a Lista I cobre os **frutos vermelhos** "
                 "congelados; a restante fica a 23%"},
        {"peso": "CP01167", "taxa": 6, "certeza": "certa",
         "desc": "Frutos secos e desidratados (Lista I, 1.6.4), a AT decidiu "
                 "expressamente que “frutas desidratadas sem qualquer "
                 "preparação” se enquadram nesta verba (ficha 28176)"},
        {"peso": "CP01168", "taxa": None, "certeza": "mista",
         "desc": "Frutos de casca rija, a Lista I refere as **castanhas** "
                 "nominalmente; amêndoa, noz e avelã ficam a 23%"},
        {"peso": "CP01169", "taxa": 23, "certeza": "certa",
         "desc": "Fruta moída e outras preparações, a AT decidiu que a verba "
                 "1.6.4 exclui expressamente “a moagem, ou laminação em palitos, "
                 "ou cubos, cobertura”, e que há produto novo sempre que a "
                 "transformação faz a fruta perder a natureza de fruto (ficha "
                 "28176). A subclasse é, por definição, o que sofreu essa "
                 "transformação"},
    ],
    "CP0117": [
        {"peso": "CP01171", "taxa": 6, "certeza": "certa", "desc": "Hortícolas de folha ou caule, frescos (Lista I, 1.6)"},
        {"peso": "CP01172", "taxa": 6, "certeza": "certa", "desc": "Hortícolas de fruto, frescos (Lista I, 1.6)"},
        {"peso": "CP01173", "taxa": 6, "certeza": "certa", "desc": "Legumes de vagem verde, frescos (Lista I, 1.6)"},
        {"peso": "CP01174", "taxa": 6, "certeza": "certa", "desc": "Outros hortícolas frescos (Lista I, 1.6)"},
        {"peso": "CP01175", "taxa": 6, "certeza": "certa", "desc": "Tubérculos e bananas para culinária (Lista I, 1.6)"},
        {"peso": "CP01176", "taxa": 6, "certeza": "certa", "desc": "Leguminosas secas (Lista I, 1.6)"},
        {"peso": "CP01177", "taxa": 6, "certeza": "certa", "desc": "Hortícolas secos e desidratados (Lista I, 1.6)"},
        {"peso": "CP01178", "taxa": 6, "certeza": "certa",
         "desc": "Hortícolas congelados, a Lista I cobre-os, “ainda que "
                 "previamente cozidos”"},
        {"peso": "CP01179", "taxa": 23, "certeza": "certa",
         "desc": "Hortícolas moídos e outras preparações, batata frita de "
                 "pacote, conservas e preparados. A AT decidiu que **“as "
                 "categorias 1.3 e 1.6 não incluem qualquer tipo de preparados”**, "
                 "e que quando o legislador os quis abranger os referiu "
                 "expressamente (ficha 24929). A categoria 1.6 cobre frescos, "
                 "secos, desidratados e congelados, não preparações"},
    ],
    "CP0118": [
        {"peso": "CP01181", "taxa": 23, "certeza": "certa",
         "desc": "Açúcar de cana e de beterraba, a verba 1.10 da Lista I foi "
                 "**revogada**"},
        {"peso": "CP01182", "taxa": 23, "certeza": "certa", "desc": "Outros açúcares e sucedâneos"},
        {"peso": "CP01183", "taxa": None, "certeza": "mista",
         "desc": "Doces, geleias, marmeladas **e mel**, só o mel está na "
                 "Lista I (1.8), e a nomenclatura agrega-os na mesma subclasse"},
        {"peso": "CP01184", "taxa": 23, "certeza": "certa", "desc": "Purés e manteigas de frutos de casca rija"},
        {"peso": "CP01185", "taxa": 23, "certeza": "certa", "desc": "Chocolate, cacau e produtos à base de cacau"},
        {"peso": "CP01186", "taxa": 23, "certeza": "certa", "desc": "Gelo, gelados e sorvetes"},
        {"peso": "CP01189", "taxa": 23, "certeza": "certa", "desc": "Outra confeitaria e sobremesas de açúcar"},
    ],
    "CP0119": [
        {"peso": "CP01191", "taxa": 23, "certeza": "predominante",
         "desc": "Alimentos pré-preparados **de retalho**. A verba 1.8 da "
                 "Lista II (13%) cobre o pronto a comer e levar e a entrega ao "
                 "domicílio, que na COICOP caem no grupo 11.1 (restauração) e "
                 "não aqui. A AT confirmou-o: refeições pré-preparadas de "
                 "retalho, a que se junta água, “não reúnem condições de "
                 "enquadramento em qualquer verba” e ficam à taxa normal (ficha "
                 "28176). Fica “predominante” porque a subclasse é larga e "
                 "abrange formatos que a ficha não apreciou"},
        {"peso": "CP01192", "taxa": 6, "certeza": "certa",
         "desc": "Alimentos para bebés e crianças de pouca idade (Lista I, 1.14)"},
        {"peso": "CP01193", "taxa": None, "certeza": "mista",
         "desc": "Sal, condimentos e molhos, o **sal** está na Lista I (1.9), "
                 "os condimentos e molhos a 23%, na mesma subclasse"},
        {"peso": "CP01194", "taxa": 23, "certeza": "certa",
         "desc": "Especiarias, ervas aromáticas e sementes para culinária"},
        {"peso": "CP01199", "taxa": None, "certeza": "mista",
         "desc": "Outros produtos alimentares, recolhe várias verbas da Lista I "
                 "a 6%: nutrição entérica e sem glúten (1.12), seitan, tofu, "
                 "tempeh e soja texturizada (1.1.6), algas (1.6.5), produtos "
                 "semelhantes a queijo sem leite (1.13) e substitutos integrais "
                 "da dieta (1.14). **A verba 1.12 é bem mais estreita do que o "
                 "seu texto sugere:** a AT só a aplica a produtos que tinham "
                 "glúten na formulação original e do qual foi removido ou "
                 "substituído, os naturalmente sem glúten ficam a 23% (ficha "
                 "28176). O restante fica a 23%"},
    ],
}


def _codigos_de_componente(comp) -> list:
    """Códigos do Eurostat que um componente do `IVA_COMPONENTES` precisa."""
    p = comp["peso"]
    return [p] if isinstance(p, str) else [p[0]] + list(p[1])


IVA_SUBCLASSES = sorted({
    cod
    for componentes in IVA_COMPONENTES.values()
    for comp in componentes
    for cod in _codigos_de_componente(comp)
})

# Agregado alimentar (soma das nove classes)
COICOP_ALIMENTAR = "CP011"

# --------------------------------------------------------------------------
# Ano-base do painel de viés de substituição
# --------------------------------------------------------------------------
# O painel “cabaz fixo contra Törnqvist” encadeia os dois índices a partir de um
# dezembro. Esse dezembro era o primeiro da janela pedida ao Eurostat, que é
# `ano corrente − 6`. A 1 de janeiro deslizava sozinho: a métrica “viés
# acumulado desde dez/20” passaria a medir outro período com o mesmo nome, sem
# que ninguém o decidisse (auditoria de 11.08.2026, E14).
#
# Uma série que se compara entre versões do documento tem de ter base estável.
# Fixa-se aqui, e a janela de pedido é dimensionada para a cobrir.
#
# 2019 é o primeiro dezembro com série completa das nove classes na ECOICOP
# versão 2 (`prc_hicp_minr`, unidade I25, verificado a 11.08.2026: as classes
# começam em 2019-01). Alterar este ano muda o valor publicado do viés, é uma
# decisão, não um detalhe de implementação.
ANO_BASE_VIES = 2019

# --------------------------------------------------------------------------
# Repercussão, a fração da alteração de imposto que chega ao preço final
# --------------------------------------------------------------------------
# É **o parâmetro decisivo** do simulador: move o resultado 250% entre 0% e
# 100%, mais do que todas as outras incertezas somadas (auditoria de
# 12.08.2026, F1). Até 12.08.2026 o valor por defeito era **40%**, declarado
# como “parâmetro de trabalho, não estimativa”, fundado em avaliações
# internacionais de outros setores e outros países, França 2009 (restauração),
# Suécia. Nenhuma delas sobre Portugal, nenhuma sobre alimentação em retalho.
#
# Portugal correu esta experiência. O “IVA zero” da Lei n.º 17/2023, de 14 de
# abril, isentou 46 bens alimentares entre 18.04.2023 e 04.01.2024, e o Banco de
# Portugal mediu a repercussão por quatro vias independentes. Os 40% não são
# uma hipótese conservadora, são **contrariados pela única evidência
# portuguesa sobre a medida idêntica**, por um fator de 2,4.
#
# ---- Como se extrai a repercussão dos números publicados -------------------
# O BdP publica o **efeito mecânico** (a variação de preço com repercussão
# integral) e o **efeito observado**. A repercussão é o quociente dos dois:
#
#     ρ = variação observada / variação mecânica
#
# O efeito mecânico de passar da taxa t₀ para t₁ é (1+t₁)/(1+t₀) − 1. Para uma
# isenção a partir de 6%: 1/1,06 − 1 = −5,66%. A partir de 23%: 1/1,23 − 1
# = −18,70%, que é exatamente o valor que o BdP publica para os óleos
# alimentares (WAPP, p. 5). A aritmética de IVA contido desta aplicação
# reproduz a do Banco de Portugal; isso está travado por teste.
#
# ---- Ressalvas, que são parte da estimativa e não uma nota de rodapé -------
# 1. O próprio BdP alerta para **desvios-padrão elevados** nas estimativas de
#    diferença-nas-diferenças, e para a granularidade insuficiente do IHPC (as
#    rubricas afetadas incluem bens não abrangidos, o que dilui observado e
#    mecânico na mesma proporção, por isso o quociente sobrevive).
# 2. Foi uma medida **temporária, taxativa e muito mediática**, com pressões de
#    custo a montante já em queda e acompanhamento público do setor. Uma
#    alteração permanente e discreta pode repercutir-se menos.
# 3. A janela avaliada vai até agosto de 2023, **quatro meses**. Não há aqui
#    evidência sobre erosão a prazo. O balanço do período completo mostra o
#    cabaz da DECO a subir 4,71%: a repercussão foi alta, e mesmo assim o
#    efeito foi superado pela inflação de base. São coisas diferentes.
# 4. A evidência robusta é sobre cortes **a partir de 6%**. Para os 23% há um
#    único produto (óleos alimentares).
# 5. Os valores acima de 100% refletem provavelmente concorrência e saliência
#    política, não repercussão pura. Não se usa mais de 1,00 por defeito.
REPERCUSSAO_FONTE = (
    "Banco de Portugal, “Impacto do IVA zero sobre os preços”, WAPP de "
    "22.11.2023 (Gouveia, Manteu, Serra e Cabral) · Boletim Económico de "
    "outubro de 2023, caixa 4"
)

# (rótulo, observado %, mecânico %, método)
# O observado e o mecânico são os publicados; o ρ é derivado, não citado.
REPERCUSSAO_ESTIMATIVAS = [
    ("IHPC, diferença-nas-diferenças vs. Espanha", 4.0, 4.2,
     "Regressão de event-study, Portugal como tratamento e Espanha como "
     "controlo; rubricas com IVA anterior de 6%; pré-tratamento set/2022 a "
     "mar/2023. O contrafactual foi estatisticamente confirmado."),
    ("IHPC, diferença-nas-diferenças vs. área do euro", 3.5, 4.2,
     "Mesma especificação, com a área do euro como controlo."),
    ("Preços online, cabaz abrangido", 6.0, 5.66,
     "Preços diários fixados nas plataformas dos principais retalhistas "
     "(BPLIM). Semana de 23-29.04 contra a semana anterior à medida. As "
     "variações concentraram-se entre −5% e −7%."),
    ("Preços online, óleos alimentares (eram 23%)", 24.5, 18.70,
     "Único produto do cabaz com taxa anterior de 23% isolado na publicação. "
     "Amostra de um: indicativo, não conclusivo."),
]

# Valor por defeito: a estimativa de diferença-nas-diferenças com **Espanha
# como controlo** (4,0/4,2 = 0,952), que é a única cujo contrafactual o BdP
# declara estatisticamente confirmado. Escolhe-se pela qualidade do
# contrafactual, e não por prudência: das duas de diferença-nas-diferenças é a
# **mais alta**, porque a de controlo da área do euro dá 3,5/4,2 = 0,833.
#
# O comentário anterior descrevia-a como “a mais conservadora das duas
# robustas”, o que é o contrário do que a tabela desta mesma aplicação mostra,
# e a interface repetia a afirmação por baixo dos números que a desmentiam
# (auditoria de 12.08.2026, L4). A escolha mantém-se; a justificação é que
# estava trocada. As duas de preços online não entram por medirem uma janela de
# duas semanas e darem acima de 100%.
REPERCUSSAO_PADRAO = 0.95

# Banda apresentada com os indicadores: da estimativa mais baixa (área do euro,
# 83,3%) à repercussão integral (100%). É aqui que a leitura conservadora
# aparece, não no valor por defeito. Não se estende abaixo de 83,3% porque
# nenhuma estimativa portuguesa o sustenta, nem acima de 100% pela ressalva 5.
REPERCUSSAO_BANDA = (0.833, 1.00)

# --------------------------------------------------------------------------
# Distribuição do IVA zero por quintil de rendimento
# --------------------------------------------------------------------------
# A mesma publicação do BdP mede duas coisas que apontam em sentidos opostos, e
# ambas são verdadeiras:
#
#   - o **alívio na inflação** foi maior nos agregados de menor rendimento,
#     porque a alimentação pesa mais no seu cabaz;
#   - a **afetação do custo orçamental** foi maior para os agregados de maior
#     rendimento, porque gastam mais em valor absoluto.
#
# Uma ferramenta que só mostre a primeira dá uma leitura incompleta a quem
# decide. O BdP é explícito: as famílias do quintil mais elevado “recebem mais
# 20% de recursos públicos do que as do quintil de menores rendimentos, não
# contribuindo para uma política focada nos agregados vulneráveis”.
IVA_ZERO_QUINTIS_FONTE = (
    "Banco de Portugal, WAPP de 22.11.2023, p. 9 · inflação por quintil: "
    "Boletim Económico de outubro de 2022, caixa “Estimativas de inflação por "
    "nível de rendimento e escalão etário” · afetação orçamental: simulações "
    "EUROMOD estendidas a impostos indiretos, sobre EU-SILC e IDF · a citação "
    "sobre os recursos públicos é da caixa 3 do Boletim Económico de junho de 2023"
)

# Perímetro e calendário da medida de 2023, transcritos da p. 2 do mesmo WAPP:
# “A medida do IVA zero entrou em vigor a 18 de abril e deverá prolongar-se até
# ao final do ano. Isenta temporariamente de IVA um cabaz de 46 alimentos (a
# maioria com taxa anterior de 6%).”
#
# O segundo número é o que interessa a quem decide, e não é uma curiosidade
# histórica: a medida efetivamente tomada em 2023 foi sobretudo uma **isenção do
# que já estava no mínimo**, não uma descida de taxa. É a mesma fronteira que o
# apuramento por subclasse mostra hoje.
#
# Como texto e não como `date`: só é usado em prosa, e o `config` não importa
# `datetime` para mais nada.
IVA_ZERO_INICIO = "18 de abril de 2023"
IVA_ZERO_N_ALIMENTOS = 46

# Citação **verbatim**, confrontada com a p. 9 do WAPP de 22.11.2023.
#
# Fica aqui inteira, e não montada no `app.py` à volta de um número calculado,
# por uma razão que é de rigor e não de arrumação: a aplicação interpolava dentro
# das aspas o resultado de `23 / 19 - 1`, que dá **21%**. O Banco de Portugal
# escreveu **20%**, partiu dos valores não arredondados, não das percentagens
# publicadas. Atribuir a uma fonte um número que ela não escreveu é uma citação
# falsa, mesmo quando a diferença é de um ponto (assinalado à Inês, 13.08.2026).
#
# Nada dentro destas aspas pode ser derivado, formatado ou enfatizado: o realce
# que não é do original não entra sem “sublinhado nosso”.
IVA_ZERO_CITACAO = (
    "as famílias do quintil mais elevado de rendimentos recebem mais 20% de "
    "recursos públicos do que as do quintil de menores rendimentos, não "
    "contribuindo para uma política focada nos agregados vulneráveis"
)

# Taxa de variação em cadeia em maio de 2023, em pontos percentuais.
# (quintil, rubricas alimentares abrangidas pela isenção, bens alimentares, IPC total)
# A ordem é esta e importa: a primeira coluna é a que sustenta o argumento do
# simulador, e as duas seguintes situam-na. Confirma-se pelos valores, o alívio
# nas rubricas abrangidas é sempre maior do que no conjunto dos alimentares, e
# este maior do que no IPC total.
#
# Sobre a unidade: o rótulo é o do original, e o original não é consistente
# consigo próprio. O gráfico da p. 9 diz “Taxa de variação em cadeia em maio de
# 2023, em pp”; os gráficos da mesma grandeza nas pp. 5 e 6 dizem “em
# percentagem”. Uma taxa de variação exprime-se em percentagem, pontos
# percentuais são para diferenças **entre** taxas. Mantém-se “p.p.” porque é o
# que o Banco de Portugal imprime neste gráfico concreto; a divergência
# regista-se aqui em vez de se corrigir em silêncio numa fonte citada.
IVA_ZERO_INFLACAO_QUINTIL = [
    ("Total de famílias", -4.1, -2.6, -0.7),
    ("Q1 (mais baixo)", -4.4, -2.9, -0.9),
    ("Q2", -4.2, -2.8, -0.9),
    ("Q3", -4.0, -2.6, -0.7),
    ("Q4", -4.5, -2.8, -0.7),
    ("Q5 (mais elevado)", -3.7, -2.3, -0.4),
]

# Fração do custo orçamental de cada medida de 2023 que chega ao quintil mais
# pobre e ao mais rico. Serve para situar a redução do IVA face às alternativas
# que o Estado tinha em cima da mesa no mesmo ano.
# (medida, % para os 20% mais pobres, % para os 20% mais ricos)
IVA_ZERO_AFETACAO_ORCAMENTAL = [
    ("Redução do IVA", 19, 23),
    ("Complemento extraordinário ao abono", 35, 1),
    ("Apoio às rendas", 40, 1),
    ("Apoio a famílias vulneráveis 2023", 71, 1),
]

# --------------------------------------------------------------------------
# Agregados especiais do índice, permitem separar o que é choque conjuntural
# do que é inflação estrutural, e situar a alimentação no conjunto dos preços.
# --------------------------------------------------------------------------
# O total era o agregado especial `FOOD`, rotulado “Alimentação e bebidas
# (total)”. Não é isso que ele mede. Verificado a 20.08.2026 contra os
# ponderadores do Eurostat (`prc_hicp_iw`, Portugal, 2026):
#
#   CP01  Produtos alimentares e bebidas não alcoólicas     207,35 ‰
#   CP02  Bebidas alcoólicas e tabaco                        32,19 ‰
#   soma                                                    239,54 ‰
#   FOOD                                                    239,54 ‰
#
# São o mesmo número, e a igualdade repete-se em **todos** os anos desde 1996.
# `FOOD` = `CP01` + `CP02`, ou seja, inclui bebidas alcoólicas e tabaco, que
# valem 13,4% do agregado.
#
# Em Portugal a contaminação era pequena no momento da verificação, mas o
# gráfico mostra também a UE-27, e aí **duplicava a leitura**. Julho de 2026:
#
#              CP01    FOOD    CP02
#   Portugal    2,2%    2,3%    2,6%
#   UE-27       0,6%    1,2%    3,9%
#
# A linha europeia dizia 1,2% quando a alimentação e as bebidas não alcoólicas
# subiam 0,6%. A diferença é o tabaco, que sobe por via do imposto especial de
# consumo e não por dinâmica do mercado alimentar. Um agregado rotulado
# “alimentação” não pode duplicar por causa disso.
#
# `FOOD_NP` + `FOOD_P` dão os mesmos 239,54 ‰ (84,32 + 155,22). Como o tabaco
# não cabe nos frescos, está do lado dos **transformados**, misturado com o pão
# e os laticínios, e o seu preço sobe por via do imposto especial de consumo,
# não por dinâmica do mercado alimentar.
#
# O total passa a ser `CP01`, que é o universo que o resto da aplicação usa e o
# que a metodologia declara. A contrapartida é que o total deixa de ser a soma
# exata das duas parcelas do gráfico: os agregados especiais só existem nesta
# forma. A incoerência é declarada em `AGREGADOS_NOTA`, e é preferível a um
# total que diz “alimentação” e traz tabaco lá dentro (decisão da Inês,
# 20.08.2026).
AGREGADOS = [
    # --- a alimentação por dentro: são componentes do objeto do estudo ---
    {"cod": "FOOD_NP", "nome": "Alimentos não transformados", "cor": "#D02117", "larg": 2.4,
     "grupo": "alimentacao", "porque": "Frescos. Reagem a clima e sazonalidade, é aqui que "
                                       "os choques de oferta aparecem primeiro."},
    {"cod": "FOOD_P", "nome": "Alimentos transformados", "cor": "#BE9C54", "larg": 2.4,
     "grupo": "alimentacao", "porque": "Pão, laticínios, conservas. Refletem custos de "
                                       "produção e distribuição, não o tempo que fez. "
                                       "Nesta convenção do Eurostat inclui também as "
                                       "bebidas alcoólicas e o tabaco."},
    {"cod": "CP01", "nome": "Alimentação e bebidas não alcoólicas", "cor": "#0E7433", "larg": 2.8,
     "grupo": "alimentacao", "porque": "O universo que o resto da aplicação mede. Não é a "
                                       "soma exata das duas linhas acima: aquelas incluem "
                                       "álcool e tabaco, esta não."},
    # --- enquadramento: não são alimentação, servem de referência ---
    # `TOTAL` e não `CP00`: na ECOICOP versão 2 o agregado de todos os produtos
    # mudou de código. `CP00` devolve HTTP 400 em `prc_hicp_minr`, e a via de
    # reserva respondia com uma fatia arbitrária em vez de erro
    # (auditoria de 11.08.2026, E1).
    {"cod": "TOTAL", "nome": "Todos os produtos", "cor": "#171715", "larg": 2.2,
     "grupo": "enquadramento", "porque": "A inflação geral. Responde a “como pode a inflação "
                                         "ser baixa e o cabaz subir?”"},
    {"cod": "TOT_X_NRG_FOOD", "nome": "Subjacente (sem energia nem alimentos)",
     "cor": "#2B5683", "larg": 1.8, "grupo": "enquadramento",
     "porque": "A medida que os bancos centrais seguem. Distingue pressão estrutural "
               "de choque temporário."},
]

COD_AGREGADOS = [a["cod"] for a in AGREGADOS]

# Vai por baixo do gráfico dos agregados. Declara a incoerência em vez de a
# esconder: sem esta nota, o leitor soma as duas parcelas, não lhe dá o total, e
# não tem como saber porquê. Sem códigos de conjunto, que vivem na metodologia.
AGREGADOS_NOTA = (
    "**A linha do total não corresponde à soma das outras duas, e a diferença é "
    "esperada.** Mede a "
    "alimentação e as bebidas não alcoólicas, que é o universo do resto da "
    "aplicação. As duas linhas que a decompõem seguem a convenção do Eurostat "
    "para separar frescos de transformados, e nessa convenção os transformados "
    "**incluem bebidas alcoólicas e tabaco**, que valem cerca de 13% desse "
    "conjunto. A diferença entre o total e a soma é sobretudo tabaco, cujo preço "
    "sobe por via do imposto especial de consumo e não por dinâmica do mercado "
    "alimentar."
)
AGREGADOS_NOTA_FONTE = ("Eurostat, ponderadores do índice harmonizado, Portugal, "
                        "verificado em 20 de agosto de 2026")

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
# Número de agregados familiares, divisor da despesa nacional
# --------------------------------------------------------------------------
# Valor de referência oficial. Os Censos são a fonte autoritativa para o número
# de agregados: é um apuramento exaustivo, não uma estimativa por amostragem.
AGREGADOS_CENSOS = 4_149_096
AGREGADOS_FONTE = "INE, Censos 2021 (resultados definitivos)"
AGREGADOS_ANO = 2021

# Dimensão média do agregado, apenas usada se o Eurostat não responder.
# O valor corrente é obtido de ilc_lvph01 (EU-SILC) em cada sessão: está em
# queda em toda a Europa, pelo que uma constante desatualiza-se depressa.
DIMENSAO_RECUO = 2.4
DIMENSAO_RECUO_FONTE = "Eurostat, ilc_lvph01 (EU-SILC), 2025"

# --------------------------------------------------------------------------
# Âncoras da despesa alimentar, duas bases oficiais que não coincidem
# --------------------------------------------------------------------------
# As Contas Nacionais medem o consumo *no território*, incluindo o de não
# residentes, e são obtidas em direto do Eurostat. O IDF mede a despesa
# declarada pelos agregados *residentes*.
#
# Para 2022 as duas divergem por um fator de 2,3 na alimentação, muito acima
# do desvio geral de 1,7 entre inquérito e Contas Nacionais.
#
# **As duas não são medições independentes.** A metainformação nacional do
# `nama_10_cp18` (ESMS de Portugal, §18.1) declara que o IDF é o ponto de
# partida da estimativa do consumo das famílias, que o INE o confrontou com o
# IVA, com o volume de negócios do retalho e com informação setorial, que
# concluiu que os valores do inquérito estavam subavaliados, e que o valor
# final é o que resulta do equilíbrio do QERU. A repartição por COICOP é
# obtida do QERU depois de fechado esse equilíbrio.
#
# O mecanismo da divergência está portanto documentado; a **magnitude** por
# rubrica não está, porque o INE não publica a taxa de cobertura por classe
# COICOP. A anomalia da alimentação (44% de cobertura, contra 66% no conjunto
# e um mínimo europeu de 58%) continua sem número que a explique.
#
# Nenhuma das duas é “a” resposta para a pergunta da aplicação: as Contas
# Nacionais respondem a “quanto se consumiu em alimentos no território”, e
# incluem autoconsumo, não residentes e ajustamentos de exaustividade, que não
# são despesa de agregados residentes; o inquérito subestima, por conclusão
# declarada do próprio compilador. A aplicação apresenta por isso o intervalo
# entre ambas e deixa o utilizador escolher a base de trabalho.
# Ver docs/2026-08-07_levantamento_lacunas.md, §2.10.
IDF_ALIMENTAR_ANUAL = 2872.0          # € por agregado e por ano, COICOP 01.1
IDF_FONTE = "INE, IDF 2022/2023 (quadro Q.2.11.a)"

# Período de referência do IDF 2022/2023, confirmado no documento metodológico
# do INE (Metainformação IDF, V.6.1.1): “O período de recolha decorrerá entre
# 3 de fevereiro de 2022 e 5 de fevereiro de 2023, correspondendo a 26
# quinzenas. Os dados de cada agregado são recolhidos ao longo de 14 dias”.
#
# Duas consequências, e ambas importam:
#
# 1. A recolha é **uniforme ao longo de doze meses** (26 quinzenas seguidas),
#    não um instantâneo. O valor publicado é uma média desse período.
# 2. O INE **não corrige os valores para uma data comum**: V.7.4, “Ajustamentos
#    dos dados: Não aplicável”. Ficam aos preços do momento em que cada
#    agregado foi inquirido.
#
# Logo, a base de indexação não é um ano civil, é a janela de recolha. A
# aplicação usava `IDF_ANO_BASE = 2023`, um pressuposto que ninguém tinha
# confirmado e que subestimava o valor atual em 21,05 €/mês, 8,3%
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
        "porque": "Medição direta da despesa dos agregados residentes. Subestima: "
                  "é o próprio INE que declara, na metainformação das Contas "
                  "Nacionais, ter concluído que os valores do inquérito estavam "
                  "subavaliados quando os confrontou com o IVA, com o volume de "
                  "negócios do retalho e com informação setorial.",
    },
    "contas": {
        # `nama_10_co3_p3` foi arquivado com a passagem à COICOP 2018 e a
        # aplicação migrou para `nama_10_cp18` a 11.08.2026 (E1/E2), esta
        # citação tinha ficado para trás, a apontar para um conjunto parado.
        "nome": "Contas Nacionais",
        "fonte": "Eurostat, nama_10_cp18 (Contas Nacionais, COICOP 2018, "
                 "compiladas pelo INE), conceito **interno**: despesa no "
                 "território económico, não residentes incluídos",
        "porque": "Agregado macroeconómico dividido pelo número de agregados. "
                  "Mede o **consumo no território**, não a despesa das famílias "
                  "residentes: inclui autoconsumo, compras de não residentes e "
                  "ajustamentos de exaustividade. Sobrestima a despesa de um "
                  "agregado, mas **não é sobretudo por causa dos não "
                  "residentes**: no caso dos alimentos consumidos em casa esse "
                  "efeito é pequeno (ver CONCEITO_CONTAS_NACIONAIS). O valor "
                  "resulta do equilíbrio do QERU, que reviu em alta os "
                  "resultados do inquérito por os ter concluído subavaliados.",
    },
}
BASE_POR_DEFEITO = "idf"

# --------------------------------------------------------------------------
# Conceito das Contas Nacionais, verificado a 12.08.2026
# --------------------------------------------------------------------------
# Ficara em aberto na auditoria de 12.08.2026 (F5) se o `nama_10_cp18` está em
# conceito **interno** (despesa no território, não residentes incluídos) ou
# **nacional** (residentes, onde quer que gastem). A distinção decide se a base
# serve para medir impacto nas famílias residentes.
#
# ---- Prova 1: identidade contabilística ------------------------------------
# O total da desagregação por COICOP excede sistematicamente o `P31_S14` do
# `nama_10_gdp`, que é o consumo das famílias no conceito nacional. Em 2024:
# 192 796 contra 171 641 M€, mais 21 155 M€, ou 12,3%. Se estivessem no mesmo
# conceito, seriam iguais.
#
# ---- Prova 2: o ano de 2020 ------------------------------------------------
# A diferença entre os dois desabou em 2020, de 13 503 para 5 277 M€ (−61%),
# no ano em que o turismo parou, e recuperou depois. Nada além do turismo
# produz esse padrão. **O `nama_10_cp18` está no conceito interno.**
#
# ---- E quanto contamina os alimentos? --------------------------------------
# Muito menos do que o total, e isto corrige o que a app afirmava. Em 2020:
#
#   CP111 restauração        −36,6%      (o turismo estava aqui)
#   CP011 alimentação em casa  +3,1%      (subiu)
#
# Se a despesa alimentar em casa fosse materialmente de turistas, teria caído em
# 2020. Subiu. Os não residentes comem em restaurantes, não cozinham em casa.
#
# **Ressalva honesta:** 2020 teve dois efeitos em sentidos opostos sobre o CP011
#, os residentes substituíram restaurante por casa (a subir) e os turistas
# desapareceram (a descer). O saldo foi +3,1%, o que **não prova que o efeito
# turista seja nulo**, só que é menor do que a substituição. O limite superior,
# se os não residentes consumissem alimentos em casa na proporção do seu peso no
# consumo total, seria 12,3% do CP011; a evidência de 2020 diz que o valor real
# está bem abaixo.
#
# ---- Consequência ----------------------------------------------------------
# A base **não se troca**, mas a razão mudou. Não é “as Contas Nacionais estão
# contaminadas por turistas”: essa contaminação existe e é pequena nos
# alimentos. É que a divergência de ~2,3× face ao IDF **continua sem explicação
# completa**, e uma diferença dessa ordem não se adota sem a perceber.
CONCEITO_CONTAS_NACIONAIS = {
    "conceito": "interno",
    "verificado": "2026-08-12",
    "prova": ("Total COICOP (nama_10_cp18) contra P31_S14 (nama_10_gdp), "
              "conceito nacional: 192 796 contra 171 641 M€ em 2024. A "
              "diferença desaba 61% em 2020, com a paragem do turismo."),
    "efeito_nos_alimentos": ("Pequeno. Em 2020 a restauração (CP111) caiu "
                             "36,6% e a alimentação em casa (CP011) subiu "
                             "3,1%. Limite superior de 12,3%; o valor real "
                             "está bem abaixo."),
}

# --------------------------------------------------------------------------
# IDF 2022/2023 por quintil de rendimento, a base estrutural
# --------------------------------------------------------------------------
# Divisão de trabalho entre as duas fontes de ponderação, decidida em 08.08.2026:
#
#   IDF   → estrutura e distribuição (quem gasta o quê, e que parte do orçamento)
#   IHPC  → movimento dos preços (como variou cada classe)
#
# A razão não é de conveniência. O Documento Metodológico do IPC (INE, 2023) é
# explícito: “O IHPC inclui a despesa realizada pelos não residentes ("turistas")
# no território económico e exclui a despesa dos residentes no exterior,
# originando uma estrutura de ponderação diferente da utilizada no IPC.” Os
# ponderadores do IHPC (os únicos que o Eurostat difunde) medem, por
# construção, um universo que inclui turistas. É a mesma contaminação que levou
# a app a abandonar as Contas Nacionais como âncora única.
#
# O INE publica ponderadores do IPC (conceito nacional, sem turistas), mas apenas
# em ine.pt. O IDF é, entre as fontes abertas, a única via para uma estrutura de
# consumo de agregados residentes, e a única que desce ao quintil.
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
# alimentar de agregados maiores, mas como ressalva qualitativa. O IDF
# 2022/2023 permite medi-la.
#
# Método: restringir a agregados **sem crianças dependentes**, onde a escala é
# mais limpa, e comparar o rácio de despesa observado entre “2 ou mais adultos”
# e “1 adulto” com o rácio que cada escala prevê para a mesma composição.
#
# O grupo “2 ou +” reparte-se por resíduo, a partir das contagens do Q.1.3, em
# 72% com dois adultos e 28% com três ou mais. Os 3+ têm 2,144 adultos
# equivalentes na escala OCDE modificada, o que implica 3,288 adultos em média.
#
# O controlo é o que torna o teste convincente: repetindo a conta para a despesa
# **total** (para a qual as escalas foram desenhadas) o desvio inverte-se.
# Ou seja, o problema não é da escala em geral: é da alimentação em particular,
# onde as economias de escala são mais fracas do que na habitação.
ESCALAS_TESTE_FONTE = "INE, IDF 2022/2023, quadros Q.1.3, Q.2.6.a e Q.2.8"

# Composição do grupo “2 ou mais adultos”: (n.º de adultos, fração do grupo)
ESCALAS_TESTE_COMPOSICAO = [(2.0, 0.72), (3.288, 0.28)]

# Rácios observados de despesa entre “2 ou +” e “1 adulto”, sem crianças
ESCALAS_TESTE_RACIO = {
    "alimentar": 1.854,   # 3 066 € / 1 654 € por ano, COICOP 01.1
    "total": 1.498,       # a mesma conta sobre a despesa total
}

# As duas restrições disponíveis são ligeiramente inconsistentes entre si
# (adultos equivalentes médios reconstruídos: 1,435 contra 1,407 publicados),
# pelo que a subestimação fica entre +10% e +13%. Robusta no sinal e na ordem
# de grandeza, não no algarismo.
ESCALAS_TESTE_INTERVALO = (10, 13)

# --------------------------------------------------------------------------
# Acessibilidade alimentar, três limiares que medem coisas diferentes
# --------------------------------------------------------------------------
# “Acessibilidade alimentar” não é uma grandeza única. Consoante o limiar,
# Portugal parece estar muito bem ou bastante mal, com dados oficiais em ambos
# os casos. Daí a regra de apresentação: os três aparecem **sempre juntos**.
#
#   1,9%   privação severa, não pagar uma refeição com carne ou peixe de dois
#           em dois dias. Limiar muito baixo: mede quase fome. Em mínimo de série.
#   14,4%  não conseguir pagar uma dieta nutricionalmente adequada ao menor
#           custo. É o nível intermédio, e é onde está o problema real.
#   14,8%  peso da alimentação no orçamento do 1.º quintil, não é privação,
#           é exposição. Vem de IDF_PESO_ALIMENTAR, acima.
#
# Apresentar só o de 1,9% dá uma leitura indevidamente tranquilizadora: sugere
# um problema de 2% da população, quando por um limiar nutricionalmente
# defensável são 14%.
#
# O SOFI é publicado em PDF, não em API, os valores abaixo são transcritos dos
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

# A DECO PROteste publica o cabaz essencial todas as quartas-feiras. Catorze
# dias tolera uma semana em atraso e apanha a segunda.
LIMITE_DIAS_DECO = 14

# O SOFI é anual, publicado a meio do ano seguinte ao de referência. Dois anos
# de distância do último ano da série significa que houve uma edição por
# incorporar.
LIMITE_ANOS_SOFI = 2

# --------------------------------------------------------------------------
# Prazos de validade das séries obtidas por API
# --------------------------------------------------------------------------
# A auditoria de 10.08.2026 (D4) criou a verificação de frescura e apontou-a ao
# SOFI e ao Observatório, com o argumento de que são as fontes **sem** API. A
# conclusão implícita, que as séries com API não têm esse problema, porque a
# rede avisaria, estava errada, e custou sete meses de dados desatualizados:
# uma série arquivada responde com HTTP 200 e simplesmente deixa de avançar
# (auditoria de 11.08.2026, E1 e E3).
#
# O limite de cada série é o seu **desfasamento normal de publicação mais um
# ciclo**. Um prazo uniforme não serviria: acusaria de velhas as fontes que são
# lentas por construção, as Contas Nacionais têm dois anos de desfasamento e
# está certo que tenham. O que se quer apanhar é a série que **parou**, não a
# série que é lenta.
#
# Em dias, para que o cálculo não dependa da aritmética de calendário.
LIMITES_FRESCURA = {
    "indice": (60, "O índice completo, com todas as classes, sai por volta do "
                   "dia 17 do mês seguinte ao de referência. Sessenta dias "
                   "tolera um mês em atraso e apanha o segundo."),
    "variacoes": (60, "Mesma publicação do índice, sai no mesmo momento."),
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
    "salario_minimo": (260, "Semestral, janeiro e julho. Oito meses e meio "
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

# Pessoas, em milhões, Portugal
SOFI_MILHOES = {2017: 2.3, 2019: 1.6, 2020: 1.7, 2021: 1.6,
                2022: 1.8, 2023: 1.6, 2024: 1.5, 2025: 1.5}

# --------------------------------------------------------------------------
# Metadados institucionais
# --------------------------------------------------------------------------
ORGANISMO = "Secretaria-Geral do Governo"
UNIDADE = "DSSD · Unidade de Pesquisa e Estatísticas"
# Reescrito em 31.08.2026. A versão anterior dizia que "o valor de referência
# do cabaz e as taxas de IVA são parâmetros do utilizador", e nenhuma das duas
# metades se mantinha: o valor de referência passou a vir da `ancora_oficial`
# (IDF e Contas Nacionais), fora do alcance do utilizador, e a taxa atual está
# bloqueada no editor, que só aceita a do cenário. Dizia também que os dados vêm
# todos em direto do Eurostat, quando a DECO e o Observatório do GPP são
# recolhas datadas lidas de CSV. E "cabaz" tinha passado a designar outra coisa
# na aplicação, o cabaz da DECO, pelo que a palavra confundia dois conceitos.
RODAPE = (
    "Ferramenta de trabalho interno. Não constitui posição oficial da "
    "Secretaria-Geral do Governo. Os dados do Eurostat são obtidos em direto; "
    "os das restantes fontes provêm de recolhas datadas e identificadas em cada "
    "quadro. As taxas de IVA do cenário e os restantes parâmetros do simulador "
    "são definidos pelo utilizador, e os resultados são condicionais à "
    "repercussão assumida. Os valores carecem de reconfirmação junto das fontes "
    "primárias antes de utilização em suporte à decisão ou em comunicação "
    "pública."
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


MESES_PT_EXTENSO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                    "julho", "agosto", "setembro", "outubro", "novembro",
                    "dezembro"]


def mes_extenso(periodo) -> str:
    """
    Converte '2026-06' em 'junho de 2026'.

    A forma curta (`mes_pt`) serve os cartões e a barra de estado, onde o espaço
    manda. Esta serve as linhas de proveniência, que são para ler devagar e para
    citar fora da aplicação, e onde o Livro de Estilo da SGGov pede a data por
    extenso.
    """
    try:
        ano, mes = str(periodo).split("-")[:2]
        return f"{MESES_PT_EXTENSO[int(mes) - 1]} de {ano}"
    except (ValueError, IndexError):
        return str(periodo)


def mes_homologo(periodo) -> str:
    """
    O mesmo mês do ano anterior, por extenso: '2026-06' devolve 'junho de 2025'.

    Existe para que as secções possam nomear **os dois extremos** da janela
    homóloga. “Últimos 12 meses” não diz de que doze meses se trata, e a data em
    falta é justamente a que o leitor precisa para verificar o número na fonte.
    """
    try:
        ano, mes = str(periodo).split("-")[:2]
        return f"{MESES_PT_EXTENSO[int(mes) - 1]} de {int(ano) - 1}"
    except (ValueError, IndexError):
        return str(periodo)


def euro(valor, casas: int = 2) -> str:
    """Formata em euros com convenção portuguesa (vírgula decimal)."""
    if valor is None:
        return "—"
    txt = f"{valor:,.{casas}f}".replace(",", "\u00a0").replace(".", ",")
    return f"{txt} €"


def percentagem(valor, casas: int = 1, sinal: bool = True) -> str:
    """
    Percentagem à portuguesa: vírgula decimal e **símbolo colado ao número**.

    O Livro de Estilo da SGGov, E.3, é explícito: o símbolo segue o número sem
    espaço. Como quase todas as percentagens da aplicação passam por aqui, é
    esta linha que decide a conformidade do conjunto (13.08.2026).
    """
    if valor is None:
        return "—"
    pre = "+" if (sinal and valor > 0) else ""
    return f"{pre}{valor:.{casas}f}".replace(".", ",") + "%"


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
