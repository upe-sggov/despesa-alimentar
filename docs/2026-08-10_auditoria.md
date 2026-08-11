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

## ✅ Auditoria encerrada a 11.08.2026

**Os dezassete itens estão fechados**, todos verificados em execução: três críticos
(**A1, A2, A3**), quatro importantes (**B1, B2, B3, B4**), seis de rigor (**C1 … C6**) e quatro
pressupostos declarados (**D1, D2, D3, D4**). O registo de cada correção está no fim do documento.

**O que mudou no que a aplicação mostra:**

| | Antes | Depois |
|---|---|---|
| Âncora IDF | 255,01 €/mês | **276,06 €/mês** |
| Rendimento do EU-SILC | ausente, com legenda a descrevê-lo | **2 154,88 €/mês** |
| Salário mínimo | rotulado «valor legal» | **média de 14 mensalidades**, valor legal citado |
| Poupança agregada do IVA | variava −14 % a +92 % com a composição | **fixa**, parte do agregado médio |
| Coeficiente de Engel | 16,4 % ao lado de 12,0 % | **intervalo 12,0 % – 16,4 %** |

**Dois itens dependeram de fontes externas** e foram resolvidos com documentos fornecidos pela
Inês: o *Boletim Económico* do Banco de Portugal (C1) e o documento metodológico do IDF (D1). Um
terceiro (D2) foi resolvido com o texto do Código do IVA.

**Três correções foram encontradas durante a aplicação, não no diagnóstico inicial:** o padrão de
formatação do C5 já estava partido em produção («p,p,» num gráfico), havia um `_milhoes` definido
duas vezes no mesmo espaço de nomes, e o teste do `IVA_MAPA` apanhou uma incoerência na estrutura
que eu próprio tinha acabado de escrever.

**A bateria passou de 38 para 46 testes.** Os oito novos não repetem o que já estava coberto: cada
um trava um dos modos de falha encontrados, e vários verificam também que **a via errada diverge**
— sem isso, passariam com a correção revertida.

Os dois itens que dependiam de fontes externas — **C1** e **D1** — foram resolvidos com documentos
fornecidos pela Inês: o *Boletim Económico* do Banco de Portugal de junho de 2026 e o documento
metodológico do IDF. O **D1**, em particular, deixou de ser um pressuposto por confirmar e passou a
ser um facto documentado, com efeito material no valor de topo da aplicação.

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

> ✅ **Corrigido a 10.08.2026, em conjunto com B2.** Ver «Registo de aplicação», no fim.

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

> ✅ **Corrigido a 10.08.2026, em conjunto com B1.** Ver «Registo de aplicação», no fim.

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

> ✅ **Corrigido a 10.08.2026.** Ver «Registo de aplicação», no fim.

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

> ✅ **Corrigido a 10.08.2026.** Ver «Registo de aplicação», no fim.

**Onde:** `app.py`, linha ~1196.

> «cerca de **um quarto** dos trabalhadores portugueses aufere a remuneração mínima»

Não tem fonte no código nem no registo de ligações, e não é verificável em nenhuma das séries que a
aplicação consome. **Ou se cita a fonte oficial (GEE/MTSSS, Relatório sobre a RMMG), ou se retira a
fração** e se escreve apenas «uma parcela significativa».

Numa ferramenta cujo argumento central é a rastreabilidade, é a afirmação mais frágil do ecrã.

---

## 🟡 C2 · Tabela de valores «ilustrativos» inscrita à mão

> ✅ **Corrigido a 11.08.2026.** Ver «Registo de aplicação», no fim.

**Onde:** `app.py`, linhas ~1269–1273 — a tabela de esforço por escala (25,9 % / 22,3 % / 28,6 %…),
marcada como *«valores ilustrativos, com dados de referência»*.

São números fixos, de origem não documentada, apresentados junto de números calculados em direto.
Um leitor não distingue uns dos outros.

**Correção.** Calcular a tabela com os dados da sessão — o cálculo já existe em
`despesa_do_agregado` — ou, se o objetivo é apenas demonstrar a propriedade, substituir os valores
por símbolos e manter só a estrutura qualitativa.

---

## 🟡 C3 · O Törnqvist descarta anos inteiros por uma classe em falta

> ✅ **Corrigido a 11.08.2026.** Ver «Registo de aplicação», no fim.

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

