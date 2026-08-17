# Auditoria à aplicação *despesa-alimentar*

**Data:** 17 de agosto de 2026 · **Âmbito:** `app.py` (6 246 linhas à data da leitura, 6 251 depois
das correções), `src/`, `dados/`, `tests/`
**Método:** leitura integral do código e do texto apresentado, recálculo por fora dos valores
citados, confronto das constantes contra a fonte, execução da bateria de testes e varrimento
automático da pontuação de todos os literais de texto.
**Prefixo dos itens:** **N** (as séries A–G e K–M pertencem às auditorias de 10, 11 e 12.08.2026).

> **Conclusão em duas linhas.** A camada analítica **resiste inteira**: fontes, cálculos e
> declaração de limitações estão corretos, e isso está verificado por recálculo, não presumido.
> O que se encontrou foram **defeitos de texto** — dois rótulos com parênteses por fechar, três
> frases com pontuação trocada que não se leem como português, e dois números que voltaram a ser
> inscritos à mão. Nenhum altera um número; todos são visíveis a quem lê.
>
> ✅ **Todos aplicados a 17.08.2026.** Ver «Registo de aplicação», na Parte D.

**Resumo por gravidade:**

| | N.º | Efeito |
|---|---|---|
| 🔴 Crítico | 0 | Nenhum número errado ou em falta no que é apresentado |
| 🟠 Importante | 3 | Texto defeituoso à vista do leitor, num documento que vai ao Gabinete |
| 🟡 A corrigir | 4 | Rigor, rastreabilidade, robustez |
| ⚪ A declarar | 1 | Decisão operacional antes da entrega |

**Veredicto quanto à entrega: está pronto.** Os itens 🟠 eram de correção imediata e estão
corrigidos. O único ponto que exige uma decisão sua é o **N8**, e não é um defeito da ferramenta.

---

## Parte A · O que foi verificado e se confirma

Esta parte existe porque uma auditoria que só lista defeitos deixa por dizer o essencial: **o que
é que resistiu**. Os valores abaixo foram recalculados por fora da aplicação.

### A.1 · Fontes

Todo o dado quantitativo ou vem em direto do Eurostat — com o conjunto, o endereço exato do pedido
registado na sessão e vigilância de frescura — ou é constante inscrita com fonte nomeada. Não
encontrei nenhuma afirmação numérica sem proveniência.

| Verificação | Resultado |
|---|---|
| IDF, despesa alimentar ÷ despesa total, por quintil | reproduz os pesos publicados nas seis colunas: 14,8 / 14,1 / 13,6 / 12,0 / 9,1 / 12,0 |
| IDF, soma das nove classes COICOP | fecha **exatamente** em total, q1, q3 e q4; 1 €/ano em q2 e q5 — precisamente como o código documenta |
| Rácio observado das escalas, 3 066 € / 1 654 € | 1,854 ✓ (`ESCALAS_TESTE_RACIO`) |
| Repercussão implícita, 4,0/4,2 e 3,5/4,2 | 0,952 → defeito **0,95** ✓ · 0,833 → base da banda ✓ |
| Efeito mecânico de 23% → 0% | **−18,70%**, igual ao publicado pelo Banco de Portugal ✓ |
| Exemplo dos 106 €, receita cessante | **−13,82 €** (ρ=0) a **−14,65 €** (ρ=1), amplitude 6% ✓ |
| Ano de referência do SOFI | resolve para **2025** pela interseção dos quatro anexos ✓ |
| Pessoas afetadas, SOFI | 1,5 milhões em 2025 ✓ |

Duas observações que merecem registo pela positiva:

**A citação dos «20%» do Banco de Portugal está mantida *verbatim***, em `IVA_ZERO_CITACAO`, em vez
de ser derivada de 23/19 = 21%. A nota no `config.py` explica porquê — o BdP partiu dos valores
não arredondados. Atribuir a uma fonte um número que ela não escreveu seria citação falsa mesmo
com um ponto de diferença.

**A distinção entre valor legal e valor difundido da RMMG** está correta em todos os pontos onde
aparece, com o quociente 12/14 calculado da série e não inscrito.

### A.2 · Cálculos

Verificados por leitura e por teste:

- **Aditividade da decomposição.** `contributo_i = V_i · g_i/(1+g_i)` soma exatamente à variação do
  total. A aplicação declara a propriedade e ela está travada por teste.
- **Identidade da taxa média efetiva.** Simular por escalão e simular com a taxa efetiva dão o
  mesmo resultado por identidade algébrica, não por aproximação. Está confrontado numericamente em
  quatro cenários e travado por teste.
- **Encadeamento Törnqvist.** O dezembro-base é representado pelo ponderador do ano `base + 1`, que
  é o que a definição do Documento Metodológico do IPC exige. Foi a correção E4 e mantém-se certa.
