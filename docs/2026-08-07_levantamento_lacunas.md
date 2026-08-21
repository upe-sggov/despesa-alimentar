# Cabaz alimentar — levantamento de lacunas, dados verificados e recolha em falta

**Data:** 7 de agosto de 2026 · **Autor:** UPE · DSSD · SGGov
**Estatuto:** documento de trabalho — base para validação. Não constitui posição oficial.

**Objeto.** Confronto entre (a) a nota técnica de enquadramento de 21.07.2026, (b) o documento
`cabaz_06082026.pdf`, (c) a aplicação *despesa-alimentar* e (d) as fontes primárias entretanto
obtidas.

**Nota sobre a verificação.** Os valores da secção 2 foram extraídos por leitura direta das fontes
em 07.08.2026 — chamadas à API do Eurostat e parsing dos ficheiros do INE. Não são citações.

**Decisões do Gabinete registadas (07.08.2026):**
- **Uso final:** (a) armar o Gabinete para o debate público e parlamentar **e** (c) construir um
  instrumento de monitorização permanente. Implica que os produtos tenham de ser simultaneamente
  comunicáveis e reprodutíveis — o que reforça a preferência por fontes automatizáveis.
- **Divergência de valores:** prevalece o PDF de 06.08.2026 (+33,88 % desde jan/2022; +3,91 %
  desde o início de 2026), por ser mais recente e ter fonte.
- **Tensão custo/privação (§2.6):** resolvida em 07.08.2026 — **o indicador entra**, agora com o
  terceiro nível de leitura que o SOFI 2026 fornece (§2.14). Deixa de haver o problema de
  apresentar só o indicador mais benigno.
- **Âncora (§2.10):** adotada a **opção 3** — apresentar o intervalo IDF–Contas Nacionais
  (239–549 €/mês para 2022), com o ponto central assinalado como não determinado.
- **Âmbito das fontes:** o trabalho usa **exclusivamente dados abertos**. Fontes que exijam pedido
  formal, protocolo ou acesso reservado ficam fora de âmbito — o que encerra B1 (Mapa do Comércio).
- **Arquitetura de ponderação (08.08.2026):** aprovadas **duas** bases, com divisão de trabalho
  explícita — **IDF** para estrutura e distribuição, **IHPC** para movimento dos preços. Uma
  terceira base («padrões de consumo», ponderadores do IHPC deflacionados) foi **rejeitada** por
  não ser calculável de forma defensável. Ver §2.16.

---

## 1. Sumário — estado de cada eixo

### Os sete eixos de melhoria (nota §1.5)

| # | Eixo | Estado | Via |
|---|---|---|---|
| 1 | Ponderar pela estrutura real de consumo (IDEF) | 🟢 **Resolvido** | IDF 2022/2023, Q.2.11 — COICOP 4 dígitos em euros |
| 2 | Desagregar por decil de rendimento | 🟢 **Resolvido** | IDF Q.2.11 — quintis ≡ D1–D2 / D9–D10 |
| 3 | Desagregar territorialmente | 🟡 Parcial | NUTS II × quintil e grau de urbanização sim; oferta retalhista não. **É o único eixo que fica em aberto** |
| 4 | Incorporar substituição efetiva (Fisher/Törnqvist) | ✅ **Feito — e o resultado surpreende** | Törnqvist ao nível das classes: o viés é de 0,12 p.p./ano, residual. Ver §2.17 |
| 5 | Indicador de acessibilidade alimentar | 🟢 **Feito, incluindo a variante «dieta saudável»** | Já existe; `ilc_mdes03` e o FAO SOFI 2026 (§2.14) acrescentam os dois limiares em falta |
| 6 | Explorar *scanner data* | 🟢 **Respondido** | O IPC **não** usa; usa *web scraping* — ver §2.7 |
| 7 | Validar contra e-fatura / AT | 🔴 Diligência | Via INE. Nota: a AT já alimenta o IPC, mas só em rendas |

### As quatro linhas de trabalho (nota §1.6)

| # | Produto | Prioridade | Estado |
|---|---|---|---|
| 1 | Nota metodológica «O que é (e o que não é) o cabaz» | Alta | ✅ **Implementada** em 08.08.2026 — quadro dos seis instrumentos na aba «Metodologia e fontes», aberto por defeito |
| 2 | Cabaz ponderado por decil de rendimento | Alta | ✅ **Implementado** em 08.08.2026 (aba 1) — ver §2.1 e §2.16 |
| 3 | Desagregação territorial do preço alimentar | Média | 🟡 Procura sim, oferta não |
| 4 | Benchmarking europeu da inflação alimentar | Média | ✅ Já feito (aba 4) |

---

## 2. Dados verificados e disponíveis

### 2.1 IDF 2022/2023 — despesa alimentar por quintil de rendimento ★ fonte primária

**Fonte:** INE, IDF 2022/2023, quadros **Q.2.11.a** (euros) e **Q.2.11.b** (estrutura %).
Quintis de rendimento **equivalente**. Unidade: € por agregado e por ano.

Supersede o HBS/Eurostat (§2.5): é mais recente, está em euros, e desce ao 4.º dígito da COICOP.

| COICOP 2018 | Rubrica | Total | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|---|---|
| — | **Despesa total do agregado** | **23 900** | 16 294 | 18 269 | 22 188 | 26 188 | 34 994 |
| 01 | Alimentares + bebidas n/alc. | 3 091 | 2 571 | 2 761 | 3 248 | 3 407 | 3 442 |
| **01.1** | **Produtos alimentares** | **2 872** | **2 412** | 2 573 | 3 022 | 3 139 | **3 192** |
| 01.1.1 | Cereais e derivados | 420 | 380 | 404 | 447 | 443 | 426 |
| 01.1.2 | Carne | 670 | 575 | 633 | 767 | 740 | 650 |
| 01.1.3 | Peixe e produtos do mar | 403 | 313 | 342 | 415 | 463 | 476 |
| 01.1.4 | Leite, lácteos e ovos | 369 | 312 | 324 | 376 | 405 | 420 |
| 01.1.5 | Óleos e gorduras | 119 | 102 | 119 | 131 | 138 | 108 |
| 01.1.6 | Fruta e frutos de casca rija | 299 | 231 | 246 | 275 | 320 | 407 |
| 01.1.7 | Hortícolas, tubérculos e leguminosas | 324 | 294 | 290 | 336 | 344 | 354 |
| 01.1.8 | Açúcar, confeitaria e sobremesas | 119 | 75 | 87 | 136 | 121 | 169 |
| 01.1.9 | Pré-preparados e outros | 149 | 130 | 127 | 139 | 165 | 181 |

**Peso da alimentação no orçamento (Q.2.11.b, %):**

| | Total | Q1 | Q2 | Q3 | Q4 | Q5 | Rácio Q1/Q5 |
|---|---|---|---|---|---|---|---|
| 01 (alim. + bebidas) | 12,9 | 15,8 | 15,1 | 14,6 | 13,0 | 9,8 | 1,61 |
| **01.1 (alimentação)** | **12,0** | **14,8** | 14,1 | 13,6 | 12,0 | **9,1** | **1,63** |

**Despesa alimentar mensal por agregado (01.1 ÷ 12):**

| Total | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| **239 €** | 201 € | 214 € | 252 € | 262 € | 266 € |

**Três leituras que a app hoje não consegue produzir:**

1. **O efeito regressivo, quantificado.** O quintil mais pobre afeta 14,8 % do orçamento à
   alimentação; o mais rico, 9,1 %.
2. **A compressão em euros.** Q5 gasta apenas 32 % mais do que Q1 em alimentação (266 € vs 201 €),
   apesar de ter 2,15× a despesa total. É a lei de Engel em estado puro.
3. **A composição muda, não só o nível.** Q1 gasta *mais* em cereais que Q5 em termos relativos
   (2,3 % vs 1,2 %) e *menos de metade* em fruta em euros (231 € vs 407 €). A substituição
   nutricional que a nota descreve está visível nos próprios dados de despesa.

**Correspondência com as classes da app** — um-para-um, sem ambiguidade:

| App (`src/config.py`) | IDF 2022/2023 |
|---|---|
| `CP0111` Pão e cereais | 01.1.1 Cereais e produtos à base de cereais |
| `CP0112` Carne | 01.1.2 Animais vivos, carne e outras partes |
| `CP0113` Peixe e marisco | 01.1.3 Peixe e outros produtos do mar |
| `CP0114` Leite, queijo e ovos | 01.1.4 Leite, outros lácteos e ovos |
| `CP0115` Óleos e gorduras | 01.1.5 Óleos e gorduras |
| `CP0116` Fruta | 01.1.6 Fruta e frutos de casca rija |
| `CP0117` Legumes e hortícolas | 01.1.7 Hortícolas, tubérculos e leguminosas |
| `CP0118` Açúcar e doces | 01.1.8 Açúcar, confeitaria e sobremesas |
| `CP0119` Outros alimentos | 01.1.9 Pré-preparados e outros n.e. |

> **Verificação da âncora da app — ver §2.10. O teste não passa.**

### 2.2 IDF — despesa alimentar por composição do agregado

**Fonte:** Q.2.6.a. Euros por ano. (O cabeçalho ocupa duas linhas; são 9 colunas de composição.)

| Composição | Despesa total | Alimentação (01.1) | Peso |
|---|---|---|---|
| Total | 23 900 | 2 872 | 12,0 % |
| 1 adulto não idoso | 17 105 | 1 594 | 9,3 % |
| 1 adulto idoso | 14 783 | 1 704 | 11,5 % |
| 2+ adultos não idosos | 25 690 | 3 051 | 11,9 % |
| 2+ adultos, ≥1 idoso | 21 858 | 3 081 | 14,1 % |
| 1 adulto c/ dependentes | 24 001 | 2 257 | 9,4 % |
| 2+ adultos c/ 1 dependente | 29 658 | 3 424 | 11,5 % |
| 2+ adultos c/ 2+ dependentes | 32 856 | 3 951 | 12,0 % |

### 2.3 IDF — escalas de equivalência

**Fonte:** Q.2.8. Confirma que o INE usa a **OCDE modificada**: dividindo despesa por agregado
pela despesa por adulto equivalente obtêm-se 1,000 (1 adulto), 1,500 (2 adultos) e 2,144 (3+).

| | Por agregado | Por adulto equivalente | Per capita |
|---|---|---|---|
| Total | 23 900 | 14 574 | 11 078 |
| 1 adulto sem dependentes | 15 832 | 15 832 | 15 832 |
| 2 adultos sem dependentes | 22 342 | 14 895 | 11 171 |
| 3+ adultos sem dependentes | 27 267 | 12 721 | 8 346 |

