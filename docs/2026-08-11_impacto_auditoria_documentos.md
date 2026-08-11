# O que a auditoria muda nos documentos do Gabinete

**Data:** 11 de agosto de 2026 · **Âmbito:** `2026-07-21_UPE_NG_SETCS_Cabaz_NotaEnquadramento.html`
e `2026-08-07_UPE_Cabaz_DadosNovos.docx`
**Base:** os dezassete itens da auditoria de 10.08.2026, todos aplicados e verificados em execução.

> **Em duas linhas.** A maior parte dos números dos dois documentos **resiste à auditoria** — e isso
> está verificado, não presumido. O que muda são **seis pontos**, dos quais dois são erros a
> corrigir, dois são atualizações de valores com a mesma conclusão, e dois são ressalvas que passam
> a ser exigíveis.
>
> ✅ **Aplicado a 11.08.2026 nos dois documentos.** Ver «Registo de aplicação», na Parte C.

**Resumo:**

| | Nota de enquadramento | Word «Dados novos» |
|---|---|---|
| 🔴 Erros a corrigir | 1 | 2 |
| 🟠 Valores a atualizar | 0 | 2 |
| 🟡 Ressalvas a acrescentar | 2 | 2 |
| ✅ Verificado sem alteração | 4 blocos | 3 blocos |

---

## Parte A · Nota de enquadramento (HTML)

### 🔴 A1 · O Observatório ainda aparece com «26 produtos» no §1.4

**Onde:** §1.4, tabela de fontes, linha «GPP — Observatório de Preços Agroalimentar».

> «Preços de **26 produtos** ao longo da cadeia (produção → consumo, via SIMA) e análise de margens
> por fileira; boletins mensais **desde 09.2023**.»

Na correção de 08.08.2026 atualizei o §1.1 para 39 produtos e deixei lá a nota de correção — **mas
não corrigi a mesma afirmação no §1.4**. O documento contradiz-se a si próprio a três secções de
distância. É um lapso meu da sessão anterior, não um achado novo da auditoria.

**Substituir por:**

> «Preços de **39 produtos** ao longo da cadeia (produção → consumo, via SIMA) e análise de margens
> por fileira; boletins em períodos de quatro semanas, com **séries que recuam a 3 de janeiro de
> 2022** (58 períodos à data da última extração, 10.08.2026).»

A menção «desde 09.2023» também precisa de cuidado: é a data de início dos **boletins**, não das
séries. O §1.1 já faz essa distinção; o §1.4 não.

### 🟡 A2 · Eixo 5 (acessibilidade): dizer qual salário mínimo

**Onde:** §1.5, eixo 5 — «Relacionar o custo do cabaz com o rendimento disponível mediano (ou com
o salário mínimo)».

A auditoria (A2) mostrou que **há dois valores e a escolha não é indiferente**. O Eurostat não
publica o valor legal: publica a RMMG em duodécimos de 14 mensalidades. Em 2026, valor legal
**920 €/mês**, valor difundido **1 073 €/mês** — 16,7 % de diferença, confirmada em toda a série
(957→820 em 2024, 1 015→870 em 2025, 1 073→920 em 2026).

**Acrescentar ao eixo 5:**

> Nota metodológica: ao usar o salário mínimo como denominador, especificar qual. Para uma fração
> **mensal** do orçamento a base correta é a **média mensal de 14 mensalidades** (1 073 € em 2026),
> que dilui os subsídios pelos doze meses; o valor legal (920 €) atribuiria a dezembro um esforço
> que na prática não existe. O Eurostat (`earn_mw_cur`) publica a primeira, não a segunda — e
> rotulá-la como «valor legal» sobrestima o rendimento em 16,7 %.

### 🟡 A3 · Eixo 5: há fonte oficial para sustentar a relevância do cenário

**Onde:** o mesmo eixo 5.

O eixo propõe o rácio face ao salário mínimo sem justificar por que é um cenário relevante. O
*Boletim Económico* do Banco de Portugal de junho de 2026 (Caixa 5) dá o fundamento, com fonte
citável:

- **Índice de Kaitz de 91 % em 2025** (87 % em 2019) — a RMMG equivale a 91 % do salário mediano do
  setor privado;
- **P50/P10 = 1,1** — a mediana está apenas 10 % acima do percentil 10;
- **o segundo decil da distribuição salarial não tem observações distintas**, «refletindo a elevada
  concentração de trabalhadores em níveis salariais próximos do salário mínimo nacional»;
- pelo *Structure of Earnings Survey*, o Kaitz português era de 69 % em 2024, **o mais elevado da
  área do euro**.

