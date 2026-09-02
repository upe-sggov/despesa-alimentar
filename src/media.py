"""
Análise mediática do cabaz alimentar: registo de casos e apuramentos.

Este módulo guarda o levantamento mediático e calcula o que dele se deriva. Não
desenha nada: o separador da aplicação consome estas estruturas e estas funções.
A separação existe pela mesma razão que a de `calculos.py`, poder testar os
apuramentos sem levantar a interface.

## O que este levantamento é

Um levantamento **amostral e avaliativo** de peças noticiosas sobre o cabaz
alimentar e sobre os lucros da distribuição, entre março de 2023 e agosto de
2026. Amostral: não é um retrato exaustivo da cobertura, e nenhuma contagem aqui
apurada deve ser lida como quota de cobertura. Avaliativo: cada caso traz um
juízo da UPE sobre a distância entre o que a peça afirma e o que os dados
disponíveis sustentam, e esse juízo é da UPE, não da fonte citada (perímetro
fixado com a Inês, 02.09.2026).

## Unidade de análise

A **peça noticiosa**. A Frente 2 cataloga sobretudo declarações (cartas,
conferências de resultados, comunicados à CMVM, ações de rua), e nesses casos a
declaração entra como atributo da peça que a veicula: `ator` diz quem falou,
`orgao` diz quem publicou. Sem isto as duas frentes não eram somáveis, porque
uma contava textos e a outra contava bocas.

## Período e as suas duas escalas

O levantamento sistemático cobre fevereiro a agosto de 2026. O bloco de março de
2023 entra por ser a génese documentável do IVA Zero (Lei n.º 17/2023, de 14 de
abril), e os casos de 2024 entram por fecharem o par de discurso empresarial.
São escalas de densidade diferente, e por isso `CASOS_DENSOS` isola a janela
onde a contagem tem algum significado relativo.

## Proveniência dos registos

Três ficheiros de trabalho da UPE, de 24 de agosto de 2026 (Frentes 1 e 2) e de
30 de julho de 2026 (Frente 3), mais um rascunho de apresentação de 26 de agosto
que já continha casos ausentes dos três ficheiros. O campo `registo` diz, para
cada caso, de onde veio. A numeração `F1 #N` é a do rascunho de apresentação,
que renumerou por ordem de aparição; a numeração original de cada ficheiro fica
em `registo`, para que a verificação possa voltar à linha certa.
"""

from __future__ import annotations

from datetime import date

# ==========================================================================
# Metadados do levantamento
# ==========================================================================
PERIODO = (date(2023, 3, 2), date(2026, 8, 26))

#: Janela em que a recolha foi sistemática. Fora dela a amostra é deliberadamente
#: esparsa (génese do IVA Zero e ciclos de resultados anuais), e comparar
#: contagens entre as duas janelas não significa nada.
JANELA_DENSA = (date(2026, 2, 16), date(2026, 8, 26))

FONTES_REGISTO = (
    "UPE/SGGov, «Varrimento mediático: cabaz alimentar / inflação alimentar», "
    "24 de agosto de 2026 (Frente 1).",
    "UPE/SGGov, «Lucros das distribuidoras: reações políticas e consistência do "
    "discurso», 24 de agosto de 2026 (Frente 2).",
    "UPE/SGGov, «Peso da alimentação no orçamento das famílias», 30 de julho de "
    "2026 (Frente 3).",
    "UPE/SGGov, rascunho de apresentação «Análise mediática», 26 de agosto de "
    "2026 (casos de 11, 21 e 26 de agosto ausentes dos ficheiros acima).",
)

#: Data em que o conflito no Médio Oriente recomeçou. Serve de referência ao
#: apuramento da latência causal: é o acontecimento a que as peças atribuem a
#: subida de preços. Consta das observações do caso F1 #5 do ficheiro da Frente 1.
CHOQUE_GEOPOLITICO = date(2026, 2, 28)

# ==========================================================================
# Vocabulário controlado
# ==========================================================================
# `sinal` responde à pergunta que o gabinete faz primeiro: a peça afasta-se dos
# dados, acompanha-os, ou não é sequer uma afirmação testável? É o campo que
# suporta qualquer contagem agregada. `classe` é o detalhe, e existe porque
# "afasta-se" tem formas muito diferentes, que pedem respostas diferentes.
SINAIS = {
    "desvio": "Afasta-se dos dados disponíveis",
    "controlo": "Consistente com os dados (caso de controlo)",
    "exemplo": "Causalidade sustentada em dados (contraste positivo)",
    "nao_testavel": "Não é uma afirmação testável contra dados",
}

CLASSES = {
    # Frente 1, peças noticiosas
    "causalidade_nao_sustentada": "Causalidade não sustentada",
    "projecao_como_facto": "Projeção apresentada como facto",
    "causas_sem_quantificacao": "Agregação de causas sem quantificação",
    "moldura_instavel": "Moldura internacional instável",
    "metricas_incomparaveis": "Métricas ou janelas temporais tratadas como comparáveis",
    "volatilidade_como_tendencia": "Volatilidade semanal tratada como tendência",
    "omissao_de_dado": "Omissão de dado relevante presente na própria peça",
    "autoridade_nao_verificavel": "Afirmação de autoridade não verificável",
    "contradicao_nao_reconciliada": "Contradição entre fontes não reconciliada",
    "indicadores_divergentes": "Pluralidade de indicadores com leituras divergentes",
    "replicacao_de_agencia": "Reporte de rotina replicado entre órgãos",
    "sem_desvio": "Sem desvio relevante",
    "causalidade_sustentada": "Causalidade sustentada com dados",
    # Frente 2, declarações
    "confirmada": "Afirmação confirmada pelos dados",
    "confirmada_incompleta": "Afirmação confirmada, mas incompleta",
    "moldura_seletiva": "Afirmação parcialmente confirmada, moldura seletiva",
    "periodo_mal_atribuido": "Base numérica correta, período mal atribuído",
    "por_verificar": "Afirmação anterior à divulgação dos dados que citaria",
    "metricas_sem_reconciliacao": "Duas métricas diferentes citadas sem reconciliação",
    "em_disputa": "Classificação em disputa, por resolver",
    "reaccao_nao_testavel": "Reação política, sindical ou de leitor",
    "dado_certo_causa_por_verificar": "Dado financeiro confirmado, ligação causal por verificar",
    # Frente 3, contexto orçamental
    "contexto_orcamental": "Contexto de pressão orçamental, sem alegação a confrontar",
}

TIPOS_EMISSOR = {
    "imprensa": "Imprensa",
    "politico": "Ator político",
    "empresa": "Empresa ou associação empresarial",
    "sindicato": "Estrutura sindical",
    "leitor": "Leitor ou consumidor",
    "governo": "Governo",
    "oficial": "Entidade oficial",
}

#: A que fonte a peça vai buscar o número que a sustenta. É o campo que responde
#: à pergunta de quem define a agenda noticiosa do tema.
ANCORAS = {
    "deco": "DECO PROteste (cabaz semanal)",
    "ine_eurostat": "INE ou Eurostat (índices oficiais)",
    "gpp": "GPP e INE (produção e comércio externo)",
    "asae": "ASAE (fiscalização de margens)",
    "empresa": "Contas das empresas (CMVM, resultados)",
    "drciq": "DRCIQ Madeira (Cabazram)",
    "jrc": "Centro Comum de Investigação da Comissão Europeia",
    "bdp": "Banco de Portugal",
    "sondagem": "Sondagem ou estudo de mercado",
    "nenhuma": "Sem âncora quantitativa identificada",
}

