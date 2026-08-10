# Auditoria à aplicação *despesa-alimentar*

**Data:** 10 de agosto de 2026 · **Âmbito:** `app.py`, `src/`, `scripts/`, `dados/`
**Método:** leitura do código, reexecução de todos os cálculos e **chamada real a todas as
ligações de dados**, com confronto dos valores devolvidos contra a fonte.

> **Conclusão em duas linhas.** A arquitetura analítica está sólida e os cálculos que verifiquei
> estão corretos. Mas **quatro ligações de dados estão mal configuradas** — duas delas com efeito
> visível no que a aplicação mostra — e **um indicador está rotulado de forma factualmente errada**.
> Nada disto é visível a olho: a aplicação não dá erro, apenas mostra menos, ou mostra outra coisa.

**Resumo por gravidade:**

| | N.º | Efeito |
|---|---|---|
| 🔴 Crítico | 3 | Números errados ou em falta no que é apresentado |
| 🟠 Importante | 4 | Risco silencioso, ou incoerência entre secções |
| 🟡 A corrigir | 6 | Rigor, rastreabilidade, robustez |
| ⚪ A declarar | 4 | Pressupostos legítimos que devem estar explícitos |

**Estado a 10.08.2026, fim do dia:** os três críticos — **A1, A2 e A3** — e o **B3** estão
corrigidos e verificados em execução. Ver «Registo de aplicação» no fim do documento. Os restantes
treze mantêm-se em aberto.

---

## 🔴 A1 · O rendimento do EU-SILC não está a ser obtido — a série está morta

> ✅ **Corrigido a 10.08.2026.** Ver «Registo de aplicação», no fim.

**Onde:** `src/eurostat.py`, função `rendimento()`, linha ~436.

**O que se passa.** As três chaves tentadas falham todas com HTTP 400. A função levanta exceção, o
`carregar_dados` apanha-a, e a aplicação continua **sem o único indicador de rendimento líquido**.

```
FALHA   rendimento MEI_E    ilc_di03 — nenhuma chave respondeu (400)
FALHA   rendimento MED_E    ilc_di03 — nenhuma chave respondeu (400)
```

**Causa.** Duas coisas erradas ao mesmo tempo:

1. **Os códigos do indicador não existem.** A aplicação usa `MEI_E` e `MED_E`. Os códigos reais da
   dimensão `statinfo` são **`MEAN_EI`** e **`MED_EI`**.
2. **A ordem das dimensões está errada.** O conjunto é
   `freq.age.sex.statinfo.unit.geo.time`; as chaves tentadas põem a unidade em segundo lugar.

**Consequência visível.** A secção «Quanto pesa no orçamento» perde a linha *Rendimento das
famílias (EU-SILC)* e passa a mostrar **apenas salários brutos**. Pior: a legenda por baixo
continua a dizer

> «**Verde:** rendimento **líquido** — depois de impostos e contribuições.»

…a descrever uma barra verde **que não é desenhada**. Um leitor conclui que está a ver um esforço
sobre rendimento líquido quando está a ver esforço sobre valores brutos — que é a leitura mais
alarmista das duas.

**Correção.** Substituir a lista de chaves de `rendimento()` por:

```python
for chave in [f"A.Y_GE16.T.{indicador}.EUR",
              f"A.TOTAL.T.{indicador}.EUR"]:
```

e passar a chamar a função com `MEAN_EI` / `MED_EI` em vez de `MEI_E` / `MED_E` (em `app.py`,
linha ~217 e ~968, e no `format` dos rótulos).

**Verificado.** `A.Y_GE16.T.MEAN_EI.EUR.PT` → 2025: **17 239 €/ano**;
`MED_EI` → **14 564 €/ano**. Oito observações cada.

---

## 🔴 A2 · O salário mínimo está rotulado como «valor legal» e não é

> ✅ **Corrigido a 10.08.2026.** Ver «Registo de aplicação», no fim.

**Onde:** `app.py`, linha ~1157 (`"Valor legal bruto, {sm_pt['periodo']}"`).

