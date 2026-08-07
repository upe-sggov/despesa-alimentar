# Cabaz alimentar — levantamento de lacunas, dados verificados e recolha em falta

**Data:** 7 de agosto de 2026
**Autor:** UPE · DSSD · SGGov
**Estatuto:** documento de trabalho — base para validação. Não constitui posição oficial.

**Objeto.** Confronto entre (a) a nota técnica de enquadramento de 21.07.2026, (b) o documento
`cabaz_06082026.pdf` e (c) a aplicação *despesa-alimentar*. Identifica o que falta, verifica
o que é exequível, e lista os dados que é preciso ir buscar.

**Nota sobre a verificação.** Todos os valores da secção 2 foram extraídos por chamada direta à
API do Eurostat em 07.08.2026. Não são citações — são leituras. Os códigos de conjunto de dados
estão indicados para reprodução.

---

## 1. Sumário — estado de cada eixo

### Os sete eixos de melhoria (nota §1.5)

| # | Eixo | Estado | Via |
|---|---|---|---|
| 1 | Ponderar pela estrutura real de consumo (IDEF) | 🟡 Parcial | Híbrido IHPC + HBS; versão plena exige INE |
| 2 | Desagregar por decil de rendimento | 🟢 **Viável já** | Eurostat `hbs_str_t223` |
| 3 | Desagregar territorialmente | 🟡 Parcial | Grau de urbanização e NUTS 2 sim; concelho não |
| 4 | Incorporar substituição efetiva (Fisher/Törnqvist) | 🟢 **Viável já** | Törnqvist ao nível das classes |
| 5 | Indicador de acessibilidade alimentar | 🟢 Feito + reforço | Já existe; `ilc_mdes03` acrescenta muito |
| 6 | Explorar *scanner data* | 🔴 Não é cálculo | Diligência junto do INE |
| 7 | Validar contra e-fatura / AT | 🔴 Não é cálculo | Diligência, via INE |

### As quatro linhas de trabalho (nota §1.6)

| # | Produto | Prioridade | Estado |
|---|---|---|---|
| 1 | Nota metodológica «O que é (e o que não é) o cabaz» | Alta | 🟡 Existe em prosa no README; ausente da interface |
| 2 | Cabaz ponderado por decil de rendimento | Alta | 🟢 Dados disponíveis — ver §2.1 |
| 3 | Desagregação territorial do preço alimentar | Média | 🟡 Só ao nível urbano/rural e NUTS 2 |
| 4 | Benchmarking europeu da inflação alimentar | Média | ✅ Já feito (aba 4) |

### Instrumentos que a app não cobre

A app usa **um** dos seis instrumentos da nota §1.1: o IPC/IHPC. Ausentes: Observatório de Preços
Agroalimentar (GPP), cabaz de apoio alimentar PO APMC/DGS. Ausentes por opção deliberada e bem
fundamentada: DECO, ASAE.

---

## 2. Dados verificados e disponíveis

### 2.1 Peso da alimentação por quintil de rendimento

**Conjunto:** `hbs_str_t223` · dims `[freq, quant_inc, coicop, unit, geo, time]` · unidade: por mil (‰)
da despesa total do agregado · vagas 2010/2015/2020.

O quintil mapeia exatamente o pedido da nota: **D1–D2 ≡ Q1**, **D9–D10 ≡ Q5**.

| Vaga | COICOP | Q1 | Q2 | Q3 | Q4 | Q5 | Rácio Q1/Q5 |
|---|---|---|---|---|---|---|---|
| 2015 | CP01 (alim. + bebidas n/alc.) | 183 | 168 | 156 | 144 | 116 | 1,58 |
| 2015 | CP011 (alimentação) | 172 | 157 | 145 | 134 | 108 | 1,59 |
| **2020** | **CP01** | **171** | 146 | 145 | 131 | **100** | **1,71** |
| 2020 | CP011 | — não publicado para PT — | | | | | |

**Leitura.** O quintil mais pobre afeta 17,1 % do orçamento à alimentação; o mais rico, 10,0 %.
O efeito regressivo que a nota afirma está aqui quantificado, em fonte oficial aberta. O rácio
agravou-se entre 2015 e 2020 (1,58 → 1,71).

**Limitação crítica.** O detalhe COICOP a 4 dígitos (CP0111–CP0119) **não está preenchido para
Portugal por quintil**. Existe a dimensão, não existem os valores. Consegue-se o agregado
alimentar por quintil, não a repartição por classe dentro de cada quintil. → ver recolha **A1**.

### 2.2 Nível de despesa por quintil

**Conjunto:** `hbs_exp_t133` · PT, 2020 · **unidade: PPS, não euros**.