# ==========================================================================
# Os casos
# ==========================================================================
# Cada entrada é uma peça. Campos:
#   id            numeração do rascunho de apresentação, que é a que o separador mostra
#   registo       linha de origem no ficheiro de trabalho, para verificação
#   frente        1 cabaz, 2 lucros e discurso, 3 peso orçamental
#   data          ISO, primeira data quando o caso cobre mais do que um dia
#   orgao         quem publicou
#   ator          quem falou, quando não coincide com quem publicou
#   tipo_emissor  ver TIPOS_EMISSOR
#   titulo        título da peça, ou descrição da ocasião quando não há título
#   afirmacao     o que a peça ou a declaração sustenta
#   contraponto   o dado com que a UPE a confrontou
#   fonte         proveniência do contraponto
#   sinal/classe  o juízo, ver SINAIS e CLASSES
#   ancora        ver ANCORAS
#   replicacao    número de órgãos que publicaram a mesma peça, 1 quando é única
#   contexto_titulo  onde vive a comparação de longo prazo: "titulo", "corpo", None
#   ligacao       URL, ou None quando é recorte de imprensa em papel
#   nota          observação da UPE
CASOS: list[dict] = [
    # ---------------------------------------------------------------- Frente 1
    {
        "id": "F1 #1", "registo": "varrimento #1", "frente": 1,
        "data": "2026-02-17", "orgao": "Euronews", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Cabaz alimentar atinge valor mais alto dos últimos 4 anos, "
                  "mas não é só em Portugal que preços sobem",
        "afirmacao": "Enquadra Portugal como estando \"em linha com a média da "
                     "UE\", com inflação alimentar de 2,8% em 2025 segundo o Eurostat.",
        "contraponto": "Leituras do Eurostat de julho de 2026 colocam Portugal "
                       "entre os poucos países da Zona Euro onde a inflação "
                       "homóloga não aliviou em junho.",
        "fonte": "SAPO, 19 de julho de 2026 (caso F1 #5).",
        "sinal": "desvio", "classe": "moldura_instavel",
        "ancora": "deco", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://pt.euronews.com/business/2026/02/17/cabaz-alimentar-atinge-valor-mais-alto-dos-ultimos-quatro-anos",
        "nota": "Não é um erro factual isolado. Mostra como a comparação entre "
                "Portugal e a UE muda de sinal consoante a leitura mensal "
                "escolhida, o que facilita usos seletivos da mesma fonte.",
    },
    {
        "id": "F1 #2", "registo": "varrimento #2", "frente": 1,
        "data": "2026-03-12", "orgao": "Jornal de Negócios", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Citrinos, legumes e peixe. Mau tempo pressiona preços",
        "afirmacao": "Integra no lead, como dado adquirido, que \"a guerra no "
                     "Irão vai agravar ainda mais a inflação alimentar\".",
        "contraponto": "A peça está bem ancorada em dados do INE para a pressão "
                       "do mau tempo. A ligação ao conflito, à data, é uma "
                       "projeção sem dados de suporte no próprio texto. Dados de "
                       "produção do GPP mostram, para vários dos produtos "
                       "visados, subidas maiores na produção do que no consumidor "
                       "(cenoura +110,7% contra +66,2%; batata +96,2% contra "
                       "+77,1%), o que aponta para pressão a montante da cadeia.",
        "fonte": "Leitura interna do artigo; GPP, Observatório de Preços "
                 "Agroalimentar, verificação de 7 de agosto de 2026.",
        "sinal": "desvio", "classe": "projecao_como_facto",
        "ancora": "ine_eurostat", "replicacao": 1, "contexto_titulo": None,
        "ligacao": None,
        "nota": "Peça de resto rigorosa, que cita o INE, a CAP e o comissário "
                "europeu. O problema está confinado a uma frase do lead.",
    },
    {
        "id": "F1 #3", "registo": "varrimento #4", "frente": 1,
        "data": "2026-03-27", "orgao": "PÚBLICO", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Cabaz alimentar nunca esteve tão caro, e o cenário \"não é animador\"",
        "afirmacao": "Atribui o recorde a uma combinação de fatores (guerra, "
                     "clima, procura de proteína) sem os hierarquizar nem "
                     "quantificar.",
        "contraponto": "O INE mostra inflação de alimentos não transformados "
                       "mais moderada do que a variação acumulada do cabaz da "
                       "DECO no mesmo período. Na decomposição do GPP, o ovo "
                       "sobe de forma quase idêntica na produção e no consumo "
                       "(+98% e +101%), um choque de origem bem transmitido, "
                       "mas na pescada o preço na produção desceu 22,8% "
                       "enquanto ao consumidor subiu 23,4%.",
        "fonte": "Nota técnica UPE/SGGov de 21 de julho de 2026; GPP, "
                 "verificação de 7 de agosto de 2026.",
        "sinal": "desvio", "classe": "causas_sem_quantificacao",
        "ancora": "deco", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.publico.pt/2026/03/27/economia/noticia/cabaz-alimentar-tao-caro-cenario-nao-animador-2169443",
        "nota": "Inclui declarações da APED, boa prática de contraditório, mas "
                "sem as confrontar com dados de inflação oficiais. A divergência "
                "entre produção e consumo na pescada não é explorada por nenhuma "
                "peça do levantamento.",
    },
    {
        "id": "F1 #4", "registo": "varrimento #6", "frente": 1,
        "data": "2026-04-09", "orgao": "Diário de Notícias", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Guerra eleva preço do cabaz alimentar para recorde de 257,95 euros",
        "afirmacao": "O título atribui o novo recorde à guerra no Médio Oriente.",
        "contraponto": "A própria APED afirmou que os preçários de janeiro já "
                       "estavam contratualizados no quarto trimestre de 2025, "
                       "antes do conflito. A série sobe de forma consistente "
                       "desde 2022 (+37,42% acumulado). As maiores subidas "
                       "acumuladas (ovos +98% a +101%, batata +77%, cenoura "
                       "+66%) já vinham em trajetória de subida bem antes de "
                       "fevereiro de 2026.",
        "fonte": "ECO, declarações de Gonçalo Lobo Xavier, diretor-geral da "
                 "APED, abril de 2026; GPP, verificação de 7 de agosto de 2026.",
        "sinal": "desvio", "classe": "causalidade_nao_sustentada",
        "ancora": "deco", "replicacao": 1, "contexto_titulo": None,
        "ligacao": None,
        "nota": "O caso mais claro do levantamento: o título propõe uma causa "
                "que os dados citados no resto do artigo, e uma fonte do próprio "
                "setor, não confirmam.",
    },
    {
        "id": "F1 #5", "registo": "varrimento #13", "frente": 1,
        "data": "2026-07-19", "orgao": "Dinheiro Vivo (via SAPO)", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Portugal, Espanha, Lituânia e Chipre são os únicos países do "
                  "euro onde a inflação não alivia",
        "afirmacao": "Agrega quatro países sob o rótulo \"a inflação não alivia\" "
                     "e atribui a persistência à guerra entre o Irão e os EUA.",
        "contraponto": "O Eurostat citado no próprio artigo mostra trajetórias "
                       "distintas entre os quatro países. A persistência "
                       "portuguesa já era visível em abril, antes de o conflito "
                       "recomeçar. Contrasta com a leitura de fevereiro de 2026, "
                       "que colocava Portugal em linha com a média da UE.",
        "fonte": "Euronews, 17 de fevereiro de 2026 (caso F1 #1).",
        "sinal": "desvio", "classe": "moldura_instavel",
        "ancora": "ine_eurostat", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://sapo.pt/artigo/portugal-espanha-lituania-e-chipre-sao-os-unicos-paises-do-euro-onde-a-inflacao-nao-alivia-6a5d3e8e4f27158af594360a",
        "nota": "A comparação internacional de Portugal muda de sinal ao longo "
                "do ano sem que as peças se remetam umas às outras.",
    },
    {
        "id": "F1 #6", "registo": "varrimento #17", "frente": 1,
        "data": "2026-07-30", "orgao": "Diário de Notícias", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Preço do cabaz alimentar aumenta 4,8% desde janeiro para mais "
                  "de 253 euros",
        "afirmacao": "Peça classificada na etiqueta editorial \"GUERRA\", mas o "
                     "corpo do texto não atribui o aumento semanal à guerra: "
                     "descreve-o com fatores genéricos de procura e oferta.",
        "contraponto": "Cabaz em 253,47 euros, mais 2,18 euros face à semana "
                       "anterior, mais 11,65 euros (4,8%) desde o início do ano, "
                       "mais 65,77 euros (35%) desde janeiro de 2022. Os produtos "
                       "que a peça destaca (bacalhau, robalo, novilho, ovos) são "
                       "os que o GPP também identifica como de maior subida ao "
                       "consumidor no mesmo período.",
        "fonte": "O próprio artigo; GPP, verificação de 7 de agosto de 2026.",
        "sinal": "controlo", "classe": "sem_desvio",
        "ancora": "deco", "replicacao": 2, "contexto_titulo": "titulo",
        "ligacao": None,
        "nota": "Peça sóbria e bem detalhada, com boa distinção entre curto e "
                "longo prazo, e das poucas em que a comparação de longo prazo "
                "chega ao título. O desvio está na etiqueta editorial, não no "
                "texto: o rótulo sugere uma causa que o corpo não sustenta.",
    },
    {
        "id": "F1 #7", "registo": "varrimento #22 e recorte de 26.08.2026",
        "frente": 1,
        "data": "2026-08-07", "orgao": "Diário de Notícias", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Balança comercial nos cereais está mais desequilibrada; "
                  "Calor e seca estão a pressionar culturas de verão",
        "afirmacao": "Explica a pressão nos preços alimentares pela dependência "
                     "externa de cereais (Portugal importa cerca de 80% dos que "
                     "consome), agravada por seca e alterações climáticas.",
        "contraponto": "Confirmado nas fontes primárias que a própria peça cita: "
                       "défice comercial de bens de 2,5 para 2,8 mil milhões de "
                       "euros entre janeiro e maio de 2026; mais de 472 milhões "
                       "de euros de prejuízos por cheias e tempestades; área "
                       "semeada de cereais de outono e inverno reduzida a "
                       "metade; produção de milho a cair cerca de 15%. Reforçado "
                       "a 26 de agosto pelo relatório do Centro Comum de "
                       "Investigação da Comissão Europeia sobre calor e seca.",
        "fonte": "GPP, boletins mensais; INE; Centro Comum de Investigação da "
                 "Comissão Europeia, relatório de agosto de 2026.",
        "sinal": "exemplo", "classe": "causalidade_sustentada",
        "ancora": "gpp", "replicacao": 1, "contexto_titulo": "corpo",
        "ligacao": None,
        "nota": "Contraste positivo do levantamento. Ao contrário dos casos F1 "
                "#2, #3, #4 e #6, hierarquiza e quantifica uma causa concreta "
                "com dados de fonte primária. Só no fim cita o cabaz da DECO, "
                "como contexto, e não como ponto de partida.",
    },
    {
        "id": "F1 #8", "registo": "varrimento #11", "frente": 1,
        "data": "2026-06-25", "orgao": "Diário de Notícias", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Valor do cabaz alimentar desce 87 cêntimos esta semana",
        "afirmacao": "Reporta a descida semanal com sobriedade, sem atribuição "
                     "causal, incluindo a estimativa do BCE para a inflação na "
                     "Zona Euro.",
        "contraponto": "Consistente com os dados disponíveis à data.",
        "fonte": "O próprio artigo. Caso de controlo, sem contraponto externo "
                 "necessário.",
        "sinal": "controlo", "classe": "sem_desvio",
        "ancora": "deco", "replicacao": 1, "contexto_titulo": "corpo",
        "ligacao": None,
        "nota": "Incluído como termo de comparação: mostra que a distorção "
                "identificada noutros casos não é sistemática a todos os órgãos "
                "nem a todas as datas.",
    },
    {
        "id": "F1 #9", "registo": "varrimento #12", "frente": 1,
        "data": "2026-07-08", "orgao": "Observador e outros (agência)",
        "ator": None, "tipo_emissor": "imprensa",
        "titulo": "Cabaz alimentar volta a subir 3,08 euros para 256,71 euros",
        "afirmacao": "Apresenta a variação acumulada desde janeiro lado a lado "
                     "com a variação semanal, sem assinalar que nenhuma delas é "
                     "comparável com a taxa de inflação homóloga do INE.",
        "contraponto": "INE: inflação de alimentos não transformados em 5,1% a "
                       "5,2% em variação homóloga, junho de 2026. É uma métrica "
                       "distinta da variação acumulada do cabaz desde 1 de janeiro.",
        "fonte": "ECO, 10 de julho de 2026, sobre dados do INE.",
        "sinal": "desvio", "classe": "metricas_incomparaveis",
        "ancora": "deco", "replicacao": 6, "contexto_titulo": "corpo",
        "ligacao": "https://observador.pt/2026/07/08/deco-proteste-cabaz-alimentar-volta-a-subir-308-euros-para-25671-euros/",
        "nota": "Peça replicada quase palavra por palavra por vários órgãos. O "
                "mesmo enquadramento repete-se em dezenas de publicações.",
    },
    {
        "id": "F1 #10", "registo": "varrimento #14", "frente": 1,
        "data": "2026-07-22", "orgao": "SOL, DNotícias e outros (agência)",
        "ator": None, "tipo_emissor": "imprensa",
        "titulo": "Cabaz alimentar tem maior descida do ano e fica 5,17 euros "
                  "mais barato numa semana",
        "afirmacao": "O título dá destaque à maior descida semanal do ano.",
        "contraponto": "O mesmo cabaz continua 36,82% mais caro do que no início "
                       "de 2022 e 4,73% mais caro do que há um ano. Ambos os "
                       "dados estão no próprio texto, secundarizados face ao título.",
        "fonte": "O próprio artigo.",
        "sinal": "desvio", "classe": "volatilidade_como_tendencia",
        "ancora": "deco", "replicacao": 4, "contexto_titulo": "corpo",
        "ligacao": "https://sol.iol.pt/sociedade/noticias/cabaz-alimentar-tem-maior-descida-do-ano-e-fica-5-17-euros-mais-barato-numa-semana/20260722/6a60bb020cf2f6a1a1e71a48",
        "nota": "Espelha, em sentido inverso, o padrão das semanas de subida: o "
                "enquadramento do título segue sempre a variação da última "
                "semana, independentemente da tendência de fundo.",
    },
    {
        "id": "F1 #11", "registo": "varrimento #15", "frente": 1,
        "data": "2026-07-23", "orgao": "SIC Notícias", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Preço do cabaz alimentar regista maior descida desde o início do ano",
        "afirmacao": "Republica, um dia depois, a mesma descida semanal já "
                     "noticiada a 22 de julho por três outros órgãos, com o "
                     "mesmo enquadramento no título.",
        "contraponto": "O cabaz continua 9,46 euros (3,91%) mais caro do que no "
                       "início do ano. O dado consta da nota original da DECO, "
                       "mas só ganha destaque no subtítulo ou no corpo, nunca no "
                       "título, em nenhuma das versões.",
        "fonte": "Agroportal, mesma nota da DECO, cópia de agência.",
        "sinal": "desvio", "classe": "volatilidade_como_tendencia",
        "ancora": "deco", "replicacao": 4, "contexto_titulo": "corpo",
        "ligacao": "https://sicnoticias.pt/economia/2026-07-23-preco-do-cabaz-alimentar-regista-maior-descida-desde-o-inicio-do-ano-c11280f1",
        "nota": "Mostra que o mesmo enquadramento se replica em ciclos de "
                "publicação diferentes, e não apenas entre órgãos no mesmo dia.",
    },
    {
        "id": "F1 #12", "registo": "varrimento #19", "frente": 1,
        "data": "2026-08-19",
        "orgao": "Observador, Folha Nacional, Diário de Coimbra, Diário de "
                 "Aveiro, Diário de Leiria, Qualfood e outros (agência)",
        "ator": None, "tipo_emissor": "imprensa",
        "titulo": "Cabaz alimentar sobe 1,48 euros na última semana para 253,55 euros",
        "afirmacao": "Peça de rotina, replicada quase palavra por palavra por "
                     "pelo menos seis órgãos no mesmo dia.",
        "contraponto": "Cabaz em 253,55 euros, mais 1,48 euros face à semana "
                       "anterior, que tinha descido 1,53 euros; mais 4,85% desde "
                       "o início do ano; mais 5,08% face a um ano antes. Dados "
                       "consistentes entre todas as réplicas encontradas.",
        "fonte": "O próprio artigo e as suas réplicas.",
        "sinal": "controlo", "classe": "replicacao_de_agencia",
        "ancora": "deco", "replicacao": 8, "contexto_titulo": "corpo",
        "ligacao": "https://observador.pt/2026/08/19/cabaz-alimentar-sobe-148-euros-na-ultima-semana-para-25355-euros/",
        "nota": "Peça sóbria e bem contextualizada. O interesse está na escala "
                "da replicação: mais órgãos do que em qualquer outro caso do "
                "mesmo padrão, todos com o texto praticamente idêntico. Um "
                "comentário de leitor anexo responde com ceticismo a discurso "
                "oficial sobre melhoria das condições económicas, sem que a "
                "declaração visada esteja identificada.",
    },
    {
        "id": "F1 #13", "registo": "varrimento #24", "frente": 1,
        "data": "2026-08-13", "orgao": "Jornal de Notícias e Correio da Manhã",
        "ator": None, "tipo_emissor": "imprensa",
        "titulo": "Cabaz alimentar da DECO desce para 252 euros",
        "afirmacao": "Reporta a descida semanal de 1,53 euros, para 252,07 euros, "
                     "entre 5 e 12 de agosto.",
        "contraponto": "Sem contraponto adicional. É o mesmo reporte semanal de "
                       "rotina já documentado noutros casos.",
        "fonte": "PressReader, recortes de 13 de agosto de 2026.",
        "sinal": "controlo", "classe": "replicacao_de_agencia",
        "ancora": "deco", "replicacao": 2, "contexto_titulo": "corpo",
        "ligacao": None,
        "nota": "Os dois órgãos citam o mesmo detalhe de produto (douradinhos "
                "+13%, couve-coração +12%, flocos de cereais +11%). Nota "
                "positiva: ao contrário de muitos reportes de rotina, mostram "
                "produtos individuais a subir dentro de um cabaz que desceu no "
                "total, o que ajuda a explicar por que a descida não é sentida "
                "por quem compra sobretudo esses produtos.",
    },
    {
        "id": "F1 #14", "registo": "varrimento #10", "frente": 1,
        "data": "2026-06-18", "orgao": "Diário de Notícias", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Portugal entre os países com inflação mais baixa, mas cabaz "
                  "alimentar volta a encarecer",
        "afirmacao": "O título constrói uma aparente contradição entre inflação "
                     "mais baixa e cabaz a encarecer.",
        "contraponto": "Compara o índice harmonizado de maio, em variação "
                       "homóloga, com a variação semanal do cabaz em junho. A "
                       "variação homóloga do próprio cabaz (6,14%) não é tão "
                       "díspar da inflação alimentar oficial quanto o título "
                       "sugere.",
        "fonte": "O próprio artigo: ambos os valores constam do texto original.",
        "sinal": "desvio", "classe": "metricas_incomparaveis",
        "ancora": "deco", "replicacao": 1, "contexto_titulo": None,
        "ligacao": None,
        "nota": "O corpo do texto é mais cuidadoso do que o título. O problema "
                "concentra-se no enquadramento do título. O caso F1 #17 dá a "
                "explicação de fundo que falta aqui.",
    },
    {
        "id": "F1 #15", "registo": "varrimento #20", "frente": 1,
        "data": "2023-03-09", "orgao": "PÚBLICO", "ator": "APED",
        "tipo_emissor": "imprensa",
        "titulo": "APED afirma que retalho alimentar \"não aumentou\" margens de "
                  "comercialização",
        "afirmacao": "A APED sustenta margens de 2% a 3% no retalho alimentar, "
                     "contestando um relatório da ASAE.",
        "contraponto": "O relatório da ASAE de 2023 identificou margens de lucro "
                       "superiores a 50% em certos produtos, em fiscalizações a "
                       "960 operadores. A contradição nunca foi reconciliada "
                       "publicamente entre as duas fontes.",
        "fonte": "PÚBLICO, peça companheira do mesmo dia sobre o relatório da ASAE.",
        "sinal": "desvio", "classe": "contradicao_nao_reconciliada",
        "ancora": "asae", "replicacao": 2, "contexto_titulo": None,
        "ligacao": "https://www.publico.pt/2023/03/09/economia/noticia/aped-afirma-retalho-alimentar-nao-aumentou-margens-comercializacao-2041803",
        "nota": "Fora da janela densa, incluído por ser o precedente direto do "
                "argumento sobre margens contra custos que continua a ser usado "
                "em 2026.",
    },
    {
        "id": "F1 #16", "registo": "varrimento #23", "frente": 1,
        "data": "2026-08-05", "orgao": "Jornal Madeira", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Cabaz de bens essenciais sobe 0,32% na Região; Alimentos 6% "
                  "mais baratos",
        "afirmacao": "Reporta o Cabazram, indicador mensal da Direção Regional "
                     "do Comércio, Indústria e Qualidade da Madeira: 82,53 euros "
                     "em julho (mais 0,32%) e 77,57 euros em agosto (menos 6%).",
        "contraponto": "No mesmo período, o cabaz nacional da DECO estava a "
                       "subir, não a descer: 253,47 euros a 29 de julho e 253,55 "
                       "euros a 19 de agosto. O Cabazram desceu 6% exatamente "
                       "quando o indicador nacional voltava a subir.",
        "fonte": "PressReader; casos F1 #6 e F1 #12 deste levantamento.",
        "sinal": "desvio", "classe": "indicadores_divergentes",
        "ancora": "drciq", "replicacao": 1, "contexto_titulo": None,
        "ligacao": None,
        "nota": "Achado metodológico. O Cabazram tem 26 produtos contra os 63 da "
                "DECO, é mensal e não semanal, regional e não nacional, e a "
                "própria entidade classifica a recolha como piloto, feita em "
                "dois estabelecimentos do Funchal. Nenhum destes cabazes é o "
                "preço da alimentação em Portugal.",
    },
    {
        "id": "F1 #17", "registo": "rascunho de apresentação, 26.08.2026",
        "frente": 1,
        "data": "2026-08-21", "orgao": "Expresso", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Há um ano que os preços dos alimentos estão a subir acima da "
                  "média da Zona Euro",
        "afirmacao": "Desde julho de 2025 que a inflação alimentar em Portugal "
                     "está acima da média da Zona Euro. Em julho de 2026 é a "
                     "terceira mais alta (2,3% contra 1,2%), mas a inflação "
                     "geral fica em linha com a média (3,1% contra 3,0%, 12.º "
                     "lugar em 27).",
        "contraponto": "Confirmado. A peça distingue explicitamente o índice "
                       "harmonizado, usado nas comparações europeias, do índice "
                       "de preços no consumidor nacional.",
        "fonte": "Eurostat, índice harmonizado de preços no consumidor.",
        "sinal": "exemplo", "classe": "causalidade_sustentada",
        "ancora": "ine_eurostat", "replicacao": 1, "contexto_titulo": "titulo",
        "ligacao": "https://expresso.pt/custo-vida/2026-08-19-ha-um-ano-que-os-precos-dos-alimentos-estao-a-subir-acima-da-media-da-zona-euro-15bcdd32",
        "nota": "A peça que explica o paradoxo construído no caso F1 #14, e a "
                "única do levantamento que distingue os dois índices de forma "
                "explícita. É também a peça com mais interações na amostra de "
                "artigos web.",
    },
    {
        "id": "F1 #18", "registo": "varrimento, folha Contexto", "frente": 1,
        "data": "2026-04-01", "orgao": "Diário de Notícias", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Portugal é o país da Zona Euro mais castigado pelos efeitos "
                  "imediatos da guerra",
        "afirmacao": "Atribui à guerra a subida da inflação portuguesa para 2% "
                     "em março, a maior subida mensal entre os 21 países da "
                     "Zona Euro.",
        "contraponto": "Confirmado, e ancorado em dados do período posterior ao "
                       "choque: energia mais 6,7% no mês, alimentos não "
                       "transformados mais 6,4%, com comparação europeia pelo "
                       "índice harmonizado.",
        "fonte": "INE e Eurostat, índice harmonizado de preços no consumidor, "
                 "março de 2026.",
        "sinal": "exemplo", "classe": "causalidade_sustentada",
        "ancora": "ine_eurostat", "replicacao": 1, "contexto_titulo": None,
        "ligacao": None,
        "nota": "O contraexemplo decisivo do levantamento. Atribui à guerra o "
                "mesmo efeito que os casos F1 #2 e F1 #4 lhe atribuem, mas "
                "trinta e dois dias depois do choque e com um mês inteiro de "
                "dados acumulados. Mostra que o que separa uma atribuição "
                "sustentada de uma atribuição infundada não é o tempo decorrido, "
                "é a existência de dados do período posterior ao acontecimento.",
    },
    # ---------------------------------------------------------------- Frente 2
    {
        "id": "F2 #1", "registo": "lucros #5", "frente": 2,
        "data": "2023-03-02", "orgao": "Polígrafo (verificação)",
        "ator": "Pedro Filipe Soares (Bloco de Esquerda)",
        "tipo_emissor": "politico",
        "titulo": "Declaração política na Assembleia da República",
        "afirmacao": "Junta os lucros da Jerónimo Martins e da Sonae (\"quase "
                     "700 milhões\") à subida de 20% nos preços dos alimentos.",
        "contraponto": "O Polígrafo confirmou a soma aproximada (629 milhões de "
                       "euros), mas notou que os dados eram do terceiro "
                       "trimestre de 2022 (Sonae 210 milhões, Jerónimo Martins "
                       "419 milhões), e não do ano completo.",
        "fonte": "Polígrafo, verificação de factos.",
        "sinal": "desvio", "classe": "periodo_mal_atribuido",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://poligrafo.sapo.pt/fact-check/pedro-filipe-soares-alimentos-estao-20-mais-caros-enquanto-jeronimo-martins-e-sonae-tem-lucros-de-quase-e700-milhoes",
        "nota": "O erro é de período e de atribuição, não de ordem de grandeza.",
    },
    {
        "id": "F2 #2", "registo": "rascunho de apresentação, 26.08.2026",
        "frente": 2,
        "data": "2023-03-12", "orgao": "Esquerda.net",
        "ator": "Catarina Martins (Bloco de Esquerda)",
        "tipo_emissor": "politico",
        "titulo": "\"Grande distribuição e banca anunciam os maiores lucros de sempre\"",
        "afirmacao": "Cita a ASAE diretamente e compara as remunerações dos "
                     "presidentes executivos (Cláudia Azevedo, 1,6 milhões de "
                     "euros por ano, nove anos de salário de um trabalhador; "
                     "Pedro Soares dos Santos, 12 milhões, setenta anos) com a "
                     "subida de 50% no preço das cebolas.",
        "contraponto": "Não confrontámos os rácios salariais com os dados de "
                       "remuneração das empresas. A referência à ASAE coincide "
                       "com o relatório citado no caso F1 #15.",
        "fonte": "Por verificar.",
        "sinal": "nao_testavel", "classe": "reaccao_nao_testavel",
        "ancora": "asae", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.esquerda.net/artigo/bloco-quer-combater-radical-desigualdade-que-assalta-o-pais/85524",
        "nota": "Ausente dos ficheiros de trabalho, presente no rascunho de "
                "apresentação. Fica por verificar.",
    },
    {
        "id": "F2 #3", "registo": "lucros #3", "frente": 2,
        "data": "2023-03-15", "orgao": "Abril Abril",
        "ator": "CGTP e CESP, movimento \"Os Mesmos de Sempre a Pagar\"",
        "tipo_emissor": "sindicato",
        "titulo": "Carta aberta entregue na sede da Sonae",
        "afirmacao": "Acusa a presidente executiva da Sonae de \"paternalismo\" "
                     "e de gerir as empresas com \"imoral\" ganância. Lembra que "
                     "os trabalhadores \"sentem na pele\" os preços praticados "
                     "pelos supermercados do próprio grupo.",
        "contraponto": "Mesmo contexto: lucro do grupo Sonae de 342 milhões de "
                       "euros em 2022, anunciado poucos dias antes.",
        "fonte": "Comunicado de resultados da Sonae, março de 2023.",
        "sinal": "nao_testavel", "classe": "reaccao_nao_testavel",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.abrilabril.pt/nacional/os-mesmos-de-sempre-pagar-reagem-ao-paternalismo-da-ceo-da-sonae",
        "nota": "Contraditório político e laboral, não uma afirmação factual a "
                "confrontar com dados. Mostra que a carta da presidente "
                "executiva não ficou sem resposta pública.",
    },
    {
        "id": "F2 #4", "registo": "lucros #6", "frente": 2,
        "data": "2023-04-14", "orgao": "Notícias ao Minuto",
        "ator": "José Gusmão (Bloco de Esquerda, eurodeputado)",
        "tipo_emissor": "politico",
        "titulo": "Publicação no Twitter/X",
        "afirmacao": "Chama \"campeões da desigualdade\" à Jerónimo Martins e à "
                     "Sonae, citando que os presidentes executivos ganham em "
                     "média 36 vezes mais do que os trabalhadores.",
        "contraponto": "Não confrontámos o rácio com dados de remuneração das "
                       "empresas. Insere-se no ciclo de escrutínio posterior aos "
                       "resultados anuais de 2022 de ambas.",
        "fonte": "Por verificar.",
        "sinal": "nao_testavel", "classe": "reaccao_nao_testavel",
        "ancora": "nenhuma", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.noticiasaominuto.com/politica/2297022/jose-gusmao-acusa-jeronimo-martins-e-sonae-de-campeoes-da-desigualdade",
        "nota": "O foco é a desigualdade salarial, não o lucro em si, mas "
                "reforça o mesmo alvo no mesmo período de escrutínio.",
    },
    {
        "id": "F2 #5", "registo": "lucros #13", "frente": 2,
        "data": "2026-05-06", "orgao": "Observador",
        "ator": "José Manuel Pureza (Bloco de Esquerda)",
        "tipo_emissor": "politico",
        "titulo": "Ação de rua em Braga",
        "afirmacao": "Associa o aumento de 7,9% nos lucros da Jerónimo Martins à "
                     "subida de 84% no preço dos ovos: \"a roda da sorte calha "
                     "sempre para os mesmos\".",
        "contraponto": "O valor do lucro está correto: 646 milhões de euros em "
                       "2025, mais 7,9%, anunciados a 19 de março de 2026. A "
                       "ligação causal entre o preço dos ovos e esse lucro é uma "
                       "interpretação política que não verificámos ao nível de "
                       "produto ou de margem.",
        "fonte": "Resultados anuais de 2025 da Jerónimo Martins.",
        "sinal": "desvio", "classe": "dado_certo_causa_por_verificar",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://observador.pt/2026/05/06/bloco-de-esquerda-exige-controlo-de-precos-com-concurso-que-imita-o-preco-certo-e-denuncia-ovos-84-mais-caros/",
        "nota": "É o tipo de cruzamento que a imprensa económica não fez e que a "
                "ação política fez, e foi coberta.",
    },
    {
        "id": "F2 #6", "registo": "lucros #14", "frente": 2,
        "data": "2026-05-20", "orgao": "Funchal Notícias",
        "ator": "PCP (Ricardo Lume, Comité Central)",
        "tipo_emissor": "politico",
        "titulo": "Ação de contacto junto ao Continente, Funchal",
        "afirmacao": "\"Aumento brutal dos lucros das empresas do setor da "
                     "distribuição\", ligado a especulação de preços e a baixos "
                     "salários dos trabalhadores.",
        "contraponto": "O valor do lucro está correto: 247 milhões de euros da "
                       "Sonae, mais 11%, anunciados dois meses antes. A "
                       "caracterização como especulação é uma leitura política "
                       "que não confrontámos com dados de margem por produto.",
        "fonte": "Resultados anuais de 2025 da Sonae.",
        "sinal": "desvio", "classe": "dado_certo_causa_por_verificar",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://funchalnoticias.net/2026/05/20/pcp-denuncia-aumento-brutal-dos-lucros-das-empresas-do-sector-da-distribuicao-assente-nos-baixos-salarios/",
        "nota": "Mesmo padrão do caso anterior, agora do PCP e sobre a Sonae. "
                "Confirma que mais do que um partido fez esta ligação, na mesma "
                "janela de resultados.",
    },
    {
        "id": "F2 #7", "registo": "lucros #15", "frente": 2,
        "data": "2026-06-08", "orgao": "Esquerda.net",
        "ator": "José Manuel Pureza (Bloco de Esquerda)",
        "tipo_emissor": "politico",
        "titulo": "Ação de denúncia à porta da sede da Jerónimo Martins",
        "afirmacao": "\"Os lucros deles são a nossa pobreza\". Cita os 646 "
                     "milhões de euros de lucro e o facto de o presidente "
                     "executivo ganhar 226 vezes mais do que um trabalhador. "
                     "Propõe taxação de lucros extraordinários e controlo "
                     "temporário de preços.",
        "contraponto": "O valor do lucro está confirmado. O rácio salarial de "
                       "226 vezes não foi verificado contra os dados de "
                       "remuneração da empresa.",
        "fonte": "Resultados anuais de 2025 da Jerónimo Martins.",
        "sinal": "desvio", "classe": "dado_certo_causa_por_verificar",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.esquerda.net/artigo/porta-da-jeronimo-martins-pureza-denunciou-duas-faces-da-crise-do-custo-de-vida/98288",
        "nota": "Terceira ação política em três meses sobre os mesmos resultados "
                "anuais, depois de Braga e do Funchal. Mostra uma campanha "
                "sustentada, não um episódio isolado.",
    },
    {
        "id": "F2 #8", "registo": "lucros #17", "frente": 2,
        "data": "2026-08-02", "orgao": "Esquerda.net", "ator": "Redação",
        "tipo_emissor": "imprensa",
        "titulo": "Sonae e Jerónimo Martins somam lucros milionários enquanto "
                  "famílias enfrentam aumento do custo de vida",
        "afirmacao": "Liga os resultados do primeiro semestre de 2026 ao aumento "
                     "do custo de vida das famílias, acrescentando o resultado "
                     "do BCP (565,8 milhões, mais 12,7%) e a subida da Euribor "
                     "no mesmo pacote noticioso.",
        "contraponto": "Os valores de lucro estão corretos e coincidem com o "
                       "caso F2 #16. A peça soma três indicadores financeiros "
                       "distintos sob um único título de custo de vida.",
        "fonte": "Resultados do primeiro semestre de 2026.",
        "sinal": "desvio", "classe": "dado_certo_causa_por_verificar",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.esquerda.net/artigo/sonae-e-jeronimo-martins-somam-lucros-milionarios-enquanto-familias-enfrentam-aumento-do",
        "nota": "É uma montagem editorial, não uma alegação factual isolada a "
                "testar. Mostra o mesmo resultado semestral a alimentar a "
                "narrativa mais de um mês depois de divulgado.",
    },
    {
        "id": "F2 #9", "registo": "lucros #19", "frente": 2,
        "data": "2026-08-13", "orgao": "Jornal de Notícias",
        "ator": "José Maria Silva (carta de leitor)", "tipo_emissor": "leitor",
        "titulo": "\"Lucros obscenos\"",
        "afirmacao": "Agrupa banca, energia, comunicações, distribuição alimentar "
                     "e medicamentos como setores de \"lucros avultados\" que "
                     "deveriam ser taxados. Cita os cinco maiores bancos, "
                     "incluindo a CGD, com lucro diário de 14 milhões de euros.",
        "contraponto": "O valor de lucro diário da banca não foi confrontado com "
                       "dados oficiais. Um comentário anexo de outro leitor "
                       "resume: \"O cabaz alimentar está ao nível dos "
                       "combustíveis, sobe 3 numa semana, desce 1 na semana "
                       "seguinte\", uma generalização qualitativa que não "
                       "confirmámos contra a série semanal da DECO.",
        "fonte": "Por verificar.",
        "sinal": "nao_testavel", "classe": "reaccao_nao_testavel",
        "ancora": "nenhuma", "replicacao": 1, "contexto_titulo": None,
        "ligacao": None,
        "nota": "Primeiro registo da voz do leitor no levantamento, em vez de um "
                "ator político, sindical ou empresarial. Mostra a narrativa dos "
                "lucros excessivos a circular espontaneamente, agrupando a "
                "distribuição alimentar com outros setores sem distinguir "
                "margens nem modelos de negócio, a mesma agregação sem "
                "hierarquização que aparece em peças jornalísticas.",
    },
    {
        "id": "F2 #10", "registo": "lucros #1", "frente": 2,
        "data": "2023-03-09", "orgao": "ECO",
        "ator": "Cláudia Azevedo (presidente executiva da Sonae)",
        "tipo_emissor": "empresa",
        "titulo": "Carta aos trabalhadores do Continente",
        "afirmacao": "Alerta para uma \"campanha de desinformação\" contra o "
                     "setor da distribuição e nega que os hipermercados e "
                     "supermercados sejam \"os culpados da inflação\".",
        "contraponto": "O grupo Sonae fechou 2022 com lucro de 342 milhões de "
                       "euros, mais 27,7%. A unidade de retalho alimentar caiu "
                       "17,8%, para 179 milhões, com margem de 2,7%.",
        "fonte": "Contas de 2022 da Sonae; ECO, março de 2023.",
        "sinal": "desvio", "classe": "moldura_seletiva",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://eco.sapo.pt/2023/03/16/dona-do-continente-insiste-que-baixou-margens-para-suportar-parte-da-pressao-inflacionista/",
        "nota": "A carta foi publicada dias antes da apresentação de resultados. "
                "A empresa antecipa a narrativa de absorção de custos antes de "
                "os números serem conhecidos publicamente.",
    },
    {
        "id": "F2 #11", "registo": "lucros #2", "frente": 2,
        "data": "2023-03-16", "orgao": "PÚBLICO",
        "ator": "Sonae (comunicado de resultados à CMVM)",
        "tipo_emissor": "empresa",
        "titulo": "Apresentação de resultados anuais de 2022",
        "afirmacao": "\"O esforço da MC em suportar parcialmente o aumento dos "
                     "vários custos para proteger os seus clientes... "
                     "contribuíram para uma erosão da rentabilidade.\"",
        "contraponto": "A queda de margem da unidade de retalho é verificável "
                       "nas contas. Ao nível do grupo, o lucro subiu 27,7% no "
                       "mesmo ano, facto que o comunicado não menciona.",
        "fonte": "Contas de 2022 da Sonae.",
        "sinal": "desvio", "classe": "confirmada_incompleta",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.publico.pt/2023/03/16/economia/noticia/resultado-liquido-modelo-continente-caiu-178-margem-desceu-27-2042604",
        "nota": "A afirmação em si não é falsa. O comunicado isola a unidade sob "
                "escrutínio sem referir o desempenho do conjunto.",
    },
    {
        "id": "F2 #12", "registo": "lucros #4", "frente": 2,
        "data": "2023-03-22", "orgao": "ECO, PÚBLICO e Observador",
        "ator": "Pedro Soares dos Santos e Ana Luísa Virgínia (Jerónimo Martins)",
        "tipo_emissor": "empresa",
        "titulo": "Conferência de resultados de 2022, com confronto direto ao "
                  "ministro da Economia",
        "afirmacao": "O presidente executivo admite que a inflação \"ajudou\" o "
                     "desempenho de 2022, mas chama-lhe \"um imposto "
                     "perigosíssimo que destrói sociedades e empresas\", e acusa "
                     "o ministro da Economia de \"desonestidade intelectual\" ao "
                     "citar margens brutas de 50%. A diretora financeira "
                     "contrapõe uma margem líquida de 0,7%.",
        "contraponto": "Lucro de 590 milhões de euros em 2022, mais 27,5%. "
                       "Margem EBITDA em queda de 0,3 pontos percentuais, para "
                       "7,3%. A ASAE fala de margem bruta e a empresa responde "
                       "com margem líquida: as duas métricas não são "
                       "diretamente comparáveis e nenhuma das partes explicou "
                       "publicamente a diferença.",
        "fonte": "Contas de 2022 da Jerónimo Martins; relatório da ASAE de 2023.",
        "sinal": "desvio", "classe": "metricas_sem_reconciliacao",
        "ancora": "empresa", "replicacao": 3, "contexto_titulo": None,
        "ligacao": "https://www.publico.pt/2023/03/23/economia/noticia/pedro-soares-santos-inflacao-imposto-perigosissimo-2043468",
        "nota": "Não é uma alegação falsa de nenhum dos lados, mas a escolha "
                "seletiva da métrica mais favorável a cada argumento gera uma "
                "falsa impressão de contradição direta. Este episódio antecede "
                "em três semanas a Lei n.º 17/2023, que criou o IVA Zero.",
    },
    {
        "id": "F2 #13", "registo": "lucros #7", "frente": 2,
        "data": "2023-04-26", "orgao": "ECO",
        "ator": "Pedro Soares dos Santos (Jerónimo Martins)",
        "tipo_emissor": "empresa",
        "titulo": "Comunicado de resultados do primeiro trimestre de 2023",
        "afirmacao": "Promete que a empresa continuará a ser \"uma força "
                     "anti-inflacionária\" e a \"absorver parte da pressão do "
                     "aumento dos preços sobre os consumidores\".",
        "contraponto": "Lucro do primeiro trimestre de 2023: 140 milhões de "
                       "euros, mais 59,1%. Vendas mais 23,4%, para 6,8 mil "
                       "milhões.",
        "fonte": "Contas do primeiro trimestre de 2023.",
        "sinal": "desvio", "classe": "moldura_seletiva",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://eco.sapo.pt/2023/04/26/lucros-da-jeronimo-martins-sobem-quase-60-no-arranque-do-ano/",
        "nota": "As duas coisas não são incompatíveis, mas o comunicado escolhe "
                "destacar a moldura de contenção e não o crescimento do lucro.",
    },
    {
        "id": "F2 #14", "registo": "lucros #9", "frente": 2,
        "data": "2024-03-06", "orgao": "Jornal de Negócios e Observador",
        "ator": "Pedro Soares dos Santos (Jerónimo Martins)",
        "tipo_emissor": "empresa",
        "titulo": "Comunicado de resultados anuais de 2023",
        "afirmacao": "Destaca que o grupo \"cresceu acima dos mercados em que "
                     "operamos\" e antecipa que a deflação alimentar combinada "
                     "com elevada inflação de custos vai pressionar as margens "
                     "em 2024.",
        "contraponto": "Lucro de 756 milhões de euros, mais 28,2%. EBITDA "
                       "recorde de 2,2 mil milhões, mais 17%. Margem EBITDA de "
                       "7,3% para 7,1%. Dividendo por ação mais 19,1%.",
        "fonte": "Contas de 2023 da Jerónimo Martins.",
        "sinal": "desvio", "classe": "confirmada_incompleta",
        "ancora": "empresa", "replicacao": 2, "contexto_titulo": None,
        "ligacao": "https://www.jornaldenegocios.pt/empresas/detalhe/lucros-da-jeronimo-martins-cresceram-282-em-2023-para-756-milhoes-de-euros",
        "nota": "O aviso sobre pressão futura nas margens é genuíno, mas o "
                "comunicado não o enquadra ao lado do EBITDA recorde e do "
                "dividendo a subir quase 20% no mesmo ano.",
    },
    {
        "id": "F2 #15", "registo": "lucros #10", "frente": 2,
        "data": "2024-03-13", "orgao": "Jornal de Negócios",
        "ator": "Sonae (comunicado de resultados à CMVM)",
        "tipo_emissor": "empresa",
        "titulo": "Apresentação de resultados anuais de 2023",
        "afirmacao": "Atribui o lucro aos impactos do apoio às famílias, do "
                     "aumento dos custos financeiros e dos impostos, \"mais do "
                     "que compensados por ganhos de eficiência, mais-valias... e "
                     "a melhoria do resultado indireto\".",
        "contraponto": "Lucro mais 6,4%, para 357 milhões de euros. EBITDA "
                       "recorde de 990 milhões, mais 7,2%, ainda que a margem "
                       "EBITDA tenha recuado 0,2 pontos percentuais.",
        "fonte": "Contas de 2023 da Sonae.",
        "sinal": "desvio", "classe": "moldura_seletiva",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.jornaldenegocios.pt/empresas/comercio/detalhe/lucros-da-sonae-aumentam-para-357-milhoes-em-2023",
        "nota": "A erosão da margem é real e confirmada. A moldura enfatiza essa "
                "erosão e não o EBITDA recorde em valor absoluto no mesmo ano.",
    },
    {
        "id": "F2 #16", "registo": "lucros #11", "frente": 2,
        "data": "2024-03-13", "orgao": "PÚBLICO",
        "ator": "Cláudia Azevedo (Sonae)", "tipo_emissor": "empresa",
        "titulo": "Contestação da taxa sobre lucros excedentários de 2022",
        "afirmacao": "Recusa a ideia de que a unidade de retalho saiu beneficiada "
                     "com a inflação, argumenta que o investimento de mais de "
                     "600 milhões em 2023 teria de gerar mais lucros, e antevê "
                     "descida de preços em 2024.",
        "contraponto": "A empresa pagou 1,3 milhões de euros da taxa de 33% "
                       "sobre lucros excedentários, aprovada por PS, BE, PAN e "
                       "Livre, com abstenção de PSD e PCP e votos contra de "
                       "Chega e IL, mas decidiu contestá-la judicialmente.",
        "fonte": "PÚBLICO, março de 2024.",
        "sinal": "nao_testavel", "classe": "em_disputa",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.publico.pt/2024/03/13/economia/noticia/continente-vai-contestar-13-milhoes-taxa-lucros-excedentarios-2083542",
        "nota": "Não é um caso de confirmação ou refutação de dados, mas de uma "
                "classificação legal contestada judicialmente. O desfecho não "
                "está fechado.",
    },
    {
        "id": "F2 #17", "registo": "lucros #12", "frente": 2,
        "data": "2026-03-19", "orgao": "Jornal de Notícias",
        "ator": "Cláudia Azevedo (Sonae)", "tipo_emissor": "empresa",
        "titulo": "Apresentação de resultados anuais de 2025",
        "afirmacao": "\"2025 foi extraordinário para a Sonae... Os nossos "
                     "negócios prosperam.\" A unidade de retalho é descrita como "
                     "tendo tido \"um ano notável\", com reforço de quota de mercado.",
        "contraponto": "Confirmado: lucro mais 11%, para 247 milhões de euros, e "
                       "volume de negócios recorde de 11,4 mil milhões.",
        "fonte": "Contas de 2025 da Sonae.",
        "sinal": "controlo", "classe": "confirmada",
        "ancora": "empresa", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://www.jn.pt/economia/artigo/lucros-da-sonae-e-da-jeronimo-martins-aumentam-em-ano-de-vendas-historicas/18063835",
        "nota": "A afirmação é factualmente sustentada. O que muda é a moldura: "
                "nenhuma menção a absorver custos ou a apoiar famílias, ao "
                "contrário de 2022 e 2023. A linguagem de sacrifício desaparece "
                "quando o escrutínio público sobre a inflação alimentar arrefece.",
    },
    {
        "id": "F2 #18", "registo": "lucros #16", "frente": 2,
        "data": "2026-07-30", "orgao": "Jornal de Negócios e Jornal de Notícias",
        "ator": "Presidentes executivos da Jerónimo Martins e da Sonae",
        "tipo_emissor": "empresa",
        "titulo": "Apresentação de resultados do primeiro semestre de 2026",
        "afirmacao": "A Jerónimo Martins descreve um semestre \"bastante mais "
                     "exigente do que o esperado\", com perspetivas \"pouco "
                     "animadoras\", citando incerteza geopolítica e custos de "
                     "combustível. A Sonae atribui o crescimento ao \"contínuo "
                     "crescimento dos volumes\", sem mencionar dificuldades.",
        "contraponto": "Jerónimo Martins: lucro de 260 milhões de euros, menos "
                       "3,3%. Sonae: lucro de 123 milhões, mais 20,5%. A "
                       "linguagem de dificuldade acompanha a queda e a linguagem "
                       "confiante acompanha a subida.",
        "fonte": "Contas do primeiro semestre de 2026 de ambas as empresas.",
        "sinal": "controlo", "classe": "confirmada",
        "ancora": "empresa", "replicacao": 2, "contexto_titulo": None,
        "ligacao": None,
        "nota": "Simetria clara. O Jornal de Notícias cobriu o mesmo resultado "
                "sob o título \"Continente ganha ao Pingo Doce na batalha dos "
                "lucros\", um enquadramento de vencedores e vencidos mais "
                "competitivo do que o do Jornal de Negócios, que atribuía a "
                "quebra sobretudo à operação polaca. Não é uma alegação falsa em "
                "nenhum dos dois: é uma diferença de ângulo editorial sobre o "
                "mesmo dado. Atenção às leituras cruzadas: a operação polaca usa "
                "a palavra cabaz para descrever a deflação alimentar na Polónia, "
                "que nada tem que ver com o cabaz da DECO.",
    },
    {
        "id": "F2 #19", "registo": "rascunho de apresentação, 26.08.2026",
        "frente": 2,
        "data": "2026-08-11", "orgao": "Jornal Económico",
        "ator": "Pingo Doce (fonte oficial)", "tipo_emissor": "empresa",
        "titulo": "Absolvição em coima por concertação de preços apresentada "
                  "como confirmação de inocência",
        "afirmacao": "A empresa afirma que a absolvição \"confirma que a decisão "
                     "de coima da Autoridade da Concorrência era infundada\".",
        "contraponto": "Não verificámos o alcance da decisão judicial nem se ela "
                       "se pronuncia sobre o mérito ou apenas sobre a coima.",
        "fonte": "Por verificar.",
        "sinal": "nao_testavel", "classe": "em_disputa",
        "ancora": "nenhuma", "replicacao": 1, "contexto_titulo": None,
        "ligacao": "https://jornaleconomico.sapo.pt/noticias/pingo-doce-diz-que-absolvicao-confirma-que-decisao-de-coima-da-adc-era-infundada/",
        "nota": "Ausente dos ficheiros de trabalho, presente no rascunho de "
                "apresentação. Abre uma frente jurídica na contranarrativa "
                "empresarial e fica por verificar.",
    },
    # ---------------------------------------------------------------- Frente 3
    {
        "id": "F3 #1", "registo": "peso orçamental, secção 13", "frente": 3,
        "data": "2026-08-02", "orgao": "Jornal de Notícias", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Prestação da casa aperta e famílias deixam de pedir crédito",
        "afirmacao": "A prestação média de todos os contratos de crédito à "
                     "habitação atingiu 436 euros por mês, máximo histórico e "
                     "décimo mês consecutivo de subida.",
        "contraponto": "Confirmado nos dados do Banco de Portugal citados na "
                       "peça. Taxa média dos novos empréstimos em 2,93%, valor "
                       "mais elevado desde maio de 2025. Novas operações de "
                       "crédito a particulares em queda de 3 863 para 3 701 "
                       "milhões de euros em junho.",
        "fonte": "Banco de Portugal; simulações da DECO PROteste.",
        "sinal": "controlo", "classe": "contexto_orcamental",
        "ancora": "bdp", "replicacao": 1, "contexto_titulo": "titulo",
        "ligacao": None,
        "nota": "A pressão sobre o orçamento familiar em 2026 não vem só da "
                "alimentação. Os dois indicadores não são somáveis (bases e "
                "universos diferentes), mas ilustram pressão cumulativa sobre o "
                "mesmo orçamento. A estimativa do presidente executivo do BPI, "
                "de 80 a 100 mil casas por ano, não foi confirmada por nós.",
    },
    {
        "id": "F3 #2", "registo": "rascunho de apresentação, 26.08.2026",
        "frente": 3,
        "data": "2026-08-26", "orgao": "Diário de Notícias", "ator": None,
        "tipo_emissor": "imprensa",
        "titulo": "Famílias cortam no lazer para suportar custos do regresso às aulas",
        "afirmacao": "Oito em cada dez consumidores admitem reduzir gastos "
                     "noutras áreas para suportar os custos do novo ano letivo. "
                     "A restauração (69%), o lazer (50%) e as férias (48%) são "
                     "os setores mais cortados.",
        "contraponto": "Estudo de mercado da ConsumerChoice, sem ficha técnica "
                       "publicada na peça. Não confrontámos os resultados com "
                       "outras fontes de inquérito.",
        "fonte": "ConsumerChoice, citado pelo Diário de Notícias.",
        "sinal": "nao_testavel", "classe": "contexto_orcamental",
        "ancora": "sondagem", "replicacao": 1, "contexto_titulo": "titulo",
        "ligacao": None,
        "nota": "Mostra a alimentação a competir por espaço no orçamento com "
                "outras despesas. Note-se que a alimentação em casa não figura "
                "entre os setores cortados: o corte incide na restauração, que "
                "no Inquérito às Despesas das Famílias é rubrica distinta da "
                "alimentação.",
    },
]