> ✅ **Corrigido a 11.08.2026.** Ver «Registo de aplicação», no fim.

**Onde:** `app.py`, linha ~1920.

A legenda diz «Variação entre **01/2022** e o fim da série» usando o mínimo global. Mas as
variações são calculadas no **período comum a cada produto**, que é bem mais curto em vários casos:
Arroz Carolino 16 períodos, Brócolo 19, Cebola 20 — contra 58 do Ovo M.

**Correção.** Retirar as datas da legenda e remeter para a coluna «Períodos», que já está na tabela;
ou indicar o intervalo por produto no gráfico.

---

## 🟡 C5 · Padrão de formatação frágil, repetido

> ✅ **Corrigido a 11.08.2026** — e tinha já partido num sítio. Ver «Registo de aplicação».

`.replace(",", " ")` e `.replace(".", ",")` aplicados a *f-strings* inteiras aparecem em vários
sítios (ex. linha ~2243). Funcionam hoje porque não há outra vírgula na frase; qualquer alteração
de redação parte a formatação **silenciosamente** — já aconteceu antes neste projeto.

**Correção.** Uma função única de formatação numérica, aplicada só ao número. Já existem `euro()` e
`percentagem()` em `config.py`; falta o equivalente para inteiros e para pontos percentuais.

---

## 🟡 C6 · O `salario_medio` não é «o salário médio» no sentido corrente

> ✅ **Corrigido a 11.08.2026.** Ver «Registo de aplicação», no fim.

Vem de `nama_10_a10` (D11 ÷ emprego) = **25 103,89 €/ano (2025)**. É a massa salarial por
trabalhador por conta de outrem, **incluindo tempo parcial**, e exclui contribuições do empregador.
Não é o salário de um trabalhador a tempo inteiro.

**Correção.** Acrescentar «por trabalhador por conta de outrem, incluindo tempo parcial» ao detalhe
da linha.

---

## ⚪ D1 · O ano-base do IDF vale 25 €/mês e não está resolvido

> ✅ **Resolvido a 10.08.2026**, com o documento metodológico do INE. Ver
> «Registo de aplicação», no fim.

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

> ✅ **Levantado e declarado a 10.08.2026.** Ver «Registo de aplicação», no fim.

`src/config.py` atribui 6 % a sete classes e 23 % a «Açúcar e doces» e «Outros alimentos». O próprio
comentário reconhece que «o Código do IVA classifica por produto (Lista I), não por classe COICOP:
a correspondência é aproximada».

É o pressuposto que mais influencia o simulador e **o único que não tem verificação documentada**.
Recomendo um confronto explícito com a Lista I do CIVA, produto a produto, e o registo do resultado
— nem que seja para concluir que a aproximação é a melhor possível.

---

## ⚪ D3 · Circularidade a declarar no teste das escalas

> ✅ **Declarada e medida a 11.08.2026.** Ver «Registo de aplicação», no fim.

`ESCALAS_TESTE_COMPOSICAO = [(2.0, 0.72), (3.288, 0.28)]`. Os **3,288 adultos** do grupo «3 ou mais»
foram deduzidos assumindo que o Q.2.8 usa a escala OCDE modificada. Esse número é depois usado para
avaliar **as três escalas, incluindo a modificada**.

A dedução está validada (o quadro reproduz 1,000 / 1,500 / 2,144), e a contagem de pessoas não
depende da escala. Mas a dependência existe e deve estar escrita ao lado do resultado, não só no
comentário do código.

---

## ⚪ D4 · Duas fontes envelhecem em silêncio

> ✅ **Corrigido a 11.08.2026.** Ver «Registo de aplicação», no fim.

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
| 5 | ✅ **B1 + B2** agregados e emparelhamento de anos | Têm de ser feitos juntos |
| 6 | ✅ **B4** dois coeficientes de Engel | Incoerência visível ao leitor |
| 7 | ✅ **C1 … C6** | Rigor e robustez |
| 8 | ✅ **D1** ano-base do IDF | Resolvido com o documento metodológico do INE |
| 9 | ✅ **D2** mapeamento do IVA | Trabalho de fundo, sem dependência externa |

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

### B1 + B2 · Agregados e emparelhamento de anos — 10.08.2026