| Unidade | TOTAL | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|---|
| PPS por agregado | 24 499 | 12 612 | 17 414 | 21 967 | 28 070 | 42 456 |
| PPS por adulto equivalente | 14 924 | 9 914 | 12 032 | 13 416 | 16 263 | 23 006 |

**Uso.** Como não vem em euros, usa-se a *estrutura relativa* entre quintis e ancora-se no valor
em euros que a app já calcula a partir das Contas Nacionais.

### 2.3 Peso da alimentação por composição do agregado

**Conjunto:** `hbs_str_t224` · dim `hhcomp` · PT, 2020 · CP01, ‰.

| 1 adulto | 1 adulto c/ filhos | 2 adultos | 2 adultos c/ filhos | 3+ adultos | 3+ adultos c/ filhos |
|---|---|---|---|---|---|
| 112 | 102 | 135 | 114 | 149 | **157** |

**Leitura — com cautela.** A série 112 → 135 → 149 (1, 2, 3+ adultos) mostra o peso orçamental
a subir com o número de adultos, o que é consistente com a ressalva metodológica da app: a
alimentação tem economias de escala mais fracas do que o consumo total, e a escala OCDE
modificada subestima agregados maiores.

**Mas não é prova.** Os agregados com filhos dependentes apresentam pesos *inferiores* aos
equivalentes sem filhos (102 < 112; 114 < 135). A quota orçamental está confundida com o
rendimento e com a estrutura das outras despesas. Serve para *testar* a ressalva, não para a
confirmar. Uma verificação séria exige despesa alimentar em euros por tipo de agregado.

### 2.4 Peso da alimentação por grau de urbanização

**Conjunto:** `hbs_str_t226` · dim `deg_urb` · PT, 2020 · CP01, ‰.

| Cidades | Vilas e subúrbios | Áreas rurais |
|---|---|---|
| 115 | 139 | **151** |

Gradiente territorial claro, sem necessidade de dados concelhios. Responde parcialmente ao eixo 3.

### 2.5 Privação alimentar — série anual até 2025

**Conjunto:** `ilc_mdes03` · dims `[freq, hhcomp, rskpovth, unit, geo, time]` · série 2003–2025 ·
indicador: % que não consegue pagar uma refeição com carne, frango ou peixe de dois em dois dias.

| Grupo | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Total da população | 2,3 | 2,5 | 2,4 | 3,0 | 2,3 | 2,5 | **1,9** |
| Abaixo do limiar de pobreza | 5,7 | 7,2 | 5,9 | 7,2 | 5,9 | 5,1 | **5,5** |
| Acima do limiar de pobreza | 1,6 | 1,6 | 1,6 | 2,2 | 1,6 | 2,0 | 1,3 |

Por composição do agregado (todos os níveis de rendimento):

| Composição | 2019 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| 1 adulto | 4,4 | 5,1 | 5,2 | 5,1 | 4,0 | 4,5 |
| 1 adulto, 65+ anos | 4,2 | 5,9 | 6,0 | 5,3 | 4,4 | 4,7 |
| 1 adulto c/ filhos dependentes | 4,2 | 4,8 | 5,2 | 2,8 | 2,3 | 3,4 |
| 2 adultos | 3,0 | 3,3 | 3,1 | 2,4 | 2,5 | 2,3 |
| 3+ adultos c/ filhos dependentes | 2,2 | 1,1 | 2,7 | 1,1 | 2,2 | 2,1 |

**Porque é que isto importa.** É anual, vai até **2025** (o HBS pára em 2020), cruza com o seletor
de composição que a app já tem, e traz a dimensão distributiva por limiar de pobreza. Custo de
implementação baixíssimo: mesma API, mesmo padrão do código existente.

> ⚠️ **Ponto que exige arbitragem antes de entrar na app.** O indicador de *custo* está em máximos
> históricos enquanto o de *privação alimentar* está no mínimo da série (1,9 % em 2025). Não são
> contraditórios — medem coisas diferentes — mas a tensão é analiticamente relevante e
> politicamente utilizável nos dois sentidos. A privação é auto-reportada, de inquérito por
> amostragem, e **não verifiquei intervalos de confiança**. Validar com o INE antes de publicar.

### 2.6 Outros conjuntos que respondem

| Conjunto | Conteúdo | Observações | Último período |
|---|---|---|---|
| `hbs_str_t211` | Estrutura de despesa por COICOP | 1 013 obs. | 2020 |
| `nama_10r_2hhinc` | Rendimento das famílias, NUTS 2 | 112 065 obs. — permite Engel regional | 2024 |
| `ilc_di01` | Distribuição do rendimento por quantil | 4 431 obs. | 2025 |
| `ilc_di04` | Rendimento mediano por quantil | 2 652 obs. | 2025 |
| `prc_hicp_midx` / `prc_hicp_inw` | Já usados pela app (controlo) | ✅ | 2025-12 / 2025 |