#: Casos dentro da janela de recolha sistemática. É a única subamostra sobre a
#: qual faz sentido calcular proporções.
CASOS_DENSOS = [c for c in CASOS
                if JANELA_DENSA[0] <= date.fromisoformat(c["data"]) <= JANELA_DENSA[1]]

# ==========================================================================
# As seis narrativas
# ==========================================================================
NARRATIVAS: list[dict] = [
    {
        "id": 1,
        "nome": "Causalidade externa não sustentada",
        "sumario": "A cobertura de rotina atribui subidas do cabaz a causas "
                   "externas (guerra, tempestades, procura de proteína) sem as "
                   "hierarquizar nem quantificar.",
        "casos": ["F1 #1", "F1 #2", "F1 #3", "F1 #18", "F1 #4", "F1 #5",
                  "F1 #6", "F1 #7"],
    },
    {
        "id": 2,
        "nome": "Reporte semanal e cópia de agência",
        "sumario": "O valor semanal do cabaz da DECO é o formato mais recorrente "
                   "do levantamento. É sóbrio no conteúdo, mas replicado quase "
                   "palavra por palavra por seis ou mais órgãos no mesmo dia.",
        "casos": ["F1 #8", "F1 #9", "F1 #10", "F1 #11", "F1 #12", "F1 #13"],
    },
    {
        "id": 3,
        "nome": "Lucros da distribuição contra custo de vida das famílias",
        "sumario": "A narrativa mais persistente do levantamento, que atravessa "
                   "quase quatro anos e escala de comunicados sindicais em 2023 "
                   "a ações de rua e cartas de leitor em 2026.",
        "casos": ["F2 #1", "F2 #2", "F2 #3", "F2 #4", "F2 #5", "F2 #6", "F2 #7",
                  "F2 #8", "F2 #9"],
    },
    {
        "id": 4,
        "nome": "Contranarrativa empresarial",
        "sumario": "Resposta direta à narrativa anterior. Em anos de lucro "
                   "elevado sublinha-se eficiência; em anos de pressão sobre "
                   "margens sublinha-se sacrifício. Ganhou recentemente uma "
                   "frente jurídica.",
        "casos": ["F2 #10", "F2 #11", "F2 #12", "F2 #13", "F2 #14", "F2 #15",
                  "F2 #16", "F2 #17", "F2 #18", "F2 #19"],
    },
    {
        "id": 5,
        "nome": "Pluralidade e fragilidade dos indicadores",
        "sumario": "Múltiplos indicadores de cabaz e fontes oficiais que se "
                   "contradizem sem reconciliação pública.",
        "casos": ["F1 #14", "F1 #15", "F1 #16", "F1 #17"],
    },
    {
        "id": 6,
        "nome": "Pressão orçamental para além do cabaz",
        "sumario": "Não são casos de discurso a confrontar com dados, mas "
                   "contexto que mostra a alimentação a competir por espaço no "
                   "orçamento com a habitação e com o regresso às aulas.",
        "casos": ["F3 #1", "F3 #2"],
    },
]