**Confirmação da fonte.** Dimensões reais do `lfst_hhnhtych`:
`freq.agechild.n_child.phhcomp.unit.geo`, unidade `THS_HH`. A chave corrigida devolve a série
completa:

| Ano | Agregados | | Ano | Agregados |
|---|---|---|---|---|
| 2018 | 4 182 600 | | 2022 | 4 102 600 |
| 2019 | 4 200 200 | | 2023 | 4 382 000 |
| 2020 | 4 122 200 | | 2024 | 4 473 300 |
| 2021 | 3 939 900 | | 2025 | 4 562 100 |

**Descoberta que muda a leitura do B1.** O EU-LFS **não mede o mesmo universo dos Censos**. É um
inquérito por amostra e exclui alojamentos coletivos. Em 2021, ano em que ambos existem:
**3 939 900** contra **4 149 096** — menos **5,0 %**. Trocar de fonte muda o nível mesmo no mesmo
ano; não é só uma questão de atualidade. Fica declarado na Metodologia.

**A razão de B1 e B2 andarem juntos, medida.** Com a despesa das Contas Nacionais de 2022
(27 318 M€):

| Denominador | Valor mensal | Efeito |
|---|---|---|
| Censos 2021 (o que estava) | 548,68 € | referência |
| **EU-LFS 2022 (emparelhado)** | **554,90 €** | **+1,1 %** |
| EU-LFS 2025 (só B1, sem B2) | 499,01 € | **−9,1 %** ⚠️ |

Corrigir B1 sozinho teria baixado a âncora 9,1 % **por razão nenhuma** — os agregados cresceram,
a despesa não os acompanhou porque é de outro ano. Teria parecido uma melhoria de rigor.

**A causa de fundo: um número a servir dois usos.** Havia um único valor de agregados, e os dois
usos pedem anos diferentes:

- **Denominador da âncora** → o ano da despesa (2022), porque numerador e denominador têm de ser
  contemporâneos;
- **Extrapolação nacional do simulador de IVA** → o ano mais recente (2025), porque o que se
  extrapola é o efeito de uma medida sobre o país de hoje.

**O que foi feito.** `numero_agregados()` com a chave e os filtros certos. `carregar_dados` guarda
a **série inteira** (`agregados_serie`), com a verificação de plausibilidade aplicada observação a
observação em vez de só à última. Nova função pura `calculos.agregados_do_ano(serie, ano)`, que
prefere o ano pedido, recorre ao mais próximo declarando o desfasamento, e cai nos Censos se não
houver série. `ancora_oficial()` usa-a para a base das Contas Nacionais e devolve a proveniência do
denominador, que a interface passa a mostrar.

**Efeito no que se vê.** Âncora das Contas Nacionais: 650,25 €/mês (antes 642,98 €). Poupança
agregada do simulador nessa base: 984,2 M€ (antes 885,1 M€) — a subida vem do multiplicador
correto, 4 562 100 em vez de 4 149 096. A base IDF não é afetada: não passa por divisão nenhuma.

**Declarações acrescentadas à interface.** A idade da base ficou visível na barra lateral («Base de
2022 — 4 anos de atraso; os preços estão atualizados, a estrutura de consumo não»), o denominador
e o seu ano aparecem em «De onde vem este valor», e a legenda da extrapolação explica porque usa um
número de agregados diferente do da âncora. Antes, a idade da base só constava do registo de
ligações.

**Teste de regressão.** `test_denominador_da_ancora_emparelha_o_ano_da_despesa` cobre os três
caminhos — ano presente, ano ausente com desfasamento declarado, ausência de série — e verifica que
o emparelhamento **importa**, exigindo mais de 8 % de diferença entre as duas escolhas.

### B4 · Coeficiente de Engel — 10.08.2026

**Correção ao diagnóstico original.** O relatório descrevia «a mesma grandeza, 4,4 pontos de
diferença» e atribuía-a a «conceito interno *versus* residentes». Duas ressalvas, depois de medir:

Primeira, **não são dois números próximos**. Os dois lados da fração divergem muito, por agregado
e por ano, em 2022:

| | Contas Nacionais | IDF | rácio |
|---|---|---|---|
| Despesa alimentar | 6 659 € | 2 872 € | **2,32×** |
| Despesa total | 40 670 € | 23 900 € | **1,70×** |
| **Engel** | **16,4 %** | **12,0 %** | |