**O que se passa.** A aplicação apresenta **1 073 €** como salário mínimo mensal de 2026. O valor
legal da retribuição mínima mensal garantida em Portugal para 2026 é **920 €**.

**Causa.** O conjunto `earn_mw_cur` do Eurostat converte, para os países que pagam 14 meses, o
valor legal em **duodécimos**: publica `legal × 14 / 12`. A série confirma-o exatamente:

| Ano | Eurostat | × 12/14 | RMMG legal |
|---|---|---|---|
| 2024 | 957 € | 820,29 € | 820 € |
| 2025 | 1 015 € | 870,00 € | 870 € |
| **2026** | **1 073 €** | **919,71 €** | **920 €** |

**Consequência.** O rendimento mensal do cenário «salário mínimo» está **sobrestimado em 16,7 %**,
pelo que o esforço alimentar aí calculado está **subestimado em cerca de 14 %**. É precisamente o
cenário que a aplicação apresenta como «o pior caso plausível» — o erro anda no sentido de o
suavizar.

**Correção — não basta dividir por 14/12.** Os 13.º e 14.º meses são rendimento real, e o esforço
é medido contra despesa mensal. O valor de 1 073 € é o correto para um rácio anualizado; o que
está errado é o **rótulo**. Substituir:

- «Valor legal bruto, 2026-S2»
- por: «**Média mensal equivalente** (14 meses distribuídos por 12), 2026-S2. O valor legal da RMMG
  é de **920 €/mês**.»

E acrescentar a mesma ressalva ao separador UE-27, porque **Espanha também paga 14 meses** e a
comparação entre países é afetada de forma desigual.

---

## 🔴 A3 · A extrapolação agregada do IVA multiplica o agregado errado

> ✅ **Corrigido a 10.08.2026.** Ver «Registo de aplicação», no fim.

**Onde:** `app.py`, linha ~2202 — `resumo_iva(sim, despesa_mensal, vezes_ano, agregados)`.

**O que se passa.** `despesa_mensal` é a despesa **ajustada à composição escolhida na barra
lateral**. `agregados` são **todos os 4,1 milhões** de agregados do país. Multiplicar um pelo outro
assume que **todos os agregados portugueses têm a composição que o utilizador escolheu**.

**Quantificado** (cenário: IVA de 6 % para 0 %, repercussão integral):

| Composição escolhida | Despesa/mês | Poupança agregada | Erro |
|---|---|---|---|
| **Média nacional** (correto) | 239,33 € | **674,5 M€** | — |
| 2 adultos (valor por defeito) | 205,49 € | 579,1 M€ | **−14,1 %** |
| 1 adulto | 120,88 € | 340,7 M€ | −49,5 % |
| 3 adultos + 2 crianças | 410,98 € | 1 158,2 M€ | +71,7 % |
| 5 adultos | 459,33 € | 1 294,5 M€ | **+91,9 %** |

O valor agregado **muda quando o utilizador mexe na composição**, o que não pode acontecer: o total
nacional não depende de quem está a olhar para o ecrã. **Mesmo por defeito está errado em −14 %.**

**Correção.** Na secção «Ordens de grandeza a nível agregado», usar a despesa **média nacional**
(`media_agregado`), não a ajustada:

```python
sim_nac = simular_iva(decompor(media_agregado, dados["pesos"], dados["variacoes_classe"]),
                      taxas_atuais, taxas_cenario, repercussao)
res_nac = resumo_iva(sim_nac, media_agregado, vezes_ano, agregados)
```

e usar `res_nac` **apenas** nos dois cartões agregados, mantendo `res` no resto do separador, que é
por agregado e está correto. Acrescentar uma legenda: «não depende da composição escolhida acima».

A caixa «Isto não é uma estimativa de custo orçamental» deve manter-se — trata de outra limitação,
não desta.

---

## 🟠 B1 · O número de agregados vem de uma série errada (salvo por uma guarda)

**Onde:** `src/eurostat.py`, `numero_agregados()`, linha ~255.