# ==========================================================================
# Indicadores de cabaz em circulação pública
# ==========================================================================
# Serve a pergunta sobre qual é o número que o noticiário trata como facto. Os
# quatro medem coisas diferentes e nenhum deles é "o preço da alimentação em
# Portugal".
INDICADORES: list[dict] = [
    {
        "nome": "Cabaz DECO PROteste",
        "entidade": "DECO PROteste (associação de consumidores)",
        "produtos": "63 produtos, quantidades fixas desde janeiro de 2022",
        "frequencia": "Semanal", "ambito": "Nacional",
        "mede": "Preço de um cabaz fixo. É um índice de Laspeyres com cabaz "
                "congelado, não um indicador de custo de vida.",
        "cautela": "Um cabaz que sobe de preço não implica que as famílias "
                   "estejam a gastar mais em alimentação: o índice não capta "
                   "substituição entre produtos.",
    },
    {
        "nome": "IPC e IHPC",
        "entidade": "INE e Eurostat",
        "produtos": "Cabaz representativo do consumo, com ponderadores revistos",
        "frequencia": "Mensal", "ambito": "Nacional e comparável na UE",
        "mede": "Variação de preços do consumo efetivo. O IHPC é o índice "
                "harmonizado usado nas comparações europeias.",
        "cautela": "Não incorpora dados de leitura ótica de caixa: a recolha "
                   "automatizada é feita por extração de páginas na Internet. "
                   "Os descontos só entram se forem de aplicação generalizada, "
                   "pelo que descontos por cartão de fidelização ou por cupão "
                   "ficam de fora.",
    },
    {
        "nome": "Cabazram",
        "entidade": "Direção Regional do Comércio, Indústria e Qualidade da Madeira",
        "produtos": "26 produtos essenciais",
        "frequencia": "Mensal", "ambito": "Regional (Madeira)",
        "mede": "Preço de um cabaz regional, criado pelo Despacho n.º 147/2026, "
                "de 20 de março.",
        "cautela": "A própria entidade classifica a recolha como piloto, feita "
                   "por observação direta em dois estabelecimentos do Funchal. "
                   "Os valores refletem a tendência da amostra e não uma média "
                   "representativa da Região.",
    },
    {
        "nome": "Inquérito às Despesas das Famílias",
        "entidade": "INE",
        "produtos": "Despesa efetiva declarada, classificação COICOP",
        "frequencia": "Quinquenal (edição 2022/2023)",
        "ambito": "Nacional, com desagregação por quintil, região e tipo de agregado",
        "mede": "O que as famílias efetivamente gastam e quanto isso pesa no "
                "orçamento: 3 091 euros por ano, 12,9% da despesa total.",
        "cautela": "São médias e não medianas. A comparação com as Contas "
                   "Nacionais dá um rácio de 2,32 vezes na despesa alimentar, "
                   "acima do desvio geral de 1,70 vezes, e a taxa de cobertura "
                   "portuguesa (43,9%) fica abaixo do mínimo europeu. Qualquer "
                   "valor absoluto de despesa alimentar deve ser lido como "
                   "intervalo, de 239 a 555 euros por mês.",
    },
]