O coeficiente diverge porque o **numerador diverge mais do que o denominador**. É a mesma
divergência de fundo que já leva a aplicação a apresentar a âncora como intervalo (255,01 € a
650,25 €), e não uma discrepância nova.

Segunda, **não confirmei a causa atribuída**. As dimensões do `nama_10_co3_p3` são
`freq.unit.coicop.geo` — não expõem eixo de conceito interno/nacional, pelo que não consigo
verificar essa explicação na fonte. Contribuem também rendas imputadas e a subdeclaração conhecida
nos inquéritos de orçamento familiar. Ficou registada a **divergência medida**, não uma causa
inferida.

**Decisão da Inês, 10.08.2026: apresentar como intervalo**, aplicando ao Engel a doutrina que a
aplicação já usa para a âncora — quando as duas bases oficiais discordam, mostra-se o intervalo e
não se arbitra.

**O que foi feito.** Nova função pura `calculos.intervalo_engel(engel_cn)`. O cartão passa a ler
**«12,0 % a 16,4 %»**, com as duas fontes nomeadas na legenda e a explicação da divergência no
tooltip. O limite inferior é a **constante publicada pelo INE** — a mesma que alimenta a coluna
«Peso no orçamento» —, e não um recálculo: 2 872 / 23 900 dá 12,017 %, que arredondaria a 12,0 %
hoje mas deixaria de coincidir com a tabela por construção. Acrescentou-se uma legenda sob a tabela
por quintil a identificar o 12,0 % como o extremo inferior do cartão.

O resultado é que o número da tabela passa a **explicar** o cartão em vez de o contradizer.

**Separador UE-27.** Mantém-se só nas Contas Nacionais, e a Metodologia passa a dizer porquê: é a
única base construída da mesma maneira em todos os países da UE. O nível é discutível, a comparação
entre países é válida porque todos entram pela mesma via.

**Teste de regressão.** `test_engel_e_um_intervalo_ancorado_no_valor_do_ine` fixa o extremo inferior
na constante do INE, cobre a ausência das Contas Nacionais (o intervalo colapsa num ponto) e
verifica que a ordem dos extremos não é assumida.

### C1 · Afirmação sobre o salário mínimo — 10.08.2026

**Fonte fornecida:** Banco de Portugal, *Boletim Económico* de junho de 2026, **Caixa 5 — «A
distribuição dos salários dos trabalhadores por conta de outrem»**, com base em microdados da
Segurança Social.

**Veredito: não confirma «um quarto dos trabalhadores».** A Caixa 5 não publica essa fração, e o
próprio Boletim remete para outro documento quando se trata dos trabalhadores abrangidos pela RMMG
(nota de rodapé 27: *Políticas em análise «A retribuição mínima mensal garantida em Portugal»*,
Boletim de março de 2025). A frase foi **retirada**.

**O que o documento dá em troca — e é mais forte.** Três factos citáveis, todos na Caixa 5:

- **Índice de Kaitz de 91 % em 2025** (87 % em 2019): a RMMG equivale a 91 % do salário mediano do
  setor privado;
- **P50/P10 = 1,1**: a mediana está apenas 10 % acima do percentil 10;
- **o segundo decil da distribuição salarial não tem observações distintas** em 2019, 2023 e 2025,
  «refletindo a elevada concentração de trabalhadores em níveis salariais próximos do salário
  mínimo nacional».

Isto sustenta melhor o argumento do que a fração original: o cenário do salário mínimo não é um
caso extremo, é um caso quase mediano. Acrescentou-se também o contraponto internacional — pelo
*Structure of Earnings Survey*, o Kaitz português era de 69 % em 2024, **o mais elevado da área do
euro**.

**Ressalvas registadas na interface**, porque o universo não é o da aplicação: setor privado
apenas (exclui a Administração Pública), vínculos a tempo completo com 30 dias declarados e
remuneração igual ou superior a 80 % da RMMG.

### D1 · Período de referência do IDF — 10.08.2026

**Resolvido na fonte.** O documento metodológico do INE (Metainformação do IDF 2022/2023), que só
existe em imagem e teve de ser lido página a página, responde em dois pontos:

- **V.6.1.1, Períodos de recolha:** «O período de recolha decorrerá entre **3 de fevereiro de 2022
  e 5 de fevereiro de 2023**, correspondendo a **26 quinzenas**. Os dados de cada agregado são
  recolhidos ao longo de 14 dias.»
- **V.7.4, Ajustamentos dos dados: «Não aplicável.»**

O segundo ponto é o decisivo: o INE **não corrige os valores para uma data comum**. Os valores
publicados são uma média aos preços dos doze meses de recolha — não de um ano civil, e muito menos
de 2023.

**Consequência, medida:**

| Base de indexação | Valor mensal | |
|---|---|---|
| Ano civil de 2023 — o que a aplicação usava | 255,01 € | — |
| Ano civil de 2022 | 280,46 € | +25,45 € |
| **Janela de recolha, fev/2022 – jan/2023** | **276,06 €** | **+21,05 € (+8,3 %)** |

A aplicação subestimava o valor de topo em **21,05 €/mês**. Nem 2022 nem 2023 eram a resposta
certa: a resposta é a janela.

**O que foi feito.** `IDF_ANO_BASE = 2023` foi substituído por `IDF_JANELA_RECOLHA =
("2022-02", "2023-01")`, com a citação do documento metodológico em `config.py`.
`_atualizar_por_indice` passa a aceitar um par de meses além de um ano, e a base do IDF passa a
indexar pela média do índice nessa janela. A Metodologia explica a diferença e quantifica-a.

O intervalo da âncora passa de «255,01 € a 650,25 €» para **«276,06 € a 650,25 €»**.

### D2 · Correspondência IVA ↔ COICOP — 10.08.2026

**Fonte fornecida:** texto integral da **Lista I** (taxa reduzida, 6 %) e da **Lista II** (taxa
intermédia, 13 %) do Código do IVA.

**O que o levantamento revelou.** Nenhuma das nove classes é homogénea, e há divergências concretas
que a predefinição escondia:

- **Óleos e gorduras** — a mais material. A classe está predefinida a 6 %, mas os **óleos vegetais
  diretamente comestíveis** estão na Lista II a **13 %** (verba 1.5.3). É uma subcategoria inteira
  à taxa intermédia.
- **Peixe e marisco** — a Lista I refere «peixes e **moluscos**»; **não** refere crustáceos. Camarão,
  lagosta e sapateira ficam a 23 %. E as **conservas de moluscos** estão na Lista II, a 13 %,
  ao contrário dos moluscos frescos.
- **Carne** — as **alheiras** têm verba própria na Lista II (13 %); a restante charcutaria fica a
  23 %, porque a Lista I só cobre carne fresca ou congelada.
- **Pão e cereais** — bolos, bolachas e massas recheadas ficam fora da Lista I; os flocos prensados
  simples estão na Lista II.
- **Açúcar e doces** — a verba do açúcar (1.10 da Lista I) está **revogada**; o mel mantém-se a 6 %.
- **Outros alimentos** — a mais heterogénea: sal, produtos sem glúten e alimentos para lactentes a
  6 %; refeições prontas a 13 %; molhos e especiarias a 23 %.

**Decisão: declarar, não alterar as taxas.** As predefinições mantêm-se como taxa **predominante**
de cada classe, porque é o que a decomposição permite — não existe despesa aberta ao nível do
produto, e **nenhuma fonte pública reparte a despesa de cada classe pelas taxas legais**. Ponderar
as taxas dentro da classe exigiria inventar essas parcelas.

**O que foi feito.** Novo `IVA_MAPA` em `config.py`, com todas as taxas presentes em cada classe e
a verba da Lista que as sustenta. Novo painel no separador do IVA que mostra o levantamento
completo, assinala qual é a predefinida, e avisa que as parcelas não são quantificáveis. A tabela
de parâmetros deixou de dizer apenas «a correspondência é aproximada».

**Teste de regressão.** `test_mapa_do_iva_cobre_as_nove_classes_e_e_coerente` exige cobertura das
nove classes, taxas que existam no Código do IVA, ordenação e ausência de repetições, e — o mais
útil — que a taxa predefinida em `CLASSES` **conste** do levantamento. Sem isso, as duas fontes de
verdade podiam divergir em silêncio. Este teste já apanhou uma incoerência na primeira versão da
estrutura, que tratava como «exceção» aquilo que era o caso geral nas classes predefinidas a 23 %.