Ressalvas de universo a acompanhar a citação: setor privado (exclui a Administração Pública),
vínculos a tempo completo com 30 dias declarados e remuneração ≥ 80 % da RMMG.

**Isto substitui com vantagem** a formulação que a aplicação tinha e que foi retirada — «cerca de um
quarto dos trabalhadores aufere a remuneração mínima» —, que **não é confirmável**: a Caixa 5 não
publica essa fração e o próprio Boletim remete para outro documento quanto aos trabalhadores
abrangidos. Se a nota vier a usar uma fração, tem de vir do relatório da RMMG (GEE/MTSSS), não daqui.

### ✅ A4 · Verificado e confirmado, sem alteração

Estes blocos foram reexecutados contra as fontes e **reproduzem-se exatamente**:

**§1.3, caixa da correção de 08.08.2026 — o mecanismo do efeito regressivo.** Todos os valores
conferem, com mês de referência **dezembro de 2025**: inflação de 3,79 % no 1.º quintil e 3,97 % no
5.º, amplitude de 0,18 p.p. com o máximo no quintil mais rico; exposição de 14,8 % contra 9,1 %
(rácio 1,63); orçamentos de 1 358 € contra 2 916 €/mês; agravamento de 0,51 % contra 0,33 % do
orçamento, e de 6,91 € contra 9,67 € em euros.

⚠️ Estes valores são **sensíveis ao mês de referência**. Se a nota for reeditada, reconfirmar — a
amplitude entre quintis é de 0,18 p.p. e o sinal pode inverter-se de mês para mês. É por isso que a
própria caixa argumenta a favor da exposição orçamental, que é estrutural, e não da diferença de
taxas.

**§1.5, eixo 4 — o viés de substituição.** Reproduzido ao algarismo: base dezembro de 2020,
**+0,59 pontos de índice em cinco anos**, **+0,12 p.p. por ano**, sobre uma subida acumulada de
**34,8 %**. A auditoria acrescenta uma garantia que não existia: o item C3 corrigiu um `dropna()`
que podia eliminar anos inteiros da série sem aviso, e a verificação confirma que **as nove classes
têm série completa em todos os dezembros do período** — não há anos em falta a contaminar o
cálculo.

**§1.1, caixa do IVA Zero.** Os valores (−10,14 % ASAE; −8,45 % e +4,71 % DECO) mantêm-se como
apurados em 06.08.2026.

**§1.4, caixa das duas afirmações sobre a ASAE.** Mantém-se.

### 🟡 A5 · Dois pontos de decisão, não erros

**Designação do inquérito.** A nota usa «IDEF 2022/2023» em §1.1, §1.4 e no eixo 1; o Word e a
aplicação usam «IDF 2022/2023», que é a designação atual do INE. Uniformizar.

**Eixo 3 (desagregação territorial).** A nota propõe cruzar preços com densidade de insígnias e
acessibilidade ao retalho. Na aplicação **abandonámos essa componente** por decisão de 10.08.2026,
por não haver dados abertos da oferta retalhista. A nota é uma proposta de trabalho, não uma
afirmação factual, pelo que não está errada — mas convém decidir se se mantém como proposta ou se
se assinala a restrição já conhecida.

---

## Parte B · Word «Dados novos» (a aplicar por si)

> Conforme combinado, não edito este ficheiro. Abaixo vai o que muda, com o texto de substituição.

### 🔴 B1 · §2.4 — a frase sobre o divisor deixou de ser verdadeira

**Texto atual:**

> «Portugal: 4 149 096 agregados (Censos 2021, quadro 4.02). **Confirma exatamente o divisor usado
> na ferramenta da UPE.**»

Depois das correções B1 e B2 da auditoria, **a aplicação já não usa esse número como divisor**. Usa
dois números diferentes, para dois fins diferentes:

- **denominador da âncora das Contas Nacionais** → agregados **do ano da despesa** (2022):
  **4 102 600** (Eurostat, Inquérito ao Emprego);
- **extrapolação nacional do simulador de IVA** → **ano mais recente** (2025): **4 562 100**.

Os Censos passaram a ser o **valor de recuo**, usado só se a série anual do Eurostat falhar ou
devolver valor implausível.

**Substituir por:**