**O que se passa.** A chave `A.THS.TOTAL.TOTAL.PT` não corresponde à estrutura do conjunto
`lfst_hhnhtych`, que é `freq.agechild.n_child.phhcomp.unit.geo.time` com unidade `THS_HH`. A via
SDMX falha, a via alternativa devolve **uma fatia arbitrária: 443,5 mil agregados** — um décimo do
valor real.

**Porque não explodiu.** Existe uma guarda de plausibilidade em `app.py` (linha ~298) que rejeita
valores fora de 3–6,5 milhões e recorre aos Censos. **A guarda está a funcionar e a salvar o
resultado.** Mas isso significa que a lógica «preferir o valor anual do Eurostat» **nunca chega a
correr**, e o divisor está de facto congelado em 2021.

**Correção.** Chave certa: `A.TOTAL.TOTAL.TOTAL.THS_HH.PT`, e filtros
`{"freq": "A", "agechild": "TOTAL", "n_child": "TOTAL", "phhcomp": "TOTAL", "unit": "THS_HH", ...}`.

**Verificado:** devolve 2025 = **4 562,1 mil agregados**, valor plausível e mais recente do que os
Censos.

> ⚠️ **Não aplicar esta correção sozinha.** Ver B2 — passar a usar 4 562 100 agregados de 2025 com
> uma despesa de 2022 **piora** a âncora em vez de a melhorar.

---

## 🟠 B2 · Numerador e denominador da âncora são de anos diferentes

**Onde:** `app.py`, `ancora_oficial()`.

A âncora das Contas Nacionais faz `despesa_alimentar(2022) ÷ agregados`. Hoje o divisor é o dos
**Censos de 2021** — desfasamento de um ano, tolerável. Com a correção de B1 passaria a ser o de
**2025**: um desfasamento de três anos, sobre uma variável que cresceu ~10 % no período.

**Correção.** Emparelhar os anos: usar o número de agregados **do mesmo ano da despesa** (2022), e
só depois atualizar pelo índice de preços. Se não houver observação para esse ano, usar a mais
próxima e **declarar o desfasamento na interface**.

Registar também, com destaque, que **a despesa das Contas Nacionais é de 2022** — quatro anos de
atraso. Hoje isso aparece apenas na mensagem de estado.

---

## 🟠 B3 · A lista de reserva do nível de preços contém categorias que não são alimentação

> ✅ **Corrigido a 10.08.2026.** Ver «Registo de aplicação», no fim.

**Onde:** `src/config.py` / `src/eurostat.py`, `PPP_CANDIDATOS_ALIMENTOS`.

```python
PPP_CANDIDATOS_ALIMENTOS = ["A010101", "E011", "CP011", "A01", "0101"]
```

A aplicação usa **a primeira que responda**. Confrontando os rótulos oficiais:

| Código | Rótulo real | Portugal (UE-27 = 100) |
|---|---|---|
| `A010101` | **Food** ✅ | **101,4** |
| `E011` | Household final consumption expenditure ❌ | 86,6 |
| `CP011` | *não existe* | — |
| `A01` | Actual individual consumption ❌ | 85,3 |
| `0101` | *não existe* | — |

Hoje funciona, porque `A010101` responde e é o código certo. **Mas se um dia falhar, a aplicação
apresenta silenciosamente o nível de preços de *todo* o consumo das famílias sob o título «nível de
preços dos alimentos»** — e a conclusão inverte-se: de «1,4 % acima da média europeia» para «13,4 %
abaixo».

**Correção.** Restringir a lista a categorias alimentares e remover as inexistentes:

```python
PPP_CANDIDATOS_ALIMENTOS = ["A010101", "A0101"]   # Food · Food and non-alcoholic beverages
```

(`A0101` inclui bebidas não alcoólicas, pelo que só deve entrar como reserva, com nota.)

---

## 🟠 B4 · Dois coeficientes de Engel diferentes, no mesmo ecrã

O separador «Despesa e composição» mostra, a poucos centímetros um do outro:

- **16,4 %** — «Do que as famílias gastam, vai para comida» (Contas Nacionais, 2022);
- **12,0 %** — «Média nacional» na tabela por quintil (IDF 2022/2023).

São a mesma grandeza conceptual e diferem 4,4 pontos, pela razão já documentada em §2.16 do
levantamento: conceito interno *versus* residentes.

**Correção.** Rotular os dois explicitamente («conceito territorial, inclui não residentes» e
«agregados residentes») e acrescentar uma frase que remeta para a explicação. Alternativa mais
limpa: mostrar o de 12,0 % no cartão e reservar o das Contas Nacionais para o separador UE-27, onde
é o único comparável entre países.

---

## 🟡 C1 · Afirmação sem fonte sobre o salário mínimo

**Onde:** `app.py`, linha ~1196.

> «cerca de **um quarto** dos trabalhadores portugueses aufere a remuneração mínima»

Não tem fonte no código nem no registo de ligações, e não é verificável em nenhuma das séries que a
aplicação consome. **Ou se cita a fonte oficial (GEE/MTSSS, Relatório sobre a RMMG), ou se retira a
fração** e se escreve apenas «uma parcela significativa».

Numa ferramenta cujo argumento central é a rastreabilidade, é a afirmação mais frágil do ecrã.

---

## 🟡 C2 · Tabela de valores «ilustrativos» inscrita à mão

**Onde:** `app.py`, linhas ~1269–1273 — a tabela de esforço por escala (25,9 % / 22,3 % / 28,6 %…),
marcada como *«valores ilustrativos, com dados de referência»*.

São números fixos, de origem não documentada, apresentados junto de números calculados em direto.
Um leitor não distingue uns dos outros.

**Correção.** Calcular a tabela com os dados da sessão — o cálculo já existe em
`despesa_do_agregado` — ou, se o objetivo é apenas demonstrar a propriedade, substituir os valores
por símbolos e manter só a estrutura qualitativa.

---

## 🟡 C3 · O Törnqvist descarta anos inteiros por uma classe em falta

**Onde:** `src/calculos.py`, `indices_comparados()`, linha ~467 — `dez[codigos].dropna()`.

`dropna()` sem argumentos elimina a **linha inteira**. Se uma única das nove classes não tiver
observação em dezembro de um ano, esse ano **desaparece da série** sem aviso.

**Correção.** Restringir às classes com série completa, em vez de aos anos completos, e registar
quais foram excluídas:

```python
completos = [c for c in codigos if dez[c].notna().all() and w[c].notna().all()]
```

---

## 🟡 C4 · Rótulo do período no Observatório é falso para metade dos produtos

**Onde:** `app.py`, linha ~1920.

A legenda diz «Variação entre **01/2022** e o fim da série» usando o mínimo global. Mas as
variações são calculadas no **período comum a cada produto**, que é bem mais curto em vários casos:
Arroz Carolino 16 períodos, Brócolo 19, Cebola 20 — contra 58 do Ovo M.

**Correção.** Retirar as datas da legenda e remeter para a coluna «Períodos», que já está na tabela;
ou indicar o intervalo por produto no gráfico.

---

## 🟡 C5 · Padrão de formatação frágil, repetido

`.replace(",", " ")` e `.replace(".", ",")` aplicados a *f-strings* inteiras aparecem em vários
sítios (ex. linha ~2243). Funcionam hoje porque não há outra vírgula na frase; qualquer alteração
de redação parte a formatação **silenciosamente** — já aconteceu antes neste projeto.

**Correção.** Uma função única de formatação numérica, aplicada só ao número. Já existem `euro()` e
`percentagem()` em `config.py`; falta o equivalente para inteiros e para pontos percentuais.

---

## 🟡 C6 · O `salario_medio` não é «o salário médio» no sentido corrente

Vem de `nama_10_a10` (D11 ÷ emprego) = **25 103,89 €/ano (2025)**. É a massa salarial por
trabalhador por conta de outrem, **incluindo tempo parcial**, e exclui contribuições do empregador.
Não é o salário de um trabalhador a tempo inteiro.