`apri_fo_cofrui` (preços agrícolas na produção) devolve **404** — código inválido ou descontinuado.

---

## 3. Acessibilidade das fontes a partir de ambiente automatizado

Testado em 07.08.2026. Confirma empiricamente o «Constrangimento de infraestrutura» da nota §1.6.

| Fonte | Estado |
|---|---|
| Eurostat | ✅ responde |
| `www.gpp.pt` | ✅ responde |
| `observatorioagroalimentar.gov.pt` | ✅ responde |
| `www.asae.gov.pt` | ✅ responde |
| `www.ine.pt` | ❌ *timeout* de ligação |
| `dados.gov.pt` | ❌ *timeout* de ligação |
| `www.dgeconomia.gov.pt` | ❌ erro de ligação |

**Ação para a DSTD:** pedir desbloqueio de saída para `www.ine.pt`, `dados.gov.pt` e
`www.dgeconomia.gov.pt`. Sem isto, qualquer monitorização contínua que dependa destas fontes é
inviável e o INE — que a nota classifica como base primária — fica inacessível por via
programática.

---

## 4. Métodos de cálculo propostos

### 4.1 Cabaz por quintil de rendimento (eixo 2 / linha #2)

```
peso_q      = hbs_str_t223[CP01, quintil q, 2020] / 1000
nivel_q     = hbs_exp_t133[PPS_HH, q] / hbs_exp_t133[PPS_HH, TOTAL]
despesa_q   = despesa_alimentar_media_app × nivel_q × (peso_q / peso_TOTAL)
```

Depois aplica-se a cada quintil a variação homóloga por classe que a app já calcula.

**A declarar:** a *composição* é de 2020; só os *preços* são correntes. É a mesma lógica que a app
já usa para a âncora das Contas Nacionais, e deve ser declarada nos mesmos termos.

### 4.2 Índice de Törnqvist ao nível das classes (eixo 4)

A app não pode construir um Fisher — não tem quantidades nem preços por produto. Mas o Törnqvist
precisa de participações de despesa, não de quantidades, e essas a app já descarrega:

```
ln(T) = Σᵢ [(wᵢ,₀ + wᵢ,ₜ) / 2] × ln(Pᵢ,ₜ / Pᵢ,₀)
```

com `wᵢ` de `prc_hicp_inw` (anual, atualizado) e `Pᵢ` de `prc_hicp_midx`.

Corrige a substituição **entre** classes, não dentro delas. Posto ao lado de um Laspeyres de
ponderadores congelados, torna o viés de substituição *visível e quantificado* em vez de apenas
explicado em prosa. Melhor relação esforço/demonstração de toda a lista.

### 4.3 Correção da afirmação sobre receita cessante

Verificado numericamente (106 €, de 23 % para 6 %):

| Repercussão | Preço final | Base tributável | Receita nova | Δ Receita |
|---|---|---|---|---|
| 0 % | 106,00 € | 100,00 € | 6,00 € | **−13,82 €** |
| 100 % | 91,35 € | 86,18 € | 5,17 € | **−14,65 €** |

Amplitude ≈ 6 %. Confirma o ponto 2 da auditoria de 27.07.2026: a receita cessante **só** é
independente da repercussão numa isenção total.

---

## 5. Recolha em falta — o que é preciso ir buscar

### 5.A Do INE — só por acesso manual (API bloqueada)

| # | O que | Onde | Formato ideal | Desbloqueia |
|---|---|---|---|---|
| **A1** | **IDEF 2022/2023 — coeficientes de despesa COICOP a 4 dígitos (CP0111–CP0119) por decil de rendimento** | ine.pt → Base de Dados → Despesas das Famílias; ou quadros anexos da publicação IDEF 2022/2023 | Excel/CSV; PDF serve | Eixos 1 e 2 na versão plena. **É o item mais importante da lista.** |
| A2 | O mesmo, por NUTS II | idem | Excel/CSV | Eixo 3 ao nível regional |
| A3 | Despesa alimentar média **em euros** por tipo de agregado | IDEF, quadros por composição | Excel/CSV | Valida (ou refuta) a ressalva das escalas de equivalência — ver §2.3 |
| A4 | Documento metodológico do IPC — secção sobre fontes de preços | ine.pt → IPC → metainformação | PDF | Eixo 6: saber se o IPC já usa *scanner data* |
| A5 | N.º de agregados domésticos privados, atualização pós-Censos 2021 | ine.pt | valor + fonte | Confirma o divisor da app (hoje 4 149 096) |