> Portugal: 4 149 096 agregados (Censos 2021, quadro 4.02). É a fonte autoritativa — apuramento
> exaustivo — e serve de valor de recuo na ferramenta da UPE. Para o cálculo da âncora, porém, a
> ferramenta usa o número de agregados **do mesmo ano da despesa**, obtido da série anual do
> Eurostat (Inquérito ao Emprego): **4 102 600 em 2022**. Numerador e denominador têm de ser
> contemporâneos; dividir a despesa de 2022 pelos agregados de 2025 (4 562 100) baixaria a âncora
> 9,1 % por razão nenhuma.
>
> Os dois universos não coincidem: o Inquérito ao Emprego é uma amostra e exclui alojamentos
> coletivos, pelo que lê sistematicamente abaixo do recenseamento. Em 2021, ano em que ambos
> existem: 3 939 900 contra 4 149 096 — menos 5,0 %.

### 🔴 B2 · §3.2 — a linha do Leite UHT mistura duas janelas

**Linha atual:** Leite UHT MG · produção **+33,3 %** · consumo **+61,8 %** · margem 0,19 € → 0,42 €
· **+121,1 %**.

Verifiquei observação a observação. A série de **produção do leite termina em 07/2025**; a de
consumo continua até 05/2026. A linha combina uma variação de produção medida até 07/2025 com uma
variação de consumo medida até 05/2026 — que é o valor que consta do §3.1, não o do período comum.

As colunas da margem, essas, **já usam o período comum** (0,19 € → 0,42 € é a diferença em 01/2022
e em 07/2025). A linha está portanto **internamente incoerente**.

**Valor correto no período comum** (01/2022 – 07/2025, 45 períodos): produção +33,3 %, consumo
**+63,6 %** (0,55 € → 0,90 €), margem 0,19 € → 0,42 €, **+121,1 %**.

**Correção:** consumo **+61,8 % → +63,6 %**. As restantes colunas mantêm-se. Verifiquei também as
outras treze linhas do quadro: **todas conferem** — a incoerência é só nesta.

### 🟠 B3 · §4.1 — a tabela da divergência entre fontes

Com o denominador emparelhado ao ano da despesa (4 102 600 em vez de 4 149 096):

| | Alimentação | Despesa total |
|---|---|---|
| Contas Nacionais ÷ agregados ÷ 12 — **atual** | 549 €/mês | 3 351 €/mês |
| Contas Nacionais ÷ agregados ÷ 12 — **corrigido** | **555 €/mês** | **3 389 €/mês** |
| IDF, medição direta | 239 €/mês | 1 992 €/mês |
| Rácio — atual | 2,29 × | 1,68 × |
| Rácio — **corrigido** | **2,32 ×** | **1,70 ×** |

E, em consequência, as taxas de cobertura descem cerca de 1,1 % em termos relativos:

| Taxa de cobertura | Atual | Corrigida | Intervalo UE |
|---|---|---|---|
| Consumo total | 59,4 % | **58,8 %** | 50 % – 97 % (continua dentro) |
| Alimentação | 44,4 % | **≈ 43,9 %** | 58 % – 108 % (continua abaixo) |

**As conclusões do §4.1 não mudam** — o consumo total continua dentro do padrão europeu e a
alimentação continua fora, precisamente na categoria de menor disparidade entre países. Muda o
algarismo, não o argumento.

*(Confirmei o valor do consumo total por cálculo independente: 58,8 %. O da alimentação apresento
como aproximação porque o Word calcula sobre COICOP 01 — alimentares **e** bebidas não alcoólicas —
e eu reproduzi sobre 01.1; a variação relativa de −1,1 % aplica-se a ambos.)*

### 🟠 B4 · §4.1 — a frase do intervalo, duas correções

**Texto atual:**

> «qualquer valor absoluto de despesa alimentar por agregado deve ser apresentado como intervalo —
> **239 a 549 €/mês a preços de 2022** — e não como valor único.»

Duas correções, uma de valor e outra de rigor:

1. o limite superior passa a **555 €/mês** (B3 acima);
2. **«a preços de 2022» é impreciso para o lado do IDF.** O documento metodológico do INE
   (Metainformação do IDF, V.6.1.1) fixa a recolha entre **3 de fevereiro de 2022 e 5 de fevereiro
   de 2023, em 26 quinzenas**, e o V.7.4 declara **«Ajustamentos dos dados: não aplicável»** — o INE
   não corrige os valores para uma data comum. Os 239 € estão aos preços médios desses doze meses,
   não aos de 2022.

**Substituir por:**

> qualquer valor absoluto de despesa alimentar por agregado deve ser apresentado como intervalo —
> **239 a 555 €/mês** — e não como valor único. Os dois extremos não estão exatamente na mesma base
> temporal: o das Contas Nacionais refere-se ao ano civil de 2022; o do IDF, aos preços médios da
> janela de recolha, entre fevereiro de 2022 e fevereiro de 2023, que o INE não ajusta a uma data
> comum (Metainformação do IDF, V.6.1.1 e V.7.4).