# ==========================================================================
# Contradições entre fontes, por reconciliar publicamente
# ==========================================================================
CONTRADICOES: list[dict] = [
    {
        "tema": "Margens do retalho alimentar",
        "fonte_a": "ASAE: margens de lucro superiores a 50% em certos produtos, "
                   "em fiscalizações a 960 operadores (2023).",
        "fonte_b": "APED: margens de 2% a 3% no retalho alimentar. Jerónimo "
                   "Martins: margem líquida de 0,7% em 2022.",
        "porque": "São métricas diferentes. A ASAE fala de margem bruta e as "
                  "empresas respondem com margem líquida, sem que nenhuma das "
                  "partes explique publicamente a diferença.",
        "estado": "Nunca reconciliada. O argumento continua a ser usado em 2026.",
        "casos": ["F1 #15", "F2 #12"],
    },
    {
        "tema": "Efeito do IVA Zero de 2023",
        "fonte_a": "ASAE: redução de 10,14% dos preços entre 18 de abril e 4 de "
                   "setembro de 2023.",
        "fonte_b": "DECO PROteste, sobre os 41 dos seus 63 produtos abrangidos: "
                   "menos 8,45% aos três meses e, no balanço final da medida, um "
                   "aumento de 4,71% face ao início.",
        "porque": "Universos e janelas de medição diferentes para a mesma medida.",
        "estado": "Por reconciliar. A leitura conjunta mostra que a subida de "
                  "preços de base anulou o efeito da isenção antes de esta "
                  "terminar.",
        "casos": ["F1 #7"],
    },
    {
        "tema": "Sentido da variação do cabaz em agosto de 2026",
        "fonte_a": "Cabaz DECO, nacional e semanal: a subir, de 253,47 euros a "
                   "29 de julho para 253,55 euros a 19 de agosto.",
        "fonte_b": "Cabazram, regional e mensal: a descer 6%, de 82,53 para "
                   "77,57 euros, entre julho e agosto.",
        "porque": "Composições diferentes (63 contra 26 produtos), periodicidades "
                  "diferentes, âmbitos geográficos diferentes e uma recolha "
                  "assumidamente piloto.",
        "estado": "Não é uma contradição a resolver, mas uma comparação que não "
                  "devia ser feita sem notar as diferenças.",
        "casos": ["F1 #16"],
    },
    {
        "tema": "Inflação baixa contra cabaz a encarecer",
        "fonte_a": "Índice harmonizado: inflação geral portuguesa em linha com a "
                   "média da Zona Euro (3,1% contra 3,0%, 12.º lugar em 27).",
        "fonte_b": "Inflação alimentar portuguesa acima da média há mais de um "
                   "ano, terceira mais alta em julho de 2026 (2,3% contra 1,2%).",
        "porque": "O paradoxo desfaz-se ao separar a inflação alimentar da "
                  "inflação geral, e o índice harmonizado do índice nacional.",
        "estado": "Explicada, mas apenas por uma peça do levantamento.",
        "casos": ["F1 #14", "F1 #17"],
    },
    {
        "tema": "Despesa alimentar por agregado",
        "fonte_a": "Inquérito às Despesas das Famílias: 239 euros por mês.",
        "fonte_b": "Contas Nacionais: 555 euros por mês.",
        "porque": "Rácio de 2,32 vezes, acima do desvio geral de 1,70 vezes "
                  "medido no consumo total. A taxa de cobertura portuguesa na "
                  "alimentação (43,9%) fica abaixo do mínimo europeu (58%), e "
                  "precisamente na categoria que o Eurostat identifica como a de "
                  "menor disparidade entre países.",
        "estado": "Não existe exercício nacional de conciliação. Três "
                  "explicações candidatas, não arbitráveis com os dados "
                  "públicos: sub-reporte no inquérito, sobre-atribuição nas "
                  "Contas Nacionais, ou consumo de não residentes.",
        "casos": [],
    },
]