- **Cobertura por quintil.** O denominador é a soma das nove classes e não o total publicado, o que
  evita contar o arredondamento do quadro do INE como falta de cobertura.
- **Extrapolação nacional.** Parte do agregado médio e não da composição escolhida, como o A3
  determinou.

### A.3 · Testes

**134 testes passam** (2,6 s). O que os torna úteis não é o número: é testarem **as afirmações que
a interface faz**, e não apenas as funções. Há testes para a aditividade prometida ao leitor, para
a identidade da taxa efetiva que a Metodologia declara, para a inversão do sinal do controlo no
teste das escalas, para os quadros do IDF reproduzirem o INE, e para a divergência da via errada —
sem esta última, vários passariam com a correção revertida.

---

## Parte B · Itens

### 🟠 N1 · Dois rótulos com parênteses por fechar

> ✅ **Corrigido a 17.08.2026.**

**Onde:** `app.py:3564` e `app.py:5593`.

**O que se passa.** Duas cadeias de texto abrem um parêntese e nunca o fecham. Saem assim no ecrã:

```
Cabaz fixo (subida desde dez/19
O que a Autoridade Tributária já decidiu (informações vinculativas
```

O primeiro é o **indicador de capa do painel do viés de substituição**, um dos argumentos mais
fortes da ferramenta. O segundo abre o bloco das informações vinculativas da AT.

**Causa.** No primeiro, o parêntese de fecho ficou fora da f-string. No segundo, perdeu-se na
quebra de linha entre os dois fragmentos concatenados.

**Correção.** Fechar ambos.

---

### 🟠 N2 · Três frases com parênteses e pontos trocados

> ✅ **Corrigido a 17.08.2026.**

**Onde:** `app.py:5827`, `app.py:6162` e `app.py:6552`.

**O que se passa.** Em três sítios o parêntese de fecho e o ponto final trocaram de lugar, e o
resultado não se lê como português:

| Onde | Texto anterior |
|---|---|
| Escalas de equivalência | «aproxima-se dela por cima (o valor sobe. Um agregado maior aproxima-se dela por baixo) o valor desce.» |
| O que estes números assumem | «o **numerador**, a despesa alimentar (e o **denominador**) o rendimento do EU-SILC, vêm ambos…» |
| Estas séries ainda estão a avançar? | «**Parou** (a série deixou de avançar. **Dentro do prazo**) está a publicar como esperado.» |

**Consequência.** A terceira é a mais grave das três, e não por ser a pior frase: é a **legenda que
diz ao leitor se pode citar os números**. Um quadro de vigilância cuja legenda não se percebe
falha exatamente na função para que foi criado.

**Correção.** Reposta a pontuação em cada uma:

> «…aproxima-se dela por cima (o valor sobe); um agregado maior aproxima-se dela por baixo (o valor
> desce).»
>
> «…o **numerador** (a despesa alimentar) e o **denominador** (o rendimento do EU-SILC) vêm ambos…»
>
> «**Parou**, a série deixou de avançar. **Dentro do prazo**, está a publicar como esperado.»

---

### 🟠 N3 · Espaço antes da vírgula, em três sítios

> ✅ **Corrigido a 17.08.2026.**

**Onde:** `app.py:2016`, `app.py:2297`, `app.py:2656`.

**O que se passa.** Um fragmento termina em espaço e o seguinte começa por vírgula, o que produz
`plausível** , 250,00 €/mês`. **Dois dos três estão dentro de alarmes `st.error`** — o da base fora
do intervalo plausível e o das classes sem ponderador —, que são precisamente as mensagens que
têm de ser lidas com confiança.

**Correção.** Vírgula colada à palavra. No terceiro caso (detalhe do salário mínimo) a vírgula deu
lugar a ponto e vírgula, que é o que a frase pedia.

---

### 🟡 N4 · Dois números voltaram a ser inscritos à mão

> ✅ **Corrigido a 17.08.2026.**

**Onde:** `app.py:6696` (limitação 7) e `app.py:3029` (ajuda do indicador do SOFI).

**O que se passa.** É a **quinta ocorrência do padrão C2 / E9 / K8 / L16**, e desta vez com um
agravante: as duas constantes já existiam.

1. A limitação 7 dizia que a repercussão «parte de **95%**», escrito à mão, enquanto
   `REPERCUSSAO_PADRAO` alimenta todas as outras menções do mesmo número.
2. A ajuda do cartão do SOFI dizia «FAO, SOFI **2026**», enquanto `SOFI_EDICAO = 2026` existe em
   `config.py` e **não era usada em lado nenhum**.

Ambos estavam corretos à data. O defeito não é o valor: é que deixam de estar corretos no dia em
que a calibração ou a edição mudarem, sem que nada o assinale.