> **Nota lateral, sem efeito no Word.** Esta mesma descoberta teve efeito material na aplicação: a
> indexação do IDF ao mês corrente partia do ano civil de 2023 e passou a partir da janela de
> recolha, o que subiu a âncora de **255,01 € para 276,06 €/mês** (+8,3 %). O Word apresenta valores
> a preços de 2022, pelo que não é afetado — mas se alguma versão futura citar o valor atualizado,
> é este o número.

### 🟡 B5 · §3.2 — acrescentar a janela de cada produto

O quadro apresenta catorze produtos lado a lado como se fossem comparáveis. **Não são:** cada
variação é medida no período comum às duas fases **desse produto**, que vai de **16 a 58 períodos**
de quatro semanas.

**Acrescentar duas colunas** (janela e n.º de períodos) e uma ressalva. Valores apurados a
10.08.2026:

| Produto | Janela | Períodos |
|---|---|---|
| Leite UHT MG | 01/2022 – 07/2025 | 45 |
| Pêra | 01/2022 – 05/2026 | 45 |
| Maçã | 01/2022 – 05/2026 | 56 |
| Laranja | 01/2022 – 05/2026 | 56 |
| Batata | 01/2022 – 05/2026 | 57 |
| Frango, Ovo M, Ovo L, Cenoura, Porco, Tomate, Alface, Pescada, Curgete | 01/2022 – 05/2026 | 58 |

**Ressalva a acrescentar ao rodapé do quadro:**

> As variações de cada produto são medidas no período comum às suas duas fases, indicado na coluna
> «Janela». **Produtos com janelas diferentes não são comparáveis entre si** — o leite, por exemplo,
> é medido até julho de 2025, porque a série de produção termina aí.

*(Os três produtos com janelas mais curtas — Arroz Carolino 16, Brócolo 19 e Cebola 20 períodos —
estão bem excluídos do quadro. O rodapé atual já os menciona.)*

### 🟡 B6 · §4.2 — declarar a circularidade do teste das escalas

O quadro conclui que «a escala subestima o custo alimentar em cerca de 10 %». O número depende de um
pressuposto que convém declarar: os **3,288 adultos** do grupo «3 ou mais» foram deduzidos
admitindo que o quadro Q.2.8 aplica a **escala OCDE modificada** — que é depois uma das escalas
avaliadas.

Testei a sensibilidade, variando esse pressuposto entre 3,0 e 3,7 adultos. **As conclusões
resistem:** a subestimação mantém-se em todos os cenários, entre **+6,7 % e +13,0 %**; o controlo da
despesa total inverte o sinal em todos; e a OCDE original é a mais próxima do observado em seis dos
sete. A modificada só passaria à frente acima de **3,58 adultos em média**, e o desvio só se
anularia com **4,5** — valor sem sentido para um grupo «3 ou mais».

**Acrescentar ao rodapé do §4.2:**

> O grupo «2 ou mais adultos» não tem contagem publicada de adultos: os 3,288 do subgrupo «3 ou
> mais» foram deduzidos admitindo que o Q.2.8 aplica a escala OCDE modificada, que é uma das
> escalas avaliadas. Testando o pressuposto entre 3,0 e 3,7 adultos, a subestimação fica entre
> +6,7 % e +13,0 % e o controlo inverte o sinal em todos os cenários: **a direção do resultado não
> depende do pressuposto; a magnitude depende**.

### ✅ B7 · Verificado e confirmado, sem alteração

**§1.1, §1.2 e §1.3 — os quadros do IDF por quintil.** Conferem integralmente com as fontes: as
nove classes COICOP, os totais por quintil, os pesos no orçamento e os valores mensais. A soma das
nove classes fecha com o total 01.1 a menos do arredondamento do próprio quadro do INE (1 €/ano).

**§3.1 — as maiores subidas ao consumidor.** Os treze produtos conferem. A extração da aplicação é
de 10.08.2026 contra 07.08.2026 no Word, mas a cobertura é idêntica (39 produtos, 58 períodos,
último período P6/2026) e os valores não mudaram.

**§4.4 — a série de privação alimentar.** Confere com o `ilc_mdes03` nas três linhas e nos seis anos.

**§5 — «Correções a introduzir na nota de enquadramento».** As cinco linhas **já foram aplicadas** à
nota em 08.08.2026, com caixas de correção datadas. Sugiro marcar a tabela como executada, para não
ficar a sugerir trabalho pendente.

