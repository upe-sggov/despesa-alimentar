# Despesa alimentar — ferramenta de análise

Aplicação de apoio à decisão sobre a despesa alimentar das famílias em Portugal, desenvolvida
pela **Unidade de Pesquisa e Estatísticas (UPE)** da Direção de Serviços de
Suporte à Decisão, Secretaria-Geral do Governo.

Obtém dados oficiais em direto do Eurostat e permite decompor a despesa alimentar
por tipo de produto, acompanhar a série histórica, simular alterações do IVA e
comparar Portugal com os restantes Estados-Membros.

---

## Índice

1. [O que a aplicação faz](#o-que-a-aplicação-faz)
2. [Porquê Streamlit e não um ficheiro HTML](#porquê-streamlit-e-não-um-ficheiro-html)
3. [Estrutura do repositório](#estrutura-do-repositório)
4. [Instalação e execução local](#instalação-e-execução-local)
5. [Publicação no GitHub](#publicação-no-github)
6. [Alojamento no Streamlit Community Cloud](#alojamento-no-streamlit-community-cloud)
7. [Fontes de dados](#fontes-de-dados)
8. [Metodologia](#metodologia)
9. [Indicadores de esforço](#indicadores-de-esforço)
10. [Limitações a declarar](#limitações-a-declarar)
11. [Manutenção](#manutenção)
12. [Resolução de problemas](#resolução-de-problemas)

---

## O que a aplicação faz

A aplicação organiza-se em sete separadores.

**1 · Evolução do Cabaz.** Preço do cabaz essencial da DECO PROteste (63 bens
alimentares, composição fixa), série completa desde janeiro de 2022, com as
variações face à semana anterior, desde o início do ano e desde o início da
série, e os produtos que mais aumentaram em três janelas de comparação. É uma
referência externa e privada, não o indicador que os restantes separadores
calculam — ver [«Despesa alimentar» e não «cabaz»](#despesa-alimentar-e-não-cabaz).

**2 · Despesa e composição.** A despesa alimentar mensal por agregado, a partir
de uma de **duas bases oficiais à escolha** — o IDF ou as Contas Nacionais —,
atualizada ao mês mais recente pelo índice de preços. A aplicação reparte-a pelas
nove classes COICOP e aplica a cada uma a sua variação homóloga, devolvendo o
contributo de cada tipo de produto para o agravamento. Inclui o **cabaz por
quintil de rendimento**, o esforço face a três referências de rendimento e os
**três limiares de acessibilidade alimentar**.

**3 · Histórico.** Série mensal do índice de preços alimentares e da variação
homóloga, e a medição do **viés de substituição** — cabaz de composição fixa
contra índice de Törnqvist.

**4 · Da produção ao consumo.** Preços do mesmo produto nas duas pontas da
cadeia, a partir do Observatório de Preços Agroalimentar do GPP. Responde a
*«onde na cadeia está o aumento?»* — que nenhum outro separador toca.

**5 · Simulador de IVA.** Permite definir uma taxa por classe e, sobretudo,
regular a **repercussão** — a fração da alteração de imposto que chega ao preço
final. Mostra quanto poupa o consumidor, quanto fica na margem do operador e
qual a variação de receita.

**6 · Comparação UE-27.** Inflação alimentar harmonizada de Portugal face à
UE-27 e aos países selecionados, com ordenação do último mês disponível.

**7 · Fontes e método.** O quadro dos **seis instrumentos** que o debate público
confunde, a proveniência de cada elemento, o registo das ligações da sessão e as
limitações a declarar.

---

## Porquê Streamlit e não um ficheiro HTML

Uma versão anterior desta ferramenta era um ficheiro HTML autónomo que tentava
ler a API do Eurostat a partir do navegador. **Não funcionava** — e a razão não
era o código:

> Um navegador impede que uma página carregada de uma origem leia dados de outra
> origem (política de *same-origin*, controlada por cabeçalhos CORS). Uma página
> aberta a partir do disco tem origem `null`, e as redes institucionais
> reforçam ainda a restrição com *proxies* de saída.

Numa aplicação Streamlit, os pedidos ao Eurostat são feitos **pelo servidor, em
Python**, com a biblioteca `requests`. A política de mesma origem não se aplica a
pedidos servidor-a-servidor: o problema desaparece por construção.

Vantagens adicionais: os dados ficam em *cache* partilhada entre utilizadores,
a aplicação tem um endereço estável, e qualquer atualização feita no GitHub é
publicada automaticamente.

---

## Estrutura do repositório

```
despesa-alimentar/
├── app.py                  # aplicação Streamlit (interface e separadores)
├── requirements.txt        # dependências
├── README.md               # este ficheiro
├── .gitignore
├── .streamlit/
│   └── config.toml         # tema institucional SGGov
├── src/
│   ├── __init__.py
│   ├── config.py           # COICOP, países, cores, IDF por quintil, SOFI
│   ├── eurostat.py         # acesso aos dados (duas vias independentes)
│   ├── calculos.py         # decomposição, IVA, quintis, Törnqvist, escalas
│   ├── observatorio.py     # leitura e análise dos dados do GPP
│   └── deco.py             # leitura e variações do cabaz da DECO PROteste
├── scripts/
│   ├── recolher_observatorio.py   # recolha do Observatório (passo manual)
│   └── recolher_deco.py           # recolha do cabaz DECO (passo manual)
├── dados/                          # versionado, e tem de ser: a nuvem não corre os scripts
│   ├── observatorio.csv
│   ├── observatorio_meta.json
│   ├── deco_cabaz.csv
│   ├── deco_top10.csv
│   └── deco_meta.json
├── docs/
│   └── 2026-08-07_levantamento_lacunas.md   # apuramento e decisões
└── tests/
    └── test_calculos.py    # 176 testes dos cálculos analíticos
```

A separação entre **acesso a dados** (`eurostat.py`, `observatorio.py`),
**cálculo** (`calculos.py`) e **apresentação** (`app.py`) é deliberada: permite
testar a lógica sem levantar a interface, e substituir a fonte de dados sem tocar
no resto.

**Três fontes não vêm de API** e exigem atualização manual: o **FAO SOFI**
(inscrito em `src/config.py`, atualizar a cada edição anual), o **Observatório
do GPP** (recolhido por script para `dados/`, atualizar quando sair novo
período de quatro semanas) e o **cabaz da DECO PROteste** (idem, atualizar
quando a DECO publicar nova semana, às quartas-feiras). Todas estão assinaladas
como tal na interface.

---

## Instalação e execução local

Requer **Python 3.10 ou superior**.

```bash
# 1. Obter o código
git clone https://github.com/<utilizador>/despesa-alimentar.git
cd despesa-alimentar

# 2. Criar e ativar um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar
streamlit run app.py
```

A aplicação abre em `http://localhost:8501`.

Para correr os testes:

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Publicação no GitHub

### Pela interface web (mais simples)

1. Em [github.com](https://github.com), clique em **New repository**.
2. Nome: `despesa-alimentar`. Visibilidade: **Public** — necessário para o plano
   gratuito do Streamlit Community Cloud. Não adicione README, `.gitignore` nem
   licença (já existem).
3. **Create repository**.
4. No ecrã seguinte, escolha **uploading an existing file** e arraste todos os
   ficheiros e pastas.
5. **Commit changes**.

> **Atenção às pastas ocultas.** `.streamlit/` começa por ponto e alguns sistemas
> escondem-na. Se não a carregar, a aplicação funciona à mesma, mas sem o tema
> institucional. Em caso de dúvida, crie o ficheiro manualmente no GitHub com
> **Add file → Create new file** e o nome `.streamlit/config.toml` — escrever a
> barra cria a pasta automaticamente.

### Por linha de comandos

```bash
cd despesa-alimentar
git init
git add .
git commit -m "Ferramenta da despesa alimentar — versao inicial"
git branch -M main
git remote add origin https://github.com/<utilizador>/despesa-alimentar.git
git push -u origin main
```

---

## Alojamento no Streamlit Community Cloud

1. Aceda a [share.streamlit.io](https://share.streamlit.io) e entre com a conta
   do GitHub.
2. **Create app** → **Deploy a public app from GitHub**.
3. Preencha:

   | Campo | Valor |
   |---|---|
   | Repository | `<utilizador>/despesa-alimentar` |
   | Branch | `main` |
   | Main file path | `app.py` |
   | App URL | `sggov-despesa-alimentar` (ou outro nome disponível) |

4. **Deploy**. A primeira instalação demora 2 a 4 minutos.

A aplicação fica em `https://<nome-escolhido>.streamlit.app`.

**Atualizações.** Qualquer alteração enviada para o ramo `main` é publicada
automaticamente em poucos segundos. Não é preciso repetir a publicação.

**Suspensão por inatividade.** No plano gratuito, aplicações sem visitas durante
alguns dias entram em suspensão e reativam-se no primeiro acesso seguinte
(demora cerca de 30 segundos). Não há perda de dados.

**Sem segredos a configurar.** As APIs do Eurostat são públicas e não exigem
chave nem registo, pelo que não é necessário preencher a secção *Secrets*.

---

## Fontes de dados

Todos os dados quantitativos provêm do **Eurostat**, que difunde o índice
harmonizado de preços no consumidor (IHPC) compilado pelos institutos nacionais
— no caso português, o **INE**.

| Elemento | Conjunto de dados | O que mede | Frequência |
|---|---|---|---|
| Despesa alimentar (âncora) | `nama_10_cp18` | Despesa efetiva em euros, Contas Nacionais | Anual |
| Consumo total das famílias | `nama_10_cp18` | Denominador do coeficiente de Engel | Anual |
| Dimensão média do agregado | `ilc_lvph01` | N.º médio de pessoas | Anual |
| Número de agregados | `lfst_hhnhtych` (recuo: Censos 2021) | Divisor da despesa nacional | Anual |
| Ponderadores por grupo | `prc_hicp_iw` | Fração de cada mil euros de consumo (‰) | Anual |
| Índice de preços | `prc_hicp_minr` (unidade do índice) | Nível do índice — não são euros | Mensal |
| Variação homóloga | `prc_hicp_minr` (unidade `RCH_A`) | Subida face ao mesmo mês do ano anterior | Mensal |
| Nível de preços comparado | `prc_ppp_ind_1` | Quão caros são os alimentos (UE-27 = 100) | Anual |
| Rendimento equivalente | `ilc_di03` | Rendimento líquido médio e mediano (EU-SILC) | Anual |
| Salário mínimo | `earn_mw_cur` | Valor bruto legal mensal | Semestral |
| Salário médio | `nama_10_a10` ÷ `nama_10_a10_e` | Remuneração média bruta dos trabalhadores por conta de outrem | Anual |
| Decomposição da inflação | `prc_hicp_minr` | Alimentos transformados e não transformados; total e subjacente como enquadramento | Mensal |

> **Nota sobre os códigos.** Este quadro listou durante algum tempo `prc_hicp_manr`,
> `prc_hicp_inw`, `prc_hicp_midx` e `nama_10_co3_p3`, que a aplicação deixou de usar.
> O índice e a variação homóloga passaram a vir do mesmo conjunto, `prc_hicp_minr`,
> distinguidos pela unidade, e a âncora migrou para `nama_10_cp18` com a passagem à
> COICOP 2018. Corrigido a 20 de agosto de 2026. A lista viva está sempre em
> `src/eurostat.py` e no separador **Fontes e método** da aplicação, que mostra os
> conjuntos efetivamente consultados em cada sessão.

**Códigos obtidos por tentativa.** Três destes conjuntos usam nomenclaturas que não coincidem
com a COICOP do índice de preços, e cujos códigos exatos não foi possível verificar à distância:
`prc_ppp_ind_1`, `earn_mw_cur` e `ilc_di03`. O código tenta várias hipóteses e usa a primeira
que responda; se nenhuma responder, o painel respetivo não é apresentado e a ocorrência fica
registada no diagnóstico. Se algum painel não aparecer, é aí que se deve olhar.

### O número de agregados familiares

É o **divisor** de todo o cálculo: a despesa alimentar nacional é dividida por ele para obter
a despesa de um agregado. Duplicá-lo reduz o resultado a metade, pelo que não pode ser um
valor arbitrário.

A aplicação usa, por esta ordem:

1. **Eurostat / Inquérito ao Emprego** (`lfst_hhnhtych`) — valor anual, o mais recente disponível;
2. **INE, Censos 2021** — **4 149 096** agregados domésticos privados, se o anterior falhar.

O valor obtido é submetido a **verificação de plausibilidade** (entre 3,0 e 6,5 milhões). Fora
desse intervalo, presume-se que o conjunto devolvido não é o esperado e recorre-se ao valor
censitário, registando a ocorrência no diagnóstico. A despesa resultante é igualmente
verificada (entre 50 € e 3 000 € mensais por agregado); fora disso a aplicação mostra um erro
e desaconselha o uso dos números.

O campo está **bloqueado por defeito**. Existe uma opção de ajuste manual, destinada apenas a
testar cenários — quando ativada com um valor diferente do oficial, a aplicação avisa que os
resultados deixam de ser reproduzíveis a partir de fontes oficiais.


### A âncora em euros

O índice de preços dá **variações, nunca níveis**: não permite dizer «isto
custa X euros». É preciso uma âncora em euros.

**Há duas âncoras oficiais, e não coincidem.** Esta é a limitação mais importante
da ferramenta, apurada na aferição de 7 de agosto de 2026.

| Base | Como se obtém | Enviesamento |
|---|---|---|
| **Contas Nacionais** (`nama_10_cp18`, COICOP 01.1) | Agregado macroeconómico ÷ n.º de agregados ÷ 12 | **Sobrestima** — mede o consumo *no território*, incluindo o de não residentes |
| **IDF 2022/2023** (INE, quadro Q.2.11.a) | Medição direta da despesa declarada pelos agregados residentes | **Subestima** — os inquéritos às despesas sub-reportam sistematicamente |

Cada uma é atualizada para o mês corrente pelo índice de preços, a partir do seu
próprio ano de referência:

```
valor_atual = despesa_mensal_base × (índice_mês / índice_médio_ano_base)
```

**Para 2022 as duas divergem por um fator de 2,3** — 549 € contra 239 € por mês
para o agregado médio. É muito acima do desvio geral entre inquérito e Contas
Nacionais, que é de 1,7. A taxa de cobertura portuguesa da alimentação (44 %)
fica **abaixo do mínimo europeu de 58 %**, e na categoria que o Eurostat
identifica como a de menor disparidade entre países. Não existe exercício
nacional de conciliação que permita arbitrar.

**Por isso a aplicação não escolhe.** Apresenta o intervalo entre as duas bases,
declara que o ponto central não é determinável, e deixa a base de trabalho à
escolha na barra lateral — por defeito o IDF, por ser a medição direta da
pergunta que a ferramenta faz. O separador do simulador de IVA mostra sempre o
resultado na outra base, como sensibilidade.

Análise completa em [`docs/2026-08-07_levantamento_lacunas.md`](docs/2026-08-07_levantamento_lacunas.md),
secções 2.10 e 2.12.

Existe também um modo **«valor externo»**, para quem queira testar o que uma
recolha de terceiros implicaria. Esse valor é assinalado na interface como não
oficial e não deve ser apresentado como número da Secretaria-Geral.

### As duas bases de ponderação

A aplicação usa **duas** estruturas de ponderação, com uma divisão de trabalho
explícita:

| | Ponderador | Responde a |
|---|---|---|
| **Estrutura e distribuição** | INE, IDF 2022/2023, por quintil | Quem gasta o quê, e que parte do orçamento leva |
| **Movimento dos preços** | Eurostat, `prc_hicp_iw` (IHPC), revisto anualmente | Quanto subiu cada grupo, e quanto contribuiu |

A razão é conceptual. O Documento Metodológico do IPC (INE, 2023) afirma que
«o IHPC inclui a despesa realizada pelos não residentes ("turistas") no
território económico e exclui a despesa dos residentes no exterior, originando
uma estrutura de ponderação diferente da utilizada no IPC». Para medir preços
isso é irrelevante — um quilo de pão sobe o mesmo para quem lá vive e para quem
está de passagem. Para medir a *estrutura de consumo das famílias portuguesas*,
não é: mistura dois universos. É a mesma contaminação que levou a aplicação a
abandonar as Contas Nacionais como âncora única.

O INE publica ponderadores do IPC em conceito nacional, mas apenas em `ine.pt`;
o Eurostat só difunde os do IHPC. O IDF é, entre as fontes abertas, a única via
para uma estrutura de agregados residentes — e a única que desce ao quintil.

As duas estruturas divergem: **desvio médio absoluto de 1,9 p.p.** dentro da
alimentação, máximo de 4,9 p.p. (pão e cereais — 19,6 % no IHPC contra 14,6 % no
IDF). Na inflação alimentar nacional a escolha vale cerca de **0,3 p.p.**
(dezembro de 2025: 3,87 % com ponderação IDF, 3,56 % com IHPC). O separador de
metodologia quantifica isto em direto.

**Contrapartida a declarar.** O IDF é quinquenal, pelo que a sua estrutura
envelhece entre vagas e reintroduz, ao nível da classe, o viés de substituição
que se critica nos cabazes de composição fixa. É o IHPC, revisto todos os anos,
que serve de contrapeso. A próxima vaga do IDF é de 2026 e a atualização de
`src/config.py` terá de ser manual.

**Uma terceira base foi ponderada e rejeitada.** Estudou-se ler a evolução dos
ponderadores do IHPC deflacionados pelo índice de cada grupo, para isolar
alterações de quantidade consumida. Não avançou: o Documento Metodológico
estabelece que «a amostra e estrutura de ponderação referem-se sempre a dezembro
do ano n−1» e que os ponderadores **já incorporam** a variação de preços até esse
momento. Deflacioná-los pela média anual do índice desconta duas vezes parte do
efeito-preço e nenhuma vez outra parte. A direção pode manter-se; a magnitude não
é defensável.

### Evolução do Cabaz — DECO PROteste

Referência externa, não o indicador que a aplicação calcula (ver [«Despesa
alimentar» e não «cabaz»](#despesa-alimentar-e-não-cabaz)). A DECO PROteste
acompanha, desde janeiro de 2022, o preço absoluto de um cabaz de composição
fixa de 63 bens alimentares essenciais, recolhido semanalmente nas principais
cadeias com loja online.

**A DECO não tem API pública.** O artigo semanal que publica o valor embute os
gráficos como infografias Infogram, e cada uma expõe os seus dados numa
variável JavaScript da própria página do embed — não é um mecanismo
documentado nem estável, é o que existe. A recolha é por isso um passo
explícito, como a do Observatório:

```
python scripts/recolher_deco.py
```

Escreve `dados/deco_cabaz.csv` (série completa), `dados/deco_top10.csv` (os
produtos que mais aumentaram, em três janelas — última semana, desde janeiro,
desde 2022) e `dados/deco_meta.json`. **Convém correr o script quando a DECO
publicar nova semana** — a aplicação mostra sempre a data de referência e avisa
se o valor tiver mais de catorze dias.

**Fragilidade a declarar.** Os identificadores dos embeds Infogram descobrem-se
a cada execução, por correspondência entre o título de cada infografia e a
série pretendida; se a DECO mudar esses títulos ou deixar de usar o Infogram, a
recolha falha de forma visível, e não em silêncio. As três variações
apresentadas (semana anterior, desde janeiro, desde o início da série) são
calculadas a partir dos próprios pontos do gráfico, e não do texto do artigo,
precisamente para não dependerem de como a DECO redige a notícia nessa semana.

### Da produção ao consumo — Observatório de Preços

Todos os outros indicadores medem o que o consumidor paga ou quanto as famílias
gastam. Nenhum diz **onde na cadeia** nasceu a subida. O Observatório de Preços
Agroalimentar do GPP é a única fonte pública que segue o mesmo produto nas duas
pontas — produção e consumo.

**Os dados não vêm em direto.** O Observatório não tem API: a série exige uma
chamada por produto ao *endpoint* AJAX do sítio. Fazer 39 pedidos POST a um sítio
institucional sempre que a cache expira seria desproporcionado, e desnecessário —
os dados saem em períodos de quatro semanas. A recolha é por isso um passo
explícito:

```
python scripts/recolher_observatorio.py
```

Escreve `dados/observatorio.csv` e `dados/observatorio_meta.json`, com data de
extração. Qualquer número apresentado é reconstituível.
**Convém correr o script quando sair novo período** — a aplicação mostra sempre a
data da última recolha.

**A pasta `dados/` tem de ser enviada para o repositório.** É dela que saem o
Observatório e o cabaz da DECO, as duas fontes sem API, e o Streamlit Community
Cloud não corre os scripts de recolha: sem estes ficheiros, os dois separadores
respetivos ficam vazios na aplicação publicada. Correr o script e fazer *commit*
do resultado é o ciclo de atualização destas duas fontes.

> **Se os ficheiros de `dados/` não aparecerem no `git status`**, é o
> `.gitignore` da raiz do repositório: tem `Dados/`, escrito para as camadas do
> Medallion em `03_Dados/`, e no Windows a comparação de nomes é indiferente a
> maiúsculas, pelo que apanhava também esta pasta. O `.gitignore` desta
> aplicação anula-o com `!dados/`. Confirme com
> `git add -n -- dados`, que deve listar os cinco ficheiros.

Recolha de 20.08.2026: **3 125 observações, 39 produtos, 20 setores**, de
03.01.2022 a 15.06.2026. Só **17 dos 39** têm série de produção; para os restantes
o Observatório publica apenas preço ao consumidor, e a aplicação distingue-os em
vez de os omitir.

> Estes quatro números não são para atualizar à mão: há um teste,
> `test_o_readme_cita_a_recolha_em_vigor`, que os confronta com
> `dados/observatorio_meta.json` e falha quando divergem.

**Ressalva central, repetida na interface:** a diferença entre o preço no consumo
e o preço na produção **não é a margem de ninguém**. Inclui transporte,
transformação, embalagem, distribuição e IVA, e as duas fases podem referir-se a
formas diferentes do produto — peixe inteiro contra posta, animal vivo contra
peça desmanchada. Não é comparável entre produtos nem legível como lucro.

O caso da **pescada** é o que justifica o separador: preço na produção **−22,8 %**
e ao consumidor **+23,4 %**. Nenhum índice de preços mostra isto — para o IHPC é
apenas mais um produto que subiu.

### Acessibilidade alimentar — três limiares

«Conseguir pagar a comida» não é uma grandeza única. Consoante o limiar, Portugal
parece estar muito bem ou bastante mal, **com dados oficiais em ambos os casos**:

| Indicador | O que mede | Portugal | Fonte |
|---|---|---|---|
| Privação severa | Não pagar refeição com carne ou peixe de 2 em 2 dias | **1,9 %** | Eurostat `ilc_mdes03` |
| Não paga dieta saudável | Cabaz nutricionalmente adequado ao menor custo | **14,4 %** (1,5 M) | FAO SOFI 2026 |
| Peso no orçamento | Fatia do orçamento do 1.º quintil | **14,8 %** | INE, IDF 2022/2023 |

O primeiro é um limiar **muito baixo** — mede algo próximo da fome, e está em
mínimo de série. Apresentá-lo sozinho daria uma leitura indevidamente
tranquilizadora: sugeriria um problema de 2 % da população quando, por um limiar
nutricionalmente defensável, são 14 %. **A fome severa recuou; a impossibilidade
de comer bem não.**

Por isso os três partilham o mesmo bloco na interface, com a mesma nota de
leitura: **não há caminho na aplicação que mostre o de 1,9 % isolado**.

**O confronto com Espanha é o dado mais forte.** Custo de uma dieta saudável
praticamente igual — 4,30 contra 4,33 PPP$/dia —, mas 14,4 % da população
portuguesa não consegue pagá-la contra 9,3 % da espanhola. Com o mesmo preço e
resultados tão diferentes, a diferença está nos rendimentos e na sua
distribuição, não nos preços. É a demonstração mais limpa de que um indicador de
preços não é um indicador de acessibilidade.

**Ressalvas.** O custo da dieta saudável é um **mínimo normativo**, não despesa
observada, e vem em PPP$ — não é comparável com a âncora em euros. A privação
severa é auto-reportada, por amostragem, sem intervalos de confiança publicados.
O SOFI é o **único conjunto da aplicação que não vem de API**: está inscrito em
`src/config.py` e exige atualização manual a cada edição anual.

### O viés de substituição, medido

O separador **Histórico** compara três índices sobre as mesmas nove classes, todos com base em
dezembro de 2020 = 100: um **cabaz de composição fixa** (Laspeyres com ponderadores congelados),
um **Törnqvist** (índice superlativo, média dos ponderadores dos dois extremos de cada elo) e o
**IHPC oficial**.

Em dezembro de 2025: cabaz fixo **135,35**, Törnqvist **134,76**, IHPC oficial **134,88**.

**O viés de substituição existe, tem o sinal esperado e é residual** — 0,59 pontos em cinco anos,
cerca de **0,12 p.p. por ano**, sobre uma subida acumulada de 34,8 %. A razão é que a substituição
relevante acontece *dentro* das classes, não entre elas: trocar novilho por frango não altera o
peso da carne.

Duas leituras, de sentido oposto, e ambas necessárias:

- Quem ataque o índice oficial invocando viés de substituição **entre grupos de alimentos** está a
  invocar um efeito que está medido e é pequeno.
- Isso **não absolve** o cabaz de composição fixa. Um cabaz de 63 produtos com quantidades fixas
  falha na marca, no calibre, na embalagem e na insígnia — e nenhuma dessas dimensões é observável
  nestes dados. O efeito medido é o menor dos dois.

O Törnqvist aqui construído fica a 0,12 pontos do IHPC oficial, que é calculado por outra via —
é o melhor indício disponível de que a aproximação de ponderadores (declarada na interface) se
comporta.

### Cabaz por quintil de rendimento

O separador «Despesa e composição» apresenta a despesa alimentar por quintil de
rendimento equivalente, a partir dos quadros **Q.2.11.a** (euros) e **Q.2.11.b**
(estrutura) do IDF 2022/2023.

Os níveis são apresentados **tal como medidos pelo IDF** — não são reescalados
para a base de cálculo escolhida na barra lateral. Reescalá-los exigiria assumir
que o sub-reporte do inquérito é uniforme entre quintis, e nada o sustenta.

**Regra de apresentação, deliberada.** A taxa de inflação por quintil nunca
aparece sem a exposição orçamental ao lado, e ambas nunca aparecem sem o
agravamento em fração do orçamento. As três colunas dizem coisas diferentes e
qualquer uma, lida sozinha, engana:

| Leitura isolada | O que sugere | Porque é falso |
|---|---|---|
| Taxa de inflação por quintil | Neutralidade — a amplitude é de 0,18 p.p. e o valor mais alto está no 5.º quintil | A taxa não mede impacto; mede movimento de preços sobre cabazes diferentes |
| Agravamento em euros | Que o quintil mais rico é o mais afetado (9,67 € contra 6,91 €) | Gasta mais em comida em termos absolutos; diz-se pouco sobre esforço |
| Agravamento sobre o orçamento | — | É esta que mede esforço: 0,51 % no 1.º quintil contra 0,33 % no 5.º |

O efeito regressivo está na **exposição** — a alimentação absorve 14,8 % do
orçamento do 1.º quintil e 9,1 % do 5.º, um rácio de 1,63 — e não numa inflação
diferenciada. Esta distinção corrige a formulação da nota de enquadramento de
21.07.2026.

### Composição do agregado

A despesa média por agregado esconde uma diferença que importa para política: um
agregado de uma pessoa e um casal com dois filhos não gastam o mesmo. A aplicação
mostra explicitamente **a quantas pessoas corresponde o valor médio** (dimensão
média do agregado, `ilc_lvph01`, EU-SILC) e permite ajustar a composição por
número de adultos e de crianças.

O ajustamento usa **escalas de equivalência**, o instrumento oficial para comparar
agregados de composição diferente:

| Escala | Primeiro adulto | Adulto adicional | Criança (<14) |
|---|---|---|---|
| Per capita | 1,0 | 1,0 | 1,0 |
| OCDE original | 1,0 | 0,7 | 0,5 |
| OCDE modificada (norma UE) | 1,0 | 0,5 | 0,3 |

**A ressalva metodológica, agora medida.** Estas escalas foram construídas para o
consumo *total*, em que a partilha da habitação gera fortes economias de escala.
Na alimentação essas economias são mais fracas — não se partilha uma refeição
como se partilha um teto. Até aqui isto era uma ressalva qualitativa; o IDF
2022/2023 permite quantificá-la.

O teste restringe-se a agregados **sem crianças dependentes**, onde a escala é
mais limpa, e compara o rácio de despesa observado entre «2 ou mais adultos» e
«1 adulto» com o que cada escala prevê para a mesma composição:

| Escala | Rácio previsto | Desvio na alimentação | Desvio na despesa total |
|---|---|---|---|
| Per capita | 2,361 | −21,5 % | −36,5 % |
| **OCDE original** | **1,952** | **−5,0 %** | −23,3 % |
| OCDE modificada (norma UE) | 1,680 | **+10,3 %** | −10,9 % |

Rácio observado: **1,854** na alimentação, **1,498** na despesa total.

**O controlo é o que torna o teste convincente.** Na alimentação, a norma da UE
subestima o custo dos agregados maiores em ~10 %; na despesa total, para a qual
foi desenhada, o desvio **inverte-se** com magnitude semelhante. O problema não é
da escala em abstrato — é de a aplicar a alimentação.

A **OCDE original** é a mais próxima do observado, o que confirma empiricamente a
escolha por defeito da aplicação. Esse valor por defeito é **calculado** por
`escala_mais_proxima()`, não fixado à mão: se uma vaga futura do IDF alterar o
rácio observado, o valor por defeito acompanha. Quando o utilizador escolhe outra
escala, a barra lateral assinala-o.

A aplicação continua a apresentar **sempre um intervalo** entre a escala mais
restritiva e a mais generosa, em vez de um valor único de falsa precisão. O
resultado do teste é robusto no sinal e na ordem de grandeza, não no algarismo:
consoante a restrição do IDF que se privilegie, a subestimação fica entre 10 % e
13 %.

O separador inclui um comparador de composições típicas (pessoa só, casal,
monoparental com filhos, casal com filhos), com o intervalo de cada uma.

### Sobre séries privadas de cabazes

Séries de cabazes publicadas por entidades privadas são úteis para
compreender o debate público, mas **não são usadas como fonte desta aplicação**,
por três razões:

1. **Propriedade.** São produto de entidades privadas. Construir um instrumento
   público cujo número principal é o número de um privado levanta questões de
   propriedade intelectual e de dependência.
2. **Metodologia.** Assentam em composição fixa (índice de Laspeyres congelado),
   com viés de substituição conhecido — precisamente a limitação que a nota de
   enquadramento da UPE assinala.
3. **Posição institucional.** A nota recomenda que a Administração **não** crie
   nem valide um cabaz concorrente. Depender de um cabaz privado seria a outra
   face do mesmo problema.

A discussão analítica dessas séries mantém-se, e deve manter-se, na nota de
enquadramento: aí o objeto é explicar ao Gabinete o que cada instrumento mede.
Aqui o objeto é produzir números — e esses são oficiais.

### As duas vias de acesso

A aplicação tenta as vias por esta ordem:

1. **SDMX 2.1** — `…/sdmx/2.1/data/prc_hicp_minr/M.RCH_A.CP011.PT?format=SDMX-CSV`
   O filtro segue no próprio caminho do endereço, pelo que a seleção é
   obrigatoriamente feita no servidor do Eurostat. É a via preferida: evita
   respostas demasiado grandes.
2. **API Statistics** — `…/statistics/1.0/data/prc_hicp_minr?coicop18=CP011&geo=PT&…`
   Filtros por parâmetro, resposta em JSON-stat. Usada se a primeira falhar.

O separador *Fontes e método* mostra, em cada sessão, qual das vias foi
efetivamente utilizada.

### Parâmetros que **não** são dados oficiais

- **N.º de agregados familiares** — parâmetro do utilizador, usado para converter
  a despesa nacional em despesa por agregado.
- **Valor externo** — quando escolhido em alternativa à âncora oficial.
- **Taxas de IVA** — predefinidas e editáveis. Ver limitação 4.
- **Repercussão** — **calibrada**, não é hipótese de trabalho: 95 % por defeito,
  derivada da avaliação do Banco de Portugal ao «IVA zero» de 2023. Continua
  ajustável, e continua a ser o parâmetro decisivo. Ver limitação 7.

---

## Metodologia

### Decomposição da despesa alimentar

O valor total é repartido pelas nove classes na proporção dos ponderadores
oficiais. A cada classe aplica-se a respetiva variação homóloga.

Se uma classe vale hoje `Vᵢ` e cresceu `gᵢ` por cento, há um ano valia
`Vᵢ/(1+gᵢ)`. O acréscimo absoluto é:

```
contributoᵢ = Vᵢ · gᵢ / (1 + gᵢ)
```

A soma dos contributos iguala exatamente a variação do total — a decomposição é
aditiva, o que é verificado por teste automático.

### Simulação de IVA

Para cada classe, com taxa atual `t₀`, taxa do cenário `t₁` e repercussão `ρ`:

```
base        = valor / (1 + t₀)
efeito_mec  = base · (1 + t₁) − valor        (repercussão integral)
efeito_real = ρ · efeito_mec                 (o que chega ao consumidor)
margem      = (1 − ρ) · efeito_mec           (o que fica no operador)
```

**A repercussão é o parâmetro decisivo** — move o resultado 250 % entre 0 % e
100 %, mais do que todas as outras incertezas somadas.

Até 12.08.2026 o valor por defeito era **40 %**, declarado como parâmetro de
trabalho e fundado nas experiências francesa (2009, restauração) e sueca. Nenhuma
dessas avaliações é sobre Portugal nem sobre alimentação em retalho.

Portugal correu esta experiência. A Lei n.º 17/2023, de 14 de abril, isentou de
IVA 46 bens alimentares entre 18.04.2023 e 04.01.2024, e o **Banco de Portugal**
mediu a repercussão por quatro vias independentes. Como publica o efeito
**observado** e o efeito **mecânico** — a variação que haveria com transmissão
integral —, a repercussão extrai-se por divisão:

```
ρ = variação observada / variação mecânica    com  mecânica = (1+t₁)/(1+t₀) − 1
```

| Estimativa | Observado | Mecânico | ρ implícito |
|---|---|---|---|
| IHPC, dif-nas-dif vs. Espanha | −4,0 pp | −4,2 % | **95,2 %** |
| IHPC, dif-nas-dif vs. área do euro | −3,5 pp | −4,2 % | **83,3 %** |
| Preços online, cabaz abrangido | −6,0 % | −5,66 % | **106,0 %** |
| Preços online, óleos (eram 23 %) | −24,5 % | −18,70 % | **131,0 %** |

Nenhum destes ρ é citado: todos são calculados a partir dos dois números
publicados. A aritmética coincide com a do BdP — para os óleos, que estavam a
23 %, a fórmula dá −18,70 %, exatamente o valor que o BdP publica. Está travado
por teste.

A diluição das rubricas do IHPC (que incluem bens não abrangidos) atenua o
observado *e* o mecânico na mesma proporção, pelo que **o quociente sobrevive** —
é o que legitima a derivação apesar da granularidade que o próprio BdP assinala.

**O valor por defeito é 95 %**: a mais conservadora das duas estimativas com
contrafactual estatisticamente validado. A banda apresentada vai de 83,3 % a
100 %. Não se usa mais de 100 %, porque os valores acima refletem provavelmente
concorrência e salivência política, não repercussão pura.

**Ressalvas, que fazem parte da estimativa:** o BdP alerta para desvios-padrão
elevados; a medida foi temporária, taxativa e muito mediática, com pressões de
custo a montante já em queda; a janela avaliada é de quatro meses, sem evidência
sobre erosão a prazo; e a evidência robusta é sobre cortes a partir de 6 %.
Convém sempre testar a sensibilidade movendo o cursor.

Nota que a simulação torna visível: **a repercussão decide sobretudo quem fica com o
dinheiro** — o consumidor ou a margem do operador — e só marginalmente a receita
cessante. Numa isenção total esta é independente da repercussão; numa redução parcial
não é, porque uma repercussão menor mantém o preço final mais alto e, com ele, uma base
tributável maior (ver auditoria, ponto 2).

---

## Indicadores de esforço

A aplicação apresenta **dois** indicadores de esforço alimentar. Ambos são percentagens sobre
alimentação, mas têm denominadores diferentes e não se substituem.

### Coeficiente de Engel — despesa sobre despesa

```
Engel = despesa alimentar nacional ÷ consumo total das famílias
```

Mede **como se reparte o orçamento de consumo**: de cada 100 € que as famílias gastam em tudo,
quantos vão para comida. **Não envolve salários nem rendimentos.**

Chama-se assim por Ernst Engel, que em 1857 formulou a regularidade que ainda hoje se verifica:
quanto menor o rendimento, maior a fatia do orçamento gasta em comida. É comparável entre
países sem conversão cambial, por ser um rácio.

É um **agregado macroeconómico nacional** e, por isso, **não responde à composição do agregado**
escolhida na barra lateral. Não existe versão «por agregado» deste indicador nas Contas
Nacionais.

### Esforço do agregado — despesa sobre rendimento

```
rendimento do agregado = rendimento equivalente × unidades de consumo ÷ 12
esforço                = despesa alimentar do agregado ÷ rendimento do agregado
```

Mede **quanto do rendimento é absorvido pela comida**, e **responde à composição** escolhida.

Usa por defeito o rendimento **médio** equivalente, não o mediano: a despesa alimentar desta
aplicação deriva de um agregado nacional dividido pelo número de agregados — ou seja, é uma
**média**. Combiná-la com um rendimento mediano misturaria duas medidas de tendência central
diferentes e inflacionaria o rácio. A mediana continua disponível, com aviso.

### Quem come e quem aufere não são o mesmo conjunto

A escala de equivalência atribui peso de adulto a **todas as pessoas com 14 ou mais anos** — e
com razão, porque a partir dessa idade come-se como adulto. Mas o rendimento é outra coisa: um
jovem de 15 ou 17 anos conta na despesa e não conta na receita.

Por isso a aplicação separa duas contagens:

| Campo | Determina |
|---|---|
| **Pessoas com 14+ anos** | A despesa alimentar, via escala de equivalência |
| **Quantas auferem rendimento** | O denominador do esforço |

Um agregado de dois pais e dois adolescentes tem **quatro pessoas com peso alimentar de adulto e
dois rendimentos**. É a composição em que o esforço alimentar é mais elevado, e precisamente a
que os indicadores médios menos revelam — a aplicação assinala-a quando ocorre.

O valor por defeito de quem aufere rendimento é **dois no máximo**, não o total de pessoas com
14+ anos: assumir que todos os adolescentes auferem seria irrealista e subestimaria o esforço.

### As três fontes de rendimento — e a distinção bruto/líquido

| Fonte | Conjunto | O que é | Natureza |
|---|---|---|---|
| Rendimento das famílias | `ilc_di03` | Rendimento do agregado, todas as fontes, deduzidos impostos e contribuições | **Líquido** |
| Salário médio | `nama_10_a10` ÷ `nama_10_a10_e` | Massa salarial das Contas Nacionais dividida pelos trabalhadores por conta de outrem | **Bruto** |
| Salário mínimo | `earn_mw_cur` | Valor legal mensal, tal como fixado por diploma | **Bruto** |

**A distinção não é um detalhe.** O salário mínimo não desconta a contribuição do trabalhador
nem o imposto retido, nem inclui prestações familiares. O rendimento efetivamente disponível de
quem aufere o mínimo é **inferior** ao valor publicado — logo o esforço alimentar real é
**superior** ao que o rácio indica. A aplicação assinala as duas naturezas com cores distintas
e adverte que não são comparáveis entre si.

### Face aos salários

Além do rendimento do EU-SILC, o esforço é comparado com dois cenários de salários. Um único
controlo — **adultos com rendimento** — evita a multiplicação de combinações: as crianças nunca
entram nessa contagem, porque não auferem rendimento.

| Referência | Natureza | Nota |
|---|---|---|
| Rendimento das famílias (EU-SILC) | Líquido | Inclui todas as fontes de rendimento e prestações |
| N × salário médio | Líquido | Trabalhador médio, após imposto e contribuições |
| N × salário mínimo | **Bruto** | Valor legal, antes de descontos |

**Bruto e líquido não se misturam.** O salário mínimo é um valor legal bruto: não desconta
contribuições nem imposto, nem inclui prestações familiares. O esforço calculado sobre ele
subestima a pressão real, porque o rendimento efetivamente disponível é inferior. A aplicação
assinala a natureza de cada referência com cor distinta.

A assimetria que este bloco torna visível: **um casal com dois filhos e um só salário continua
a ter um salário, mas quatro pessoas a alimentar.** É essa desproporção que faz o esforço
disparar — e que nenhum indicador nacional médio revela.

### Propriedade a conhecer

A despesa usa a escala escolhida pelo utilizador; o rendimento tem de usar a OCDE modificada,
porque é essa que o EU-SILC aplica. **Se as duas coincidirem, o esforço é constante** seja qual
for a composição — ambos os lados escalam de forma idêntica. A subida do esforço com o número
de pessoas resulta, portanto, da **diferença entre as escalas**.

Isso não invalida a leitura — a alimentação tem economias de escala genuinamente mais fracas do
que o consumo total —, mas a magnitude depende da escala. Leia a direção como robusta e o valor
exato como condicional. Há um teste automático que fixa esta propriedade.

---

## Auditoria de 27 de julho de 2026

O modelo foi submetido a auditoria — verificação numérica das fórmulas, coerência económica e
robustez do código. Foram encontrados **três problemas**, todos corrigidos ou declarados.

### 1 · Incompatibilidade de bases no indicador de esforço · **grave**

O numerador (despesa alimentar) vem das **Contas Nacionais**; o denominador (rendimento) vem do
**EU-SILC**. São universos distintos: as Contas Nacionais incluem rendas imputadas, consumo de
instituições sem fins lucrativos e consumo no território, incluindo o de não residentes; o
EU-SILC mede rendimento monetário líquido dos residentes.

O consumo por agregado das Contas Nacionais é estruturalmente **cerca de 1,8 vezes** o
rendimento do EU-SILC — um rácio que implicaria taxa de poupança fortemente negativa. Combinar
as duas bases **sobrestima o esforço**.

*Sinal de deteção:* se o esforço exceder o coeficiente de Engel para o mesmo agregado, é este o
motivo — o esforço sobre o rendimento deveria ser inferior ao peso no consumo, porque as
famílias poupam.

**Estado:** declarado na aplicação com aviso destacado; o esforço passa a ser apresentado como
**limite superior**, e não como estimativa. A correção exigiria despesa e rendimento da mesma
fonte, o que só o IDEF/INE permite.

### 2 · Afirmação incorreta sobre a receita de IVA · **corrigido**

A aplicação afirmava que a receita cessante é a mesma qualquer que seja a repercussão. **Só é
verdade numa isenção total.** Numa redução parcial, uma repercussão menor mantém o preço final
mais alto e portanto a base tributável maior: o Estado recupera parte do que o operador retém.

Verificação numérica (106 €, de 23 % para 6 %): a receita cessante varia entre −13,82 € e
−14,65 € consoante a repercussão vá de 0 % a 100 % — cerca de 6 % de amplitude.

**Estado:** texto corrigido e propriedade fixada em teste automático.

### 3 · Viés na modelação do agregado médio · **quantificado**

O agregado médio nacional é modelado como composto apenas por adultos, porque a dimensão média é
publicada sem decomposição etária. Como o agregado médio real inclui menores, que pesam menos na
escala, o denominador fica sobrestimado em **4 a 5 %** e todos os valores por agregado saem
subestimados na mesma proporção.

**Estado:** quantificado e declarado. O viés é **proporcional** — igual para todas as
composições —, pelo que não contamina as comparações entre elas. Propriedade fixada em teste.

### Verificações que passaram

| Teste | Resultado |
|---|---|
| Aditividade da decomposição (500 combinações aleatórias) | 0 falhas |
| Ordem de grandeza da âncora face ao IDEF | Plausível |
| Robustez numérica (valores nulos, taxas iguais, repercussão 0 e 1) | Sem exceções |
| Agregados extremos (10 adultos, 10 menores) | Sem valores não finitos |
| Divisão por zero em ponderadores, rendimento e escalas | Protegida |

## «Despesa alimentar» e não «cabaz»

Os dois termos designam objetos diferentes. Esta aplicação usa apenas o primeiro para o que
mede; «cabaz» aparece só quando se fala dos cabazes **de outros**.

| | **Cabaz** | **Despesa alimentar** |
|---|---|---|
| O que é | Lista de produtos com quantidades definidas | Quanto uma família gasta em comida |
| Como se obtém | Somando os preços dos artigos da lista | Repartindo despesa efetiva por grupos |
| Unidade natural | Um ato de compra | Um mês |
| Quantidades | Fixas e conhecidas | Não existem — só euros |

A aplicação **não tem cabaz nenhum**: não conhece quantidades, não observa preços de produtos,
não tem lista de artigos.

### Os seis instrumentos, na interface

Não existe um cabaz alimentar oficial em Portugal. Existem pelo menos **seis** instrumentos com
naturezas diferentes — o cabaz de 63 produtos da DECO, o IPC/IHPC, o índice de supermercados
online da DECO, o Observatório de Preços Agroalimentar do GPP, o cabaz de apoio alimentar do
PO APMC e o cabaz «IVA zero» de 2023–24 — que o debate público tende a fundir num só.

O quadro que os distingue está no separador **«Metodologia e fontes»**, aberto por defeito, e
inclui o posicionamento explícito desta ferramenta: não é um sétimo cabaz, é um instrumento de
repartição e enquadramento. Responde a «quanto pesa a alimentação no orçamento de quem, e quanto
disso é aumento de preço» — não a «quanto custa este cabaz hoje».

Entrega a linha de trabalho #1 da nota de enquadramento («O que é (e o que não é) o cabaz»), que
até aqui existia apenas em prosa neste ficheiro e estava ausente da interface — onde faz falta,
porque é a interface que vai ao Gabinete.

### Coerência do nome do repositório

A aplicação chama-se **despesa alimentar**. Se o repositório e o endereço público ainda
disserem «cabaz», há incoerência — e vale a pena resolvê-la, porque o nome do endereço é a
primeira coisa que quem recebe a ligação vê.

**Renomear o repositório**

1. GitHub → repositório → **Settings** → separador **General**
2. Campo **Repository name** → escrever `despesa-alimentar` → **Rename**

O GitHub cria automaticamente um encaminhamento do nome antigo para o novo, pelo que ligações
já enviadas continuam a funcionar. Quem tiver o repositório clonado deve atualizar a origem:

```bash
git remote set-url origin https://github.com/<utilizador>/despesa-alimentar.git
```

**Reapontar o Streamlit**

O Streamlit guarda a referência ao repositório e **não acompanha a mudança de nome**. Depois de
renomear:

1. `share.streamlit.io` → ⋮ na aplicação → **Delete**
2. **Create app** → repositório `despesa-alimentar`, branch `main`, ficheiro `app.py`
3. Em **App URL**, definir o subdomínio — por exemplo `sggov-despesa-alimentar`

Demora cerca de três minutos e a aplicação volta ao ar. **O endereço antigo deixa de
funcionar**, pelo que convém avisar quem já o tenha.

**Se preferir não mexer**, a alternativa coerente é assumir o nome antigo apenas como
identificador técnico do repositório, e garantir que **nada no que é visível ao utilizador**
— título, separadores, textos, ficheiros exportados — usa a palavra «cabaz» para designar
este indicador. É o que a aplicação já faz.

## Limitações a declarar

Qualquer utilização destes resultados em suporte à decisão ou em comunicação
deve fazer-se acompanhar destas ressalvas:

1. **A decomposição não é observação.** É uma imputação de um valor total por
   ponderadores oficiais. Não substitui a recolha de preços produto a produto,
   que nenhuma fonte pública disponibiliza por interface automática.
2. **Ponderadores de consumo médio.** Os ponderadores do IHPC refletem a
   estrutura de despesa média das famílias — não a composição de nenhum cabaz
   específico, nem a de um agregado concreto.
3. **A âncora parte de uma média nacional.** A despesa por agregado resulta de
   dividir um agregado macroeconómico pelo número de agregados. O ajustamento por
   composição usa escalas de equivalência aplicadas a essa média — não substitui
   uma observação direta por tipo de agregado, que exigiria o IDEF/INE. Não
   distingue escalão de rendimento nem região.
4. **As escalas de equivalência são aproximações.** Foram construídas para o
   consumo total e subestimam o custo alimentar de agregados maiores; o agregado
   médio é modelado como composto por adultos, porque a dimensão média é publicada
   sem decomposição etária. Daí a apresentação em intervalo.
5. **Desfasamento das Contas Nacionais.** A âncora assenta num ano com cerca de
   dois anos de desfasamento, atualizado por índice de preços — capta a variação
   de preços, não eventuais alterações de comportamento de consumo desde então.
6. **A correspondência COICOP → taxa de IVA é aproximada.** O Código do IVA
   classifica por produto (Lista I), não por classe COICOP; uma mesma classe pode
   conter produtos a taxas diferentes.
7. **A repercussão está calibrada, mas continua a ser o parâmetro decisivo.** Desde
   12.08.2026 parte de **95 %**, derivado da avaliação do Banco de Portugal ao «IVA
   zero» de 2023 — a medida idêntica, no mesmo país e no retalho alimentar. Antes
   partia de 40 %, um valor de trabalho fundado em França 2009 e na Suécia, que
   fazia a aplicação subestimar a poupança por um fator de **2,4**. Mesmo calibrado,
   é o número que mais move o resultado: qualquer valor é condicional a ele e deve
   ser apresentado como intervalo, nunca como valor único. A estimativa vem de uma
   medida **temporária e mediática**, avaliada ao longo de quatro meses — uma
   alteração permanente e discreta pode repercutir-se menos.
8. **Preço de prateleira não é preço pago — e o critério é preciso.** O Documento
   Metodológico do IPC (INE, 2023) determina que os descontos entram no índice
   **«desde que de aplicação generalizada aos consumidores»** (citação literal,
   pp. 26 e 40). Uma promoção aberta a qualquer cliente é captada; um desconto
   condicional — cartão de fidelização, cupão, talão — é excluído **por regra**,
   não por falha de recolha. *A arrumação dos tipos concretos de desconto é
   leitura nossa: o documento fixa o critério, não classifica casos.* O desvio
   entre preço registado e preço pago é o que resulta dos descontos condicionais e
   tende a crescer com a difusão dos programas de fidelização, pelo que o índice
   pode sobrestimar ligeiramente a aceleração do preço efetivamente pago. Só dados
   de transação (e-fatura, *scanner data*) o mediriam — e o IPC **não usa scanner
   data**: a recolha automatizada é por *web scraping* em cadeias de implantação
   nacional.
9. **A extrapolação agregada é ilustrativa.** A multiplicação pelo número de
   agregados serve para dimensionar ordens de grandeza. **Não é uma estimativa de
   custo orçamental** — essa exigiria a base tributável real por taxa, via Contas
   Nacionais, IDEF ou dados da Autoridade Tributária.

---

## Como a aplicação se mantém atualizada

**Não há dados gravados no código.** Em cada arranque, a aplicação pede ao Eurostat as séries de
que precisa e usa **a observação mais recente de cada uma**.

**Seleção do valor mais recente.** Para cada série, as observações são ordenadas por período e
retém-se a última. Funciona para qualquer periodicidade — mensal (`2026-06`), semestral
(`2026S1`) ou anual (`2026`) — porque a codificação de períodos do Eurostat é ordenável. Quando o
Eurostat publicar um mês novo, a aplicação passa a usá-lo **sem qualquer alteração ao código**.

**Janela de pedido.** As séries anuais e semestrais são pedidas com **oito anos** de margem
(constante `JANELA` em `app.py`). É folgado de propósito: se uma publicação atrasar, continua a
haver observações no intervalo. As mensais usam janelas mais curtas, por serem densas.

**Cache de seis horas.** Evita repetir pedidos desnecessários — as séries mudam no máximo uma vez
por mês. O botão **Recarregar do Eurostat** limpa a cache e força um pedido novo.

**Período visível.** Cada indicador mostra o seu período de referência, para que não se confunda
a data da consulta com a data do dado.

## Calendário de divulgação

Saber quando os dados mudam evita conclusões precipitadas sobre variações que são apenas
atualizações de fonte.

| Dado | Publicação | Desfasamento |
|---|---|---|
| Estimativa rápida (só agregados) | Último dia útil do mês de referência | Semanas |
| **Índice completo, com todas as classes** | **Cerca do dia 17 do mês seguinte** | ~2 semanas |
| Ponderadores | Com os dados de janeiro, em fevereiro | Anual |
| Contas Nacionais (âncora) | — | ~2 anos |
| EU-SILC (rendimento, dimensão) | — | ~1 ano |
| Paridades de poder de compra | Junho do ano seguinte | ~1 ano |
| Salário mínimo | Janeiro e julho | Semestral |

A aplicação usa sempre o mês mais recente disponível e indica-o no topo. Os dados ficam em
*cache* durante 6 horas; o botão **Recarregar do Eurostat** força a atualização.

### Alterações metodológicas de fevereiro de 2026

A partir dos dados de janeiro de 2026, o índice passou a ser compilado segundo a **ECOICOP
versão 2**, alinhada com a COICOP 2018, e o período de referência do índice passou para
**2025 = 100**. As séries com a classificação anterior foram arquivadas.

A aplicação já prefere a base mais recente disponível, com recuo ordenado para as anteriores.
Se em algum momento as classes `CP011x` deixarem de responder, é nesta alteração que se deve
olhar primeiro.

## Manutenção

**Periodicidade dos dados.** O Eurostat publica o IHPC mensalmente, cerca de duas
a três semanas após o fim do mês de referência. Os ponderadores são revistos
anualmente. A aplicação guarda os dados em *cache* durante 6 horas; o botão
**Recarregar do Eurostat**, na barra lateral, força a atualização.

**Alterar classes, países ou taxas por defeito.** Editar `src/config.py`. As
listas `CLASSES` e `PAISES` controlam tudo o que aparece na interface.

**Se o Eurostat alterar a nomenclatura.** Está prevista a transição para a
ECOICOP versão 2. Se os códigos `CP011x` deixarem de responder, basta atualizar o
campo `cod` em `CLASSES`; o resto da aplicação não precisa de alterações.

**Antes de qualquer alteração aos cálculos**, correr `python -m pytest tests/ -v`.
Os 176 testes cobrem a aditividade da decomposição e a aritmética do IVA, incluindo
casos-limite conhecidos.

---

## Resolução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| «Não foi possível obter os dados» na nuvem | Serviço do Eurostat indisponível | Aguardar e usar **Recarregar**; confirmar em `ec.europa.eu/eurostat` |
| O mesmo erro em execução local | Rede institucional a bloquear a saída | Pedir à Transformação Digital a autorização de `ec.europa.eu`, ou usar a versão alojada |
| Aplicação demora ~30 s a abrir | Reativação após suspensão por inatividade | Normal no plano gratuito |
| Tema sem as cores institucionais | Pasta `.streamlit/` não foi carregada | Criar `.streamlit/config.toml` diretamente no GitHub |
| `ModuleNotFoundError` na publicação | Dependência em falta | Confirmar que `requirements.txt` está na raiz do repositório |
| Tabelas vazias mas sem erro | Códigos COICOP alterados na fonte | Verificar `src/config.py` face à nomenclatura em vigor |

Para diagnóstico detalhado, o separador **Fontes e método** mostra o registo das
ligações da sessão: que pedidos foram feitos, por que via e quantas observações
devolveram.

---

## Créditos e estatuto

Desenvolvido pela **Unidade de Pesquisa e Estatísticas (UPE)**, Direção de
Serviços de Suporte à Decisão, Secretaria-Geral do Governo.

Dados: **Eurostat** — reutilização livre com indicação da fonte, nos termos da
política de reutilização da Comissão Europeia.

> **Estatuto do produto.** Ferramenta de trabalho interno. Não constitui posição
> oficial da Secretaria-Geral do Governo. Os valores carecem de reconfirmação
> junto das fontes primárias antes de qualquer utilização em suporte à decisão
> política ou em comunicação pública.