**Correção.** O primeiro passa pelo marcador `@RHO_LIM@` com `.replace()`, que é o idioma já usado
no ficheiro para blocos de texto com chavetas literais. O segundo passa a f-string com
`SOFI_EDICAO`, agora importada.

---

### 🟡 N5 · O comentário do quadro por quintil descreve mal os dados que rotula

> ✅ **Corrigido a 17.08.2026.**

**Onde:** `src/config.py:821`, sobre `IVA_ZERO_INFLACAO_QUINTIL`.

**O que se passa.** O comentário dizia:

```
# (quintil, IPC bens alimentares, rubricas afetadas, IPC bens alimentares, IPC total)
```

São **cinco campos anunciados para tuplos de quatro**, e a segunda posição é descrita como «IPC
bens alimentares» quando a aplicação a lê — corretamente — como «rubricas alimentares abrangidas
pela isenção».

**Qual das duas está certa.** A leitura da aplicação, e os próprios valores provam-no: em todos os
quintis o alívio nas rubricas abrangidas (−4,4 no Q1) é maior do que no conjunto dos alimentares
(−2,9) e este maior do que no IPC total (−0,9). A ordem inversa não faria sentido.

**Consequência.** Nenhuma hoje. O risco é a próxima pessoa que edite o quadro confiar no comentário
e trocar colunas — e a coluna trocada alimentaria o gráfico que sustenta a conclusão distributiva
do simulador.

**Correção.** Comentário reescrito com os quatro campos corretos e com a razão pela qual a ordem
importa.

---

### 🟡 N6 · O comentário do acoplamento entre separadores promete mais do que o código faz

**Onde:** `app.py:5459`.

**O que se passa.** O separador Metodologia consome `_comp_iva` e `_taxas_ef`, definidos no
separador do IVA. O comentário diz:

> «Os nomes vêm do separador do IVA, que corre antes deste; se lá tiver falhado, este bloco não
> entra.»

Não é o que acontece. Se o separador do IVA falhasse antes da linha 4029, o acesso a `_comp_iva`
levantaria `NameError` e **perder-se-ia o separador Metodologia inteiro**, não apenas este bloco.
O `painel()` contém o erro e os outros separadores sobrevivem, mas o efeito é maior do que o
comentário anuncia.

**Gravidade real: baixa.** A definição está logo no início do separador do IVA, a seguir ao título
e ao seletor de cenário, pelo que a janela de falha é estreita.

**Recomendação.** Ou guardar o bloco com `if "_comp_iva" in dir()`, ou corrigir o comentário para
descrever o que de facto sucede. **Não aplicado** — é uma alteração de estrutura, não de texto, e
não quis mexer em fluxo de controlo numa véspera de entrega.

---

### 🟡 N7 · `"Indeterminado"` pode ser devolvido mas não consta de `PADROES`

**Onde:** `src/observatorio.py`, `_classificar()` e `PADROES`.

**O que se passa.** `_classificar()` devolve `"Indeterminado"` quando uma das variações é `None`,
mas essa chave não existe em `PADROES`. Como o separador percorre `PADROES.items()`, esses produtos
sairiam da lista de padrões **continuando a contar** no total de produtos com as duas fases
declarado na legenda de cobertura.

**Alcançabilidade.** Só com preço inicial igual a zero. Confirmei o ficheiro: **zero linhas com
preço nulo** em 3 125 observações. Não ocorre hoje.

**Recomendação.** Acrescentar a entrada a `PADROES`, com uma linha a dizer que é ausência de
observação e não um padrão de transmissão — o mesmo tratamento que «Sem série de produção» já
recebeu. **Não aplicado**, pela mesma razão do N6.

---

### ⚪ N8 · O Observatório está fora do prazo hoje, e a falha não é da ferramenta

**Onde:** `dados/observatorio.csv` e `dados/observatorio_meta.json`.

**O que se passa.** O último período recolhido é **15/06 a 12/07/2026**, o que dá **63 dias** contra
um limite de 60 (`LIMITE_DIAS_OBSERVATORIO`). A aplicação mostrará o aviso «Estes preços têm mais
de 60 dias».

**De quem é a falha.** Não é de quem mantém a ferramenta. A recolha correu a **13/08/2026** e não
encontrou nada mais recente: o GPP é que ainda não publicou o período seguinte. É exatamente a
distinção que o `frescura_do_observatorio()` foi criado para estabelecer (K2), e está a funcionar.

**Decisão que fica para a Inês**, e é a única deste documento:

1. voltar a correr `scripts/recolher_observatorio.py` imediatamente antes da entrega, para o caso
   de o GPP ter publicado entretanto; e
2. decidir se o aviso é aceitável à frente da audiência, ou se prefere uma nota de rodapé a
   explicar que a fonte publica de quatro em quatro semanas e está com um período em atraso.