# ==========================================================================
# Afirmações por verificar
# ==========================================================================
# A coluna `responsabilidade` distingue o que interessa a um gabinete: uma
# afirmação de um deputado é matéria de debate; uma afirmação do Governo é
# matéria de resposta.
POR_VERIFICAR: list[dict] = [
    {
        "quem": "Ministro das Finanças", "quando": "14 de abril de 2026",
        "onde": "Jornal de Negócios",
        "afirmacao": "Parte da descida do IVA \"fica sempre em quem vende e em "
                     "quem produz\", e \"isso está demonstrado por estudos\".",
        "estado": "Nenhum estudo é identificado na peça.",
        "contraponto": "O precedente do IVA Zero (Lei n.º 17/2023, de 14 de "
                       "abril, vigente de 18 de abril a 31 de outubro de 2023, "
                       "prorrogado até 4 de janeiro de 2024) mostra um efeito "
                       "que se esgotou: a ASAE mediu menos 10,14% e a DECO "
                       "menos 8,45% aos três meses, mas no balanço final da "
                       "medida registou um aumento de 4,71% face ao início.",
        "responsabilidade": "governo",
    },
    {
        "quem": "Declaração ministerial não identificada",
        "quando": "agosto de 2026",
        "onde": "Comentário de leitor no Jornal de Notícias",
        "afirmacao": "\"Estamos bem melhor, diz o nosso ministro!!! Ele tem razão\", "
                     "em tom sarcástico, anexo à notícia da subida semanal do cabaz.",
        "estado": "Não conseguimos identificar a que declaração se refere: não "
                  "está citada na peça nem no comentário.",
        "contraponto": "Registado apenas como evidência de receção cética do "
                       "público a discurso oficial sobre melhoria das condições "
                       "económicas.",
        "responsabilidade": "governo",
    },
    {
        "quem": "José Gusmão (Bloco de Esquerda)", "quando": "14 de abril de 2023",
        "onde": "Twitter/X",
        "afirmacao": "Os presidentes executivos das duas distribuidoras ganham "
                     "em média 36 vezes mais do que os trabalhadores.",
        "estado": "Não confrontado com os dados de remuneração das empresas.",
        "contraponto": "Por verificar.",
        "responsabilidade": "politica",
    },
    {
        "quem": "José Manuel Pureza (Bloco de Esquerda)",
        "quando": "8 de junho de 2026", "onde": "Esquerda.net",
        "afirmacao": "O presidente executivo da Jerónimo Martins ganha 226 vezes "
                     "mais do que um trabalhador da empresa.",
        "estado": "Não confrontado com os dados de remuneração da empresa.",
        "contraponto": "Por verificar. O valor do lucro citado no mesmo discurso "
                       "está confirmado.",
        "responsabilidade": "politica",
    },
    {
        "quem": "PCP (Ricardo Lume)", "quando": "20 de maio de 2026",
        "onde": "Funchal Notícias",
        "afirmacao": "Os lucros da distribuição assentam em \"especulação de preços\".",
        "estado": "Não confrontado com dados de margem por produto.",
        "contraponto": "Por verificar. O valor do lucro citado está confirmado.",
        "responsabilidade": "politica",
    },
    {
        "quem": "Carta de leitor", "quando": "13 de agosto de 2026",
        "onde": "Jornal de Notícias",
        "afirmacao": "Os cinco maiores bancos têm um lucro diário de 14 milhões "
                     "de euros.",
        "estado": "Não confrontado com dados oficiais.",
        "contraponto": "Por verificar.",
        "responsabilidade": "opiniao",
    },
    {
        "quem": "Pingo Doce", "quando": "11 de agosto de 2026",
        "onde": "Jornal Económico",
        "afirmacao": "A absolvição em coima \"confirma que a decisão da "
                     "Autoridade da Concorrência era infundada\".",
        "estado": "Não verificámos o alcance da decisão judicial.",
        "contraponto": "Por verificar.",
        "responsabilidade": "empresarial",
    },
]