**Correção.** Acrescentar «por trabalhador por conta de outrem, incluindo tempo parcial» ao detalhe
da linha.

---

## ⚪ D1 · O ano-base do IDF vale 25 €/mês e não está resolvido

`IDF_ANO_BASE = 2023`. O inquérito é o **IDF 2022/2023** e cobre os dois anos.

| Ano-base | Índice médio | Fator | Âncora hoje |
|---|---|---|---|
| 2022 | 120,09 | 1,1718 | **280,46 €/mês** |
| 2023 | 132,07 | 1,0655 | **255,01 €/mês** |

**25,45 €/mês de diferença — cerca de 10 % do valor de topo da aplicação**, decidido por uma
constante que ninguém confirmou junto do INE.

Acresce uma incoerência interna: o levantamento apresenta o valor de **239 €/mês como sendo de
2022**, enquanto a aplicação o indexa a partir de **2023**.

**A resolver.** Confirmar junto do INE o período de referência dos valores do quadro Q.2.11.a. Se
for a média da vaga, o defensável é indexar a partir da média de 2022–2023, e não de um dos anos.
Até lá, **declarar a sensibilidade na interface**.

---

## ⚪ D2 · O mapeamento IVA ↔ COICOP é o parâmetro menos verificado da aplicação

`src/config.py` atribui 6 % a sete classes e 23 % a «Açúcar e doces» e «Outros alimentos». O próprio
comentário reconhece que «o Código do IVA classifica por produto (Lista I), não por classe COICOP:
a correspondência é aproximada».

É o pressuposto que mais influencia o simulador e **o único que não tem verificação documentada**.
Recomendo um confronto explícito com a Lista I do CIVA, produto a produto, e o registo do resultado
— nem que seja para concluir que a aproximação é a melhor possível.

---

## ⚪ D3 · Circularidade a declarar no teste das escalas

`ESCALAS_TESTE_COMPOSICAO = [(2.0, 0.72), (3.288, 0.28)]`. Os **3,288 adultos** do grupo «3 ou mais»
foram deduzidos assumindo que o Q.2.8 usa a escala OCDE modificada. Esse número é depois usado para
avaliar **as três escalas, incluindo a modificada**.

A dedução está validada (o quadro reproduz 1,000 / 1,500 / 2,144), e a contagem de pessoas não
depende da escala. Mas a dependência existe e deve estar escrita ao lado do resultado, não só no
comentário do código.

---

## ⚪ D4 · Duas fontes envelhecem em silêncio

O **SOFI** (em `config.py`) e o **Observatório** (em `dados/`) não vêm de API. Se ninguém os
atualizar, a aplicação continua a apresentá-los sem nunca dar erro.

**Correção.** Um aviso automático quando a recolha do Observatório tiver mais de 60 dias, e quando o
último ano do SOFI ficar a mais de dois anos da data corrente.

---

## O que verifiquei e está correto

Para que o âmbito da garantia fique claro:

- **Aritmética da decomposição** — a soma dos contributos iguala exatamente a variação do total.
  Propriedade coberta por teste.
- **Simulação de IVA por agregado** — base sem imposto, efeito mecânico, repercussão e imposto
  contido conferem. A correção A3 afeta **apenas** os dois cartões agregados.
- **Cabaz por quintil** — os nove valores por quintil somam o total publicado a menos de 1 €/ano
  (arredondamento do próprio quadro do INE). Inflação por quintil e agravamento reproduzem.
- **Törnqvist** — reproduz o IHPC oficial a 0,12 pontos de índice, por via de cálculo independente.
- **Escalas de equivalência** — desvios de +10,3 % (alimentação) e −10,9 % (despesa total)
  reproduzem; a inversão de sinal confirma-se.