**Cobertura confirmada:** 39 produtos, 59 períodos, série desde 03/01/2022, 17 produtos com as duas
fases, sem falhas de recolha registadas.

---

## Parte C · Narrativa e storytelling

Não é matéria de defeito, e por isso vai à parte. A avaliação é de conteúdo, não de forma.

**O movimento que atravessa o trabalho é a recusa de falsa precisão.** Intervalo em vez de ponto na
âncora e no coeficiente de Engel; «as duas leituras são verdadeiras ao mesmo tempo» na distribuição
do IVA zero; os três limiares de acessibilidade sempre juntos porque isolados mentem; o ponto
central da âncora declarado **não determinável** em vez de arbitrado. Isto é o que separa uma
ferramenta de análise de um instrumento de advocacia.

**Três peças que sustentam a ferramenta em debate público:**

- **O painel do viés de substituição conclui contra o interesse retórico da própria aplicação.**
  Mede o efeito, mostra que é residual, e a seguir diz que isso **não absolve** o cabaz de
  composição fixa, porque o problema maior — marca, calibre, embalagem, insígnia — fica por medir.
  Quem argumenta assim é difícil de atacar, porque já fez o trabalho do adversário.
- **O confronto Portugal/Espanha no SOFI** é o dado mais limpo do trabalho: mesmo custo da dieta
  saudável, resultados muito diferentes, logo a diferença não está nos preços. Vem com um par
  comparável em vez de uma afirmação, e está bem colocado.
- **A separação IHPC/IDF por universo estatístico**, com a razão declarada em fonte primária,
  antecipa a objeção óbvia de quem quiser contestar os pesos.

**Onde a narrativa se estica.** O rácio de 2,3× entre Contas Nacionais e IDF continua sem
explicação completa, e a aplicação diz isso em três sítios. É honesto, e é a razão certa para
manter o intervalo em vez de escolher uma base — mas é também o ponto onde uma pergunta difícil
não tem resposta. Convém que quem apresentar a ferramenta saiba de antemão que a resposta correta
é «não sabemos, e é por isso que apresentamos as duas».

**Hierarquia editorial.** Os quatro degraus (página, bloco, secção, componente) e os blocos
numerados funcionam: é possível passar os olhos por uma página e saber onde se está, que era o
problema declarado da primeira versão. As decisões de 13.08 — recolher legendas para o (i) do
título, tirar tabelas que repetiam gráficos, pôr os números antes da explicação — melhoraram
mensuravelmente a leitura.

---

## Parte D · Registo de aplicação — 17.08.2026

Aplicados ao abrigo da autorização permanente para corrigir erros encontrados.

| | O que ficou |
|---|---|
| **N1** | `app.py:3564` e `app.py:5593`, parênteses fechados nos dois rótulos. |
| **N2** | `app.py:5827`, `6162` e `6552`, pontuação reposta nas três frases. |
| **N3** | `app.py:2016`, `2297` e `2656`, vírgula colada à palavra; ponto e vírgula no terceiro. |
| **N4** | `app.py:6696` passa por `@RHO_LIM@` ← `REPERCUSSAO_PADRAO`; `app.py:3029` passa a usar `SOFI_EDICAO`, acrescentada à lista de importações. |
| **N5** | `src/config.py:821`, comentário reescrito com os quatro campos corretos. |
| **N6, N7** | **Não aplicados.** Alteram fluxo de controlo e não texto; ficam como recomendação. |
| **N8** | **Decisão da Inês.** Nada a alterar no código. |

**Verificado depois de aplicar:** `py_compile` limpo nos cinco módulos; **134 testes passam**; o
varrimento automático de pontuação fica sem ocorrências, exceto o único parêntese legítimo do
título «O que é (e o que não é) “o cabaz”».

**Diff:** `app.py` 43 linhas tocadas, `src/config.py` 6. Nenhuma alteração a fórmula, constante
numérica ou fluxo de dados.

### Nota de método, para a próxima auditoria

O varrimento que apanhou o N1, o N2 e o N3 vale a pena repetir: reconstrói o texto de cada literal
(incluindo f-strings e concatenação implícita, que é onde estes defeitos se escondem) e procura
parênteses desemparelhados, espaço antes de vírgula e parentéticos com fim de frase lá dentro.
Nenhum destes defeitos era visível na leitura do código, porque em todos eles o fragmento
individual parecia correto — só o texto **montado** revela o problema.

É a mesma lição do C5, aplicada à pontuação em vez de à formatação de números: **o que se verifica
tem de ser o que o leitor vê, não o que o programador escreveu**.

---

*Documento de trabalho interno — UPE · DSSD · Secretaria-Geral do Governo.
Não constitui posição oficial.*