> **Nota sobre A1.** A nota aponta o IDEF 2022/2023, que é mais recente e mais rico do que a vaga
> HBS de 2020 que já tenho. O HBS permite avançar já; o IDEF é a versão que a nota pede. Se A1 vier,
> substitui-se — não se acumula.

### 5.B Da DGE — bloqueado por rede

| # | O que | Onde | Formato ideal | Desbloqueia |
|---|---|---|---|---|
| B1 | Mapa do Comércio, Serviços e Restauração — estabelecimentos georreferenciados | dgeconomia.gov.pt (2025, Agenda Comércio e Serviços 2030) | Shapefile / GeoJSON / CSV com coordenadas | Denominador dos *food deserts* (eixo 3) |
| B2 | Histórico oficial de monitorização do cabaz IVA Zero | DGE (ex-DGAE) | Excel/CSV | Retro-teste do simulador |

### 5.C Da ASAE

| # | O que | Onde | Desbloqueia |
|---|---|---|---|
| C1 | Confirmação do universo de lojas monitorizadas (as «1 220 lojas» que não conseguiu confirmar) | asae.gov.pt ou contacto | Fecha uma nota de verificação em aberto |
| C2 | Série de monitorização do cabaz próprio desde jan/2022 | idem | Contraponto público ao cabaz DECO |

### 5.D Decisões suas — não são dados

| # | Questão |
|---|---|
| D1 | Qual o uso final pretendido pelo Gabinete: (a) armar para o debate, (b) suportar desenho de medidas, (c) monitorização permanente? A nota diz que sem isto o risco é entregar trabalho sólido e desajustado. |
| D2 | Arbitrar a divergência: nota diz +37 % desde jan/2022 e +6,05 % desde início de 2026; o PDF diz +33,88 % e +3,91 %. Presumo que prevaleça o PDF, mais recente e com fonte. |
| D3 | O ponto de tensão da §2.5 (custo em máximos vs. privação em mínimos) entra na app, fica só na nota, ou fica de fora até validação com o INE? |

### 5.E O que eu próprio posso ir buscar — só precisa de autorização

Estas fontes **respondem** a partir daqui; não precisa de as recolher.

| # | O que | Esforço | Nota |
|---|---|---|---|
| E1 | Boletins do Observatório de Preços Agroalimentar (26 produtos, margens ao longo da cadeia) | Médio | O portal é WordPress sem *endpoint* de dados abertos — implica *scraping* das páginas ou parsing dos PDF. Frágil a mudanças de layout. |
| E2 | Cotações SIMA na produção (`regsima.gpp.pt`) | Médio | Complementa E1 no elo da produção |
| E3 | Metadados metodológicos do IHPC para PT no Eurostat | Baixo | Pode responder ao A4 sem depender do INE |
| E4 | FAO / Banco Mundial «Cost of a Healthy Diet» | Baixo | **Não testado** — não confirmo que tenha série para Portugal |

---

## 6. Prioridade sugerida

1. **Quadro dos seis instrumentos na aba «Metodologia e fontes»** — zero dependências de dados,
   entrega a linha #1 (prioridade Alta) dentro da app.
2. **`ilc_mdes03`** — baixo custo, alto valor, atual até 2025. Sujeito a D3.
3. **Törnqvist ao nível das classes** — sem dados novos, demonstra o viés de substituição.
4. **Cabaz por quintil com o HBS 2020** — entrega a linha #2 (Alta) na versão possível hoje.
5. **A1 (IDEF por decil)** — quando chegar, faz a versão plena de 1 e 2.
6. **E1 (Observatório)** — a única via para a pergunta das margens, mas a de maior esforço.

---

## 7. Correções aplicadas ao repositório em 07.08.2026

| # | Correção | Estado |
|---|---|---|
| 1 | Criado `.streamlit/config.toml` — a app corria sem o tema institucional | ✅ |
| 2 | Criado `.gitignore` | ✅ |
| 3 | Removidos 7 ficheiros órfãos da raiz com conteúdos trocados: `calculos.py`, `config.py`, `config.toml`, `download`, `eurostat.py`, `logo_b64.txt`, `test_calculos.py` | ✅ |
| 4 | Corrigida a frase truncada em `app.py` sobre o precedente IVA Zero, com os valores confirmados do PDF | ✅ |
| 5 | Afirmação incorreta sobre a receita cessante (`app.py` e `README.md`) | ⏳ redação proposta, a aguardar validação |

Verificação: 15 testes passam; `app.py` sem erros de sintaxe.