---

## Parte C · Registo de aplicação — 11.08.2026

**Tudo aplicado**, nos dois documentos, a pedido expresso da Inês («vamos avançar com as correções;
quero também que faças as alterações no word»). A edição do Word é uma exceção à regra habitual —
normalmente indico em texto e ela aplica.

**Cópias de segurança feitas antes de qualquer alteração**, na mesma pasta:

- `2026-08-07_UPE_Cabaz_DadosNovos_antes_auditoria_20260811_104622.docx`
- `2026-07-21_UPE_NG_SETCS_Cabaz_NotaEnquadramento_antes_auditoria_20260811_104622.html`

### Nota de enquadramento (HTML)

| | O que ficou |
|---|---|
| **A1** | §1.4 passa a «39 produtos», com a distinção entre início dos **boletins** (09.2023) e início das **séries** (03.01.2022). Caixa de correção datada acrescentada, no formato das anteriores. |
| **A2** | Eixo 5 ganhou a nota metodológica sobre qual salário mínimo usar, com a série de confirmação do fator 14/12. |
| **A3** | Eixo 5 ganhou o fundamento do Banco de Portugal — Kaitz 91 %, P50/P10 1,1, segundo decil sem observações distintas — com as ressalvas de universo. |
| **A5a** | «IDEF» → «IDF» em todo o documento (10 ocorrências). |
| **A5b** | Eixo 3 passa a assinalar a restrição: a componente de **procura** é exequível (Q.2.12.a e Q.2.3.a do IDF), a de **oferta retalhista** não foi obtida. Recomenda-se não anunciar o eixo completo sem essa peça garantida. |

Verificado no fim: 58 `<div>` abertos e 58 fechados, 15 `<li>`, 85 `<td>`, sem `IDEF` remanescente.
Os dois «26 produtos» que subsistem estão dentro de caixas de correção, a citar a redação original —
como deve ser.

### Word «Dados novos» — 28 alterações

| | O que ficou |
|---|---|
| **B1** | §2.4 reescrito: os Censos passam a valor de recuo; explicitados os dois divisores e a diferença de 5,0 % entre universos. |
| **B2** | §3.2, Leite UHT MG: consumo **+61,8 % → +63,6 %**. |
| **B3** | §4.1: denominador 4 149 096 → 4 102 600; 549 → **555 €/mês**; 3 351 → **3 389 €/mês**; rácios 2,29 → **2,32** e 1,68 → **1,70**; coberturas 59,4 → **58,8 %** e 44,4 → **43,9 %**. O parágrafo narrativo foi atualizado a par da tabela. |
| **B4** | §4.1: a frase do intervalo passa a «239 a 555 €/mês», com a ressalva sobre a base temporal do IDF. |
| **B5** | §3.2: cada produto passa a indicar o número de períodos da sua janela; o rodapé ganhou a ressalva de não comparabilidade e a lista dos três produtos excluídos. |
| **B6** | §4.2: rodapé ganhou a declaração da circularidade e o intervalo de sensibilidade. |
| **B7** | §5 passa a «Correções à nota de enquadramento — aplicadas em 08.08.2026». |

Cada substituição validou o conteúdo esperado antes de escrever, e o processo abortaria se algum não
batesse certo. Verificado no fim: zip íntegro, 36 peças, todos os XML válidos.

**Reproduzi os 44,4 % e 59,4 % do Word antes de os corrigir**, para confirmar que a base era COICOP
01 (alimentares e bebidas não alcoólicas) e não 01.1 — o que valida os novos 43,9 % e 58,8 % como
comparáveis com os antigos.

### Uma opção que tomei, e que pode rever

O levantamento propunha **acrescentar duas colunas** ao quadro §3.2. Não o fiz: acrescentar uma
coluna obriga a mexer no `tblGrid` e na largura de todas as células, e um erro aí estraga a
maquetação de um documento que segue para o Gabinete. Pus a informação **no nome de cada produto**
— «Frango inteiro (58 per.)», «Leite UHT MG (45 per., até 07/2025)» — e o detalhe completo no
rodapé. O leitor fica com a mesma informação e o quadro não corre risco. Se preferir as colunas,
digo-lhe e faço.

### Fica pendente

A incorporação dos dados do **SOFI** no Word, de sessão anterior e sem relação com a auditoria. As
instruções em texto foram enviadas na altura.

---

*Documento de trabalho interno — UPE · DSSD · Secretaria-Geral do Governo.
Não constitui posição oficial.*