# ==========================================================================
# Alcance nas redes sociais
# ==========================================================================
REDES_NOTA = (
    "Dados do NewsWhip, com pesquisa em português restrita a Portugal, cobrindo "
    "oito plataformas (artigos web, Facebook, X, Instagram, Bluesky, Reddit, "
    "TikTok e YouTube), entre 27 de agosto de 2025 e 27 de agosto de 2026. O "
    "limite de doze meses é imposto pela ferramenta, pelo que o bloco de génese "
    "do levantamento, de março e abril de 2023, não está representado nestas "
    "métricas. A própria ferramenta avisa que as interações do Bluesky só entram "
    "a partir de 24 de junho de 2026 e as do Reddit a partir de 13 de maio de "
    "2026: para conteúdo anterior, ambas estão sistematicamente subcontadas, o "
    "que é uma limitação de cobertura e não um sinal de menor viralização."
)

REDES_TOPO: list[dict] = [
    {"data": "2026-04-10", "plataforma": "TikTok",
     "ator": "Inês Sousa Real (PAN)", "tipo_emissor": "politico",
     "resumo": "Sobre o aumento histórico do cabaz alimentar e os custos elevados.",
     "interacoes": 17854, "caso": None,
     "ligacao": "https://www.tiktok.com/@ines.sousa.real/video/7627154011023609120"},
    {"data": "2026-05-29", "plataforma": "Instagram",
     "ator": "Bloco de Esquerda", "tipo_emissor": "politico",
     "resumo": "Sobre o novo máximo do cabaz alimentar.",
     "interacoes": 11433, "caso": None,
     "ligacao": "https://www.instagram.com/p/DY6Z8YtiOf_/"},
    {"data": "2026-05-11", "plataforma": "Facebook",
     "ator": "José Luís Carneiro (PS)", "tipo_emissor": "politico",
     "resumo": "Interpelação ao primeiro-ministro sobre o custo de vida.",
     "interacoes": 6423, "caso": None,
     "ligacao": "https://www.facebook.com/108820094072933/posts/1568327965293604"},
    {"data": "2026-05-07", "plataforma": "Facebook",
     "ator": "Pedro dos Santos Frazão (Chega)", "tipo_emissor": "politico",
     "resumo": "Episódio de uma audição parlamentar.",
     "interacoes": 4830, "caso": None,
     "ligacao": "https://www.facebook.com/106002254502331/posts/2089247128610797"},
    {"data": "2026-08-19", "plataforma": "Instagram", "ator": "Expresso",
     "tipo_emissor": "imprensa",
     "resumo": "Desde julho de 2025 que a inflação alimentar está acima da média "
               "da Zona Euro.",
     "interacoes": 4825, "caso": "F1 #17",
     "ligacao": "https://www.instagram.com/p/DcO_wBkgeSC/"},
    {"data": "2026-06-29", "plataforma": "Facebook", "ator": "Partido Socialista",
     "tipo_emissor": "politico",
     "resumo": "Sobre a ausência de resposta do Governo ao custo de vida.",
     "interacoes": 3737, "caso": None,
     "ligacao": "https://www.facebook.com/1242565439164840/posts/1569174961236772"},
    {"data": "2026-03-13", "plataforma": "Instagram", "ator": "Jornal de Notícias",
     "tipo_emissor": "imprensa",
     "resumo": "A escalada do preço dos combustíveis a chegar aos bens alimentares.",
     "interacoes": 3415, "caso": None,
     "ligacao": "https://www.instagram.com/p/DV1iNMJjRR5/"},
    {"data": "2026-04-15", "plataforma": "Facebook", "ator": "CHEGA",
     "tipo_emissor": "politico",
     "resumo": "Defesa da aplicação de IVA zero ao cabaz alimentar.",
     "interacoes": 3295, "caso": None,
     "ligacao": "https://www.facebook.com/1989920374407828/posts/1522610799221968"},
    {"data": "2026-02-24", "plataforma": "Facebook", "ator": "SIC Notícias",
     "tipo_emissor": "imprensa",
     "resumo": "Sobre a subida dos preços dos alimentos e a mudança de hábitos.",
     "interacoes": 2219, "caso": None,
     "ligacao": "https://www.facebook.com/150808986387/posts/1489191296580789"},
    {"data": "2026-06-15", "plataforma": "Instagram", "ator": "CNN Portugal",
     "tipo_emissor": "imprensa",
     "resumo": "Sobre o relatório do Centro Comum de Investigação da Comissão "
               "Europeia.",
     "interacoes": 1705, "caso": "F1 #7",
     "ligacao": "https://www.instagram.com/p/DZntN5ADrN_/"},
]