- **Privação alimentar** — a série obtida em direto coincide com a documentada (2025: 1,9 / 5,5 / 1,3).
- **Observatório** — Ovo M, Cenoura e Pescada reproduzem ao decimal os valores do levantamento.
- **Ponderadores, índices, variações, dimensão do agregado, salário mínimo, nível de preços,
  Engel** — todas as ligações respondem e devolvem valores plausíveis.
- **38 testes** passam; a aplicação renderiza sem exceções nas duas bases de âncora.

---

## Ordem de execução sugerida

| # | Item | Porquê primeiro |
|---|---|---|
| 1 | ✅ **A1** rendimento EU-SILC | Repõe um indicador em falta e corrige uma legenda falsa |
| 2 | ✅ **A2** rótulo do salário mínimo | Erro factual, correção de texto, custo nulo |
| 3 | ✅ **A3** extrapolação agregada | Número errado num ecrã que fala de milhões de euros |
| 4 | ✅ **B3** lista do nível de preços | Custo nulo, remove risco de inversão de conclusão |
| 5 | **B1 + B2** agregados e emparelhamento de anos | Têm de ser feitos juntos |
| 6 | **B4** dois coeficientes de Engel | Incoerência visível ao leitor |
| 7 | **C1 … C6** | Rigor e robustez |
| 8 | **D1** ano-base do IDF | Depende de resposta do INE |
| 9 | **D2** mapeamento do IVA | Trabalho de fundo, sem dependência externa |

---

## Registo de aplicação

### A1 · Rendimento do EU-SILC — 10.08.2026

**O que estava errado.** Três coisas ao mesmo tempo: os códigos do indicador (`MEI_E`, `MED_E`)
não existem, a ordem das dimensões estava trocada, e a lista de chaves alternativas fazia com que
as três tentativas falhassem em silêncio.

**O que foi feito.** `src/eurostat.py`, `rendimento()`: chave única e correta,
`freq.age.sex.statinfo.unit.geo` → `A.Y_GE16.T.{MEAN_EI|MED_EI}.EUR.{geo}`. **A lista de chaves
alternativas foi eliminada** — era ela que transformava um código errado numa série vazia sem
ninguém dar por isso. Passa a haver validação prévia do indicador contra
`RENDIMENTO_INDICADORES`, com erro explícito. `app.py` passa a iterar sobre essa constante em vez
de repetir os códigos em quatro sítios.

**Verificado em execução.** A linha «Rendimento das famílias (EU-SILC)» aparece na tabela de
esforço: rendimento equivalente médio de **17 239 €** (2025) × 1,50 unidades = **2 154,88 €/mês**.
A barra verde que a legenda descrevia passa a existir. Nas duas âncoras: 10,2 % de esforço com o
IDF, 25,6 % com as Contas Nacionais.

### A2 · Rótulo do salário mínimo — 10.08.2026

**Confirmação da fonte.** Toda a série do `earn_mw_cur` foi confrontada com o valor legal:
957 → 820 (2024), 1 015 → 870 (2025), 1 073 → 920 (2026). O fator 14/12 reproduz-se ao cêntimo em
todos os anos. O Eurostat difunde a RMMG em duodécimos de 14 mensalidades, para comparar países
com número diferente de pagamentos.

**Decisão: corrigir o rótulo, não o valor.** A despesa alimentar é mensal e recorrente, pelo que a
base certa para a fatia do orçamento é a média mensal do rendimento anual, com os subsídios
diluídos pelos 12 meses. Usar os 920 € atribuiria a dezembro um esforço que na prática não existe.
O que estava errado era chamar-lhe «valor legal».

**O que foi feito.** O detalhe passa a ler «Média mensal bruta de 14 mensalidades, {período} — o
valor legal da RMMG é de {X} €/mês», com o valor legal **derivado** (`× 12/14`, arredondado ao
euro, porque a RMMG é fixada em euros inteiros) e não inscrito à mão. As duas tabelas de fontes na
Metodologia foram corrigidas, e a nota sobre o salário mínimo passou a explicar a conversão.
`salario_minimo()` ganhou a advertência na *docstring*.

### A3 · Extrapolação agregada do IVA — 10.08.2026