### C2 · Tabela das escalas — 11.08.2026

**O que foi feito.** O quadro de nove valores fixos, rotulado «valores ilustrativos», passa a ser
**calculado com os dados da sessão**: para cada escala e cada composição, a despesa sai de
`despesa_do_agregado` com a âncora ativa e o denominador é o rendimento equivalente do EU-SILC
convertido pelas unidades da OCDE modificada. A legenda declara a âncora e o ano do rendimento, e
avisa que os valores mudam com a base escolhida. Se o rendimento não estiver disponível, o quadro
dá lugar a uma nota em vez de a números inventados.

**Validação implícita, e é a parte interessante.** A linha da OCDE modificada dá **11,3 % nas três
composições** — exatamente a invariância que o texto ao lado afirma. Antes isso era uma
propriedade escrita à mão; agora é um resultado do cálculo, e serve de verificação de que o
cálculo está certo.

Com a base IDF: per capita 8,0 / 10,7 / 15,3 %; OCDE original 9,7 / 11,0 / 12,5 %; OCDE modificada
11,3 % constante.

### C3 · Cobertura do Törnqvist — 11.08.2026

**O que foi feito.** `dez[codigos].dropna()` eliminava a **linha** inteira: uma classe sem
observação em dezembro de um ano fazia esse ano desaparecer da série, e com ele um elo da cadeia do
índice. Passa a restringir-se às **classes** com série completa, não aos anos completos.
`indices_comparados` devolve em `df.attrs` as classes usadas e as excluídas, e a interface
declara-as — com aviso destacado quando alguma fica de fora.

Hoje entram as **nove classes**, pelo que o resultado não muda. O que muda é que deixa de haver um
modo de falhar silencioso: se amanhã faltar uma observação, perde-se um pouco de cobertura em vez
de se perder um ano inteiro, e o utilizador é informado.

### C4 · Janela do Observatório — 11.08.2026

**O que foi feito.** A legenda anunciava «variação entre 01/2022 e o fim da série» usando o mínimo
global, mas cada variação é medida no **período comum às duas fases desse produto** — que vai de
**16 a 58 períodos** de quatro semanas. Era falsa para boa parte dos produtos.

Passa a dizer que cada produto é medido na sua própria janela, com o intervalo de períodos
observado, e a tabela ganhou a coluna **«Janela medida»** (mm/aaaa – mm/aaaa) ao lado do número de
períodos. Acrescentou-se o aviso de que **variações medidas em janelas diferentes não são
comparáveis entre si** — que era a consequência prática, e não estava dita em lado nenhum.

### C5 · Formatação numérica — 11.08.2026

**Encontrei o padrão já partido.** A etiqueta do gráfico de Engel fazia
`f"{valor:.1f} %  ({gap:+.1f} p.p.)".replace(".", ",")` — a substituição apanhava também o sufixo,
e o gráfico mostrava **«p,p,»** em vez de «p.p.». Era exatamente o modo de falha previsto no
diagnóstico, já em produção.

**O que foi feito.** Três funções novas em `config.py`, ao lado de `euro()` e `percentagem()`:
`numero()` (milhares com espaço inquebrável e vírgula decimal), `milhoes()` e `pontos()` (pontos
percentuais ou de índice, com sufixo configurável). Todas as ocorrências do padrão antigo foram
substituídas — nove sítios em `app.py`.

**Um segundo problema, encontrado pelo caminho.** Existia um `_milhoes` definido **duas vezes** no
mesmo espaço de nomes: um valor numérico do SOFI no separador 2 e uma função no separador 4.
Funcionava só porque os separadores correm por ordem. O nome do valor passou a `_sofi_pessoas` e a
função deu lugar ao `milhoes()` partilhado.

**Teste de regressão.** `test_formatadores_nao_estragam_o_texto_a_volta` verifica os três
formatadores e trava especificamente o caso que falhava, com `assert "p,p," not in etiqueta`.

### C6 · Rótulo do salário médio — 11.08.2026