#: Interações em artigos web dos casos já catalogados que aparecem no export.
#: Cinco observações. É uma amostra pequena de mais para sustentar uma
#: afirmação sobre a relação entre rigor e alcance, e o separador di-lo.
ALCANCE_WEB: list[dict] = [
    {"caso": "F1 #10", "data": "2026-07-22", "orgao": "SOL",
     "tipo": "Reporte semanal de rotina", "interacoes": 0},
    {"caso": "F1 #12", "data": "2026-08-19", "orgao": "Observador",
     "tipo": "Reporte semanal de rotina", "interacoes": 0},
    {"caso": "F1 #9", "data": "2026-07-08", "orgao": "Observador",
     "tipo": "Reporte semanal de rotina", "interacoes": 3},
    {"caso": "F1 #3", "data": "2026-03-27", "orgao": "PÚBLICO",
     "tipo": "Causalidade não sustentada", "interacoes": 27},
    {"caso": "F1 #17", "data": "2026-08-21", "orgao": "Expresso",
     "tipo": "Causalidade sustentada com dados", "interacoes": 143},
]

# ==========================================================================
# Limites do levantamento
# ==========================================================================
# Escritos aqui e mostrados no separador, para que nenhuma leitura das contagens
# acima possa ser feita sem eles.
LIMITES: tuple[str, ...] = (
    "O levantamento é amostral e não exaustivo. Nenhuma contagem aqui apurada é "
    "uma quota de cobertura, e a ausência de um órgão não significa que não "
    "tenha coberto o tema.",
    "Não há volume de cobertura por mês, pelo que o levantamento não sustenta "
    "afirmações sobre aumento ou diminuição da atenção mediática.",
    "Não há codificação de tom nem análise de sentimento. As classificações "
    "dizem respeito à distância entre a peça e os dados, não à sua orientação "
    "editorial.",
    "Os dados de redes sociais cobrem doze meses, de agosto de 2025 a agosto de "
    "2026, e não alcançam o bloco de 2023. O Bluesky e o Reddit estão "
    "subcontados antes de meados de 2026.",
    "A amostra de interações em artigos web tem cinco observações. Não sustenta "
    "a afirmação de que o rigor é recompensado pelo alcance, apenas a levanta "
    "como hipótese a testar com amostra maior.",
    "Seis dos treze recortes de imprensa são imagem sem texto pesquisável, e a "
    "sua leitura depende do resumo feito no ficheiro de trabalho de origem, não "
    "de nova verificação sobre o original.",
    "Os ficheiros de trabalho de 24 de agosto de 2026 e o rascunho de "
    "apresentação de 26 de agosto não coincidem: cinco casos existem apenas no "
    "rascunho e ficam por verificar contra fonte primária.",
)


# ==========================================================================
# Apuramentos
# ==========================================================================
def _data(caso: dict) -> date:
    return date.fromisoformat(caso["data"])


def por_sinal(casos: list[dict] | None = None) -> dict[str, int]:
    """Quantos casos em cada juízo. A contagem de capa do separador."""
    casos = CASOS if casos is None else casos
    contagem = {k: 0 for k in SINAIS}
    for c in casos:
        contagem[c["sinal"]] += 1
    return contagem


def por_tipo_emissor(casos: list[dict] | None = None) -> dict[str, int]:
    """Quem fala, agregado por família de emissor."""
    casos = CASOS if casos is None else casos
    contagem: dict[str, int] = {}
    for c in casos:
        contagem[c["tipo_emissor"]] = contagem.get(c["tipo_emissor"], 0) + 1
    return dict(sorted(contagem.items(), key=lambda kv: -kv[1]))


def dependencia_de_fonte(frente: int = 1) -> dict:
    """
    Que parte da cobertura de uma frente tem por gancho um só emissor.

    Responde à pergunta de quem define a agenda. Calcula-se sobre a Frente 1,
    onde a unidade é a peça noticiosa sobre o cabaz: nas outras frentes o gancho
    é o calendário de resultados das empresas, que não é escolha de ninguém.
    """
    casos = [c for c in CASOS if c["frente"] == frente]
    ancorados = [c for c in casos if c["ancora"] == "deco"]
    return {
        "total": len(casos),
        "ancorados": len(ancorados),
        "ids": [c["id"] for c in ancorados],
        "proporcao": len(ancorados) / len(casos) if casos else 0.0,
    }


def contexto_no_titulo(frente: int = 1) -> dict:
    """
    Onde vive a comparação de longo prazo nas peças que a trazem.

    Só conta as peças que efetivamente citam a variação acumulada: as que não a
    citam de todo são um problema diferente, e ficam em `ausente`.
    """
    casos = [c for c in CASOS if c["frente"] == frente]
    titulo = [c["id"] for c in casos if c["contexto_titulo"] == "titulo"]
    corpo = [c["id"] for c in casos if c["contexto_titulo"] == "corpo"]
    ausente = [c["id"] for c in casos if c["contexto_titulo"] is None]
    return {"titulo": titulo, "corpo": corpo, "ausente": ausente,
            "total_com_contexto": len(titulo) + len(corpo)}


def latencia_causal() -> list[dict]:
    """
    Distância, em dias, entre o choque geopolítico e cada peça que lhe atribui a
    subida de preços, com indicação de se a peça ancorou a atribuição em dados
    posteriores ao choque.

    O apuramento existe para testar a hipótese óbvia, de que as atribuições
    precoces são as más. **A hipótese não se confirma**: há uma peça bem
    fundamentada aos 32 dias e uma peça não sustentada aos 40. O que distingue
    umas das outras não é o tempo decorrido, é a existência de dados do período
    posterior ao choque. O separador mostra as duas colunas por isso mesmo.
    """
    atribuicoes = {
        "F1 #2": False, "F1 #3": False, "F1 #18": True, "F1 #4": False,
        "F1 #5": False, "F1 #6": False, "F1 #7": True,
    }
    linhas = []
    for ident, ancorada in atribuicoes.items():
        caso = por_id(ident)
        linhas.append({
            "id": ident, "data": caso["data"], "orgao": caso["orgao"],
            "dias": (_data(caso) - CHOQUE_GEOPOLITICO).days,
            "ancorada_em_dados": ancorada, "sinal": caso["sinal"],
        })
    return sorted(linhas, key=lambda linha: linha["dias"])


def replicacao(minimo: int = 2) -> list[dict]:
    """Casos publicados por mais do que um órgão, do mais replicado ao menos."""
    casos = [c for c in CASOS if c["replicacao"] >= minimo]
    return sorted(casos, key=lambda c: -c["replicacao"])


def por_verificar_por_responsabilidade() -> dict[str, list[dict]]:
    """Afirmações por verificar, agrupadas por quem responde por elas."""
    grupos: dict[str, list[dict]] = {}
    for item in POR_VERIFICAR:
        grupos.setdefault(item["responsabilidade"], []).append(item)
    return grupos


def por_id(ident: str) -> dict:
    """O caso com este identificador. Levanta `KeyError` se não existir."""
    for c in CASOS:
        if c["id"] == ident:
            return c
    raise KeyError(ident)


def casos_da_narrativa(narrativa_id: int) -> list[dict]:
    """Os casos de uma narrativa, pela ordem em que ela os lista."""
    for n in NARRATIVAS:
        if n["id"] == narrativa_id:
            return [por_id(i) for i in n["casos"]]
    raise KeyError(narrativa_id)


def cronologia(casos: list[dict] | None = None) -> list[dict]:
    """Todos os casos por ordem cronológica."""
    casos = CASOS if casos is None else casos
    return sorted(casos, key=_data)