**Teste da ressalva da app — incompleto.** A app afirma que a OCDE modificada *subestima* o custo
alimentar de agregados maiores. Para o testar é preciso despesa **alimentar** por adulto
equivalente. Consegui-o só para os agregados de 1 adulto (1,0 adultos equivalentes): 1 594 €/ano
para o não idoso, 1 704 € para o idoso, contra 1 751 € na média nacional. Para os agregados de 2+
o Q.2.6.a agrupa «2 ou mais», enquanto o Q.2.8 separa «2» de «3 ou +» — as categorias não cruzam.
→ ver recolha **A6**.

### 2.4 IDF — território

**Grau de urbanização (Q.2.3.a), € por ano:**

| | Portugal | Predom. urbana | Mediamente urbana | Predom. rural |
|---|---|---|---|---|
| Despesa total | 23 900 | 24 960 | 22 713 | 18 690 |
| Alimentação (01.1) | 2 872 | 2 833 | 3 177 | 2 756 |
| **Peso** | **12,0 %** | **11,3 %** | **14,0 %** | **14,7 %** |

Em euros, o rural gasta *menos* em alimentação; em peso orçamental, gasta *mais*. As duas leituras
são verdadeiras e contam histórias opostas — atenção à que se escolhe comunicar.

**NUTS II × quintil (Q.2.12.a/b/c).** Existe, com as sete NUTS II e os cinco quintis cruzados.
Exemplo, despesa total do 1.º quintil: Portugal 16 294 · Norte 16 207 · Centro 14 629 ·
A.M. Lisboa 18 309 · Alentejo 15 558 · Algarve 18 111 · Açores 13 725 · Madeira 15 977.

### 2.5 Eurostat / HBS — fonte secundária

Mantida como corroboração e para comparação europeia. Peso da alimentação (CP01, ‰), PT:

| Vaga | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| 2015 | 183 | 168 | 156 | 144 | 116 |
| «2020» | 171 | 146 | 145 | 131 | 100 |

> ⚠️ **A etiqueta «2020» é enganadora e a série não é uma evolução quinquenal.** Ver §2.12: a
> metainformação do Eurostat lista Portugal como não participante na vaga de 2020, e tudo indica
> que estes valores são o **IDF 2022/2023** disseminado sob aquela etiqueta. Não usar para leituras
> de tendência 2015→2020.

Conjuntos: `hbs_str_t223` (quintil), `hbs_str_t224` (composição), `hbs_str_t226` (urbanização),
`hbs_exp_t133` (nível, em PPS). Detalhe COICOP a 4 dígitos **não publicado para PT** — razão pela
qual o IDF passa a ser a fonte primária. O HBS continua útil para comparar Portugal com a UE.

### 2.6 Privação alimentar — série anual até 2025

**Conjunto:** `ilc_mdes03` · % que não consegue pagar uma refeição com carne, frango ou peixe de
dois em dois dias.

| Grupo | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Total | 2,3 | 2,5 | 2,4 | 3,0 | 2,3 | 2,5 | **1,9** |
| Abaixo do limiar de pobreza | 5,7 | 7,2 | 5,9 | 7,2 | 5,9 | 5,1 | **5,5** |
| Acima do limiar | 1,6 | 1,6 | 1,6 | 2,2 | 1,6 | 2,0 | 1,3 |

> ✅ **Decisão de 07.08.2026: o indicador entra**, mas **nunca sozinho** — sempre acompanhado do
> indicador da FAO (§2.14), que mede um limiar muito mais exigente.
>
> A minha caracterização inicial desta secção — «custo em máximos, privação em mínimos» — estava
> incompleta. Não era falsa, mas ficava-se pelo indicador mais benigno de todos: este mede
> privação **severa**, e 1,9 % é o mínimo da série. O SOFI 2026 fornece o nível intermédio que
> faltava: **14,4 % da população não consegue pagar uma dieta saudável**. Apresentar só o de 1,9 %
> daria uma leitura indevidamente tranquilizadora.
>
> Mantém-se a cautela técnica: é auto-reportado, de inquérito por amostragem, e **sem intervalos de
> confiança verificados**.

### 2.7 Metodologia do IPC — resposta ao eixo 6

**Fonte:** INE, *Documento Metodológico do IPC*, 2023, v2.0 (43 páginas).

| Questão | Resposta |
|---|---|
| O IPC usa *scanner data*? | **Não.** Nenhuma referência em todo o documento. |
| Que recolha automatizada usa? | ***Web scraping***, para «cadeias de lojas com implantação nacional». Permite mais variedades e maior representatividade; metodologia comparável à da recolha física. |
| Base de amostragem | O **IDF**, quinquenal, com representatividade a NUTS II |
| Cobertura territorial | **45 centros de recolha** (concelhos ou agrupamentos), seleção não probabilística |
| Dados administrativos da AT | Já usados — mas só **RER** (rendas) e **IMI**. Nada em alimentação. |
| Tratamento de descontos | Incluídos «desde que de **aplicação generalizada** aos consumidores» |

**Duas consequências diretas:**

1. **O eixo 6 fica respondido**, e negativamente. Se se quiser *scanner data*, é matéria a propor
   ao INE, não a verificar.
2. ~~**A limitação 8 da app pode ser afinada com fonte.**~~ ✅ **Feito em 08.08.2026.** Dizia que o
   IHPC não capta «integralmente» descontos de cartão e talão — formulação que sugere falha de
   recolha. O critério real é uma **regra**: descontos **de aplicação generalizada** entram; os
   condicionais — cartão de fidelização, talão, cupão — são excluídos por definição. A app e o
   README passam a citar o critério, com a consequência que dele decorre e que não estava dita:
   como a difusão dos programas de fidelização aumenta ao longo do tempo, **o índice tende a
   sobrestimar ligeiramente a aceleração do preço efetivamente pago**. O sentido do enviesamento é
   conhecido; a magnitude não é mensurável sem dados de transação.

### 2.8 Número de agregados — confirmação do divisor

**Fonte:** Censos 2021, quadro 4.02 (`Q402.xlsx`, 8 folhas: PT + 7 NUTS II).

**Portugal: 4 149 096 agregados domésticos privados** — confirma exatamente a constante
`AGREGADOS_CENSOS` em [`src/config.py`](../src/config.py). Nada a alterar.

O ficheiro desce a detalhe sub-regional fino (77 581 linhas só no Norte), com tipologia de agregado
e dimensão. **É o denominador territorial** para o eixo 3 — o que falta é o lado da oferta
retalhista.

### 2.9 API do INE — formato confirmado

`indica.json` é uma resposta da API `json_indicador` do INE (indicador **0013519**, «Despesas de
consumo médias anuais dos agregados domésticos privados por local de residência», atualizado
2024-10-17, último período 2022/2023, 462 observações). Confirma que a API devolve dados
estruturados e utilizáveis — o obstáculo é exclusivamente de rede, não de formato.

### 2.10 ★ Aferição da âncora da app — o teste não passa

**O que se testou.** A app deriva a despesa alimentar por agregado das Contas Nacionais
(`nama_10_co3_p3`, CP011, preços correntes) ÷ n.º de agregados ÷ 12. O IDF mede a mesma coisa
diretamente. Nunca tinham sido confrontadas com números — a auditoria de 27.07.2026 dava o teste
como «plausível» sem valor de referência.

**Resultado, ano de 2022 (último das Contas Nacionais):**

| | Alimentação (CP011 / 01.1) | Despesa total do agregado |
|---|---|---|
| Contas Nacionais ÷ 4 149 096 ÷ 12 | **549 €/mês** | 3 351 €/mês |
| IDF 2022/2023, medição direta | **239 €/mês** | 1 992 €/mês |
| **Rácio** | **2,29×** | 1,68× |

**A leitura.** O desvio geral de 1,68× é o gap conhecido entre Contas Nacionais e inquérito, e é
coerente com o ~1,8× que a auditoria já registava. **Mas na alimentação o desvio é de 2,29× — muito
pior do que o desvio geral.** Não é ruído: é sinal de que algo específico da alimentação está a
inflacionar o numerador.

**Decomposição da causa** (verificada em 07.08.2026, não inferida):

**(i) Conceito interno — confirmado, mas menor do que se supôs.** O conjunto `nama_10_co3_p3` é
publicado no **conceito interno**: mede o consumo no território, incluindo o de não residentes.
Confronto com os agregados principais das Contas Nacionais, PT 2022:

| Agregado | M€ |
|---|---|
| `P31_S14` — consumo das famílias, conceito **nacional** (residentes) | 151 318 |
| `nama_10_co3_p3` TOTAL — conceito **interno** | 166 851 |
| Diferença — turismo líquido | +15 533 (**+10,3 %**) |

O efeito existe e vai no sentido esperado, **mas +10 % não explica um desvio de 129 %**. Foi um
erro atribuir-lhe o papel principal.

**(ii) Sub-cobertura do inquérito — este é o fator dominante.** É um fenómeno estrutural e
documentado: os inquéritos às despesas captam sistematicamente menos do que as Contas Nacionais.

| | IDF implícito | Contas Nacionais | Cobertura |
|---|---|---|---|
| Despesa total | 99 163 M€ | 151 318 M€ (nacional) | **65,5 %** |
| Alimentação | 11 916 M€ | 27 318 M€ (interno) | **43,6 %** |

A cobertura global de ~66 % é o valor típico deste tipo de inquérito. **O que é anómalo é a
alimentação estar nos 44 %** — e essa anomalia está agora **quantificada contra uma referência
europeia**: ver §2.12. Três explicações candidatas, que os dados disponíveis não permitem arbitrar:

- o inquérito sub-reporta alimentação pior do que o resto — compras pequenas, frequentes e de baixo
  valor unitário são as que mais escapam ao diário de despesas;
- as Contas Nacionais sobre-atribuem à alimentação, por a estimativa assentar em volume de negócios
  do retalho e em dados do lado da oferta;
- o efeito do turismo é maior na alimentação do que a média de +10,3 % sugere. A média dilui-se por
  todas as rubricas, mas a compra de bens alimentares em retalho por não residentes — alojamento
  local, alojamento com cozinha — cresceu muito em Portugal e recai justamente em CP011. Não é
  quantificável com os dados públicos.

**Corroboração.** Três fontes dão três pesos diferentes para a alimentação no consumo:

| Fonte | Peso de CP011 | Conceito |
|---|---|---|
| Ponderadores IHPC (`prc_hicp_inw`, 2025) | **20,0 %** | Território, e exclui rendas imputadas do denominador |
| Contas Nacionais 2022 | **16,4 %** | Território |
| IDF 2022/2023 | **12,0 %** | Agregados residentes |

A escada é monotónica e explica-se pelo conceito e pelo denominador, não por erro de nenhuma das
fontes.