**O que foi feito.** O detalhe passa de «Remuneração média anual, bruta» para «Massa salarial ÷
trabalhadores por conta de outrem — **inclui tempo parcial**, pelo que fica abaixo do salário de um
trabalhador a tempo inteiro». A Metodologia ganhou um parágrafo a explicar que o divisor conta
todos os trabalhadores por conta de outrem, que o numerador exclui as contribuições do empregador,
e que o valor **não é comparável** com estatísticas de ganho médio convertidas a equivalentes a
tempo completo.

### D3 · Circularidade no teste das escalas — 11.08.2026

**A circularidade é real.** O grupo «3 ou mais adultos» não tem contagem publicada: os **3,288
adultos** foram deduzidos admitindo que o quadro Q.2.8 do INE aplica a escala OCDE modificada — que
é depois uma das três escalas avaliadas.

**Declarar não bastava; interessava saber se as conclusões sobrevivem.** Nova função
`sensibilidade_escalas()`, que recalcula tudo para sete valores entre 3,0 e 3,7 adultos:

| Adultos «3 ou +» | Per capita | OCDE original | OCDE modificada | Mais próxima |
|---|---|---|---|---|
| 3,000 | −18,7 % | −2,2 % | +13,0 % | OCDE original |
| 3,200 | −20,6 % | −4,2 % | +11,2 % | OCDE original |
| **3,288** ← pressuposto | −21,5 % | −5,0 % | +10,3 % | OCDE original |
| 3,500 | −23,4 % | −7,0 % | +8,4 % | OCDE original |
| 3,700 | −25,1 % | −8,8 % | +6,7 % | OCDE modificada |

**As duas conclusões resistem.** Em todos os cenários a OCDE modificada continua a subestimar o
custo alimentar (entre +6,7 % e +13,0 %) e o controlo da despesa total continua a inverter o sinal.
A OCDE original é a mais próxima do observado em seis dos sete cenários. Os pontos de rutura,
calculados por bissecção: a modificada só passaria à frente acima de **3,58 adultos em média**, e o
desvio só se anularia com **4,5 adultos** — valor sem sentido para um grupo «3 ou mais».

**A direção do resultado não depende do pressuposto; a magnitude depende.** É isso que passou a
estar escrito ao lado do resultado, com a tabela à vista, em vez de num comentário do código.

**Teste de regressão.** `test_sensibilidade_das_escalas_ao_pressuposto_circular` fixa a
invariância das conclusões no intervalo plausível **e** exige que a magnitude se mova mais de
3 pontos — senão o teste não estaria a testar nada.

### D4 · Fontes que envelhecem em silêncio — 11.08.2026

**O que foi feito.** Nova função pura `calculos.idade_fonte(referencia, limite_dias)`, que aceita
uma data ISO, um objeto de data ou um ano (tomado como 31 de dezembro — a leitura mais favorável à
fonte, para não exagerar a idade). Se a referência for ilegível devolve «não desatualizada»: na
dúvida, não se acusa a fonte.

Dois limites em `config.py`, ambos justificados:

- `LIMITE_DIAS_OBSERVATORIO = 60` — o Observatório publica de 28 em 28 dias; sessenta dias tolera
  um período em atraso e apanha o segundo;
- `LIMITE_ANOS_SOFI = 2` — o SOFI é anual, publicado a meio do ano seguinte; dois anos significa
  que há uma edição por incorporar.

O separador do Observatório passa a avisar com a idade em dias e a lembrar o script de recolha; o
bloco do SOFI mostra um erro destacado, com a idade em anos e o pedido explícito de confirmação
antes de citar.

**Estado hoje:** ambas frescas — Observatório recolhido há 1 dia, SOFI de 2025 há 223 dias — pelo
que nenhum aviso dispara. O caminho contrário está coberto por teste.

**Teste de regressão.** `test_idade_fonte_avisa_so_quando_deve` cobre data dentro e fora do prazo,
a conversão de ano para 31 de dezembro, e quatro formas de referência ilegível.

### Estado da bateria de testes

46 testes passam (38 iniciais + 8 novos), em cerca de um segundo. `agregados_do_ano` foi colocada
em `src/calculos.py`, e não em `app.py`, para que o teste não tenha de importar a aplicação — o que
disparava a recolha de dados e punha a bateria dependente da rede.

A aplicação renderiza sem exceções nas duas âncoras e nos dois caminhos do nível de preços.

---

*Documento de trabalho interno — UPE · DSSD · Secretaria-Geral do Governo.
Não constitui posição oficial.*