**O que foi feito.** Os dois cartões nacionais passam a correr uma segunda simulação sobre a
**despesa do agregado médio** (`media_agregado`), não sobre a despesa ajustada à composição
escolhida. A mesma regra foi aplicada à legenda de sensibilidade entre âncoras, que tinha o mesmo
defeito. `resumo_iva()` ganhou uma advertência explícita: os campos `*_agregada_milhoes` só são
válidos quando a simulação parte do agregado médio.

**Verificado em execução.** Com 1, 2 e 5 adultos, a poupança agregada mantém-se em **351,0 M€** e
a variação de receita em **−877,6 M€**, enquanto a poupança por agregado varia como deve
(42,73 € → 72,64 € → 162,37 €). Antes, o total nacional variava de −14 % a +92 %.

**Teste de regressão.** `test_extrapolacao_nacional_nao_depende_da_composicao` fixa a invariância
e verifica também que a via errada **diverge** — sem isso o teste passaria mesmo que a correção
fosse revertida.

**Correção acessória.** Os dois cartões formatavam o separador decimal em inglês («351.0 M€»);
passam a usar o mesmo auxiliar `_milhoes()` do resto do ecrã.

### B3 · Categorias do nível de preços — 10.08.2026

**Confirmação da fonte.** O `prc_ppp_ind_1` tem **64 categorias**, quase todas não alimentares, e o
ramo alimentar é `A0101*`. Rótulos e valores para Portugal em 2025:

| Código | Rótulo oficial | PT | Alimentar? |
|---|---|---|---|
| `A010101` | Food | 101,4 | ✅ preferida |
| `A0101` | Food and non-alcoholic beverages | 102,0 | ✅ reserva |
| `E011` | Household final consumption expenditure | 86,6 | ❌ removida |
| `A01` | Actual individual consumption | 85,3 | ❌ removida |
| `CP011`, `0101` | *não existem* | — | ❌ removidas |

**O que foi feito.** `PPP_CANDIDATOS_ALIMENTOS` foi substituída por `PPP_CATEGORIAS_ALIMENTOS` —
um dicionário código → rótulo em português, restrito ao ramo `A0101*` — e por
`PPP_CATEGORIA_PREFERIDA`. A reserva `A0101` é mais lata do que a preferida, pelo que **o rótulo
do gráfico passou a ser dinâmico**: o título do eixo e a legenda nomeiam a categoria efetivamente
obtida, e, se a reserva for usada, aparece um aviso a dizer que inclui águas, sumos, cafés e chás.
Antes, o título dizia sempre «nível de preços dos alimentos», fosse qual fosse a categoria.

**Verificado em execução, nos dois caminhos.** Com `A010101` disponível: «categoria `A010101` —
Alimentação», Portugal 101, sem aviso. Forçando a indisponibilidade de `A010101`: «categoria
`A0101` — Alimentação e bebidas não alcoólicas», Portugal 102, com o aviso visível. Sem exceções
em nenhum dos casos.

**Teste de regressão.** `test_candidatas_do_nivel_de_precos_sao_todas_alimentares` exige que toda
a lista comece por `A0101`, proíbe nominalmente os quatro códigos removidos e verifica que a
preferida é a primeira a ser tentada.

**Achado colateral, não aplicado.** O ramo alimentar desce a nove sub-categorias,
`A01010101`–`A01010109` (cereais, carne, peixe, lacticínios, óleos e gorduras, frutos, produtos
hortícolas, açúcar, outros), que correspondem quase um a um às nove classes COICOP usadas na
aplicação. Abre a possibilidade de comparar o nível de preços **por classe** entre países, e não
só o agregado alimentar. Fica registado como hipótese de trabalho — não foi implementado.

### Estado da bateria de testes

40 testes passam (38 anteriores + 2 novos). A aplicação renderiza sem exceções nas duas âncoras e
nos dois caminhos do nível de preços.

---

*Documento de trabalho interno — UPE · DSSD · Secretaria-Geral do Governo.
Não constitui posição oficial.*
