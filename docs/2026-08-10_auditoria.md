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

> ⚠️ **Esta secção deixou de ser a última palavra.** Uma segunda auditoria, feita no mesmo dia
> sobre o `app.py`, encontrou **quinze novos itens**, dois deles críticos — a começar por
> **toda a família de séries de preços estar a ser lida de conjuntos que o Eurostat arquivou
> em dezembro de 2025**. Os dezassete itens abaixo continuam fechados e as suas correções
> continuam válidas; o que se segue não os revoga. Ver **[Segunda auditoria — 11.08.2026](#segunda-auditoria--11-de-agosto-de-2026)**, no fim do documento.

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

# Segunda auditoria — 11 de agosto de 2026

**Âmbito:** `app.py` na íntegra (3 671 linhas) e os quatro módulos de que depende — `src/config.py`,
`src/calculos.py`, `src/eurostat.py`, `src/observatorio.py`.
**Método:** leitura integral do código; reexecução da bateria de testes; **chamada real a todas as
ligações de dados**, com confronto contra a fonte; e reconstituição independente, fora da
aplicação, dos valores que ela apresenta.

**Numeração:** os itens desta segunda auditoria são **E1 a E15**, para não colidirem com os
A1–D4 da primeira.

> **Conclusão em três linhas.** As correções da primeira auditoria estão todas de pé e voltei a
> verificá-las uma a uma. Mas a aplicação **está a ler as três séries de preços de conjuntos que o
> Eurostat arquivou em dezembro de 2025** e substituiu por outros na passagem para a ECOICOP
> versão 2. Hoje, 11 de agosto de 2026, a aplicação apresenta **dezembro de 2025 como «último mês
> disponível»** e não dá erro nenhum: seis meses de inflação alimentar estão simplesmente fora do
> ecrã, e os ponderadores estão uma vaga atrasados.

**Resumo por gravidade:**

| | N.º | Efeito |
|---|---|---|
| 🔴 Crítico | 3 | Números desatualizados e nomenclatura errada, sem qualquer sinal ao utilizador |
| 🟠 Importante | 5 | Erro de método medido, ou rastreabilidade que não cumpre o que promete |
| 🟡 A corrigir | 7 | Rigor, robustez, reincidências de itens já fechados |
| ⚪ A declarar | 1 | Pressuposto legítimo que deve estar explícito |

> ✅ **Todos aplicados a 11.08.2026.** O terceiro crítico — **E16** — não constava do diagnóstico
> inicial: foi encontrado durante a aplicação, pela própria verificação criada no E3. O registo de
> cada correção está no fim do documento, e o balanço em
> **[Encerramento da segunda auditoria](#encerramento-da-segunda-auditoria--11082026)**.

---

## 🔴 E1 · A aplicação lê séries arquivadas: os preços param em dezembro de 2025

**Onde:** `src/eurostat.py` — `ponderadores()`, `indice_precos()`, `indice_classes()`,
`variacoes()`. Afeta, a jusante, praticamente todo o `app.py`.

**O que se passa.** O Eurostat encerrou a família ECOICOP ver.1 e passou a difundir o IHPC em
conjuntos novos. Os três que a aplicação usa **deixaram de ser atualizados**. Do próprio catálogo
do Eurostat, obtido hoje:

| Conjunto usado pela app | Título no catálogo | Última atualização |
|---|---|---|
| `prc_hicp_midx` | HICP — monthly data (index) **(1996-2025)** | 06.02.2026 |
| `prc_hicp_manr` | HICP — monthly data (annual rate of change) **(1997-2025)** | 06.02.2026 |
| `prc_hicp_inw` | HICP — item weights **(1996-2025)** | 20.08.2025 |

Os intervalos entre parênteses fazem parte do título oficial: o Eurostat **inscreveu o fim da
série no nome do conjunto**. Os substitutos, na pasta *HICP — ECOICOP ver.2*:

| Conjunto corrente | O que contém | Última atualização |
|---|---|---|
| `prc_hicp_minr` | Índice **e** taxas de variação, mensal — substitui `midx` **e** `manr` | 31.07.2026 |
| `prc_hicp_iw` | Ponderadores por rubrica | 18.07.2026 |
| `prc_hicp_ainr` | Índice e variação, anual | 17.07.2026 |

**Verificado em execução.** Pedidos reais feitos hoje, para Portugal:

```text
prc_hicp_midx  CP011  I15   -> ultimo periodo 2025-12
prc_hicp_manr  CP011  RCH_A -> ultimo periodo 2025-12
prc_hicp_inw   CP011        -> ultimo ano     2025
prc_hicp_minr  CP011  I25   -> ultimo periodo 2026-06
prc_hicp_minr  CP011  RCH_A -> ultimo periodo 2026-06   (agregados: 2026-07)
prc_hicp_iw    CP011        -> ultimo ano     2026
```

Não é uma falha da rede nem um atraso de publicação: no mesmo instante, `une_rt_m` devolve
2026-06, `namq_10_gdp` devolve 2026-Q2 e `earn_mw_cur` devolve 2026-S2. **Só as séries de preços
que a aplicação usa é que estão paradas** — porque foram arquivadas.

**Consequência, medida.** Reconstituí os dois valores de topo pelas duas vias:

| | App hoje (série arquivada) | Série corrente | Diferença |
|---|---|---|---|
| Último mês do índice | **dez/2025** | **jun/2026** | 6 observações |
| Ponderadores | 2025 | 2026 | uma vaga |
| Âncora **IDF**, agregado médio | 276,06 €/mês | **281,06 €/mês** | **+5,00 € (+1,81 %)** |
| Âncora **Contas Nacionais** | 650,25 €/mês | **662,02 €/mês** | **+11,77 € (+1,81 %)** |

E as variações homólogas por classe — que alimentam os nove cartões, o gráfico de contributos e a
comparação europeia — não são ligeiramente diferentes, são **outras**:

| Classe | dez/2025 (o que a app mostra) | jun/2026 (corrente) |
|---|---|---|
| Pão e cereais | 2,8 % | 2,5 % |
| Carne | **7,7 %** | **4,3 %** |
| Peixe e marisco | **7,3 %** | **10,7 %** |
| Leite, queijo e ovos | 2,0 % | 0,4 % |
| Óleos e gorduras | **−14,5 %** | **−2,0 %** |
| Fruta | **5,1 %** | **−0,3 %** |
| Legumes e hortícolas | 1,6 % | 3,8 % |
| Açúcar e doces | **4,3 %** | **−3,9 %** |
| Outros alimentos | 1,9 % | 2,7 % |

Três classes mudam de sinal. A carne aparece a subir quase o dobro do que sobe. Os seis meses de
inflação alimentar que não estão no ecrã são **3,3 · 3,7 · 3,7 · 4,6 · 3,4 · 3,1 %**.

Efeito conjunto no que um utilizador vê, para um casal com a escala OCDE original e a âncora IDF:

| | App hoje | Corrigido |
|---|---|---|
| Agregado médio nacional | 276,06 € | **281,06 €** |
| Despesa do casal | 237,02 € | **241,32 €** |
| Agravamento nos últimos 12 meses | 7,55 € | **6,96 €** |
| Inflação alimentar implícita | 3,29 % | **2,97 %** |

**Repare-se no sentido dos dois erros: o nível está subestimado e o agravamento está
sobrestimado.** Não é um desvio com uma direção só, que se pudesse descrever como conservador.

**O que agrava.** Três coisas, por ordem de gravidade:

1. **A aplicação não dá erro.** A mensagem verde de estado diz «Dados oficiais carregados ·
   último mês disponível **dez/25** · ponderadores de **2025**». Um leitor lê isto como *o
   Eurostat ainda não publicou mais nada* — que é exatamente a leitura que o separador
   Metodologia lhe ensina a fazer: «Se um valor parecer desatualizado, é porque a fonte ainda não
   publicou — não porque a aplicação não o foi buscar.» Neste caso é o contrário.
2. **A aplicação previu esta falha e errou a mitigação.** O aviso «Alteração metodológica de
   fevereiro de 2026», no separador Metodologia, descreve a transição corretamente e conclui: «A
   aplicação prefere automaticamente a base mais recente disponível, com recuo ordenado para as
   anteriores.» A preferência implementada é pela **unidade** (`I25` → `I15` → `I05` → `I96`), e o
   problema não é a unidade — é o conjunto. Em `prc_hicp_midx` **não existe** `I25`; a preferência
   nunca dispara e o recuo funciona perfeitamente, para a série errada.
3. **O aviso remata com «se as classes deixarem de responder, é nesta alteração que se deve olhar
   primeiro».** As classes continuam a responder. Só que respondem com dados de dezembro.

**Correção.** Migrar para `prc_hicp_minr` e `prc_hicp_iw`. Não é uma troca de nomes — há cinco
pontos onde a migração falha em silêncio se for feita à letra:

- **A dimensão mudou de nome: `coicop` → `coicop18`.** `_via_sdmx` faz
  `bruto.get("coicop", pd.Series([""] * len(bruto)))` e `_descodifica_jsonstat` devolve sempre a
  coluna `coicop`. Com o conjunto novo, **as nove classes colapsariam numa coluna vazia** e o
  `groupby("coicop")` juntaria tudo numa linha só, sem erro. É exatamente o modo de falha que a
  guarda do parâmetro `extra` foi criada para travar em `ilc_mdes03` — essa guarda tem de deixar
  de ser um caso especial e passar a ser a regra.
- **Índice e variação passam a vir do mesmo conjunto**, distinguidos por `unit` (`I25` para o
  índice, `RCH_A` para a variação homóloga). `indice_precos`, `indice_classes` e `variacoes`
  passam a partilhar uma função, e a unidade **tem de ir explícita na chave** — sem isso a
  resposta traz índice e taxas misturados.
- **`CP00` deixou de existir.** O agregado «Todos os produtos» chama-se agora `TOTAL`. Verificado:
  `prc_hicp_minr/M.RCH_A.CP00.PT` devolve **HTTP 400**. `COD_AGREGADOS`, em `config.py`, tem
  `CP00`. Os outros quatro (`FOOD`, `FOOD_NP`, `FOOD_P`, `TOT_X_NRG_FOOD`) respondem sem
  alteração.
- **`prc_hicp_iw` tem uma dimensão a mais:** `freq.coicop18.statinfo.geo.time`, com
  `statinfo = IW`. Chave: `A.{classes}.IW.{geo}`.
- **Cobertura histórica, confirmada:** `I25` cobre 1996-01 a 2026-06 para `CP011` e 2019-01 a
  2026-06 para as nove classes; `prc_hicp_iw` cobre 1996 a 2026. A janela do Törnqvist e as duas
  janelas de indexação das âncoras (ano civil de 2022; fev/2022–jan/2023) ficam **integralmente
  cobertas** — não se perde nada na migração.

---

## 🔴 E2 · As nove classes mudaram de conteúdo; os rótulos e o mapa do IVA descrevem a nomenclatura antiga

**Onde:** `src/config.py`, `CLASSES` e `IVA_MAPA`.

**O que se passa.** Os códigos `CP0111`–`CP0119` sobreviveram à revisão, mas **o que está dentro
deles mudou**. Rótulos oficiais, lado a lado, obtidos hoje das duas versões do conjunto:

| Código | ECOICOP ver.1 (rótulo da app) | ECOICOP ver.2 (rótulo atual) |
|---|---|---|
| CP0111 | Pão e cereais | Cereais e produtos à base de cereais |
| CP0112 | Carne | **Animais vivos**, carne e outras partes de animais terrestres abatidos |
| CP0113 | Peixe e marisco | Peixe e outros produtos do mar |
| CP0114 | Leite, queijo e ovos | Leite, outros lacticínios e ovos |
| CP0115 | Óleos e gorduras | Óleos e gorduras |
| CP0116 | Fruta | Frutos **e frutos de casca rija** |
| CP0117 | Legumes e hortícolas | Produtos hortícolas, **tubérculos e leguminosas** |
| CP0118 | Açúcar, doces, mel e chocolate | Açúcar, confeitaria **e sobremesas** |
| CP0119 | Outros produtos alimentares n.e. | **Refeições prontas** e outros produtos alimentares |

Os ponderadores movem-se em conformidade — não é só o rótulo:

| Classe | 2025 (ver.1) ‰ | 2026 (ver.2) ‰ |
|---|---|---|
| CP0113 Peixe | 31,03 | **28,29** |
| CP0115 Óleos e gorduras | 10,82 | **7,56** |
| CP0118 Açúcar e doces | 9,86 | **11,72** |
| CP0119 Outros alimentos | 9,30 | **10,59** |
| **Soma das nove** | **199,63** | **195,48** |

**Consequência mais material — e é no simulador de IVA.** A classe `CP0119` passou a ser
encabeçada por **refeições prontas a consumir**, que estão na **Lista II, verba 1.8, a 13 %**. A
aplicação predefine essa classe a **23 %**, e o `IVA_MAPA` descreve-a como «a das especiarias e
molhos». Com a nova composição, **a taxa predefinida deixou de ser plausivelmente a
predominante** — e o teste `test_mapa_do_iva_cobre_as_nove_classes_e_e_coerente`, que compara o
`IVA_MAPA` com o `CLASSES`, continua a passar porque compara a app consigo própria, não com a
nomenclatura em vigor.

O mesmo raciocínio aplica-se, em menor grau, a `CP0118` (absorve sobremesas), `CP0116` (absorve
frutos de casca rija) e `CP0112` (absorve animais vivos, que não são despesa alimentar das
famílias no sentido corrente).

**Correção.** Refazer, sobre o texto das Listas I e II, o levantamento do D2 — mas contra as
**definições da ECOICOP ver.2**, e não contra as da ver.1. Rever os nomes portugueses em
`CLASSES` para que descrevam o que a classe passou a conter. E acrescentar ao teste de coerência
do `IVA_MAPA` uma verificação que **não seja circular**: confrontar a lista de classes com os
rótulos devolvidos pela própria API, para que uma revisão futura da nomenclatura dispare o teste.

> ⚠️ **E2 não pode ser aplicado sozinho nem adiado para depois de E1.** Migrar os conjuntos sem
> rever os rótulos deixa a aplicação a chamar «Carne» a uma classe que inclui animais vivos, e a
> tributar refeições prontas a 23 %. Rever os rótulos sem migrar os conjuntos põe nomes novos em
> dados velhos. Vão juntos.

---

## 🟠 E3 · As fontes com API não têm verificação de frescura nenhuma

**Onde:** `src/calculos.py`, `idade_fonte()` — e a ausência de qualquer chamada equivalente para
as séries do Eurostat.

**O que se passa.** O item **D4** da primeira auditoria criou o `idade_fonte()` e aplicou-o ao
SOFI e ao Observatório, com este argumento: «Nem o SOFI nem o Observatório têm API: se ninguém os
atualizar, a aplicação continua a apresentá-los sem nunca dar erro.» A conclusão implícita — que
as fontes **com** API não têm esse problema, porque a rede avisaria — está errada, e o E1 é a
demonstração. Uma série arquivada responde com HTTP 200, devolve dados válidos e bem formados, e
simplesmente não avança.

**A verificação existe, foi bem construída, e foi apontada ao sítio errado.** Não faltava a
ferramenta: faltava aplicá-la ao caso que efetivamente falhou.

**Correção.** Passar `idade_fonte()` sobre o último período de **cada série obtida**, com limite
por periodicidade — mensal, 60 dias; semestral, 240; anual, 18 meses — e um aviso destacado no
topo da aplicação, não escondido no registo de ligações. Uma série mensal cujo último período
tenha mais de dois meses é, por si só, motivo para não citar os números até alguém confirmar
porquê.

---

## 🟠 E4 · O Laspeyres e o Törnqvist datam o mesmo dezembro de forma diferente — e 22 % do viés publicado é esse artefacto

**Onde:** `src/calculos.py`, `indices_comparados()`, linhas ~692 e ~701-702.

**O que se passa.** O painel «Cabaz fixo contra cabaz que acompanha o consumo» compara dois
índices. A correspondência entre ponderadores e momentos está documentada com cuidado, e é
respeitada no Törnqvist:

```python
q_ini = quotas.loc[anterior + 1] if (anterior + 1) in quotas.index else quotas.loc[anterior]
```

O ponderador do ano `y+1` representa dezembro de `y` — é a definição do Documento Metodológico do
IPC, que o próprio código cita. Mas o Laspeyres de base fixa usa:

```python
base = anos[0]
quotas_base = quotas.loc[base]
```

O ponderador do ano `base` refere-se a dezembro de `base−1`. **O mesmo dezembro-base é
representado por dois vetores de ponderadores distintos, com um ano de diferença**, nos dois
índices cuja diferença é precisamente o que se está a medir.

**Verificado, com os dados reais da sessão** (dezembros de 2020 a 2025):

| Ano | Laspeyres com `w(base)` | Laspeyres com `w(base+1)` | Törnqvist |
|---|---|---|---|
| 2020 | 100,000 | 100,000 | 100,000 |
| 2022 | 124,325 | 124,191 | 124,056 |
| 2024 | 130,670 | 130,473 | 130,291 |
| **2025** | **135,351** | **135,222** | **134,761** |

Viés acumulado apresentado: **0,590 pontos**. Viés com o ponderador coerente: **0,461 pontos**.
**A diferença, 0,129 pontos, é 22 % do número que a aplicação publica** — e é o número que
sustenta a frase «sobre uma subida acumulada de 34,8 %, é residual».

**A conclusão qualitativa aguenta** — 0,46 pontos continua a ser residual, e continua a ser
verdade que a substituição relevante acontece dentro das classes. Mas o painel existe justamente
para *medir em vez de afirmar*, e a medida está inflacionada em cerca de um quinto por uma
incoerência interna de datação.

**Correção.** Uma linha:

```python
quotas_base = quotas.loc[base + 1] if (base + 1) in quotas.index else quotas.loc[base]
```

E um teste que fixe a coerência: os dois índices têm de datar o dezembro-base pelo mesmo vetor.

---

## 🟠 E5 · O painel «endereços exatos desta sessão» oferece endereços que devolvem erro

**Onde:** `src/eurostat.py`, `_via_sdmx()` linha ~57 e `_via_stats()`.

**O que se passa.** `_via_sdmx` regista o endereço em `ENDERECOS` **antes** de fazer o pedido:

```python
ENDERECOS.append((dataset, _completo))
resp = requests.get(url, params=params, ...)
```

Se o pedido falhar e a aplicação recorrer à API Statistics, o endereço da tentativa falhada fica
registado na mesma — e `_via_stats` **nunca regista nada**. O painel «Ver os dados em bruto —
endereços exatos desta sessão» apresenta-o como sendo a proveniência do número.

**Verificado hoje, e não é hipotético.** Os ponderadores vieram pela API Statistics. O endereço
que o painel oferece para os verificar é:

```text
GET .../sdmx/2.1/data/prc_hicp_inw/A..CP0111+...+CP0119.PT?format=SDMX-CSV   ->  HTTP 400
```

**Consequência.** O texto do painel promete: «Servem para **verificar qualquer valor** sem
depender da aplicação, e para reproduzir o cálculo em Excel ou noutra ferramenta.» Quem seguir o
link dos ponderadores recebe um erro. Numa ferramenta cujo argumento central é a rastreabilidade,
é a promessa mais visível e a que hoje não se cumpre. E note-se que hoje **três** das ligações
(ponderadores, dimensão do agregado, salário mínimo) vêm pela API Statistics.

**Correção.** Registar depois do sucesso, não antes; registar também a via Statistics, com o
endereço completo com parâmetros; e marcar no painel a via de cada um. As tentativas falhadas têm
lugar no registo de diagnóstico, não na lista de verificação.

---

## 🟠 E6 · O cabeçalho de proveniência dos CSV atribui ao Eurostat ficheiros que não são do Eurostat

**Onde:** `app.py`, `csv_com_fonte()`, linhas ~513-523.

**O que se passa.** A função escreve um cabeçalho **fixo**:

```text
# Fonte dos dados: Eurostat (indice harmonizado de precos no consumidor e contas nacionais)
# Conjuntos: prc_hicp_midx, prc_hicp_manr, prc_hicp_inw, nama_10_co3_p3, ilc_lvph01
```

É a mesma função que exporta **oito** ficheiros diferentes, entre os quais:

- **«Descarregar série completa do Observatório»** — dados do **GPP**, recolhidos por script, que
  nunca passaram pelo Eurostat;
- **«Descarregar cabaz por quintil»** — níveis do **INE, IDF 2022/2023**;
- **«Descarregar simulação de IVA»** — cujas taxas e repercussão são parâmetros do utilizador.

A lista fixa de cinco conjuntos omite ainda `ilc_di03`, `earn_mw_cur`, `lfst_hhnhtych`,
`prc_ppp_ind_1`, `ilc_mdes03` e `nama_10_a10`, todos efetivamente usados.

**Consequência.** São **os ficheiros que saem da aplicação e circulam sozinhos** — precisamente
aqueles em que o cabeçalho de proveniência é a única coisa que resta. Um CSV do Observatório do
GPP a declarar-se Eurostat é uma atribuição de fonte errada num documento que pode acabar anexado
a uma nota.

**Correção.** A fonte passa a parâmetro obrigatório da função; a lista de conjuntos passa a ser
derivada de `dados["registo"]`, que já sabe quais responderam.

---

## 🟠 E7 · O coeficiente de Engel é documentado como `CP011/CP00` e é calculado como `CP011/TOTAL`

**Onde:** `src/eurostat.py`, `despesa_total_consumo()`; `app.py`, linhas ~2737 e ~2752.

**O que se passa.** A função tenta quatro códigos por ordem — `TOTAL`, `CP00`, `P31_S14`,
`CP_TOT` — e usa o primeiro que responda. Verificado hoje: responde **`TOTAL`**. Mas a legenda do
gráfico e o cabeçalho do CSV afirmam:

> Fonte: Contas Nacionais (`nama_10_co3_p3`), rácio **CP011/CP00**.

**Consequência.** É a mesma classe de problema que o **B3** — uma lista de candidatos cujo
resultado efetivo não chega ao rótulo. No B3 foi resolvido bem: o título do gráfico passou a
nomear a categoria PPP efetivamente obtida, com aviso quando é a de reserva. Aqui a doutrina não
foi aplicada. Hoje o valor está certo (16,37 % para Portugal em 2022, que reproduz os 16,4 %
documentados), mas o leitor que quiser reproduzir o cálculo procura um código que não foi usado.

**Correção.** Devolver o código utilizado, como já se faz para as PPP, e nomeá-lo na legenda e no
CSV. Se o código de recuo alguma vez for usado, avisar.

---

## 🟡 E8 · O padrão de formatação frágil do C5 sobreviveu num sítio

**Onde:** `app.py`, linhas ~1597-1602.

```python
st.caption(
    f"Em {_ano_sev}, **{...} %** entre quem está em risco de pobreza, contra "
    f"**{...} %** no total — "
    f"**{_sev_pobres / _sev:.1f}×**".replace(".", ",") + " mais."
)
```

Cadeias adjacentes concatenam-se em tempo de compilação: o `.replace(".", ",")` **aplica-se à
frase inteira**, não ao número. É literalmente o modo de falha que o C5 fechou em nove outros
sítios. Hoje não parte porque não há nenhum ponto literal no texto; parte na primeira reescrita
que introduza um «p.p.», um «n.º» ou uma abreviatura.

**Correção.** `pontos()` ou `numero()`, aplicados só ao número, como nos restantes nove.

---

## 🟡 E9 · Números derivados fixados à mão ao lado de números calculados

Reincidência do **C2**, em três sítios:

| Onde | Valor inscrito | Devia ser |
|---|---|---|
| ~3230 | «só acima de **3,58 adultos**», «só se anularia com **4,5 adultos**» | resultado de bissecção sobre `ESCALAS_TESTE_RACIO` — calculável |
| ~1564-1565 | «um problema de **2 %** da população», «são **14 %**» | `_sev` (1,9) e `_sofi_pt` (14,4), que estão na mesma função |
| ~1071 | «mais **2,3 vezes** de despesa alimentar contra mais **1,7 vezes** de despesa total» | rácios de 2022 entre as duas bases — derivam de constantes existentes |

O argumento do C2 vale sem alteração: aparecem ao lado de números calculados em direto e o leitor
não os distingue. Os dois últimos casos são **arredondamentos de valores que a app já tem na
mão** e que deixam de bater certo assim que a fonte for atualizada.

**Correção.** Calcular. Onde o cálculo não compensar, marcar com a data de apuramento.

---

## 🟡 E10 · `decompor` redistribui a despesa em silêncio quando falta um ponderador

**Onde:** `src/calculos.py`, `decompor()`, linha ~178.

```python
total_pesos = sum(v for v in pesos.values() if v and v > 0)
```

Se uma classe não vier do Eurostat, o seu peso é 0, sai do denominador, e **as oito restantes
absorvem 100 % da despesa** — cada uma com uma quota inflacionada, sem aviso nenhum. É o mesmo
modo de falha que o **C3** fechou no Törnqvist, onde passou a declarar-se quais as classes
excluídas. Aqui continua aberto, e é o cálculo mais central da aplicação.

**Correção.** Devolver a lista de classes em falta em `df.attrs`, como `indices_comparados` já
faz, e declará-la na interface.

---

## 🟡 E11 · `cabaz_quintis` compara um agravamento parcial com um orçamento total

**Onde:** `src/calculos.py`, `cabaz_quintis()`, linhas ~534-555.

O `agravamento` soma apenas as classes com variação disponível; o `agravamento_orcamento`
divide-o pelo orçamento **total** do quintil. Faltando uma classe, o numerador encolhe e o
denominador não — a coluna «Agravamento / orçamento» subestima, e é justamente a coluna que fecha
o argumento sobre a regressividade.

**Correção.** A mesma de E10: devolver a cobertura efetiva e declará-la quando não for total.

---

## 🟡 E12 · O nível de preços comparado é apresentado com zero casas decimais

**Onde:** `app.py`, linhas ~2597-2600.

```python
d1.metric(f"Portugal em {ano_pli}", f"{v:.0f}"...)
d2.metric("Face à média da UE-27", f"{numero(abs(v - 100))} % {posicao}")
```

`numero()` tem `casas=0` por omissão. Portugal está em **101,4** e a aplicação escreve **101** e
**«1 % mais caros»**. A grandeza comunicada é a distância à média europeia: arredondar 1,4 para 1
perde **quase um terço** dela. O documento da primeira auditoria cita, com razão, «1,4 % acima da
média europeia» — a aplicação não consegue mostrar esse número.

**Correção.** Uma casa decimal nos dois indicadores.

---

## 🟡 E13 · A vista de inflação parte com uma exceção técnica se o último mês vier vazio

**Onde:** `app.py`, linhas ~2815-2819.

Se nenhum país tiver observação no último período, `pd.DataFrame([])` não tem coluna `geo` e o
`.map(PAISES)` seguinte levanta `KeyError`. Fica contido pelo `painel()`, mas o utilizador recebe
um erro técnico em vez de «não há observações para este mês».

**Correção.** Guarda explícita antes de construir o *ranking*.

---

## 🟡 E14 · O ano-base do painel de viés de substituição desliza sozinho em cada 1 de janeiro

**Onde:** `app.py`, `carregar_dados()`, linha ~122.

```python
desde_indice = f"{ano - anos_historico}-01"      # anos_historico = 6
```

O ano-base do Törnqvist e do Laspeyres é o primeiro dezembro da janela pedida — hoje, 2020. A 1 de
janeiro de 2027 passa a 2021, **sem que ninguém decida**, e a métrica «Viés de substituição
acumulado desde dez/20» passa a medir outro período com o mesmo nome. Uma série que se compara
entre versões do documento tem de ter base estável.

**Correção.** Ano-base explícito em `config.py`, independente da janela de pedido, com a janela
dimensionada para o cobrir.

---

## ⚪ E15 · A extrapolação nacional na base Contas Nacionais é um híbrido de dois anos

**Onde:** `app.py`, linhas ~2420-2423 e ~2497-2509.

Na base Contas Nacionais, `media_agregado` resulta da despesa de **2022** dividida pelos agregados
de **2022**, atualizada a preços correntes — e é depois multiplicada pelos agregados de **2025**.
Cada passo está certo e cada um está justificado (B2 para o denominador, A3 para o multiplicador),
mas o produto não é o agregado de 2022 nem uma medição de 2026: é **o consumo real de 2022, a
preços de hoje, sobre a população de agregados de hoje**.

É a leitura defensável, e é a que a pergunta de política exige. Mas deve estar escrita ao lado do
número, porque não é o que um leitor infere de «poupança agregada anual».

**Correção.** Uma frase na legenda dos dois cartões nacionais.

---

## O que verifiquei e está correto — segunda auditoria

Para que o âmbito da garantia fique claro. Tudo o que segue foi **reexecutado**, não relido:

- **A bateria de 46 testes passa**, em 1,3 segundos.
- **As dezassete correções da primeira auditoria estão de pé.** Confirmei uma a uma contra a
  fonte: `ilc_di03` responde com `MEAN_EI` = 17 239 € e `MED_EI` = 14 564 € (2025); o salário
  mínimo dá 1 073 € em 2026-S2, que × 12/14 = 920 € legais; a série do EU-LFS devolve os oito
  anos, 4 182,6 a 4 562,1 mil agregados; `A010101` = 101,4 e a reserva `A0101` = 102,0; a
  privação alimentar de 2025 dá 1,9 / 5,5 / 1,3.
- **Os quadros do IDF são internamente coerentes.** A soma das nove classes reproduz o total
  publicado em quatro dos seis quintis e desvia-se **1 €/ano** nos outros dois — arredondamento do
  próprio quadro do INE. Os seis pesos orçamentais publicados reproduzem-se todos, a uma casa
  decimal, a partir dos níveis: 12,02 / 14,80 / 14,08 / 13,62 / 11,99 / 9,12.
- **O teste das escalas reproduz ao centésimo:** rácios previstos 2,3606 / 1,9524 / 1,6803 e
  desvios −21,5 % / −5,0 % / **+10,3 %**; o controlo da despesa total inverte o sinal, −10,9 %.
- **A aritmética do IVA reproduz ao cêntimo**, incluindo o exemplo que a interface apresenta
  (106 €, de 23 % para 6 %): receita cessante de **−13,82 €** com repercussão nula e **−14,65 €**
  com repercussão integral, **6,0 %** de amplitude — e independência exata da repercussão na
  isenção total, como o texto afirma.
- **A âncora das Contas Nacionais reproduz:** 27 318,5 M€ ÷ 4 102 600 ÷ 12 = **554,90 €**, com o
  denominador emparelhado no ano da despesa.
- **O coeficiente de Engel de Portugal reproduz:** 27 318,5 / 166 851,3 = **16,37 %** em 2022.
- **A decomposição é aditiva** e a soma dos contributos iguala a variação do total.
- **Todas as vinte e uma ligações respondem** e devolvem valores plausíveis — incluindo as três
  arquivadas do E1, que é precisamente o problema.

**O que não pude verificar.** A correspondência entre as nove classes da ECOICOP ver.2 e as
Listas I e II do Código do IVA (E2) exige o texto das Listas confrontado com as **novas**
definições de classe. Tenho o texto das Listas, do trabalho do D2; falta-me a decomposição da
despesa pelas novas subclasses, que o Eurostat publica a cinco dígitos — é trabalho a fazer, não
uma fonte em falta.

---

## Ordem de execução proposta

| # | Item | Gravidade | Porquê nesta posição |
|---|---|---|---|
| 1 | ✅ **E1 + E2** migração ECOICOP ver.2 | 🔴 | Tudo o resto está a jusante. **Não separar:** conjuntos novos com rótulos velhos é pior do que o estado atual, porque parece correto |
| 2 | ✅ **E3** frescura das séries com API | 🟠 | É o que impede a repetição do E1. Fazer **logo a seguir**, enquanto a causa está à vista — e foi aqui que apareceu o **E16** |
| 3 | ✅ **E5 + E7** rastreabilidade | 🟠 | Custo quase nulo, e são a promessa central da ferramenta. O E5 tem de ser refeito depois do E1, porque os endereços mudam |
| 4 | ✅ **E4** ponderador-base do Laspeyres | 🟠 | Uma linha; corrige 29 % de um número publicado |
| 5 | ✅ **E6** cabeçalho dos CSV | 🟠 | Ficheiros que circulam sozinhos, com atribuição de fonte errada |
| 6 | ✅ **E10 + E11** cobertura declarada | 🟡 | Mesma correção nos dois sítios; fecha o modo de falha que o C3 só fechou num |
| 7 | ✅ **E8, E9, E12, E13** | 🟡 | Rigor de apresentação, sem dependências |
| 8 | ✅ **E14** ano-base estável | 🟡 | Só se torna visível em janeiro; melhor resolver antes de o esquecer |
| 9 | ✅ **E15** declaração do híbrido | ⚪ | Uma frase |

**A ordem aguentou-se, com uma correção.** O E7 acabou por ser feito no passo 2 e não no 3: a
migração das Contas Nacionais obrigava a tocar exatamente no código da lista de candidatos. E o
valor do E4, estimado em 22 %, ficou em **29 %** depois de recalculado sobre os dados migrados.

**Recomendação sobre o uso entretanto.** Enquanto o E1 não estiver aplicado, os números da
aplicação são de **dezembro de 2025** e não devem ser citados como situação corrente. As
comparações entre composições, entre escalas, entre quintis e entre bases de âncora **mantêm-se
válidas** — são rácios internos e não dependem do mês. O que não se pode usar é o nível em euros,
a variação homóloga e a comparação europeia, apresentados como sendo de hoje.

## O que preciso de si

1. **Autorização para aplicar E1 e E2**, que alteram os números que a aplicação mostra. Está
   quantificado acima: âncoras +1,8 %, e variações por classe substancialmente diferentes.
2. **Nomes portugueses das nove classes na ECOICOP ver.2.** Posso traduzir os rótulos oficiais do
   Eurostat, mas se o INE já publicou a designação portuguesa da nomenclatura revista, é essa que
   deve ficar — e é fonte que a Inês encontra mais depressa do que eu.
3. **Confirmação de que se mantém a decisão de usar `CP011`** (produtos alimentares) e não `CP01`
   (alimentares e bebidas não alcoólicas). Na ver.2 os dois continuam a existir, com ponderadores
   de 195,47 ‰ e 207,35 ‰; a escolha atual é `CP011` e parece-me a certa, mas passa a valer a pena
   dizê-lo em texto, porque a nomenclatura nova torna a distinção mais visível.

---

## Registo de aplicação — segunda auditoria

### E1 + E2 · Migração para a ECOICOP versão 2 — 11.08.2026

Aplicados em conjunto, como o diagnóstico exigia.

**O que foi feito, na camada de dados.** `src/eurostat.py` passou de `prc_hicp_midx`,
`prc_hicp_manr` e `prc_hicp_inw` para **`prc_hicp_minr`** e **`prc_hicp_iw`**. Como o conjunto
novo traz o índice e as taxas de variação juntos, `indice_precos`, `indice_classes` e `variacoes`
passaram a partilhar a mesma chamada, distinguidas pela unidade — `I25`/`I15` para os níveis,
`RCH_A` para a variação homóloga. A unidade vai **explícita na chave**: omiti-la traria níveis e
taxas empilhados na mesma coluna de valores.

**A guarda que faltava, generalizada.** A dimensão de classificação chama-se `coicop18` no
conjunto novo. O código antigo lia-a com `bruto.get("coicop", "")` — com o conjunto novo isso
devolveria uma coluna vazia e as nove classes colapsariam numa só, sem erro. A regra inverteu-se:
nova função `_coluna_classe()`, o parâmetro `dim_coicop` atravessa `obter`, `_via_sdmx` e
`_via_stats`, **quem precisa da classificação declara-a, e a ausência é erro**. Deixou de ser um
caso especial do `ilc_mdes03` e passou a ser a doutrina da camada de acesso.

**`CP00` → `TOTAL`** em `config.py`. O agregado «Todos os produtos» mudou de código; o antigo
devolve HTTP 400 no conjunto corrente. Antes da correção, a via SDMX falhava e a de reserva
respondia com uma fatia arbitrária — outra vez o padrão do B1.

**Designações das classes.** Vieram do **anexo do relatório do IDF 2022/2023** — «Classificação
do Consumo Individual por Objetivo (COICOP, versão 2018)», páginas 54-55 —, fornecido pela Inês.
Não são tradução desta ferramenta. Cada classe passou a ter dois campos: `nome`, a forma curta
para cartões e gráficos, que é a que o levantamento de 07.08.2026 já usava no §2.1; e `oficial`,
a designação do INE, que acompanha a tabela detalhada, o painel do IVA e as exportações.

| Código | Antes (ECOICOP v1) | Agora (forma curta) | Designação oficial do INE |
|---|---|---|---|
| CP0111 | Pão e cereais | Cereais e derivados | Cereais e produtos à base de cereais |
| CP0112 | Carne | Carne | Animais vivos, carne e outras partes de animais terrestres abatidos |
| CP0113 | Peixe e marisco | Peixe e produtos do mar | Peixe e outros produtos alimentares do mar |
| CP0114 | Leite, queijo e ovos | Leite, lácteos e ovos | Leite, outros produtos lácteos e ovos |
| CP0115 | Óleos e gorduras | Óleos e gorduras | Óleos e gorduras |
| CP0116 | Fruta | Fruta e frutos de casca rija | Fruta e frutos de casca rija |
| CP0117 | Legumes e hortícolas | Hortícolas, tubérculos e leguminosas | Produtos hortícolas, tubérculos, bananas-pão, bananas para culinária e leguminosas |
| CP0118 | Açúcar e doces | Açúcar, confeitaria e sobremesas | Açúcar, confeitaria e sobremesas |
| CP0119 | Outros alimentos | Pré-preparados e outros | Alimentos pré-preparados e outros produtos alimentares n.e. |

**`IVA_MAPA` refeito contra as subclasses da COICOP 2018.** As verbas das Listas I e II não
mudaram — mudou o que cada classe contém, e portanto o que fica dentro e fora de cada verba. O
levantamento passou a citar a subclasse concreta (`01.1.5.1`, `01.1.3.4`, …) em vez de descrever
em geral, o que torna cada atribuição verificável.

> **Correção ao diagnóstico do E2, e é minha.** Escrevi que a classe `CP0119` tinha passado a ser
> encabeçada por refeições prontas e que, por isso, «a taxa predefinida deixou de ser
> plausivelmente a predominante». **Está errado, e a predefinição a 23 % mantém-se.** Fui verificar
> as subclasses das duas versões: a ECOICOP v1 já tinha `CP01194`, refeições prontas, dentro de
> `CP0119`; o que mudou foi o **rótulo** da classe, que passou a nomeá-las à cabeça, não o
> conteúdo. E a verba 1.8 da Lista II cobre o pronto a comer e levar e a entrega ao domicílio, que
> na COICOP caem no grupo **11.1, restauração**, e não em 01.1.9 — a subclasse `01.1.9.1` é
> pré-preparado de retalho. A conclusão do E2 mantém-se, mas por outra razão: o mapa tinha de ser
> refeito porque descrevia classes com fronteiras diferentes, não porque a taxa estivesse errada.

**Achado durante a aplicação, e mais interessante do que o item que o gerou.** Ao confrontar os
níveis do `IDF_CLASSES_QUINTIL` com o quadro da página 44 do relatório do INE, os nove valores
reproduzem exatamente — 420, 670, 403, 369, 119, 299, 324, 119, 149 — **contra as designações da
COICOP 2018**. Ou seja: **o IDF 2022/2023 já estava na versão 2018 desde o início, enquanto o
índice ainda estava na versão 1**. Durante todo esse período a aplicação cruzou as duas: estrutura
de despesa numa classificação, variação de preços na outra, sob o mesmo rótulo. É uma incoerência
que ninguém tinha visto — nem eu, na primeira auditoria — e que **a migração fecha por
consequência**: as duas fontes passaram a estar na mesma classificação. Ficou declarado no
separador da COICOP.

**Verificado em execução, com dados reais.** A aplicação renderiza **sem uma única exceção** nos
seis separadores. Os valores movem-se exatamente como o diagnóstico previu:

| | Antes | Depois |
|---|---|---|
| Mensagem de estado | último mês **dez/25**, ponderadores de **2025** | último mês **jun/26**, ponderadores de **2026** |
| Agregado médio nacional (IDF) | 276,06 € | **281,06 €** |
| Casal, escala OCDE original | 237,02 € | **241,32 €** |
| Agravamento nos últimos 12 meses | 7,55 € | **6,96 €** |
| Maior contributo | 🥩 Carne | **🐟 Peixe e produtos do mar**, 3,38 € |
| Agregados de enquadramento | via de reserva, `CP00` sem resposta | **SDMX 2.1**, série até **jul/26** |

A soma dos nove ponderadores passou de 199,63 ‰ para 195,48 ‰, que é o valor publicado para
`CP011` em 2026 — bate exatamente, o que confirma que as nove classes cobrem o agregado alimentar
na nomenclatura nova sem sobreposição nem lacuna.

**Testes de regressão — seis novos, a bateria passa de 46 para 52.** Nenhum repete o que já
estava coberto:

- `test_dimensao_coicop18_e_normalizada_para_coicop` — a dimensão declarada chega ao resto da
  aplicação com o nome de sempre;
- `test_sem_declarar_a_classificacao_as_classes_colapsam` — **exige que a via errada divirja**, e
  fixa em teste o modo de falha exato do E1: sem declaração, as nove classes ficam numa só;
- `test_classificacao_declarada_e_ausente_e_erro` — melhor falhar do que juntar;
- `test_conjuntos_do_ihpc_sao_os_correntes_e_nao_os_arquivados` — proíbe nominalmente os três
  conjuntos arquivados no código-fonte das quatro funções do IHPC, exige a unidade explícita na
  chave, e exige que a dimensão seja declarada. É o teste que impede a regressão por distração;
- `test_agregado_de_enquadramento_usa_o_codigo_da_ecoicop2` — `TOTAL`, nunca `CP00`;
- `test_classes_tem_designacao_oficial_da_coicop_2018` — toda a classe tem designação oficial, as
  nove são distintas, duas âncoras verificáveis no anexo do INE, e **os rótulos da versão 1 estão
  proibidos por nome**.

**O que não fica resolvido por isto.** Nada nesta correção impede que volte a acontecer: um
conjunto que seja arquivado amanhã continuará a responder com HTTP 200. É o **E3**, o passo
seguinte.

### E3 · Verificação de frescura das séries com API — 11.08.2026

**O que foi feito.** Nova função pura `calculos.frescura_das_series()`, apoiada em
`fim_do_periodo()`, que traduz a codificação de períodos do Eurostat — `2026`, `2026-06`,
`2026M06`, `2026-S2`, `2026-Q2` — na data em que o período fecha. Toma-se o **fim** do período, e
não o início, por ser a leitura mais favorável à fonte. Um período ilegível devolve
«não desatualizada» mas fica marcado como **não verificado**: na dúvida não se acusa, mas também
não se dá por confirmado.

**Os prazos não são uniformes, e essa é a decisão central.** Um prazo único acusaria de velhas as
fontes que são lentas por construção — as Contas Nacionais têm ano e meio de desfasamento e está
certo que tenham. O que se quer apanhar é a série que **parou**. Por isso `LIMITES_FRESCURA`, em
`config.py`, dá a cada série o seu desfasamento normal mais um ciclo, **com a razão escrita ao
lado** — e há um teste que exige que essa razão exista e que as duas séries mensais sejam as mais
apertadas, por serem as que falharam.

**Onde aparece.** Um erro destacado **no topo da aplicação**, antes da mensagem de estado, com a
série, o conjunto, o último período, a idade em dias e o prazo — e a indicação de que a causa mais
provável é o conjunto ter sido arquivado. E um quadro completo na Metodologia, «Estas séries ainda
estão a avançar?», com as onze séries vigiadas.

**Estado hoje:** nenhum aviso dispara. As onze séries estão dentro do prazo.

---

## 🔴 E16 · Segunda ocorrência do E1 — a âncora vinha das Contas Nacionais em COICOP 1999

> ✅ **Encontrado e corrigido a 11.08.2026.** Encontrado **pela verificação criada no E3**, o que
> é a melhor demonstração de que ela fazia falta.

**Onde:** `src/eurostat.py`, `despesa_alimentar()`, `despesa_total_consumo()` e
`despesa_alimentar_paises()`.

**Como apareceu.** Ao escrever o teste do E3, a série das Contas Nacionais disparou o aviso. A
primeira reação foi assumir prazo mal calibrado — as Contas Nacionais são lentas. Fui verificar
antes de alargar o prazo, e o alargamento teria sido um erro:

| Conjunto | Último ano, Portugal |
|---|---|
| `nama_10_co3_p3` (a âncora) | **2022** |
| `nama_10_a10` (salário médio) | 2025 |
| `ilc_di03` (rendimento) | 2025 |
| `prc_ppp_ind_1` (nível de preços) | 2025 |
| `lfst_hhnhtych` (agregados) | 2025 |

**Todos os outros conjuntos anuais estavam em 2025; só a âncora estava em 2022.** E o 2022 não era
um atraso português: era o último ano para **todos** os países — DE, ES, FR, IT, NL, EU-27.

**A causa, no catálogo do Eurostat**, exatamente com a mesma forma do E1:

| Conjunto | Título oficial | Atualizado |
|---|---|---|
| `nama_10_co3_p3` | Household final consumption expenditure by purpose **(COICOP 1999)** | parado em 2022 |
| **`nama_10_cp18`** | Household final consumption expenditure by purpose **(COICOP 2018)** | **30.07.2026** |

A transição para a COICOP 2018 não afetou só o índice de preços: afetou também as Contas
Nacionais, e a aplicação ficou no conjunto legado nas duas frentes. A dimensão volta a chamar-se
`coicop18`, pelo que a guarda criada no E1 serviu tal e qual.

**O que foi feito.** As três funções passaram para `nama_10_cp18`. Aproveitou-se para fechar o
**E7**: a lista de candidatos ao código do total — `TOTAL`, `CP00`, `P31_S14`, `CP_TOT`, com o
primeiro que respondesse — deu lugar a uma constante única, `TOTAL_CONSUMO = "TOTAL"`, verificada
na API e **nomeada na interface**. A legenda do gráfico de Engel e o cabeçalho do CSV passaram a
dizer o conjunto e os códigos efetivamente pedidos, em vez do `CP011/CP00` que nunca foi usado.

**Efeito, medido.** A âncora das Contas Nacionais desce ligeiramente, mas o que importa é outra
coisa:

| | Antes (`co3_p3`, 2022) | Depois (`cp18`, 2024) |
|---|---|---|
| Despesa alimentar nacional | 27 318,5 M€ | **33 037,8 M€** |
| Denominador (agregados do ano) | 4 102 600 (2022) | **4 473 300 (2024)** |
| Base mensal por agregado | 554,90 € | **615,46 €** |
| Fator de atualização por preços | **1,1930** | **1,0597** |
| Âncora final | 662,02 €/mês | **652,22 €/mês** |
| Coeficiente de Engel, Portugal | 16,4 % (2022) | **17,1 % (2024)** |

O valor final quase não se move — **mas passa a ser muito menos extrapolação**. Antes, 19 % do
valor vinha de indexar quatro anos de preços a uma estrutura de consumo de 2022; agora são 6 %
sobre uma estrutura de 2024. É a diferença entre um número medido e um número projetado, e não se
vê no resultado.

O intervalo da âncora passa de «276,06 € a 662,02 €» para **«281,06 € a 652,22 €»** — e o aviso de
idade da base na barra lateral passa de quatro anos de atraso para dois.

**Nota de método.** Em 2022, ano em que ambos os conjuntos existem, a despesa alimentar é
27 318,5 M€ na COICOP 1999 e 28 187,6 M€ na COICOP 2018 — **+3,2 %**. Parte é revisão das contas,
parte é a reclassificação. Não separei as duas causas e não tenho como o fazer com fontes abertas;
fica declarado.

**Testes de regressão — cinco novos, a bateria passa de 52 para 56.**
`test_serie_arquivada_e_apanhada_e_serie_lenta_nao_e` cobre os quatro casos que interessam: o
índice parado, o índice migrado, a âncora parada e a âncora migrada — e exige que a série lenta
**não** dispare, senão o mecanismo seria só um alarme permanente.
`test_conjuntos_do_ihpc_sao_os_correntes_e_nao_os_arquivados` passou a proibir também o
`nama_10_co3_p3`.

### E5 · Endereços de verificação — 11.08.2026

**O que estava errado.** `_via_sdmx` registava o endereço **antes** de fazer o pedido, e
`_via_stats` não registava nada. Uma tentativa falhada ficava listada como se fosse a proveniência
do número, e as séries obtidas pela via alternativa não tinham endereço nenhum.

**O que foi feito.** `_via_sdmx` e `_via_stats` passam a devolver `(dados, endereço)`, e é o
`obter()` que regista — **só quando aceita o resultado**, com a via identificada. O endereço é o
`resp.url` do pedido efetivo, com os parâmetros já resolvidos pelo `requests`, e não uma
reconstrução. O painel passa a mostrar a via de cada um.

**Verificado em execução.** Os **onze** endereços que a aplicação oferece nesta sessão respondem
todos com HTTP 200 — incluindo os dois que vêm pela API Statistics (`ilc_lvph01` e `earn_mw_cur`),
que antes apareceriam com o endereço SDMX que falhou.

**Teste de regressão.** `test_tentativa_falhada_nao_entra_na_lista_de_verificacao` força a via SDMX
a falhar, deixa a Statistics responder, e exige que fique registado **um único** endereço, o da via
que produziu o número.

### E4 · Ponderador-base do Laspeyres — 11.08.2026

**O que foi feito.** Uma linha em `indices_comparados()`:

```python
quotas_base = quotas.loc[base + 1] if (base + 1) in quotas.index else quotas.loc[base]
```

O ponderador que representa **dezembro de `base`** é o do ano `base + 1` — a mesma definição que o
Törnqvist já respeitava vinte linhas abaixo. O Laspeyres usava o do ano `base`, que se refere a
dezembro de `base − 1`.

**Efeito, recalculado sobre os dados já migrados** (dezembros de 2020 a 2025):

| | Viés acumulado |
|---|---|
| Ponderador de `base` — o que estava | 0,447 pontos |
| **Ponderador de `base + 1`** — o coerente | **0,319 pontos** |

**29 % do número publicado era o artefacto.** A conclusão qualitativa não muda — 0,32 pontos sobre
uma subida acumulada de cerca de 35 % continua a ser residual, e continua a ser verdade que a
substituição relevante acontece dentro das classes. Mas o painel existe para *medir em vez de
afirmar*, e a medida estava inflacionada em quase um terço por uma incoerência interna de datação.

**Teste de regressão.** `test_os_dois_indices_datam_o_dezembro_base_pelo_mesmo_ponderador` constrói
uma série em que o ponderador do ano-base e o do ano seguinte são quase opostos, e exige duas
coisas: que o cabaz fixo fique próximo do Törnqvist com o ponderador certo, **e que a via errada
divirja em mais de 40 pontos**. Sem a segunda metade, o teste passaria com a correção revertida.

### E6 · Proveniência dos ficheiros exportados — 11.08.2026

**O que foi feito.** `csv_com_fonte()` ganhou dois parâmetros: `fonte`, que identifica quem
produziu os dados **daquele ficheiro**, e `conjuntos`, que por omissão passa a ser **derivado do
registo de ligações da sessão** em vez de uma lista fixa de cinco nomes. A lista fixa omitia mais
de metade dos conjuntos usados e, depois da migração, teria ficado a nomear conjuntos arquivados.

As oito exportações foram revistas uma a uma:

| Ficheiro | Fonte declarada |
|---|---|
| Observatório de Preços | **GPP** — não passa pelo Eurostat |
| Cabaz por quintil | **INE, IDF 2022/2023** (níveis) + Eurostat (variações) |
| Decomposição por grupo | A **âncora ativa** — INE ou Eurostat, conforme a base escolhida — + Eurostat |
| Simulação de IVA | Eurostat + **parâmetros do utilizador**, com a advertência de que não é fonte oficial no seu conjunto |
| Coeficiente de Engel | Eurostat, Contas Nacionais (COICOP 2018) |
| Comparação UE-27, viés de substituição, série do índice | Eurostat, IHPC |

**Testes de regressão.** `test_csv_do_observatorio_nao_se_declara_eurostat` fixa o caso mais
gritante; `test_csv_declara_os_conjuntos_que_responderam_e_nao_uma_lista_fixa` exige que a lista
venha do registo, sem repetições, e **proíbe nominalmente** os conjuntos arquivados — que é o modo
de a lista fixa voltar a envelhecer.

### E10 + E11 · Cobertura declarada — 11.08.2026

Aplicados juntos: é a mesma correção em dois sítios, e é a que o **C3** já tinha feito no
Törnqvist e que não tinha sido estendida ao resto.

**E10 — `decompor()`.** Faltando o ponderador de uma classe, o seu peso é zero, sai do
denominador, e as restantes absorvem 100 % da despesa — cada quota inflacionada, sem aviso. Passa
a devolver `classes_sem_ponderador` e `classes_sem_variacao` em `df.attrs`. A interface distingue
os dois casos, porque as consequências são diferentes:

- **sem ponderador** → erro destacado: *todas* as quotas e valores em euros ficam sobrestimados;
- **sem variação** → aviso: quotas e euros intactos, só o agravamento fica subestimado.

**E11 — `cabaz_quintis()`.** O agravamento somava só as classes com variação, mas o
`agravamento_orcamento` dividia pelo orçamento **total** do quintil. Passa a devolver a `cobertura`
por quintil e a `cobertura_minima` em `attrs`, e a interface declara-a quando não é total,
dizendo exatamente qual coluna fica subestimada.

**Uma decisão que vale a pena registar.** O denominador da cobertura é a **soma das nove classes**,
e não o total publicado pelo INE. Os dois diferem 1 €/ano em dois dos seis quintis, por
arredondamento do próprio quadro — e isso não é falta de cobertura. Medir contra o total publicado
dava 99,96 % de cobertura com os nove valores todos presentes, o que teria feito o aviso disparar
sem razão.

**Testes de regressão — três novos.** Todos exigem que a **consequência** seja real, não apenas
que a declaração exista: com uma classe sem ponderador, as outras oito ficam com 1/8 em vez de 1/9;
com a carne fora, a cobertura dos quintis cai abaixo de 85 % e o agravamento encolhe mesmo.

### E8, E9, E12, E13 · Rigor de apresentação — 11.08.2026

**E8 — a última ocorrência do padrão do C5.** A legenda da privação severa fazia
`.replace(".", ",")` sobre uma cadeia de f-strings adjacentes, que o Python concatena em tempo de
compilação: a substituição apanhava a frase inteira, não o número. Passou a usar `percentagem()` e
`numero()`. O teste inclui a demonstração de que a via antiga **estragaria mesmo** — com um «n.º»
na frase, o resultado é «n,º».

**E9 — números derivados, calculados em vez de inscritos.** Nova função pura
`calculos.pontos_de_rutura_das_escalas()`, que apura por bissecção os dois pontos que estavam
fixos na interface. Reproduzem os valores escritos à mão: **3,578** e **4,529** adultos, contra
«3,58» e «4,5». No bloco da acessibilidade, os «2 %» e «14 %» passaram a vir de `_sev` e
`_sofi_pt`. E as frases que citavam «2,3 vezes» e «16,4 %» — desatualizadas pela migração das
Contas Nacionais — deram lugar à relação qualitativa, que é o que o argumento precisa, com os
valores a virem do `intervalo_engel` da sessão.

**E12 — nível de preços com uma casa decimal.** Portugal está em 101,4 e a aplicação escrevia
«101» e «1 % mais caros», perdendo quase um terço da grandeza que a frase comunica. Passa a
mostrar **101,4** e **1,4 %**, no indicador, no gráfico e nas etiquetas.

**E13 — `ranking` com colunas explícitas.** `pd.DataFrame([])` não tem a coluna `geo`, e o `.map`
seguinte levantava `KeyError`. Passa a construir-se com `columns=["geo", "valor"]` e a explicar o
caso em texto. Optou-se por isto e **não** por `st.stop()`, que teria parado a renderização de
todos os separadores seguintes — a cura seria pior do que a doença.

**Testes de regressão — quatro novos**, incluindo o caso do `ranking` vazio e a verificação de que
os pontos de rutura calculados coincidem com os que estavam fixos.

### E14 · Ano-base estável do painel de viés — 11.08.2026

**O que foi feito.** `ANO_BASE_VIES = 2019` em `config.py`, com a razão escrita ao lado: é o
primeiro dezembro com série completa das nove classes na ECOICOP versão 2. `indices_comparados()`
passou a aceitar `ano_base`, a usar a constante por omissão, e a **descartar os anos anteriores**
— antes o ano-base era simplesmente o primeiro da janela pedida, que é `ano corrente − 6` e
deslizava a cada 1 de janeiro. A janela de pedido passou a ser `min(ano − 6, ANO_BASE_VIES)`, para
garantir que cobre a base.

Se o ano fixado não estiver disponível, a série recua para o primeiro que esteja **e a interface
diz que recuou**, avisando que o viés deixa de ser comparável com versões anteriores do documento.

**Efeito.** O painel passa a encadear a partir de dezembro de 2019, com as nove classes, e o viés
acumulado é de **0,325 pontos em seis anos**. Deixa de haver um número publicado cujo período de
referência muda sozinho na passagem de ano.

**Testes de regressão — dois.** Um exige que o ano anterior ao fixado **fique de fora** — sem isso
a base teria deslizado; o outro cobre o recuo e verifica que o ano pedido e o usado ficam ambos
registados, para a interface os poder confrontar.

---

### E15 · O híbrido da extrapolação nacional, declarado — 11.08.2026

**O que foi feito.** Uma nota sob os dois cartões nacionais, apenas na base Contas Nacionais, a
dizer o que o número é: o **consumo real de 2024**, a **preços de junho de 2026**, sobre a
**população de agregados de 2025**. Cada passo está justificado — o denominador da âncora tem de
ser contemporâneo da despesa (B2), e o que se extrapola é o efeito de uma medida sobre o país de
hoje (A3) —, mas o produto não é uma medição de nenhum desses anos, e um leitor não infere isso
de «poupança agregada anual».

---

## Encerramento da segunda auditoria — 11.08.2026

**Os dezasseis itens estão fechados.** Quinze do diagnóstico inicial (E1 … E15) e um encontrado
durante a aplicação (**E16**), pela verificação de frescura criada no E3.

| Passo | Itens | Efeito principal |
|---|---|---|
| 1 | ✅ **E1 + E2** | Migração para a ECOICOP v2. Sete meses de dados repostos |
| 2 | ✅ **E3 + E16** (e **E7**) | Vigilância de frescura — e a segunda série arquivada que ela apanhou |
| 3 | ✅ **E5** | Endereços de verificação que respondem todos |
| 4 | ✅ **E4** | 29 % do viés publicado era artefacto de datação |
| 5 | ✅ **E6** | Cada CSV declara a fonte que é a sua |
| 6 | ✅ **E10 + E11** | Cobertura declarada em vez de silenciosa |
| 7 | ✅ **E8, E9, E12, E13** | Rigor de apresentação |
| 8 | ✅ **E14** | Ano-base que deixa de deslizar |
| 9 | ✅ **E15** | Declaração do híbrido |

**O que mudou no que a aplicação mostra:**

| | Antes | Depois |
|---|---|---|
| Último mês | dez/2025 | **jun/2026** |
| Ponderadores | 2025 (ECOICOP v1) | **2026 (ECOICOP v2)** |
| Âncora IDF | 276,06 €/mês | **281,06 €/mês** |
| Âncora Contas Nacionais | 650,25 €/mês (base 2022) | **652,22 €/mês (base 2024)** |
| Coeficiente de Engel | 12,0 % a 16,4 % | **12,0 % a 17,1 %** |
| Viés de substituição | 0,590 pontos (base móvel) | **0,325 pontos (base fixa em 2019)** |
| Nomenclatura | ECOICOP v1, rótulos desatualizados | **COICOP 2018, designações do INE** |

**A bateria passou de 46 para 69 testes.** Os vinte e três novos travam cada um dos modos de falha
encontrados, e vários verificam também que **a via errada diverge** — sem isso passariam com a
correção revertida.

**Três coisas que aprendi e que ficam inscritas no código:**

1. **Uma série que responde não é uma série que avança.** Foi o erro de fundo do E1 e do E16, e é
   agora uma verificação automática.
2. **Quem precisa de uma dimensão declara-a; a ausência é erro.** A guarda que existia só para o
   `ilc_mdes03` passou a ser a regra da camada de acesso, e foi ela que tornou a migração segura.
3. **Uma lista de candidatos esconde o que foi usado.** Valia para as categorias das PPP (B3), para
   o código do total (E7) e para os endereços de verificação (E5) — em todos os casos a correção é
   a mesma: escolher um, verificá-lo, e nomeá-lo na interface.

**O que fica por fazer, e é de fundo:** confrontar as Listas I e II do Código do IVA com as
**subclasses de cinco dígitos** da COICOP 2018, para saber quanto de cada classe segue taxa
diferente da predefinida. O `IVA_MAPA` diz hoje *o quê*; não diz *quanto*. Exige a despesa aberta
ao nível da subclasse, que o Eurostat publica — é trabalho por fazer, não fonte em falta.

> ✅ **Feito a 11.08.2026.** Ver **«D2 reaberto»**, a secção seguinte. O resultado não é o que eu
> esperava: a aproximação por classe é **pior do que parecia**, e agora está medida.

---

## 🔴 D2 reaberto · Quanto de cada classe segue cada taxa — 11.08.2026

O **D2** da primeira auditoria concluiu, e cito-me: «as parcelas não são quantificáveis com dados
abertos: nenhuma fonte pública reparte a despesa da classe por taxa legal». **Era verdade à data,
e deixou de ser** — não por ter aparecido fonte nova, mas porque a COICOP 2018 desce um nível
abaixo da nomenclatura anterior.

**O que a nomenclatura nova permite e a anterior não permitia.** O `prc_hicp_iw` publica
ponderadores a cinco e a seis dígitos. Três cortes resolvem as maiores ambiguidades:

| Corte novo | Ponderador PT, 2026 | Porque importa |
|---|---|---|
| `CP011131` **Pão** contra `CP011139` **Outros produtos de padaria** | 18,66 ‰ contra 13,81 ‰ | Reparte a maior classe do cabaz: o pão está na Lista I, a pastelaria não |
| `CP011513` **Azeite** dentro de `CP01151` Óleos vegetais | 4,01 ‰ de 5,84 ‰ | Isola **exatamente** a verba 1.5.3 da Lista II: o resto, 1,83 ‰, são os óleos correntes a 13 % |
| `CP01123` **Carne seca ou fumada** separada de `CP01122` carne fresca | 6,48 ‰ contra 28,11 ‰ | A Lista I só cobre fresca ou congelada |

Na nomenclatura anterior estes produtos partilhavam subclasse. Não era falta de fonte: era falta
de resolução.

**O método, e o que o impede de prometer de mais.** Cada componente do levantamento tem um grau de
certeza, e a distinção não é decorativa:

- **certa** — a subclasse cai inteira numa verba;
- **predominante** — é maioritariamente de uma taxa, mas não só;
- **mista** — atravessa taxas em proporção não repartível, e o peso vai para a parcela
  **indeterminada**, que **não é arbitrada**.

**O resultado, e é desconfortável.**

| | Ponderador | % do cabaz |
|---|---|---|
| À taxa reduzida, 6 % | 133,69 ‰ | **68,4 %** |
| À taxa intermédia, 13 % | 1,83 ‰ | 0,9 % |
| À taxa normal, 23 % | 48,50 ‰ | **24,8 %** |
| Indeterminado | 11,47 ‰ | 5,9 % |

**A simulação por classe assume que 88,6 % do cabaz está a 6 %** — porque sete dos nove grupos têm
essa predefinição. O apurado é **68,4 % a 74,3 %**, sendo o limite superior o que se obtém
admitindo que *toda* a parcela indeterminada cai na taxa reduzida.

**A base afetada por uma descida da taxa reduzida está sobrestimada entre 19 % e 30 %.** Os valores
de poupança do simulador, incluindo os agregados nacionais, são **majorantes**. Um cenário «cabaz
zero» sobre os grupos a 6 % não atinge a despesa que o simulador lhe atribui, porque uma parte
dessa despesa já hoje é tributada a 23 %.

**Por grupo, a qualidade da aproximação varia muito:**

| Grupo | Predefinida | Fração do grupo que a segue |
|---|---|---|
| Leite, lácteos e ovos | 6 % | **96,8 %** |
| Açúcar, confeitaria e sobremesas | 23 % | 92,4 % |
| Fruta e frutos de casca rija | 6 % | 90,4 % |
| Peixe e produtos do mar | 6 % | 86,3 % |
| Óleos e gorduras | 6 % | 75,8 % |
| Hortícolas, tubérculos e leguminosas | 6 % | 72,4 % |
| Carne | 6 % | 71,4 % |
| Pré-preparados e outros | 23 % | 61,7 % |
| **Cereais e derivados** | 6 % | **58,7 %** |

Os cereais são o pior caso e a maior classe: 13,81 ‰ de pastelaria e bolachas a 23 % dentro de uma
classe predefinida a 6 %. É o corte `CP011131`/`CP011139` que o revela.

**Limitação declarada.** Os ponderadores são do **IHPC**, que inclui a despesa de não residentes.
É a única fonte aberta que desce à subclasse — o IDF fica-se pelo quarto dígito. Serve para
repartir *dentro* de cada grupo, que é o uso aqui, mas o nível de cada parcela herda a limitação.
E 20,1 % do cabaz foi atribuído por **predominância**, não com certeza.

**O que foi feito.** `IVA_COMPONENTES` em `config.py`, com 63 componentes e a verba de cada um;
`eurostat.ponderadores_subclasses()`; `calculos.composicao_iva()` e `resumo_composicao_iva()`; um
painel no separador do IVA com o quadro por grupo, o aviso quantificado e o detalhe subclasse a
subclasse; e a nota de limitações passou a citar o intervalo em vez de dizer apenas «aproximada».

**Testes de regressão — seis novos.** O que mais interessa é
`test_parcela_indeterminada_nao_e_arbitrada`: o valor deste apuramento está em declarar o que não
se sabe, e um teste que só verificasse as somas deixaria passar uma versão que empurrasse o
marisco para os 6 %. Há também um que exige que **o assumido exceda o apurado por margem** — se
não excedesse, o trabalho não teria valido a pena — e um que trava a incoerência entre `taxa=None`
e `certeza="mista"`, que são a mesma afirmação dita duas vezes e divergiriam em silêncio.

**Fica em aberto, e é decisão sua.** O simulador continua a aplicar **uma taxa por grupo**. Com o
apuramento feito, passa a ser possível aplicar a taxa do cenário **apenas à parcela que hoje está
à taxa de partida** — o que é mais próximo de como uma alteração do IVA é legislada, produto a
produto. Muda o significado dos resultados e a leitura da tabela editável, pelo que não avancei
sem decisão. O que está feito é o que permite tomá-la com números à frente.

---

*Documento de trabalho interno — UPE · DSSD · Secretaria-Geral do Governo.
Não constitui posição oficial.*