**Plausibilidade — nenhum dos dois extremos convence.** Para um agregado médio de 2,4 pessoas:

| | Por agregado | Por pessoa | Por pessoa/dia |
|---|---|---|---|
| Contas Nacionais | 549 €/mês | 229 €/mês | ~7,5 € |
| IDF | 239 €/mês | 100 €/mês | ~3,3 € |

Excluindo restauração, 7,5 €/pessoa/dia é alto para Portugal em 2022; 3,3 €/pessoa/dia é
baixo — dificilmente cobre uma alimentação normal. **O valor real estará entre os dois**, e cada
fonte erra num sentido: as Contas Nacionais por excesso (conceito interno e possível
sobre-atribuição), o IDF por defeito (sub-reporte do inquérito).

**Conclusão.** O número principal da app está **muito provavelmente sobrestimado**, mas a
magnitude da sobrestimação não é determinável com estas duas fontes — só se sabe que está entre
0 % e 129 %. Não é um erro de cálculo: o código faz o que o README descreve. É uma questão de
conceito, agravada pelo facto de a pergunta que a app diz responder («quanto uma família gasta em
comida») não ter uma fonte única e não enviesada que lhe responda.

**O que isto afeta e o que não afeta:**

| Afetado | Não afetado |
|---|---|
| O valor em euros da despesa por agregado | A decomposição em % por classe |
| Todos os outputs do simulador de IVA (escalam com a âncora) | As variações homólogas e o histórico |
| A extrapolação «ordens de grandeza a nível agregado» | A comparação UE-27 |
| O indicador de esforço (já declarado como limite superior — a sobrestimação é maior do que se supunha) | O coeficiente de Engel (é um rácio interno às Contas Nacionais) |

**Três opções — decisão a tomar:**

1. **Trocar a âncora para o IDF.** É a medição direta da pergunta que a app faz, e o
   contra-argumento do README — «as Contas Nacionais são mais atuais» — já não se aplica: aquelas
   param em 2022 e o IDF é de 2022/2023. Contra: substitui um enviesamento por excesso por um
   enviesamento por defeito, e o segundo é tão pouco quantificado como o primeiro.
2. **Manter as Contas Nacionais e declarar o desvio**, apresentando o IDF ao lado.
3. **Apresentar o intervalo IDF–Contas Nacionais** (239–549 €/mês para 2022), com o ponto central
   assinalado como não determinado.
4. **Seguir o *benchmark procedure* do EGDNA** (§2.11): usar o IDF para a **forma** da distribuição
   e as Contas Nacionais para o **nível**, depois de lhes ajustar o âmbito — passar do conceito
   interno ao nacional e retirar os agregados não privados.
   **Atenção ao que isto implica:** o EGDNA trata o total macro como autoritativo, pelo que o valor
   médio continuaria próximo dos 549 €, não dos 239 €. O ajustamento de conceito interno→nacional
   corrige apenas ~10 % (549 → ~498 €/mês), deixando por explicar a maior parte do desvio. É a via
   metodologicamente ortodoxa, mas foi desenhada para o rendimento, onde as Contas Nacionais são
   inquestionavelmente a referência — o que é menos evidente na despesa alimentar medida em
   conceito interno num país de forte turismo.

**Recomendação: a 3**, com a **4** como direção de médio prazo. A 3 é o idioma que a app já usa
para as escalas de equivalência — «a direção é robusta, o valor exato é condicional» — e é a única
que não afirma uma precisão que os dados não sustentam. A 1 seria preferível se o IDF fosse não
enviesado; não é. A 4 é a via ortodoxa, mas exige trabalho de ajustamento de âmbito e, ainda assim,
não fecha o desvio.

> **Correção.** Na primeira versão deste documento recomendei a opção 1, com base na atribuição do
> desvio ao conceito interno das Contas Nacionais. A verificação subsequente mostrou que esse
> efeito vale ~10 %, não ~129 %, e que o fator dominante é a sub-cobertura do inquérito — que
> penaliza o IDF, não as Contas Nacionais. A recomendação muda em conformidade.

Não avanço sem decisão sua: muda o número que a ferramenta apresenta em primeiro lugar.

#### Adenda de 20.08.2026: existe exercício de conciliação, e está documentado

Este apuramento assentava na premissa de que «não existe exercício nacional de conciliação que
permita arbitrar». **A premissa está errada**, e a fonte que a desmente é aberta: a metainformação
de referência do conjunto usado pela aplicação, no anexo nacional de Portugal
(`nama_10_cp18_esms_pt`, secção 18.1, «Source data»).

Transcrição literal:

> «The HBS is the starting point for estimating the resident Households' final consumption
> expenditure as an element of information for compiling the Supply Use Tables (SUT). However, the
> comparison between the results obtained by the HBS and other data sources, in particular VAT
> receipts, the turnover in retail trade and the specific information of businesses or of sectors of
> activity, led to the conclusion that to the HBS results were undervalued. Consequently, in
> preparing the SUT, the final value of HFCE was determined when establishing the balance between
> the supply and the various uses of each product.»
>
> «HFCE is compiled using the National Accounts Product Classification and not according to the
> COICOP. The COICOP breakdown of HFCE is obtained from the SUT data once the balancing process is
> completed, applying weights calculated for each COICOP/Product.»

O documento «Como se calcula o PIB» (INE, Departamento de Contas Nacionais, novembro de 2025,
secção 3.A) corrobora em português e dá o vocabulário nacional: o instrumento é o **Quadro de
Equilíbrio de Recursos e Utilizações (QERU)**, com cerca de 430 produtos, e o consumo final das
famílias é uma das colunas do lado das utilizações.

**O que isto altera neste apuramento:**

1. **A conciliação existe e é o QERU.** É o exercício que o §2.11 procurava em documentos
   metodológicos europeus e que já estava descrito na metainformação do próprio conjunto.
2. **As duas bases não são medições independentes.** O IDF é o ponto de partida da estimativa das
   Contas Nacionais. A frase deste documento sobre «duas fontes que não é possível arbitrar»
   descreve mal a relação entre elas.
3. **A sub-cobertura do inquérito deixa de ser inferência nossa.** É conclusão declarada do
   compilador, obtida por confronto com o IVA, com o volume de negócios do retalho e com informação
   setorial.
4. **A opção 4 é a que o INE de facto segue**, e confirma-se o que ali se antecipava: o resultado da
   conciliação não é um ponto intermédio, é o valor das Contas Nacionais. O inquérito é que foi
   revisto em alta até ao valor imposto pelo equilíbrio.

**O que não altera, e é a razão de a recomendação se manter:**

A **magnitude** continua desconhecida ao nível da alimentação. O INE não publica a taxa de cobertura
por rubrica COICOP, e sem ela não é possível dizer quanto do fator de 2,3 é sub-reporte do inquérito
e quanto é âmbito do agregado macroeconómico. A anomalia dos 44% de cobertura na alimentação, contra
66% no conjunto, continua sem número que a explique.

A ela acresce agora uma lista de componentes que estão no valor macroeconómico e **não são despesa
de agregados residentes**, todas a empurrar no mesmo sentido e nenhuma quantificada para a
alimentação:

| Componente | Porque não responde à pergunta da ferramenta |
|---|---|
| Autoconsumo de bens, sobretudo agrícolas | É consumo, não é despesa. Quem come os legumes da própria horta não gasta nesses legumes |
| Compras de não residentes em território português | Não são famílias portuguesas. Nos alimentos o efeito é pequeno, com limite superior de 12,3% |
| Ajustamentos de exaustividade | Captam atividade não declarada, o que é correto para o PIB e alheio à pergunta «quanto gasta este agregado» |
| População institucional | O total do setor das famílias não coincide com o universo dos agregados domésticos privados pelo qual se divide |

**Decisão tomada em 20.08.2026:** manter a opção 3, ou seja, o IDF por defeito e o intervalo entre
as duas bases. A fragilidade conhecida do IDF passa a estar documentada pelo próprio INE, o que é
melhor do que a inferência que aqui se fazia, e as Contas Nacionais respondem a uma pergunta mais
larga do que a da ferramenta.

Alterações aplicadas à aplicação na mesma data: reescrita do separador da metodologia sobre as
Contas Nacionais, que passa a explicar o QERU e o âmbito do valor; nova linha no cartão da âncora a
distinguir as duas perguntas, com o rácio entre bases calculado e não inscrito; atualização de
`BASES_ANCORA` em `src/config.py`, que mostrava na interface a afirmação agora superada.

**Via encerrada.** O caminho para resolver a magnitude seria pedir ao INE a taxa de cobertura por
rubrica COICOP entre o IDF e o QERU. Fica registado como não prosseguível: a ferramenta só usa
fontes abertas, e esse apuramento não está publicado.

### 2.11 Referências metodológicas sobre a conciliação micro-macro

Dois documentos do Eurostat, verificados em 07.08.2026. **Resolvem o método, não o número.**

**KS-RA-13-023-EN — *European household income by groups of households* (2013, 88 pp.)**

Documenta o exercício «a-minima» do **EGDNA** (grupo de peritos conjunto OCDE-Eurostat sobre
disparidades num quadro de Contas Nacionais) — a metodologia oficial europeia para repartir
agregados das Contas Nacionais por grupos de agregados familiares, conciliando-os com dados de
inquérito. Contributos utilizáveis:

- Estabelece que o problema encontrado em §2.10 **é um problema reconhecido, com nome e método**,
  e não uma fragilidade desta app. Isso é defensável perante o Gabinete.
- §3.1 documenta um passo que a minha decomposição omitiu: **ajustamento do âmbito dos totais das
  Contas Nacionais**, designadamente a remoção dos **agregados não privados** (população
  institucional). É uma terceira componente do desvio, a somar ao conceito interno e à
  sub-cobertura.
- §3.4.3 descreve o *benchmark procedure*: usar a distribuição do inquérito e calibrá-la aos totais
  das Contas Nacionais. **É a solução formal para o dilema de §2.10** — em vez de escolher entre as
  duas fontes, usar o inquérito para a *forma* da distribuição e as Contas Nacionais para o *nível*.

**Limite:** o exercício a-minima cobriu **rendimento**, não consumo. Não traz rácios de
conciliação para a despesa alimentar, nem para Portugal. Os valores portugueses que contém
(coberturas e *average gap indicator*) são de componentes de rendimento, em 2008.

**KS-TC-16-026-EN-N — *Statistical matching of EU-SILC and the HBS* (2017, 35 pp.)**

Método para cruzar rendimento (EU-SILC) com despesa (HBS) ao nível do agregado. Relevante para o
ponto 1 da auditoria de 27.07.2026, que assinala a incompatibilidade de bases no indicador de
esforço: este documento descreve a via formal para a resolver.

Traz ainda uma advertência com consequência direta para a leitura de §2.1: a evidência sugere que
**o rendimento é sub-reportado pelos agregados de menores recursos, enquanto a sua despesa é
reportada com relativa exatidão; e que a despesa dos agregados de rendimentos mais altos tende a
ser sub-reportada** (Meyer & Sullivan 2011; Brewer & O'Dea 2012; Sabelhaus et al. 2011).

> **Implicação para o efeito regressivo.** Se a despesa do Q5 é sub-reportada e a sub-declaração se
> concentra em rubricas discricionárias — não alimentares —, então o denominador do Q5 está
> subestimado e o seu peso alimentar aparente (9,1 %) está **sobre**estimado. O rácio real Q1/Q5
> seria então **superior** aos 1,63 medidos. A conclusão de regressividade é, nesse cenário,
> conservadora. Não é demonstração — é uma direção de enviesamento a declarar.

### 2.12 ★ A anomalia da alimentação, aferida contra referência europeia

**Fonte:** Eurostat, *Concepts for household consumption — comparison between micro and macro
approach* (Statistics Explained, dados de março de 2018, vaga HBS de 2010, estatística
experimental) e *Consumption expenditure of private households (hbs)* — metainformação de
referência ESMS, atualizada em 19.04.2024.

Este é o exercício de conciliação que faltava: **compara HBS com Contas Nacionais por categoria
COICOP** e usa exatamente a métrica que calculei — «*coverage rate*: dados agregados do HBS a
dividir pelos agregados correspondentes das Contas Nacionais, em percentagem», sobre o mesmo
conjunto `nama_10_co3_p3`.

**Valores de referência para a UE (vaga de 2010):**

| Indicador | Valor |
|---|---|
| Cobertura média, consumo total | **~73 %** (intervalo 50 %–97 %) |
| *Data gap* médio, consumo total | 27 % |
| Cobertura da **alimentação (01)** | **58 %–108 %** |
| Cobertura de bebidas alcoólicas e tabaco (02) | 13 %–69 % (a pior) |
| Cobertura de educação (10) | 6 %–119 % (a mais dispersa) |

E a conclusão do artigo, textualmente: *«the smallest differences and disparities among the
countries are for food and non-alcoholic beverages (01)»* — **a alimentação é normalmente a
categoria mais bem comportada.**

**Confronto com Portugal, 2022** (ambos os lados em conceito interno, para comparabilidade):

| | IDF implícito | Contas Nacionais | Cobertura PT | Referência UE |
|---|---|---|---|---|
| Consumo total | 99 163 M€ | 166 851 M€ | **59,4 %** | 50–97 % ✅ dentro |
| Alimentação (CP01) | 12 825 M€ | 28 916 M€ | **44,4 %** | 58–108 % ❌ **abaixo do mínimo** |

**Duas conclusões.**

1. **O consumo total português está normal.** O *data gap* de ~35 % que calculei para 2022 coincide
   com o que a Figura 4 do artigo atribui a Portugal em 2010 (~34–35 %). Não houve degradação: é o
   nível estrutural português, estável há mais de uma década.
2. **A alimentação é que está fora do padrão.** 44,4 % fica abaixo do mínimo europeu de 58 %, e
   fica-o precisamente na categoria que o Eurostat identifica como a de menores disparidades entre
   países. **A anomalia é específica da alimentação e é real** — não é artefacto do meu método, que
   é o mesmo do Eurostat.

O artigo nomeia expressamente Portugal entre os países onde *«the differences between the data
sources are considerable»* (com BG, HU, LT, RO e UK). Não é novidade para o Eurostat.

**Razões documentadas para o desvio**, todas aplicáveis:

| Razão | Sentido |
|---|---|
| População de referência: o HBS exclui agregados institucionais | HBS < CN |
| Conceito interno vs nacional | HBS < CN |
| Sub-cobertura dos agregados mais ricos | HBS < CN, mas o artigo nota que «é menos pronunciado no consumo do que no rendimento» |
| FISIM, seguros e salários em espécie: nas CN, não no HBS | HBS < CN (afeta CP12, não alimentação) |
| Bens em segunda mão e reparações: no HBS, não nas CN | HBS > CN |

Nota do artigo com relevância direta: o ajustamento interno↔nacional *«é complexo e não foi
efetuado, por o Eurostat não dispor do nível de detalhe necessário»*. E os Estados-Membros são
**expressamente encorajados a repetir o exercício a nível nacional** — o que é precisamente o
pedido a dirigir ao INE.

**Caveat sobre a vaga do HBS.** A metainformação ESMS lista Portugal **sem participação na vaga de
2020** (X em 1988–2015, em branco em 2020). Contudo o Eurostat dissemina dados PT para 2020, que
verifiquei existirem. A explicação mais provável é que o **IDF 2022/2023 esteja disseminado sob a
etiqueta «2020»** — a metainformação data de abril de 2024 e a publicação do IDF é de outubro de
2024. Sustenta-o a proximidade dos valores: Q3, Q4 e Q5 do HBS «2020» (145, 131, 100 ‰) contra os
do IDF (146, 130, 98 ‰). Q1 e Q2 divergem (171/146 contra 158/151), provavelmente por o IDF usar
quintis de rendimento **equivalente** e o HBS outra definição.

> **Consequência:** a série do §2.5 **não deve ser lida como evolução 2015→2020**. É 2015→2022/2023,
> com sete a oito anos de intervalo e uma possível mudança de definição de quintil pelo meio.

### 2.13 ★ A ressalva das escalas de equivalência — testada e confirmada

**A6 está substancialmente resolvido.** O ficheiro `IDF20222023_a.xlsx` não são microdados — são os
mesmos quadros publicados —, mas traz o **Q.1.3**, com o *número de agregados* por composição. Isso
permite desagregar por resíduo o grupo «2 ou mais adultos» e completar o teste.

**Método.** Combinando Q.1.3 (contagens), Q.2.6.a (alimentação 01.1) e Q.2.8 (despesa total e por
adulto equivalente), restringido a **agregados sem crianças dependentes** — onde a escala é mais
limpa, sem os pesos das crianças.

Primeiro, a validação de que o Q.2.8 usa mesmo a OCDE modificada — dividindo despesa por agregado
pela despesa por adulto equivalente: 1 adulto → **1,000**; 2 adultos → **1,500**; 3 ou + → **2,144**.
Bate certo com a escala.

Depois, o grupo «2 ou +» reparte-se por resíduo em **72 % com 2 adultos** e **28 % com 3 ou mais**,
o que dá **1,68 adultos equivalentes**.

**Resultado:**

| Agregados sem crianças | Alimentação €/ano | Adultos equiv. | €/adulto equiv. |
|---|---|---|---|
| 1 adulto | 1 654 | 1,000 | **1 654** |
| 2 ou + adultos | 3 066 | 1,679 | **1 827** |

| | Rácio 2+/1 |
|---|---|
| Observado na alimentação | **1,854** |
| Previsto pela escala OCDE modificada | 1,679 |
| **A escala subestima em** | **≈ +10 %** |

**O controlo é o que torna isto convincente.** Repetindo a mesma conta para a despesa **total** —
para a qual a escala foi desenhada — o desvio inverte-se: rácio observado 1,498 contra 1,679 da
escala, ou seja a escala **sobre**estima em −11 %.

> **Conclusão.** A ressalva que a app declara está **confirmada e quantificada**: a escala OCDE
> modificada, que funciona (ou até sobre-ajusta) para o consumo total, **subestima o custo
> alimentar de agregados maiores em cerca de 10 %**. A alimentação tem de facto economias de escala
> mais fracas do que o consumo total. A app pode passar de «é uma ressalva metodológica» para «está
> medido, e é desta ordem».

**Implementado em 08.08.2026**, com um resultado adicional que o apuramento inicial não tinha
extraído: comparando as **três** escalas contra o mesmo rácio observado, é possível eleger a que
melhor reproduz a despesa alimentar.

| Escala | Rácio previsto (2+/1) | Desvio na alimentação | Desvio na despesa total |
|---|---|---|---|
| Per capita | 2,361 | −21,5 % | −36,5 % |
| **OCDE original** | **1,952** | **−5,0 %** | −23,3 % |
| OCDE modificada (norma UE) | 1,680 | **+10,3 %** | −10,9 % |

Rácio observado: **1,854** na alimentação, **1,498** na despesa total.

Duas leituras:

1. **O sinal inverte-se entre as duas colunas**, e com magnitude semelhante (+10,3 % contra
   −10,9 % na modificada). É o que fecha o argumento: o problema não é da escala em abstrato, é da
   aplicação de uma escala de consumo total à alimentação.
2. **A OCDE original é a mais próxima** — erro de 5,0 % contra 10,3 % da norma da UE. A escolha
   por defeito da aplicação deixa de assentar num argumento teórico e passa a assentar num teste.
   Na app, o valor por defeito é agora **calculado** por `escala_mais_proxima()`, não fixado à mão:
   se uma vaga futura do IDF mudar o rácio observado, o valor por defeito acompanha.

**Precisão.** As duas restrições disponíveis — contagens do Q.1.3 e sub-linhas do Q.2.8 — são
ligeiramente inconsistentes entre si (adultos equivalentes médios reconstruídos: 1,435 contra 1,407
publicados). Consoante a que se privilegie, a subestimação fica entre **+10 % e +13 %**. Robusta na
direção e na ordem de grandeza; não no segundo decimal. Declarar como «cerca de 10 %».

### 2.14 ★ Custo e acessibilidade de uma dieta saudável — FAO SOFI 2026

**Fonte:** FAO/FIDA/UNICEF/PAM/OMS, *The State of Food Security and Nutrition in the World 2026*,
anexos A1.5 e A1.6. A edição de 2026 é integralmente dedicada ao tema — subtítulo *«Understanding
and addressing the high cost of a healthy diet»*.

**Resolve o E3**, que eu tinha dado como inacessível: a API do FAOSTAT devolve 401, mas a série
publicada existe, é oficial e cobre 2017–2025. **O eixo 5 na variante «custo de uma dieta saudável»
deixa de ter de ser construído de raiz.**

#### Custo de uma dieta saudável (PPP$ por pessoa e por dia)

| | 2017 | 2019 | 2021 | 2022 | 2023 | 2024 | 2025 | Var. 17–25 |
|---|---|---|---|---|---|---|---|---|
| **Portugal** | 2,64 | 2,85 | 2,99 | 3,57 | 4,10 | 4,17 | **4,30** | **+62,9 %** |
| Europa | 2,51 | 2,72 | 2,91 | 3,33 | 3,76 | 3,84 | 3,97 | +58,2 % |
| Europa do Sul | 2,79 | 3,01 | 3,20 | 3,73 | 4,36 | 4,47 | 4,62 | +65,6 % |
| Espanha | 2,53 | 2,70 | 2,94 | 3,45 | 4,13 | 4,22 | 4,33 | +71,1 % |
| Eslovénia | 2,60 | 2,85 | 3,01 | 3,49 | 3,97 | 4,02 | 4,26 | +63,8 % |

#### Incapacidade de pagar uma dieta saudável

| Portugal | 2017 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| % da população | 22,1 | 15,1 | 16,1 | 15,7 | **16,9** | 15,0 | 14,8 | **14,4** |
| Milhões de pessoas | 2,3 | 1,6 | 1,7 | 1,6 | **1,8** | 1,6 | 1,5 | **1,5** |
| *Espanha, %* | *12,6* | *11,3* | *11,7* | *10,2* | *9,5* | *9,9* | *9,6* | *9,3* |

**Quatro leituras.**

1. **O choque de 2022 está visível e é datável.** A proporção sobe de 15,7 % para 16,9 % — mais
   200 mil pessoas — e recupera depois. É a única série que capta o efeito do pico inflacionário
   sobre a *acessibilidade*, não sobre o preço.
2. **Portugal está acima da média europeia no custo** (4,30 contra 3,97 PPP$) e a subir mais
   depressa (+62,9 % contra +58,2 %), mas **abaixo da Europa do Sul** e de Espanha na velocidade.
3. **O ponto mais afiado: Portugal e Espanha têm custo praticamente igual** (4,30 contra 4,33) **mas
   Portugal tem 14,4 % de população incapaz de o pagar contra 9,3 % em Espanha.** A diferença não
   está nos preços — está nos rendimentos e na sua distribuição. É exatamente o argumento que a nota
   de enquadramento faz sobre o cabaz não ser indicador de acessibilidade, aqui com prova
   internacional.
4. **Dá o nível intermédio que faltava** entre o custo e a privação severa — ver §2.6.

> ⚠️ **Não é uma âncora de despesa e não deve ser usado como tal.** O custo de uma dieta saudável é
> um **mínimo normativo** — o preço da dieta mais barata que cumpre os requisitos nutricionais —,
> não a despesa observada. Comparar com os 239–549 €/mês de §2.10 seria comparar objetos
> diferentes. Acresce que vem em **PPP$**, não em euros: qualquer conversão exigiria a paridade de
> poder de compra do consumo privado, e continuaria a não o tornar comparável com despesa efetiva.

**Os três limiares, para uso conjunto:**

| Indicador | Limiar | Portugal 2025 | Fonte |
|---|---|---|---|
| Privação alimentar severa | Refeição com carne ou peixe de 2 em 2 dias | **1,9 %** | Eurostat `ilc_mdes03` |
| Incapacidade de dieta saudável | Cabaz nutricionalmente adequado ao menor custo | **14,4 %** (1,5 M) | FAO SOFI 2026 |
| Peso da alimentação no orçamento | 1.º quintil de rendimento | **14,8 %** | INE, IDF 2022/2023 |

**Implementado em 08.08.2026**, na aba 1. Notas da implementação:

- O `ilc_mdes03` é obtido **em direto**, e os valores devolvidos reproduzem exatamente os desta
  secção (2025: total 1,9 %, em risco de pobreza 5,5 %, acima do limiar 1,3 %). O SOFI é
  publicado apenas em PDF e ficou **inscrito em `src/config.py`** — é o único conjunto da
  aplicação que não vem de API e que exige atualização manual a cada edição.
- A regra de «nunca sozinho» ficou **garantida por construção**, não por disciplina de quem
  escreve: os três indicadores partilham o mesmo bloco, a mesma nota de leitura e as mesmas
  ressalvas. Não há caminho na interface que mostre o de 1,9 % isolado.
- Foi preciso alterar `src/eurostat.py`. O descodificador normalizava tudo para
  `unit/coicop/geo/time/valor` e **descartava dimensões próprias do conjunto** — as três séries do
  `ilc_mdes03` vinham empilhadas e indistinguíveis, sem erro nem aviso. `obter()` passa a aceitar
  `extra`, e recusa-se a prosseguir se a dimensão pedida não existir na resposta. É um defeito
  latente que só apareceu por este conjunto ter dimensão própria; qualquer conjunto futuro nas
  mesmas condições estaria sujeito ao mesmo problema silencioso.

### 2.15 Observatório de Preços Agroalimentar — onde na cadeia está o aumento

**Fonte:** GPP, `observatorioagroalimentar.gov.pt`, extraído em 07.08.2026 via o *endpoint*
`get_produto_graph` (`wp-admin/admin-ajax.php`), com parâmetros `fase` (1 produção, 2 consumo),
`product`, `start_year`/`start_period`, `end_year`/`end_period`. **39 produtos × 58 períodos de
quatro semanas desde 03.01.2022.** Automatizável — não exige *scraping* de PDF.

Responde à pergunta que a nota §1.1 diz que nenhum outro instrumento toca. **Três padrões distintos,
que a leitura agregada do cabaz esconde:**

| Padrão | Produto | Produção | Consumo | Var. da diferença |
|---|---|---|---|---|
| Choque na origem, transmitido | Ovo M | +98,2 % | +101,3 % | +109,5 % |
| Absorvido pela cadeia | Cenoura | +110,7 % | +66,2 % | +35,0 % |
| **Divergência** | **Pescada** | **−22,8 %** | **+23,4 %** | **+106,5 %** |

A pescada é o caso mais nítido: preço na produção **cai** 22,8 % enquanto o preço ao consumidor
**sobe** 23,4 %, com a diferença a passar de 2,61 € para 5,39 €/kg.

Maiores subidas ao consumidor desde P1 2022: ovo M +101,3 %, ovo L +98,8 %, batata +77,1 %,
cenoura +66,2 %, leite UHT +61,8 %, brócolo +60,5 %, dourada +59,3 %, cebola +57,8 %, azeite virgem
extra +55,7 %. Descidas: curgete −36,5 %, alface 4.ª gama −28,9 %, esparguete −6,5 %.

> ⚠️ **A diferença consumo–produção não é margem de nenhum operador.** Inclui transporte,
> transformação, embalagem, distribuição e IVA; e as duas fases podem referir-se a formas
> diferentes do produto (peixe inteiro contra posta, animal vivo contra peça desmanchada). Não é
> comparável entre produtos. Algumas séries de produção terminam antes de 2026 — cebola e brócolo
> em 2023, leite e arroz em 2025.

**Implementado em 08.08.2026**, em separador próprio («Da produção ao consumo»). Notas:

- **A recolha é um script, não uma chamada da aplicação.** O Observatório não tem API: a série
  exige uma chamada por produto ao *endpoint* AJAX do WordPress. Fazer 39 pedidos POST a um sítio
  institucional sempre que a cache expira seria desproporcionado, e desnecessário — os dados saem
  em períodos de quatro semanas. `scripts/recolher_observatorio.py` escreve
  `dados/observatorio.csv` e `dados/observatorio_meta.json`, ambos versionados. Ganha-se
  reprodutibilidade: qualquer número apresentado é reconstituível a partir do ficheiro e da data
  de extração.
- **Uma chamada devolve as duas fases.** Pedindo a fase de consumo, a resposta traz também a série
  de produção, pelo mecanismo de comparação do próprio sítio. Reduz a recolha a metade.
- **Só 17 dos 39 produtos têm série de produção.** Para os outros 22 o Observatório publica apenas
  preço ao consumidor, e a comparação entre pontas da cadeia não é possível. A aplicação
  distingue-os explicitamente em vez de os omitir.
- **As variações são calculadas no período comum às duas fases.** Não é detalhe: várias séries de
  produção terminam antes das de consumo, e medir cada fase no seu próprio intervalo produziria
  variações de períodos diferentes, cuja comparação não significa nada. Tem teste.

**Recolha de 08.08.2026:** 3 074 observações, 39 produtos, 20 setores, 58 períodos de
03.01.2022 a 18.05.2026. Os três valores registados acima reproduzem-se exatamente.

**Distribuição dos padrões** (17 produtos com as duas fases):

| Padrão | N.º | Exemplos |
|---|---|---|
| Choque na origem, transmitido | 13 | Ovo M, Ovo L, Batata, Leite UHT |
| Absorvido pela cadeia | 2 | Cenoura, Brócolo |
| **Divergência** | **1** | **Pescada** |
| Descida em ambas as fases | 1 | Curgete |

O **frango inteiro** merece nota: produção +39,2 %, consumo +51,6 %, mas a diferença entre as duas
pontas alarga **+178,9 %** — o maior de toda a série. Vale a mesma ressalva: pode refletir mudança
de forma do produto entre fases, e não é margem de ninguém.

### 2.16 Arquitetura de ponderação — IDF e IHPC ★ decisão de 08.08.2026

**A pergunta.** A aplicação usava um único ponderador — o do IHPC (`prc_hicp_inw`) — tanto para
repartir a despesa pelas classes como para calcular a inflação alimentar. Com o IDF disponível,
punha-se a questão de qual usar para quê.

**O facto decisivo, em fonte primária.** O Documento Metodológico do IPC (INE, 2023, `DMet_IPC_2023_v2-0.pdf`):

> «O IHPC inclui a despesa realizada pelos não residentes ("turistas") no território económico e
> exclui a despesa dos residentes no exterior, originando uma **estrutura de ponderação diferente
> da utilizada no IPC**.»

Os ponderadores que a aplicação usava incluem, por construção, despesa de turistas. É a mesma
contaminação de conceito que levou a abandonar as Contas Nacionais como âncora única (§2.10) — e
não tinha sido detetada. O INE publica ponderadores do IPC em conceito nacional, mas apenas em
`ine.pt`; o Eurostat só difunde os do IHPC. **O IDF é a única via aberta para uma estrutura de
agregados residentes.**

**Decisão.** Duas bases, com divisão de trabalho explícita:

| | Ponderador | Responde a | Onde |
|---|---|---|---|
| Estrutura e distribuição | IDF 2022/2023, por quintil | Quem gasta o quê, e que parte do orçamento leva | Aba 1, secção «Quem está mais exposto» |
| Movimento dos preços | IHPC, revisto anualmente | Quanto subiu cada grupo, e quanto contribuiu | Cartões de classe, aba 2, simulador de IVA |

**Quanto vale a escolha, medido** (dezembro de 2025, ponderadores de 2025):

| | Ponderação IHPC | Ponderação IDF | Diferença |
|---|---|---|---|
| Inflação alimentar nacional | 3,56 % | 3,87 % | **+0,32 p.p.** |

Desvio médio absoluto entre as duas estruturas: **1,89 p.p.**; máximo **4,93 p.p.**

| Classe | Quota IHPC | Quota IDF | Desvio |
|---|---|---|---|
| Pão e cereais | 19,6 % | 14,6 % | **+4,93** |
| Carne | 19,4 % | 23,3 % | **−3,89** |
| Legumes e hortícolas | 9,0 % | 11,3 % | −2,25 |
| Peixe e marisco | 15,5 % | 14,0 % | +1,51 |
| Óleos e gorduras | 5,4 % | 4,1 % | +1,28 |
| Fruta | 9,4 % | 10,4 % | −1,04 |
| Leite, queijo e ovos | 12,1 % | 12,9 % | −0,80 |
| Açúcar e doces | 4,9 % | 4,1 % | +0,80 |
| Outros alimentos | 4,7 % | 5,2 % | −0,53 |

O sinal do maior desvio é o esperado se for efeito de turismo — pão, pastelaria e produtos de
padaria pesam mais no consumo de quem está de passagem. **Não é demonstração:** parte do desvio é
a diferença de anos de referência (IHPC 2025, IDF 2022/2023), e os dados abertos não permitem
separar as duas causas, precisamente porque não existe exercício nacional de conciliação (A8).

**Terceira base, rejeitada.** Estudou-se um instrumento que lesse os ponderadores do IHPC
deflacionados pelo índice de preços de cada classe, para isolar mudanças de *quantidade*
consumida. Foi rejeitado. O mesmo Documento Metodológico estabelece que «a amostra e estrutura de
ponderação referem-se sempre a **dezembro do ano n−1**» e que os ponderadores resultam das Contas
Nacionais, Censos e IDF, **já atualizados pela variação de preços** até esse momento. Deflacionar
um ponderador do ano *n* pela média anual do índice de *n* desconta duas vezes parte do
efeito-preço e nenhuma vez outra parte.

> **Correção a registar.** Numa versão anterior desta análise foram apresentados resultados dessa
> deflação — designadamente que a quota real da carne teria caído 1,4 p.p. entre 2020 e 2025,
> «o dobro» da queda nominal. **Esses valores não são defensáveis** e não devem ser usados. A
> direção pode manter-se; a magnitude não. Medir alteração de quantidade exigiria dados de volume
> que nenhuma destas fontes publica.

**Regra de apresentação, deliberada.** As três grandezas do cabaz por quintil nunca são
apresentadas isoladamente, porque qualquer uma engana sozinha:

| Leitura isolada | O que sugere | Porque é falso |
|---|---|---|
| Taxa de inflação por quintil | Neutralidade distributiva — amplitude de **0,18 p.p.**, com o valor mais alto no 5.º quintil (3,97 %) | A taxa mede movimento de preços sobre cabazes diferentes, não impacto |
| Agravamento em euros | Que o 5.º quintil é o mais afetado (**9,67 €** contra **6,91 €**) | Gasta mais em comida em absoluto; nada diz sobre esforço |
| Agravamento sobre o orçamento total | — | É esta que mede esforço: **0,51 %** no 1.º quintil contra **0,33 %** no 5.º |

**Consequência para a nota de enquadramento de 21.07.2026.** A nota descreve o impacto da inflação
alimentar como regressivo por via de uma inflação diferenciada entre escalões. Os dados não o
sustentam: a amplitude entre quintis é de 0,18 p.p. e o valor mais alto está no quintil mais rico.
**O efeito regressivo é real, mas é de exposição** — a alimentação absorve 14,8 % do orçamento do
1.º quintil e 9,1 % do 5.º, um rácio de 1,63, sobre um orçamento total que é menos de metade. A
formulação deve ser corrigida em conformidade; o argumento sai reforçado, não enfraquecido, porque
a exposição é uma medida mais robusta e menos dependente do mês de referência.

**Contrapartida a declarar.** O IDF é quinquenal. A sua estrutura envelhece entre vagas e
reintroduz, ao nível da classe, o viés de substituição que a nota critica nos cabazes de composição
fixa. O contrapeso é o IHPC, revisto anualmente. A próxima vaga é o IDF 2026 e a atualização de
`src/config.py` terá de ser manual.

### 2.17 Viés de substituição — medido, e menor do que se supunha ★ apuramento de 08.08.2026

**Fontes:** Eurostat, `prc_hicp_midx` (índice mensal por classe) e `prc_hicp_inw` (ponderadores
anuais). Base: dezembro de 2020 = 100. Só ponderação IHPC — o IDF tem uma vaga, não dá série.

Três índices sobre as mesmas nove classes, para isolar o efeito da regra de ponderação:

| Dezembro | Cabaz fixo (Laspeyres) | Törnqvist | IHPC oficial | Viés (fixo − Törnqvist) |
|---|---|---|---|---|
| 2020 | 100,00 | 100,00 | 100,00 | — |
| 2021 | 103,17 | 103,00 | 103,05 | +0,16 |
| 2022 | 124,33 | 124,06 | 124,10 | +0,27 |
| 2023 | 126,01 | 125,89 | 125,89 | +0,12 |
| 2024 | 130,67 | 130,29 | 130,24 | +0,38 |
| **2025** | **135,35** | **134,76** | **134,88** | **+0,59** |

**O viés existe, tem o sinal esperado — e é residual.** Congelar os ponderadores sobrestima a
subida em **0,59 pontos de índice em cinco anos**, cerca de **0,12 p.p. por ano**, sobre uma
subida acumulada de 34,8 %. Em proporção, **1,7 % do aumento medido**.

**Validação da construção.** O Törnqvist aqui calculado fica a 0,12 pontos do IHPC oficial, que é
construído por outra via e por outra entidade. Duas cadeias de cálculo independentes que convergem
é o melhor indício disponível de que a aproximação de ponderadores (§ abaixo) se comporta.

**Porque é tão pequeno — e porque isso não absolve o cabaz fixo.** A substituição relevante ocorre
**dentro** das classes, não entre elas: trocar novilho por frango não altera o peso da carne;
trocar marca de fabricante por marca própria não altera peso nenhum. Nove classes COICOP são uma
grelha demasiado grossa para ver o que as famílias fazem.

Daqui saem duas conclusões de sentido oposto, e ambas devem ser ditas:

1. **Contra quem ataque o índice oficial** invocando viés de substituição entre grupos de
   alimentos: o efeito está medido e é de 0,12 p.p./ano. Não sustenta a acusação.
2. **Contra quem defenda o cabaz de composição fixa** com base neste resultado: não serve. O
   problema de um cabaz de 63 produtos com quantidades fixas é de outra ordem — marca, calibre,
   embalagem, insígnia — e **nenhuma dessas dimensões é observável nestes dados**. O efeito medido
   aqui é o menor dos dois; o maior fica por medir, e mediria-se com dados de transação.

**Aproximação a declarar.** O Törnqvist exige as quotas de despesa observadas nos dois extremos de
cada elo. Em fonte aberta existem os ponderadores do IHPC, que o DMet_IPC define como referidos a
**dezembro do ano n−1** e já atualizados a preços desse momento. A correspondência adotada decorre
dessa definição: o elo de dezembro de y−1 a dezembro de y usa a média dos ponderadores de y e de
y+1. No último elo, o ponderador de y+1 ainda não está publicado e repete-se o de y — assume
estrutura constante no último ano e afeta apenas esse elo.

> É a mesma armadilha que fez cair a terceira base de ponderação (§2.16): os ponderadores do IHPC
> não são quotas de despesa de um ano civil. Aqui a aproximação é aceitável porque o índice
> resultante é validável contra o IHPC oficial; lá não era, porque não havia contra o que validar.

---

## 3. Acessibilidade das fontes a partir de ambiente automatizado

Testado em 07.08.2026.

| Fonte | Estado |
|---|---|
| Eurostat | ✅ responde |
| `www.gpp.pt` · `observatorioagroalimentar.gov.pt` · `www.asae.gov.pt` | ✅ respondem |
| `www.ine.pt` | ❌ *timeout* |
| `dados.gov.pt` | ❌ *timeout* |
| `www.dgeconomia.gov.pt` | ❌ erro de ligação |

**Ação para a DSTD:** pedir desbloqueio de saída para `www.ine.pt`, `dados.gov.pt` e
`www.dgeconomia.gov.pt`. Dado que o uso pretendido inclui **monitorização permanente** (decisão
D1), isto deixa de ser conveniência e passa a ser requisito: sem acesso programático ao INE, a
atualização do IDF terá de ser manual a cada vaga.

---

## 4. Métodos de cálculo

### 4.1 Cabaz por quintil (eixos 1 e 2 / linha #2)

Com o IDF já não é preciso estimar — os valores são diretos:

```
despesa_alimentar_mensal[q]      = Q.2.11.a[01.1, q] / 12
despesa_por_classe_mensal[c, q]  = Q.2.11.a[c, q] / 12
peso_da_classe[c, q]             = Q.2.11.a[c, q] / Q.2.11.a[01.1, q]
```

Aplica-se depois a cada classe a variação homóloga que a app já obtém do Eurostat:

```
contributo[c, q] = despesa_por_classe_mensal[c, q] × g[c] / (1 + g[c])
```

**A declarar:** a *composição* é de 2022/2023; só os *preços* são correntes. Mesma lógica —
e mesma redação — que a app já usa para a âncora das Contas Nacionais.

### 4.2 Índice de Törnqvist ao nível das classes (eixo 4)

A app não pode construir um Fisher — não tem quantidades. Mas o Törnqvist precisa de participações
de despesa, não de quantidades:

```
ln(T) = Σᵢ [(wᵢ,₀ + wᵢ,ₜ) / 2] × ln(Pᵢ,ₜ / Pᵢ,₀)
```

com `wᵢ` de `prc_hicp_inw` e `Pᵢ` de `prc_hicp_midx`. Corrige a substituição **entre** classes, não
dentro delas. Posto ao lado de um Laspeyres de ponderadores congelados, torna o viés de
substituição visível e quantificado em vez de apenas explicado em prosa.

### 4.3 Receita cessante e repercussão — verificado

Exemplo de 106 €, descida de 23 % para 6 %:

| Repercussão | Preço final | Base tributável | Receita nova | Δ Receita |
|---|---|---|---|---|
| 0 % | 106,00 € | 100,00 € | 6,00 € | **−13,82 €** |
| 100 % | 91,35 € | 86,18 € | 5,17 € | **−14,65 €** |

Amplitude ≈ 6 %. Confirma o ponto 2 da auditoria: a receita cessante só é independente da
repercussão numa isenção total. Corrigido na app e no README em 07.08.2026.

---

## 5. Recolha ainda em falta

### 5.A Do INE

| # | O que | Porquê | Estado |
|---|---|---|---|
| ~~A1~~ | IDEF por decil, COICOP 4 dígitos | Eixos 1 e 2 | ✅ **Entregue** (Q.2.11) |
| ~~A2~~ | O mesmo por NUTS II | Eixo 3 | ✅ **Entregue** (Q.2.12) |
| ~~A3~~ | Despesa alimentar em euros por tipo de agregado | Escalas de equivalência | 🟡 Parcial (Q.2.6.a) — ver A6 |
| ~~A4~~ | Metodologia do IPC / *scanner data* | Eixo 6 | ✅ **Entregue** — resposta é «não usa» |
| ~~A5~~ | N.º de agregados | Divisor da app | ✅ **Entregue** — confirma 4 149 096 |
| ~~A6~~ | Despesa alimentar por composição fina | Escalas de equivalência | ✅ **Resolvido por via aritmética** — ver §2.13. O Q.1.3 do `IDF20222023_a.xlsx` deu as contagens que faltavam. |
| A7 | Existe versão por **decil** (não quintil) do Q.2.11? | Os quintis já respondem a D1–D2 / D9–D10 | ⚪ Dispensado |
| ~~A8~~ | Exercício nacional de conciliação IDF ↔ Contas Nacionais | Fecharia §2.10 | 🔴 **Não existe** (confirmado 07.08.2026). O desvio da alimentação fica **por explicar em fonte oficial** — o que reforça a opção 3 para a âncora: não há como estreitar o intervalo. |
| ~~A9~~ | Etiqueta da vaga HBS «2020» | Evitar leitura de tendência errada | ✅ **Resolvido** — ver nota abaixo |

> **Sobre A9.** A «vaga 2020» é uma designação **harmonizada do Eurostat**, não um ano de referência
> fixo: agrupa a ronda de recolha seguinte a 2015, com trabalho de campo entre 2018 e 2022 consoante
> o país, ajustado a preços de 2020. Para Portugal corresponde ao **IDF 2022/2023** — o INE afirma
> que o IDF se enquadra no projeto HBS, a vaga anterior foi alimentada pelo IDF 2015/2016 e não há
> vaga intermédia.
>
> **O que fica por confirmar é a definição de quintil.** A convenção do Eurostat é rendimento
> disponível **equivalizado** (OCDE modificada); o IDF nacional pode usar outra base. Não há
> confirmação documental de qual o INE aplica na transmissão. **Há porém evidência empírica de que
> diferem:** Q3, Q4 e Q5 batem quase certo entre as duas fontes (145/146, 131/130, 100/98) e Q1 e Q2
> divergem claramente (171/158, 146/151) — que é exatamente o padrão esperado se a base de
> equivalização mudar, porque é nos escalões baixos que os agregados grandes se deslocam.
> Consequência prática: **usar o IDF para qualquer leitura por quintil**, e não o HBS.

### 5.B Da DGE — encerrado

| # | O que | Estado |
|---|---|---|
| B1 | Mapa do Comércio — estabelecimentos georreferenciados | 🔴 **Encerrado.** O mapa é só de visualização e não exporta dados; a única via seria pedido formal à DGE/DCSR, **fora do âmbito de trabalho, que é exclusivamente de dados abertos**. Alternativa se o eixo 3 avançar: OpenStreetMap (`shop=supermarket`), aberto mas proxy imperfeito. O lado da procura fica servido pelo Q402. |
| B2 | Histórico oficial de monitorização do cabaz IVA Zero | ⚪ **Dispensado.** O PDF de 06.08.2026 já dá os valores essenciais (ASAE −10,14 %; DECO −8,45 % / +4,71 %). |

### 5.C Da ASAE — encerrado sem resultado

| # | O que | Estado |
|---|---|---|
| C1 | Universo de lojas monitorizadas («1 220 lojas») | 🔴 **Não confirmável.** Sem informação oficial no sítio da ASAE. **Decisão: não fazer referência ao número.** O dado atual disponível é outro e não substituível — 22 242 operadores económicos fiscalizados em 2026, sem desagregação. |
| C2 | Série de monitorização do cabaz próprio desde jan/2022 | 🔴 **Não existe publicamente.** Só notícias que remetem para o cabaz da DECO. A afirmação da nota §1.4 de que a ASAE mantém monitorização própria de um cabaz desde jan/2022 **não é sustentável em fonte pública** e deve ser retirada ou requalificada. |

> **Consequência para a nota de enquadramento.** Duas afirmações do quadro de fontes caem: as
> «1 220 lojas» e a série própria da ASAE. Mantém-se o que está documentado — a monitorização do
> IVA Zero em 2023, cujos valores o PDF de 06.08.2026 confirma.

### 5.D Recolha própria — concluída em 07.08.2026

| # | O que | Estado |
|---|---|---|
| ~~E1~~ | Observatório de Preços Agroalimentar | ✅ **Concluído.** Encontrado o *endpoint* que serve os gráficos (`get_produto_graph` em `admin-ajax.php`): **39 produtos × 58 períodos de quatro semanas desde 03.01.2022**, com preço na produção e no consumo. Não foi preciso *scraping* de PDF. Ver §2.15. |
| ~~E2~~ | Cotações SIMA na produção | ⚪ **Dispensado** — o SIMA é a fase «Produção» do Observatório e já vem incorporado no E1. |
| ~~E3~~ | FAO «Cost of a Healthy Diet» | ✅ **Resolvido** — ver §2.14. A API do FAOSTAT devolve 401, mas a série publicada no **SOFI 2026** cobre Portugal de 2017 a 2025. Corrijo a minha conclusão anterior de que não haveria série para Portugal. |
| ~~E3~~ | FAO «Cost of a Healthy Diet» | ✅ **Resolvido** — ver §2.14. A API do FAOSTAT devolve 401, mas a série publicada no **SOFI 2026** cobre Portugal de 2017 a 2025. Corrijo a minha conclusão anterior de que não haveria série para Portugal. |

---

## 6. Prioridade sugerida

Reordenada face à decisão D1 (usos **a** e **c** — debate público *e* monitorização permanente),
que privilegia o que é ao mesmo tempo comunicável e automatizável.

**A recolha está encerrada e a âncora está decidida** (opção 3, o intervalo). Tudo o que segue é
implementação — nada depende já de dados externos.

1. ~~**Âncora em intervalo** (§2.10)~~ — ✅ **feito em 07.08.2026** (commit `da58135`). Seletor de
   base na barra lateral, intervalo no topo da aba 1, sensibilidade no simulador de IVA.
2. ~~**Cabaz por quintil** com o Q.2.11~~ — ✅ **feito em 08.08.2026**. Entrega a linha #2 (Alta).
   Implementado com ponderação IDF, segundo a arquitetura de §2.16, e com a regra de apresentação
   das três grandezas em conjunto. Inclui a comparação IDF/IHPC na aba de metodologia.
3. ~~**Quadro dos seis instrumentos** na aba «Metodologia e fontes»~~ — ✅ **feito em 08.08.2026**.
   Entrega a linha #1 (Alta). Inclui o posicionamento explícito da própria ferramenta, que não é um
   sétimo cabaz, e o aviso de leitura pública sobre o número da DECO.
4. ~~**Afinar a limitação 8** com o critério do documento metodológico (§2.7)~~ — ✅ **feito em
   08.08.2026**, na app e no README, com o sentido do enviesamento explicitado.
5. ~~**Törnqvist ao nível das classes**~~ — ✅ **feito em 08.08.2026**, na aba do histórico. Não
   demonstrou o que se esperava: o viés é de 0,12 p.p./ano, residual. O apuramento é útil na mesma,
   mas **muda o argumento** — ver §2.17 e a consequência para a nota, abaixo.
6. ~~**Escalas de equivalência**: passar a ressalva de qualitativa a quantificada~~ — ✅ **feito em
   08.08.2026**. O teste de §2.13 passou para a aba de metodologia, com o controlo na despesa total.
   Rendeu mais do que se previa: a escala por defeito da app deixa de ser uma escolha teórica e
   passa a ser a que o teste elege, calculada em tempo de execução.
7. ~~**Os três limiares de acessibilidade** (§2.14)~~ — ✅ **feito em 08.08.2026**, na aba 1. Os
   três saem sempre juntos, com o confronto Portugal–Espanha. A regra de «nunca sozinho» está
   garantida por construção: os três indicadores partilham o mesmo bloco e a mesma nota de leitura.
8. ~~**Observatório de Preços** (§2.15)~~ — ✅ **feito em 08.08.2026**, em separador próprio.
   Recolha reprodutível por script, com ficheiro versionado. **A lista de prioridades fica
   encerrada.**

---

## 7. Alterações ao repositório em 07.08.2026

| # | Alteração | Estado |
|---|---|---|
| 1 | Criado `.streamlit/config.toml` — a app corria sem o tema institucional | ✅ |
| 2 | Criado `.gitignore` | ✅ |
| 3 | Removidos 7 ficheiros órfãos da raiz com conteúdos trocados: `calculos.py`, `config.py`, `config.toml`, `download`, `eurostat.py`, `logo_b64.txt`, `test_calculos.py` | ✅ |
| 4 | Corrigida a frase truncada em `app.py` sobre o precedente IVA Zero, com os valores confirmados do PDF (ASAE −10,14 %; DECO −8,45 % aos 3 meses; +4,71 % no balanço final) | ✅ |
| 5 | Corrigida a afirmação incorreta sobre a receita cessante em `app.py` e `README.md` | ✅ |
| 6 | Criado este documento | ✅ |

**Verificação:** 15 testes passam; `app.py` sem erros de sintaxe.

---

## 8. Alterações ao repositório em 08.08.2026

| # | Alteração | Estado |
|---|---|---|
| 1 | `src/config.py`: acrescentados os quadros Q.2.11 do IDF por quintil — níveis, pesos no orçamento e despesa por classe | ✅ |
| 2 | `src/calculos.py`: `cabaz_quintis()`, `composicao_quintis()` e `comparar_ponderadores()` | ✅ |
| 3 | `app.py`, aba 1: secção «Quem está mais exposto — por quintil de rendimento», com tabela das três grandezas, composição por quintil, diferenças Q5−Q1 e exportação em CSV | ✅ |
| 4 | `app.py`, aba 5: expansor «Duas bases de ponderação — qual serve para quê», com o diagnóstico quantificado em direto e o registo da terceira base rejeitada | ✅ |
| 5 | `app.py`: substituída a «ressalva a confirmar» sobre turistas nos ponderadores do IHPC — está confirmada em fonte primária | ✅ |
| 6 | `app.py`: corrigido o passo 1 do quadro de fórmulas, que ainda descrevia a âncora como sendo só das Contas Nacionais | ✅ |
| 7 | `app.py`: corrigido o cabeçalho de proveniência dos CSV, que afirmava âncora única | ✅ |
| 8 | `tests/test_calculos.py`: 7 testes novos sobre os quintis e a comparação de ponderadores | ✅ |
| 9 | `README.md`: secções «As duas bases de ponderação» e «Cabaz por quintil de rendimento» | ✅ |
| 10 | `app.py`, aba 5: quadro dos seis instrumentos «O que é — e o que não é — o cabaz», aberto por defeito, com o posicionamento da própria ferramenta e o aviso de leitura pública | ✅ |
| 11 | `app.py` e `README.md`: limitação sobre preço de prateleira reescrita com o critério citado do DMet_IPC e o sentido do enviesamento (§2.7) | ✅ |
| 12 | `src/eurostat.py`: `indice_classes()` — índice mensal por classe, matéria-prima do Törnqvist | ✅ |
| 13 | `src/calculos.py`: `indices_comparados()` e `_dezembros()` — cabaz fixo, Törnqvist e viés | ✅ |
| 14 | `app.py`, aba 2: secção «Cabaz fixo contra cabaz que acompanha o consumo», com os três índices, o quadro de construção e a aproximação declarada | ✅ |
| 15 | `tests/test_calculos.py`: 4 testes novos sobre o Törnqvist, incluindo o caso em que o ponderador migra para a classe barata e o cabaz fixo tem de sobrestimar | ✅ |
| 16 | `src/config.py` e `src/calculos.py`: dados e funções do teste das escalas — `testar_escalas()` e `escala_mais_proxima()` | ✅ |
| 17 | `app.py`, aba 5: ressalva das escalas passa de qualitativa a medida, com o controlo na despesa total; barra lateral assinala a escala apurada e avisa quando se escolhe outra | ✅ |
| 18 | `tests/test_calculos.py`: 4 testes sobre as escalas, incluindo a inversão de sinal entre alimentação e despesa total | ✅ |
| 19 | `src/eurostat.py`: `obter()` ganha o parâmetro `extra`, que preserva uma dimensão própria do conjunto — sem ele, as três séries de `ilc_mdes03` vinham empilhadas e indistinguíveis | ✅ |
| 20 | `src/eurostat.py`: `privacao_alimentar()` e `PRIVACAO_NIVEIS` | ✅ |
| 21 | `src/config.py`: séries do FAO SOFI 2026 — custo, incapacidade e população afetada | ✅ |
| 22 | `app.py`, aba 1: secção «Acessibilidade alimentar — três limiares, três respostas», com o confronto Portugal–Espanha e as ressalvas de uso | ✅ |
| 23 | `app.py`: corrigida a afirmação de que uma medida por escalão de rendimento «exigiria o IDEF/INE ou microdados» — passou a existir na própria página | ✅ |
| 24 | `tests/test_calculos.py`: 3 testes sobre a preservação de dimensões, incluindo a recusa de uma dimensão inexistente | ✅ |
| 25 | `scripts/recolher_observatorio.py`: recolha reprodutível do Observatório do GPP, com descoberta automática de setores e produtos | ✅ |
| 26 | `dados/observatorio.csv` e `dados/observatorio_meta.json`: 3 074 observações versionadas, com data de extração | ✅ |
| 27 | `src/observatorio.py`: leitura, variações no período comum e classificação de padrões de transmissão | ✅ |
| 28 | `app.py`: separador novo «Da produção ao consumo» — panorama, padrões, detalhe por produto e exportação | ✅ |
| 29 | `tests/test_calculos.py`: 5 testes sobre o Observatório, incluindo a restrição ao período comum | ✅ |

**Verificação:** 38 testes passam; render completo da aplicação sem exceções nem erros de ecrã,
nas duas bases de âncora; os valores do IDF fecham com os totais publicados a menos de 1 €/ano de
arredondamento do próprio quadro do INE; o Törnqvist calculado fica a 0,12 pontos do IHPC oficial,
apesar de construído por via independente.

### Consequência de §2.17 para a nota de enquadramento

O eixo 4 da nota propõe o Törnqvist para «corrigir o viés de substituição e aproximar o indicador
do que o consumidor realmente paga». O apuramento mostra que, **ao nível das nove classes, quase
não há o que corrigir** — 0,12 p.p./ano.

A recomendação não cai, mas muda de fundamento. Deixa de ser «o cabaz fixo sobrestima a inflação»,
que os dados não sustentam com esta granularidade, e passa a ser: **a composição fixa falha onde
não se consegue medir** — marca, calibre, embalagem, insígnia. É um argumento mais honesto e, para
o debate, mais sólido: não depende de uma magnitude que alguém pode ir verificar e desmentir.

✅ **Alterado na nota em 08.08.2026** (correção 6 de §9). Decisão do Gabinete: *«se a expectativa
não está confirmada então podemos seguir com a nota segura sobre o que sabemos»*. A recomendação do
eixo 4 mantém-se; o que muda é o fundamento invocado, que passa a ser o que os dados sustentam.

---

## 9. Correções aplicadas à nota de enquadramento de 21.07.2026

Aplicadas diretamente em `2026-07-21_UPE_NG_SETCS_Cabaz_NotaEnquadramento.html`, com registo
visível no próprio documento, em 08.08.2026. Autorização permanente dada pelo Gabinete para
corrigir erros deste tipo assim que sejam detetados.

| # | Local | O que dizia | O que passa a dizer | Fundamento |
|---|---|---|---|---|
| 1 | §1.3, cartão «Onde está a pressão» | Que o impacto regressivo decorre de a subida se concentrar em bens com maior peso na base da distribuição | Que o impacto **é regressivo por via da exposição orçamental** (14,8 % contra 9,1 %), e não de uma inflação mais alta na base | §2.16 — a inflação por quintil varia 0,18 p.p. e é mais alta no quintil mais rico |
| 2 | §1.1, quadro dos instrumentos | Observatório de Preços com **26 produtos** | **39 produtos**, com séries que recuam a janeiro de 2022 | §2.15 — extração direta do portal em 07.08.2026 |
| 3 | §1.1 e §1.4, linhas da ASAE | Recolha em **«1 220 lojas, físicas e online»** | Referência **retirada**, sem substituição | §5.C — não confirmável em fonte pública; decisão do Gabinete de 08.08.2026 |
| 4 | §1.4, linha da ASAE | **«Monitorização própria de um cabaz desde janeiro de 2022»** | Referência **retirada**; mantém-se a monitorização documentada do cabaz IVA zero de 2023–24 | §5.C — a série própria não tem suporte público |
| 5 | §1.1, quadro do IVA Zero | «DECO: −5,8 % no período inicial» | Valores publicados, com o balanço final de **+4,71 %** e a nota de que a DECO mede 41 dos 63 produtos | Notas de verificação, p.3 do `cabaz_06082026.pdf` |
| 6 | §1.5, eixo 4 | «Corrige o viés de substituição e aproxima o indicador do que o consumidor realmente paga» | Mantém a recomendação, mas com o viés medido (0,12 p.p./ano, residual) e o fundamento deslocado para o que **não** se consegue medir | §2.17 — decisão do Gabinete de 08.08.2026 |

**Sobre a correção 1.** A conclusão da nota estava certa; o mecanismo invocado é que não estava.
A distinção não é académica: se a regressividade viesse da composição do cabaz, uma medida dirigida
a produtos específicos (IVA sobre carne, por exemplo) atacaria o problema. Vindo da exposição, não
ataca — o instrumento adequado é do lado do rendimento, ou uma medida que reduza a fatura alimentar
na proporção do que cada agregado gasta. A formulação corrigida é também mais robusta, porque a
exposição orçamental é estrutural, ao passo que a diferença de taxas se altera de mês para mês.

O argumento da nota sobre elasticidade e renúncia na base da distribuição foi **mantido**, mas
reposicionado: é uma perda de bem-estar que o índice de preços não capta, não uma explicação para
uma inflação medida mais alta. São coisas diferentes e a nota fundia-as.

**Sobre as correções 3 e 4.** Foram supressões, não substituições — não existe valor alternativo em
fonte pública. O único dado de dimensão que a ASAE publica é de outra natureza e não é
substituível: 22 242 operadores económicos fiscalizados em 2026, sem desagregação por tipo de
estabelecimento nem ligação ao cabaz. Decisão do Gabinete em 08.08.2026: *«eliminamos a referência
ao número de lojas porque não consegui confirmar»*.

A caixa inserida na nota regista ainda um dado que o quadro original não continha e que é o mais
relevante para avaliar o precedente do IVA Zero: o balanço final de **+4,71 %**. O quadro
apresentava apenas as descidas iniciais, o que dava do episódio uma leitura mais favorável do que
os dados sustentam.

**Correção 5 — o −5,8 % da DECO.** Numa primeira leitura afirmei que o −5,8 % do quadro e o
−8,45 % do documento de 06.08.2026 se referiam a períodos diferentes e podiam ambos estar certos.
**Isso está errado.** As notas de verificação na p.3 do `cabaz_06082026.pdf` são explícitas: o
−5,8 % *«consegui confirmar em nenhuma fonte primária (nem jornalística)»*, com a recomendação de
usar em vez dele os valores efetivamente publicados. Não é uma diferença de período — é um valor
sem suporte. Substituído na nota.

**Proveniência dos valores do IVA Zero**, apurada na p.2 do mesmo documento:

| Valor | Medidor | Período | Universo | Fonte citada |
|---|---|---|---|---|
| **−10,14 %** | ASAE | 18.04 → 04.09.2023 | Bens abrangidos pela isenção | portugal.gov.pt |
| −9,67 % | ASAE | 17.04 → fim de junho 2023 | idem | Sapo |
| −9,29 % | ASAE | 17.04 → 28.08.2023 | idem | Sapo |
| **−8,45 %** (−11,72 €) | DECO | 3 meses | **41 dos 63 produtos** | Adefesa |
| **+4,71 %** (+6,45 €, 136,83 → 143,28 €) | DECO | 18.04.2023 → 04.01.2024 | **41 dos 63 produtos** | Jornal SOL |

Duas qualificações que não tinham sido registadas e que importam:

1. **Os valores da DECO referem-se a 41 produtos, não aos 63 do cabaz semanal.** Citá-los como
   «o cabaz da DECO» é impreciso.
2. **ASAE e DECO não são comparáveis entre si** — universos, amostras e períodos diferentes. A
   divergência entre as duas leituras não demonstra, por si, discrepância metodológica: podem estar
   as duas certas sobre coisas diferentes.

Nenhum destes valores isola o efeito do IVA da evolução dos preços de base, pelo que **nenhum é
uma estimativa de repercussão**. É a razão pela qual o simulador trata a repercussão como
parâmetro explícito.

**Nota sobre o ambiente:** o `.venv` do projeto está vazio. Para o tornar funcional:
`.venv\Scripts\pip install -r requirements.txt`.
