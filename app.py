"""
Despesa alimentar, ferramenta de análise
UPE · DSSD · Secretaria-Geral do Governo

Executar localmente:   streamlit run app.py
"""

from __future__ import annotations

import re
import unicodedata
from contextlib import contextmanager
from datetime import date, datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pathlib import Path

from src import deco, eurostat, observatorio
from src.calculos import (ESCALAS, agregados_do_ano, cabaz_quintis,
                          comparar_ponderadores, composicao_iva,
                          composicao_quintis, decompor, despesa_do_agregado,
                          escala_mais_proxima, frescura_das_series,
                          frescura_do_observatorio,
                          idade_fonte, indices_comparados,
                          intervalo_agregado, intervalo_engel,
                          pontos_de_rutura_das_escalas,
                          efeito_mecanico_pct, estimativas_repercussao,
                          repercussao_banda,
                          resumo_composicao_iva, resumo_decomposicao, resumo_iva,
                          sensibilidade_escalas, simular_iva, taxas_efetivas,
                          testar_escalas, unidades_equivalentes)
from src.config import (AGREGADOS, AGREGADOS_ANO, AGREGADOS_CENSOS, AGREGADOS_FONTE,
                        AGREGADOS_NOTA, AGREGADOS_NOTA_FONTE,
                        BASE_POR_DEFEITO, BASES_ANCORA, COD_AGREGADOS,
                        DIMENSAO_RECUO, DIMENSAO_RECUO_FONTE,
                        ESCALAS_TESTE_COMPOSICAO, ESCALAS_TESTE_FONTE,
                        ESCALAS_TESTE_INTERVALO, ESCALAS_TESTE_RACIO,
                        IVA_COMPONENTES, IVA_COMPONENTES_FONTE,
                        AT_FICHAS, PRINCIPIO_LISTA_TAXATIVA,
                        IVA_MAPA, IVA_MAPA_FONTE, IVA_SUBCLASSES,
                        IVA_ZERO_AFETACAO_ORCAMENTAL, IVA_ZERO_INFLACAO_QUINTIL,
                        IVA_ZERO_CITACAO, IVA_ZERO_QUINTIS_FONTE,
                        IVA_ZERO_INICIO, IVA_ZERO_N_ALIMENTOS,
                        REPERCUSSAO_BANDA, REPERCUSSAO_FONTE, REPERCUSSAO_PADRAO,
                        IDF_ALIMENTAR_ANUAL,
                        IDF_JANELA_FONTE, IDF_JANELA_RECOLHA,
                        IDF_PESO_ALIMENTAR, IDF_QUINTIS,
                        LIMITE_ANOS_SOFI, LIMITE_DIAS_DECO, LIMITE_DIAS_OBSERVATORIO,
                        LIMITES_FRESCURA,
                        SOFI_CUSTO, SOFI_EDICAO, SOFI_FONTE, SOFI_INCAPACIDADE,
                        SOFI_MILHOES,
                        ANO_BASE_VIES,
                        AZUL, CINZENTO, CLASSES, CLASSES_FONTE, CODIGOS,
                        COICOP_ALIMENTAR, DOURADO, ORGANISMO,
                        ICONES_CLASSE, SETORES_OBSERVATORIO,
                        PAISES, PAISES_POR_DEFEITO, POR_CODIGO, RODAPE,
                        UNIDADE, VERDE, VERMELHO,
                        euro, mes_extenso, mes_homologo, mes_pt, milhoes,
                        numero, percentagem, pontos)

LOGO = ""
try:
    LOGO = (Path(__file__).parent / "src" / "logo_b64.txt").read_text().strip()
except Exception:                                          # noqa: BLE001
    LOGO = ""

st.set_page_config(
    page_title="Despesa alimentar, UPE/SGGov",
    # O favicon é o símbolo da SGGov, não um emoji. Se o ficheiro do logótipo
    # não estiver disponível, o Streamlit fica com o seu ícone por omissão.
    page_icon=(f"data:image/png;base64,{LOGO}" if LOGO else None),
    layout="wide",
    # Sem `initial_sidebar_state`: a aplicação deixou de ter barra lateral a
    # 01.09.2026, e o Streamlit não a desenha se nada lhe for escrito.
)

# ==========================================================================
# Sistema de design institucional
# ==========================================================================
# Camada exclusivamente visual. Os tokens abaixo são a **única** fonte de
# valores de estilo da aplicação: cores, tipografia, espaçamento e raios estão
# aqui e não espalhados pelos componentes. As cores institucionais vêm de
# `src/config.py` (Manual de Normas Gráficas da SGGov) e entram como variáveis
# CSS para que HTML e gráficos usem exatamente os mesmos valores.
#
# Regra de utilização da cor: verde = identidade/Portugal/positivo; azul =
# informação, análise e comparação; dourado = destaque editorial e valores
# brutos; vermelho = alerta, erro e agravamento. Nenhuma cor é decorativa.
FUNDO = "#F8F9FA"
SUPERFICIE = "#FFFFFF"
TEXTO = "#171715"
TEXTO_2 = "#4A4A48"
TEXTO_3 = "#6B7280"
BORDA = "#E2E8F0"
BORDA_2 = "#CBD5E1"
GRELHA = "#EEF1F4"
NEUTRO = "#B7C2CE"
TIPO = "Lexend, 'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', sans-serif"

# Paleta categórica das nove classes COICOP. Até 31.08.2026 estava escrita aqui,
# a substituir na apresentação a paleta do `config`, e as duas divergiam em sete
# das nove classes: o `config` dizia uma cor, o ecrã mostrava outra. Passou a
# haver uma só, no `config`, e é esta função que a serve a toda a aplicação.
# Os tons são contidos e nenhum deles é o vermelho de alerta, que numa paleta
# categórica sinalizaria um problema onde só há uma categoria. A associação ao
# tipo de produto mantém-se (peixe azul, hortícolas verde, óleos dourado) para
# que a leitura do donut continue intuitiva.
def cor_classe(codigo: str, recuo: str = NEUTRO) -> str:
    """Cor de apresentação de uma classe COICOP."""
    classe = POR_CODIGO.get(str(codigo))
    return classe["cor"] if classe else recuo


def icone_classe(codigo: str, cor: str | None = None, tamanho: int = 14) -> str:
    """
    SVG de um grupo COICOP, já com a cor da classe.

    Devolve cadeia vazia se o código não tiver símbolo, para que quem o insere
    não tenha de saber quais têm: um grupo sem ícone perde a sinalização, não
    parte o cartão.
    """
    return _svg(ICONES_CLASSE.get(str(codigo)), cor or cor_classe(codigo), tamanho)


def icone_setor(setor: str, tamanho: int = 14) -> str:
    """SVG de um setor do Observatório, com a cor herdada do seu grupo COICOP."""
    s = SETORES_OBSERVATORIO.get(str(setor))
    if not s:
        return ""
    return _svg(s["icone"], cor_classe(s["grupo"]), tamanho)


def _svg(caminho: str | None, cor: str, tamanho: int) -> str:
    """
    Envolve um caminho do `config` num SVG em linha.

    Traço e nunca preenchimento, terminações redondas, e `currentColor` não
    serve aqui porque o SVG vai dentro de HTML solto onde a cor herdada é a do
    texto: a cor entra explícita.
    """
    if not caminho:
        return ""
    return (f'<svg class="sg-icone" width="{tamanho}" height="{tamanho}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{cor}" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'<path d="{caminho}"/></svg>')


# Houve aqui uma `etiqueta_classe`, que punha o nome do grupo numa pastilha com
# o fundo a 12% da cor, e a `tinta` que calculava esse fundo. Saíram a pedido da
# Inês (31.08.2026): o único sítio onde a etiqueta era usada era a linha do
# produto no Observatório, e ali o nome da classe COICOP dizia em texto longo o
# que a cor do símbolo já diz. Sem utilizador, era código a envelhecer sozinho.
# Se um dia o fundo ténue for preciso nas tabelas, volta com a forma que essa
# necessidade lhe der.


st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700&display=swap');

:root {{
  --sg-verde: {VERDE}; --sg-azul: {AZUL}; --sg-dourado: {DOURADO};
  --sg-vermelho: {VERMELHO};
  --sg-fundo: {FUNDO}; --sg-superficie: {SUPERFICIE};
  --sg-texto: {TEXTO}; --sg-texto-2: {TEXTO_2}; --sg-texto-3: {TEXTO_3};
  --sg-borda: {BORDA}; --sg-borda-2: {BORDA_2}; --sg-grelha: {GRELHA};
  /* Contorno de contentor. É mais claro do que `--sg-borda`, que fica
     reservada aos filetes que **separam** (blocos, secções, rodapé). A
     distinção existe porque uma caixa não precisa de se afirmar para conter:
     precisa apenas de não se confundir com o fundo. */
  --sg-borda-1: #EBEFF4;
  --sg-tipo: {TIPO};
  --sg-raio: 2px;
  /* Escada de espaçamento. Nenhum componente inventa margens próprias:
     --sg-e5 separa blocos analíticos, --sg-e4 secções dentro do bloco,
     --sg-e2 um título do seu conteúdo, --sg-e3 um gráfico da sua nota. */
  --sg-e1: .5rem; --sg-e2: 1.15rem; --sg-e3: 1.6rem;
  --sg-e4: 2.25rem; --sg-e5: 3rem;
}}

/* ---------- tipografia e superfícies ---------------------------------- */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] :is(p, li, h1, h2, h3, h4, h5, h6,
                                         strong, em, a, td, th, blockquote),
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"],
[data-testid="stMetricDelta"], [data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p, [data-testid="stDataFrame"],
[data-testid="stExpander"] summary,
/* O rótulo do separador é um contentor de markdown que assume o `bodyFont` do
   tema (Source Sans) em vez de herdar: sem esta entrada saía fora da Lexend. */
.stTabs [data-testid="stTab"],
.stTabs [data-testid="stTab"] [data-testid="stMarkdownContainer"],
button, input, select, textarea {{
  font-family: var(--sg-tipo);
  font-feature-settings: "tnum" 0;
}}

[data-testid="stAppViewContainer"], .stApp {{ background: var(--sg-fundo); }}
[data-testid="stHeader"] {{ background: transparent; }}
/* Largura útil de ~1288 px em ecrã largo (1376 menos as duas margens de
   2,75rem). Acima disso as linhas de texto ficam longas de mais; abaixo, os
   gráficos e os quadros perdem o espaço de que precisam para se lerem. */
[data-testid="stMainBlockContainer"] {{
  padding: 2.25rem 2.75rem 1rem; max-width: 1376px;
}}
@media (max-width: 1200px) {{
  [data-testid="stMainBlockContainer"] {{ padding: 2rem 2rem 1rem; }}
}}
@media (max-width: 900px) {{
  [data-testid="stMainBlockContainer"] {{ padding: 1.75rem 1.15rem 1rem; }}
}}

/* Números tabulares em tudo o que é valor, para que as colunas alinhem. */
[data-testid="stMetricValue"], [data-testid="stMetricDelta"],
.sg-cartao__valor, .sg-cartao__contrib,
[data-testid="stMarkdownContainer"] td {{ font-variant-numeric: tabular-nums; }}

/* ---------- texto corrente -------------------------------------------- */
/* O `:not([class*="sg-"])` separa o markdown escrito pelo Streamlit dos
   componentes desta aplicação, e **não é cosmético**.
   `[data-testid="stMarkdownContainer"] :is(p, li)` tem especificidade (0,1,1)
   porque `:is()` assume a do seu argumento mais específico; `.sg-hero__v` e
   `.sg-cabecalho__inst` têm (0,1,0). A regra genérica ganhava, portanto, a
   **todos** os nossos <p> e <h*>, que vivem dentro do mesmo contentor de
   markdown. Consequências que se viam no ecrã: o cabeçalho institucional saía
   a cinzento-escuro sobre o verde, em vez de branco, e o valor de capa saía ao
   corpo do texto corrido, em vez de dominar a página. As declarações estavam
   escritas; nunca chegavam a aplicar-se. */
[data-testid="stMarkdownContainer"] :is(p, li):not([class*="sg-"]) {{
  font-size: .8125rem; line-height: 1.7; color: var(--sg-texto-2);
}}
[data-testid="stMarkdownContainer"] strong {{ color: var(--sg-texto); font-weight: 600; }}
[data-testid="stMarkdownContainer"] a {{ color: var(--sg-azul); text-decoration: none;
  border-bottom: 1px solid rgba(43,86,131,.3); }}
[data-testid="stMarkdownContainer"] a:hover {{ border-bottom-color: var(--sg-azul); }}
[data-testid="stCaptionContainer"] p {{
  font-size: .75rem; line-height: 1.58; color: var(--sg-texto-3);
}}

/* Hierarquia de títulos: quatro degraus, sem tamanhos intermédios. Mesma
   ressalva de especificidade do bloco acima. */
[data-testid="stMarkdownContainer"] h1:not([class*="sg-"]) {{ font-size: 1.75rem;
  font-weight: 600; letter-spacing: -.025em; color: var(--sg-texto); margin: 0 0 .5rem; }}
[data-testid="stMarkdownContainer"] h2:not([class*="sg-"]) {{ font-size: 1.3125rem;
  font-weight: 600; letter-spacing: -.015em; color: var(--sg-texto); margin: 2.5rem 0 .5rem; }}
[data-testid="stMarkdownContainer"] :is(h3, h4):not([class*="sg-"]) {{
  font-size: 1.125rem; font-weight: 600;
  letter-spacing: -.01em; color: var(--sg-texto); margin: 2.25rem 0 .4rem; }}
[data-testid="stMarkdownContainer"] :is(h5, h6):not([class*="sg-"]) {{
  font-size: .9375rem; font-weight: 600;
  letter-spacing: .01em; color: var(--sg-texto); margin: 1.75rem 0 .35rem;
  text-transform: none; }}

/* Tabelas de markdown com aspeto de quadro estatístico, e que não rebentam
   a largura da página em ecrã estreito. Sem filetes verticais, cabeçalho
   discreto, e ar suficiente entre linhas para não parecerem folha de cálculo. */
[data-testid="stMarkdownContainer"] table {{
  display: block; width: fit-content; max-width: 100%; overflow-x: auto;
  border-collapse: collapse; font-size: .875rem; margin: 1rem 0 1.1rem;
}}
[data-testid="stMarkdownContainer"] th {{
  text-align: left; font-size: .6875rem; font-weight: 600; letter-spacing: .08em;
  text-transform: uppercase; color: var(--sg-texto-3); background: transparent;
  border: 0; border-bottom: 1px solid var(--sg-borda); padding: .6rem .95rem .5rem;
}}
[data-testid="stMarkdownContainer"] td {{
  border: 0; border-bottom: 1px solid var(--sg-grelha);
  padding: .68rem .95rem; color: var(--sg-texto-2); vertical-align: top;
  line-height: 1.6;
}}
/* Primeira coluna mais forte: é a que identifica a linha. */
[data-testid="stMarkdownContainer"] td:first-child {{ color: var(--sg-texto); }}

hr {{ border: 0; border-top: 1px solid var(--sg-borda); margin: 2.75rem 0 2.25rem; }}

/* ---------- masthead institucional ------------------------------------ */
/* Identificação institucional, não uma faixa de abertura de sítio. É por isso
   compacto: duas linhas de marca em corpo pequeno e o título da aplicação a
   dominar, sem gradiente, sem sombra e sem filete decorativo. A altura desceu
   cerca de 30% face à primeira versão, que funcionava como banner e empurrava
   o primeiro número da página para fora do primeiro ecrã. */
.sg-cabecalho {{
  background: var(--sg-verde); color: #fff; border-radius: var(--sg-raio);
  padding: 1.35rem 2rem 1.45rem; margin: 0 0 var(--sg-e3);
  display: flex; flex-direction: column; gap: 1rem; box-shadow: none;
}}
/* Contraste do masthead. O Streamlit injeta, por emotion, a regra
   `"h1, h2, h3, h4, h5, h6": {{ color: inherit }}` sobre o contentor de
   markdown (ver StreamlitMarkdown, função `Kf`). O seletor gerado é
   `.css-hash h1`, de especificidade (0,1,1) — **empatada** com a que aqui
   estava, `.sg-cabecalho :is(p, h1)`. Um empate resolve-se por ordem no
   documento, o que torna o resultado dependente da ordem de injeção das
   folhas e explica o título a sair escuro sobre o verde.
   Passa a (0,2,1), ancorada no contentor real, o que ganha sem depender de
   ordem nenhuma. O `!important` é a segunda linha de defesa e está limitado
   à **cor dos quatro elementos do masthead**: é texto sobre fundo verde, onde
   uma regressão não é um detalhe estético mas uma falha de contraste.
   Os dois níveis secundários usam .86 de opacidade: sobre o verde SGGov dá
   4,6:1, acima do mínimo de 4,5:1 (os .72 anteriores davam 3,7:1). */
[data-testid="stMarkdownContainer"] .sg-cabecalho,
[data-testid="stMarkdownContainer"] .sg-cabecalho :is(p, h1) {{
  color: #fff !important;
}}
[data-testid="stMarkdownContainer"] .sg-cabecalho .sg-cabecalho__uni,
[data-testid="stMarkdownContainer"] .sg-cabecalho .sg-cabecalho__sub {{
  color: rgba(255,255,255,.86) !important;
}}
.sg-cabecalho__marca {{ display: flex; align-items: center; gap: .85rem; }}
.sg-cabecalho__logo {{
  width: 40px; height: 40px; flex: 0 0 40px; border-radius: 50%;
  background: #fff; padding: 2px; display: block;
}}
/* A mesma correção de especificidade que os títulos levaram, agora nos <p>.
   O Streamlit declara `fontSize` sobre `p` dentro do `stMarkdownContainer`, em
   (0,1,1); uma classe simples, em (0,1,0), perde. Foi por isto que **todos**
   os parágrafos de componente desta aplicação vinham a render aos 16 px de
   omissão em vez do corpo aqui declarado, enquanto os separadores e os títulos
   — que já estavam ancorados — saíam certos. Daqui para baixo, todo o <p> com
   classe `sg-` traz o contentor e a tag no seletor, ficando em (0,2,1). */
[data-testid="stMarkdownContainer"] p.sg-cabecalho__inst {{
  font-size: .6875rem; font-weight: 600; letter-spacing: .16em;
  text-transform: uppercase; margin: 0; line-height: 1.25;
}}
[data-testid="stMarkdownContainer"] p.sg-cabecalho__uni {{
  font-size: .75rem; font-weight: 400; margin: .18rem 0 0; line-height: 1.25;
  letter-spacing: .005em;
}}
/* O tamanho e o peso do título têm de vencer o `h1: {{ fontSize, fontWeight }}`
   que a mesma função `Kf` injeta, e que está em (0,1,1). */
[data-testid="stMarkdownContainer"] h1.sg-cabecalho__titulo {{
  font-size: 1.5rem; font-weight: 600; letter-spacing: -.022em;
  margin: 0; padding: 0; line-height: 1.2;
}}
[data-testid="stMarkdownContainer"] p.sg-cabecalho__sub {{
  font-size: .875rem; margin: .38rem 0 0;
  max-width: 100ch; line-height: 1.5;
}}
@media (max-width: 640px) {{
  .sg-cabecalho {{ padding: 1.2rem 1.2rem 1.3rem; gap: .9rem; }}
  /* Acompanha a especificidade da regra acima, senão perde para ela. */
  [data-testid="stMarkdownContainer"] h1.sg-cabecalho__titulo {{ font-size: 1.375rem; }}
}}

/* ---------- barra de estado dos dados --------------------------------- */
/* Metadados de publicação estatística: rótulos pequenos em versalete, valores
   um degrau acima, separadores quase impercetíveis. Não é um cartão, e não
   compete com o primeiro indicador da página. */
/* Sem caixa: fundo da página e um filete em baixo. É metadado de publicação,
   não um cartão, e não tem de competir com o indicador de capa logo abaixo. */
.sg-estado {{
  background: transparent; border: 0; border-bottom: 1px solid var(--sg-borda-1);
  border-radius: 0; padding: .1rem 0 .85rem; margin: 0; box-shadow: none;
}}
[data-testid="stMarkdownContainer"] p.sg-estado__t {{
  font-size: .625rem; font-weight: 600; letter-spacing: .15em;
  text-transform: uppercase; color: var(--sg-texto-3); margin: 0 0 .5rem;
}}
.sg-estado__l {{ display: flex; flex-wrap: wrap; gap: .55rem 0; }}
.sg-estado__i {{
  display: flex; flex-direction: column; gap: .1rem;
  padding: 0 1.5rem; border-left: 1px solid var(--sg-grelha);
}}
.sg-estado__i:first-child {{ padding-left: 0; border-left: 0; }}
.sg-estado__r {{
  font-size: .625rem; font-weight: 500; letter-spacing: .1em;
  text-transform: uppercase; color: var(--sg-texto-3); line-height: 1.4;
}}
.sg-estado__v {{
  font-size: .8125rem; font-weight: 600; color: var(--sg-texto);
  line-height: 1.35; font-variant-numeric: tabular-nums;
}}
@media (max-width: 720px) {{
  .sg-estado__i {{ padding: 0 1rem; }}
}}

/* ---------- hierarquia editorial -------------------------------------- */
/* Quatro degraus, do mais forte para o mais fraco: título de página, bloco
   analítico (numerado, com filete), secção, rótulo de componente. O que
   distingue um bloco de uma secção é espaço e uma linha, não uma caixa. */
.sg-pagina {{ margin: .25rem 0 1.5rem; }}
/* Ancorado no contentor de markdown, em (0,2,1). É um <h1>, e o Streamlit
   injeta `h1: {{ fontSize, fontWeight, padding }}` em (0,1,1) sobre esse mesmo
   contentor: uma declaração de classe simples, em (0,1,0), perdia sempre, e o
   título de página vinha a render no corpo de omissão do Streamlit em vez do
   declarado aqui. O `padding: 0` anula o espaçamento que essa regra acrescenta
   e que o `.sg-pagina` já dá. */
[data-testid="stMarkdownContainer"] h1.sg-pagina__t {{
  font-size: 1.25rem; font-weight: 600; letter-spacing: -.018em;
  color: var(--sg-texto); margin: 0; padding: 0; line-height: 1.26;
}}
/* Sem `max-width`: as descrições acompanham a largura da página, por decisão
   da Inês (13.08.2026). A medida tipográfica de 72-74 caracteres favorece a
   leitura de texto corrido, mas estas são frases curtas de enquadramento e
   ficavam a meio da página, com o gráfico ou o quadro a ocupar o resto. */
[data-testid="stMarkdownContainer"] p.sg-pagina__s {{
  font-size: .8125rem; color: var(--sg-texto-2); margin: .55rem 0 0;
  line-height: 1.65; }}

.sg-secao {{ margin: var(--sg-e4) 0 var(--sg-e2); }}
.sg-secao--topo {{ margin-top: 1.25rem; }}
/* Mesma correção do título de página, agora sobre <h2>. */
[data-testid="stMarkdownContainer"] h2.sg-secao__t {{
  font-size: 1.125rem; font-weight: 600; letter-spacing: -.012em;
  color: var(--sg-texto); margin: 0; padding: 0; line-height: 1.32;
}}
[data-testid="stMarkdownContainer"] p.sg-secao__d {{
  font-size: .75rem; color: var(--sg-texto-3); margin: .5rem 0 0;
  line-height: 1.6; }}
/* Título de secção com (i). É o único caso em que o cabeçalho vem do Streamlit
   e não do nosso HTML: é o que dá acesso ao painel de ajuda, onde cabe a nota
   metodológica que estava em prosa por baixo dos gráficos. O aspeto é o mesmo
   do sg-secao__t; só a margem de topo é uniforme, sem a variante --topo. */
[data-testid="stHeadingWithActionElements"] {{ margin: var(--sg-e4) 0 0; }}
/* O título com (i) é renderizado **dentro** do contentor de markdown (o
   `stHeadingWithActionElements` envolve a própria tag do cabeçalho, dentro do
   `stMarkdownContainer`), pelo que apanha a mesma regra de emotion em (0,1,1)
   que os outros títulos. Ancorá-lo no contentor põe-no em (0,2,1) e garante
   que um título com ajuda não sai maior do que um título sem ela: ambos a
   20 px. */
[data-testid="stMarkdownContainer"] [data-testid="stHeadingWithActionElements"] :is(h1, h2, h3) {{
  font-size: 1.125rem; font-weight: 600; letter-spacing: -.012em;
  color: var(--sg-texto); margin: 0; padding: 0; line-height: 1.32; }}
.sg-secao--dep {{ margin-top: 0; }}

/* ---------- bloco analítico (super-secção) ----------------------------- */
/* O degrau que faltava. Cada página passou a ser uma sequência de blocos
   numerados, e é isso que permite perceber a estrutura sem ler o conteúdo.
   A distinção vem de um filete, de um rótulo em versalete e de muito espaço
   por cima: sem caixa à volta, sem barra de cor, sem ícone. */
.sg-bloco {{
  margin: var(--sg-e5) 0 var(--sg-e2); padding-top: 1rem;
  border-top: 1px solid var(--sg-borda-2);
}}
.sg-bloco--topo {{ margin-top: var(--sg-e4); }}
.sg-bloco--so {{ margin-bottom: 0; }}
[data-testid="stMarkdownContainer"] p.sg-bloco__r {{
  font-size: .6875rem; font-weight: 600; letter-spacing: .12em;
  text-transform: uppercase; color: var(--sg-verde); margin: 0; line-height: 1.4;
}}
/* O número ordena, não anuncia: fica em cinzento e com menos peso do que o
   nome do bloco, e nenhum dos dois compete com o título que vem a seguir. */
.sg-bloco__n {{
  color: var(--sg-texto-3); font-weight: 500; letter-spacing: .1em;
  margin-right: .8rem;
}}
/* Acompanha a especificidade da regra do <h2> acima, que agora está em (0,2,1)
   e declara `margin: 0`: sem isto, o título colava-se ao rótulo do bloco. */
[data-testid="stMarkdownContainer"] .sg-bloco h2.sg-secao__t {{ margin-top: .55rem; }}
/* Quando o título do bloco tem (i), ele vem do Streamlit, no elemento
   seguinte: é preciso anular-lhe a margem de topo para que não se descole
   do rótulo do bloco. */
[data-testid="stElementContainer"]:has(.sg-bloco--so)
  + [data-testid="stElementContainer"] [data-testid="stHeadingWithActionElements"] {{
  margin-top: .55rem;
}}

.sg-comp {{ margin: var(--sg-e3) 0 .6rem; }}
[data-testid="stMarkdownContainer"] p.sg-comp__t {{
  font-size: .8125rem; font-weight: 600; letter-spacing: .01em;
  color: var(--sg-texto); margin: 0; line-height: 1.42; }}
[data-testid="stMarkdownContainer"] p.sg-comp__d {{
  font-size: .75rem; color: var(--sg-texto-3); margin: .3rem 0 0;
  line-height: 1.58; }}

/* ---------- indicador principal (KPI de capa) -------------------------- */
/* O número mais importante da página, e só um por página. A hierarquia face
   aos indicadores secundários é dada pelo corpo do número (2,4rem contra
   1,44rem) e pelo espaço à volta, não por cor nem por moldura. */
/* Composição: rótulo em cima, valor à esquerda, grandeza que o qualifica à
   direita, proveniência em baixo a atravessar o cartão. Três registos de
   tamanho bem separados, 36 / 22 / 13 px, que são os três níveis da aplicação
   inteira: número de capa, indicador secundário, metadado. */
.sg-hero {{
  background: var(--sg-superficie); border: 1px solid var(--sg-borda-1);
  border-radius: var(--sg-raio); box-shadow: none;
  padding: 1.9rem 2.1rem 1.55rem; margin: var(--sg-e2) 0 0;
}}
.sg-hero__topo {{
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 1.1rem 2.5rem; flex-wrap: wrap;
}}
.sg-hero__p {{ min-width: min(100%, 15rem); }}
[data-testid="stMarkdownContainer"] p.sg-hero__r {{
  font-size: .6875rem; font-weight: 600; letter-spacing: .10em;
  text-transform: uppercase; color: var(--sg-texto-3); margin: 0; line-height: 1.4;
}}
/* Valor de partida, quando o cartão mostra uma transição (simulador de IVA). */
[data-testid="stMarkdownContainer"] p.sg-hero__antes {{
  font-size: .8125rem; color: var(--sg-texto-3); margin: .55rem 0 0;
  line-height: 1.4; font-variant-numeric: tabular-nums;
}}
/* Ancorado no contentor de markdown, em (0,2,1). O Streamlit define o corpo de
   letra no próprio `stMarkdownContainer` (`fontSize: fontSizes.md`) e estilos
   de `p` em (0,1,1); uma declaração de classe simples, em (0,1,0), fica
   dependente de ordem. Aqui não fica: os 36 px passam a ganhar sempre.
   Sem `!important` — a especificidade chega. */
[data-testid="stMarkdownContainer"] p.sg-hero__v {{
  font-size: 2rem; font-weight: 700; letter-spacing: -.03em; line-height: 1;
  color: var(--sg-texto); margin: .55rem 0 0; font-variant-numeric: tabular-nums;
}}
[data-testid="stMarkdownContainer"] p.sg-hero__c {{
  font-size: .75rem; color: var(--sg-texto-3); margin: 1.3rem 0 0;
  padding-top: 1rem; border-top: 1px solid var(--sg-grelha);
  line-height: 1.58;
}}
.sg-hero__c strong {{ color: var(--sg-texto-2); font-weight: 600; }}
.sg-hero__s {{ text-align: right; padding-bottom: .3rem; }}
/* Mesmo tratamento do valor de capa, pela mesma razão: é o nível 2 da escala e
   tem de ficar a meio caminho entre os 36 px e os 13 px do metadado. A cor é
   definida em linha quando a variação tem sinal, e o `style` de elemento ganha
   a esta regra, que é o comportamento pretendido. */
[data-testid="stMarkdownContainer"] p.sg-hero__sv {{
  font-size: 1.25rem; font-weight: 700; letter-spacing: -.022em; line-height: 1;
  margin: 0; color: var(--sg-texto); font-variant-numeric: tabular-nums;
}}
[data-testid="stMarkdownContainer"] p.sg-hero__sr {{
  font-size: .78rem; color: var(--sg-texto-3); margin: .4rem 0 0;
  letter-spacing: .01em;
}}
@media (max-width: 700px) {{
  .sg-hero {{ padding: 1.45rem 1.35rem 1.2rem; }}
  /* Acompanha a especificidade da regra acima, senão perde para ela. */
  [data-testid="stMarkdownContainer"] p.sg-hero__v {{ font-size: 1.875rem; }}
  .sg-hero__s {{ text-align: left; }}
}}

/* ---------- parâmetro herdado de outro separador ----------------------- */
/* Uma linha de metadados e não um aviso: o simulador não escolhe a base, herda
   a que está em “Despesa e composição”, e quem lê o resultado tem de saber
   qual é sem sair daqui. Discreta de propósito, que o dado principal é o
   resultado da simulação e não este rótulo (31.08.2026). */
[data-testid="stMarkdownContainer"] p.sg-heranca {{
  display: flex; align-items: baseline; gap: .55rem; flex-wrap: wrap;
  margin: -.35rem 0 1.25rem; padding: .4rem .7rem;
  border-left: 2px solid var(--sg-azul); background: var(--sg-superficie);
  font-size: .75rem; letter-spacing: .04em; text-transform: uppercase;
  color: var(--sg-texto-3);
}}
p.sg-heranca strong {{ font-size: .8125rem; letter-spacing: 0;
  text-transform: none; color: var(--sg-texto); font-weight: 600; }}
.sg-heranca__onde {{ letter-spacing: 0; text-transform: none;
  color: var(--sg-texto-3); }}

/* ---------- símbolos das categorias ----------------------------------- */
/* Sinalização, não decoração: o símbolo identifica e a cor reforça, e nenhum
   dos dois pode disputar atenção com o nome ou com o valor ao lado. Vai sempre
   sem fundo, dentro da caixa que já existe (31.08.2026). */
.sg-icone {{ flex: 0 0 auto; vertical-align: -.15em; }}
.sg-cartao__topo .sg-icone {{ margin-right: .45rem; }}
/* Linha de identificação de um produto do Observatório: símbolo do produto,
   nome, e o grupo a que pertence numa etiqueta menor. */
[data-testid="stMarkdownContainer"] p.sg-produto {{
  display: flex; align-items: center; gap: .5rem; flex-wrap: wrap;
  margin: .1rem 0 .55rem; }}
.sg-produto__nome {{ font-size: 1rem; font-weight: 600; color: var(--sg-texto); }}

/* ---------- cartões de indicador -------------------------------------- */
.sg-cartao {{
  background: var(--sg-superficie); border: 1px solid var(--sg-borda-1);
  border-radius: var(--sg-raio); padding: 1.45rem 1.5rem 1.3rem;
  height: 100%; display: flex; flex-direction: column; box-shadow: none;
}}
/* Cartões da mesma linha com a mesma altura. O `height: 100%` do cartão só
   funciona se o que está por cima dele também esticar: o Streamlit envolve
   cada cartão numa coluna e num contentor de markdown, e nenhum dos dois
   estica por si (decisão da Inês, 13.08.2026). */
[data-testid="stHorizontalBlock"]:has(.sg-cartao) {{
  align-items: stretch; margin-bottom: .9rem;
}}
[data-testid="stHorizontalBlock"]:has(.sg-cartao) [data-testid="stColumn"],
[data-testid="stColumn"]:has(.sg-cartao) > div,
[data-testid="stColumn"]:has(.sg-cartao) [data-testid="stVerticalBlock"],
[data-testid="stColumn"]:has(.sg-cartao) [data-testid="stMarkdownContainer"],
[data-testid="stColumn"]:has(.sg-cartao) [data-testid="stMarkdown"] {{ height: 100%; }}
.sg-cartao__topo {{ display: flex; align-items: baseline;
  justify-content: space-between; gap: .8rem; }}
/* Alinha ao centro e não à linha de base: o quadrado de 7 px assentava na
   base do texto, mas um símbolo de 14 px assim fica descaído. */
.sg-cartao__nome {{ font-size: .875rem; font-weight: 600; color: var(--sg-texto);
  line-height: 1.35; display: flex; align-items: center; gap: .45rem; }}
.sg-cartao__cod {{ font-size: .6875rem; letter-spacing: .06em; color: var(--sg-texto-3);
  margin: .3rem 0 0; padding-left: calc(14px + .45rem); }}
/* Mesmo corpo do valor de um indicador secundário: os cartões de grupo e os
   `st.metric` são o mesmo degrau da escala, e tinham 24 px contra 22 px. */
[data-testid="stMarkdownContainer"] p.sg-cartao__valor {{
  font-size: 1.375rem; font-weight: 700; letter-spacing: -.03em;
  color: var(--sg-texto); margin: 1.35rem 0 0; line-height: 1; }}
[data-testid="stMarkdownContainer"] p.sg-cartao__desc {{
  font-size: .78rem; color: var(--sg-texto-3); margin: .42rem 0 0;
  line-height: 1.5; }}
/* Duas linhas, não uma: a variação homóloga e o contributo passaram a viver
   uma sobre a outra, cada uma com o seu rótulo. Antes a variação estava solta
   no canto superior do cartão, sem nome nenhum, era essa a origem da confusão,
   e não a posição (relatado pela Inês, 13.08.2026). */
.sg-cartao__rodape {{ margin-top: auto; padding-top: 1.15rem;
  border-top: 1px solid var(--sg-grelha); font-size: .78rem;
  color: var(--sg-texto-3); line-height: 1.4; }}
.sg-cartao__linha {{ display: flex; align-items: baseline;
  justify-content: space-between; gap: .6rem; }}
.sg-cartao__linha + .sg-cartao__linha {{ margin-top: .5rem; }}
.sg-cartao__contrib {{ font-weight: 600; white-space: nowrap; }}

/* ---------- nota editorial -------------------------------------------- */
/* Reservada ao insight de um bloco, no máximo um por bloco. Tudo o resto é
   texto corrido, legenda ou bloco recolhível: a caixa perde o efeito no
   momento em que se repete de parágrafo em parágrafo. */
/* Nota editorial, não alerta de sistema. Perdeu o contorno completo: fica só
   o acento dourado à esquerda sobre o branco, com mais ar interno. O contorno
   fazia-a ler como aviso mesmo quando o conteúdo era explicativo. */
.sg-nota {{
  background: var(--sg-superficie); border: 0;
  border-left: 3px solid var(--sg-dourado); border-radius: 0;
  padding: 1.3rem 1.75rem 1.35rem; margin: var(--sg-e3) 0; font-size: .8125rem;
  line-height: 1.7; color: var(--sg-texto-2); box-shadow: none;
}}
/* Aqui não basta o par contentor+tag. O rótulo da nota é um <p> **dentro** de
   `.sg-nota`, pelo que apanha também a regra de corpo da própria nota, mais
   abaixo, que está em (0,2,1): o rótulo saía a 13 px e a cinzento, em vez dos
   11 px a dourado declarados aqui. Somar a classe da caixa põe este seletor em
   (0,3,1) e resolve, sem depender da ordem das duas regras. */
[data-testid="stMarkdownContainer"] .sg-nota p.sg-nota__t {{
  font-size: .6875rem; font-weight: 600; letter-spacing: .12em;
  text-transform: uppercase; color: var(--sg-dourado); margin: 0 0 .65rem;
}}
.sg-nota strong {{ color: var(--sg-texto); font-weight: 600; }}
.sg-nota ul {{ margin: .55rem 0 0; padding-left: 1.15rem; }}
/* Os <li> de uma nota não trazem classe, pelo que caem dentro da guarda
   `:not([class*="sg-"])` e apanhariam o corpo do texto corrido, 15 px, dentro
   de uma nota que é de 14. Este seletor tem a mesma especificidade (0,2,1) da
   regra genérica e vem depois dela na folha, que é o que o faz ganhar. */
[data-testid="stMarkdownContainer"] .sg-nota :is(p, li) {{
  font-size: .8125rem; line-height: 1.7; color: var(--sg-texto-2);
}}
.sg-nota li {{ margin-bottom: .45rem; }}
.sg-nota--alerta {{ border-left-color: var(--sg-vermelho); }}
/* Acompanha a especificidade da regra do rótulo, senão perde para ela. */
[data-testid="stMarkdownContainer"] .sg-nota--alerta p.sg-nota__t {{
  color: var(--sg-vermelho); }}

/* ---------- repartição consumidor / margem ---------------------------- */
.sg-reparticao {{
  border: 1px solid var(--sg-borda-1); border-radius: var(--sg-raio);
  background: var(--sg-superficie); padding: 1.1rem 1.3rem 1.2rem;
  font-size: .875rem; color: var(--sg-texto-2); margin-top: .35rem;
}}
.sg-reparticao__par {{ display: flex; gap: 1.5rem; margin-top: .85rem;
  flex-wrap: wrap; }}
.sg-reparticao__val {{ font-size: 1.25rem; font-weight: 700; letter-spacing: -.02em;
  font-variant-numeric: tabular-nums; }}
.sg-reparticao__rot {{ font-size: .75rem; color: var(--sg-texto-3); margin-top: .15rem; }}

/* ---------- separadores ------------------------------------------------ */
/* **Todo o CSS anterior desta secção apontava para `[data-baseweb="tab-list"]`
   e `[data-baseweb="tab"]`, que não existem nesta versão do Streamlit.** As
   regras não acertavam em nada, e era por isso que o último separador continuava
   cortado e a seta de deslocamento continuava a aparecer, por muito que se
   aumentasse a dose.
   O separador é hoje construído sobre react-aria, não sobre BaseWeb. A árvore
   real é:
     div.stTabs[data-testid="stTabs"]        <- position: relative quando excede
       └ div                                  <- invólucro
          └ div  (overflow-x: auto, gap)      <- é **este** que desliza
             └ div[data-testid="stTab"] …     <- cada separador
       └ button[data-testid="stTabsScrollLeft"|"stTabsScrollRight"]
   O contentor que desliza não tem `data-testid`, e identifica-se pelo que
   contém: `div:has(> [data-testid="stTab"])`. Com quebra de linha deixa de
   haver transbordo, o observador de dimensões nunca marca `isOverflowing`, e
   as setas não chegam a ser montadas.
   Nenhuma destas regras precisa de `!important`: `:has()` traz a
   especificidade do seu argumento, o que põe o seletor em (0,2,1) contra os
   (0,1,0) das classes geradas por emotion. */
.stTabs div:has(> [data-testid="stTab"]) {{
  display: flex; flex-wrap: wrap;
  overflow-x: visible; overflow-y: visible;
  column-gap: 1.75rem; row-gap: 0;
  margin: var(--sg-e3) 0 var(--sg-e4);
}}
.stTabs [data-testid="stTab"] {{
  flex: 0 0 auto; height: auto; padding: .7rem 0;
  font-size: .75rem; font-weight: 500; color: var(--sg-texto-3);
  white-space: nowrap;
}}
.stTabs [data-testid="stTab"]:hover {{ color: var(--sg-texto); }}
.stTabs [data-testid="stTab"][data-selected] {{
  color: var(--sg-verde); font-weight: 600;
}}
/* O rótulo é um contentor de markdown com estilos próprios: herda os do
   separador para que peso e corpo sigam o estado ativo. */
.stTabs [data-testid="stTab"] [data-testid="stMarkdownContainer"],
.stTabs [data-testid="stTab"] [data-testid="stMarkdownContainer"] p {{
  font-size: inherit; font-weight: inherit; color: inherit;
  white-space: nowrap; overflow: visible; text-overflow: clip;
}}
/* O indicador de separador ativo é um elemento absoluto **dentro** de cada
   separador, e não uma barra única sobre a lista: sobrevive à quebra de linha
   sem ajuste nenhum. Fica com o verde institucional. */
.stTabs [data-testid="stTab"][data-selected] .react-aria-SelectionIndicator {{
  background-color: var(--sg-verde);
}}
/* Rede de segurança, para o caso de uma janela ser redimensionada antes de a
   quebra ser recalculada. */
[data-testid="stTabsScrollLeft"], [data-testid="stTabsScrollRight"] {{ display: none; }}
/* Em larguras intermédias encolhe-se o **intervalo** entre separadores, nunca
   o corpo da letra: um rótulo ilegível não é melhor do que um rótulo cortado.
   Esgotado o intervalo, a barra quebra para uma segunda linha. */
@media (max-width: 1320px) {{
  .stTabs div:has(> [data-testid="stTab"]) {{ column-gap: 1.25rem; }}
}}
@media (max-width: 1100px) {{
  .stTabs div:has(> [data-testid="stTab"]) {{ column-gap: 1rem; }}
}}

/* ---------- indicadores secundários (st.metric) ------------------------ */
/* Subordinados ao KPI de capa: mesma linguagem, metade do corpo do número. */
/* O `min-height` é um piso, e sozinho não chegava: alinhava a fila quando a
   diferença vinha do rótulo, mas não quando vinha do conteúdo. Um cartão com
   variação percentual por baixo do valor ao lado de um sem ela ficava mais
   alto, e a fila desalinhava na base (relatado pela Inês, 20.08.2026).

   `height: 100%` no cartão só funciona se o que está por cima também esticar,
   como nos cartões de grupo. O que travou esta correção da primeira vez foi o
   receio de partir as colunas que têm um indicador **e** uma legenda por baixo,
   onde esticar tudo faria o indicador comer a coluna inteira.

   A guarda resolve-o: a cadeia só estica quando o indicador é **filho único**
   da sua coluna. Havendo legenda por baixo, há dois contentores, `:only-child`
   não pega, e essas colunas ficam exatamente como estavam. O `height: 100%` do
   cartão é inofensivo aí, porque uma altura em percentagem contra um pai de
   altura automática resolve para automático.

   Isso deixava a coluna com legenda desalinhada na base, e a 01.09.2026tentei
   corrigi-lo por CSS: tirar a guarda e fazer crescer o contentor do indicador
   com `flex`. **Não pegou.** Nesta versão o contentor é desenhado por um
   mecanismo próprio do Streamlit (`minStretchBehavior`), e a folha de autor não
   o vence. Ficou o que funciona, e a legenda saiu da coluna para debaixo da
   fila, onde alias contextualiza os tres cartoes e nao so um. */
[data-testid="stMetric"] {{
  background: var(--sg-superficie); border: 1px solid var(--sg-borda-1);
  border-radius: var(--sg-raio); padding: 1.3rem 1.4rem 1.35rem;
  min-height: 7.5rem; height: 100%; box-shadow: none;
}}
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {{
  align-items: stretch;
}}
[data-testid="stColumn"]:has([data-testid="stElementContainer"]:only-child
    > [data-testid="stMetric"]) > div,
[data-testid="stColumn"]:has([data-testid="stElementContainer"]:only-child
    > [data-testid="stMetric"]) [data-testid="stVerticalBlock"],
[data-testid="stColumn"] [data-testid="stElementContainer"]:only-child:has(
    > [data-testid="stMetric"]) {{ height: 100%; }}
/* Rótulos a duas linhas, sem reticências. O `st.metric` desenha o rótulo com
   `<Markdown … truncate>`, e essa opção injeta, no contentor **e** no seu <p>:
     overflow: hidden; white-space: nowrap; text-overflow: ellipsis
   (ver StreamlitMarkdown, o ramo `...truncate && {{…}}`). Era daí que vinham os
   “AGREGADO MÉDIO NACIONAL (2,…”. Anula-se nos dois níveis, com (0,2,0) e
   (0,2,1) contra os (0,1,0) e (0,1,1) do emotion: sem `!important`.
   `min-height` reserva as duas linhas para que os cartões de uma fila não
   fiquem desalinhados por o vizinho ter rótulo mais curto. */
[data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"],
[data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"] p {{
  white-space: normal; overflow: visible; text-overflow: clip;
  line-height: 1.45;
}}
[data-testid="stMetricLabel"] {{ overflow: visible; }}
[data-testid="stMetricLabel"] p {{
  font-size: .6875rem; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; color: var(--sg-texto-3); line-height: 1.45;
  min-height: 2.1em;
}}
/* Nível 2 da escala: 20 px contra os 32 px do indicador de capa e os 11 px do
   seu rótulo. A distância continua a chegar para o número de capa dominar. */
[data-testid="stMetricValue"] {{
  font-size: 1.25rem; font-weight: 700; letter-spacing: -.025em;
  color: var(--sg-texto); line-height: 1.2;
}}
[data-testid="stMetricDelta"] {{ font-size: .8125rem; font-weight: 600; padding-top: .3rem; }}

/* ---------- mensagens: hierarquia sem dominar a página ----------------- */
[data-testid="stAlertContainer"] {{
  border: 1px solid var(--sg-borda-1); border-left: 2px solid var(--sg-borda-2);
  border-radius: var(--sg-raio); background: var(--sg-superficie);
  box-shadow: none; padding: 1.1rem 1.4rem; color: var(--sg-texto-2);
}}
/* Acompanha o corpo de texto: um `st.info` contém prosa analítica, e ficar um
   degrau acima do texto que o rodeia fá-lo-ia ler como aviso de sistema. */
[data-testid="stAlertContainer"] :is(p, li) {{ font-size: .8125rem; line-height: 1.7; }}
[data-testid="stAlertContainer"] strong {{ color: var(--sg-texto); }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {{
  border-left-color: var(--sg-azul);
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {{
  border-left-color: var(--sg-verde);
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {{
  border-left-color: var(--sg-dourado); background: #FDFAF2;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {{
  border-left-color: var(--sg-vermelho); border-left-width: 3px;
  background: #FDF4F3; color: var(--sg-texto);
}}

/* ---------- blocos recolhíveis ----------------------------------------- */
[data-testid="stExpander"] {{
  border: 1px solid var(--sg-borda-1); border-radius: var(--sg-raio);
  background: var(--sg-superficie); box-shadow: none;
}}
/* O sumário é o título de um bloco recolhível: alinha com o título de
   componente, que é a mesma função. */
[data-testid="stExpander"] summary {{
  padding: .9rem 1.2rem; font-size: .8125rem; font-weight: 500;
  color: var(--sg-texto);
}}
[data-testid="stExpander"] summary:hover {{ color: var(--sg-verde); }}
[data-testid="stExpanderDetails"] {{ padding: 0 1.2rem 1.2rem; }}

/* ---------- botões e controlos ----------------------------------------- */
.stButton > button, .stDownloadButton > button {{
  border-radius: var(--sg-raio); border: 1px solid var(--sg-borda-2);
  background: var(--sg-superficie); color: var(--sg-texto);
  font-size: .8125rem; font-weight: 500; padding: .5rem 1.05rem; box-shadow: none;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  border-color: var(--sg-verde); color: var(--sg-verde); background: var(--sg-superficie);
}}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {{
  outline: 2px solid var(--sg-verde); outline-offset: 2px;
}}
[data-testid="stWidgetLabel"] p {{
  font-size: .75rem; font-weight: 500; color: var(--sg-texto-2);
}}
/* O contorno dos campos editáveis **não** está aqui: está no `.streamlit/
   config.toml`, em `showWidgetBorder` e `borderColor`. Esteve aqui, a apontar
   para `div[data-baseweb="input"]`, e não pegava: nesta versão o campo numérico
   é `stNumberInputContainer` e o seletor deixou de usar BaseWeb. As opções de
   tema valem para todos os tipos de campo e não dependem da estrutura interna
   do Streamlit, que muda entre versões (01.09.2026). */
/* Contadores estreitos. Um `number_input` ocupa a coluna
   toda, e numa coluna larga isso punha o “−” e o “+” a quatrocentos píxeis do
   número que alteram: o controlo deixava de se ler como um contador
   (relatado pela Inês, 20.08.2026).

   Duas larguras, e não uma. O contentor limita-se ao suficiente para o rótulo
   caber numa linha, o que também encosta o (i) ao texto em vez de o deixar
   perdido na margem direita. O campo, esse, é bem mais estreito, e é o que põe
   os botões junto ao número. Limitar só o contentor não chegava: os botões são
   alinhados à direita do campo, logo é a largura **do campo** que os afasta.

   O `:not` do rótulo em vez de `> div`: o rótulo é um `<label>` nesta versão do
   Streamlit, mas já houve versões em que estes contentores mudaram de elemento,
   e a exclusão por identificador sobrevive a isso. */
[data-testid="stNumberInput"] {{ max-width: 15rem; }}
[data-testid="stNumberInput"] > :not([data-testid="stWidgetLabel"]) {{
  max-width: 9rem;
}}
/* Os dois contadores da composição do agregado vivem numa coluna estreita. Com
   o limite geral acima, o campo ficava tão estreito que o Streamlit deixava de
   desenhar o “−” e o “+”, e o contador passava a parecer um valor fixo. Sem
   limite nenhum, os botões iam para a margem direita da coluna, longe do número
   que alteram, que é o defeito que o limite geral existe para evitar.
   Fica um limite próprio, entre os dois: chega para os botões existirem e
   mantém-nos encostados ao número (relatado pela Inês, 01.09.2026). */
.st-key-comp-agregado [data-testid="stNumberInput"],
.st-key-comp-agregado [data-testid="stNumberInput"]
    > :not([data-testid="stWidgetLabel"]) {{ max-width: 11.5rem; }}

/* ---------- quadros de dados ------------------------------------------- */
[data-testid="stDataFrame"] {{
  border: 1px solid var(--sg-borda-1); border-radius: var(--sg-raio);
}}

/* ---------- estado da recolha ------------------------------------------ */
/* Substituiu a barra lateral a 01.09.2026. Metadado editorial, no mesmo corpo
   e na mesma cor dos restantes: o que o distingue é estar ao lado do botão que
   o renova, e não uma caixa nem um destaque. Alinhado com a base do botão pelo
   `vertical_alignment` da coluna, não por margem à mão. */
[data-testid="stMarkdownContainer"] p.sg-recolha {{
  font-size: .75rem; color: var(--sg-texto-3); margin: 0; line-height: 1.5;
}}
[data-testid="stMarkdownContainer"] p.sg-recolha strong {{
  font-weight: 600; color: var(--sg-texto-2); font-variant-numeric: tabular-nums;
}}

/* Tracking mais curto em tudo o que é versalete. O espaçamento largo dava a
   estes rótulos uma presença que não corresponde ao seu lugar na hierarquia:
   são etiquetas, não títulos. O corpo de letra não desce; só o tracking. */
/* Rótulo de grupo dos parâmetros, no topo de “Despesa e composição”. */
[data-testid="stMarkdownContainer"] p.sg-grupo {{
  font-size: .6875rem; font-weight: 600; letter-spacing: .08em;
  text-transform: uppercase; color: var(--sg-texto-3);
  margin: 1.3rem 0 .45rem; padding-top: .9rem;
  border-top: 1px solid var(--sg-borda);
}}
/* A regra acima declara `margin` completa em (0,2,1); a variante tem de subir
   ao mesmo nível para lhe alterar o topo. */
[data-testid="stMarkdownContainer"] p.sg-grupo--primeiro {{ margin-top: 1.15rem; }}

/* ---------- rodapé ------------------------------------------------------ */
.sg-rodape {{ margin-top: 3.25rem; padding: 1.75rem 0 2.5rem;
  border-top: 1px solid var(--sg-borda-2); }}
.sg-rodape__l {{ display: flex; align-items: baseline;
  justify-content: space-between; gap: .6rem 2rem; flex-wrap: wrap; }}
[data-testid="stMarkdownContainer"] p.sg-rodape__org {{
  font-size: .6875rem; font-weight: 600; letter-spacing: .14em;
  text-transform: uppercase; color: var(--sg-texto-2); margin: 0; }}
[data-testid="stMarkdownContainer"] p.sg-rodape__uni {{
  font-size: .75rem; color: var(--sg-texto-3); margin: .3rem 0 0; }}
[data-testid="stMarkdownContainer"] p.sg-rodape__app {{
  font-size: .75rem; color: var(--sg-texto-3); margin: 0; }}
/* Sem `max-width`: a nota acompanha a largura da linha de cima, que é um flex
   com `space-between` e já ia de ponta a ponta. Tinha 92ch, medida de leitura
   confortável, mas deixava a nota a terminar a meio da folha enquanto o resto
   do rodapé chegava à margem, e o desalinhamento lia-se como defeito
   (decisão da Inês, 31.08.2026). */
[data-testid="stMarkdownContainer"] p.sg-rodape__nota {{
  font-size: .72rem; color: var(--sg-texto-3); margin: 1.35rem 0 0;
  line-height: 1.62; }}

/* Esconde o rodapé próprio do Streamlit, não o rodapé institucional. */
footer:not(.sg-rodape) {{ visibility: hidden; }}

/* ---------- voltar ao topo ---------------------------------------------- */
/* Uma **âncora**, e não um botão com script. O `st.markdown` insere HTML em
   bruto, mas o navegador não executa `<script>` inserido por essa via: qualquer
   solução com JavaScript seria inerte aqui. Um `href="#topo"` manda o navegador
   trazer o topo à vista, e quem faz o deslocamento é o próprio contentor do
   Streamlit, seja ele qual for, sem que a regra precise de o saber.

   Da mesma restrição decorre que **fica sempre visível**: aparecer só depois de
   se ter descido exigiria observar a posição de deslocamento, que é trabalho de
   script.

   O seletor repete `[data-testid="stMarkdownContainer"] a` de propósito. A regra
   genérica das ligações, lá em cima, tem especificidade (0,1,1) e declara `color`
   e `border-bottom`; uma `.sg-subir` sozinha tem (0,1,0) e **perderia as duas**,
   ficando um botão azul com um risco por baixo. É a mesma armadilha que o bloco
   do texto corrente documenta.

   Sem sombra, como tudo o resto nesta aplicação: a profundidade faz-se com
   borda. E a cor não é decorativa, o repouso é superfície neutra e o verde
   (identidade) entra só na interação. */
[data-testid="stMarkdownContainer"] a.sg-subir {{
  position: fixed; right: 1.5rem; bottom: 4.25rem; z-index: 90;
  width: 2.25rem; height: 2.25rem;
  display: flex; align-items: center; justify-content: center;
  background: var(--sg-superficie); color: var(--sg-texto-3);
  border: 1px solid var(--sg-borda-2); border-radius: var(--sg-raio);
  text-decoration: none;
}}
/* A seta é desenhada com dois lados de uma caixa rodada 45°: não é emoji nem
   ficheiro, e herda `currentColor`, pelo que acompanha o estado sem uma regra
   própria. O mesmo critério do favicon, que é o símbolo da SGGov e não um
   emoji, e o dos marcadores das tabelas, que são texto. */
[data-testid="stMarkdownContainer"] a.sg-subir::before {{
  content: ""; width: .5rem; height: .5rem; margin-top: .2rem;
  border-left: 1.5px solid currentColor; border-top: 1.5px solid currentColor;
  transform: rotate(45deg);
}}
[data-testid="stMarkdownContainer"] a.sg-subir:hover {{
  background: var(--sg-verde); border-color: var(--sg-verde); color: #fff;
}}
[data-testid="stMarkdownContainer"] a.sg-subir:focus-visible {{
  outline: 2px solid var(--sg-azul); outline-offset: 2px;
}}
/* O `bottom` afasta-se mais do que a margem natural porque o Streamlit
   Community Cloud desenha o seu emblema «Manage app» exatamente neste canto, e
   os dois sobrepunham-se. Em execução local sobra espaço; alojada, não sobrava.
   Em ecrã estreito encolhe e encosta-se, para tapar menos conteúdo. */
@media (max-width: 640px) {{
  [data-testid="stMarkdownContainer"] a.sg-subir {{
    right: 1rem; bottom: 3.75rem; width: 2rem; height: 2rem;
  }}
}}
/* Impede que o alvo da âncora fique encostado ao limite superior do contentor,
   por baixo da barra do Streamlit. */
.sg-cabecalho {{ scroll-margin-top: 1rem; }}

/* ---------- índice pesquisável da metodologia --------------------------- */
/* Duas colunas de ligações, agrupadas pelo bloco documental a que pertencem.
   Não é uma lista com marcas: são trinta entradas, e as marcas dariam-lhe o
   peso de conteúdo quando o que ela é vale como moldura de navegação. */
.sg-indice {{
  column-count: 2; column-gap: 2.5rem; margin: .35rem 0 .5rem;
}}
@media (max-width: 720px) {{ .sg-indice {{ column-count: 1; }} }}
[data-testid="stMarkdownContainer"] p.sg-indice__b {{
  font-size: .625rem; font-weight: 600; letter-spacing: .1em;
  text-transform: uppercase; color: var(--sg-texto-3);
  margin: .9rem 0 .3rem; break-after: avoid;
}}
.sg-indice__b:first-child {{ margin-top: 0; }}
[data-testid="stMarkdownContainer"] a.sg-indice__l {{
  display: block; font-size: .8125rem; color: var(--sg-texto-2);
  text-decoration: none; padding: .16rem 0; line-height: 1.4;
  break-inside: avoid;
}}
[data-testid="stMarkdownContainer"] a.sg-indice__l:hover {{
  color: var(--sg-verde); text-decoration: underline;
}}
/* Âncora sem corpo, imediatamente antes de cada bloco recolhível. A margem de
   deslocamento impede que o título fique colado ao topo da janela no salto. */
.sg-ancora {{ display: block; height: 0; scroll-margin-top: 5rem; }}

/* ---------- profundidade: borda, nunca sombra -------------------------- */
[data-testid="stDataFrame"], [data-testid="stExpander"], [data-testid="stMetric"],
[data-testid="stAlertContainer"], [data-testid="stPopoverBody"],
.stButton > button, .stDownloadButton > button {{ box-shadow: none; }}

/* ---------- ecrãs realmente largos ------------------------------------- */
/* A escala compacta acima é a **normal**: a aplicação não depende de um ecrã
   grande para estar equilibrada. Acima de 1800 px sobra largura, e cinco níveis
   ganham um degrau — só cinco. Rótulos, legendas, metadados, separadores e
   cabeçalhos da barra lateral **não** sobem: se subissem, isto deixava de ser
   uma escala e passava a ser um zoom. O indicador de capa vai a 34 px, e não
   volta aos 36 de onde veio.
   Os seletores repetem os das regras base porque a media query não altera a
   especificidade: qualquer um mais fraco perderia para a regra que substitui. */
@media (min-width: 1800px) {{
  [data-testid="stMarkdownContainer"] p.sg-hero__v {{ font-size: 2.125rem; }}
  [data-testid="stMarkdownContainer"] h1.sg-pagina__t {{ font-size: 1.375rem; }}
  [data-testid="stMarkdownContainer"] h2.sg-secao__t,
  [data-testid="stMarkdownContainer"] [data-testid="stHeadingWithActionElements"] :is(h1, h2, h3) {{
    font-size: 1.25rem;
  }}
  [data-testid="stMarkdownContainer"] :is(p, li):not([class*="sg-"]) {{
    font-size: .875rem;
  }}
  [data-testid="stMarkdownContainer"] p.sg-pagina__s {{ font-size: .875rem; }}
}}

/* ---------- larguras intermédias --------------------------------------- */
/* O Streamlit só empilha colunas abaixo de ~640 px. Entre isso e o ecrã
   largo, uma grelha de três cartões fica com colunas estreitas de mais para o
   nome do grupo e para o valor: passa a duas colunas, e só depois a uma. */
@media (max-width: 1080px) {{
  [data-testid="stHorizontalBlock"]:has(.sg-cartao) {{ flex-wrap: wrap; }}
  [data-testid="stHorizontalBlock"]:has(.sg-cartao) > [data-testid="stColumn"] {{
    flex: 1 1 calc(50% - 1rem); min-width: 15rem;
  }}
}}
@media (max-width: 1080px) {{
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {{ flex-wrap: wrap; }}
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {{
    min-width: 12rem;
  }}
}}
</style>
""", unsafe_allow_html=True)


# ==========================================================================
# Componentes de hierarquia editorial
# ==========================================================================
# Quatro degraus, e só quatro: título de página, bloco analítico, título de
# secção, rótulo de componente. Existem para que a página tenha ritmo visual
# sem que cada peça invente o seu espaçamento, e para que a descrição fique
# presa ao título em vez de aparecer como uma legenda solta por baixo.
#
# O degrau do **bloco** entrou nesta segunda versão. Sem ele, quinze secções
# seguidas tinham todas o mesmo peso e a página lia-se como uma lista: era
# preciso ler o conteúdo para perceber a estrutura. O bloco é numerado, traz um
# filete por cima e um rótulo em versalete, e é o que permite passar os olhos
# por uma página e saber onde se está.
def _html(txt) -> str:
    """Escapa o mínimo indispensável para inserir texto em HTML."""
    return (str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def titulo_pagina(titulo: str, subtitulo: str | None = None) -> None:
    sub = f'<p class="sg-pagina__s">{subtitulo}</p>' if subtitulo else ""
    st.markdown(f'<div class="sg-pagina"><h1 class="sg-pagina__t">{_html(titulo)}</h1>'
                f'{sub}</div>', unsafe_allow_html=True)


def _olho(rotulo: str) -> str:
    """
    Rótulo de bloco. O número de ordem sai em cinzento e com menos peso do que o
    nome do bloco: ordena a leitura, não a anuncia, e nenhum dos dois deve
    competir com o título da secção que vem a seguir.
    """
    partes = str(rotulo).split(" · ", 1)
    if len(partes) == 2:
        return (f'<p class="sg-bloco__r">'
                f'<span class="sg-bloco__n">{_html(partes[0])}</span>'
                f'{_html(partes[1])}</p>')
    return f'<p class="sg-bloco__r">{_html(rotulo)}</p>'


def bloco(rotulo: str, topo: bool = False) -> None:
    """
    Abre um grande bloco analítico sem lhe dar título próprio. Serve os casos em
    que o que se segue são blocos recolhíveis ou controlos, e um título seria
    inventar um cabeçalho para conteúdo que já se nomeia a si mesmo.

    Também marca o bloco corrente para o índice da metodologia: os expansores
    que se seguirem ficam-lhe associados, até ao `bloco` seguinte.
    """
    global _BLOCO_CORRENTE
    _BLOCO_CORRENTE = rotulo
    classe = "sg-bloco sg-bloco--so" + (" sg-bloco--topo" if topo else "")
    st.markdown(f'<div class="{classe}">{_olho(rotulo)}</div>',
                unsafe_allow_html=True)


# ==========================================================================
# Índice pesquisável da metodologia
# ==========================================================================
# A metodologia tem trinta blocos recolhíveis por cinco secções, e quem procura
# um assunto concreto não tem por onde começar senão abri-los à vez. O Ctrl+F do
# navegador também não serve: o texto está dentro de blocos fechados, e o
# navegador não procura no que não está desenhado.
#
# **O que isto é e o que não é.** É um índice: procura em títulos e em palavras
# associadas a cada bloco, não no corpo do texto. Procurar “escalas” encontra;
# procurar uma palavra que só aparece a meio de um parágrafo não encontra. Uma
# pesquisa no texto obrigava a passar o conteúdo dos trinta blocos para uma
# estrutura de dados antes de o desenhar, que é reescrever metade do separador
# (opção A, escolhida pela Inês a 01.09.2026).
#
# O índice é construído **enquanto o separador se desenha**, e não a partir de
# uma lista escrita à mão: uma lista à mão diverge do conteúdo à primeira
# alteração, e ninguém dá por isso. Como no Streamlit a ordem do ficheiro é a
# ordem de execução, o índice só existe depois de todos os expansores correrem,
# e por isso o lugar dele no topo é guardado por um contentor reservado e
# preenchido no fim, como o alarme de cobertura.
_INDICE_METODOLOGIA: list[dict] = []
_BLOCO_CORRENTE = ""


def _sem_acentos(texto: str) -> str:
    """Para comparar “Törnqvist” com “tornqvist” e “IVA” com “iva”."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto).lower())
                   if not unicodedata.combining(c))


@contextmanager
def bloco_metodologia(titulo: str, chaves: str = ""):
    """
    Um bloco recolhível da metodologia, inscrito no índice e com âncora própria.

    `chaves` são termos que o leitor procuraria e que não estão no título. Não
    aparecem no ecrã: existem só para a procura acertar em quem escreve
    “turistas” à espera das Contas Nacionais.
    """
    ref = "met-" + re.sub(r"[^a-z0-9]+", "-", _sem_acentos(titulo)).strip("-")[:60]
    _INDICE_METODOLOGIA.append({
        "bloco": _BLOCO_CORRENTE, "titulo": titulo, "chaves": chaves, "ref": ref,
    })
    # Âncora vazia, imediatamente antes do expansor. O `scroll-margin-top` no
    # CSS impede que o título fique colado ao topo da janela depois do salto.
    st.markdown(f'<span class="sg-ancora" id="{ref}"></span>',
                unsafe_allow_html=True)
    with st.expander(titulo):
        yield


def indice_metodologia(consulta: str) -> None:
    """
    Desenha os resultados da procura. **Sem consulta, não desenha nada.**

    Chegou a mostrar o índice inteiro por defeito, e eram 28 ligações em duas
    colunas à entrada do separador: uma parede, que é exatamente o que a regra
    deste separador proíbe, e a mesma razão por que os blocos abrem fechados. A
    caixa de procura basta-se, e o texto que a acompanha diz o que procurar
    (decisão da Inês, 01.09.2026).
    """
    termos = [t for t in _sem_acentos(consulta).split() if t]
    if not termos:
        return
    achados = [e for e in _INDICE_METODOLOGIA
               if all(t in _sem_acentos(f"{e['bloco']} {e['titulo']} "
                                        f"{e['chaves']}") for t in termos)]

    if not achados:
        st.caption(
            "Nada com esse termo nos títulos. O índice procura em títulos e "
            "palavras associadas, não no corpo do texto: para procurar dentro "
            "de um bloco, abra-o e use o **Ctrl+F** do navegador.")
        return

    linhas, ultimo = [], None
    for e in achados:
        if e["bloco"] != ultimo:
            ultimo = e["bloco"]
            linhas.append(f'<p class="sg-indice__b">{_html(e["bloco"])}</p>')
        linhas.append(f'<a class="sg-indice__l" href="#{e["ref"]}">'
                      f'{_html(e["titulo"])}</a>')
    st.markdown(f'<nav class="sg-indice">{"".join(linhas)}</nav>',
                unsafe_allow_html=True)
    st.caption(f"{numero(len(achados))} de "
               f"{numero(len(_INDICE_METODOLOGIA))} blocos.")


def secao(titulo: str, descricao: str | None = None, topo: bool = False,
          ajuda: str | None = None, grupo: str | None = None) -> None:
    """
    Cabeçalho de secção. `ajuda` aceita markdown e aparece num **(i)** ao lado do
    título, é onde vai a nota que interessa a quem a procura e estorva quem não
    a procura. Nesse caso o título é emitido pelo Streamlit, para se aproveitar o
    seu painel de ajuda; o CSS iguala-o ao nosso, e o `topo` deixa de ter efeito
    sobre a margem, que passa a ser sempre a normal.

    `grupo` promove a secção a **início de bloco analítico**: acrescenta-lhe o
    filete e o rótulo numerado por cima do título. É o degrau que separa os
    grandes blocos de uma página das secções dentro de cada um.
    """
    desc = f'<p class="sg-secao__d">{descricao}</p>' if descricao else ""
    olho = _olho(grupo) if grupo else ""
    extra = " sg-bloco--topo" if topo else ""
    if ajuda:
        if grupo:
            # O título vem do Streamlit no elemento seguinte; o CSS encosta-o
            # ao rótulo do bloco pelo seletor de irmão adjacente.
            st.markdown(f'<div class="sg-bloco sg-bloco--so{extra}">{olho}</div>',
                        unsafe_allow_html=True)
        st.subheader(titulo, anchor=False, help=ajuda)
        if desc:
            st.markdown(f'<div class="sg-secao sg-secao--dep">{desc}</div>',
                        unsafe_allow_html=True)
        return
    if grupo:
        st.markdown(f'<div class="sg-bloco{extra}">{olho}'
                    f'<h2 class="sg-secao__t">{_html(titulo)}</h2>{desc}</div>',
                    unsafe_allow_html=True)
        return
    classe = "sg-secao sg-secao--topo" if topo else "sg-secao"
    st.markdown(f'<div class="{classe}"><h2 class="sg-secao__t">{_html(titulo)}</h2>'
                f'{desc}</div>', unsafe_allow_html=True)


def componente(titulo: str, descricao: str | None = None) -> None:
    desc = f'<p class="sg-comp__d">{descricao}</p>' if descricao else ""
    st.markdown(f'<div class="sg-comp"><p class="sg-comp__t">{_html(titulo)}</p>'
                f'{desc}</div>', unsafe_allow_html=True)


def indicador_principal(rotulo: str, valor: str, contexto: str | None = None,
                        sec_valor: str | None = None, sec_rotulo: str | None = None,
                        sec_cor: str | None = None, antes: str | None = None) -> None:
    """
    O número de capa de uma página, e só um por página.

    Existe porque, na primeira versão, o valor mais importante da aplicação
    entrava como mais um `st.metric` numa fila de cinco, todos do mesmo tamanho:
    não havia forma de saber, de relance, qual deles era o número da página.
    `contexto` aceita HTML simples e é onde vai a proveniência (base, composição,
    escala) que antes vivia num *tooltip*. `sec_valor` é a grandeza que qualifica
    o número principal, tipicamente a variação homóloga.

    `antes` mostra o valor de partida por cima do valor de capa, em corpo de
    metadado. Serve o simulador de IVA, onde o que interessa não é só a despesa
    nova mas a passagem da atual para ela; a diferença entre as duas vai no
    `sec_valor`. É texto, e não uma seta: o mesmo critério que rege o resto da
    aplicação.
    """
    ant = f'<p class="sg-hero__antes">{antes}</p>' if antes else ""
    ctx = f'<p class="sg-hero__c">{contexto}</p>' if contexto else ""
    lado = ""
    if sec_valor is not None:
        estilo = f' style="color:{sec_cor}"' if sec_cor else ""
        lado = (f'<div class="sg-hero__s">'
                f'<p class="sg-hero__sv"{estilo}>{_html(sec_valor)}</p>'
                f'<p class="sg-hero__sr">{_html(sec_rotulo or "")}</p></div>')
    st.markdown(
        f'<section class="sg-hero"><div class="sg-hero__topo">'
        f'<div class="sg-hero__p">'
        f'<p class="sg-hero__r">{_html(rotulo)}</p>{ant}'
        f'<p class="sg-hero__v">{_html(valor)}</p></div>{lado}</div>{ctx}</section>',
        unsafe_allow_html=True)


def barra_estado(titulo: str, itens) -> None:
    """
    Metadados de publicação: período dos dados, ponderadores, âncora, momento da
    recolha. `itens` é uma sequência de pares (rótulo, valor).
    """
    celulas = "".join(
        f'<div class="sg-estado__i"><span class="sg-estado__r">{_html(r)}</span>'
        f'<span class="sg-estado__v">{_html(v)}</span></div>' for r, v in itens)
    st.markdown(f'<div class="sg-estado"><p class="sg-estado__t">{_html(titulo)}</p>'
                f'<div class="sg-estado__l">{celulas}</div></div>',
                unsafe_allow_html=True)


def nota(titulo: str, corpo: str, alerta: bool = False) -> None:
    """Nota editorial. `corpo` pode conter HTML simples (<strong>, <br>)."""
    classe = "sg-nota sg-nota--alerta" if alerta else "sg-nota"
    st.markdown(f'<div class="{classe}"><p class="sg-nota__t">{_html(titulo)}</p>'
                f'{corpo}</div>', unsafe_allow_html=True)


# ==========================================================================
# Obtenção de dados (executada no servidor, sem restrições de navegador)
# ==========================================================================
@st.cache_data(ttl=6 * 3600, show_spinner=False)
def carregar_dados(anos_historico: int = 6):
    """Obtém tudo o que a aplicação precisa. Em cache durante 6 horas."""
    ano = date.today().year
    # A janela do índice tem de cobrir o **ano-base do painel de viés**, que é
    # fixo em `config.py`. Antes era só `ano − anos_historico`, o que fazia o
    # ano-base deslizar a cada 1 de janeiro (auditoria de 11.08.2026, E14).
    primeiro_ano = min(ano - anos_historico, ANO_BASE_VIES)
    desde_indice = f"{primeiro_ano}-01"
    desde_variacao = f"{ano - 3}-01"

    # Janela generosa para as fontes anuais e semestrais. Custa pouco em volume
    # e garante que, mesmo com atraso de publicação, há sempre uma observação,
    # a aplicação usa depois a mais recente de cada série.
    JANELA = 8

    registo = []
    eurostat.ENDERECOS.clear()

    pesos_df, via1 = eurostat.ponderadores(CODIGOS)
    registo.append(("Ponderadores", via1, len(pesos_df)))

    # Ponderadores das subclasses, é o que permite dizer **quanto** de cada
    # classe segue cada taxa de IVA, e não apenas o quê. Se falhar, o painel
    # respetivo não é apresentado e a aplicação continua: não é dependência
    # de mais nada.
    try:
        sub_df, via15 = eurostat.ponderadores_subclasses(IVA_SUBCLASSES + CODIGOS)
        registo.append(("Ponderadores por subclasse", via15, len(sub_df)))
    except Exception as exc:                                   # noqa: BLE001
        sub_df, via15 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Ponderadores por subclasse", via15, 0))

    indice_df, via2 = eurostat.indice_precos(COICOP_ALIMENTAR, desde_indice)
    registo.append(("Índice de preços", via2, len(indice_df)))

    # Índice por classe, só serve o Törnqvist. Se falhar, a aplicação continua
    # sem esse painel: não é dependência de mais nada.
    try:
        idx_classes_df, via13 = eurostat.indice_classes(CODIGOS, desde_indice)
        registo.append(("Índice de preços por classe", via13, len(idx_classes_df)))
    except Exception as exc:                                   # noqa: BLE001
        idx_classes_df, via13 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Índice de preços por classe", via13, 0))

    var_df, via3 = eurostat.variacoes(
        [COICOP_ALIMENTAR] + CODIGOS, list(PAISES.keys()), desde_variacao
    )

    # Série longa de Portugal, para o gráfico do histórico acompanhar o cursor
    # em toda a janela do índice. Um grupo, um país: pedido barato. Se falhar, a
    # aplicação recorre à série curta e o gráfico continua a funcionar.
    try:
        var_pt_longo, via16 = eurostat.variacoes(
            [COICOP_ALIMENTAR], ["PT"], desde_indice)
        registo.append(("Variação homóloga PT (série longa)", via16, len(var_pt_longo)))
    except Exception as exc:                                   # noqa: BLE001
        var_pt_longo = pd.DataFrame()
        registo.append(("Variação homóloga PT (série longa)", f"indisponível ({exc})", 0))
    registo.append(("Variações e UE-27", via3, len(var_df)))

    # Agregados especiais: separam choque conjuntural de inflação estrutural.
    #
    # A janela é a **do índice**, e não `ano − anos_historico`. É o índice que
    # define as opções do cursor no separador Histórico, e este gráfico é
    # filtrado por esse cursor: pedi-lo com uma janela mais curta deixava doze
    # meses do intervalo escolhido sem dados, em silêncio. É o mesmo defeito que
    # foi corrigido ontem na linha da variação homóloga e que ficou aberto no
    # gráfico logo abaixo (auditoria de 12.08.2026, K5).
    try:
        agr_esp_df, via12 = eurostat.variacoes(
            COD_AGREGADOS, ["PT", "EU27_2020"], desde_indice)
        registo.append(("Agregados especiais do índice", via12, len(agr_esp_df)))
    except Exception as exc:                                   # noqa: BLE001
        agr_esp_df, via12 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Agregados especiais do índice", via12, 0))

    # Âncora oficial em euros, Contas Nacionais (opcional: pode não estar
    # disponível para o último ano; a aplicação funciona sem ela).
    try:
        desp_df, via4 = eurostat.despesa_alimentar(ano - JANELA)
        registo.append(("Despesa alimentar (Contas Nacionais)", via4, len(desp_df)))
    except Exception as exc:                                   # noqa: BLE001
        desp_df, via4 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Despesa alimentar (Contas Nacionais)", via4, 0))

    # Privação alimentar severa, o mais baixo dos três limiares de
    # acessibilidade. Nunca é apresentado sozinho: ver a nota em config.py.
    try:
        priv_df, via14 = eurostat.privacao_alimentar(["PT", "ES", "EU27_2020"], ano - 10)
        registo.append(("Privação alimentar (EU-SILC)", via14, len(priv_df)))
    except Exception as exc:                                   # noqa: BLE001
        priv_df, via14 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Privação alimentar (EU-SILC)", via14, 0))

    try:
        dim_df, via5 = eurostat.dimensao_agregado(ano - JANELA)
        registo.append(("Dimensão média do agregado", via5, len(dim_df)))
    except Exception as exc:                                   # noqa: BLE001
        dim_df, via5 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Dimensão média do agregado", via5, 0))

    try:
        agr_df, via6 = eurostat.numero_agregados(ano - JANELA)
        registo.append(("N.º de agregados familiares", via6, len(agr_df)))
    except Exception as exc:                                   # noqa: BLE001
        agr_df, via6 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("N.º de agregados familiares", via6, 0))

    # Nível de preços comparado, a codificação das categorias das PPP não é a
    # mesma do índice de preços, pelo que se tenta a preferida e depois a
    # reserva. Ambas são alimentares: uma reserva não alimentar invertia a
    # conclusão sem dar erro (auditoria de 10.08.2026, B3). Se nenhuma
    # responder, o painel respetivo não é apresentado.
    pli_df, pli_cat = pd.DataFrame(), None
    for candidato in eurostat.PPP_CATEGORIAS_ALIMENTOS:
        try:
            tentativa, via7 = eurostat.nivel_precos(
                list(PAISES.keys()), candidato, ano - JANELA)
            if not tentativa.empty:
                pli_df, pli_cat = tentativa, candidato
                registo.append((f"Nível de preços ({candidato})", via7, len(tentativa)))
                break
        except Exception:                                      # noqa: BLE001
            continue
    if pli_df.empty:
        registo.append(("Nível de preços comparado", "indisponível", 0))

    # Esforço alimentar, coeficiente de Engel (alimentação / consumo total)
    # Os dois lados do coeficiente de Engel são obtidos em separado: se o
    # agregado total falhar, a despesa alimentar por país continua disponível.
    partes_engel = []
    try:
        tot_df, via8a = eurostat.despesa_total_consumo(list(PAISES.keys()), ano - JANELA)
        registo.append(("Consumo total das famílias", via8a, len(tot_df)))
        partes_engel.append(tot_df)
    except Exception as exc:                                   # noqa: BLE001
        registo.append(("Consumo total das famílias", f"indisponível ({exc})", 0))
    try:
        ali_df, via8b = eurostat.despesa_alimentar_paises(list(PAISES.keys()), ano - JANELA)
        registo.append(("Despesa alimentar por país", via8b, len(ali_df)))
        partes_engel.append(ali_df)
    except Exception as exc:                                   # noqa: BLE001
        registo.append(("Despesa alimentar por país", f"indisponível ({exc})", 0))
    engel_df = pd.concat(partes_engel, ignore_index=True) if len(partes_engel) == 2 else pd.DataFrame()

    try:
        sm_df, via9 = eurostat.salario_minimo(list(PAISES.keys()), ano - JANELA)
        registo.append(("Salário mínimo nacional", via9, len(sm_df)))
    except Exception as exc:                                   # noqa: BLE001
        sm_df, via9 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append(("Salário mínimo nacional", via9, 0))

    # Salário médio: massa salarial ÷ trabalhadores por conta de outrem. É
    # **bruto**, antes de imposto e contribuições do trabalhador. O registo
    # chamava-lhe “líquido”, que é o contrário do que é, e fazia-o justamente
    # no painel de rastreabilidade e sobre a distinção que a aplicação declara
    # não ser um detalhe (auditoria de 12.08.2026, L5).
    _ROTULO_SME = ("Salário médio bruto (massa salarial ÷ trabalhadores "
                   "por conta de outrem)")
    try:
        sme_df, via11 = eurostat.salario_medio(list(PAISES.keys()), ano - JANELA)
        registo.append((_ROTULO_SME, via11, len(sme_df)))
    except Exception as exc:                                   # noqa: BLE001
        sme_df, via11 = pd.DataFrame(), f"indisponível ({exc})"
        registo.append((_ROTULO_SME, via11, 0))

    # Rendimento das famílias: média e mediana. A média é a coerente com a
    # despesa (que também é uma média); a mediana fica disponível para
    # caracterizar o agregado do meio da distribuição.
    rend_por_tipo = {}
    for indic, nome_indic in eurostat.RENDIMENTO_INDICADORES.items():
        try:
            df_r, via_r = eurostat.rendimento(list(PAISES.keys()), ano - JANELA, indic)
            registo.append((f"Rendimento {nome_indic} equivalente", via_r, len(df_r)))
            rend_por_tipo[indic] = df_r
        except Exception as exc:                               # noqa: BLE001
            registo.append((f"Rendimento {nome_indic} equivalente",
                            f"indisponível ({exc})", 0))

    # --- ponderadores: ano mais recente de cada classe ---
    #
    # Cada classe contribui com a **sua** última observação, mas o rótulo que a
    # aplicação mostra é o máximo de todas. Se uma classe ficar um ano atrás, a
    # aplicação combina ponderadores de anos diferentes e anuncia um só
    # (auditoria de 12.08.2026, K13).
    #
    # **Não se filtra pelo período comum**, ao contrário do que o diagnóstico
    # recomendava, e a razão é que a alternativa é pior. Deixar cair a classe
    # tira-lhe o ponderador, e as oito restantes absorvem 100% da despesa: cada
    # quota inflacionada em cerca de 1/8. Usar o ponderador do ano anterior para
    # uma classe introduz um erro de segunda ordem, porque os ponderadores
    # mudam pouco de ano para ano. Mantém-se o recuo, **declara-se o
    # desalinhamento**, que era o que faltava.
    pesos_df = pesos_df.sort_values("time")
    pesos = pesos_df.groupby("coicop")["valor"].last().to_dict()
    ano_pesos = pesos_df["time"].max() if not pesos_df.empty else None
    pesos_desalinhados = {
        c: str(p) for c, p in pesos_df.groupby("coicop")["time"].last().items()
        if str(p) != str(ano_pesos)
    }

    # --- ponderadores por subclasse, do mesmo ano mais recente ---
    pesos_sub, ano_pesos_sub = {}, None
    if not sub_df.empty:
        sub_df = sub_df.sort_values("time")
        ano_pesos_sub = sub_df["time"].max()
        pesos_sub = (sub_df[sub_df["time"] == ano_pesos_sub]
                     .set_index("coicop")["valor"].to_dict())

    # --- variações por classe (Portugal, mês mais recente) ---
    pt_classes = var_df[(var_df["geo"] == "PT") & (var_df["coicop"].isin(CODIGOS))]
    pt_classes = pt_classes.sort_values("time")
    variacoes_classe = pt_classes.groupby("coicop")["valor"].last().to_dict()
    mes_variacoes = pt_classes["time"].max() if not pt_classes.empty else None
    # Mesma questão dos ponderadores, e mesma decisão: uma classe que fique um
    # mês atrás entra com a taxa desse mês em vez de sair do cálculo, mas o
    # desalinhamento passa a ser declarado (auditoria de 12.08.2026, K13).
    variacoes_desalinhadas = {
        c: str(p) for c, p in pt_classes.groupby("coicop")["time"].last().items()
        if str(p) != str(mes_variacoes)
    }

    # --- séries globais de Portugal ---
    if not indice_df.empty:
        # A base do índice mudou ao longo do tempo (2015=100 → 2025=100).
        # Preferir a mais recente disponível; se nenhuma for reconhecida,
        # usar a unidade com mais observações.
        unidades = indice_df["unit"].value_counts()
        preferida = None
        for candidata in ("I25", "I15", "I05", "I96"):
            if candidata in unidades.index:
                preferida = candidata
                break
        if preferida is None:
            preferida = unidades.index[0]
        indice_pt = indice_df[indice_df["unit"] == preferida].sort_values("time")
        base_indice = preferida
    else:
        indice_pt, base_indice = indice_df, None

    # A variação de Portugal tem de cobrir **a mesma janela do índice**, porque é
    # o índice que define as opções do cursor de intervalo no separador Histórico.
    # Vinha de `var_df`, pedido para três anos e muitos países por questão de
    # volume, resultado: arrastar o cursor para trás de janeiro do ano−3 mostrava
    # a linha do índice sem a linha vermelha da variação, sem qualquer aviso
    # (relatado pela utilizadora, 12.08.2026).
    #
    # A série de PT sozinha (um grupo, um país) é barata, e é pedida à parte
    # com a janela do índice. O pedido largo continua a servir a comparação
    # europeia, onde três anos chegam.
    if not var_pt_longo.empty:
        var_pt = var_pt_longo[
            (var_pt_longo["geo"] == "PT")
            & (var_pt_longo["coicop"] == COICOP_ALIMENTAR)].sort_values("time")
    else:
        var_pt = var_df[(var_df["geo"] == "PT") &
                        (var_df["coicop"] == COICOP_ALIMENTAR)].sort_values("time")

    # --- variação homóloga **oficial** do agregado alimentar (CP011) ---
    # É o número que o INE publica e que qualquer pessoa encontra ao verificar.
    # A aplicação apresentava na capa uma taxa **reconstituída** da decomposição,
    # que difere desta em cerca de 0,15 p.p. (auditoria de 12.08.2026, K1).
    # Toma-se o mesmo mês das variações por classe, para que a comparação entre
    # as duas seja do mesmo momento.
    variacao_oficial, mes_var_oficial = None, None
    if not var_pt.empty:
        _cand = var_pt[var_pt["time"] == mes_variacoes] if mes_variacoes else var_pt
        _linha_of = (_cand if not _cand.empty else var_pt).sort_values("time").iloc[-1]
        variacao_oficial = float(_linha_of["valor"])
        mes_var_oficial = str(_linha_of["time"])

    # --- comparação europeia: todos os grupos, todos os países ---
    bench_todos = var_df.sort_values("time")
    bench = var_df[var_df["coicop"] == COICOP_ALIMENTAR].sort_values("time")

    # --- âncora oficial: despesa alimentar por agregado ---
    despesa_ano, despesa_valor = None, None
    if not desp_df.empty:
        recente = desp_df.sort_values("time").iloc[-1]
        despesa_ano, despesa_valor = str(recente["time"]), float(recente["valor"])

    # --- número de agregados: preferir os valores anuais do Eurostat ---
    # Guarda-se a **série inteira**, não só o ano mais recente, porque os dois
    # usos do número de agregados pedem anos diferentes: o denominador da âncora
    # das Contas Nacionais tem de ser do ano da despesa (2022), e a extrapolação
    # nacional do simulador de IVA tem de ser do ano mais recente. Antes havia
    # um único valor a servir os dois (auditoria de 10.08.2026, B2).
    #
    # Verificação de plausibilidade, aplicada observação a observação: um valor
    # fora deste intervalo indica que o conjunto devolvido não é o esperado
    # (dimensão errada, unidade errada, série trocada). Nesse caso recorre-se ao
    # valor censitário, que é seguro.
    agregados_serie: dict[str, int] = {}
    rejeitados = []
    if not agr_df.empty:
        for _, linha in agr_df.sort_values("time").iterrows():
            candidato = int(round(float(linha["valor"]) * 1000))      # vem em milhares
            if 3_000_000 <= candidato <= 6_500_000:
                agregados_serie[str(linha["time"])] = candidato
            else:
                rejeitados.append(candidato)
    if rejeitados:
        _quantos_rej = ("valores implausíveis" if len(rejeitados) > 1
                        else "valor implausível")
        registo.append(
            ("N.º de agregados, verificação",
             f"{len(rejeitados)} {_quantos_rej}, o primeiro "
             f"{numero(rejeitados[0])}; ignorados", 0)
        )

    agregados_valor, agregados_ano, agregados_fonte = None, None, None
    if agregados_serie:
        agregados_ano = max(agregados_serie)
        agregados_valor = agregados_serie[agregados_ano]
        agregados_fonte = "Eurostat / Inquérito ao Emprego (EU-LFS)"

    dimensao_media, dimensao_ano = None, None
    if not dim_df.empty:
        rec = dim_df.sort_values("time").iloc[-1]
        dimensao_ano, dimensao_media = str(rec["time"]), float(rec["valor"])

    # --- coeficiente de Engel por país, ano mais recente comum ---
    engel = {}
    if not engel_df.empty:
        for geo in engel_df["geo"].unique():
            sub = engel_df[engel_df["geo"] == geo]
            tot = sub[sub["coicop"] == "TOTAL"].sort_values("time")
            ali = sub[sub["coicop"] == "CP011"].sort_values("time")
            if tot.empty or ali.empty:
                continue
            anos_comuns = sorted(set(tot["time"]) & set(ali["time"]))
            if not anos_comuns:
                continue
            a = anos_comuns[-1]
            t = float(tot[tot["time"] == a]["valor"].iloc[0])
            f = float(ali[ali["time"] == a]["valor"].iloc[0])
            if t > 0:
                engel[geo] = {"ano": a, "quota": f / t * 100,
                              "total": t, "alimentar": f}

    rendimento = {}
    for indic, df_r in rend_por_tipo.items():
        rendimento[indic] = {}
        for geo in df_r["geo"].unique():
            sub = df_r[df_r["geo"] == geo].sort_values("time")
            if not sub.empty:
                rendimento[indic][geo] = {"ano": str(sub["time"].iloc[-1]),
                                          "valor": float(sub["valor"].iloc[-1])}

    salario_med = {}
    if not sme_df.empty:
        for geo in sme_df["geo"].unique():
            sub = sme_df[sme_df["geo"] == geo].sort_values("time")
            if not sub.empty:
                salario_med[geo] = {"ano": str(sub["time"].iloc[-1]),
                                    "valor": float(sub["valor"].iloc[-1])}

    salario = {}
    if not sm_df.empty:
        for geo in sm_df["geo"].unique():
            sub = sm_df[sm_df["geo"] == geo].sort_values("time")
            if not sub.empty:
                salario[geo] = {"periodo": str(sub["time"].iloc[-1]),
                                "valor": float(sub["valor"].iloc[-1])}

    # --- vigilância de frescura das séries obtidas por API ---
    # Uma série arquivada responde com HTTP 200 e devolve dados bem formados;
    # apenas deixa de avançar. Foi assim que a aplicação apresentou dezembro de
    # 2025 durante sete meses (auditoria de 11.08.2026, E1 e E3). Regista-se
    # aqui o **último período de cada série**; a comparação com a data corrente
    # é feita na renderização, para não ficar congelada na cache.
    def _lim(chave):
        return LIMITES_FRESCURA[chave]

    _ult_indice = str(indice_pt["time"].max()) if not indice_pt.empty else None
    _ult_pli = str(pli_df["time"].max()) if not pli_df.empty else None
    _ult_priv = str(priv_df["time"].max()) if not priv_df.empty else None
    _ult_rend = None
    for _ind in rendimento.values():
        if _ind.get("PT"):
            _ult_rend = _ind["PT"]["ano"]
            break

    # Três séries obtidas ficavam de fora da vigilância (auditoria de 12.08.2026,
    # K12). Vêm de conjuntos já vigiados por outras séries, o que atenua o risco
    # mas não o elimina: um conjunto pode continuar a publicar um agregado e
    # parar uma classe. E a terceira é a base de todo o apuramento do IVA.
    _ult_var_longa = (str(var_pt_longo["time"].max())
                      if not var_pt_longo.empty else None)
    _ult_agr_esp = (str(agr_esp_df["time"].max())
                    if not agr_esp_df.empty else None)
    _ult_sub = str(ano_pesos_sub) if ano_pesos_sub is not None else None

    vigilancia = []
    for chave, nome, conjunto, cadencia, periodo in [
        ("indice", "Índice de preços", eurostat.HICP_MENSAL, "mensal", _ult_indice),
        ("variacoes", "Variação homóloga", eurostat.HICP_MENSAL, "mensal",
         str(mes_variacoes) if mes_variacoes is not None else None),
        ("ponderadores", "Ponderadores por classe", eurostat.HICP_PONDERADORES,
         "anual", str(ano_pesos) if ano_pesos is not None else None),
        ("contas_nacionais", "Despesa alimentar (Contas Nacionais)",
         eurostat.CONTAS_NACIONAIS, "anual", despesa_ano),
        ("agregados", "N.º de agregados familiares", "lfst_hhnhtych", "anual",
         agregados_ano),
        ("dimensao", "Dimensão média do agregado", "ilc_lvph01", "anual", dimensao_ano),
        ("rendimento", "Rendimento das famílias (EU-SILC)", "ilc_di03", "anual", _ult_rend),
        ("privacao", "Privação alimentar (EU-SILC)", "ilc_mdes03", "anual", _ult_priv),
        ("salario_minimo", "Salário mínimo nacional", "earn_mw_cur", "semestral",
         (salario.get("PT") or {}).get("periodo")),
        ("salario_medio", "Salário médio", "nama_10_a10", "anual",
         (salario_med.get("PT") or {}).get("ano")),
        ("nivel_precos", "Nível de preços comparado", "prc_ppp_ind_1", "anual", _ult_pli),
        ("variacoes", "Variação homóloga PT (série longa)", eurostat.HICP_MENSAL,
         "mensal", _ult_var_longa),
        ("variacoes", "Agregados especiais do índice", eurostat.HICP_MENSAL,
         "mensal", _ult_agr_esp),
        ("ponderadores", "Ponderadores por subclasse", eurostat.HICP_PONDERADORES,
         "anual", _ult_sub),
    ]:
        if periodo is None:
            continue                       # série indisponível, já consta do registo
        limite, porque = _lim(chave)
        vigilancia.append({"serie": nome, "conjunto": conjunto, "cadencia": cadencia,
                           "periodo": periodo, "limite_dias": limite, "porque": porque})

    return {
        "agregados_especiais": agr_esp_df,
        "vigilancia": vigilancia,
        "engel": engel,
        "rendimento": rendimento,
        "salario": salario,
        "salario_medio": salario_med,
        "pli": pli_df,
        "pli_cat": pli_cat,
        "agregados_valor": agregados_valor,
        "agregados_ano": agregados_ano,
        "agregados_fonte": agregados_fonte,
        "agregados_serie": agregados_serie,
        "base_indice": (base_indice if not indice_df.empty else None),
        "dimensao_media": dimensao_media,
        "dimensao_ano": dimensao_ano,
        "despesa_ano": despesa_ano,
        "despesa_milhoes": despesa_valor,
        "privacao": priv_df,
        "pesos": pesos,
        "pesos_subclasses": pesos_sub,
        "ano_pesos_subclasses": ano_pesos_sub,
        "pesos_por_ano": pesos_df,
        "indice_classes": idx_classes_df,
        "ano_pesos": ano_pesos,
        "pesos_desalinhados": pesos_desalinhados,
        "variacoes_classe": variacoes_classe,
        "mes_variacoes": mes_variacoes,
        "variacoes_desalinhadas": variacoes_desalinhadas,
        "variacao_oficial": variacao_oficial,
        "mes_variacao_oficial": mes_var_oficial,
        "indice_pt": indice_pt,
        "var_pt": var_pt,
        "bench": bench,
        "bench_todos": bench_todos,
        "registo": registo,
        "enderecos": list(eurostat.ENDERECOS),
        "momento": datetime.now(),
    }


def _atualizar_por_indice(mensal_base: float, ano_base: int, indice) -> tuple:
    """
    Atualiza um valor mensal do seu período de referência para o mês mais
    recente do índice de preços. Devolve (valor, mês, fator).

    `ano_base` pode ser um ano (`2022`, e usam-se os doze meses desse ano) ou
    um par `("2022-02", "2023-01")` delimitando a janela efetiva de referência.
    A segunda forma existe porque o IDF não é um instantâneo anual: a recolha
    decorreu em 26 quinzenas seguidas, de fevereiro de 2022 a fevereiro de
    2023, e o INE não corrige os valores para uma data comum. Indexar a partir
    de um ano civil, qualquer que fosse, era um pressuposto não confirmado
    (auditoria de 10.08.2026, D1).
    """
    if indice.empty:
        return mensal_base, None, 1.0

    if isinstance(ano_base, (tuple, list)) and len(ano_base) == 2:
        inicio, fim = str(ano_base[0]), str(ano_base[1])
        do_periodo = indice[(indice["time"] >= inicio) & (indice["time"] <= fim)]
    else:
        do_periodo = indice[indice["time"].str.startswith(str(ano_base))]

    if do_periodo.empty:
        return mensal_base, None, 1.0
    media_base = float(do_periodo["valor"].mean())
    ultimo = indice.sort_values("time").iloc[-1]
    fator = float(ultimo["valor"]) / media_base if media_base else 1.0
    return mensal_base * fator, str(ultimo["time"]), fator


def ancora_oficial(dados: dict, agregados: int) -> dict | None:
    """
    Calcula a despesa alimentar mensal por agregado nas **duas bases oficiais
    disponíveis**, cada uma atualizada para o mês mais recente pelo índice de
    preços a partir do seu próprio ano de referência.

    As duas não coincidem (para 2022 divergem por um fator de 2,3) e não há
    forma de arbitrar entre elas com fontes públicas. Por isso a aplicação
    devolve ambas e apresenta o intervalo. Ver `src/config.py`, secção das
    âncoras, e docs/2026-08-07_levantamento_lacunas.md, §2.10.

    **As duas bases são independentes uma da outra.** A do IDF é uma constante
    publicada, atualizada pelo índice: não passa por divisão de agregado
    macroeconómico nenhum e não precisa das Contas Nacionais. Até 12.08.2026
    esta função devolvia None quando a despesa das Contas Nacionais faltava, e
    a aplicação **parava inteira**, incluindo na base IDF, que é a base por
    defeito e não usa esse número para nada. Uma ligação declarada opcional no
    `carregar_dados` derrubava tudo (auditoria de 12.08.2026, L2).

    Devolve None apenas se nenhuma das bases for calculável.
    """
    indice = dados["indice_pt"]
    bases = {}

    # --- Contas Nacionais: agregado macroeconómico ÷ agregados ÷ 12 ---
    # O denominador é o do **ano da despesa**, não o mais recente: ver
    # `agregados_do_ano`. O `agregados` recebido serve os outros usos da
    # aplicação (a extrapolação nacional do simulador), que pedem o ano
    # corrente e não este.
    if dados.get("despesa_milhoes") and agregados:
        ano_cn = dados["despesa_ano"]
        denominador = agregados_do_ano(dados.get("agregados_serie") or {}, ano_cn)
        mensal_cn = dados["despesa_milhoes"] * 1e6 / denominador["valor"] / 12
        valor_cn, mes, fator_cn = _atualizar_por_indice(mensal_cn, ano_cn, indice)
        bases["contas"] = {
            "valor": valor_cn, "base_mensal": mensal_cn, "ano_base": ano_cn,
            "ano_fim": int(str(ano_cn)[:4]),
            "fator": fator_cn, "plausivel": 50.0 <= valor_cn <= 3000.0,
            "denominador": denominador,
            **BASES_ANCORA["contas"],
        }
    else:
        mes = None

    # --- IDF: medição direta, constante publicada ---
    # Indexado a partir da **janela de recolha**, não de um ano civil: ver
    # `IDF_JANELA_RECOLHA` em config.py.
    mensal_idf = IDF_ALIMENTAR_ANUAL / 12
    valor_idf, mes_idf, fator_idf = _atualizar_por_indice(
        mensal_idf, IDF_JANELA_RECOLHA, indice)
    bases["idf"] = {
        "valor": valor_idf, "base_mensal": mensal_idf,
        "ano_base": "2022/2023", "janela": IDF_JANELA_RECOLHA,
        "ano_fim": int(IDF_JANELA_RECOLHA[1][:4]),
        "fator": fator_idf, "plausivel": 50.0 <= valor_idf <= 3000.0,
        **BASES_ANCORA["idf"],
    }

    valores = [b["valor"] for b in bases.values()]
    if not valores:
        return None
    return {
        "bases": bases,
        "mes": mes or mes_idf,
        "minimo": min(valores),
        "maximo": max(valores),
        # Com uma só base não há intervalo: o cartão e as legendas têm de o
        # dizer em vez de apresentarem um intervalo de amplitude zero.
        "base_unica": len(bases) == 1,
    }


# ==========================================================================
# Componentes visuais
# ==========================================================================
# Fonte por omissão dos ficheiros exportados. É **parâmetro obrigatório na
# prática**: o cabeçalho era fixo e dizia “Fonte dos dados: Eurostat” em todos
# os ficheiros, incluindo o do Observatório do GPP, que nunca passou pelo
# Eurostat, e o do cabaz por quintil, cujos níveis são do INE. São ficheiros
# que saem da aplicação e circulam sozinhos: o cabeçalho é a única coisa que
# resta a acompanhá-los (auditoria de 11.08.2026, E6).
FONTE_EUROSTAT = "Eurostat (índice harmonizado de preços e contas nacionais)"


def csv_com_fonte(df: pd.DataFrame, titulo: str, dados: dict, extra=None,
                  fonte: str = FONTE_EUROSTAT, conjuntos=None) -> bytes:
    """
    Exporta em CSV com cabeçalho de proveniência, para que o ficheiro seja
    autoexplicativo fora da aplicação.

    `fonte` identifica quem produziu os dados **deste ficheiro**, e não da
    aplicação em geral. `conjuntos` restringe a lista de conjuntos declarados;
    por omissão declaram-se os que responderam nesta sessão, lidos do registo
    de ligações, em vez de uma lista fixa que envelhecia sem ninguém dar por
    isso e que omitia mais de metade dos conjuntos usados.
    """
    if conjuntos is None:
        vistos = [ds for ds, _url, _via in (dados.get("enderecos") or [])]
        conjuntos = sorted(dict.fromkeys(vistos))       # únicos, ordem estável
    conjuntos_txt = ", ".join(conjuntos) if conjuntos else "-"

    linhas = [
        f"# {titulo}",
        "# Produzido por: Unidade de Pesquisa e Estatísticas (UPE), DSSD, Secretaria-Geral do Governo",
        f"# Fonte dos dados: {fonte}",
        f"# Conjuntos consultados nesta sessão: {conjuntos_txt}",
        f"# Último mês disponível: {dados.get('mes_variacoes') or '-'}",
        f"# Ponderadores de: {dados.get('ano_pesos') or '-'}",
        f"# Âncora das Contas Nacionais: {dados.get('despesa_ano') or '-'} "
        f"(a aplicação usa duas bases; ver a linha 'Base de cálculo' quando presente)",
        f"# Extraído em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]
    for chave, valor in (extra or []):
        linhas.append(f"# {chave}: {valor}")
    linhas += [
        "# Documento de trabalho interno. Não constitui posição oficial da Secretaria-Geral do Governo.",
        "",
    ]
    corpo = df.to_csv(index=False, sep=";", decimal=",")
    return ("\n".join(linhas) + corpo).encode("utf-8-sig")


def cartao_classe(linha: pd.Series) -> str:
    """
    Indicador editorial de um grupo de produtos. A hierarquia é: nome, valor em
    euros como elemento dominante, peso no cabaz, e por fim as duas grandezas de
    variação (a homóloga e o contributo), **rotuladas e uma sobre a outra**.

    Até 13.08.2026 a variação homóloga estava solta no canto superior direito,
    sem rótulo, e o código COICOP ocupava a segunda linha. Quem lia o cartão não
    tinha como saber a que se referia aquela percentagem, nem distingui-la do
    contributo lá em baixo. O código saiu (continua no CSV da tabela detalhada,
    que circula sozinho e precisa de ser rastreável) e as duas variações passaram
    a estar juntas, cada uma com o seu nome.

    Ambas trazem o sinal escrito, para que a leitura não dependa só da cor.
    """
    var = linha["variacao"]
    cor_var = TEXTO_3 if var is None else (VERMELHO if var > 0 else VERDE)
    quota = f"{linha['quota'] * 100:.1f}".replace(".", ",")
    if linha["contributo"] is not None:
        rotulo_contrib = ("Contributo para o aumento" if linha["contributo"] > 0
                          else "Contributo para a descida")
        # O sinal é escrito, e não deduzido da cor: é a mesma regra da variação.
        _sinal = "+" if linha["contributo"] > 0 else ""
        contributo = (f'<span class="sg-cartao__contrib" style="color:{cor_var}">'
                      f"{_sinal}{euro(linha['contributo'])}</span>")
    else:
        rotulo_contrib = "Contributo nos últimos 12 meses"
        contributo = '<span class="sg-cartao__contrib">Aguarda dados</span>'
    var_txt = "—" if var is None else percentagem(var)
    # A variação usa a mesma classe do contributo, e não uma sua: é o que garante
    # que as duas linhas do rodapé alinham à direita com o mesmo corpo de letra.
    var_html = (f'<span class="sg-cartao__contrib" style="color:{cor_var}">'
                f"{var_txt}</span>")
    cod = linha["codigo"]
    return f"""
    <div class="sg-cartao" style="--sg-cor:{cor_classe(cod)}">
      <div class="sg-cartao__topo">
        <span class="sg-cartao__nome">{icone_classe(cod)}{linha['classe']}</span>
      </div>
      <p class="sg-cartao__valor">{euro(linha['valor'])}</p>
      <p class="sg-cartao__desc">{quota}% da despesa alimentar mensal</p>
      <div class="sg-cartao__rodape">
        <div class="sg-cartao__linha"><span>Variação homóloga</span>{var_html}</div>
        <div class="sg-cartao__linha"><span>{rotulo_contrib}</span>{contributo}</div>
      </div>
    </div>"""


# --------------------------------------------------------------------------
# Linguagem visual única dos gráficos
# --------------------------------------------------------------------------
# Todos os gráficos passam por aqui antes de serem apresentados. O objetivo é
# que pareçam um conjunto, mesma tipografia, mesmas grelhas, mesmas margens,
# mesmo tratamento de legenda e de rótulo, e não quinze gráficos com quinze
# estilos. Nada aqui altera dados: só forma.
def estilo_grafico(fig: go.Figure) -> go.Figure:
    # As margens de cada gráfico não são tocadas: várias dependem de rótulos
    # colocados fora da área de traçado e reduzi-las cortava-os.
    # Os corpos de letra subiram meio ponto com o resto da aplicação, para que
    # um rótulo de eixo não fique mais pequeno do que a legenda que o explica.
    fig.update_layout(
        font=dict(family=TIPO, size=12.5, color=TEXTO_2),
        paper_bgcolor=SUPERFICIE, plot_bgcolor=SUPERFICIE,
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                    font=dict(size=12, color=TEXTO_2)),
        hoverlabel=dict(bgcolor=SUPERFICIE, bordercolor=BORDA,
                        font=dict(family=TIPO, size=12.5, color=TEXTO)),
        # Convenção portuguesa nos números dos gráficos, como no resto da
        # aplicação: vírgula decimal, espaço nos milhares.
        separators=", ",
    )
    fig.update_xaxes(
        gridcolor=GRELHA, linecolor=BORDA, zerolinecolor=BORDA_2, zerolinewidth=1,
        tickfont=dict(size=11.5, color=TEXTO_3),
        title_font=dict(size=12, color=TEXTO_3),
    )
    fig.update_yaxes(
        gridcolor=GRELHA, linecolor=BORDA, zerolinecolor=BORDA_2, zerolinewidth=1,
        tickfont=dict(size=11.5, color=TEXTO_3),
        title_font=dict(size=12, color=TEXTO_3),
    )
    return fig


def grafico(fig: go.Figure, rodape: str | None = None, **kwargs) -> None:
    """
    Aplica a linguagem visual comum e apresenta o gráfico.

    `rodape` carimba o texto **dentro da figura**, em corpo pequeno, por baixo
    do eixo. Uma legenda em HTML por baixo do gráfico não acompanha a imagem:
    quem copie o gráfico para uma nota ou uma apresentação fica com um quadro
    sem data nenhuma. O carimbo viaja com ela (20.08.2026).

    A margem inferior é aumentada para o acolher, e a posição é calculada a
    partir dela, para não colidir com o título do eixo, que fica mais acima.
    """
    fig = estilo_grafico(fig)
    if rodape:
        base = fig.layout.margin.b if fig.layout.margin.b is not None else 40
        fig.update_layout(margin=dict(b=base + 30))
        fig.add_annotation(
            text=rodape, xref="paper", yref="paper", x=0, y=0,
            xanchor="left", yanchor="top", yshift=-(base + 14),
            showarrow=False, align="left",
            font=dict(family=TIPO, size=10, color=TEXTO_3))
    st.plotly_chart(fig, width="stretch", **kwargs)


def carimbo_do_grafico(dados: dict, mes_indice: str | None = None,
                       variacao: bool = True) -> str:
    """
    O que tem de viajar com a imagem: fonte e período, e mais nada.

    É a metade da proveniência que identifica o quadro. A outra metade, a base
    de cálculo, fica em `base_de_calculo`, por baixo do gráfico. Repartir em vez
    de duplicar: com a frase inteira nos dois sítios, o leitor via duas legendas
    encostadas a dizer o mesmo (decisão da Inês, 20.08.2026).
    """
    mes = dados.get("mes_variacoes")
    mes_nivel = mes_indice or mes

    if mes and variacao:
        periodo = f"variação de {mes_homologo(mes)} para {mes_extenso(mes)}"
    elif mes_nivel:
        periodo = f"valores a preços de {mes_extenso(mes_nivel)}"
    else:
        periodo = "período não determinado"

    # Curto de propósito: vai em corpo 10 dentro da figura. “Eurostat / INE”
    # em vez de “Eurostat, compilado pelo INE”, e sem “no consumidor”, poupa
    # quase trinta caracteres sem perder a atribuição. O nome por extenso e a
    # distinção entre IPC e IHPC estão na metodologia.
    return f"Fonte: Eurostat / INE, índice harmonizado de preços · {periodo}"


def base_de_calculo(dados: dict, base: dict | None = None,
                    mes_indice: str | None = None) -> str:
    """
    A outra metade: com que ponderadores se repartiu e sobre que nível.

    Fica de fora do carimbo por não ser o que identifica o quadro, e por não
    caber em corpo 10 sem atravessar a figura toda.
    """
    partes = []
    if dados.get("ano_pesos"):
        partes.append(f"Ponderadores de {dados['ano_pesos']}.")
    if base:
        # O período de referência vai sempre, quando existe. Havia aqui uma
        # guarda que o omitia se já constasse do nome, e existia por causa de um
        # nome que trazia a data atrás, “IDF 2022/2023”. Os nomes deixaram de a
        # trazer a 01.09.2026, por serem rótulos: a guarda passou a nunca
        # disparar, e uma condição que nunca dispara é pior do que nenhuma,
        # porque parece proteger alguma coisa.
        ano = str(base.get("ano_base") or "")
        nivel = f"{base['nome']} ({ano})" if ano else base["nome"]
        mes_nivel = mes_indice or dados.get("mes_variacoes")
        if mes_nivel:
            nivel += f", indexado a {mes_extenso(mes_nivel)}"
        partes.append(f"Nível de despesa: {nivel}.")
    return " ".join(partes)


def nota_desalinhamento(dados: dict) -> str | None:
    """
    Aviso curto para junto do gráfico, quando nem todas as classes são do mesmo
    período.

    A declaração completa está no topo da página, mas o topo fica a mais de mil
    linhas dos contributos por grupo, e é ali que o desalinhamento produz
    efeito: são aquelas barras que misturam meses. Devolve None quando está tudo
    alinhado, que é o caso normal (20.08.2026).
    """
    desal = dados.get("variacoes_desalinhadas") or {}
    if not desal:
        return None
    nomes = [POR_CODIGO[c]["nome"] if c in POR_CODIGO else c
             for c in sorted(desal)]
    quantos = ("Uma classe entra" if len(nomes) == 1
               else f"{numero(len(nomes))} classes entram")
    return (f"**Nem todas as classes são do mesmo mês.** {quantos} com a última "
            f"observação disponível, anterior à das restantes: "
            f"{', '.join(nomes)}. Entram assim em vez de saírem do cálculo, "
            "porque excluí-las faria as outras absorver a despesa toda. Ver o "
            "aviso no topo da página.")


def proveniencia(dados: dict, base: dict | None = None,
                 mes_indice: str | None = None, variacao: bool = True) -> str:
    """
    Linha de proveniência de um gráfico: fonte, período de referência,
    ponderadores e nível de despesa, numa só frase.

    Existe porque o período de referência estava a três ecrãs de distância dos
    números que o usam. Aparecia no indicador de capa, na barra de estado e na
    barra lateral, e em nenhum dos gráficos, pelo que quem olhasse para os
    contributos não tinha como saber a que mês se referiam (relatado pela Inês,
    20.08.2026).

    **Sem códigos de conjunto.** `prc_hicp_minr` e companhia não dizem nada a
    quem usa a aplicação. Quem os quiser tem-nos no separador da metodologia,
    com a ligação para o *databrowser* do Eurostat; no corpo fica o nome da
    coisa (decisão da Inês, 20.08.2026).

    Uma função e não uma frase escrita em cada sítio, por duas razões: as datas
    aparecem em vários pontos e à mão acabariam por divergir; e a última parte
    **muda com a base escolhida na barra lateral**, que é precisamente o que
    ninguém se lembraria de atualizar numa legenda distante.

    `mes_indice` é o mês a que a âncora foi indexada, que pode não coincidir com
    o mês das variações: são séries diferentes e uma pode publicar antes da
    outra. Sem ele, assume-se o mês das variações.

    `variacao=False` para os gráficos que não mostram variação nenhuma, como a
    composição da despesa: aí a janela homóloga não é o período de referência do
    que está no ecrã, e anunciá-la seria dizer que o gráfico responde a uma
    pergunta que não responde.

    **Onde usar esta e onde usar as duas metades.** Num gráfico, a identificação
    vai carimbada dentro da figura (`carimbo_do_grafico`, via `grafico(rodape=)`)
    e a base de cálculo por baixo (`base_de_calculo`): repartidas, não repetidas.
    Esta função junta as duas e serve o que **não é figura**, como o detalhe por
    grupo, que são cartões e não tem imagem nenhuma para carimbar.
    """
    return " ".join(p for p in (
        carimbo_do_grafico(dados, mes_indice, variacao) + ".",
        base_de_calculo(dados, base, mes_indice),
    ) if p)


def grafico_composicao(df: pd.DataFrame) -> go.Figure:
    """
    Repartição da despesa alimentar pelos nove grupos, em **ranking horizontal**.

    Era um donut. Os dados são exatamente os mesmos, e as percentagens são as
    mesmas que o donut calculava (valor do grupo sobre a soma dos nove); o que
    muda é a legibilidade. Nove fatias obrigam a saltar entre o círculo e a
    legenda para saber de que grupo é cada fatia, e as quatro menores ficavam
    indistinguíveis entre si. Em barras ordenadas, o nome está encostado à
    barra, a ordem de grandeza lê-se de uma vez e a comparação entre dois
    grupos quaisquer é imediata. O total mensal, que estava no centro do donut,
    é o indicador de capa da página.

    A cor por grupo mantém-se: é a mesma que marca cada cartão do detalhe, logo
    abaixo, e é o que liga as duas leituras.
    """
    # Ascendente de propósito: o Plotly desenha a primeira categoria em baixo,
    # pelo que o maior grupo fica no topo, que é onde a leitura começa.
    dados = df[df["valor"] > 0].sort_values("valor", ascending=True)
    total = float(dados["valor"].sum())
    quotas = [(v / total * 100 if total else 0.0) for v in dados["valor"]]
    fig = go.Figure(go.Bar(
        y=list(dados["classe"]), x=list(dados["valor"]), orientation="h",
        marker_color=[cor_classe(c) for c in dados["codigo"]],
        customdata=quotas,
        text=[f"{q:.1f}%".replace(".", ",") for q in quotas],
        textposition="outside",
        textfont=dict(size=11.5, color=TEXTO_2),
        cliponaxis=False,
        hovertemplate=("<b>%{y}</b><br>%{x:.2f} € por mês"
                       "<br>%{customdata:.1f}% da despesa alimentar<extra></extra>"),
    ))
    fig.update_layout(
        height=max(400, 40 * len(dados)),
        margin=dict(t=12, b=40, l=10, r=70),
        xaxis_title="Euros por mês", showlegend=False,
    )
    return fig


def grafico_historico(indice: pd.DataFrame, variacao: pd.DataFrame,
                      meses: int) -> go.Figure:
    idx = indice.tail(meses)
    var = variacao.tail(meses)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[mes_pt(t) for t in idx["time"]], y=idx["valor"],
        name="Índice de preços", line=dict(color=VERDE, width=2.2),
        hovertemplate="%{x}<br>Índice: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[mes_pt(t) for t in var["time"]], y=var["valor"],
        name="Variação homóloga (%)", yaxis="y2",
        line=dict(color=VERMELHO, width=1.8, dash="dot"),
        hovertemplate="%{x}<br>Variação: %{y:.1f}%<extra></extra>",
    ))
    # Mais alto do que na primeira versão: é o gráfico principal do separador
    # Histórico e estava a competir em altura com os cartões que o rodeiam.
    fig.update_layout(
        height=490, margin=dict(t=34, b=42),
        yaxis=dict(title="Índice"),
        yaxis2=dict(title="Variação homóloga (%)", overlaying="y", side="right",
                    zeroline=True, zerolinecolor=BORDA_2, showgrid=False),
        legend=dict(orientation="h", y=1.11, x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    return fig


def grafico_reparticao(sim: pd.DataFrame) -> go.Figure:
    dados = sim[sim["mecanico"].abs() > 0.001].copy()
    if dados.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=list(dados["classe"]),
        x=dados["efetivo"].abs(), name="Chega ao consumidor",
        orientation="h", marker_color=VERDE,
        hovertemplate="%{y}<br>Consumidor: %{x:.2f} €<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=list(dados["classe"]),
        x=dados["margem"].abs(), name="Capturado na margem",
        orientation="h", marker_color=DOURADO,
        hovertemplate="%{y}<br>Margem: %{x:.2f} €<extra></extra>",
    ))
    # Escala fixa ao efeito total. Sem isto, desligar uma das séries na legenda
    # fazia o Plotly reescalar o eixo, e a barra restante passava a preencher a
    # largura toda, parecia ter absorvido o valor da outra. Os valores estavam
    # certos; a impressão é que não (relatado pela utilizadora, 13.08.2026).
    # Com a escala travada, desligar uma série mostra literalmente a fração que
    # ela representa, que é a leitura pretendida.
    _maximo = float(dados["mecanico"].abs().max())
    fig.update_layout(
        barmode="stack", height=max(440, 44 * len(dados)),
        margin=dict(t=36, b=42),
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis_title="Euros por mês",
        xaxis=dict(range=[0, _maximo * 1.08], autorange=False),
    )
    return fig


# ==========================================================================
# Cabeçalho
# ==========================================================================
_logo_html = (
    f'<img class="sg-cabecalho__logo" src="data:image/png;base64,{LOGO}" '
    f'alt="Secretaria-Geral do Governo">' if LOGO else ""
)
st.markdown(f"""
<header class="sg-cabecalho" id="topo">
  <div class="sg-cabecalho__marca">
    {_logo_html}
    <div>
      <p class="sg-cabecalho__inst">{ORGANISMO}</p>
      <p class="sg-cabecalho__uni">Suporte à Decisão · {UNIDADE}</p>
    </div>
  </div>
  <div>
    <h1 class="sg-cabecalho__titulo">Despesa alimentar das famílias</h1>
    <p class="sg-cabecalho__sub">Repartição, evolução e enquadramento europeu da
    despesa alimentar dos agregados, a partir de fontes oficiais.</p>
  </div>
</header>
""", unsafe_allow_html=True)

# ==========================================================================
# Carregamento (executado no servidor, sem restrições de navegador)
# ==========================================================================
try:
    with st.spinner("A obter dados oficiais do Eurostat…"):
        dados = carregar_dados()
    erro_carregamento = None
except Exception as exc:                                   # noqa: BLE001
    dados, erro_carregamento = None, exc

if erro_carregamento is not None:
    st.error(
        "**Não foi possível obter os dados do Eurostat.**\n\n"
        f"`{erro_carregamento}`\n\n"
        "Se esta aplicação estiver alojada no Streamlit Community Cloud, verifique o "
        "estado do serviço do Eurostat. Em execução local numa rede institucional, "
        "confirme se o acesso a `ec.europa.eu` está autorizado."
    )
    st.stop()

ultimo_mes = dados["mes_variacoes"] or (
    dados["var_pt"]["time"].max() if not dados["var_pt"].empty else "—"
)

# ==========================================================================
# Estado da recolha
# ==========================================================================
# Isto era uma barra lateral. Foi esvaziando: os parâmetros desceram para o
# topo de “Despesa e composição” a 31.08.2026, o período de referência passou
# para as faixas de proveniência dos três separadores que o índice governa a
# 01.09.2026, e a assinatura da unidade duplicava o cabeçalho, que já mostra as
# duas linhas. O que sobrava era um botão, uma hora e uma descrição de
# metadados que já não estavam lá. Uma gaveta lateral permanente para isso não
# se justifica, e a página ganha a largura que ela ocupava.
#
# **O que fica é o momento da recolha, e fica junto do botão.** É o único
# metadado desta aplicação que é propriedade da *sessão* e não de uma fonte:
# vale nos sete separadores, incluindo os da DECO e do GPP, porque é quando
# esta sessão foi buscar os dados em direto. E é o que justifica o botão
# existir: mostra-se a idade e oferece-se a ação, lado a lado. O período de
# referência é do índice, e por isso está nas faixas e não aqui.
#
# O bloco de erro fatal também sai da gaveta: com as duas bases em falta a
# aplicação pára, e a mensagem que o diz estava a ser desenhada na barra
# lateral (decisão da Inês, 01.09.2026).

# --- número de agregados: sempre o valor oficial, no ano mais recente ---
# Este é o valor usado para **extrapolar para o país** (simulador de IVA):
# aí interessa quantos agregados existem hoje. O denominador da âncora das
# Contas Nacionais é outro (o do ano da despesa), calculado em
# `agregados_do_ano` (auditoria de 10.08.2026, B2).
if dados.get("agregados_valor"):
    agregados = int(dados["agregados_valor"])
    agr_fonte = f"{dados['agregados_fonte']}, {dados['agregados_ano']}"
else:
    agregados = AGREGADOS_CENSOS
    agr_fonte = AGREGADOS_FONTE

ancora = ancora_oficial(dados, agregados)
if ancora is None:
    st.error(
        "Não foi possível calcular a despesa em nenhuma das duas bases oficiais. "
        "Consulte o registo de ligações no separador Metodologia."
    )
    st.stop()

# A hora à esquerda e o botão à direita, na mesma linha. O botão não vai a toda
# a largura: é uma ação secundária e rara, não a chamada à ação da página.
_c_recolha, _c_botao = st.columns([3, 1], gap="small",
                                  vertical_alignment="center")
_c_recolha.markdown(
    f'<p class="sg-recolha">Dados em direto obtidos às '
    f'<strong>{dados["momento"].strftime("%H:%M de %d/%m/%Y")}</strong></p>',
    unsafe_allow_html=True)
with _c_botao:
    if st.button("Recarregar do Eurostat"):
        st.cache_data.clear()
        st.rerun()

# --- vigilância de frescura: uma série que responde não é uma série que avança ---
# Calculada aqui, e não dentro de `carregar_dados`, para não ficar congelada na
# cache: o que envelhece é a distância à data corrente, não os dados.
_fresc = frescura_das_series(dados.get("vigilancia") or [])
_paradas = _fresc[_fresc["desatualizada"]] if not _fresc.empty else pd.DataFrame()
if not _paradas.empty:
    _linhas_p = "\n".join(
        f"- **{r.serie}** (`{r.conjunto}`, {r.cadencia}), último período "
        f"**{r.periodo}**, há **{numero(r.dias)} dias**; o normal seria no "
        f"máximo {numero(r.limite_dias)}. {r.porque}"
        for r in _paradas.itertuples()
    )
    _quantas_p = ("séries do Eurostat deixaram" if len(_paradas) > 1
                  else "série do Eurostat deixou")
    st.error(
        f"**{len(_paradas)} {_quantas_p} de avançar.** "
        "Não é falha de rede nem atraso de publicação: o pedido foi bem-sucedido "
        "e os dados vieram; apenas não são recentes.\n\n"
        f"{_linhas_p}\n\n"
        "**A causa mais provável é o conjunto ter sido arquivado** e substituído "
        "por outro, como aconteceu na passagem para a ECOICOP versão 2. Confirme "
        "no catálogo do Eurostat antes de citar estes valores: o título dos "
        "conjuntos arquivados indica habitualmente o intervalo de anos coberto."
    )

# --- proveniência do índice, junto de quem o usa --------------------------
# Era uma faixa única escrita **acima do `st.tabs`**, e por isso aparecia nos
# sete separadores. Anunciava metadados do índice harmonizado, que governam
# três deles e não governam os outros quatro: quem abria o cabaz da DECO lia
# “Dados oficiais carregados · Último mês disponível: …” por cima de um título
# sobre uma série semanal de outra entidade, que já declara a sua própria
# fonte logo abaixo. Sobreanunciava a proveniência e ainda a duplicava.
#
# Passa a ser escrita **dentro** de cada um dos três separadores que o índice
# governa, e com os campos que interessam a esse separador e mais nenhum:
#
#   Despesa e composição   sem o mês, que o indicador de capa anuncia em corpo
#                          grande a seguir; repeti-lo duas linhas depois era a
#                          redundância que esta alteração veio eliminar
#   Histórico              só o mês e a recolha: não usa a âncora de despesa
#                          (não dá valores em euros) nem um ano de
#                          ponderadores (a secção de Törnqvist usa vários, e
#                          nomear um só seria falso)
#   Simulador de IVA       tudo: parte da despesa em euros da base herdada
#
# O rótulo deixou de dizer “Dados oficiais carregados”, que é um relatório de
# carregamento e não proveniência: o carregamento correr bem é o caso normal.
# Os separadores da DECO, do GPP, da comparação europeia e da metodologia
# ficam sem esta faixa e mantêm a proveniência que já traziam, junto do bloco
# a que respeita (pedido da Inês, 01.09.2026).
#
# O mesmo problema existia na barra lateral, que mostrava período e recolha em
# todos os separadores. Resolveu-se logo a seguir, e por inteiro: a barra
# desapareceu, o período ficou nestas faixas e a recolha ficou uma só vez, no
# topo da página, ao lado do botão que a renova.
FONTE_INDICE = "Fonte: Eurostat / INE, índice harmonizado de preços"


def faixa_fonte(mes: bool = True, ponderadores: bool = True,
                ancora: bool = True) -> None:
    """
    Proveniência do índice, no topo do separador que dele depende.

    Sem o momento da recolha, que esteve aqui: é propriedade da sessão e não do
    índice, vale igualmente nos separadores que não o usam, e por isso ficou uma
    só vez, junto do botão que o renova (01.09.2026).
    """
    itens = []
    if mes:
        itens.append(("Último mês disponível", mes_pt(ultimo_mes)))
    if ponderadores:
        itens.append(("Ponderadores", str(dados["ano_pesos"] or "—")))
    if ancora and dados.get("despesa_ano"):
        itens.append(("Âncora de despesa", str(dados["despesa_ano"])))
    barra_estado(FONTE_INDICE, itens)

# --- classes cujo período não é o que a mensagem acima anuncia ---
# Cada classe entra com a sua última observação, e o rótulo é o máximo de todas.
# Hoje coincidem; quando não coincidirem, tem de ser dito em vez de assumido
# (auditoria de 12.08.2026, K13).
_desal_p = dados.get("pesos_desalinhados") or {}
_desal_v = dados.get("variacoes_desalinhadas") or {}
if _desal_p or _desal_v:
    def _lista_desal(mapa, rotulo_global):
        return ", ".join(
            f"**{POR_CODIGO[c]['nome'] if c in POR_CODIGO else c}** ({p} em vez de "
            f"{rotulo_global})" for c, p in sorted(mapa.items()))

    _partes = []
    if _desal_p:
        _partes.append("Ponderadores: " + _lista_desal(_desal_p, dados["ano_pesos"]))
    if _desal_v:
        _partes.append("Variações homólogas: "
                       + _lista_desal(_desal_v, dados["mes_variacoes"]))
    st.warning(
        "**Nem todas as classes têm o mesmo período.** A mensagem acima mostra o "
        "período mais recente do conjunto, mas há classes cuja última observação é "
        "anterior, entram com essa, e não são excluídas do cálculo, porque deixá-las "
        "cair distorceria mais (as restantes absorveriam a totalidade da despesa).\n\n"
        + "\n\n".join(f"- {p}" for p in _partes)
        + "\n\nO efeito é de segunda ordem, mas os números deixam de se referir todos "
        "ao mesmo momento."
    )

# --- espaço reservado para o alarme de cobertura da decomposição -------
# A decomposição depende dos controlos, que passaram para o topo do
# separador “Despesa e composição”, e por isso só pode ser calculada depois
# de eles existirem. As duas mensagens que dela dependem continuam a
# aparecer aqui, acima das abas: o contentor guarda-lhes o lugar e é
# preenchido mais abaixo (31.08.2026).
_slot_cobertura = st.container()

@contextmanager
def painel(nome: str):
    """
    Isola cada separador. Se algo falhar, um conjunto de dados com estrutura
    inesperada, um estado de sessão preso de uma versão anterior, o erro fica
    contido nesse separador, com indicação do que fazer, em vez de derrubar a
    aplicação inteira.
    """
    try:
        yield
    except Exception as exc:                                   # noqa: BLE001
        st.error(
            f"**Não foi possível apresentar “{nome}”.**\n\n"
            f"`{type(exc).__name__}: {exc}`\n\n"
            "Os restantes separadores continuam a funcionar. Passos a tentar, por esta ordem:\n"
            "1. **Recarregar do Eurostat**, no topo da página, limpa a cache de dados;\n"
            "2. **Recarregar a página** com Ctrl+F5, limpa o estado da sessão;\n"
            "3. Consultar o **registo de ligações** no separador Metodologia, para ver "
            "se algum conjunto de dados falhou."
        )


abaD, aba1, aba2, aba6, aba3, aba4, aba5 = st.tabs([
    "Evolução do cabaz", "Despesa e composição", "Histórico", "Da produção ao consumo",
    "Simulador de IVA", "Comparação UE-27", "Metodologia e fontes",
])

# ==========================================================================
# Parâmetros de análise, no topo de “Despesa e composição”
# ==========================================================================
# Deixaram de ser globais: a base de cálculo e a composição do agregado são
# definidas no separador onde actuam. Ficam escritos aqui, antes de todos os
# separadores que os consomem, porque no Streamlit a ordem do ficheiro é a
# ordem de execução, e não a ordem visual das abas. O `with aba1:` volta a
# abrir mais abaixo para o resto do separador (decisão da Inês, 31.08.2026).
with aba1:
    # O título da página abre o separador, como em todos os outros. Estava
    # escrito mais abaixo, com os parâmetros à frente dele, e este era o único
    # separador que começava por um rótulo de bloco numerado em vez do seu
    # nome. Sobe para aqui, e com ele volta o filete por cima do primeiro
    # bloco, que passou a ter alguma coisa de que se separar (pedido da Inês,
    # 01.09.2026).
    #
    # Sem `painel` à volta: é uma emissão de markdown fixo, não há aqui nada que
    # possa falhar, e um `try` que nunca dispara é ruído.
    titulo_pagina(
        "Despesa alimentar das famílias",
        "Repartição, evolução e esforço da despesa alimentar do agregado "
        "escolhido. A base de cálculo e a composição definem-se abaixo.")

    # O bloco não tinha cabeçalho: os controlos abriam o separador sem nada os
    # nomear. Não se chamam “cenário” de propósito, que nesta aplicação cenário
    # é o do simulador de IVA, e o mesmo termo para duas coisas diferentes é o
    # que a consistência terminológica proíbe. São parâmetros, e é o nome que a
    # barra lateral já lhes dava (pedido da Inês, 01.09.2026).
    secao("Parâmetros de análise",
          "Definem a base de despesa e o agregado a que se referem todos os "
          "valores deste separador. O simulador de IVA herda daqui a base de "
          "cálculo; os restantes separadores não respondem a estes parâmetros.",
          grupo="01 · Parâmetros", topo=True)

    # --- base de cálculo: as duas fontes oficiais não coincidem ---
    # As opções são **as bases efetivamente calculáveis nesta sessão**, e não a
    # lista fixa: se as Contas Nacionais não responderem, o IDF continua a
    # funcionar sozinho, é uma constante publicada atualizada pelo índice
    # (auditoria de 12.08.2026, L2).
    _bases_disp = [k for k in BASES_ANCORA if k in ancora["bases"]]

    # Os tres grupos na mesma linha. Sao tres parametros independentes e do
    # mesmo nivel, e empilhados empurravam o primeiro indicador do separador
    # para fora do ecra (pedido da Inês, 01.09.2026). A escala leva mais
    # largura por o nome da opcao trazer os coeficientes atras.
    #
    # As larguras não são iguais, e não há coluna vazia. Chegou a haver uma, para
    # encostar os controlos à esquerda, mas deixava metade da folha por usar. Cada
    # coluna leva antes a largura do que tem dentro: a base tem duas opções, a
    # composição dois contadores lado a lado, e a escala leva quase metade
    # porque carrega os dois expansores e o nome da opção traz os coeficientes
    # atrás (01.09.2026).
    #
    # A coluna da base subiu de 0,95 para 1,45: as opções deixaram de ser
    # “IDF 2022/2023” e passaram a ser a designação por extenso, que na largura
    # anterior quebrava em três linhas por opção.
    _c_base, _c_comp, _c_esc = st.columns([1.45, 1.15, 1.9], gap="medium")

    with _c_base:
        st.markdown('<p class="sg-grupo sg-grupo--primeiro">Base de cálculo</p>',
                    unsafe_allow_html=True)
        # Lugar reservado para o (i) do grupo, preenchido no fim: o que ele diz
        # depende da base que for escolhida no seletor abaixo, e o Streamlit desenha
        # por ordem de execução.
        _slot_nota_base = st.empty()
        if len(_bases_disp) == 1:
            base_chave = _bases_disp[0]
            st.info(
                f"Só a base **{BASES_ANCORA[base_chave]['nome']}** está disponível nesta "
                "sessão. A outra depende de uma ligação que não respondeu, ver o registo "
                "de ligações no separador Metodologia. **Não há intervalo: o valor "
                "apresentado é um ponto de uma só base.**"
            )
        else:
            base_chave = st.radio(
                "Base de cálculo",
                options=_bases_disp,
                index=(_bases_disp.index(BASE_POR_DEFEITO)
                       if BASE_POR_DEFEITO in _bases_disp else 0),
                format_func=lambda k: BASES_ANCORA[k]["nome"],
                label_visibility="collapsed",
                help=("As duas fontes oficiais medem grandezas diferentes e divergem por um fator "
                      "próximo de 2. Nenhuma das duas mede isoladamente a grandeza pretendida, "
                      "pelo que a aplicação apresenta o intervalo. Ver separador Metodologia."),
            )
        base_ancora = ancora["bases"][base_chave]
        outra_chave = next((k for k in ancora["bases"] if k != base_chave), None)
        outra_ancora = ancora["bases"][outra_chave] if outra_chave else None

        media_agregado = float(base_ancora["valor"])
        valor_medio_agregado = media_agregado
        dim_media = dados.get("dimensao_media")

        # A verificação de plausibilidade existe para dizer “não use estes números”,
        # e só olhava para a base **ativa**. Com a âncora das Contas Nacionais
        # absurda e o IDF escolhido, a aplicação não dava alarme nenhum, e mostrava
        # à mesma o valor absurdo, no intervalo acima, no cartão de topo
        # e na sensibilidade do simulador (auditoria de 12.08.2026, M1).
        _suspeitas = [b["nome"] for b in ancora["bases"].values()
                      if not b.get("plausivel", True)]
        _outra_suspeita = (outra_ancora is not None
                           and not outra_ancora.get("plausivel", True))


    with _c_comp:
        st.markdown('<p class="sg-grupo">Composição do agregado</p>',
                    unsafe_allow_html=True)
        # A instrução vem antes dos contadores e não depois: quem não reconhece
        # os botões como controlos precisa de a ler **antes** de olhar para o
        # número, não a seguir (Inês, 01.09.2026).
        st.caption("Use o **−** e o **+**, ou escreva o número.")
        # Um por linha, e não dois lado a lado. Repartidos em duas sub-colunas
        # de uma coluna que já é um quarto da página, o campo ficava tão estreito
        # que o Streamlit deixava de desenhar o “−” e o “+”: o contador passava a
        # parecer um valor fixo, e nada dizia que se podia alterar (relatado pela
        # Inês, 01.09.2026). Empilhados, cada um leva a largura da coluna, os
        # botões voltam, e o rótulo deixa de partir em duas linhas.
        # A `key` do contentor sai no HTML como a classe `st-key-comp-agregado`, e
        # é por ela que o CSS levanta a estes dois campos o limite de largura que
        # vale para os contadores do resto da aplicação. Sem isso o campo ficava
        # abaixo da largura a que o Streamlit desenha os botões.
        with st.container(key="comp-agregado"):
            adultos = st.number_input(
                "Com 14+ anos", min_value=1, max_value=10, value=2, step=1,
                help=("Todas as pessoas com 14 ou mais anos, incluindo jovens dependentes. "
                      "A partir dessa idade, a escala de equivalência atribui a mesma "
                      "ponderação alimentar de um adulto, independentemente de a pessoa "
                      "auferir rendimento próprio."))
            criancas = st.number_input(
                "Menos de 14 anos", min_value=0, max_value=10, value=0, step=1,
                help=("14 anos é o limiar definido pelas próprias escalas de equivalência "
                      "da OCDE e do Eurostat, não é a definição demográfica de criança. "
                      "Ver separador Metodologia."))


    # A dimensão média do agregado entra em **todos** os valores em euros, pelo
    # lado do denominador de `despesa_do_agregado`. Se a série do EU-SILC não
    # responder, entra uma constante, e isso tem de ser dito, como já se diz do
    # número de agregados e das fontes sem API. Era o único recuo da aplicação
    # que acontecia em silêncio (auditoria de 12.08.2026, L6).
    dim_efetiva = dim_media if dim_media else DIMENSAO_RECUO

    with _c_esc:
        # A escala tinha ficado dentro do grupo da composição, sem cabeçalho
        # próprio, apesar de ser um terceiro parâmetro independente dos outros dois.
        st.markdown('<p class="sg-grupo">Escala de equivalência</p>',
                    unsafe_allow_html=True)
        _escala_apurada = escala_mais_proxima()
        escala_chave = st.selectbox(
            "Escala de equivalência", options=list(ESCALAS.keys()),
            index=list(ESCALAS.keys()).index(_escala_apurada) if _escala_apurada else 1,
            format_func=lambda k: (ESCALAS[k]["nome"]
                                   + (", apurada" if k == _escala_apurada else "")),
            help=("Como se ajusta a despesa ao número de pessoas. A assinalada como "
                  "“apurada” é a que, no teste contra o Inquérito às Despesas das Famílias "
                  "(IDF) de 2022/2023, fica mais perto da despesa alimentar observada. "
                  "Ver separador Metodologia."),
        )
        if _escala_apurada and escala_chave != _escala_apurada:
            st.caption(
                f"A escala escolhida não é a que melhor reproduz a despesa alimentar observada "
                f"(**{ESCALAS[_escala_apurada]['nome'].split(' (')[0]}**). Ver o teste no "
                f"separador Metodologia."
            )

        # Lugar dos dois expansores, preenchidos mais abaixo: o comparador das
        # escalas precisa da `faixa`, que só existe depois de os três parâmetros
        # estarem lidos.
        #
        # Os dois ficam aqui, e não um em cada coluna, por decisão da Inês
        # (01.09.2026). O da proveniência qualifica a base e não a escala, mas
        # dois expansores lado a lado em colunas de larguras diferentes davam
        # duas caixas desalinhadas a meia altura do bloco; juntos, são um par.
        _slot_escalas = st.container()
        _slot_proveniencia = st.container()


    # As duas legendas (o intervalo entre bases e a idade da base) recolheram-se
    # a um (i) junto ao título do grupo: são qualificações do seletor, e em texto
    # corrido ocupavam metade do espaço visível da barra lateral
    # (decisão da Inês, 13.08.2026).
    #
    # Um popover e não o (i) do `secao()`: aquele é dado pelo cabeçalho do
    # Streamlit, que nesta largura sairia maior do que o rótulo do grupo.
    #
    # Os alarmes de implausibilidade **não** entram aqui: são para ver sem
    # procurar, e ficam no corpo da barra.
    _nota_base = []
    if outra_ancora is not None:
        _nota_base.append(
            f"Intervalo entre as duas bases: **{euro(ancora['minimo'])} a "
            f"{euro(ancora['maximo'])}** por mês, para o agregado médio. "
            f"O ponto central não é determinável."
            + (f" Um dos extremos vem de **{outra_ancora['nome']}**, que está fora do "
               "intervalo plausível, ver o alarme abaixo."
               if _outra_suspeita else ""))
        # O que separa as duas bases não é a fonte, é a pergunta: uma mede a
        # despesa dos agregados residentes, a outra o consumo no território. O
        # rácio é **calculado**, não inscrito: move-se com o mês do índice,
        # porque as duas bases são indexadas a partir de períodos de referência
        # diferentes, e um número escrito à mão desatualizava-se em silêncio
        # (é o modo de falha que o L16 fechou noutro sítio).
        _racio_bases = (ancora["maximo"] / ancora["minimo"]
                        if ancora["minimo"] else None)
        if _racio_bases and _racio_bases > 1.05:
            _racio_txt = numero(_racio_bases, 1)
            if base_chave == "idf":
                _nota_base.append(
                    "A base ativa é a que mede a **despesa das famílias residentes**; a outra "
                    f"mede o **consumo no território** e é cerca de {_racio_txt} vezes superior, "
                    "por razões que a metainformação do INE explica. Ver “O que são as Contas "
                    "Nacionais e o que medem”, no separador da metodologia.")
            else:
                _nota_base.append(
                    "A base ativa é a que mede o **consumo no território**, cerca de "
                    f"{_racio_txt} vezes a **despesa das famílias residentes** medida pela outra, "
                    "por razões que a metainformação do INE explica. Ver “O que são as Contas "
                    "Nacionais e o que medem”, no separador da metodologia.")
    else:
        _nota_base.append(
            f"**{euro(media_agregado)}** por mês para o agregado médio, na única base "
            f"disponível. Com as duas bases a aplicação apresentaria um intervalo.")

    # --- período de referência de cada base ---
    # Estava no rótulo do seletor, que dizia “IDF 2022/2023”. Saiu de lá por ser
    # data e não etiqueta, e vem para aqui, incondicionalmente: antes só se via
    # quando a base tinha dois anos ou mais de atraso, e o período de referência
    # é informação que vale sempre, não é um alarme. É também aqui que a sigla é
    # apresentada pela primeira vez, o que licencia o seu uso no resto da
    # aplicação (pedido da Inês, 01.09.2026).
    # Pela ordem de `BASES_ANCORA`, que é a ordem do seletor, e não pela ordem
    # em que as bases foram calculadas, que é a inversa.
    _periodos = " · ".join(
        f"**{ancora['bases'][k]['nome']}**"
        + (" (IDF)" if k == "idf" else "")
        + f", {ancora['bases'][k]['ano_base']}"
        for k in BASES_ANCORA if k in ancora["bases"])
    _nota_base.append(f"Períodos de referência: {_periodos}.")

    # A idade da base tem de estar acessível, não só no registo de ligações: a
    # despesa é atualizada por preços, mas a estrutura de consumo é a do ano de
    # referência (auditoria de 10.08.2026, B2).
    _idade_base = date.today().year - int(base_ancora["ano_fim"])
    if _idade_base >= 2:
        _nota_base.append(
            f"A base ativa tem **{_idade_base} anos de atraso**. Os preços estão "
            "atualizados ao mês corrente; a **estrutura de consumo** é a de "
            f"{base_ancora['ano_base']}.")

    with _slot_nota_base.popover("Sobre esta base", icon=":material/info:"):
        for _n in _nota_base:
            st.markdown(_n)


    # Fora das colunas, a largura toda: um alarme espremido num terço da
    # largura deixa de se ler como alarme, e estes dizem “não use estes
    # números”.
    if not base_ancora.get("plausivel", True):
        st.error(
            f"**A base ativa ({base_ancora['nome']}) está fora do intervalo plausível**, "
            f"{euro(media_agregado)}/mês por agregado. Verifique o registo de ligações "
            "no separador Metodologia. **Os valores apresentados não devem ser utilizados.**"
        )
    elif _outra_suspeita:
        # A base ativa está sã, mas a outra não, e a outra aparece em três
        # sítios: o extremo do intervalo aqui em cima, o “Na outra base seria…”
        # do cartão de topo, e a sensibilidade à base no simulador de IVA.
        st.error(
            f"**A base {outra_ancora['nome']} está fora do intervalo plausível**, "
            f"{euro(outra_ancora['valor'])}/mês por agregado. A base ativa "
            f"(**{base_ancora['nome']}**, {euro(media_agregado)}/mês) não é afetada, mas "
            "**ignore o intervalo, o valor “na outra base” e a sensibilidade à base no "
            "simulador de IVA**, todos consomem esse número. Verifique o registo de "
            "ligações no separador Metodologia."
        )

    if not dim_media:
        st.warning(
            f"**A dimensão média do agregado não foi obtida nesta sessão.** Entra a "
            f"constante de recuo, **{numero(DIMENSAO_RECUO, 1)} pessoas** "
            f"({DIMENSAO_RECUO_FONTE}), que envelhece: a dimensão média está em queda "
            "em toda a Europa. **Todos os valores em euros por agregado dependem deste "
            "número.** Consulte o registo de ligações no separador Metodologia."
        )
    despesa_mensal = despesa_do_agregado(
        media_agregado, dim_efetiva, adultos, criancas, escala_chave)
    faixa = intervalo_agregado(media_agregado, dim_efetiva, adultos, criancas)

    # O rótulo tem de refletir o que a escala mede: pessoas com 14 ou mais anos
    # pesam como adultos, tenham ou não rendimento próprio.
    if criancas:
        composicao = (f"{adultos} com 14+ anos e {criancas} "
                      + ("menores de 14" if criancas > 1 else "menor de 14"))
    else:
        composicao = f"{adultos} pessoa{'s' if adultos > 1 else ''} com 14+ anos"
    pessoas = adultos + criancas
    ue = unidades_equivalentes(adultos, criancas, escala_chave)
    origem = (f"{base_ancora['nome']} · {composicao} · "
              f"escala {ESCALAS[escala_chave]['nome']}")
    vezes_ano = 12

    # Cada expansor vai para dentro da coluna do que explica, e não à
    # largura da página: ocupavam a folha toda para qualificar um
    # controlo que ocupa um terço dela (pedido da Inês, 01.09.2026).
    with _slot_escalas:
        # O grupo “Despesa estimada” repetia na barra lateral o indicador que abre o
        # separador Despesa e composição, mesmo rótulo, mesmo valor, e agora também
        # a mesma posição, logo abaixo. Saiu, e com ele o cabeçalho do grupo: o que
        # resta é o comparador das escalas, que pertence ao seletor de escala logo
        # acima e não existe em mais lado nenhum (decisão da Inês, 13.08.2026).
        with st.expander("Comparar as três escalas"):
            maior_que_media = pessoas > dim_efetiva
            st.dataframe(
                pd.DataFrame([
                    {"Escala": ESCALAS[k]["nome"].split(" (")[0],
                     "Coeficientes": f"{ESCALAS[k]['primeiro']:.0f} / "
                                     f"{ESCALAS[k]['adulto']:.1f} / "
                                     f"{ESCALAS[k]['crianca']:.1f}".replace(".", ","),
                     "Despesa (€)": round(faixa["por_escala"][k], 2)}
                    for k in ESCALAS
                ]), width="stretch", hide_index=True)

            st.markdown(f"""
    **Efeito dos coeficientes da escala sobre o valor apurado**

    O ponto de partida é sempre o **agregado médio português, {('%.2f' % dim_efetiva).replace('.', ',')} pessoas**.
    A escala não calcula a despesa a partir do zero: **ajusta** desse agregado médio para o agregado
    selecionado, e é aplicada aos **dois lados** do cálculo, ao agregado selecionado e ao agregado
    médio que serve de referência.

    Daí resulta o comportamento seguinte:

    | Agregado selecionado | Escala com economias de escala mais fortes |
    |---|---|
    | **Menor** que {('%.2f' % dim_efetiva).replace('.', ',')} pessoas | valor **mais alto** |
    | **Maior** que {('%.2f' % dim_efetiva).replace('.', ',')} pessoas | valor **mais baixo** |

    Coeficientes menores significam que **cada pessoa adicional acresce menos**. Isso comprime as
    diferenças entre agregados de dimensão diferente, aproximando todos da média. Um casal, sendo
    **menor** que a média, aproxima-se dela por cima; um casal com três filhos, sendo **maior**,
    aproxima-se dela por baixo.

    O ponto de viragem é a dimensão média. O agregado selecionado, com {pessoas}
    pessoa{'s' if pessoas > 1 else ''}, situa-se **{'acima' if maior_que_media else 'abaixo'}** dessa dimensão.
            """)
            st.caption(
                "É por esta razão que a aplicação apresenta sempre um intervalo: nenhuma das três "
                "escalas reproduz exatamente a despesa alimentar observada, e a escolha entre elas "
                "altera o resultado em sentidos diferentes consoante a dimensão do agregado."
            )


    with _slot_proveniencia:
        _agr_txt = numero(agregados)
        _mes_txt = mes_pt(ancora["mes"]) if ancora["mes"] else "—"
        _den = base_ancora.get("denominador")
        # O denominador da âncora das Contas Nacionais, independentemente da base
        # escolhida: a Metodologia explica-o sempre, e o `_den` acima é None quando
        # a base ativa é a do IDF, que não passa por divisão nenhuma.
        _den_contas = (ancora["bases"].get("contas") or {}).get("denominador") or {
            "valor": agregados, "ano": dados.get("agregados_ano") or "—"}
        with st.expander("De onde vem este valor"):
            if base_chave == "contas":
                _den_txt = numero(_den["valor"]) if _den else _agr_txt
                _proveniencia = (
                    "Da **despesa alimentar de todas as famílias portuguesas** registada nas Contas "
                    f"Nacionais, dividida pelo número de agregados desse mesmo ano ({_den_txt} em "
                    f"{_den['ano'] if _den else '—'}), atualizada ao mês corrente pelo índice oficial "
                    "de preços e ajustada à composição indicada acima."
                )
            else:
                _proveniencia = (
                    "Da **despesa alimentar declarada pelos agregados** no Inquérito às Despesas das "
                    "Famílias do INE, atualizada ao mês corrente pelo índice oficial de preços e "
                    "ajustada à composição indicada acima. Não passa por divisão de nenhum agregado "
                    "macroeconómico: é medição direta."
                )
            if base_chave == "contas" and _den:
                _linha_agr = (f"**Denominador:** {_den['fonte']}, {_den['ano']}, "
                              "o mesmo ano da despesa")
                if _den["desfasamento"]:
                    _linha_agr = (f"**Denominador:** {_den['fonte']}, {_den['ano']}, "
                                  f"**{_den['desfasamento']} ano(s) de desfasamento** face à "
                                  f"despesa, que é de {base_ancora['ano_base']}")
            else:
                _linha_agr = f"**N.º de agregados:** {agr_fonte}"
            st.markdown(
                _proveniencia + "\n\n"
                + _linha_agr + "  \n"
                + f"**Base de despesa:** {base_ancora['nome']} ({base_ancora['ano_base']}), "
                f"a preços de {_mes_txt}  \n"
                f"**Fonte:** {base_ancora['fonte']}\n\n"
                f"*{base_ancora['porque']}*\n\n"
                + (f"Na outra base, {outra_ancora['nome']}, o mesmo agregado médio daria "
                   f"**{euro(outra_ancora['valor'])}** por mês."
                   if outra_ancora is not None else
                   "A outra base oficial não está disponível nesta sessão, pelo que não há "
                   "intervalo a apresentar.")
            )


# --- decomposição base, usada por vários separadores ---
df_decomp = decompor(despesa_mensal, dados["pesos"], dados["variacoes_classe"])
resumo = resumo_decomposicao(df_decomp, despesa_mensal)

# Cobertura da decomposição. Faltando um ponderador, as restantes classes
# absorvem 100% da despesa e cada quota sai inflacionada, sem aviso nenhum
# (auditoria de 11.08.2026, E10). Declara-se, como já se fazia no Törnqvist.
_sem_peso = df_decomp.attrs.get("classes_sem_ponderador") or []
_sem_var = df_decomp.attrs.get("classes_sem_variacao") or []


def _nomes_classes(codigos):
    return ", ".join(POR_CODIGO[c]["nome"] for c in codigos if c in POR_CODIGO)


# Escritas no contentor reservado lá em cima, e não aqui: o alarme pertence ao
# topo da página, acima das abas, porque afeta os valores de todos os
# separadores. O que desceu foi a execução, não o sítio onde aparece.
with _slot_cobertura:
    if _sem_peso:
        st.error(
            f"**{len(_sem_peso)} das nove classes não têm ponderador nesta sessão**, "
            f"{_nomes_classes(_sem_peso)}. A despesa foi repartida apenas pelas "
            f"restantes {9 - len(_sem_peso)}, pelo que **todas as quotas e todos os "
            "valores em euros estão sobrestimados**. Consulte o registo de ligações "
            "no separador Metodologia."
        )
    elif _sem_var:
        st.warning(
            f"**{len(_sem_var)} das nove classes não têm variação homóloga nesta "
            f"sessão**, {_nomes_classes(_sem_var)}. As quotas e os valores em euros "
            "não são afetados; o **agravamento dos últimos 12 meses** é o das classes "
            "com dados, e fica por isso subestimado."
        )


# ==========================================================================
# ABA D, Evolução do cabaz
# ==========================================================================
with abaD:
    with painel("Evolução do cabaz"):
        titulo_pagina(
            "Evolução do cabaz essencial (DECO PROteste)",
            "Preço de uma cesta de 63 bens alimentares essenciais, de composição fixa, "
            "seguida pela DECO PROteste desde janeiro de 2022. Não é o indicador que esta "
            "aplicação calcula, é uma referência externa e privada, que complementa a "
            "leitura da despesa alimentar apresentada nos restantes separadores.")

        _serie_deco, _top10_deco, _meta_deco = deco.carregar()

        if _serie_deco.empty:
            st.warning(
                "**Sem dados recolhidos.** A DECO PROteste não tem API pública: a série é "
                "obtida por `scripts/recolher_deco.py`, que escreve `dados/deco_cabaz.csv`. "
                "Execute o script para preencher este separador."
            )
        else:
            _var_deco = deco.variacoes(_serie_deco)
            _sv = _var_deco["semana_anterior"]
            _dj = _var_deco["desde_ano_corrente"]
            _di = _var_deco["desde_inicio"]

            _fresc_deco = frescura_do_observatorio(
                _var_deco["atual"]["data"], _meta_deco.get("extraido_em"),
                LIMITE_DIAS_DECO, cadencia_dias=7)
            if _fresc_deco["parada"]:
                st.warning(
                    f"**Este valor tem mais de {numero(LIMITE_DIAS_DECO)} dias.** "
                    "A DECO publica semanalmente, às quartas-feiras; confirme antes de o "
                    "citar como situação corrente."
                )

            indicador_principal(
                "Cabaz essencial DECO PROteste",
                euro(_var_deco["atual"]["valor"]),
                contexto=(f"Semana de {_var_deco['atual']['data'].strftime('%d/%m/%Y')} "
                          "· 63 bens alimentares essenciais, composição fixa"),
                sec_valor=(percentagem(_sv["delta_pct"])
                           if _sv.get("delta_pct") is not None else None),
                sec_rotulo="face à semana anterior",
                sec_cor=(None if _sv.get("delta_pct") is None
                         else (VERMELHO if _sv["delta_pct"] > 0 else VERDE)))

            nota("Não é o indicador desta aplicação", f"""
                A DECO PROteste soma o <strong>preço absoluto</strong> de uma lista fixa de
                63 produtos, sem ponderação pelo consumo real das famílias e sem cobrir o
                comércio tradicional. A <strong>despesa alimentar</strong>, que é o que os
                restantes separadores medem, reparte a despesa efetiva das famílias pelos
                grupos de produtos, com base no índice de preços do INE/Eurostat. Ver
                “Distinção entre despesa alimentar e cabaz”, no separador
                Metodologia. Fonte: <a href="{_meta_deco.get('endereco', '#')}"
                target="_blank" rel="noopener noreferrer">{_meta_deco.get('fonte',
                'DECO PROteste')}</a>, extraído em {_meta_deco.get('extraido_em', '—')}.""")

            secao("Evolução desde 2022",
                  f"Preço semanal do cabaz, de {_di['data'].strftime('%d/%m/%Y')} a "
                  f"{_var_deco['atual']['data'].strftime('%d/%m/%Y')}.",
                  grupo="01 · Evolução do cabaz")

            d1, d2, d3 = st.columns(3)
            d1.metric("Semana anterior", euro(_sv["valor"]),
                      delta=(f"{euro(_sv['delta'])} ({percentagem(_sv['delta_pct'])})"
                             if _sv.get("delta_pct") is not None else None),
                      delta_color="inverse")
            d2.metric(f"Primeira semana de {_dj['data'].year}", euro(_dj["valor"]),
                      delta=(f"{euro(_dj['delta'])} ({percentagem(_dj['delta_pct'])})"
                             if _dj.get("delta_pct") is not None else None),
                      delta_color="inverse")
            d3.metric(f"Início da série ({_di['data'].strftime('%m/%Y')})", euro(_di["valor"]),
                      delta=(f"{euro(_di['delta'])} ({percentagem(_di['delta_pct'])})"
                             if _di.get("delta_pct") is not None else None),
                      delta_color="inverse")

            figD = go.Figure()
            figD.add_trace(go.Scatter(
                x=_serie_deco["data"], y=_serie_deco["valor"], mode="lines",
                line=dict(color=VERMELHO, width=2.5),
                fill="tozeroy", fillcolor="rgba(208,33,23,0.08)",
                hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f} €<extra></extra>"))
            figD.update_layout(
                height=420, margin=dict(t=12, b=10, l=10, r=10),
                yaxis_title="Preço do cabaz (€)")
            grafico(figD)

            st.download_button(
                "Descarregar série do cabaz DECO (CSV com fonte)",
                csv_com_fonte(
                    _serie_deco.rename(columns={"data": "Data", "valor": "Preço do cabaz (€)"}),
                    "Cabaz essencial DECO PROteste, série desde 2022", dados,
                    fonte=_meta_deco.get("fonte", "DECO PROteste"),
                    conjuntos=["DECO PROteste"],
                    extra=[("Endereço", _meta_deco.get("endereco", "-")),
                           ("Extraído em", _meta_deco.get("extraido_em", "-"))]),
                "deco_cabaz.csv", "text/csv")

            secao("Produtos que mais aumentaram",
                  "Três janelas de comparação: a última semana, desde a primeira semana "
                  "do ano corrente, e desde o início da monitorização em 2022.",
                  grupo="02 · Produtos")

            if _top10_deco.empty:
                st.info("Sem tabelas de produtos nesta recolha.")
            else:
                _rotulos_top10 = {
                    "semanal": "Última semana",
                    "desde_janeiro": f"Desde janeiro de {_dj['data'].year}",
                    "desde_2022": "Desde 2022",
                }
                _disponiveis = [c for c in _rotulos_top10
                                if c in set(_top10_deco["tabela"])]
                _subabas = st.tabs([_rotulos_top10[c] for c in _disponiveis])
                for _chave, _sub in zip(_disponiveis, _subabas):
                    with _sub:
                        _t = (_top10_deco[_top10_deco["tabela"] == _chave]
                              .sort_values("aumento_pct", ascending=True))
                        _custom = list(zip(
                            _t["preco_atual"].astype(float),
                            _t["unidade_preco"], _t["aumento_valor"].astype(float)))
                        figT = go.Figure(go.Bar(
                            y=_t["produto"], x=_t["aumento_pct"], orientation="h",
                            marker_color=VERMELHO, customdata=_custom,
                            hovertemplate="<b>%{y}</b><br>+%{x:.0f}%"
                                          "<br>Preço atual: %{customdata[0]:.2f} %{customdata[1]}"
                                          "<br>Aumento: +%{customdata[2]:.2f} €"
                                          "<extra></extra>"))
                        figT.update_layout(
                            height=max(320, 36 * len(_t)),
                            margin=dict(t=12, b=10, l=10, r=10),
                            xaxis_title="Aumento (%)")
                        grafico(figT)

                st.download_button(
                    "Descarregar produtos com maior aumento (CSV com fonte)",
                    csv_com_fonte(
                        _top10_deco.rename(columns={
                            "tabela": "Janela", "produto": "Produto",
                            "preco_atual": "Preço atual", "unidade_preco": "Unidade",
                            "aumento_valor": "Aumento (€)", "aumento_pct": "Aumento (%)"}),
                        "Produtos com maior aumento, DECO PROteste", dados,
                        fonte=_meta_deco.get("fonte", "DECO PROteste"),
                        conjuntos=["DECO PROteste"],
                        extra=[("Endereço", _meta_deco.get("endereco", "-")),
                               ("Extraído em", _meta_deco.get("extraido_em", "-"))]),
                    "deco_top10.csv", "text/csv")

# ==========================================================================
# ABA 1, Despesa e composição
# ==========================================================================
with aba1:
    with painel("Despesa e composição"):
        # O título da página está escrito lá em cima, antes dos parâmetros, que
        # é onde tem de aparecer. Aqui continua o resto do separador.
        #
        # Sem o mês: o indicador de capa, logo a seguir, di-lo em corpo grande.
        faixa_fonte(mes=False)

        # ---- grandezas da variação, apuradas antes de se desenhar o que quer
        # que seja: o indicador de capa e o indicador secundário do agravamento
        # consomem exatamente as mesmas, e o de capa vem primeiro na página.
        #
        # A taxa apresentada é a **oficial** do CP011, e não a reconstituída da
        # decomposição. Decisão da Inês, 12.08.2026 (auditoria, K1).
        _var_of = dados.get("variacao_oficial")
        _taxa_capa = (_var_of if _var_of is not None
                      else resumo.get("variacao_implicita"))
        # Os rótulos e as cores seguem o **sinal**. A inflação alimentar já foi
        # negativa em Portugal (auditoria de 12.08.2026, M2).
        _desce = (resumo["contributo_total"] < 0
                  if resumo["contributo_total"] is not None else False)

        # ---- o número da página ----
        # Antes era o primeiro de uma fila de cinco indicadores do mesmo
        # tamanho, a meio da página. É o valor a que toda a aplicação se
        # refere: passa a abrir o separador e a dominá-lo. A proveniência
        # (base, composição, escala) estava num *tooltip* e passa a estar à
        # vista, que é onde tem de estar num documento que se cita.
        indicador_principal(
            "Despesa alimentar mensal",
            euro(despesa_mensal),
            contexto=f"{origem} · a preços de <strong>{mes_pt(ultimo_mes)}</strong>",
            sec_valor=(percentagem(_taxa_capa) if _taxa_capa is not None else None),
            sec_rotulo="variação homóloga",
            sec_cor=(None if _taxa_capa is None
                     else (VERDE if _taxa_capa < 0 else VERMELHO)))

        # Primeiro o país, depois o agregado escolhido. A ordem estava invertida:
        # a página abria com os valores já ajustados à barra lateral e só no fim
        # mostrava a referência nacional de que eles derivam, apesar de o próprio
        # texto dessa referência lhe chamar “o ponto de partida do cálculo”
        # (decisão da Inês, 13.08.2026).
        secao("Referência nacional",
              "O agregado médio português, antes de qualquer ajustamento. É deste "
              "valor que parte o cálculo dos indicadores ajustados, mais abaixo.",
              grupo="02 · Referência nacional")
        dim_txt = ('%.1f' % dim_efetiva).replace('.', ',')
        r1, r2, r3 = st.columns([1, 1, 2])
        r1.metric(f"Agregado médio nacional ({dim_txt} pessoas)",
                  euro(valor_medio_agregado),
                  help=(f"Base {base_ancora['nome']}. "
                        + (f"Na outra base seria {euro(outra_ancora['valor'])}. "
                           if outra_ancora is not None else
                           "A outra base não está disponível nesta sessão. ")
                        + "Valor de referência antes de qualquer ajustamento de composição."))
        r2.metric("Equivalente anual (agregado médio)", euro(valor_medio_agregado * 12))
        eng_pt = (dados.get("engel") or {}).get("PT")
        _eng = intervalo_engel(eng_pt)

        if eng_pt:
            # Intervalo, e não ponto: as duas bases oficiais divergem, e é a
            # mesma divergência que já leva a âncora a ser apresentada como
            # intervalo. O extremo inferior é o número do INE que aparece na
            # tabela por quintil logo abaixo (auditoria de 10.08.2026, B4).
            r3.metric("Peso da alimentação na despesa total",
                      f"{percentagem(_eng['minimo'], sinal=False)} a {percentagem(_eng['maximo'], sinal=False)}",
                      help=("Coeficiente de Engel nas duas bases oficiais: "
                            f"{percentagem(_eng['idf'], sinal=False)} no Inquérito às Despesas "
                            "das Famílias de 2022/2023 (agregados residentes) "
                            f"e {percentagem(_eng['contas'], sinal=False)} nas Contas Nacionais de "
                            f"{_eng['ano_contas']} (conceito macroeconómico). Divergem "
                            "porque a despesa alimentar por agregado difere entre bases "
                            "mais do que a despesa total, o mesmo motivo por que a "
                            "âncora é um intervalo. O limite inferior é o valor que "
                            "consta da tabela por quintil, mais abaixo. Comparação "
                            "europeia no separador UE-27, que usa as Contas Nacionais "
                            "por serem a única base comparável entre países."))
        else:
            r3.markdown(
            f"<p class='sg-comp__d' style='padding-top:14px'>"
            f"É este o ponto de partida do cálculo: a despesa alimentar de um agregado "
            f"com a dimensão média portuguesa ({dim_txt} pessoas). Os valores mais abaixo "
            f"estão ajustados para <strong>{composicao}</strong>.</p>",
            unsafe_allow_html=True)

        # Fora das colunas, e por duas razões. A visual: dentro da terceira, o
        # cartão parava onde ela começava e a fila desalinhava na base, porque a
        # regra que estica os cartões só age quando o indicador é filho único da
        # coluna. Tentei corrigi-lo por CSS e não pegou, o contentor é desenhado
        # por um mecanismo próprio do Streamlit que a folha de autor não vence.
        #
        # A editorial, que é a que a justifica mesmo: estas são as duas bases em
        # que assentam **os três** cartões, e não só o do coeficiente de Engel.
        # Uma nota só contextualiza o bloco inteiro (relatado pela Inês,
        # 01.09.2026).
        if eng_pt:
            st.caption(f"Inquérito às Despesas das Famílias 2022/2023 · Contas "
                       f"Nacionais {_eng['ano_contas']}, ver Metodologia")

        if outra_ancora is not None:
            nota("O valor exato não é determinável, use o intervalo", f"""
          As duas fontes oficiais que medem a despesa alimentar das famílias não coincidem.
          Para o agregado médio, a despesa mensal situa-se entre
          <strong>{euro(ancora['minimo'])}</strong> e <strong>{euro(ancora['maximo'])}</strong>,
          consoante se use o inquérito às despesas ou as Contas Nacionais. O ponto central
          <strong>não é determinável</strong>: o inquérito subestima e as Contas Nacionais
          sobrestimam, e não existe exercício de conciliação que permita arbitrar.
          Os valores desta página usam a base <strong>{base_ancora['nome']}</strong>,
          escolhida no bloco acima. Ver separador Metodologia.""")
        else:
            nota("Uma só base, não há intervalo nesta sessão", f"""
          A aplicação apresenta normalmente a despesa como um <strong>intervalo</strong> entre as
          duas fontes oficiais, que divergem por um fator próximo de 2. Nesta sessão só a base
          <strong>{base_ancora['nome']}</strong> está disponível, pelo que os valores desta página são
          um <strong>ponto de uma só base</strong> e não devem ser lidos como o valor central de
          nada. Ver o registo de ligações no separador Metodologia.""", alerta=True)

        secao(f"Ajustado ao agregado selecionado ({composicao})",
              "Os mesmos dados aplicados à composição escolhida no bloco acima. "
              "A despesa mensal é a que abre o separador; estes indicadores "
              "qualificam-na. A escala de equivalência está no separador Metodologia.",
              grupo="03 · O agregado selecionado")
        # Quatro indicadores, e não cinco: a despesa mensal saiu daqui para o
        # indicador de capa, no topo da página, onde ocupa o lugar que o seu
        # peso na aplicação justifica. O rótulo e o *tooltip* que tinha (a
        # proveniência, em `origem`) acompanharam-na.
        colunas = st.columns(4)
        if resumo["contributo_total"] is not None:
            # A percentagem é uma **taxa de variação de preços** e não depende da
            # base de despesa: mudar de IDF para Contas Nacionais muda os euros,
            # não a taxa. Sem esta nota parece que a app ignorou a mudança de base
            # (relatado pela utilizadora, 12.08.2026).
            _nota_taxa = ("A percentagem é uma **taxa de variação de preços**, vem do índice "
                          "e dos ponderadores, não do nível de despesa. Por isso **não muda** "
                          "quando troca a base entre IDF e Contas Nacionais: o que muda é o "
                          "valor em euros, porque a mesma taxa aplicada a uma despesa maior "
                          "dá mais euros.")
            # A taxa de capa (`_taxa_capa`) é a **oficial** do CP011 e foi
            # apurada no topo do separador, porque o indicador principal a
            # consome antes deste. Numa ferramenta que vai apoiar o Gabinete em
            # debate público, o número de capa tem de ser o que qualquer pessoa
            # pode ir verificar ao INE: um número que não bate certo com o
            # publicado é fácil de atacar e difícil de neutralizar, e o risco
            # reputacional é assimétrico.
            #
            # Os euros continuam a ser a **soma dos nove contributos**, que é a
            # propriedade que a decomposição promete e que está travada por
            # teste. As duas grandezas correspondem a taxas ligeiramente
            # diferentes, e é isso que o tooltip diz, e a legenda por baixo dos
            # gráficos de decomposição.
            _nota_capa = ""
            if _var_of is not None and resumo["variacao_implicita"] is not None:
                _nota_capa = (
                    f"\n\n**A percentagem é a taxa oficial** do agregado alimentar "
                    f"({mes_pt(dados.get('mes_variacao_oficial'))}), o número "
                    "publicado pelo INE, que se pode verificar diretamente na fonte. "
                    "**Os euros são a soma dos nove contributos** apresentados abaixo, "
                    "que corresponde a "
                    f"{percentagem(resumo['variacao_implicita'], sinal=False)}: essa "
                    "agregação pondera as nove taxas pelos valores de há um ano, e a "
                    "oficial pelos do período corrente. A diferença é de décimas de "
                    "ponto, ver a nota sob os gráficos.")
            # `_desce` foi apurado no topo do separador, pela mesma razão de
            # `_taxa_capa`. Os rótulos seguem o **sinal**: a inflação alimentar
            # já foi negativa em Portugal, e nesse caso o cartão anunciava um
            # “Agravamento” de −9,79 € e um “Maior contributo” que era, na
            # verdade, a classe que menos contribuiu para a descida
            # (auditoria de 12.08.2026, M2).
            _rot_agr = ("Alívio nos últimos 12 meses" if _desce
                        else "Agravamento nos últimos 12 meses")
            _verbo_agr = "Descida" if _desce else "Subida"
            colunas[0].metric(_rot_agr, euro(abs(resumo["contributo_total"])),
                              percentagem(_taxa_capa),
                              help=f"{_verbo_agr} da despesa alimentar face ao mesmo mês do ano "
                                   f"anterior, à composição de consumo atual. {_nota_taxa}"
                                   f"{_nota_capa}")
            colunas[1].metric("Despesa há 12 meses", euro(resumo["valor_ha_um_ano"]),
                              help="A mesma despesa deflacionada pela variação homóloga de "
                                   "cada classe. Escala com a base escolhida.")
            if resumo["maior"]:
                maior = resumo["maior"]
                # `resumo_decomposicao` devolve a classe de maior contributo em
                # **valor absoluto**; o rótulo diz em que sentido pesou.
                _rot_maior = ("Maior alívio" if maior["contributo"] < 0
                              else "Maior contributo")
                colunas[2].metric(f"{_rot_maior} ({maior['classe']})",
                                  euro(abs(maior["contributo"])),
                                  percentagem(maior["variacao"]),
                                  help=f"A classe que mais pesou {'na descida' if _desce else 'no agravamento'}"
                                       ", em euros, combinando a sua variação de preços com o "
                                       f"seu peso no cabaz. {_nota_taxa}")
        colunas[3].metric(f"Equivalente anual ({composicao})",
                          euro(despesa_mensal * vezes_ano),
                          help=f"Despesa mensal × {vezes_ano}. Mesma base e mesma "
                               f"composição: {origem}.")

        # ---- esforço do agregado escolhido ----
        # O `st.divider()` que aqui estava saiu: pertence ao mesmo bloco
        # analítico da secção anterior (o agregado selecionado), e o filete de
        # bloco já separa o que tem de ser separado. Dois traços seguidos a
        # dividir níveis diferentes anulam-se um ao outro.
        #
        # A página dá três números que o leitor arruma todos como “peso no
        # orçamento”, o coeficiente de Engel no topo, o peso por quintil mais
        # abaixo, e este. Os denominadores são diferentes, e o quadro
        # que os distingue está no separador UE-27, que pode nunca ser aberto.
        # A distinção passa a ser feita onde a confusão acontece.
        secao(f"Quanto pesa no orçamento ({composicao})",
              "<strong>Aqui o denominador é o rendimento, não a despesa.</strong> "
              "O coeficiente de Engel, em cima, e o peso no orçamento por quintil, "
              "mais abaixo, repartem o que as famílias <em>gastam</em>. Esta mede "
              "quanto do que <em>recebem</em> é absorvido pela alimentação, e é a única "
              "<strong>das três</strong> que responde à composição escolhida no topo "
              "deste separador.",
              ajuda=("Estes valores são **limites superiores**, a despesa e o rendimento "
                     "vêm de fontes com bases estatísticas diferentes, e combiná-las "
                     "sobrestima o esforço. Leia as **diferenças entre composições** e a "
                     "**direção** como informativas, e o **nível** como majorante. O "
                     "desenvolvimento está em “Pressupostos subjacentes a estes valores”, "
                     "no separador Metodologia."))

        rendimentos = dados.get("rendimento") or {}
        sm_pt = (dados.get("salario") or {}).get("PT")
        sme_pt = (dados.get("salario_medio") or {}).get("PT")
        tem_rend = any(rendimentos.get(k, {}).get("PT")
                       for k in eurostat.RENDIMENTO_INDICADORES)

        # O indicador de rendimento em uso e o rácio Contas Nacionais/EU-SILC
        # eram apurados **dentro** do ramo que desenha esta secção. O separador
        # Metodologia passou a consumi-los, e lá não há ramo nenhum a garanti-los:
        # numa sessão sem EU-SILC a aplicação rebentaria com NameError. Sobem
        # para aqui, onde correm sempre (13.08.2026).
        indic_r = None
        if tem_rend:
            _disp_r = [k for k in eurostat.RENDIMENTO_INDICADORES
                       if rendimentos.get(k, {}).get("PT")]
            indic_r = "MEAN_EI" if "MEAN_EI" in _disp_r else _disp_r[0]
        # O rácio entre consumo total das Contas Nacionais por agregado e
        # rendimento do EU-SILC estava **inscrito à mão** como “cerca de 1,8
        # vezes”. Com o `nama_10_cp18` de 2024 e o EU-SILC de 2025 são hoje
        # cerca de 1,5, o número tinha ficado para trás, num bloco que a
        # própria aplicação rotula “leitura obrigatória”
        # (auditoria de 12.08.2026, L3). Passa a ser calculado.
        _racio_cn_silc = None
        _eng_cn = (dados.get("engel") or {}).get("PT")
        if base_chave == "contas" and _eng_cn and tem_rend and indic_r:
            _den_cn = agregados_do_ano(dados.get("agregados_serie") or {},
                                       _eng_cn["ano"])
            _consumo_mes = _eng_cn["total"] * 1e6 / _den_cn["valor"] / 12
            _ue_medio = unidades_equivalentes(
                max(int(round(dim_efetiva)), 1), 0, "ocde_modificada")
            _rend_mes_medio = rendimentos[indic_r]["PT"]["valor"] * _ue_medio / 12
            if _rend_mes_medio > 0:
                _racio_cn_silc = _consumo_mes / _rend_mes_medio


        if not tem_rend and not sm_pt and not sme_pt:
            st.info(
                "Os indicadores de rendimento não estão disponíveis nesta sessão. "
                "Consulte o registo de ligações no separador Metodologia."
            )
        else:
            # A coluna do contador estreita com ele: com o campo limitado a
            # 9rem, um terço da largura deixava um vazio entre o contador e o
            # texto que o qualifica, e os dois lêem-se como um só bloco.
            #
            # Um sexto, e não um quarto: a um quarto o vazio continuava grande
            # de mais (Inês, 20.08.2026). Abaixo disto o rótulo do contador
            # deixa de caber numa linha, que é o que fixa o limite.
            ca_, cb_ = st.columns([1, 5])
            with ca_:
                trabalhadores = st.number_input(
                    "Quantos auferem rendimento", min_value=1, max_value=int(adultos),
                    value=min(int(adultos), 2), step=1,
                    help=("Das pessoas com 14 ou mais anos, quantas auferem "
                          "efetivamente rendimento. Jovens dependentes, estudantes "
                          "e pessoas sem rendimento próprio não contam, mas "
                          "continuam a pesar na despesa alimentar."),
                )
                dependentes = int(adultos) - int(trabalhadores)
            with cb_:
                st.markdown(
                    f"<p class='sg-comp__d' style='padding-top:26px'>"
                    f"<strong>{pessoas}</strong> pessoa{'s' if pessoas > 1 else ''} a "
                    f"alimentar · <strong>{trabalhadores}</strong> "
                    + ("auferem" if trabalhadores > 1 else "aufere")
                    + " rendimento"
                    + (f" · <strong>{dependentes}</strong> com 14+ anos sem rendimento próprio"
                       if dependentes else "")
                    + (f" · <strong>{criancas}</strong> com menos de 14 anos"
                       if criancas else "")
                    + f"<br>Despesa alimentar mensal: <strong>{euro(despesa_mensal)}</strong>."
                    "</p>",
                    unsafe_allow_html=True)

                if dependentes:
                    st.warning(f"""
    **{dependentes} pessoa{'s' if dependentes > 1 else ''} com 14 ou mais anos sem rendimento
    próprio.** A escala de equivalência atribui a adolescentes, estudantes e outros dependentes
    **a mesma ponderação alimentar de um adulto**, mas estes **não auferem rendimento**. É a
    composição em que o esforço alimentar é mais elevado e a que os indicadores médios menos
    evidenciam.
                    """)

            # --- construir as referências disponíveis ---
            refs = []
            if tem_rend:
                r = rendimentos[indic_r]["PT"]
                ue_ocde = unidades_equivalentes(adultos, criancas, "ocde_modificada")
                refs.append({
                    "ref": "Rendimento das famílias (EU-SILC)",
                    "detalhe": (f"{'Médio' if indic_r == 'MEAN_EI' else 'Mediano'} equivalente "
                                f"{r['ano']} × {('%.2f' % ue_ocde).replace('.', ',')} unidades. "
                                "Estatísticas do Rendimento e Condições de Vida (EU-SILC)"),
                    "mensal": r["valor"] * ue_ocde / 12,
                    "natureza": "líquido",
                })
            if sme_pt:
                refs.append({
                    "ref": f"{trabalhadores} × salário médio",
                    # Sem `**`: vai para uma célula da coluna “Detalhe”, e um
                    # quadro de dados não interpreta markdown nenhum.
                    "detalhe": (f"Massa salarial ÷ trabalhadores por conta de outrem, "
                                f"{sme_pt['ano']}; inclui tempo parcial, pelo que fica "
                                "abaixo do salário de um trabalhador a tempo inteiro"),
                    "mensal": sme_pt["valor"] * trabalhadores / 12,
                    "natureza": "bruto",
                })
            if sm_pt:
                # O Eurostat publica a RMMG em duodécimos de 14 mensalidades:
                # o valor difundido é o legal × 14/12. Para a fatia mensal do
                # orçamento é essa a base certa, distribui os subsídios pelos
                # 12 meses. Mas não é o valor legal, e rotulá-lo como tal
                # sobrestimava o rendimento em 16,7% (auditoria, A2). A RMMG é
                # fixada em euros inteiros, daí o arredondamento.
                rmmg_legal = round(sm_pt["valor"] * 12 / 14)
                refs.append({
                    "ref": f"{trabalhadores} × salário mínimo",
                    "detalhe": (f"Média mensal bruta de 14 mensalidades, {sm_pt['periodo']}; "
                                "o valor legal da retribuição mínima mensal garantida "
                                f"(RMMG) é de {rmmg_legal} €/mês"),
                    "mensal": sm_pt["valor"] * trabalhadores,
                    "natureza": "bruto",
                })

            for r in refs:
                r["esforco"] = despesa_mensal / r["mensal"] * 100 if r["mensal"] else None

            tab_r = pd.DataFrame([{
                "Referência": r["ref"],
                "Rendimento mensal": euro(r["mensal"]),
                "Esforço alimentar": (f"{r['esforco']:.1f}%".replace(".", ",")
                                      if r["esforco"] is not None else "—"),
                "Natureza": r["natureza"],
                "Detalhe": r["detalhe"],
            } for r in refs])

            # A tabela dizia os mesmos três números que o gráfico logo a seguir.
            # Fica o gráfico à vista (responde a “quanto”) e a tabela desce para
            # um expander, porque o que ela acrescenta são as colunas “Natureza” e
            # “Detalhe”, que respondem a “como se obteve” (Inês, 13.08.2026).
            #
            # O gráfico formatava `None` diretamente e rebentava com TypeError
            # (auditoria de 12.08.2026, L14).
            figR = go.Figure(go.Bar(
                y=[r["ref"] for r in refs],
                x=[r["esforco"] for r in refs], orientation="h",
                marker_color=[VERDE if r["natureza"] == "líquido" else DOURADO
                              for r in refs],
                text=[percentagem(r["esforco"], sinal=False) for r in refs],
                textposition="outside",
                hovertemplate="%{y}: %{x:.1f}% do rendimento<extra></extra>"))
            figR.update_layout(height=max(270, 74 * len(refs)),
                               margin=dict(t=22, b=42, l=10, r=72),
                               xaxis_title="Proporção do rendimento absorvida pela alimentação (%)",
                               showlegend=False)
            grafico(figR)

            # A legenda das cores sobe para debaixo do gráfico: é a única das três
            # que o leitor tem de ler para interpretar o que está a ver.
            st.caption(
                "**Verde:** rendimento **líquido**, depois de impostos e contribuições. "
                "**Dourado:** valores **brutos**, salário médio e salário mínimo, antes de "
                "descontos. O rendimento efetivamente disponível é inferior, pelo que o esforço "
                "real sobre eles é **superior** ao apresentado. Verde e dourado não são "
                "diretamente comparáveis entre si."
            )

            with st.expander("De onde vem cada referência"):
                st.dataframe(tab_r, width="stretch", hide_index=True)

        # ---- onde está concentrado o aumento ----
        # “Contributo” e não “o que está a pesar mais”: é a palavra que os cartões
        # e a tabela detalhada já usam para exatamente este número. O mesmo
        # conceito tinha três nomes ao longo do separador (Inês, 13.08.2026).
        #
        # A aditividade é a propriedade central da decomposição, e continua a
        # valer, mas a taxa que ela implica não é exatamente a oficial que está
        # na capa. Isso tem de estar escrito onde os contributos aparecem
        # (auditoria de 12.08.2026, K1). Estava numa legenda de treze linhas por
        # baixo do gráfico; passa para o (i) do título, que é onde a encontra
        # quem a procura e onde não estorva quem não a procura
        # (decisão da Inês, 13.08.2026).
        _ajuda_adit = None
        if (resumo["contributo_total"] is not None
                and resumo["variacao_implicita"] is not None
                and dados.get("variacao_oficial") is not None):
            _dif_k1 = dados["variacao_oficial"] - resumo["variacao_implicita"]
            _ajuda_adit = (
                f"**Os nove contributos somam exatamente "
                f"{euro(resumo['contributo_total'])}**, é a propriedade que esta "
                "decomposição garante, e está verificada por teste automático. Essa "
                f"soma corresponde a uma {'descida' if _desce else 'subida'} de "
                f"**{percentagem(abs(resumo['variacao_implicita']), sinal=False)}**, "
                f"enquanto o índice oficial do agregado alimentar regista "
                f"**{percentagem(dados['variacao_oficial'], sinal=False)}** em "
                f"{mes_pt(dados.get('mes_variacao_oficial'))}, uma diferença de "
                f"{pontos(abs(_dif_k1), casas=2, sinal=False)}\n\n"
                "**Não é discrepância: são duas agregações da mesma coisa.** Para os "
                "nove contributos somarem ao total, a taxa que deles resulta pondera "
                "as nove classes pelos seus valores **de há um ano**; a oficial "
                "pondera-as pelos do **período corrente**. Verificado: ponderando "
                "pelos valores correntes obtêm-se "
                f"{percentagem(sum(r.quota * r.variacao for r in df_decomp.itertuples() if r.variacao is not None), sinal=False)}, "
                "que reproduz a oficial. Sobre 90 meses de série, a diferença tem "
                "média absoluta de 0,15 p.p. e nunca chegou a 1 p.p. **A percentagem "
                "no indicador de topo é a oficial**, para que seja verificável na "
                "fonte; os euros são os desta decomposição."
            )
        # “Últimos 12 meses” não dizia de que doze meses se tratava. A janela
        # passa a ser nomeada pelos dois extremos, aqui e no detalhe por grupo.
        _janela = (f"de {mes_homologo(ultimo_mes)} para {mes_extenso(ultimo_mes)}"
                   if ultimo_mes and ultimo_mes != "—" else "nos últimos 12 meses")
        # Calculado uma vez para as duas secções que o usam, e fora do `if` do
        # gráfico: se os contributos não tiverem dados, os cartões continuam a
        # aparecer e a nota tem de existir na mesma.
        _desal_nota = nota_desalinhamento(dados)
        secao("Contributo de cada grupo para a variação homóloga",
              f"Euros de variação <strong>{_janela}</strong> atribuíveis a cada "
              "grupo, positivos à direita, negativos à esquerda.",
              ajuda=_ajuda_adit, grupo="04 · Onde está a variação")
        com_dados = df_decomp.dropna(subset=["contributo"]).sort_values("contributo")
        if com_dados.empty:
            st.info("Sem variações disponíveis para o período.")
        else:
            fig = go.Figure(go.Bar(
                y=list(com_dados["classe"]),
                x=com_dados["contributo"], orientation="h",
                marker_color=[VERMELHO if v > 0 else VERDE for v in com_dados["contributo"]],
                hovertemplate="%{y}<br>%{x:.2f} €<extra></extra>",
            ))
            fig.update_layout(height=max(450, 45 * len(com_dados)),
                              margin=dict(t=12, b=42, l=10, r=20),
                              xaxis_title="Euros por mês")
            # O zero é a leitura central deste gráfico, separa quem agrava de
            # quem alivia, e vinha com o mesmo peso das linhas de grelha.
            fig.update_xaxes(zeroline=True, zerolinecolor=TEXTO_3, zerolinewidth=1.5)
            grafico(fig, rodape=carimbo_do_grafico(dados,
                                                   mes_indice=ancora.get("mes")))
            st.caption("Vermelho: grupos que encareceram e agravam a despesa. "
                       "Verde: grupos que baixaram e a aliviam. A linha vertical "
                       "marca o zero.")
            st.caption(base_de_calculo(dados, base_ancora,
                                       mes_indice=ancora.get("mes")))
            # O aviso de desalinhamento esteve aqui, e saiu a 01.09.2026. Estava
            # a ser dito três vezes na mesma página: por inteiro no topo, com a
            # lista das classes e os meses de cada uma, aqui, e outra vez nos
            # cartões cinquenta linhas abaixo. Ficou o dos cartões, que é onde
            # mais engana: ali cada classe mostra a sua taxa isolada, e uma
            # classe de outro mês passa por comparável com as vizinhas. Nestas
            # barras seria a terceira legenda seguida sob o mesmo gráfico
            # (decisão da Inês).

        # ---- composição da despesa ----
        # A caixa que estava à direita do donut explicava os **cartões**, dizia-o
        # ela própria, “mais abaixo”, e não o gráfico que acompanhava. O texto não
        # se perdeu: foi reescrito para o subtítulo de “Cada grupo em detalhe”, que
        # é o que ele sempre descreveu (relatado pela Inês, 13.08.2026).
        #
        # O donut deu lugar a um ranking horizontal: mesmos dados, mesmas
        # percentagens, sem o salto entre o círculo e a legenda. Ver
        # `grafico_composicao`. O total mensal, que estava no centro do donut,
        # é agora o indicador de capa do separador.
        secao("Como se distribui a despesa",
              "Fração da despesa alimentar mensal que vai para cada grupo de produtos, "
              "do maior para o menor. Cada barra é o <strong>peso</strong> do grupo no "
              "cabaz, não a variação dos seus preços."
              + (f" Repartição segundo os ponderadores oficiais de "
                 f"<strong>{dados['ano_pesos']}</strong>."
                 if dados.get("ano_pesos") else ""),
              grupo="05 · Composição da despesa")
        # Este gráfico não mostra variação nenhuma, logo a janela homóloga não é
        # o seu período de referência. O que o data são duas outras coisas: o
        # ano dos ponderadores, que decide a repartição, e o mês a que o nível
        # de despesa está indexado.
        grafico(grafico_composicao(df_decomp),
                rodape=carimbo_do_grafico(dados, mes_indice=ancora.get("mes"),
                                          variacao=False))
        # Sem a base de cálculo por baixo. Era a segunda de três declarações da
        # mesma base em cinquenta linhas, e a única que não acrescentava nada:
        # a primeira abre o bloco, sob os contributos, a terceira fecha-o, na
        # proveniência inteira dos cartões, e entre elas nada mudou. O ano dos
        # ponderadores, que era a outra metade desta linha, já está no subtítulo
        # desta secção, três elementos acima (decisão da Inês, 01.09.2026).

        # ---- detalhe por grupo ----
        secao("Cada grupo em detalhe",
              "Para cada grupo: quanto se gasta por mês, que proporção do cabaz representa, "
              f"quanto variaram os seus preços <strong>{_janela}</strong>, e quantos "
              "euros da variação desse período são atribuíveis a esse grupo. Os nove "
              "contributos somam a variação total.")
        for inicio in range(0, len(df_decomp), 3):
            cols = st.columns(3)
            for col, (_, linha) in zip(cols, df_decomp.iloc[inicio:inicio + 3].iterrows()):
                col.markdown(cartao_classe(linha), unsafe_allow_html=True)
        # Aqui a proveniência vai inteira: são cartões, não há figura para
        # carimbar, logo não há nada de que repartir.
        st.caption(proveniencia(dados, base_ancora,
                                mes_indice=ancora.get("mes")))
        # É nos cartões que a taxa de cada classe aparece isolada, e por isso é
        # aqui que uma classe de outro mês mais engana.
        if _desal_nota:
            st.caption(_desal_nota)

        # ---- cabaz por quintil de rendimento ----
        # O `st.divider()` que abria esta secção saiu: passou a ser um bloco
        # analítico, e o filete do bloco faz o mesmo trabalho sem duplicar traço.
        #
        # O subtítulo explicava a **proveniência** dos dados, IDF contra IHPC,
        # quadros Q.2.11, despesa de turistas, a quem só queria saber o que cada
        # coluna mede. A proveniência desceu para a legenda da tabela, com o
        # desenvolvimento na Metodologia (Inês, 13.08.2026).
        # O confronto entre o peso no orçamento desta tabela e o intervalo do
        # coeficiente de Engel lá em cima estava numa legenda por baixo da
        # tabela, de seis linhas. É a explicação de uma aparente contradição
        # entre dois números da mesma página: quem não a nota não precisa dela,
        # e quem a nota vai procurá-la ao título (decisão da Inês, 13.08.2026).
        _ajuda_engel = None
        if not _eng["so_idf"]:
            # `intervalo_engel` devolve min e max sem presumir qual das bases é
            # a maior, e há um teste que o exige. A prosa presumia, e invertia-se
            # sozinha se as Contas Nacionais alguma vez descessem abaixo do IDF
            # (auditoria de 12.08.2026, K14). Os rótulos derivam do intervalo.
            _idf_e_inferior = _eng["idf"] <= _eng["contas"]
            _pos_idf = "inferior" if _idf_e_inferior else "superior"
            _pos_cn = "superior" if _idf_e_inferior else "inferior"
            _mais_ou_menos = "mais" if _idf_e_inferior else "menos"
            _ajuda_engel = (
                f"O **{percentagem(_eng['idf'], sinal=False)}** da média nacional, na coluna "
                f"“Peso no orçamento”, é o limite **{_pos_idf}** do intervalo do coeficiente de "
                f"Engel mostrado em cima. O limite **{_pos_cn}**, "
                f"{percentagem(_eng['contas'], sinal=False)}, vem das Contas Nacionais: medem o "
                f"consumo das famílias por via macroeconómica e registam, por agregado, "
                f"**{_mais_ou_menos}** despesa alimentar do que o inquérito, e o coeficiente "
                f"diverge porque **o numerador diverge mais do que o denominador**. Nenhuma das "
                "duas é a resposta certa, ver Metodologia."
            )
        secao("Quem está mais exposto, por quintil de rendimento",
              "Cada linha é <strong>um quinto das famílias</strong>, ordenadas do menor "
              "para o maior rendimento. <strong>Despesa alimentar</strong> e "
              "<strong>despesa total</strong> são valores mensais; o <strong>peso no "
              "orçamento</strong> é a primeira dividida pela segunda. "
              "<strong>Inflação 12m</strong> e <strong>agravamento</strong> dizem quanto "
              "subiram os preços e quantos euros por mês isso custa. A última coluna "
              "exprime esse custo em fração do orçamento, é a que compara o "
              "<strong>esforço</strong> entre quintis.",
              ajuda=_ajuda_engel, grupo="06 · Distribuição por rendimento")

        df_quintis = cabaz_quintis(dados["variacoes_classe"])
        df_comp_q = composicao_quintis()

        tab_q = pd.DataFrame([{
            "Quintil": r.nome,
            "Despesa alimentar": euro(r.despesa_mensal, 0) + "/mês",
            "Despesa total": euro(r.despesa_total_mensal, 0) + "/mês",
            "Peso no orçamento": f"{r.peso_orcamento:.1f}%".replace(".", ","),
            "Inflação 12m": percentagem(r.inflacao, sinal=False) if r.inflacao is not None else "—",
            "Agravamento": euro(r.agravamento) + "/mês" if r.agravamento is not None else "—",
            "Agravamento / orçamento": (
                f"{r.agravamento_orcamento:.2f}%".replace(".", ",")
                if r.agravamento_orcamento is not None else "—"),
        } for r in df_quintis.itertuples()])
        st.dataframe(tab_q, width="stretch", hide_index=True)
        st.caption(
            "Ponderação do **IDF 2022/2023**, e não do índice harmonizado de preços no "
            "consumidor (IHPC): é a única fonte aberta que mede agregados residentes. "
            "Ver Metodologia."
        )

        # O agravamento só soma as classes com variação; o orçamento é sempre o
        # total. Faltando classes, a coluna “Agravamento / orçamento”
        # subestimava sem o dizer (auditoria de 11.08.2026, E11).
        _cob_q = df_quintis.attrs.get("cobertura_minima", 1.0)
        if _cob_q < 0.999:
            _falta_q = df_quintis.attrs.get("classes_sem_variacao") or []
            st.warning(
                f"**Cobertura parcial: {percentagem(_cob_q * 100, sinal=False)} da despesa alimentar.** "
                f"{len(_falta_q)} {'classes' if len(_falta_q) > 1 else 'classe'} sem "
                f"variação homóloga nesta sessão, "
                f"{_nomes_classes(_falta_q)}. As colunas **Inflação 12m** e "
                "**Agravamento** medem só as classes cobertas, mas a coluna "
                "**Agravamento / orçamento** divide pelo orçamento **total** do "
                "quintil, está por isso subestimada na mesma proporção."
            )

        _q1 = df_quintis[df_quintis["quintil"] == "q1"].iloc[0]
        _q5 = df_quintis[df_quintis["quintil"] == "q5"].iloc[0]
        _amplitude = None
        _infs = df_quintis[df_quintis["quintil"] != "total"]["inflacao"].dropna()
        if not _infs.empty:
            _amplitude = float(_infs.max() - _infs.min())

        _racio = _q1.peso_orcamento / _q5.peso_orcamento
        _frase_taxa = ""
        if _amplitude is not None:
            _mais_alto = _infs.idxmax()
            _nome_alto = df_quintis.loc[_mais_alto, "nome"]
            _frase_taxa = (
                f"A <em>taxa</em> de inflação, essa, quase não difere entre quintis: a amplitude "
                f"é de <strong>{numero(_amplitude, 2)} p.p.</strong>, e o valor mais alto está no "
                f"<strong>{_nome_alto}</strong>. "
            )

        _frase_esforco = ""
        if _q1.agravamento_orcamento is not None and _q5.agravamento_orcamento is not None:
            _frase_esforco = (
                f"Medido em euros, o agravamento dos últimos 12 meses é <em>maior</em> no "
                f"quintil de rendimento mais elevado "
                f"(<strong>{euro(_q5.agravamento)}</strong> contra "
                f"<strong>{euro(_q1.agravamento)}</strong>), por este registar maior despesa "
                f"alimentar. Medido contra o orçamento de cada um, a relação inverte-se: "
                f"<strong>{numero(_q1.agravamento_orcamento, 2)}%</strong> do orçamento do "
                f"1.º quintil contra <strong>{numero(_q5.agravamento_orcamento, 2)}%</strong> "
                f"do 5.º. "
            )

        nota("O efeito distributivo decorre da exposição, não da taxa", f"""
          A alimentação absorve <strong>{numero(_q1.peso_orcamento, 1)}%</strong> do orçamento do
          quintil de menor rendimento e <strong>{numero(_q5.peso_orcamento, 1)}%</strong> do de
          maior rendimento, um rácio de <strong>{numero(_racio, 2)}</strong>. {_frase_taxa}A
          proximidade das taxas entre quintis não implica neutralidade distributiva: o mesmo
          aumento percentual incide sobre uma proporção do orçamento <strong>{numero(_racio, 1)}
          vezes maior</strong> na base da distribuição, e sobre um orçamento total que é menos de
          metade.<br><br>{_frase_esforco}Nenhuma destas colunas deve por isso ser lida
          isoladamente: a taxa, só por si, sugere neutralidade; os euros, só por si, sugerem o
          inverso.""")

        # Era [3, 2], e os dois gráficos ficavam apertados. A legenda das nove
        # classes ocupava um terço da figura da esquerda, em coluna, e o que
        # sobrava para as barras não chegava; à direita, os nomes das classes no
        # eixo comiam quase toda a largura da coluna.
        #
        # A legenda desceu para baixo das barras, na horizontal, e essa largura
        # voltou para a figura. As colunas ficam iguais: o gráfico da direita
        # precisa dela para os nomes do eixo, e o da esquerda já não a gasta com
        # a legenda (pedido da Inês, 01.09.2026).
        cq1, cq2 = st.columns([1, 1])
        with cq1:
            componente("A composição muda, não só o nível",
                       "Fração da despesa alimentar de cada quintil que vai para cada grupo.")
            chaves_q = [k for k in IDF_QUINTIS if k != "total"]
            figq = go.Figure()
            for classe in CLASSES:
                sub = df_comp_q[df_comp_q["codigo"] == classe["cod"]].set_index("quintil")
                figq.add_trace(go.Bar(
                    name=classe["nome"],
                    x=[IDF_QUINTIS[k] for k in chaves_q],
                    y=[sub.loc[k, "quota"] * 100 for k in chaves_q],
                    marker_color=cor_classe(classe["cod"]),
                    hovertemplate="%{x}<br>" + classe["nome"] + ": %{y:.1f}%<extra></extra>",
                ))
            # A legenda em baixo, na horizontal. `b` sobe de 34 para 150 para
            # lhe abrir lugar: são nove nomes longos, e ao pé da figura eles
            # partem-se em três ou quatro filas. A altura total sobe com ela,
            # senão o que a legenda ganha vinha das barras.
            figq.update_layout(barmode="stack", height=560,
                               margin=dict(t=12, b=150, l=10, r=10),
                               yaxis_title="% da despesa alimentar",
                               legend=dict(orientation="h", font=dict(size=10),
                                           yanchor="top", y=-0.12,
                                           xanchor="left", x=0,
                                           traceorder="normal"))
            figq.update_yaxes(range=[0, 100])
            grafico(figq)
        with cq2:
            componente("Onde a diferença é maior",
                       "Variação da quota entre o 1.º e o 5.º quintil, "
                       "em pontos percentuais.")
            larguras = []
            for classe in CLASSES:
                sub = df_comp_q[df_comp_q["codigo"] == classe["cod"]].set_index("quintil")
                larguras.append({
                    "classe": classe["nome"],
                    "delta": (sub.loc["q5", "quota"] - sub.loc["q1", "quota"]) * 100,
                })
            df_delta = pd.DataFrame(larguras).sort_values("delta")
            figd = go.Figure(go.Bar(
                y=df_delta["classe"], x=df_delta["delta"], orientation="h",
                marker_color=[AZUL if v > 0 else DOURADO for v in df_delta["delta"]],
                hovertemplate="%{y}<br>%{x:+.1f} p.p.<extra></extra>",
            ))
            # A mesma altura da figura da esquerda, para as duas assentarem na
            # mesma linha. Acompanha a subida que a legenda lá provocou.
            figd.update_layout(height=560, margin=dict(t=12, b=34, l=10, r=10),
                               xaxis_title="p.p. (Q5 − Q1)")
            figd.update_xaxes(zeroline=True, zerolinecolor=TEXTO_3, zerolinewidth=1.5)
            grafico(figd)

        st.caption(
            "**Níveis do IDF tal como medidos**, não são reescalados para a base de cálculo "
            "escolhida em “Despesa e composição”. Reescalá-los exigiria assumir que o sub-reporte do "
            "inquérito é uniforme entre quintis, e nada o sustenta. Os quintis são de "
            "rendimento equivalente (escala OCDE modificada), definidos pelo INE."
        )
        st.download_button(
            "Descarregar cabaz por quintil (CSV)",
            csv_com_fonte(df_quintis, "Cabaz alimentar por quintil de rendimento", dados,
                          fonte=("INE, Inquérito às Despesas das Famílias 2022/2023 "
                                 "(níveis e estrutura); Eurostat, IHPC (variações de preço)"),
                          conjuntos=[eurostat.HICP_MENSAL],
                          extra=[
                              ("Níveis e ponderação", "INE, IDF 2022/2023, quadros Q.2.11.a e Q.2.11.b"),
                              ("Variações de preço", "Eurostat, prc_hicp_minr (IHPC, ECOICOP v2)"),
                              ("Nota", "Níveis do IDF tal como medidos, sem reescalamento"),
                          ]),
            file_name="cabaz_por_quintil.csv", mime="text/csv")

        # ---- acessibilidade alimentar: os três limiares, sempre juntos ----
        # Mesmo tratamento das anteriores: o `st.divider()` deu lugar ao filete
        # do bloco analítico.
        secao("Acessibilidade alimentar (três limiares, três respostas)",
              "A capacidade para suportar a despesa alimentar não é uma grandeza única. "
              "Consoante o limiar adotado, os resultados para Portugal variam de forma "
              "substancial, com dados oficiais em qualquer dos casos. Os três limiares "
              "são por isso apresentados em conjunto.",
              grupo="07 · Acessibilidade alimentar")

        _priv = dados.get("privacao", pd.DataFrame())
        _priv_pt = pd.DataFrame()
        if not _priv.empty:
            _priv_pt = _priv[(_priv["geo"] == "PT")].sort_values("time")

        # O ano de referência tem de existir nos **três** quadros do SOFI, que
        # são inscritos à mão e já hoje não têm o mesmo conjunto de anos: o de
        # incapacidade tem 2020, o de custo não. Tomar o máximo de um deles e
        # indexar os outros por esse ano rebentaria na próxima edição em que os
        # anexos divergissem (auditoria de 12.08.2026, L17).
        _anos_sofi = (set(SOFI_INCAPACIDADE["Portugal"]) & set(SOFI_INCAPACIDADE["Espanha"])
                      & set(SOFI_CUSTO["Portugal"]) & set(SOFI_CUSTO["Espanha"]))
        _ano_sofi = max(_anos_sofi) if _anos_sofi else max(SOFI_INCAPACIDADE["Portugal"])
        _sofi_pt = SOFI_INCAPACIDADE["Portugal"][_ano_sofi]
        _sofi_es = SOFI_INCAPACIDADE["Espanha"][_ano_sofi]
        _sofi_pessoas = SOFI_MILHOES.get(_ano_sofi)

        _sev, _ano_sev, _sev_pobres = None, None, None
        if not _priv_pt.empty:
            _tot = _priv_pt[_priv_pt["rskpovth"] == "TOTAL"]
            if not _tot.empty:
                _sev = float(_tot.iloc[-1]["valor"])
                _ano_sev = str(_tot.iloc[-1]["time"])
                _pob = _priv_pt[(_priv_pt["rskpovth"] == "B_60")
                                & (_priv_pt["time"] == _ano_sev)]
                if not _pob.empty:
                    _sev_pobres = float(_pob.iloc[0]["valor"])

        t1, t2, t3 = st.columns(3)
        t1.metric(
            "Privação severa" + (f" ({_ano_sev})" if _ano_sev else ""),
            f"{_sev:.1f}%".replace(".", ",") if _sev is not None else "—",
            help=("Não conseguir pagar uma refeição com carne, frango ou peixe, ou equivalente "
                  "vegetariano, de dois em dois dias. Fonte: Eurostat, EU-SILC."))
        t2.metric(
            f"Sem capacidade para uma dieta saudável ({_ano_sofi})",
            f"{_sofi_pt:.1f}%".replace(".", ","),
            help=("População que não consegue suportar o custo da dieta mais barata que "
                  "cumpre os requisitos nutricionais. Fonte: FAO, relatório The State of "
                  f"Food Security and Nutrition in the World (SOFI), edição de {SOFI_EDICAO}."))
        t3.metric(
            "Peso no orçamento do 1.º quintil",
            f"{IDF_PESO_ALIMENTAR['q1']:.1f}%".replace(".", ","),
            help=("INE, IDF 2022/2023. Não mede privação, mede exposição da despesa "
                  "alimentar no orçamento."))

        # Sem `**`: estas duas entram na `nota`, que é HTML de bloco, e em HTML
        # de bloco o markdown não é interpretado. Saíam ao leitor com os
        # asteriscos à vista (relatado pela Inês, 01.09.2026). O primeiro já cai
        # dentro de um <strong> na lista abaixo, e por isso não leva nenhum.
        _texto_sev = (f"{('%.1f' % _sev).replace('.', ',')}%" if _sev is not None
                      else "o indicador de privação severa")
        _texto_milhoes = (f", cerca de <strong>{numero(_sofi_pessoas, 1)} milhões "
                          f"de pessoas</strong>" if _sofi_pessoas else "")
        # Em tópicos, e não em prosa corrida: são três definições paralelas, e a
        # prosa obrigava a reconstruir a que número se referia cada frase
        # (decisão da Inês, 13.08.2026).
        nota("Os três indicadores não são substituíveis entre si", f"""
          Medem exigências muito diferentes.
          <ul>
            <li><strong>Privação severa ({_texto_sev})</strong>, limiar <strong>muito
                baixo</strong>: mede uma situação próxima da carência alimentar e regista o
                valor mínimo da série.</li>
            <li><strong>Dieta saudável inacessível
                ({('%.1f' % _sofi_pt).replace('.', ',')}%)</strong>, o nível intermédio e o mais
                abrangente: é a proporção da população que não consegue suportar o custo de uma
                dieta nutricionalmente adequada{_texto_milhoes}.</li>
            <li><strong>Peso no orçamento do 1.º quintil</strong>, que não mede privação: mede
                <strong>exposição</strong>, ou seja, que proporção do orçamento dos 20% de menor
                rendimento é afeta à alimentação.</li>
          </ul>
          Apresentado isoladamente, o primeiro indicador circunscreveria a questão a
          <strong>{percentagem(_sev, sinal=False) if _sev is not None else '≈2%'}</strong> da
          população, quando por um limiar nutricionalmente definido a proporção é de
          <strong>{percentagem(_sofi_pt, sinal=False)}</strong>. Os dois indicadores registam
          evoluções distintas e devem ser lidos em conjunto.""")

        ca1, ca2 = st.columns(2)
        with ca1:
            # O subtítulo dizia “o mesmo indicador nas três linhas, repartido por
            # grupo de rendimento”, e “repartido” é justamente o que não é. Cada
            # linha tem o **seu** denominador, e é por isso que as três não se
            # somam e que a nacional não é um ponto médio (Inês, 13.08.2026).
            componente("Privação severa e quem a sofre",
                       "Percentagem que <strong>não consegue pagar uma refeição com carne, "
                       "frango ou peixe</strong> (ou equivalente vegetariano) de dois em "
                       "dois dias. <strong>Cada linha mede a percentagem dentro do seu "
                       "próprio grupo</strong>, e não a proporção da população: por isso as "
                       "três não se somam.")
            if _priv_pt.empty:
                st.info("Série indisponível nesta sessão. Ver o registo de ligações "
                        "no separador Metodologia.")
            else:
                figp = go.Figure()
                _cores_p = {"TOTAL": CINZENTO, "B_60": VERMELHO, "A_60": AZUL}
                for nivel, rotulo in eurostat.PRIVACAO_NIVEIS.items():
                    sub = _priv_pt[_priv_pt["rskpovth"] == nivel]
                    if sub.empty:
                        continue
                    figp.add_trace(go.Scatter(
                        x=sub["time"], y=sub["valor"], name=rotulo, mode="lines+markers",
                        line=dict(color=_cores_p.get(nivel, CINZENTO),
                                  width=2.8 if nivel == "TOTAL" else 2),
                        hovertemplate="%{x}<br>%{y:.1f}%<extra>" + rotulo + "</extra>"))
                figp.update_layout(height=380, margin=dict(t=12, b=34, l=10, r=10),
                                   yaxis_title="% da população",
                                   hovermode="x unified",
                                   legend=dict(orientation="h", y=-0.18))
                figp.update_yaxes(rangemode="tozero")
                grafico(figp)

                # Três legendas seguidas por baixo do gráfico eram mais texto do
                # que gráfico. A que dizia que a linha do total não é um ponto
                # médio saiu, o subtítulo passou a dizer que cada linha tem o
                # seu denominador, que é a causa e não a consequência. As outras
                # duas recolheram-se aqui (decisão da Inês, 13.08.2026).
                #
                # Um popover e não o (i) dos títulos de secção: aquele é dado pelo
                # cabeçalho do Streamlit, que a esta escala, dentro de uma coluna,
                # sob um título de componente, sairia maior do que o título que o
                # encima.
                with st.popover("Leitura do gráfico", icon=":material/info:"):
                    st.markdown(
                        "**O que cada linha é.** *Em risco de pobreza:* quem tem rendimento "
                        "equivalente **abaixo de 60% da mediana nacional**, é uma medida de "
                        "distância à mediana do país, não de indigência. *Acima do limiar:* "
                        "toda a restante população. Cada pessoa está numa e só numa destas "
                        "duas. *População total:* as duas juntas, o número nacional."
                    )
                    if _sev_pobres is not None and _sev:
                        # O `.replace(".", ",")` aplicava-se à cadeia inteira, as
                        # f-strings adjacentes concatenam em tempo de compilação, e
                        # não ao número. É o padrão que o C5 fechou em nove sítios e
                        # que sobreviveu neste (auditoria de 11.08.2026, E8).
                        st.markdown(
                            f"**Leitura.** Em {_ano_sev}, "
                            f"**{percentagem(_sev_pobres, sinal=False)}** entre a população em "
                            f"risco de pobreza, contra **{percentagem(_sev, sinal=False)}** no "
                            f"total, um valor **{numero(_sev_pobres / _sev, 1)}×** superior. O "
                            "valor nacional, tomado isoladamente, não evidencia esta "
                            "concentração."
                        )

        with ca2:
            componente("Custo de uma dieta saudável",
                       "Dólares em paridade de poder de compra (PPP$) por pessoa e por dia. "
                       "Mínimo normativo, não despesa observada.")
            figc = go.Figure()
            _cores_c = {"Portugal": VERDE, "Europa": AZUL,
                        "Europa do Sul": DOURADO, "Espanha": "#7a5ea8"}
            for regiao, serie in SOFI_CUSTO.items():
                anos_c = sorted(serie)
                figc.add_trace(go.Scatter(
                    x=anos_c, y=[serie[a] for a in anos_c], name=regiao,
                    mode="lines+markers",
                    line=dict(color=_cores_c.get(regiao, CINZENTO),
                              width=2.8 if regiao == "Portugal" else 1.8,
                              dash=None if regiao == "Portugal" else "dot"),
                    hovertemplate="%{x}<br>%{y:.2f} PPP$<extra>" + regiao + "</extra>"))
            figc.update_layout(height=380, margin=dict(t=12, b=34, l=10, r=10),
                               yaxis_title="PPP$ por pessoa e por dia",
                               hovermode="x unified",
                               legend=dict(orientation="h", y=-0.18))
            figc.update_xaxes(dtick=1)
            grafico(figc)

        _custo_pt = SOFI_CUSTO["Portugal"][_ano_sofi]
        _custo_es = SOFI_CUSTO["Espanha"][_ano_sofi]
        st.info(f"""
    **Comparação com Espanha**

    Portugal e Espanha registam um custo da dieta saudável praticamente idêntico,
    **{('%.2f' % _custo_pt).replace('.', ',')}** contra
    **{('%.2f' % _custo_es).replace('.', ',')} PPP$** por pessoa e por dia. A proporção da
    população que não consegue suportar esse custo é de
    **{('%.1f' % _sofi_pt).replace('.', ',')}%** em Portugal e de
    **{('%.1f' % _sofi_es).replace('.', ',')}%** em Espanha.

    Com custos equivalentes e resultados divergentes, **a diferença não é atribuível ao nível de
    preços**, o que remete para o nível dos rendimentos e para a sua distribuição. O par ilustra
    a distinção entre um indicador de preços e um indicador de acessibilidade.
        """)

        # O bloco “O que estes indicadores não são” passou para as “Limitações a
        # declarar em qualquer uso”, no separador Metodologia, onde estão as
        # outras nove (decisão da Inês, 13.08.2026).
        st.caption(f"Fontes: Eurostat, EU-SILC · {SOFI_FONTE} · "
                   "INE, IDF 2022/2023 (Q.2.11.b). Os conjuntos exatos estão no "
                   "separador Metodologia.")

        # Sendo inscrito à mão, o SOFI envelhece sem a aplicação dar erro
        # (auditoria de 10.08.2026, D4). O ano é tomado como 31 de dezembro,
        # a leitura mais favorável à fonte.
        _idade_sofi = idade_fonte(_ano_sofi, LIMITE_ANOS_SOFI * 365)
        if _idade_sofi["desatualizada"]:
            _anos_sofi = _idade_sofi["dias"] / 365.25
            st.error(
                f"**O SOFI apresentado é de {_ano_sofi}**, há cerca de "
                f"{numero(_anos_sofi, 1)} anos. Como é publicado em PDF e inscrito à mão em "
                "`src/config.py`, é provável que já exista pelo menos uma edição por "
                "incorporar. **Confirme antes de citar estes valores.**"
            )

        # ------- blocos recolhíveis lado a lado, para reduzir o deslocamento -------
        bloco("07 · Método, comparações e detalhe")
        e1, e2, e3 = st.columns(3)

        with e1.expander("Como é calculado"):
            # O passo 1 **depende da base escolhida**, e as duas não se parecem:
            # a das Contas Nacionais divide um agregado macroeconómico, a do IDF
            # não divide nada. Este bloco descrevia sempre a primeira, incluindo
            # quando a base ativa era o IDF, que é a base por defeito
            # (auditoria de 12.08.2026, L7).
            if base_chave == "contas":
                _passo1 = (
                    "**1 ·** Das **Contas Nacionais** vem a despesa anual de todas as famílias "
                    "em produtos alimentares. Divide-se pelo número de agregados **desse mesmo "
                    "ano** e por doze.")
            else:
                _passo1 = (
                    "**1 ·** Do **Inquérito às Despesas das Famílias 2022/2023** vem a despesa "
                    "alimentar anual **por agregado**, medida diretamente. Divide-se apenas por "
                    "doze: não passa por divisão de nenhum agregado macroeconómico.")
            st.markdown(f"""
    {_passo1}

    **2 ·** O valor é trazido ao mês corrente pelo índice oficial de preços.

    **3 ·** Ajusta-se à composição do agregado pela escala de equivalência.

    **4 ·** Reparte-se pelos nove grupos com os ponderadores oficiais do índice.

    Descreve a base **{base_ancora['nome']}**, escolhida em “Despesa e composição”. As fórmulas
    completas das duas bases estão no separador **Metodologia**.
            """)
            st.warning(
                "**Não é um cabaz de compras.** Não há quilos nem litros: há euros e variações "
                "de preço. E os preços são médias nacionais do INE, não de uma insígnia concreta."
            )

        with e2.expander("Comparar composições"):
            comps = [(1, 0, "1 adulto"), (2, 0, "Casal"), (1, 1, "Monoparental + 1"),
                     (1, 2, "Monoparental + 2"), (2, 1, "Casal + 1 criança"),
                     (2, 2, "Casal + 2 crianças"), (2, 3, "Casal + 3 crianças")]
            dm = dim_efetiva
            # A coluna do meio fixava a OCDE original, fosse qual fosse a escala
            # escolhida na barra lateral, e não o dizia. Passa a usar a escala
            # ativa e a nomeá-la no cabeçalho (auditoria de 12.08.2026, L19).
            _rot_esc = ESCALAS[escala_chave]["nome"].split(" (")[0]
            _col_central = f"{_rot_esc} (€)"
            # Ordem Mín. → escala ativa → Máx., para que se veja **onde** a
            # escolha cai dentro do intervalo. Com uma escala extrema, per
            # capita ou OCDE modificada, a coluna coincide com um dos limites,
            # e assim isso lê-se em vez de parecer um valor repetido.
            linhas_c = []
            _coincide = 0
            for a, c, rot in comps:
                iv = intervalo_agregado(valor_medio_agregado, dm, a, c)
                _central = round(despesa_do_agregado(
                    valor_medio_agregado, dm, a, c, escala_chave), 2)
                if _central in (round(iv["minimo"], 2), round(iv["maximo"], 2)):
                    _coincide += 1
                linhas_c.append({
                    "Composição": rot, "Pessoas": a + c,
                    "Mín. (€)": round(iv["minimo"], 2),
                    _col_central: _central,
                    "Máx. (€)": round(iv["maximo"], 2),
                })
            st.dataframe(pd.DataFrame(linhas_c), width="stretch", hide_index=True)
            st.caption(
                f"Agregado médio nacional: {('%.2f' % dm).replace('.', ',')} pessoas. "
                f"A coluna **{_rot_esc}** usa a escala escolhida em “Despesa e composição”; o "
                "intervalo resulta das três escalas de equivalência."
                + (f" Nesta escala a coluna coincide com um dos limites em "
                   f"{_coincide} das {len(comps)} composições, a **{_rot_esc}** é uma "
                   "das escalas extremas." if _coincide else "")
            )

        with e3.expander("Tabela detalhada"):
            tabela = df_decomp[["codigo", "classe", "classe_oficial", "ponderador",
                                "quota", "valor", "variacao", "contributo"]].copy()
            tabela.columns = ["Código", "Grupo", "Designação oficial (INE)",
                              "Ponderador (‰)", "Quota",
                              "Valor (€)", "Variação (%)", "Contributo (€)"]
            # A coluna do código sai do ecrã, é nomenclatura que só interessa a
            # quem vai à fonte, mas fica no CSV, que circula sozinho e precisa
            # de ser rastreável (decisão da Inês, 13.08.2026).
            st.dataframe(tabela.drop(columns=["Código"]),
                         width="stretch", hide_index=True,
                         column_config={
                             "Quota": st.column_config.ProgressColumn(
                                 "Quota", format="%.1f%%", min_value=0, max_value=1),
                             "Valor (€)": st.column_config.NumberColumn(format="%.2f"),
                             "Variação (%)": st.column_config.NumberColumn(format="%.1f"),
                             "Contributo (€)": st.column_config.NumberColumn(format="%.2f"),
                             "Ponderador (‰)": st.column_config.NumberColumn(format="%.1f"),
                         })
            st.download_button(
                "Descarregar tabela (CSV)",
                csv_com_fonte(tabela, "Decomposição por grupo de produto", dados,
                              # A âncora pode ser do INE (IDF) ou do Eurostat
                              # (Contas Nacionais): o cabeçalho segue a que
                              # estiver ativa.
                              fonte=(f"{base_ancora['fonte']} (âncora da despesa); "
                                     "Eurostat, IHPC (ponderadores e variações)"),
                              extra=[("Base de cálculo", base_ancora["nome"]),
                                     ("Composição do agregado", composicao),
                                     ("Escala", ESCALAS[escala_chave]["nome"])]),
                f"despesa_alimentar_decomposicao_{date.today()}.csv", "text/csv",
                width="stretch")

    # ==========================================================================
    # ABA 2, Histórico
    # ==========================================================================
with aba2:
    with painel("Histórico"):
        titulo_pagina(
            "Histórico dos preços alimentares",
            "Índice de preços dos produtos alimentares em Portugal e variação "
            "homóloga, mês a mês, com a decomposição entre frescos e transformados.")

        # Este separador não dá valores em euros, logo não tem âncora de
        # despesa; e a comparação de índices usa os ponderadores de vários
        # anos, pelo que nomear um só seria falso.
        faixa_fonte(ponderadores=False, ancora=False)

        base = dados.get("base_indice") or "—"
        # Doze linhas de definição antes do primeiro gráfico da página. O texto
        # é bom e fica inteiro, mas passa a bloco recolhível: quem já sabe o que
        # é um índice não tem de o atravessar todas as vezes para chegar à
        # série, que é o que veio ver.
        with st.expander("Em que consiste o índice"):
            st.markdown(f"""
    **Não são euros.** É um número que mede o **nível dos preços**
    relativamente a um ano de referência, ao qual se atribui o valor 100. A base atualmente em
    vigor é **{base}**: se o índice estiver em 118, os preços dos produtos alimentares estão
    18% acima do que estavam nesse ano de referência.

    O índice **não diz quanto custa** um cabaz, diz de quanto os preços se afastaram do
    ponto de partida. É por isso que a despesa em euros do primeiro separador precisa de uma
    âncora nas Contas Nacionais: o índice sozinho nunca daria um valor em euros.

    A **variação homóloga** (linha vermelha) é derivada do índice: compara cada mês com o mesmo
    mês do ano anterior.
            """)

        secao("Evolução do índice e da variação homóloga",
              "Série mensal de Portugal para o agregado alimentar, no intervalo "
              "escolhido no cursor.",
              grupo="01 · Série mensal", topo=True)

        if dados["indice_pt"].empty:
            st.info("Sem série de índices disponível.")
            periodos, inicio_sel, fim_sel = [], None, None
        else:
            periodos = sorted(dados["indice_pt"]["time"].unique())
            pre = periodos[-25] if len(periodos) > 25 else periodos[0]
            inicio_sel, fim_sel = st.select_slider(
                "Intervalo a apresentar",
                options=periodos, value=(pre, periodos[-1]),
                format_func=mes_pt,
            )
            st.caption(
                f"A mostrar de **{mes_pt(inicio_sel)}** a **{mes_pt(fim_sel)}**, "
                f"{periodos.index(fim_sel) - periodos.index(inicio_sel) + 1} meses. "
                "Arraste as extremidades para alterar."
            )

            idx_sel = dados["indice_pt"][
                (dados["indice_pt"]["time"] >= inicio_sel) &
                (dados["indice_pt"]["time"] <= fim_sel)]
            var_sel = dados["var_pt"][
                (dados["var_pt"]["time"] >= inicio_sel) &
                (dados["var_pt"]["time"] <= fim_sel)]

            # Se a série da variação não cobrir todo o intervalo escolhido, a linha
            # vermelha aparece truncada, e isso tem de ser dito, não descoberto.
            if not var_sel.empty and len(var_sel) < len(idx_sel):
                st.warning(
                    f"A linha da **variação homóloga** só cobre "
                    f"{mes_pt(var_sel['time'].min())} a {mes_pt(var_sel['time'].max())}, "
                    f"{len(var_sel)} dos {len(idx_sel)} meses do intervalo escolhido. O índice "
                    "recua mais do que a série de variação disponível nesta sessão."
                )
            elif var_sel.empty:
                st.warning(
                    "Não há variação homóloga publicada para o intervalo escolhido: o gráfico "
                    "mostra apenas o índice."
                )

            grafico(grafico_historico(idx_sel, var_sel, len(idx_sel)))

            if len(idx_sel) >= 2:
                acum = (idx_sel["valor"].iloc[-1] / idx_sel["valor"].iloc[0] - 1) * 100
                st.info(
                    f"**Variação acumulada no intervalo escolhido: {percentagem(acum)}**, "
                    f"de {mes_pt(inicio_sel)} a {mes_pt(fim_sel)}. "
                    "A taxa homóloga de um mês isolado tem alcance limitado; a variação "
                    "acumulada desde uma data de referência caracteriza melhor o período."
                )

        var_pt = dados["var_pt"]
        if not var_pt.empty and inicio_sel is not None:
            janela = var_pt[(var_pt["time"] >= inicio_sel) &
                            (var_pt["time"] <= fim_sel)]["valor"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Variação mais recente", percentagem(var_pt["valor"].iloc[-1]),
                      help=f"Mês de referência: {mes_pt(var_pt['time'].iloc[-1])}")
            if len(janela):
                c2.metric("Média do intervalo", percentagem(janela.mean()))
                c3.metric("Máximo do intervalo", percentagem(janela.max()))
                c4.metric("Mínimo do intervalo", percentagem(janela.min()))

        st.caption(
            "Frequência mensal, a mais fina publicada por fonte oficial. Existem séries semanais "
            "de cabazes publicadas por entidades privadas, mas não são dados oficiais nem têm "
            "acesso automático, e as variações semanais são muito voláteis por efeitos de base."
        )

        # ---------- o que está por trás da inflação alimentar ----------
        agr_esp = dados.get("agregados_especiais")
        if agr_esp is not None and not agr_esp.empty:
            secao("Composição da variação: frescos e transformados",
                  "A alimentação não constitui um agregado homogéneo: os produtos não "
                  "transformados e os transformados respondem a determinantes distintos.",
                  grupo="02 · Frescos e transformados")
            st.info("""
    A alimentação não constitui um agregado homogéneo. **Os produtos não transformados e os
    transformados respondem a determinantes distintos:**

    - **Não transformados** (carne, peixe, fruta, legumes) respondem a condições climáticas,
      sazonalidade e custos de transporte. Uma subida nesta componente está tipicamente associada
      a um **choque de oferta**.
    - **Transformados** (pão, laticínios, conservas) refletem custos de produção e distribuição já
      incorporados. Uma subida nesta componente tende a ser **mais persistente**.

    As duas componentes têm, por isso, origens e durações diferentes, e a distinção é relevante
    para caracterizar a natureza da variação observada.
            """)

            pt_esp = agr_esp[agr_esp["geo"] == "PT"]
            meses_esp = sorted(pt_esp["time"].unique())
            # O cursor é definido pelo índice por classe, que sai por volta do
            # dia 17. A estimativa rápida dos **agregados** sai no último dia
            # útil do mês de referência, pelo que esta série pode ter um mês a
            # mais, que ficava fora do intervalo e desaparecia sem uma palavra
            # (auditoria de 12.08.2026, L15).
            _alem = [m for m in meses_esp if fim_sel is not None and m > fim_sel]
            if inicio_sel is not None:
                meses_esp = [m for m in meses_esp if inicio_sel <= m <= fim_sel]
                # Se a série não cobrir todo o intervalo escolhido, isso tem de
                # ser dito, não descoberto por o gráfico começar mais tarde.
                _esperados = [p for p in periodos if inicio_sel <= p <= fim_sel]
                if meses_esp and len(meses_esp) < len(_esperados):
                    st.warning(
                        f"Estes agregados só cobrem {mes_pt(meses_esp[0])} a "
                        f"{mes_pt(meses_esp[-1])}, {len(meses_esp)} dos "
                        f"{len(_esperados)} meses do intervalo escolhido. O índice recua "
                        "mais do que a série disponível nesta sessão."
                    )
                elif not meses_esp:
                    st.warning(
                        "Não há observações destes agregados no intervalo escolhido."
                    )
                if _alem:
                    st.info(
                        f"**Estes agregados já têm {mes_pt(_alem[-1])}**, um mês à frente do "
                        f"índice por classe ({mes_pt(fim_sel)}), que é o que define o cursor. "
                        "A estimativa rápida do índice (só agregados) sai no último dia útil "
                        "do mês de referência; o índice completo, com as nove classes, só por "
                        "volta do dia 17 do mês seguinte. A observação existe e não é "
                        "apresentada, porque o gráfico está alinhado com o cursor."
                    )

            so_alim = st.toggle(
                "Mostrar também os agregados de enquadramento", value=False,
                help=("Inflação geral e subjacente. Não são alimentação, servem para situar "
                      "a subida alimentar no conjunto dos preços."))
            visiveis = [a for a in AGREGADOS
                        if so_alim or a["grupo"] == "alimentacao"]

            if visiveis and meses_esp:
                figA = go.Figure()
                for a in visiveis:
                    sub = pt_esp[pt_esp["coicop"] == a["cod"]].set_index("time")["valor"]
                    if sub.empty:
                        continue
                    figA.add_trace(go.Scatter(
                        x=[mes_pt(m) for m in meses_esp],
                        y=[sub.get(m) for m in meses_esp],
                        name=a["nome"],
                        line=dict(color=a["cor"], width=a["larg"],
                                  dash="dot" if a["grupo"] == "enquadramento" else "solid"),
                        hovertemplate="%{x}<br>%{y:.1f}%<extra>" + a["nome"] + "</extra>"))
                figA.update_layout(height=460, margin=dict(t=22, b=42, l=10, r=10),
                                   yaxis_title="Variação homóloga (%)",
                                   legend=dict(orientation="h", y=1.13, x=0),
                                   hovermode="x unified")
                figA.update_xaxes(showgrid=False)
                grafico(figA)
                if so_alim:
                    st.caption("A tracejado, os agregados de enquadramento, não são alimentação.")
                # A incoerência entre o total e as duas parcelas é declarada
                # aqui, e não escondida: quem some as duas linhas não chega ao
                # total, e tem de poder saber porquê sem sair do gráfico.
                # Sem linha de proveniência: estes agregados publicam antes do
                # índice por classe e o gráfico é cortado pelo cursor, pelo que
                # o mês aqui não é o `mes_variacoes` que a `proveniencia` usa. O
                # período deste gráfico é o que os avisos acima já declaram.
                st.caption(AGREGADOS_NOTA + f" ({AGREGADOS_NOTA_FONTE}.)")

                ult_esp = meses_esp[-1]
                linhas_a = []
                for a in visiveis:
                    sub = pt_esp[(pt_esp["coicop"] == a["cod"]) & (pt_esp["time"] == ult_esp)]
                    if sub.empty:
                        continue
                    ue_sub = agr_esp[(agr_esp["geo"] == "EU27_2020") &
                                     (agr_esp["coicop"] == a["cod"]) &
                                     (agr_esp["time"] == ult_esp)]
                    linhas_a.append({
                        # Marcador em texto, e não emoji: a distinção entre
                        # componentes da alimentação e agregados de
                        # enquadramento é informação, e tem de se ler também
                        # sem depender de um ícone.
                        "Tipo": ("Alimentação" if a["grupo"] == "alimentacao"
                                 else "Enquadramento"),
                        "Agregado": a["nome"],
                        "Portugal (%)": round(float(sub["valor"].iloc[0]), 1),
                        "UE-27 (%)": (round(float(ue_sub["valor"].iloc[0]), 1)
                                      if not ue_sub.empty else None),
                        "Para que serve": a["porque"],
                    })
                if linhas_a:
                    st.dataframe(pd.DataFrame(linhas_a), width="stretch", hide_index=True)
                    st.caption(
                        f"Variação homóloga em {mes_pt(ult_esp)}. A coluna “Tipo” distingue "
                        "os componentes da alimentação dos agregados de enquadramento, "
                        "que não são alimentação."
                    )
                    st.download_button(
                        "Descarregar (CSV com fonte)",
                        csv_com_fonte(pd.DataFrame(linhas_a).drop(columns=["Tipo"]),
                                      "Decomposição da inflação alimentar", dados,
                                      extra=[("Mês de referência", ult_esp)]),
                        # Nome distinto do CSV da decomposição por grupo, no
                        # separador 1: os dois saíam como
                        # `despesa_alimentar_decomposicao_<data>.csv` e ficavam
                        # indistinguíveis na pasta de transferências
                        # (auditoria de 12.08.2026, L13).
                        f"despesa_alimentar_agregados_indice_{date.today()}.csv", "text/csv")

        # ---- viés de substituição: cabaz fixo contra Törnqvist ----
        _cmp_idx = indices_comparados(dados.get("indice_classes", pd.DataFrame()),
                                      dados.get("pesos_por_ano", pd.DataFrame()))
        if not _cmp_idx.empty and len(_cmp_idx) >= 3:
            secao("Cabaz fixo contra cabaz que acompanha o consumo",
                  "A crítica central ao cabaz de composição fixa é que não acompanha a "
                  "substituição de consumo. Nesta secção essa crítica é quantificada"
                  ", comparando um índice de ponderadores fixos com um índice "
                  "superlativo de Törnqvist, que usa a média dos ponderadores dos dois "
                  "extremos de cada ano.", grupo="03 · Viés de substituição")

            _ano_base = int(_cmp_idx["ano"].iloc[0])
            # O ano-base é fixo em `config.py`. Se não estiver disponível nos
            # dados, a série recua, e isso tem de ser dito, porque o valor do
            # viés depende do ano-base (auditoria de 11.08.2026, E14).
            if _cmp_idx.attrs.get("ano_base_pedido") != _ano_base:
                st.warning(
                    f"**Ano-base substituído.** O painel está fixado em dezembro de "
                    f"**{_cmp_idx.attrs.get('ano_base_pedido')}**, mas essa observação não está "
                    f"disponível nesta sessão. Os índices foram encadeados a partir de dezembro "
                    f"de **{_ano_base}**, pelo que o viés acumulado **não é comparável** com o "
                    "que consta de versões anteriores deste documento."
                )
            _ult = _cmp_idx.iloc[-1]
            _ano_fim = int(_ult["ano"])

            # O índice oficial do agregado, rebaseado ao mesmo dezembro. A base
            # do índice é irrelevante depois de rebasear: é um rácio interno.
            _oficial = None
            _ipt = dados["indice_pt"]
            if not _ipt.empty:
                _d = _ipt[_ipt["time"].astype(str).str.endswith("-12")].copy()
                if not _d.empty:
                    _d["ano"] = _d["time"].astype(str).str[:4].astype(int)
                    _s = _d.groupby("ano")["valor"].last()
                    if _ano_base in _s.index:
                        _oficial = _s / _s.loc[_ano_base] * 100

            _subida_fixo = _ult["laspeyres_fixo"] - 100
            _subida_torn = _ult["tornqvist"] - 100
            _vies = float(_ult["vies"])
            _anos_decorridos = max(_ano_fim - _ano_base, 1)

            k1, k2, k3 = st.columns(3)
            k1.metric(f"Cabaz fixo (subida desde dez/{str(_ano_base)[2:]})",
                      percentagem(_subida_fixo),
                      help="Ponderadores congelados no ano-base, como num cabaz de "
                           "composição fixa.")
            k2.metric("Törnqvist (a mesma subida)", percentagem(_subida_torn),
                      help="Ponderadores revistos a cada ano, pela média dos dois extremos.")
            k3.metric("Viés de substituição acumulado",
                      pontos(_vies, sufixo=" pontos"),
                      pontos(_vies / _anos_decorridos, sufixo=" p.p./ano"),
                      delta_color="off",
                      help="Quanto o cabaz fixo sobrestima a subida, face ao índice superlativo.")

            figt = go.Figure()
            figt.add_trace(go.Scatter(
                x=_cmp_idx["ano"], y=_cmp_idx["laspeyres_fixo"], name="Cabaz fixo (Laspeyres)",
                mode="lines+markers", line=dict(color=VERMELHO, width=2.6),
                hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"))
            figt.add_trace(go.Scatter(
                x=_cmp_idx["ano"], y=_cmp_idx["tornqvist"], name="Törnqvist (superlativo)",
                mode="lines+markers", line=dict(color=VERDE, width=2.6),
                hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"))
            if _oficial is not None:
                _al = [a for a in _cmp_idx["ano"] if a in _oficial.index]
                figt.add_trace(go.Scatter(
                    x=_al, y=[_oficial.loc[a] for a in _al], name="IHPC oficial (publicado)",
                    mode="lines", line=dict(color=AZUL, width=1.8, dash="dot"),
                    hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"))
            figt.update_layout(height=440, margin=dict(t=12, b=34, l=10, r=10),
                               yaxis_title=f"Índice (dez/{_ano_base} = 100)",
                               hovermode="x unified",
                               legend=dict(orientation="h", y=-0.16))
            figt.update_xaxes(dtick=1)
            grafico(figt)

            st.info(f"""
    **O resultado difere do que a crítica ao cabaz de composição fixa antecipa.**

    Em {_anos_decorridos} anos, a fixação dos ponderadores das nove classes sobrestima a subida em
    **{pontos(_vies, sufixo=" pontos de índice")}**, cerca de
    **{pontos(_vies / _anos_decorridos, sufixo=" p.p. por ano")}**. Sobre uma subida
    acumulada de {percentagem(_subida_torn)}, o efeito é residual.

    A razão é que **a substituição relevante ocorre dentro das classes e não entre elas**. A
    substituição entre cortes de carne não altera o ponderador da carne; a substituição entre
    marca própria e marca de fabricante não altera nenhum ponderador. Nove classes COICOP
    constituem um nível de agregação insuficiente para captar essas alterações de consumo.

    **Este resultado tem duas implicações.** Primeira: o viés de substituição *entre grupos de
    alimentos*, medido nestes dados, é reduzido. Segunda: o resultado **não é extensível** a um
    cabaz de composição fixa ao nível do produto. Um cabaz de 63 produtos com quantidades fixas
    não capta a mudança de marca, de calibre, de embalagem nem de insígnia, e nenhuma dessas
    dimensões é observável nestes dados. O efeito medido aqui é o menor dos dois; o maior não é
    quantificável com as fontes disponíveis.
            """)

            _excl = _cmp_idx.attrs.get("classes_excluidas") or []
            if _excl:
                _nomes_excl = ", ".join(POR_CODIGO[c]["nome"] for c in _excl
                                        if c in POR_CODIGO)
                st.warning(
                    f"**Cobertura reduzida.** {len(_excl)} das nove classes não têm série "
                    f"completa em todos os dezembros do período e ficaram de fora deste "
                    f"cálculo: **{_nomes_excl}**. Os dois índices são comparáveis entre si, "
                    "usam exatamente as mesmas classes, mas não cobrem todo o cabaz alimentar."
                )

            with st.expander("Como estes índices são construídos"):
                st.markdown(f"""
    Todos partem de dezembro de {_ano_base} = 100 e usam o índice mensal por classe e os
    ponderadores anuais, ambos do Eurostat. Os conjuntos exatos estão no separador Metodologia.
    Entram as **{len(_cmp_idx.attrs.get('classes_usadas') or [])} classes** com série completa em
    todos os dezembros do período: uma classe sem observação num único mês eliminaria esse mês da
    comparação, e com ele o elo do índice.

    **Cabaz fixo (Laspeyres de base fixa)**, as quotas do ano-base aplicadas ao relativo de preço
    acumulado desde esse ano:
                """)
                st.latex(r"P_L(t) = \sum_i w_i(0)\,\frac{I_i(t)}{I_i(0)}")
                st.markdown(
                    "**Törnqvist**, média geométrica ponderada dos relativos de cada elo, com a "
                    "média aritmética das quotas dos dois extremos:")
                st.latex(r"\ln P_T(t\!-\!1 \to t) = \sum_i \frac{s_i(t\!-\!1)+s_i(t)}{2}"
                         r"\,\ln\frac{I_i(t)}{I_i(t\!-\!1)}")
                st.warning("""
    **Aproximação a declarar.** O Törnqvist exige as quotas de despesa observadas nos dois extremos
    de cada elo. O que existe em fonte aberta são os ponderadores do IHPC, que o Documento
    Metodológico do IPC define como referidos a **dezembro do ano n−1** e já atualizados a preços
    desse momento. A correspondência adotada decorre dessa definição: o elo de dezembro de y−1 a
    dezembro de y usa a média dos ponderadores de y e de y+1. Para o último elo, o ponderador de
    y+1 ainda não está publicado e repete-se o de y.

    Não é o Törnqvist exato. É a melhor aproximação possível sem microdados de despesa anuais, e o
    facto de a série resultante acompanhar de perto o IHPC oficial, que é construído por outra
    via, é indício da adequação da aproximação.
                """)

            st.download_button(
                "Descarregar comparação de índices (CSV)",
                csv_com_fonte(_cmp_idx, "Viés de substituição, cabaz fixo contra Törnqvist", dados,
                              fonte="Eurostat, IHPC (ECOICOP v2); cálculo da UPE",
                              conjuntos=[eurostat.HICP_MENSAL, eurostat.HICP_PONDERADORES],
                              extra=[
                                  ("Base", f"dezembro de {_ano_base} = 100"),
                                  ("Séries", "prc_hicp_minr (índice por classe) e prc_hicp_iw"),
                                  ("Nota", "Törnqvist aproximado; ver a metodologia no separador"),
                              ]),
                file_name="vies_substituicao.csv", mime="text/csv")

        serie = dados["indice_pt"][["time", "valor"]].rename(
            columns={"time": "Período", "valor": f"Índice ({base})"})
        var_tab = dados["var_pt"][["time", "valor"]].rename(
            columns={"time": "Período", "valor": "Variação homóloga (%)"})
        junto = serie.merge(var_tab, on="Período", how="outer").sort_values("Período")

        st.download_button(
            "Descarregar série completa (CSV com fonte)",
            csv_com_fonte(junto, "Série do índice de preços alimentares, Portugal", dados,
                          extra=[("Base do índice", base), ("Classe COICOP", "CP011")]),
            f"despesa_alimentar_serie_{date.today()}.csv", "text/csv",
        )

    # ==========================================================================
    # ABA 6, Da produção ao consumo
    # ==========================================================================
with aba6:
    with painel("Da produção ao consumo"):
        titulo_pagina(
            "Da produção ao consumo",
            "Todos os outros indicadores desta ferramenta medem o que o consumidor paga "
            "ou quanto as famílias gastam. Nenhum identifica se a variação teve origem na "
            "exploração agrícola, na transformação ou na distribuição. O Observatório de "
            "Preços Agroalimentar do Gabinete de Planeamento, Políticas e Administração "
            "Geral (GPP) é a única fonte pública que segue o mesmo produto nas duas pontas "
            "da cadeia.")

        _obs, _obs_meta = observatorio.carregar()
        if _obs.empty:
            st.warning(
                "**Sem dados recolhidos.** O Observatório não tem API: a série é obtida por "
                "`scripts/recolher_observatorio.py`, que escreve `dados/observatorio.csv`. "
                "Execute o script para preencher este separador."
            )
        else:
            _var = observatorio.variacoes(_obs)
            _com_prod = _var[_var["tem_producao"]].copy()
            _ini = _obs["inicio"].min()
            _fim = _obs["inicio"].max()

            # Os preços referem-se a um **período de quatro semanas**, não a um
            # dia: o ficheiro guarda a data de início, e o fim é o início mais
            # 27 dias. Apresentar só a data de início dava a entender que os
            # preços eram desse dia.
            _fim_periodo = _fim + pd.Timedelta(days=27)
            _n_periodo = None
            _ult = _obs[_obs["inicio"] == _fim]
            if not _ult.empty and "periodo" in _ult.columns:
                try:
                    _n_periodo = int(_ult["periodo"].iloc[0])
                except (TypeError, ValueError):
                    _n_periodo = None
            _periodo_txt = (f"{_fim.strftime('%d/%m/%Y')} a "
                            f"{_fim_periodo.strftime('%d/%m/%Y')}")

            o1, o2, o3, o4 = st.columns(4)
            o1.metric("Produtos seguidos", f"{_obs['produto'].nunique()}")
            o2.metric("Com as duas fases", f"{len(_com_prod)}",
                      help="Só para estes é possível comparar produção e consumo.")
            o3.metric("Períodos de quatro semanas", f"{_obs['inicio'].nunique()}")
            o4.metric("Preços do período", _fim_periodo.strftime("%d/%m/%Y"),
                      help=f"Os preços mostrados são a média do período de {_periodo_txt}. "
                           "O Observatório publica em períodos de quatro semanas.")

            st.caption(
                f"**Os preços mostrados referem-se ao período de {_periodo_txt}**"
                # O ano vem da própria observação. Escrevê-lo à mão é o padrão
                # que as auditorias deste projeto já apanharam quatro vezes.
                + (f" (período {_n_periodo} de {_fim.year})" if _n_periodo else "")
                + f". Série completa desde {_ini.strftime('%d/%m/%Y')}. "
                + f"Fonte: {_obs_meta.get('fonte', 'GPP')}."
            )

            # Vigilância de frescura mantida, mas o que se **mostra** é apenas o
            # que o utilizador precisa de saber para decidir se pode citar os
            # números: quão antigos são. A distinção entre “a fonte parou” e “a
            # recolha está velha” é operacional, diz respeito a quem mantém a
            # ferramenta, não a quem a lê, e a aplicação não a consegue sequer
            # estabelecer com segurança: só vê o ficheiro, não a fonte. Ficou de
            # fora da interface por decisão da Inês, 13.08.2026.
            _fresc_obs = frescura_do_observatorio(
                _fim, _obs_meta.get("extraido_em"), LIMITE_DIAS_OBSERVATORIO)

            if _fresc_obs["parada"]:
                st.warning(
                    f"**Estes preços têm mais de {numero(LIMITE_DIAS_OBSERVATORIO)} dias.** "
                    "O Observatório publica de quatro em quatro semanas, e o período acima "
                    "está mais atrasado do que o habitual, confirme antes de os citar como "
                    "situação corrente. As comparações entre produtos e entre fases não são "
                    "afetadas: assentam em janelas de vários anos."
                )

            # A ressalva que governa a leitura de todo o separador. Era um aviso
            # do Streamlit entre outros três; passa a nota editorial, que é o
            # peso que lhe corresponde: sem ela, cada barra deste separador
            # lê-se como margem de alguém.
            nota("A diferença entre os preços não é uma margem", """
          Inclui transporte, transformação, embalagem, distribuição e IVA. E as duas fases podem
          referir-se a <strong>formas diferentes do mesmo produto</strong>, peixe inteiro contra
          posta, animal vivo contra peça desmanchada. Por isso a diferença <strong>não é
          comparável entre produtos</strong> e <strong>não deve ser lida como lucro</strong> de
          nenhum operador. O que estes dados mostram com segurança é <em>onde</em> os preços se
          moveram, não <em>quem</em> decidiu o quê.""", alerta=True)

            # ---- panorama dos produtos com as duas fases ----
            secao("Os dois lados da cadeia, por produto",
                  "Variação do preço em cada fase, produto a produto, na janela "
                  "comum às duas.", grupo="01 · Panorama da cadeia")
            # As percentagens vão **formatadas em Python**, e não por `%{x:+.1f}`
            # no modelo do hover do Plotly, que não estava a pegar (relatado pela
            # Inês, 20.08.2026). Definida aqui, fora do `if`/`else` que se segue,
            # porque é usada também mais abaixo em "Ver um produto em detalhe",
            # que corre sempre — com `_com_prod` vazio essa secção ficava sem
            # `_pct_obs` definida e rebentava com `NameError` (auditoria de
            # 21.08.2026).
            def _pct_obs(v):
                return percentagem(v, casas=2) if pd.notna(v) else "—"

            # A janela **não é a mesma para todos os produtos**: cada variação é
            # medida no período comum às duas fases desse produto, que em vários
            # casos é bem mais curto do que a série global. A legenda anterior
            # anunciava a data mínima global, e era falsa para metade dos
            # produtos (auditoria de 10.08.2026, C4).
            if not _com_prod.empty:
                _n_min, _n_max = int(_com_prod["n_periodos"].min()), int(_com_prod["n_periodos"].max())
                # “N períodos de quatro semanas” dizia-se aqui, e induzia em
                # erro: convidava a multiplicar N por quatro para saber a
                # duração da janela, o que só está certo nas séries sem falhas.
                # O Arroz Carolino tem 16 observações num intervalo de quatro
                # anos, não de 64 semanas (relatado pela Inês, 20.08.2026).
                _c_falhas = int(_com_prod["tem_falhas"].sum())
                _cap_janela = (
                    f"Cada produto é medido **no seu próprio período comum às duas fases**, "
                    f"entre {_n_min} e {_n_max} observações, conforme o produto. O Observatório "
                    "publica de quatro em quatro semanas, mas **o número de observações não dá a "
                    "duração da janela**: há séries com falhas. As janelas e as contagens estão "
                    "na tabela abaixo; **as variações não são comparáveis entre produtos com "
                    "janelas diferentes**. Só os produtos com série de produção aparecem aqui."
                    + (f" {_c_falhas} destes produtos têm falhas na série."
                       if _c_falhas else "")
                )
            else:
                _cap_janela = "Só os produtos com série de produção aparecem aqui."
            st.caption(_cap_janela)

            if _com_prod.empty:
                st.info("Nenhum produto tem as duas fases nesta recolha.")
            else:
                # A tabela repetia o gráfico e acrescentava quatro colunas. As
                # quatro passam para o próprio hover das barras, para que não seja
                # preciso procurar em baixo o que qualifica a barra que se está a
                # olhar (decisão da Inês, 13.08.2026).
                #
                # A ordem das barras é a inversa da tabela **de propósito**: o
                # Plotly desenha a primeira categoria em baixo, e é isso que faz
                # com que as duas fiquem a coincidir de cima para baixo. Mexer numa
                # sem mexer na outra parte-as em silêncio.
                _ord = _com_prod.sort_values("consumo_var")

                _extra = list(zip(
                    _ord["inicio"].dt.strftime("%m/%Y"),
                    _ord["fim"].dt.strftime("%m/%Y"),
                    _ord["n_periodos"].astype(int),
                    [_pct_obs(v) for v in _ord["diferenca_var"]],
                    _ord["padrao"],
                    [_pct_obs(v) for v in _ord["producao_var"]],
                    [_pct_obs(v) for v in _ord["consumo_var"]],
                ))
                _qualifica = ("<br>Janela: %{customdata[0]} – %{customdata[1]}"
                              " (%{customdata[2]} períodos)"
                              "<br>Diferença consumo−produção: %{customdata[3]}"
                              "<br>Padrão: %{customdata[4]}")
                figo = go.Figure()
                figo.add_trace(go.Bar(
                    y=_ord["produto"], x=_ord["producao_var"], orientation="h",
                    name="Produção", marker_color=DOURADO, customdata=_extra,
                    hovertemplate="<b>%{y}</b><br>Produção: %{customdata[5]}"
                                  + _qualifica + "<extra></extra>"))
                figo.add_trace(go.Bar(
                    y=_ord["produto"], x=_ord["consumo_var"], orientation="h",
                    name="Consumo", marker_color=VERDE, customdata=_extra,
                    hovertemplate="<b>%{y}</b><br>Consumo: %{customdata[6]}"
                                  + _qualifica + "<extra></extra>"))
                figo.update_layout(barmode="group", height=max(470, 43 * len(_ord)),
                                   margin=dict(t=12, b=46, l=10, r=10),
                                   xaxis_title="Variação desde o início da série (%)",
                                   legend=dict(orientation="h", y=-0.07))
                figo.update_xaxes(zeroline=True, zerolinecolor=TEXTO_3, zerolinewidth=1.5)
                grafico(figo)

                _tab_o = pd.DataFrame([{
                    "Produto": r.produto,
                    "Janela medida": (f"{r.inicio.strftime('%m/%Y')} – "
                                      f"{r.fim.strftime('%m/%Y')}"),
                    # “Observações” e não “Períodos”: é a contagem de leituras,
                    # e a coluna ao lado diz quantas caberiam na janela, para
                    # que as séries com falhas se distingam das seguidas.
                    "Observações": int(r.n_periodos),
                    "Caberiam na janela": int(r.periodos_esperados),
                    # Mesmas casas decimais do hover: é o mesmo número, e lido
                    # com precisão diferente nos dois sítios dava a impressão de
                    # serem dois.
                    "Preço na produção: variação na janela": _pct_obs(r.producao_var),
                    "Preço no consumo: variação na janela": _pct_obs(r.consumo_var),
                    "Diferença consumo−produção": _pct_obs(r.diferenca_var),
                    "Padrão": r.padrao,
                } for r in _com_prod.itertuples()])
                # A tabela recolhe-se: tudo o que ela diz está no hover das barras.
                # Não desaparece, passar o rato é apontar com o comando, e há
                # quem leia isto num tablet, quem precise de ordenar por coluna e
                # quem queira copiar os números. É a mesma regra da cor: a
                # informação não pode existir só num canal.
                with st.expander("Os números produto a produto"):
                    st.dataframe(_tab_o, width="stretch", hide_index=True)
                st.caption(
                    "**De que é esta percentagem.** É a variação do **preço em euros por "
                    "unidade** em cada fase, entre o primeiro e o último período da coluna "
                    "“Janela medida”, que é a janela **comum às duas fases**, para que as duas "
                    "colunas sejam comparáveis entre si. Não é uma quota nem uma proporção: "
                    "*+20%* significa que o preço nessa fase está 20% acima do que estava no "
                    "início da janela. A última coluna é a variação da **diferença** entre as "
                    "duas pontas, e mantém-se a ressalva do topo do separador: essa diferença "
                    "não corresponde à margem de nenhum operador."
                )

            # ---- o que os padrões significam ----
            # Duas correções de 13.08.2026, ambas relatadas pela utilizadora:
            #
            # 1. O título dizia “Três padrões” e a lista tinha cinco entradas.
            # 2. “Sem série de produção” não é um padrão de transmissão, é
            #    ausência de dados, e é o maior grupo de todos (22 de 39).
            #    Listado ao lado dos outros, lia-se como uma conclusão da
            #    análise. Passa a ressalva de cobertura, a seguir à lista.
            #
            # A contagem entre parênteses também não estava explicada: um “(13)”
            # isolado tanto podia ser uma percentagem como um índice.
            _SEM_PRODUCAO = "Sem série de produção"
            _contagem = _var["padrao"].value_counts()
            secao(
                "Como se transmitem os preços ao longo da cadeia",
                "Cada produto com as duas fases é classificado pelo sentido em que os "
                "preços se moveram na produção e no consumo.",
                grupo="02 · Transmissão de preços")
            for nome, explicacao in observatorio.PADROES.items():
                if nome == _SEM_PRODUCAO or nome not in _contagem:
                    continue
                _n_pad = int(_contagem[nome])
                exemplos = _var[_var["padrao"] == nome]["produto"].head(4).tolist()
                st.markdown(
                    f"- **{nome}** ({_n_pad} produto{'s' if _n_pad > 1 else ''}), "
                    f"{explicacao} *Ex.: {', '.join(exemplos)}.*"
                )

            _n_sem = int(_contagem.get(_SEM_PRODUCAO, 0))
            if _n_sem:
                st.caption(
                    f"**Cobertura.** {_n_sem} dos {_var['produto'].nunique()} produtos "
                    "seguidos não têm série de preço na produção, para esses o "
                    "Observatório publica apenas o preço ao consumidor, e a comparação "
                    "entre as duas pontas da cadeia não é possível. A classificação acima "
                    f"incide sobre os {len(_com_prod)} produtos com as duas fases."
                )

            _div = _var[_var["padrao"] == "Divergência"]
            if not _div.empty:
                _d = _div.iloc[0]
                # A janela vai **na frase**, e não numa legenda ao lado. Este é o
                # texto mais citável do separador, e é lido em voz alta sem o
                # resto do ecrã à volta: sem a janela, quem o ouve assume doze
                # meses, que é o que o resto da aplicação mede (20.08.2026).
                _jan_d = (f"{mes_extenso(_d['inicio'].strftime('%Y-%m'))} a "
                          f"{mes_extenso(_d['fim'].strftime('%Y-%m'))}")
                st.info(f"""
    **{_d['produto']} apresenta a maior divergência entre as duas fases da cadeia.**

    Entre **{_jan_d}**, o preço na produção
    **desce {percentagem(abs(_d['producao_var']), sinal=False)}** enquanto o
    preço ao consumidor **sobe {percentagem(_d['consumo_var'], sinal=False)}**. A diferença entre
    as duas pontas passa de {euro(_d['diferenca_inicial'])} para {euro(_d['diferenca_final'])}
    por {_d['unidade'] or 'unidade'}.

    **Não é a variação homóloga.** É a variação **acumulada** ao longo de
    {int(_d['n_periodos'])} observações nesse intervalo, ou seja, a distância entre os dois
    extremos da janela. A variação homóloga, que é o que os outros separadores medem, compara
    cada mês com o mesmo mês do ano anterior, e as duas não são comparáveis entre si.

    Os índices de preços no consumidor não captam esta decomposição: para o IHPC, trata-se de mais
    um produto cujo preço subiu. Mantém-se integralmente a ressalva acima: o alargamento da
    diferença não corresponde, por si, à margem de nenhum operador, e pode refletir a mudança de
    forma do produto entre as duas fases.
                """)

            # ---- detalhe por produto ----
            secao("Ver um produto em detalhe",
                  "Série de preço nas duas fases e, quando existem ambas, a "
                  "diferença entre elas.", grupo="03 · Detalhe por produto")
            _lista = sorted(_var["produto"].unique())
            _pref = next((p for p in ("Pescada", "Ovo M", "Cenoura") if p in _lista), _lista[0])
            # Largura fixa, e não “stretch”: em largura total a seta ficava no
            # extremo direito da página, longe do nome do produto, e deixava de se
            # ler como um seletor. Fixa, a seta está sempre à mesma distância da
            # margem esquerda, não acompanha o comprimento do nome escolhido, que
            # aqui vai de “Ovo” a “Queijo Flamengo fatias” (Inês, 13.08.2026).
            _escolhido = st.selectbox(
                "Produto", options=_lista, index=_lista.index(_pref),
                label_visibility="collapsed", width=300)

            _serie = observatorio.serie_produto(_obs, _escolhido)
            _linha = _var[_var["produto"] == _escolhido].iloc[0]

            # O símbolo diz o produto, a cor diz a família. O nome do grupo
            # chegou a acompanhar esta linha, e saiu: escrever "Hortícolas,
            # tubérculos e leguminosas" ao lado de "Brócolo" é dizer em texto
            # longo o que a cor já diz, e o nome da classe COICOP é mais comprido
            # do que o do produto que devia identificar (decisão da Inês,
            # 31.08.2026).
            _sec = _obs.loc[_obs["produto"] == _escolhido, "setor"]
            _sec = _sec.iloc[0] if not _sec.empty else None
            if _sec in SETORES_OBSERVATORIO:
                st.markdown(
                    f'<p class="sg-produto">{icone_setor(_sec, tamanho=17)}'
                    f'<span class="sg-produto__nome">{_html(_escolhido)}</span></p>',
                    unsafe_allow_html=True)

            # A janela deste produto, escrita por extenso, porque **não é a
            # mesma para todos**. Seis dos 39 acabam antes dos restantes, por a
            # série de produção parar mais cedo, e o leite é um deles: o seu
            # número acaba um ano antes do dos vizinhos e nada no ecrã o dizia
            # (relatado pela Inês, 20.08.2026).
            _jan_p = (f"{mes_extenso(_linha['inicio'].strftime('%Y-%m'))} a "
                      f"{mes_extenso(_linha['fim'].strftime('%Y-%m'))}")
            _fim_geral = _var["fim"].max()
            _mais_curta = _linha["fim"] < _fim_geral
            _falhas_p = (
                f" A série tem **falhas**: são {int(_linha['n_periodos'])} observações num "
                f"intervalo onde caberiam {int(_linha['periodos_esperados'])}, porque o "
                "Observatório não publicou este produto em todos os períodos."
                if _linha["tem_falhas"] else "")
            st.caption(
                f"**{_escolhido}: {_jan_p}**, {int(_linha['n_periodos'])} observações. "
                f"No consumo, {_pct_obs(_linha['consumo_var'])}"
                + (f"; na produção, {_pct_obs(_linha['producao_var'])}"
                   if _linha["tem_producao"] else "")
                # “Variação anual” é ambíguo: tanto se lê como “face ao ano
                # anterior” quanto como “por ano”, que aqui seria outra conta.
                # O resto da aplicação diz sempre “variação homóloga”, e é esse
                # o termo que tem de estar aqui (pergunta da Inês, 20.08.2026).
                + ". É a variação **acumulada nessa janela**, ou seja, quanto o preço está "
                  "acima do que estava no início. Não é a **variação homóloga**, a subida "
                  "face ao mesmo mês do ano anterior, que é o que os outros separadores medem."
                + (f" A janela deste produto termina em "
                   f"{mes_extenso(_linha['fim'].strftime('%Y-%m'))}, antes da dos restantes "
                   f"({mes_extenso(_fim_geral.strftime('%Y-%m'))}), porque a sua série de "
                   "produção para aí. O valor não é comparável com o dos produtos de janela "
                   "mais longa." if _mais_curta else "")
                + _falhas_p
            )

            if _serie.empty:
                st.info("Sem série para este produto.")
            else:
                figd2 = go.Figure()
                _cores_f = {"Consumo": VERDE, "Produção": DOURADO}
                for coluna in _serie.columns:
                    figd2.add_trace(go.Scatter(
                        x=_serie.index, y=_serie[coluna], name=coluna, mode="lines",
                        line=dict(color=_cores_f.get(coluna, CINZENTO), width=2.6),
                        hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f} €<extra>" + coluna + "</extra>"))
                if {"Consumo", "Produção"}.issubset(set(_serie.columns)):
                    figd2.add_trace(go.Scatter(
                        x=_serie.index, y=_serie["Consumo"] - _serie["Produção"],
                        name="Diferença", mode="lines",
                        line=dict(color=AZUL, width=1.6, dash="dot"),
                        hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f} €<extra>Diferença</extra>"))
                figd2.update_layout(
                    height=440, margin=dict(t=12, b=34, l=10, r=10),
                    yaxis_title=f"Preço ({_linha['unidade'] or '€'})",
                    hovermode="x unified",
                    legend=dict(orientation="h", y=-0.15))
                figd2.update_yaxes(rangemode="tozero")
                grafico(figd2)

                if not _linha["tem_producao"]:
                    st.info(
                        "O Observatório publica apenas o preço ao consumidor para este produto. "
                        "A comparação com a produção não é possível."
                    )

            st.download_button(
                "Descarregar série completa do Observatório (CSV)",
                csv_com_fonte(
                    _obs.assign(inicio=_obs["inicio"].dt.strftime("%Y-%m-%d")),
                    "Observatório de Preços Agroalimentar, produção e consumo", dados,
                    # Não é Eurostat: estes dados nunca passaram por lá.
                    fonte="GPP, Gabinete de Planeamento, Políticas e Administração Geral",
                    conjuntos=[],
                    extra=[
                        ("Fonte", "GPP, Observatório de Preços Agroalimentar"),
                        ("Recolha", _obs_meta.get("extraido_em", "-")),
                        ("Script", "scripts/recolher_observatorio.py"),
                        ("Nota", "A diferença entre consumo e produção não corresponde "
                                 "à margem de nenhum operador"),
                    ]),
                file_name="observatorio_precos.csv", mime="text/csv")

    # ==========================================================================
    # ABA 3, Simulador de IVA
    # ==========================================================================
with aba3:
    with painel("Simulador de IVA"):
        titulo_pagina(
            "Simulador de IVA",
            "Cenário hipotético de alteração das taxas de IVA sobre a despesa alimentar. "
            "As taxas do cenário e a fração que chega ao consumidor são parâmetros de "
            "quem simula, não são dados oficiais.")

        faixa_fonte()

        # A base de cálculo é herdada, não escolhida aqui: é a mesma que está em
        # “Despesa e composição”, e o simulador é o único separador onde ela
        # altera o resultado sem ser evidente de onde vem. Por isso é declarada,
        # e só aqui: nos restantes separadores a ausência de etiqueta é a
        # informação, quer dizer que aquele separador não responde a este
        # parâmetro (31.08.2026).
        st.markdown(
            f'<p class="sg-heranca">Base de cálculo'
            f'<strong>{_html(base_ancora["nome"])}</strong>'
            f'<span class="sg-heranca__onde">definida em “Despesa e composição”, '
            f'no topo do separador</span></p>',
            unsafe_allow_html=True)

        CENARIOS = {
            "manual": ("Definir manualmente", None),
            "zero": ("“Cabaz zero”, isenção total (precedente de 2023-2024)", 0.0),
            "seis": ("Taxa reduzida (6%) em tudo", 6.0),
            "treze": ("Taxa intermédia (13%) em tudo", 13.0),
        }
        # O estado de sessão persiste entre versões da aplicação. Se ficar com um
        # valor que já não existe nas opções atuais, o Streamlit levanta exceção,
        # por isso valida-se antes de usar.
        if st.session_state.get("cenario_iva") not in CENARIOS:
            st.session_state["cenario_iva"] = "zero"

        secao("Cenário a simular",
              "Escolha as taxas do cenário e a fração que chega ao consumidor. "
              "O resultado, mais abaixo, recalcula-se a cada alteração.",
              grupo="01 · Cenário", topo=True)

        cenario = st.radio(
            "Cenário a simular",
            options=list(CENARIOS.keys()),
            format_func=lambda k: CENARIOS[k][0],
            key="cenario_iva",
        )

        # ---- taxa atual de cada grupo: apurada, não predefinida ----
        # A taxa que cada grupo suporta **hoje** é um facto, não um parâmetro.
        # Até 11.08.2026 a simulação usava a taxa predefinida do grupo, o que
        # equivalia a assumir que toda a despesa do grupo a seguia, e isso
        # subestimava o IVA contido em 25% a 36% (auditoria, D2 reaberto).
        _comp_iva = composicao_iva(dados.get("pesos_subclasses") or {})
        _res_iva = resumo_composicao_iva(_comp_iva) if not _comp_iva.empty else {}
        _tem_apuramento = bool(_res_iva)

        if _tem_apuramento:
            _taxas_ef = taxas_efetivas(_comp_iva)
            _taxas_ef_min = taxas_efetivas(_comp_iva, indeterminado="reduzida")
            _taxas_ef_max = taxas_efetivas(_comp_iva, indeterminado="normal")
        else:
            # Sem os ponderadores por subclasse não há apuramento possível:
            # recorre-se à predefinição e diz-se que se recorreu.
            _taxas_ef = dict(zip(df_decomp["codigo"], df_decomp["iva_defeito"].astype(float)))
            _taxas_ef_min = _taxas_ef_max = _taxas_ef
            st.warning(
                "**Os ponderadores por subclasse não estão disponíveis nesta sessão.** A "
                "simulação recorre à taxa **predefinida** de cada grupo, o que subestima o IVA "
                "contido em cerca de 25% a 36% numa isenção total. Consulte o registo de "
                "ligações no separador Metodologia."
            )

        editor = pd.DataFrame({
            "Grupo": list(df_decomp["classe"]),
            "Valor (€)": df_decomp["valor"].round(2),
            "Taxa média efetiva (%)": [
                round(float(_taxas_ef.get(c, d)), 1)
                for c, d in zip(df_decomp["codigo"], df_decomp["iva_defeito"])],
            "Taxa do cenário (%)": df_decomp["iva_defeito"].astype(float),
        })

        # O editor de taxas guarda estado por chave. Versões anteriores permitiam
        # valores fora da lista legal (era um campo numérico livre); se esse estado
        # sobreviver, o seletor rejeita-o. Limpa-se o que não seja válido.
        for _k in [k for k in list(st.session_state.keys()) if str(k).startswith("editor_iva_")]:
            try:
                _est = st.session_state[_k]
                _edicoes = (_est or {}).get("edited_rows", {}) if isinstance(_est, dict) else {}
                for _linha in list(_edicoes.values()):
                    for _col, _val in list(_linha.items()):
                        if "Taxa" in str(_col) and float(_val) not in (0.0, 6.0, 13.0, 23.0):
                            del st.session_state[_k]
                            raise StopIteration
            except StopIteration:
                continue
            except Exception:                                      # noqa: BLE001
                st.session_state.pop(_k, None)

        taxa_forcada = CENARIOS[cenario][1]
        if taxa_forcada is not None:
            editor["Taxa do cenário (%)"] = float(taxa_forcada)

        # Só as taxas que existem no Código do IVA (continente). Uma caixa de texto
        # livre permitiria valores impossíveis (80%, por exemplo) e produziria
        # resultados sem qualquer significado.
        TAXAS_LEGAIS = [0.0, 6.0, 13.0, 23.0]
        col_taxa = st.column_config.SelectboxColumn(
            options=TAXAS_LEGAIS, required=True,
            help="Taxas em vigor no continente: isenção, reduzida (6%), intermédia (13%), normal (23%).",
        )

        # A chave do editor tem de variar com o cenário: caso contrário o Streamlit
        # mantém o estado do widget e as taxas do cenário nunca chegam à tabela.
        editado = st.data_editor(
            editor, width="stretch", hide_index=True,
            key=f"editor_iva_{cenario}",
            # Linhas com mais ar. O quadro é o controlo central do separador e
            # tinha densidade de folha de cálculo.
            row_height=42,
            # A taxa atual **não é editável**: é apurada, não escolhida.
            disabled=["Grupo", "Valor (€)", "Taxa média efetiva (%)"],
            column_config={
                "Valor (€)": st.column_config.NumberColumn(format="%.2f"),
                # Sem apuramento a coluna não é uma taxa efetiva nenhuma: é a
                # taxa predefinida do grupo. O rótulo e a explicação afirmavam o
                # contrário justamente no caso em que a afirmação era falsa
                # (auditoria de 12.08.2026, L18).
                "Taxa média efetiva (%)": st.column_config.NumberColumn(
                    format="%.1f%%",
                    help=("A taxa única que suporta o mesmo imposto que o conjunto dos "
                          "produtos do grupo. Não corresponde a nenhuma taxa legal "
                          "aplicada: é apurada a partir da composição do grupo por "
                          "subclasse."
                          if _tem_apuramento else
                          "Sem os ponderadores por subclasse nesta sessão, esta coluna "
                          "**não é uma taxa efetiva**: é a taxa predefinida do grupo, que "
                          "subestima o imposto contido.")),
                "Taxa do cenário (%)": col_taxa,
            },
        )

        st.caption(
            ("**A coluna do meio é apurada, não escolhida**, por isso não é editável. "
             if _tem_apuramento else
             "**A coluna do meio é, nesta sessão, a taxa predefinida do grupo**, o apuramento "
             "por subclasse não está disponível, ver o aviso acima. Não é editável. ")
            + "A **taxa do cenário** é o único parâmetro definido pelo utilizador. Só estão "
            "disponíveis as taxas que existem no Código do IVA, isenção, 6%, 13% e 23%."
            + ("" if cenario == "manual" else
               " Escolha “Definir manualmente”, acima, para as alterar grupo a grupo.")
        )

        if cenario == "zero":
            nota("Precedente: o “cabaz zero” de 2023-2024", """
              Entre abril de 2023 e janeiro de 2024 vigorou em Portugal a isenção de IVA
              sobre uma lista taxativa de 46 bens alimentares essenciais (Lei n.º 17/2023,
              de 14 de abril). Duas observações decorrem desse precedente. Primeira: o
              resultado <strong>depende do universo medido</strong>. A ASAE apurou −10,14%
              entre 18 de abril e 4 de setembro de 2023; a DECO, sobre os 41 produtos do seu
              cabaz abrangidos pela isenção, apurou −8,45% ao fim de três meses. Listas,
              períodos e critérios de recolha diferentes produzem resultados diferentes para
              a mesma medida. Segunda: no balanço final do período (18 de abril de 2023 a 4
              de janeiro de 2024) esse cabaz de 41 produtos tinha <strong>subido
              4,71%</strong> (de 136,83 € para 143,28 €), tendo o efeito da isenção sido
              progressivamente compensado pela subida dos preços de base. O efeito de uma
              alteração de taxa sobre o nível de preços é pontual e não altera, por si, a
              trajetória subsequente. O cursor de repercussão permite explorar esta
              distinção.""")

        componente("Fração da redução do imposto transmitida ao preço final")
        # O valor de partida é calibrado, não escolhido: vem da avaliação do
        # Banco de Portugal ao “IVA zero” de 2023. Até 12.08.2026 partia de
        # 40%, um parâmetro de trabalho sem fonte portuguesa, que a
        # evidência contraria por um fator de 2,4 (auditoria, F1).
        repercussao = st.slider(
            "Fração que chega ao consumidor", 0, 100,
            int(round(REPERCUSSAO_PADRAO * 100)), 5,
            format="%d%%", label_visibility="collapsed",
        ) / 100

        ao_consumidor = int(round(repercussao * 100))
        na_margem = 100 - ao_consumidor
        st.markdown(f"""
<div class="sg-reparticao">
  Por cada <strong>1,00 €</strong> de imposto que o Estado deixa de cobrar:
  <div class="sg-reparticao__par">
    <div style="flex:1">
      <div class="sg-reparticao__val" style="color:{VERDE}">{ao_consumidor} cêntimos</div>
      <div class="sg-reparticao__rot">reduzem o preço final, poupança do consumidor</div>
    </div>
    <div style="flex:1">
      <div class="sg-reparticao__val" style="color:{DOURADO}">{na_margem} cêntimos</div>
      <div class="sg-reparticao__rot">são retidos na margem do operador</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        _rho_lo, _rho_central, _rho_hi = repercussao_banda()
        _est_rho = estimativas_repercussao()

        with st.expander(
                f"Calibração do valor de partida do cursor "
                f"({numero(_rho_central * 100, 0)}%)"):
            st.markdown("""
    Quando o Estado reduz o IVA, **não é garantido que o preço final desça na mesma medida**.
    Parte da redução pode ficar retida na margem do operador. A esse fenómeno chama-se
    *repercussão*, e é o parâmetro que determina a repartição do efeito entre consumidor e
    operador. **É o parâmetro que mais influencia o resultado desta ferramenta**: a poupança é
    proporcional a ele, pelo que entre 0% e 100% varia de zero ao máximo. Nenhuma outra
    incerteza desta aplicação tem esta amplitude.

    ##### Portugal já correu esta experiência

    A Lei n.º 17/2023, de 14 de abril, isentou de IVA 46 bens alimentares entre 18 de abril de
    2023 e 4 de janeiro de 2024, a maioria com taxa anterior de 6%. O **Banco de Portugal**
    avaliou a repercussão por quatro vias independentes. Não se trata de um caso análogo noutro
    país e noutro setor: é **a medida idêntica, no mesmo país, no retalho alimentar**.

    ##### Como se extrai a repercussão dos números publicados

    O Banco de Portugal publica a variação **observada** e a variação **mecânica**, que é a que
    resultaria se a redução fosse integralmente transmitida ao preço. A repercussão é o quociente
    das duas:
    """)
            st.latex(r"\rho = \frac{\text{variação observada}}{\text{variação mecânica}}"
                     r"\qquad\text{com}\qquad "
                     r"\text{mecânica} = \frac{1+t_1}{1+t_0}-1")
            st.markdown(
                "| Estimativa | Observado | Mecânico | **ρ implícito** |\n"
                "|---|---|---|---|\n"
                + "\n".join(
                    f"| {r['estimativa']} | −{numero(r['observado'], 1)}% | "
                    f"−{numero(r['mecanico'], 2)}% | **{numero(r['rho'] * 100, 1)}%** |"
                    for _, r in _est_rho.iterrows())
            )
            st.markdown(f"""
    **Nenhum destes ρ é citado; todos são calculados aqui**, a partir dos dois valores que o Banco
    de Portugal publica. A coluna é um cálculo desta aplicação sobre dados do Banco de Portugal.

    **Verificação da concordância aritmética:** os óleos alimentares estavam a 23% e o Banco de
    Portugal publica um efeito mecânico de −18,7%. A fórmula desta aplicação dá
    **{numero(efeito_mecanico_pct(23, 0), 2).replace("-", "−")}%**. Os valores coincidem, e a
    coincidência está verificada por teste automático; sem ela, a derivação acima não seria
    válida.

    **Efeito da diluição sobre o quociente:** as rubricas do IHPC incluem bens não abrangidos pela
    medida, o que atenua a variação observada *e* a mecânica. Como atenua ambas na mesma
    proporção, o quociente mantém-se. É por essa razão que a derivação é admissível apesar da
    granularidade insuficiente que o próprio Banco de Portugal assinala.

    ##### Porquê {numero(_rho_central * 100, 0)}% e não a média das quatro

    Das quatro estimativas, só as **duas de diferença-nas-diferenças** têm contrafactual: as de
    preços online medem uma janela de duas semanas e dão **acima de 100%**, o que reflete
    provavelmente concorrência e saliência política, não repercussão pura. Entre as duas de
    diferença-nas-diferenças toma-se a de **Espanha como controlo**,
    {numero(_est_rho['rho'].iloc[0] * 100, 1)}%, que é a única cujo contrafactual o BdP
    declara **estatisticamente confirmado**.

    **É a mais alta das duas, e não a mais conservadora**: a de controlo da área do euro dá
    {numero(_est_rho['rho'].iloc[1] * 100, 1)}%. O critério é a qualidade do contrafactual e não a
    prudência, e é por essa razão que a estimativa mais baixa não é descartada: **constitui o
    extremo inferior da banda** apresentada com os indicadores, que vai de
    **{numero(_rho_lo * 100, 1)}%** (área do euro) a **{numero(_rho_hi * 100, 0)}%** (integral).
    A leitura conservadora obtém-se fixando o cursor nos {numero(_rho_lo * 100, 0)}%, com
    recálculo automático de todos os valores.

    ##### Ressalvas que integram a estimativa

    1. O próprio Banco de Portugal assinala **desvios-padrão elevados** e recomenda cautela na
       interpretação.
    2. Tratou-se de uma medida **temporária, taxativa e com forte exposição pública**, com
       pressões de custo a montante já em redução e acompanhamento público do setor. Uma
       alteração permanente e sem essa exposição pode repercutir-se menos.
    3. A janela avaliada estende-se até **agosto de 2023, quatro meses**. Não existe, nesta
       avaliação, evidência sobre a erosão do efeito a prazo. Repercussão elevada e efeito
       duradouro são propriedades distintas: no balanço de todo o período, o cabaz da DECO tinha
       **subido 4,71%**, com a inflação de base a superar a redução do imposto.
    4. A evidência robusta incide sobre reduções **a partir de 6%**. Para a taxa de 23% existe um
       único produto.
    5. Os valores acima de 100% das duas estimativas de preços em linha não são adotados: por
       omissão não se admite repercussão superior à integral.

    ##### Efeito adicional que a simulação evidencia

    **A repercussão determina sobretudo a repartição do efeito** entre consumidor e operador, e só
    marginalmente o montante que o Estado deixa de cobrar. Numa isenção total a receita cessante é
    independente da repercussão; numa redução parcial não é, porque uma repercussão menor mantém
    o preço final mais alto e, com ele, uma base tributável maior. No exemplo de 106 € com descida
    de 23% para 6%, a receita cessante vai de **−13,82 €** (repercussão 0%) a **−14,65 €**
    (repercussão 100%), cerca de 6% de amplitude.

    **Fonte:** {REPERCUSSAO_FONTE}.
            """)



        # A taxa atual vem do apuramento e nunca do editor: mesmo que um estado
        # de sessão antigo traga a coluna antiga, é ignorada.
        taxas_atuais = {c: float(_taxas_ef.get(c, d))
                        for c, d in zip(df_decomp["codigo"], df_decomp["iva_defeito"])}
        taxas_cenario = dict(zip(df_decomp["codigo"], editado["Taxa do cenário (%)"]))

        sim = simular_iva(df_decomp, taxas_atuais, taxas_cenario, repercussao)
        res = resumo_iva(sim, despesa_mensal, vezes_ano, agregados)

        # Extrapolação nacional: parte do **agregado médio**, não da composição
        # escolhida na barra lateral. Multiplicar uma despesa ajustada a “2
        # adultos” pelos 4,1 milhões de agregados dava um total nacional que
        # mudava com quem estava a olhar para o ecrã, de −14% a +92% conforme
        # a composição (auditoria de 10.08.2026, A3).
        _sim_nac = simular_iva(decompor(media_agregado, dados["pesos"],
                                        dados["variacoes_classe"]),
                               taxas_atuais, taxas_cenario, repercussao)
        res_nac = resumo_iva(_sim_nac, media_agregado, vezes_ano, agregados)

        # Sensibilidade à parcela indeterminada: os dois extremos são a mesma
        # simulação com a parcela não repartível levada toda a 6% e toda a 23%.
        _res_band = None
        if _tem_apuramento and _res_iva["indeterminado_pct"] > 0.05:
            _band = []
            for _t in (_taxas_ef_min, _taxas_ef_max):
                _band.append(resumo_iva(
                    simular_iva(df_decomp, {c: float(_t.get(c, d)) for c, d
                                            in zip(df_decomp["codigo"], df_decomp["iva_defeito"])},
                                taxas_cenario, repercussao),
                    despesa_mensal, vezes_ano, agregados))
            _res_band = sorted(b["poupanca_mes"] for b in _band)

        # Sensibilidade à repercussão: os extremos da banda calibrada com a
        # avaliação do BdP ao “IVA zero” de 2023 (config, REPERCUSSAO_BANDA).
        # É a maior das incertezas do simulador, e por isso é a que aparece
        # primeiro, antes da parcela indeterminada, que move 3,4 vezes menos.
        _band_rho = sorted(
            (resumo_iva(simular_iva(df_decomp, taxas_atuais, taxas_cenario, _r),
                        despesa_mensal, vezes_ano, agregados)["poupanca_mes"],
             resumo_iva(simular_iva(decompor(media_agregado, dados["pesos"],
                                             dados["variacoes_classe"]),
                                    taxas_atuais, taxas_cenario, _r),
                        media_agregado, vezes_ano,
                        agregados)["poupanca_agregada_milhoes"])
            for _r in (_rho_lo, _rho_hi))

        # Os rótulos seguem o **sinal**, como no separador 1. Um cenário que
        # sobe as taxas, “13% em tudo” sobe-as à maioria dos grupos, cujas
        # taxas efetivas ficam abaixo disso, produzia “Poupança por mês:
        # −4,37 €”, que obriga a uma dupla negação, e “Capturado na margem:
        # −1,87 €”, que é pior: nesse caso a margem não capturou nada, absorveu
        # parte da subida, o que é favorável ao consumidor e aparecia com sinal
        # negativo. É o defeito que o M2 corrigiu na capa e que tinha ficado por
        # corrigir aqui (relatado pela utilizadora, 13.08.2026).
        _sobe = res["poupanca_mes"] < -0.005
        _rot_pou = "Agravamento por mês" if _sobe else "Poupança por mês"
        _rot_pou_ano = ("Agravamento anual por agregado" if _sobe
                        else "Poupança anual por agregado")
        _rot_margem = "Absorvido pela margem" if _sobe else "Capturado na margem"
        _ajuda_margem = (
            "Parte da subida do imposto que o vendedor absorveu em vez de a passar "
            "ao preço." if _sobe else
            "Parte da descida do imposto que ficou na margem em vez de descer o preço.")

        # A descrição diz só a base: a composição, o cenário e a repercussão
        # passaram a estar no próprio cartão do resultado, e repeti-las aqui
        # punha a mesma frase duas vezes com um centímetro de intervalo.
        secao("Resultado do cenário",
              f"Na base <strong>{base_ancora['nome']}</strong>.",
              grupo="02 · Resultado do cenário")

        # A nova despesa mensal é o número que o cenário produz: passa a
        # indicador de capa desta secção, com a variação em euros ao lado, e
        # deixa de ser o primeiro de cinco cartões iguais.
        #
        # Sinal e cor. Uma descida da despesa alimentar é **bom** para o
        # agregado: a seta por omissão do Streamlit pintava a poupança de
        # vermelho e a fatia capturada na margem de verde a subir, as duas ao
        # contrário do que significam (auditoria de 12.08.2026, L20).
        # A leitura desta secção e a passagem da despesa atual para a do
        # cenário, e a diferenca entre as duas. As tres grandezas ficam no mesmo
        # cartao, em tres registos: o valor de partida em corpo de metadado, o
        # valor novo como numero de capa, a diferenca a direita.
        _efeito = res["efetivo"]
        indicador_principal(
            "Nova despesa alimentar mensal",
            euro(res["novo_valor"]),
            antes=f"Despesa atual <strong>{euro(despesa_mensal)}</strong> por mês",
            contexto=(f"Cenário <strong>{CENARIOS[cenario][0]}</strong> · "
                      f"repercussão de <strong>{ao_consumidor}%</strong> · "
                      f"agregado com <strong>{composicao}</strong>"),
            sec_valor=(euro(_efeito) if abs(_efeito) > 0.005 else None),
            sec_rotulo="variação por mês",
            sec_cor=(None if abs(_efeito) <= 0.005
                     else (VERDE if _efeito < 0 else VERMELHO)))

        c = st.columns(4)
        c[0].metric(_rot_pou, euro(abs(res["poupanca_mes"])),
                    help=f"Efeito com repercussão integral: "
                         f"{euro(abs(res['mecanico']))}")
        c[1].metric(_rot_pou_ano, euro(abs(res["poupanca_ano"])))
        c[2].metric(_rot_margem, euro(abs(res["margem"])),
                    f"{(1 - repercussao) * 100:.0f}% do efeito",
                    delta_color="off", help=_ajuda_margem)
        # O valor e a **variacao** da receita, nao o seu nivel. O rotulo dizia
        # “Receita de IVA por mês” e mostrava −22,24 €, o que sugeria uma receita
        # negativa. O cartão agregado, dois abaixo, já lhe chamava “Variação de
        # receita implícita” (auditoria de 12.08.2026, K9).
        c[3].metric("Variação da receita de IVA por mês", euro(res["receita_mes"]),
                    help=(f"Imposto contido na despesa deste agregado: "
                          f"{euro(res['iva_antes'])} → {euro(res['iva_depois'])}. "
                          "O valor apresentado é a diferença entre os dois."))

        fig_rep = grafico_reparticao(sim)
        if fig_rep is not None:
            secao("Como se reparte o benefício",
                  "<strong>Cada barra é o efeito total da medida nesse grupo, dividido "
                  "em duas partes.</strong> A verde, o que reduz o preço final; "
                  "a dourado, o que é retido na margem do operador.",
                  grupo="03 · Como se distribui o benefício")
        else:
            secao("Como se reparte o benefício", grupo="03 · Como se distribui o benefício")
        if fig_rep is not None:
            grafico(fig_rep)
        else:
            st.info("Defina um cenário diferente das taxas atuais para ver a repartição.")


        # --- sensibilidade à base de cálculo ---
        # Calculada aqui, e não dentro do bloco recolhível onde vivia, porque a
        # síntese visível logo abaixo precisa destes valores. É a mesma conta,
        # no mesmo sítio da leitura; o que mudou foi quem a consome.
        if outra_ancora is not None:
            _despesa_outra = despesa_do_agregado(
                float(outra_ancora["valor"]), dim_efetiva, adultos, criancas, escala_chave)
            _decomp_outra = decompor(_despesa_outra, dados["pesos"], dados["variacoes_classe"])
            _sim_outra = simular_iva(_decomp_outra, taxas_atuais, taxas_cenario, repercussao)
            _res_outra = resumo_iva(_sim_outra, _despesa_outra, vezes_ano, agregados)
            # O agregado nacional da outra âncora segue a mesma regra do da âncora
            # ativa: parte do agregado médio, não da composição escolhida.
            _media_outra = float(outra_ancora["valor"])
            _res_outra_nac = resumo_iva(
                simular_iva(decompor(_media_outra, dados["pesos"], dados["variacoes_classe"]),
                            taxas_atuais, taxas_cenario, repercussao),
                _media_outra, vezes_ano, agregados)

        # --- a amplitude, à vista ---
        # As quatro notas de sensibilidade estão recolhidas desde 13.08.2026, e
        # bem: são quatro parágrafos, e a demonstração de cada uma não pertence
        # ao meio da leitura. Mas recolhê-las inteiras escondia também **o
        # facto**, que é material para interpretar o número de capa: a diferença
        # entre as duas bases oficiais anda perto de um fator de 2, e quem não
        # abrisse o bloco lia o resultado como se fosse único.
        #
        # Fica visível a grandeza, e recolhida a demonstração. Duas frases, em
        # corpo de legenda: os dois pressupostos de maior amplitude, com os
        # valores que já estão calculados, e nada mais (pedido da Inês,
        # 01.09.2026).
        _amp = []
        if outra_ancora is not None:
            _amp.append(
                f"com a outra base oficial (**{outra_ancora['nome']}**) seria "
                f"**{euro(_res_outra['poupanca_mes'])}**")
        if abs(_band_rho[1][0] - _band_rho[0][0]) > 0.005:
            _amp.append(
                f"entre os extremos publicados da repercussão, de "
                f"**{euro(_band_rho[0][0])}** a **{euro(_band_rho[1][0])}**")
        if _amp:
            st.caption(
                f"**Amplitude.** A poupança mensal acima é de "
                f"**{euro(abs(res['poupanca_mes']))}**: " + "; ".join(_amp)
                + ". O detalhe destes e dos restantes pressupostos, a seguir.")

        with st.expander("Amplitude de variação destes valores"):
            if abs(_band_rho[1][0] - _band_rho[0][0]) > 0.005:
                st.caption(
                    f"**Sensibilidade à repercussão, a maior incerteza desta ferramenta.** "
                    f"O cursor parte de **{numero(_rho_central * 100, 0)}%**, calibrado com a "
                    f"avaliação do Banco de Portugal ao “IVA zero” de 2023. Entre os extremos das "
                    f"estimativas publicadas, {numero(_rho_lo * 100, 1)}% (contrafactual da área "
                    f"do euro) e {numero(_rho_hi * 100, 0)}% (repercussão integral), a poupança "
                    f"mensal fica entre **{euro(_band_rho[0][0])}** e **{euro(_band_rho[1][0])}**, "
                    f"e a agregada anual entre **{milhoes(_band_rho[0][1])}** e "
                    f"**{milhoes(_band_rho[1][1])}**. Qualquer outro valor pode ser obtido "
                    "no cursor."
                )

            # Sensibilidade às parcelas atribuídas **por predominância**. Até
            # 12.08.2026 a aplicação mostrava banda para a parcela indeterminada
            # (5,9% do cabaz) e nenhuma para esta (20,1%), que move o resultado
            # 3,4 vezes mais, mostrava a incerteza pequena e escondia a grande
            # (auditoria de 12.08.2026, F4).
            _res_band_pred = None
            if _tem_apuramento and _res_iva.get("por_predominancia_pct", 0) > 0.05:
                _bp = []
                for _p in ("reduzida", "normal"):
                    _tp = taxas_efetivas(_comp_iva, predominancia=_p)
                    _bp.append(resumo_iva(
                        simular_iva(df_decomp,
                                    {c: float(_tp.get(c, d)) for c, d
                                     in zip(df_decomp["codigo"], df_decomp["iva_defeito"])},
                                    taxas_cenario, repercussao),
                        despesa_mensal, vezes_ano, agregados))
                _res_band_pred = sorted(b["poupanca_mes"] for b in _bp)

            if _res_band_pred is not None and abs(_res_band_pred[1] - _res_band_pred[0]) > 0.005:
                st.caption(
                    f"**Sensibilidade às atribuições por predominância, limite exterior.** "
                    f"{percentagem(_res_iva['por_predominancia_pct'], sinal=False)} do cabaz está em subclasses cuja "
                    "taxa foi atribuída por **juízo sobre a rubrica**, e não por leitura inequívoca "
                    "das Listas, o **pão** a 6%, onde a AT excluiu o pré-cozido congelado; o "
                    "bacalhau seco a 6%, onde o fumado fica a 23%; os pré-preparados a 23%. Se "
                    "**todas** essas atribuições estivessem erradas ao mesmo tempo e no mesmo "
                    f"sentido, a poupança mensal ficaria entre **{euro(_res_band_pred[0])}** e "
                    f"**{euro(_res_band_pred[1])}**. É um **limite exterior e não um intervalo "
                    "plausível**: não há fundamento para admitir que a totalidade do pão vendido "
                    "seja pré-cozido congelado. O seu propósito é evidenciar que esta parcela "
                    "tem maior peso do que a indeterminada, apresentada a seguir."
                )

            if _res_band is not None and abs(_res_band[1] - _res_band[0]) > 0.005:
                st.caption(
                    f"**Sensibilidade à parcela indeterminada.** "
                    f"{percentagem(_res_iva['indeterminado_pct'], sinal=False)} do cabaz está em subclasses que "
                    "atravessam taxas em proporção não repartível. Levando essa parcela toda à taxa "
                    f"reduzida ou toda à normal, a poupança mensal fica entre "
                    f"**{euro(_res_band[0])}** e **{euro(_res_band[1])}**. Os valores acima usam, "
                    "para essa parcela, a taxa predefinida do grupo **confinada ao intervalo em que "
                    "a lei situa cada subclasse**, que nem sempre vai de 6% a 23%: os cereais de "
                    "pequeno-almoço estão entre 13% e 23%, e nunca a 6%."
                )

            # A conta subiu para antes do bloco, que é onde a síntese visível a
            # consome. A nota fica: aqui é que estão a explicação e o valor
            # agregado anual, que a síntese não leva.
            if outra_ancora is not None:
                st.caption(
                    f"**Sensibilidade à base de cálculo.** Estes valores usam a base "
                    f"**{base_ancora['nome']}**. Com **{outra_ancora['nome']}**, a poupança mensal "
                    f"seria {euro(_res_outra['poupanca_mes'])} em vez de {euro(res['poupanca_mes'])}, "
                    f"e a poupança agregada anual "
                    f"{milhoes(_res_outra_nac['poupanca_agregada_milhoes'])} "
                    f"em vez de {milhoes(res_nac['poupanca_agregada_milhoes'])}. "
                    "Todos os resultados do simulador escalam proporcionalmente com a âncora, "
                    "a repartição entre consumidor e margem não depende dela."
                )
            else:
                st.caption(
                    f"**Sensibilidade à base de cálculo.** Estes valores usam a base "
                    f"**{base_ancora['nome']}**, a única disponível nesta sessão. Todos os "
                    "resultados do simulador escalam proporcionalmente com a âncora, pelo que a "
                    "amplitude entre bases (que normalmente é próxima de um fator de 2) não pode "
                    "ser apresentada."
                )


        # Os números primeiro, a explicação a seguir e recolhida. Antes vinham
        # dois parágrafos de legenda e só depois os dois valores, que são a
        # razão de ser da secção (decisão da Inês, 13.08.2026).
        secao("Ordens de grandeza a nível agregado",
              "O mesmo cenário aplicado ao país, a partir do agregado médio.")
        # Mesmo tratamento de sinal do bloco por agregado. O agregado nacional
        # pode divergir em sentido do individual? Não: ambos derivam do mesmo
        # cenário de taxas, pelo que o sinal é o mesmo, mas lê-se do próprio
        # valor, e não do `_sobe` acima, para não depender dessa suposição.
        _sobe_nac = res_nac["poupanca_agregada_milhoes"] < 0
        g1, g2 = st.columns(2)
        g1.metric("Agravamento agregado anual" if _sobe_nac else "Poupança agregada anual",
                  milhoes(abs(res_nac["poupanca_agregada_milhoes"])))
        g2.metric("Variação de receita implícita",
                  milhoes(res_nac["receita_agregada_milhoes"]))
        st.caption(
            f"Extrapolação para {numero(agregados)} agregados, a partir do **agregado "
            f"médio** ({euro(media_agregado)}/mês). **Não mudam com a composição "
            "escolhida em “Despesa e composição”**, só com a base de despesa e com o cenário."
        )

        with st.expander("Definição dos dois indicadores agregados"):
            st.markdown(
                f"**Número de agregados utilizado ({numero(agregados)}).** É o total mais "
                f"recente ({dados.get('agregados_ano') or '—'}), porque o que se extrapola é "
                "o efeito de uma medida sobre a população atual. É por isso um número "
                "diferente do denominador da âncora das Contas Nacionais, que tem de "
                "ser o do ano da despesa.\n\n"
                "**Utilização do agregado médio e não da composição selecionada.** "
                "Multiplicar uma despesa já ajustada a uma composição específica pelo total "
                "nacional equivaleria a admitir que todos os agregados do país têm essa "
                "composição. O desvio resultante é quantificável: −14% para dois adultos "
                "e +92% para cinco."
            )
            if base_chave == "contas":
                # Cada passo está justificado, B2 para o denominador, A3 para o
                # multiplicador, mas o produto não é nenhum dos dois anos. Tem de
                # estar escrito ao lado do número (auditoria de 11.08.2026, E15).
                st.warning(
                    f"**Na base Contas Nacionais este número combina três momentos:** o "
                    f"**consumo real de {base_ancora['ano_base']}**, a **preços de "
                    f"{_mes_txt}**, sobre a **população de agregados de "
                    f"{dados.get('agregados_ano') or '—'}**. Cada passo está justificado, "
                    "o denominador da âncora tem de ser contemporâneo da despesa, e o que "
                    "se extrapola é o efeito de uma medida sobre o país de hoje, mas o "
                    "produto **não é uma medição de nenhum ano**. Leia-o como ordem de "
                    "grandeza, não como estimativa."
                )

        # A ressalva antiga dizia “não é custo orçamental” sem dizer porquê nem
        # quanto. Confrontar as duas bases dá a ordem de grandeza do desvio e
        # mostra que não são uma melhor e outra pior: são bases de perguntas
        # diferentes (auditoria de 12.08.2026, F5).
        #
        # Os quatro números deste bloco estavam **inscritos à mão**, 15 400 M€,
        # 28 188 M€, 33 038 M€ e “1,8 a 2,1 vezes”, dois deles ao lado de
        # números calculados em direto, e o valor das Contas Nacionais estava
        # escrito ao lado do sítio de onde podia vir. Deixavam de bater certo no
        # dia em que o Eurostat publicasse outro ano (auditoria, K8; é a terceira
        # ocorrência do padrão do C2 e do E9).
        #
        # E o bloco estava escrito **como se a base ativa fosse sempre o IDF**.
        # Com a base Contas Nacionais o numerador do rácio é a própria fonte com
        # que se está a comparar, e o resultado invertia-se: a aplicação
        # anunciava “as duas bases não estão perto uma da outra” e a seguir
        # “33 038 M€, 0,9 vezes mais”, o que não é sequer uma frase possível.
        # Ao mesmo tempo dizia medir “a despesa das famílias residentes, apurada
        # por inquérito” quando a base ativa não era um inquérito
        # (auditoria de 12.08.2026, L1).
        # A nota trazia a seguir o confronto numérico entre a base do simulador e
        # a despesa alimentar das Contas Nacionais, rácio, denominadores, anos.
        # É verdadeiro e continua a valer, mas é aparelho metodológico no meio de
        # uma advertência que tem de se ler em três segundos. Fica só a
        # advertência (decisão da Inês, 13.08.2026); o confronto entre bases está
        # no separador Metodologia, em “Em que conceito estão as Contas
        # Nacionais” e “Duas bases de ponderação”.
        if base_chave == "contas":
            _abertura = (
                "Esta ferramenta mede o <strong>impacto nas famílias</strong>. Nesta sessão "
                "está a fazê-lo sobre a base das <strong>Contas Nacionais</strong>, escolhida "
                "em “Despesa e composição”. O <strong>custo orçamental</strong> é outra pergunta: o IVA "
                "é cobrado sobre transações reais, e uma estimativa de receita cessante exige a "
                "base tributável, não a despesa alimentar doméstica repartida por agregado.")
        else:
            _abertura = (
                "Esta ferramenta mede o <strong>impacto nas famílias</strong>, e mede-o na base "
                "própria dessa pergunta: a despesa das famílias residentes, apurada por "
                "inquérito. O <strong>custo orçamental</strong> é outra pergunta, e pede outra "
                "base, o IVA é cobrado sobre transações reais, que são o que as Contas "
                "Nacionais medem.")

        nota("Isto não é uma estimativa de custo orçamental", _abertura, alerta=True)

        # ------------------------------------------------------------------
        # Quem recebe o quê. O simulador diz **quanto**; esta secção diz **a
        # quem**, e as duas leituras apontam em sentidos opostos, ambas
        # verdadeiras. Sem isto, a ferramenta responde a metade da pergunta que
        # uma decisão de política exige (auditoria de 12.08.2026, F3).
        # ------------------------------------------------------------------

        secao("Distribuição do efeito por quintil de rendimento (medida em 2023)",
              grupo="04 · Efeito por rendimento")
        st.caption(
            "O simulador quantifica **o montante** da medida; esta secção caracteriza **a quem** "
            "chega. O Banco de Portugal mediu ambas as dimensões no “IVA zero” de 2023, com "
            "resultados que apontam em sentidos opostos sem que nenhum esteja incorreto.  \n"
            f"A medida entrou em vigor a **{IVA_ZERO_INICIO}** e isentou um cabaz de "
            f"**{IVA_ZERO_N_ALIMENTOS} alimentos**, a maioria já à taxa reduzida."
        )

        _q1, _q2 = st.columns(2)
        with _q1:
            # Era uma tabela de 6×3: vinte e quatro números para o leitor extrair
            # dois. Passa a barras, na mesma orientação do painel da direita, para
            # que o par se leia de relance, desce mais em baixo, chega mais acima.
            # A tabela completa, com as colunas de contexto do IPC, está na
            # Metodologia (decisão da Inês, 13.08.2026).
            _inf = pd.DataFrame(
                IVA_ZERO_INFLACAO_QUINTIL,
                columns=["Quintil", "Bens alimentares afetados", "Bens alimentares", "IPC total"])
            # “Total de famílias” não é um quintil: entra como referência, na cor
            # neutra, e não como sexta barra a competir com as cinco. O que a linha
            # é diz-se no subtítulo e não numa anotação dentro do gráfico, o
            # espaço à esquerda da linha é estreito, e o rótulo sairia da área.
            _ref_inf = _inf[_inf["Quintil"] == "Total de famílias"]
            _txt_ref = ""
            if not _ref_inf.empty:
                _txt_ref = (" A tracejado, a média de todas as famílias "
                            f"({pontos(float(_ref_inf['Bens alimentares afetados'].iloc[0]), casas=1)}).")
            componente("Redução da inflação: maior nos quintis inferiores de rendimento",
                       "Quanto desceram, em maio de 2023, os preços dos produtos abrangidos "
                       "pelo IVA zero, face ao mês anterior." + _txt_ref)
            _qs_inf = _inf[_inf["Quintil"] != "Total de famílias"]
            _fig_inf = go.Figure()
            _fig_inf.add_trace(go.Bar(
                y=_qs_inf["Quintil"], x=_qs_inf["Bens alimentares afetados"],
                orientation="h", marker_color=VERDE, showlegend=False,
                hovertemplate="%{y}<br>%{x} p.p.<extra></extra>"))
            if not _ref_inf.empty:
                _fig_inf.add_vline(
                    x=float(_ref_inf["Bens alimentares afetados"].iloc[0]),
                    line=dict(color=NEUTRO, width=1, dash="dot"))
            _fig_inf.update_layout(
                height=320, margin=dict(t=32, b=34, l=10, r=10),
                xaxis_title="Variação em pontos percentuais")
            grafico(_fig_inf)

        with _q2:
            componente("Afetação do custo orçamental: maior nos quintis superiores de rendimento",
                       "De cada 100 € de custo orçamental de cada medida, que parcela foi "
                       "afeta aos 20% de menor rendimento e que parcela aos 20% de maior "
                       "rendimento.")
            _afet = pd.DataFrame(IVA_ZERO_AFETACAO_ORCAMENTAL,
                                 columns=["Medida", "pobres", "ricos"])
            _fig_af = go.Figure()
            _fig_af.add_trace(go.Bar(
                y=_afet["Medida"], x=_afet["pobres"], name="20% de menor rendimento",
                orientation="h", marker_color=VERDE,
                hovertemplate="%{y}<br>20% de menor rendimento: %{x}%<extra></extra>"))
            _fig_af.add_trace(go.Bar(
                y=_afet["Medida"], x=_afet["ricos"], name="20% de maior rendimento",
                orientation="h", marker_color=DOURADO,
                hovertemplate="%{y}<br>20% de maior rendimento: %{x}%<extra></extra>"))
            _fig_af.update_layout(
                barmode="group", height=320, margin=dict(t=32, b=34, l=10, r=10),
                legend=dict(orientation="h", y=1.16, x=0),
                xaxis_title="% do custo orçamental da medida")
            grafico(_fig_af)

        # Os cinco números desta caixa estavam inscritos à mão ao lado dos dois
        # que já vinham do `config`, “−4,4 pp”, “−3,7 pp”, “71%” e o “mais
        # 20%”, e nenhum deles é dedutível das tabelas que estão logo acima
        # sem os reler. É a quarta ocorrência do padrão do C2/E9/K8
        # (auditoria de 12.08.2026, L16). Passam todos a sair das constantes.
        _iva_pobres, _iva_ricos = next(
            (p, r) for m, p, r in IVA_ZERO_AFETACAO_ORCAMENTAL if m == "Redução do IVA")
        _q_inf = {q: a for q, a, _b, _c in IVA_ZERO_INFLACAO_QUINTIL}
        _pp_q1 = _q_inf.get("Q1 (mais baixo)")
        _pp_q5 = _q_inf.get("Q5 (mais elevado)")
        # A citação vem inteira do `config`, verbatim. Estava aqui montada à volta
        # de `round((23 / 19 - 1) * 100)` = **21%**, dentro de aspas atribuídas ao
        # Banco de Portugal, que escreveu **20%**, o BdP partiu dos valores não
        # arredondados, e a derivação a partir das percentagens publicadas não lhes
        # chega. Confrontado com a p. 9 do WAPP em 13.08.2026.
        # O parágrafo que aqui estava descrevia por palavras o gráfico da direita,
        # que medida dirigiu que fração a que quintil. Fica a conclusão, que o
        # gráfico não dá, e sai a enumeração, que ele já dá.
        #
        # Entra em contrapartida o que a tabela escondia e as barras mostram: o
        # alívio **não é monótono** ao longo da distribuição. Afirmar “maior nos
        # mais pobres” com o Q4 acima do Q1 à vista seria contradizer o gráfico
        # logo por cima. A frase é condicional aos dados, e não uma asserção fixa:
        # se a série passar a ser monótona, desaparece sozinha.
        _q_ordem = [r for r in IVA_ZERO_INFLACAO_QUINTIL if r[0] != "Total de famílias"]
        _pico = min(_q_ordem, key=lambda r: r[1]) if _q_ordem else None
        _frase_pico = ""
        if _pico is not None and _q_ordem and _pico[0] != _q_ordem[0][0]:
            _frase_pico = (
                f"A redução <strong>não cresce de forma regular ao longo da distribuição</strong>: "
                f"o valor mais elevado situa-se no {_pico[0]} ({pontos(_pico[1], casas=1)}) e não "
                f"no primeiro quintil. O contraste que a série sustenta é o dos extremos. ")
        nota("As duas leituras são simultaneamente válidas", f"""
          A redução do IVA produz maior <strong>redução da inflação</strong> nos quintis de menor
          rendimento, {pontos(_pp_q1, casas=1)} no Q1 contra {pontos(_pp_q5, casas=1)} no Q5,
          por a alimentação ter maior peso no seu cabaz, e <strong>afeta</strong> simultaneamente
          maior parcela do custo orçamental aos quintis de maior rendimento:
          {_iva_ricos}% para os 20% de maior rendimento e {_iva_pobres}% para os 20% de menor
          rendimento. O Banco de Portugal pronuncia-se expressamente sobre esta consequência:
          “{_html(IVA_ZERO_CITACAO)}”.
          <br><br>
          {_frase_pico}Das {len(IVA_ZERO_AFETACAO_ORCAMENTAL)} medidas de 2023 avaliadas, é a que
          dirige menor parcela do custo orçamental ao quintil de menor rendimento. As duas
          dimensões são independentes, pelo que a comparação entre medidas apenas pelo custo
          total não é suficiente.""", alerta=True)
        st.caption(f"**Fonte:** {IVA_ZERO_QUINTIS_FONTE}.")


        # Bloco de fecho, emitido antes do ramo condicional: o quadro das taxas
        # em vigor depende do apuramento por subclasse, mas o detalhe da
        # simulação, mais abaixo, não depende — e sem isto ficava um bloco
        # recolhível órfão, sem cabeçalho, nas sessões sem apuramento.
        bloco("05 · Contexto e limitações")

        if _res_iva:
            # A descrição anterior descrevia o comportamento **anterior a
            # 11.08.2026** e estava escrita no presente: dizia que aplicar uma
            # taxa por grupo “equivale a assumir que toda a despesa do grupo
            # segue a taxa predefinida”. Já não segue, segue a taxa média
            # efetiva, e a equivalência à simulação subclasse a subclasse é
            # exata, não um pressuposto. Contradizia o expander logo abaixo, que
            # a demonstra e a declara travada por teste
            # (assinalado pela utilizadora, 13.08.2026).
            # O título diz para que serve, e não como se obteve: em dois terços
            # do cabaz já não há para onde descer a não ser para zero, e é essa
            # a fronteira do possível que interessa a quem decide. A derivação
            #, taxa média efetiva, Listas do Código do IVA, apuramento por
            # subclasse, mudou-se para o separador Metodologia
            # (decisão da Inês, 13.08.2026).
            # O precedente de 2023 não é ilustração: é a mesma fronteira, já
            # encontrada uma vez por quem teve de decidir (Inês, 13.08.2026).
            secao("Repartição da despesa alimentar pelas taxas legais de IVA",
                  # (o subtítulo continua abaixo)
                  "Que proporção da despesa alimentar segue hoje cada taxa legal. Uma "  # noqa: E501
                  "redução de imposto só produz efeito sobre a parcela onde existe imposto "
                  "a reduzir: a fração já sujeita à taxa reduzida limita o alcance de "
                  "qualquer alteração que não seja a isenção total. Foi essa a delimitação "
                  f"aplicável à medida de 2023, que isentou {IVA_ZERO_N_ALIMENTOS} alimentos, "
                  "“a maioria com taxa anterior de 6%”, constituindo por isso uma isenção "
                  "sobre uma base já sujeita à taxa mínima e não uma redução de taxa.")
            w1, w2, w3, w4 = st.columns(4)
            w1.metric("À taxa reduzida (6%)", f"{percentagem(_res_iva['taxa_6_pct'], sinal=False)}",
                      help="Parcela do cabaz alimentar que está seguramente a 6%.")
            w2.metric("À taxa intermédia (13%)", f"{percentagem(_res_iva['taxa_13_pct'], sinal=False)}",
                      help="Os óleos vegetais que não são azeite (Lista II, 1.5.3).")
            w3.metric("À taxa normal (23%)", f"{percentagem(_res_iva['taxa_23_pct'], sinal=False)}")
            w4.metric("Indeterminado", f"{percentagem(_res_iva['indeterminado_pct'], sinal=False)}",
                      help=("Subclasses que atravessam taxas em proporção não repartível, "
                            "marisco (moluscos a 6%, crustáceos a 23%), o mel dentro dos "
                            "doces, o sal dentro dos condimentos, os leites aromatizados "
                            "dentro das sobremesas lácteas. Cada uma entra com o intervalo "
                            "em que a lei a situa, e nem todas vão de 6% a 23%: os cereais "
                            "de pequeno-almoço estão entre 13% e 23%."))

            # O bloco que aqui estava contava o histórico de edições da própria
            # aplicação, “até 11.08.2026 a simulação fazia X”. Quem usa a
            # ferramenta não precisa de o saber (decisão da Inês, 13.08.2026).
            # Salva-se a única frase que é um facto sobre o **cabaz**, e não
            # sobre a app: que grupos com predefinição de 6% contêm produtos a
            # 23%. Essa desce para a legenda do quadro por grupo, abaixo.
            # As colunas “Predefinida” e “Na predefinida” saíram daqui. A primeira
            # já não é a taxa de partida da simulação (é a efetiva), e a segunda
            # era, linha a linha, a cópia exata da coluna da taxa correspondente à
            # predefinida. Ambas mediam a qualidade de uma aproximação que a
            # aplicação deixou de fazer (decisão da Inês, 13.08.2026). Entra em
            # seu lugar a taxa que a simulação **realmente** aplica.
            _tab_iva = pd.DataFrame([{
                "Grupo": r.classe,
                "Taxa efetiva": _taxas_ef.get(r.codigo),
                "A 6%": r.taxa_6_pct,
                "A 13%": r.taxa_13_pct,
                "A 23%": r.taxa_23_pct,
                "Indeterminado": r.indeterminado_pct,
            } for r in _comp_iva.itertuples()])
            st.dataframe(
                _tab_iva, width="stretch", hide_index=True, row_height=42,
                column_config={
                    "Taxa efetiva": st.column_config.NumberColumn(
                        format="%.1f%%",
                        help=("A taxa única que suporta o mesmo imposto que o conjunto dos "
                              "produtos do grupo. É a taxa de partida da simulação e não "
                              "corresponde a nenhuma taxa legal aplicada.")),
                    **{c: st.column_config.NumberColumn(format="%.1f%%")
                       for c in ("A 6%", "A 13%", "A 23%", "Indeterminado")},
                })
            st.caption(
                "As quatro últimas colunas repartem cada grupo pelas taxas legais e **somam "
                "100%**. A **taxa efetiva** é a média que daí resulta. "
                "**Pastelaria**, **charcutaria** e **hortícolas transformados** são os casos "
                "em que ela mais se afasta da taxa reduzida: são grupos maioritariamente a "
                "6% que contêm produtos à taxa normal."
            )
            with st.expander("Leitura do quadro acima"):
                st.markdown(
                    "Cada linha reparte **um grupo**, não o cabaz: as colunas “A 6%”, "
                    "“A 13%”, “A 23%” e “Indeterminado” somam 100% dentro do grupo. "
                    "A **taxa efetiva** não se lê na tabela como uma das taxas legais, é a "
                    "média que essa repartição implica, e é com ela que a simulação parte. "
                    f"{percentagem(_res_iva['por_predominancia_pct'], sinal=False)} do cabaz foi atribuído por "
                    "**predominância** e não com certeza, ver o detalhe por subclasse na "
                    "Metodologia."
                )
                st.warning(
                    "**Ponderadores do IHPC, que incluem a despesa de não residentes.** É a única "
                    "fonte aberta que desce à subclasse, o IDF fica-se pelo quarto dígito. Serve "
                    "para repartir *dentro* de cada grupo, que é o uso aqui, mas o nível de "
                    "cada parcela herda essa limitação."
                )
            st.download_button(
                "Descarregar composição por taxa (CSV)",
                csv_com_fonte(_comp_iva, "Composição do cabaz alimentar por taxa de IVA", dados,
                              fonte=("Código do IVA, Listas I e II (leitura da UPE); Eurostat, "
                                     "prc_hicp_iw (ponderadores por subclasse)"),
                              conjuntos=[eurostat.HICP_PONDERADORES],
                              extra=[("Ano dos ponderadores", dados.get("ano_pesos_subclasses") or "-"),
                                     ("AVISO", "A parcela indeterminada não é arbitrada")]),
                file_name="composicao_iva_por_taxa.csv", mime="text/csv")


        with st.expander("Ver detalhe da simulação"):
            det = sim[["classe", "valor", "taxa_atual", "taxa_cenario",
                       "base", "mecanico", "efetivo", "margem", "novo_valor"]].copy()
            det.columns = ["Classe", "Valor (€)", "Taxa média efetiva (%)", "Taxa cenário (%)",
                           "Base sem IVA (€)", "Efeito mecânico (€)",
                           "Efeito efetivo (€)", "Margem (€)", "Novo valor (€)"]
            st.dataframe(det.round(2), width="stretch", hide_index=True)
            st.download_button(
                "Descarregar simulação (CSV com fonte)",
                csv_com_fonte(det.round(2), "Simulação de alteração do IVA", dados,
                              # Despesa oficial, mas taxas e repercussão são do
                              # utilizador: o cabeçalho tem de o dizer.
                              fonte=("Eurostat (despesa e preços); parâmetros do utilizador "
                                     "(taxas de IVA e repercussão). NÃO é uma fonte oficial "
                                     "no seu conjunto"),
                              extra=[("Cenário", CENARIOS[cenario][0]),
                                     ("Repercussão assumida", f"{repercussao*100:.0f}%"),
                                     ("Composição do agregado", composicao),
                                     ("Taxa de partida",
                                      "taxa média efetiva apurada por subclasse (COICOP 2018)"
                                      if _tem_apuramento else
                                      "taxa predefinida do grupo; apuramento indisponível"),
                                     ("AVISO", "A taxa do cenário e a repercussão são parâmetros do utilizador, não dados oficiais")]),
                f"despesa_alimentar_simulacao_iva_{date.today()}.csv", "text/csv",
            )

    # ==========================================================================
    # ABA 4, Comparação UE-27
    # ==========================================================================
with aba4:
    with painel("Comparação UE-27"):
        titulo_pagina(
            "Comparação UE-27",
            "Três leituras da posição portuguesa: o nível dos preços, o esforço "
            "das famílias e o ritmo da inflação alimentar.")

        # As opções deixaram de ter emoji, e por isso a vista escolhida deixou de
        # se identificar pelo primeiro carácter do rótulo. Passa a haver chaves
        # estáveis, e o rótulo é só o que se apresenta.
        VISTAS = {
            "precos": "Nível de preços",
            "esforco": "Peso no orçamento das famílias",
            "ritmo": "Ritmo de variação dos preços",
        }
        bloco("01 · A leitura", topo=True)
        vista = st.radio(
            "O que quer ver",
            options=list(VISTAS.keys()), format_func=lambda k: VISTAS[k],
            horizontal=True, label_visibility="collapsed",
        )
        ver_precos = vista == "precos"
        ver_esforco = vista == "esforco"

        st.info(
            "**As três vistas respondem a questões distintas.** O *nível de preços* compara o "
            "nível dos preços entre países. O *peso no orçamento* mede o esforço das famílias, "
            "ou seja, que proporção da sua despesa total é afeta à alimentação. O *ritmo de "
            "variação* compara a inflação. Um país pode registar preços baixos e, ainda assim, "
            "um esforço alimentar elevado, se os rendimentos forem baixos, pelo que as três "
            "leituras devem ser consideradas em conjunto."
        )

        pli = dados.get("pli")

        # ==================== VISTA: NÍVEL DE PREÇOS ====================
        if ver_precos:
            if pli is None or pli.empty:
                st.warning(
                    "O índice de nível de preços não está disponível nesta sessão. "
                    "Consulte o registo de ligações no separador Metodologia. "
                    "Está entretanto disponível a vista “Ritmo de variação dos preços”."
                )
            else:
                # A categoria efetivamente obtida determina o rótulo: a reserva
                # inclui bebidas não alcoólicas e não pode ser apresentada como
                # se fosse só alimentação (auditoria, B3).
                pli_cat_usada = dados.get("pli_cat")
                pli_rotulo = eurostat.PPP_CATEGORIAS_ALIMENTOS.get(
                    pli_cat_usada, "Alimentação")
                pli_e_reserva = pli_cat_usada != eurostat.PPP_CATEGORIA_PREFERIDA

                ano_pli = pli["time"].max()
                pli_ult = pli[pli["time"] == ano_pli].copy()
                pli_ult["pais"] = pli_ult["geo"].map(PAISES)
                pli_ult = pli_ult.dropna(subset=["pais"]).sort_values("valor")

                secao(f"Nível de preços dos alimentos em {ano_pli}",
                      "Índice comparado, com a média da UE-27 fixada em 100. "
                      "Indicador de <strong>nível</strong>, não de conjuntura.",
                      grupo="02 · Nível de preços", topo=True)

                pt_pli = pli_ult.loc[pli_ult["geo"] == "PT", "valor"]
                if not pt_pli.empty:
                    v = float(pt_pli.iloc[0])
                    posicao = "mais caros" if v > 100 else "mais baratos"
                    d1, d2, d3 = st.columns(3)
                    # Uma casa decimal: a grandeza comunicada é a distância à
                    # média europeia, e arredondar 1,4 para 1 perdia quase um
                    # terço dela (auditoria de 11.08.2026, E12).
                    d1.metric(f"Portugal em {ano_pli}", numero(v, 1),
                              help="Índice: média da UE-27 = 100")
                    d2.metric("Face à média da UE-27",
                              f"{numero(abs(v - 100), 1)}% {posicao}")
                    posto = int((pli_ult["geo"] != "EU27_2020").cumsum()[
                        pli_ult["geo"] == "PT"].iloc[0])
                    total = int((pli_ult["geo"] != "EU27_2020").sum())
                    d3.metric("Posição", f"{posto}.º de {total}",
                              help="Do mais barato para o mais caro, entre os países selecionados")

                figp = go.Figure(go.Bar(
                    y=pli_ult["pais"], x=pli_ult["valor"], orientation="h",
                    marker_color=[VERDE if g == "PT" else (AZUL if g == "EU27_2020" else NEUTRO)
                                  for g in pli_ult["geo"]],
                    text=[numero(x, 1) for x in pli_ult["valor"]],
                    textposition="outside",
                    hovertemplate="%{y}: %{x:.0f} (UE-27 = 100)<extra></extra>",
                ))
                figp.add_vline(x=100, line_width=2, line_dash="dash", line_color="#64748b",
                               annotation_text="média UE-27", annotation_position="top")
                figp.update_layout(height=max(380, 38 * len(pli_ult)),
                                   margin=dict(t=44, b=42, l=10, r=72),
                                   xaxis_title=(f"Nível de preços, {pli_rotulo.lower()} "
                                                "(média UE-27 = 100)"),
                                   showlegend=False)
                grafico(figp)
                st.caption(
                    "Barras à direita da linha: alimentos mais caros do que a média europeia. "
                    "À esquerda: mais baratos. Portugal a verde. Fonte: programa de Paridades de "
                    f"Poder de Compra Eurostat-OCDE, categoria {pli_rotulo.lower()}. "
                    "Publicação **anual**, indicador de nível, não de conjuntura."
                )
                if pli_e_reserva:
                    st.warning(
                        f"A categoria de referência (`{eurostat.PPP_CATEGORIA_PREFERIDA}`, "
                        "só alimentação) não respondeu nesta sessão. Estes valores usam a "
                        f"categoria de reserva `{pli_cat_usada}`, que **inclui bebidas não "
                        "alcoólicas**, águas, sumos, cafés e chás. O nível é próximo, mas o "
                        "âmbito não é o mesmo."
                    )

        # ==================== VISTA: ESFORÇO (COEFICIENTE DE ENGEL) ====================
        elif ver_esforco:
            engel = dados.get("engel") or {}
            if not engel:
                st.warning(
                    "**O indicador de esforço não está disponível nesta sessão.**\n\n"
                    "O cálculo precisa de dois valores das Contas Nacionais, a despesa "
                    "alimentar e o consumo total das famílias. O separador **Metodologia**, "
                    "no bloco “Registo das ligações desta sessão”, mostra qual dos dois "
                    "falhou e porquê."
                )
            else:
                # Vinte e cinco linhas de enquadramento antes do primeiro número:
                # quem foi Ernst Engel, a regularidade de 1857, a divergência
                # entre bases e um quadro comparativo. Nada disso é o que o leitor
                # veio ver nesta vista, e a definição do coeficiente é matéria de
                # metodologia (Inês, 13.08.2026). Fica o que é preciso para não ler
                # o gráfico ao contrário, que é rácio de despesa, não de
                # rendimento, e o resto está no separador Metodologia.
                secao("Peso da alimentação no orçamento das famílias",
                      "De cada 100 € que as famílias gastam na totalidade dos bens e "
                      "serviços, incluindo habitação, transportes, saúde e lazer, que "
                      "parcela é afeta à alimentação. É <strong>despesa sobre "
                      "despesa</strong>, e não despesa sobre rendimento.",
                      grupo="02 · Esforço alimentar", topo=True,
                      ajuda=(
                          "**Não confundir com o “esforço alimentar”** do separador Despesa "
                          "e composição. São rácios diferentes:\n\n"
                          "| | Numerador | Denominador |\n"
                          "|---|---|---|\n"
                          "| **Aqui** | O que as famílias gastam em **alimentação** | O que as "
                          "famílias gastam na **totalidade dos bens e serviços** |\n"
                          "| **Esforço alimentar** | O que o agregado gasta em **alimentação** | "
                          "O que o agregado **recebe** |\n\n"
                          "Por isso **este indicador não responde à composição do agregado** "
                          "escolhida em “Despesa e composição”: é um rácio macroeconómico nacional, e "
                          "não existe versão “por agregado” nas Contas Nacionais.\n\n"
                          "Usam-se as **Contas Nacionais**, e só elas, por serem a única base "
                          "construída da mesma maneira em todos os países da UE. O nível é "
                          "discutível; a **comparação entre países** é o que este quadro "
                          "serve. Ver Metodologia."))

                linhas_e = []
                for geo, d in engel.items():
                    if geo not in PAISES:
                        continue
                    linhas_e.append({"geo": geo, "pais": PAISES[geo],
                                     "quota": d["quota"], "ano": d["ano"]})
                df_e = pd.DataFrame(linhas_e).sort_values("quota")

                pt_e = engel.get("PT")
                ue_e = engel.get("EU27_2020")
                if pt_e:
                    e1, e2, e3 = st.columns(3)
                    e1.metric(f"Portugal ({pt_e['ano']}), proporção do consumo",
                              f"{pt_e['quota']:.1f}%".replace(".", ","),
                              help=("De cada 100 € que as famílias portuguesas gastam na "
                                    "totalidade dos bens e serviços, incluindo habitação, "
                                    "transportes, saúde e lazer, esta é a proporção afeta à "
                                    "alimentação. Não envolve salários nem rendimentos."))
                    if ue_e:
                        dif = pt_e["quota"] - ue_e["quota"]
                        e2.metric("Face à média da UE-27", pontos(dif, casas=1))
                    posto = int((df_e["geo"] != "EU27_2020").cumsum()[
                        df_e["geo"] == "PT"].iloc[0])
                    total_p = int((df_e["geo"] != "EU27_2020").sum())
                    e3.metric("Posição", f"{posto}.º de {total_p}",
                              help="Do menor esforço para o maior")

                figE = go.Figure(go.Bar(
                    y=df_e["pais"], x=df_e["quota"], orientation="h",
                    marker_color=[VERDE if g == "PT" else (AZUL if g == "EU27_2020" else NEUTRO)
                                  for g in df_e["geo"]],
                    text=[f"{v:.1f}%".replace(".", ",") for v in df_e["quota"]],
                    textposition="outside",
                    hovertemplate="%{y}: %{x:.1f}% do consumo<extra></extra>"))
                if ue_e:
                    figE.add_vline(x=ue_e["quota"], line_width=2, line_dash="dash",
                                   line_color="#64748b", annotation_text="média UE-27",
                                   annotation_position="top")
                figE.update_layout(height=max(380, 38 * len(df_e)),
                                   margin=dict(t=44, b=42, l=10, r=82),
                                   xaxis_title="Proporção do consumo das famílias afeta à alimentação (%)",
                                   showlegend=False)
                grafico(figE)
                st.caption(
                    "Barras mais longas significam **maior esforço alimentar**: maior parcela do "
                    "orçamento familiar absorvida pela alimentação e menor disponibilidade para "
                    "as restantes despesas. "
                    "Fonte: Eurostat, Contas Nacionais (COICOP 2018), rácio entre a despesa "
                    "alimentar e o consumo total das famílias. Publicação anual. Os conjuntos "
                    "exatos estão no separador Metodologia."
                )

                with st.expander("Descarregar dados do esforço"):
                    tab_e = df_e[["pais", "quota", "ano"]].copy()
                    tab_e.columns = ["País", "Proporção do consumo em alimentação (%)", "Ano"]
                    tab_e["Proporção do consumo em alimentação (%)"] = \
                        tab_e["Proporção do consumo em alimentação (%)"].round(1)
                    st.dataframe(tab_e.sort_values("Proporção do consumo em alimentação (%)",
                                                   ascending=False),
                                 width="stretch", hide_index=True)
                    st.download_button(
                        "CSV com fonte",
                        csv_com_fonte(tab_e, "Coeficiente de Engel, esforço alimentar", dados,
                                      fonte="Eurostat, Contas Nacionais (COICOP 2018)",
                                      conjuntos=[eurostat.CONTAS_NACIONAIS],
                                      extra=[("Indicador", "Despesa alimentar sobre consumo total das famílias"),
                                             ("Conjunto",
                                              f"{eurostat.CONTAS_NACIONAIS}, "
                                              f"CP011 / {eurostat.TOTAL_CONSUMO}")]),
                        f"despesa_alimentar_engel_{date.today()}.csv", "text/csv")

        # ==================== VISTA: INFLAÇÃO ====================
        else:
            cpais, cgrupo = st.columns([3, 2])
            with cpais:
                escolhidos = st.multiselect(
                    "Países", options=list(PAISES.keys()),
                    default=[p for p in PAISES_POR_DEFEITO if p in PAISES],
                    format_func=lambda g: PAISES[g],
                )
            with cgrupo:
                opcoes_grupo = [COICOP_ALIMENTAR] + CODIGOS
                rotulos = {COICOP_ALIMENTAR: "Todos os alimentos"}
                rotulos.update({c["cod"]: c["nome"] for c in CLASSES})
                grupo_sel = st.selectbox(
                    "Grupo de produto", options=opcoes_grupo,
                    format_func=lambda g: rotulos[g],
                    help="Compare a inflação de um tipo de produto específico entre países.",
                )

            bench_todos = dados["bench_todos"]
            bench, _ts = {}, {}
            for _, lb in bench_todos[bench_todos["coicop"] == grupo_sel].iterrows():
                bench.setdefault(lb["geo"], {})[lb["time"]] = lb["valor"]
                _ts[lb["time"]] = 1
            tempos_b = sorted(_ts)

            if grupo_sel != COICOP_ALIMENTAR:
                st.caption(
                    f"A comparar **{rotulos[grupo_sel]}**. Grupos individuais são "
                    "bastante mais voláteis do que o agregado alimentar, a fruta e os legumes, em "
                    "particular, sofrem efeitos sazonais e climáticos fortes."
                )

            if not escolhidos or not tempos_b:
                st.info("Selecione pelo menos um país.")
            else:
                fig = go.Figure()
                paleta = [VERDE, AZUL, DOURADO, VERMELHO, "#7a5ea8", "#c2681a",
                          "#0f8f9c", "#4a7c3f", "#8f4a6b", "#5a6b8f", "#a0568f", "#2980b9"]
                for i, geo in enumerate(escolhidos):
                    if geo not in bench:
                        continue
                    fig.add_trace(go.Scatter(
                        x=[mes_pt(t) for t in tempos_b],
                        y=[bench[geo].get(t) for t in tempos_b],
                        name=PAISES[geo],
                        line=dict(color=paleta[i % len(paleta)],
                                  width=3.2 if geo == "PT" else 1.9,
                                  dash="dot" if geo == "EU27_2020" else "solid"),
                        hovertemplate="%{x}<br>%{y:.1f}%<extra>" + PAISES[geo] + "</extra>",
                    ))
                fig.update_layout(height=470, margin=dict(t=22, b=42, l=10, r=10),
                                  yaxis_title="Variação homóloga (%)",
                                  legend=dict(orientation="h", y=1.1, x=0),
                                  hovermode="x unified")
                fig.update_xaxes(showgrid=False)
                grafico(fig)

                ultimo = tempos_b[-1]
                # Colunas explícitas: sem observações, `pd.DataFrame([])` não
                # tem a coluna `geo` e o `.map` seguinte levantava KeyError,
                # um erro técnico onde devia estar uma explicação
                # (auditoria de 11.08.2026, E13).
                ranking = pd.DataFrame(
                    [{"geo": g, "valor": v[ultimo]}
                     for g, v in bench.items() if v.get(ultimo) is not None],
                    columns=["geo", "valor"])
                ranking["pais"] = ranking["geo"].map(PAISES)
                ranking = ranking.dropna(subset=["pais"])
                ue = ranking.loc[ranking["geo"] == "EU27_2020", "valor"]
                valor_ue = float(ue.iloc[0]) if not ue.empty else None

                # Sem observações no mês comum, a explicação era dada e o
                # cabeçalho “Posição em …” aparecia à mesma, com um gráfico de
                # barras vazio por baixo a desmenti-la
                # (auditoria de 12.08.2026, L22).
                if ranking.empty:
                    st.info(
                        f"Nenhum dos países selecionados tem observação em "
                        f"**{mes_pt(ultimo)}**, o mês mais recente da série. O gráfico "
                        "acima mostra o histórico disponível; a comparação de posições "
                        "precisa de um mês comum."
                    )

            # `or` curto-circuita: sem países ou sem série, `ranking` não existe
            # e não chega a ser avaliado.
            if not (escolhidos and tempos_b) or ranking.empty:
                pass
            else:
                secao(f"Posição em {mes_pt(ultimo)}",
                      "Do mais lento para o mais rápido, com a distância à média "
                      "da UE-27 entre parênteses.",
                      grupo="02 · Posição relativa")
                ordenado = ranking.sort_values("valor", ascending=True)
                cores, etiquetas = [], []
                for geo, valor in zip(ordenado["geo"], ordenado["valor"]):
                    gap = (valor - valor_ue) if valor_ue is not None else None
                    if geo == "PT":
                        cores.append(VERDE)
                    elif geo == "EU27_2020":
                        cores.append(AZUL)
                    elif gap is not None and gap > 0:
                        cores.append("#e08b84")
                    else:
                        cores.append("#8fb3d0")
                    if gap is None or geo == "EU27_2020":
                        etiquetas.append(percentagem(valor, sinal=False))
                    else:
                        # Antes: `.replace(".", ",")` sobre a frase inteira, que
                        # convertia também o “p.p.” em “p,p,” (auditoria, C5).
                        etiquetas.append(f"{percentagem(valor, sinal=False)}  "
                                         f"({pontos(gap, casas=1)})")

                figc = go.Figure(go.Bar(
                    y=ordenado["pais"], x=ordenado["valor"], orientation="h",
                    marker_color=cores, text=etiquetas, textposition="outside",
                    hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
                if valor_ue is not None:
                    figc.add_vline(x=valor_ue, line_width=2, line_dash="dash",
                                   line_color="#64748b",
                                   annotation_text=("média UE-27: "
                                                    + percentagem(valor_ue, sinal=False)),
                                   annotation_position="top")
                figc.update_layout(height=max(390, 38 * len(ordenado)),
                                   margin=dict(t=44, b=42, l=10, r=122),
                                   xaxis_title="Variação homóloga dos preços alimentares (%)",
                                   showlegend=False)
                grafico(figc)
                st.caption(
                    "A linha tracejada é a média da UE-27: à direita, inflação mais rápida do que na "
                    "UE; à esquerda, mais lenta. Entre parênteses, a distância em pontos percentuais."
                )

                if valor_ue is not None:
                    tb = ranking[["pais", "valor"]].copy()
                    tb["Face à UE-27 (p.p.)"] = (tb["valor"] - valor_ue).round(1)
                    tb.columns = ["País", "Variação homóloga (%)", "Face à UE-27 (p.p.)"]
                    tb = tb.sort_values("Variação homóloga (%)", ascending=False)
                    st.download_button(
                        "Descarregar comparação (CSV com fonte)",
                        csv_com_fonte(tb, "Comparação europeia da inflação alimentar", dados,
                                      fonte="Eurostat, IHPC (ECOICOP v2)",
                                      conjuntos=[eurostat.HICP_MENSAL],
                                      extra=[("Mês de referência", ultimo),
                                             ("Grupo", grupo_sel)]),
                        f"despesa_alimentar_ue27_{date.today()}.csv", "text/csv")

    # ==========================================================================
    # ABA 5, Metodologia e fontes
    # ==========================================================================
with aba5:
    with painel("Metodologia e fontes"):
        titulo_pagina(
            "Metodologia e fontes",
            "Documentação completa do método, das fontes e das limitações. A nota "
            "metodológica em anexo à ferramenta desenvolve estes pontos com as "
            "referências legais.")

        # Lugar do índice pesquisável. Fica reservado aqui e é preenchido no fim
        # do separador: o índice constrói-se enquanto os blocos se desenham, e
        # no Streamlit a ordem do ficheiro é a ordem de execução (01.09.2026).
        _slot_indice = st.container()

        # Vinte e sete blocos recolhíveis em fila davam uma página sem relevo:
        # era preciso abrir cada um para saber do que tratava. Ficam todos onde
        # estão, na mesma ordem (há dependências entre eles), mas agrupados em
        # cinco blocos documentais, que é o que permite procurar.
        bloco("01 · Conceitos e definições", topo=True)

        # Abria aberto, e era o único dos 40 expansores da aplicação a fazê-lo.
        # Fechado por decisão da Inês (01.09.2026): a regra do separador é que o
        # leitor abre o que procura, e um bloco aberto à entrada é a parede de
        # texto que essa regra existe para evitar.
        with bloco_metodologia("Delimitação do conceito de cabaz",
                               chaves="DECO cabaz essencial composição fixa seis instrumentos"):
            st.markdown("""
    **Não existe um cabaz alimentar oficial em Portugal.** Existem pelo menos seis instrumentos,
    com naturezas e finalidades diferentes, que o debate público tende a fundir num só. A primeira
    utilidade desta ferramenta é não os confundir.
            """)
            st.markdown("""
    | Instrumento | Entidade | Natureza | O que mede | Limitação crítica |
    |---|---|---|---|---|
    | **Cabaz essencial** (63 produtos) | DECO PROteste | Privado | Preço absoluto em euros de um cabaz de **composição fixa**, recolha semanal nas principais cadeias. Série desde 05.01.2022 | Composição fixa, não acompanha substituição; sem ponderação pelo consumo real; não abrange comércio tradicional; metodologia não plenamente pública |
    | **IPC / IHPC**, classe COICOP 01 | INE / Eurostat | Oficial | **Variação** de preços, ponderada pela estrutura de despesa das famílias. Mensal | É índice, não nível: não responde a “quanto custa alimentar uma família”. Média nacional |
    | **Índice de supermercados online** | DECO PROteste | Privado | Índice **relativo** entre insígnias (base 100 = a mais barata), ~250 produtos, por concelho | Mede *dispersão entre insígnias*, não nível nem evolução. Só canal online. Ponderadores de 2015/2016 |
    | **Observatório de Preços Agroalimentar** | GPP | Oficial | Preços de **39 produtos ao longo da cadeia** (da produção ao consumo) com margens por fileira | Cobertura limitada a 39 produtos e fileiras selecionadas; não mede o custo de um cabaz de consumo |
    | **Cabaz de apoio alimentar** | PO APMC / DGS | Social | Composição definida por **critério nutricional** (Roda dos Alimentos), para distribuição em espécie | Não é instrumento de preços. É a única definição pública de cabaz com critério nutricional |
    | **Cabaz “IVA zero”** (2023–24) | Governo / AT / ASAE | Administrativo | Lista taxativa de 46 tipologias com isenção temporária de IVA | Vigência encerrada. Critério nutricional/social, não estatístico. Ver o separador do simulador de IVA |
            """)

            st.markdown("**Onde se situa esta ferramenta**")
            st.markdown("""
    Esta aplicação **não é um sétimo cabaz**, não recolhe preços nem define uma lista de produtos.
    É um **instrumento de repartição e enquadramento**: parte de uma âncora oficial de despesa
    (IDF ou Contas Nacionais), reparte-a pelas nove classes COICOP e aplica a cada uma a variação
    oficial do índice. Responde a “quanto pesa a alimentação no orçamento de quem, e quanto disso é
    aumento de preço”, não a “quanto custa este cabaz hoje”.

    Daí decorre o que **não** pode fazer: não dá o preço de nenhum produto, não compara insígnias,
    e não substitui a recolha da DECO como sinalizador semanal de preços no retalho.
            """)

            st.warning("""
    **Ponto central para leitura pública.** O indicador com maior difusão pública, habitualmente
    referido como o preço do cabaz e o seu valor máximo, é o da DECO PROteste. É um indicador
    legítimo e útil enquanto sinalizador de tendência de preços no retalho alimentar, mas **não é
    um indicador de custo de vida nem de acessibilidade alimentar**. A subida do preço de um cabaz
    não implica que as famílias estejam a gastar mais em alimentação: podem estar a substituir
    produtos, a mudar de insígnia ou a reduzir quantidades. Essa substituição constitui, ela
    própria, uma perda de bem-estar, e é precisamente o que um cabaz de composição fixa não capta.
            """)

        with bloco_metodologia("O IHPC e a sua distinção face ao IPC",
                               chaves="IPC harmonizado residentes território nacional"):
            st.markdown("""
    O **IHPC, Índice Harmonizado de Preços no Consumidor** é o índice de inflação construído
    segundo metodologia comum a todos os Estados-Membros, precisamente para que os valores sejam
    comparáveis entre países. Base legal: **Regulamento (UE) 2016/792**, desenvolvido pelo
    Regulamento de Execução (UE) 2020/1148. Em inglês designa-se HICP.

    Portugal produz **dois** índices, ambos calculados pelo INE a partir da mesma recolha de
    preços, mas com âmbitos distintos:
            """)
            st.dataframe(pd.DataFrame([
                {"Índice": "IPC, Índice de Preços no Consumidor",
                 "Para que serve": "Índice nacional: atualizações contratuais, indexação, leitura interna da inflação",
                 "Âmbito": "Consumo das famílias residentes; inclui rendas imputadas"},
                {"Índice": "IHPC, Índice Harmonizado",
                 "Para que serve": "Comparação entre Estados-Membros e política monetária do BCE",
                 "Âmbito": "Consumo monetário no território (inclui não residentes); exclui rendas imputadas"},
            ]), width="stretch", hide_index=True)
            st.markdown(
                "As diferenças de âmbito produzem valores próximos mas não idênticos. "
                "**Esta ferramenta usa o IHPC** por ser a única base que permite comparar Portugal "
                "com os restantes Estados-Membros com garantia de que se mede a mesma coisa."
            )

        with bloco_metodologia("Como se calcula o IHPC",
                               chaves="ponderadores agregação elementar"):
            st.markdown("""
    O IHPC é um **índice de Laspeyres encadeado anualmente**. O cálculo tem dois níveis.

    **Nível elementar**, sem ponderadores, combinam-se os relativos de preço, em regra por
    média geométrica (fórmula de Jevons):
    """)
            st.latex(r"I = \prod_i \left( \frac{p_{i,t}}{p_{i,0}} \right)^{1/n}")
            st.markdown("""
    **Acima do nível elementar**, agregação ponderada, com encadeamento em dezembro do ano
    anterior:
    """)
            st.latex(r"I(m,y) = I(\text{Dez},y-1) \times \sum_i w_i^{\,y} \cdot \frac{I_i(m,y)}{I_i(\text{Dez},y-1)}")
            st.markdown("""
    Os ponderadores seguem uma regra precisa, fixada no Regulamento de Execução (UE) 2020/1148:

    1. Partem das **Contas Nacionais do ano y−2**, o último com dados de qualidade completa.
    2. São **revistos para representar o ano y−1**, com toda a informação disponível.
    3. São **atualizados a preços de dezembro de y−1**, para coincidir com o encadeamento.

    Daqui decorre a propriedade essencial: **os ponderadores são revistos todos os anos**. É isso
    que permite ao IHPC acompanhar alterações no padrão de consumo, quando as famílias trocam
    novilho por frango, o ponderador da carne reflete-o no ano seguinte. Um cabaz de composição
    fixa não o faz, e acumula por isso o chamado *viés de substituição*.

    A variação homóloga obtém-se diretamente do índice:
    """)
            st.latex(r"\pi(m) = \left[ \frac{I(m,y)}{I(m,y-1)} - 1 \right] \times 100")

        with bloco_metodologia("O que são as Contas Nacionais e o que medem",
                               chaves="turistas não residentes território autoconsumo exaustividade QERU"):
            st.markdown("""
    As **Contas Nacionais** são o sistema de contabilidade macroeconómica do país. São elaboradas
    pelo INE segundo o **Sistema Europeu de Contas (SEC 2010)**, norma comum a todos os
    Estados-Membros fixada pelo Regulamento (UE) n.º 549/2013 e alterada pelo Regulamento (UE)
    2023/734, e é delas que sai o PIB.

    A despesa de consumo final das famílias é uma das componentes do PIB na ótica da despesa. O
    Regulamento (UE) 2023/734 substituiu nas contas nacionais as referências à COICOP 1999 pela
    **COICOP 2018**, com aplicação a partir de 1 de setembro de 2024, e é da rubrica **01.1,
    produtos alimentares**, que esta ferramenta parte.

    ##### Como se apura o valor

    O apuramento faz-se no **Quadro de Equilíbrio de Recursos e Utilizações (QERU)**, que nas
    contas portuguesas tem cerca de 430 produtos. Para cada produto confronta-se o que foi
    produzido e importado com o que foi consumido pelas empresas, investido, exportado ou
    acrescentado a existências. O consumo final das famílias é uma das colunas desse equilíbrio, e
    o seu valor fica determinado quando o quadro fecha.

    As fontes que alimentam o quadro são o inquérito às despesas das famílias, o volume de
    negócios do comércio a retalho, a informação empresarial simplificada, a e-fatura e a
    informação do IVA, o comércio internacional, a Balança de Pagamentos e as estatísticas do
    turismo.

    **O inquérito às despesas das famílias é o ponto de partida, mas não a palavra final.** O INE
    declara, na metainformação deste conjunto, que a comparação dos resultados do inquérito com o
    IVA, com o volume de negócios do retalho e com informação setorial levou à conclusão de que os
    valores do inquérito estavam subavaliados. O valor final do consumo das famílias é por isso o
    que resulta do equilíbrio entre a oferta e as utilizações de cada produto, não o que o
    inquérito mediu. É esta a razão de fundo pela qual as duas bases desta ferramenta divergem.

    A repartição por COICOP é feita no fim: obtém-se do QERU depois de concluído o equilíbrio,
    aplicando ponderadores calculados para cada par COICOP/produto.

    Daqui decorrem três propriedades que importam à leitura:

    1. **É um total nacional, não uma média observada.** A despesa por agregado obtém-se por
       divisão, não por medição.
    2. **Procura ser exaustivo.** Inclui ajustamentos que nenhum inquérito capta, como gorjetas,
       pagamentos em espécie e atividade não declarada.
    3. **É lento.** O conjunto é transmitido nove meses após o fim do ano de referência e os
       agregados europeus são atualizados em novembro de cada ano. A aplicação atualiza o valor ao
       mês corrente pelo índice de preços.

    ##### O que está incluído

    | Está incluído | Não está incluído |
    |---|---|
    | Alimentos comprados em supermercado, mercearia, mercado, talho, peixaria e padaria | Refeições em restaurantes, cafés, cantinas e comida entregue ao domicílio (divisão 11) |
    | Alimentos pré-preparados comprados no retalho | Bebidas não alcoólicas: águas, sumos, café e chá (grupo 01.2) |
    | Compras feitas em Portugal por quem não reside no país | Bebidas alcoólicas e tabaco (divisão 02) |
    | Bens produzidos para consumo próprio, sobretudo agrícolas | Serviços que as famílias produzem para si, como preparar refeições |

    ##### O que está no valor e não responde à pergunta desta ferramenta

    A ferramenta mede quanto gasta uma família portuguesa em alimentação. As Contas Nacionais
    medem quanto se consumiu em alimentos no território. A diferença entre as duas grandezas tem
    componentes identificáveis, e todas deslocam o valor no mesmo sentido:

    | Componente | Porque não responde à pergunta da ferramenta |
    |---|---|
    | Autoconsumo de bens, sobretudo agrícolas | É consumo, não é despesa. Quem come os legumes da própria horta não gasta nesses legumes |
    | Compras de não residentes em território português | Não são famílias portuguesas. Nos alimentos o efeito é pequeno, com limite superior de 12,3% |
    | Ajustamentos de exaustividade | Captam atividade não declarada, o que é correto para o PIB e alheio à pergunta “quanto gasta este agregado” |
    | População institucional | O total do setor das famílias não coincide com o universo dos agregados domésticos privados pelo qual se divide |

    Nenhuma destas componentes está quantificada ao nível da alimentação, e somadas não explicam um
    fator de 2,3. Servem para saber **em que sentido** o valor macroeconómico se afasta da pergunta,
    não para o corrigir.

    ##### Em que conceito está

    O conjunto está no **conceito interno**, e não é dedução: a metainformação de referência do
    Eurostat declara-o. Mede a despesa realizada no território económico português, seja quem for
    que a realize, e a despesa dos não residentes entra por ajustamento explícito, a partir da
    rubrica “viagens e turismo” da Balança de Pagamentos e do inquérito ao turismo internacional. Em
    contrapartida, exclui as compras de residentes portugueses no estrangeiro.

    Os dados portugueses confirmam-no por duas vias independentes.

    **Identidade contabilística.** O total da desagregação por COICOP excede sistematicamente o
    `P31_S14` do `nama_10_gdp`, que é o consumo das famílias no conceito nacional:

    | Ano | COICOP (`nama_10_cp18`) | Nacional (`P31_S14`) | Diferença |
    |---|---|---|---|
    | 2019 | 146 691 M€ | 133 188 M€ | +13 503 M€ (10,1%) |
    | **2020** | **129 986 M€** | **124 709 M€** | **+5 277 M€ (4,2%)** |
    | 2024 | 192 796 M€ | 171 641 M€ | +21 155 M€ (12,3%) |

    A diferença desceu 61% no ano em que o turismo parou e recuperou depois. O padrão é consistente
    com o efeito do turismo e não foram identificadas outras explicações compatíveis com esta
    evolução.

    **O peso dos não residentes na alimentação é pequeno.** Em 2020:

    | | Variação 2020/2019 |
    |---|---|
    | Restauração (divisão 11) | **−36,6%** |
    | Alimentação em casa (grupo 01.1) | **+3,1%** |

    Se a despesa alimentar em casa fosse materialmente atribuível a não residentes, teria
    **descido** em 2020. Subiu. A despesa dos não residentes concentra-se na restauração e não
    na alimentação adquirida para consumo doméstico.

    **Ressalva.** 2020 teve dois efeitos opostos sobre a alimentação em casa: os residentes
    substituíram restaurante por casa (a subir) e os visitantes desapareceram (a descer). O saldo
    foi +3,1%, o que **não prova que o efeito seja nulo**, só que é menor do que a substituição. O
    limite superior, se os não residentes consumissem alimentos em casa na proporção do seu peso no
    consumo total, seria 12,3%; a evidência de 2020 indica que o valor real fica bem abaixo disso.

    ##### Porque é que a aplicação apresenta duas bases

    As duas bases não são duas medições independentes: o inquérito é o ponto de partida da
    estimativa macroeconómica, que depois o corrige em alta por o considerar subavaliado. O que as
    separa é a dimensão dessa correção, e essa não é conhecida ao nível da alimentação, porque o
    INE não publica a taxa de cobertura por rubrica COICOP. A aplicação apresenta por isso ambas as
    bases como um **intervalo**, e declara que o ponto central não é determinável.
            """)
            st.caption(
                "Fontes: Eurostat, metainformação ESMS do conjunto `nama_10_cp18`, europeia e "
                "nacional de Portugal (§18.1, fontes de base e método de compilação); INE, "
                "“Como se calcula o PIB”, Departamento de Contas Nacionais, novembro de 2025, "
                "secção 3.A; Regulamento (UE) n.º 549/2013 e Regulamento (UE) 2023/734."
            )

        bloco("02 · Método de cálculo e apuramento do IVA")

        with bloco_metodologia("Os quatro passos desta ferramenta",
                               chaves="âncora decomposição contributo passos"):
            st.markdown("**1 · Âncora: quanto gasta o agregado médio em alimentação**")
            st.latex(r"\text{Contas Nacionais:}\quad \frac{D(y)}{H \times 12}"
                     r"\qquad\qquad \text{IDF:}\quad \frac{A(y)}{12}")
            st.caption(
                "D(y) = despesa alimentar nacional anual (Contas Nacionais) · H = número de "
                "agregados · A(y) = despesa alimentar anual por agregado, medida diretamente "
                "pelo IDF. As duas bases divergem por um fator próximo de 2, a aplicação "
                "apresenta o intervalo e deixa a base à escolha."
            )

            st.markdown("**2 · Atualização ao mês corrente**")
            st.latex(r"\text{valor atual} = \text{valor da base} \times "
                     r"\frac{I(m)}{\bar{I}(R)}")
            # O efeito de indexar pela janela em vez do ano civil de 2023 estava
            # inscrito à mão como “21,05 €/mês, 8,3%”. É um valor que se move
            # a cada mês novo do índice, e estava escrito no presente
            # (auditoria de 12.08.2026, L16). Passa a ser calculado aqui.
            _idf_2023, _, _ = _atualizar_por_indice(
                IDF_ALIMENTAR_ANUAL / 12, int(IDF_JANELA_RECOLHA[1][:4]), dados["indice_pt"])
            _idf_janela = float(ancora["bases"]["idf"]["valor"])
            _ganho_janela = _idf_janela - _idf_2023
            _frase_janela = ""
            if abs(_ganho_janela) > 0.005 and _idf_2023:
                _frase_janela = (
                    f" Indexar a partir do ano civil de {IDF_JANELA_RECOLHA[1][:4]} "
                    f"subestimaria hoje o valor atual em "
                    f"**{euro(_ganho_janela)}/mês**, "
                    f"{percentagem(_ganho_janela / _idf_2023 * 100, sinal=False)}.")
            st.caption(
                "I(m) = índice do mês · Ī(R) = média do índice no **período de referência** da "
                "base. Nas Contas Nacionais esse período é o ano civil da despesa. No IDF **não "
                "é um ano civil**: a recolha decorreu em 26 quinzenas seguidas, de fevereiro de "
                "2022 a fevereiro de 2023, e o INE não corrige os valores para uma data comum "
                f"({IDF_JANELA_FONTE}). A média é por isso calculada sobre a janela "
                f"**{mes_pt(IDF_JANELA_RECOLHA[0])} a {mes_pt(IDF_JANELA_RECOLHA[1])}**."
                + _frase_janela
            )

            st.markdown("**3 · Ajustamento à composição do agregado**")
            st.latex(r"\text{despesa do agregado} = \text{valor atual} \times \frac{eq(A,C)}{eq(\bar{s})}")
            st.caption("A = adultos · C = crianças · s̄ = dimensão média nacional do agregado")

            st.markdown("**4 · Repartição por grupo de produto**")
            st.latex(r"V_i = \text{despesa total} \times \frac{w_i}{\sum_j w_j}")
            st.caption("wᵢ = ponderador oficial da classe i")

            st.markdown("**Contributo de cada grupo para o agravamento homólogo**")
            st.latex(r"\text{contributo}_i = V_i \cdot \frac{g_i}{1 + g_i}")
            st.markdown(
                "A soma dos contributos iguala exatamente a variação do total, a decomposição é "
                "**aditiva**, propriedade verificada por teste automático."
            )

            st.markdown("---")
            st.markdown("**5 · Taxa de IVA de partida, no simulador**")
            st.markdown("""
    O simulador precisa de saber que taxa cada grupo suporta **hoje**, antes de aplicar o cenário.
    Essa taxa não é escolhida: é apurada. Cada grupo COICOP contém produtos em taxas legais
    diferentes (pão a 6% e pastelaria a 23%, azeite a 6% e óleos vegetais a 13%), e os
    ponderadores por subclasse da COICOP 2018 permitem medir a proporção de cada um.
                """)
            st.latex(r"c_i = \frac{\sum_b w_b \cdot \dfrac{t_b}{1+t_b}}{\sum_b w_b}"
                     r"\qquad\qquad t_i^{ef} = \frac{c_i}{1-c_i}")
            st.caption(
                "b percorre as subclasses do grupo i · w = ponderador da subclasse · "
                "t = taxa legal da subclasse · c = fração do preço que é imposto · "
                "t_ef = taxa única equivalente. **Não é uma taxa legal**: é a carga fiscal média "
                "do grupo tal como ele é hoje consumido."
            )
            st.markdown(
                "Usar esta taxa é **matematicamente idêntico** a simular escalão a escalão e não "
                "constitui uma aproximação. A demonstração e a verificação numérica constam de "
                "“Cálculo da taxa média efetiva e sua suficiência”, nesta página."
            )

        # Derivação da taxa de partida do simulador. Vive aqui, e não no
        # separador do IVA, porque é **como se chega ao número** e não o que
        # o número diz, a distinção que separa este separador dos outros
        # (decisão da Inês, 13.08.2026). Os nomes vêm do separador do IVA,
        # que corre antes deste; se lá tiver falhado, este bloco não entra.
        if _tem_apuramento and not _comp_iva.empty:
            with bloco_metodologia("Cálculo da taxa média efetiva e sua suficiência",
                                   chaves="taxa efetiva subclasse ponderador carga fiscal"):
                st.markdown("""
    **O que é.** A taxa média efetiva de um grupo é **a taxa única que suporta o mesmo imposto que
    o conjunto dos produtos desse grupo**. Não corresponde a nenhuma taxa legal aplicada: é uma
    medida da carga fiscal média do grupo, tal como ele é hoje consumido.

    **Como se obtém.** Primeiro apura-se a fração do preço que é imposto, ponderando as subclasses:
                """)
                st.latex(r"c = \frac{\sum_b w_b \cdot \dfrac{t_b}{1+t_b}}{\sum_b w_b}")
                st.markdown(
                    "onde *b* percorre as subclasses do grupo, *w* é o ponderador de cada uma e "
                    "*t* a sua taxa legal. Depois inverte-se para obter a taxa equivalente:")
                st.latex(r"t_{ef} = \frac{c}{1-c}")
                st.markdown(f"""
    **Exemplo com números, Cereais e derivados.** O grupo pesa
    {numero(float(_comp_iva.set_index('codigo').loc['CP0111', 'peso']), 2)} ‰, dos quais
    {numero(float(_comp_iva.set_index('codigo').loc['CP0111', 'taxa_6']), 2)} ‰ a 6% (cereais,
    farinhas e **pão**) e
    {numero(float(_comp_iva.set_index('codigo').loc['CP0111', 'taxa_23']), 2)} ‰ a 23%
    (**outros produtos de padaria**, bolos, bolachas, pastelaria). A carga média resultante é de
    **{numero(float(_taxas_ef['CP0111']), 1)}%**, e não os 6% que a predefinição indicava.

    **E porque é que uma taxa média basta.** Podia parecer que era preciso simular escalão a
    escalão. Não é, e não por aproximação, mas por **identidade algébrica**. A base sem imposto de
    um grupo é a soma das bases dos seus escalões; se a taxa efetiva for definida como acima, a
    base que ela produz é exatamente essa soma. E como a taxa do cenário é uniforme dentro do
    grupo, tudo o que se calcula a seguir, efeito mecânico, repercussão, imposto contido no preço
    novo, depende apenas da base e da taxa do cenário.

    Os dois caminhos foram confrontados numericamente em quatro cenários, incluindo a isenção
    total e um cenário misto: **coincidem até à décima quarta casa decimal**, que é o limite da
    aritmética de vírgula flutuante. Está travado por teste automático.
                """)
                st.warning("""
    **O que continua a ser aproximação.** A taxa efetiva é exata *dado* o apuramento das
    subclasses, mas o apuramento tem uma parcela indeterminada, e uma parte foi atribuída por
    predominância. E os ponderadores são do IHPC, que inclui não residentes. A sensibilidade a
    isso está declarada por baixo dos indicadores, como intervalo.

    Continua também a valer, sem alteração, a advertência de que **isto não é uma estimativa de
    custo orçamental**: a despesa de referência não é a despesa alimentar total das famílias, e
    uma estimativa de receita cessante exige a base tributável real.
                """)

            with bloco_metodologia("O que o Código do IVA diz sobre cada grupo e o que fica de fora",
                                   chaves="Lista I Lista II taxa reduzida intermédia normal"):
                st.markdown(
                    "O Código do IVA classifica **por produto**, nas Listas I (6%) e II (13%); a "
                    "aplicação classifica **por grupo COICOP**, porque não existe despesa aberta ao "
                    "nível do produto. Nenhum dos nove grupos é homogéneo: a taxa predefinida é a "
                    "**predominante**, nunca a única. O quadro seguinte diz, para cada grupo, o que "
                    "está na taxa reduzida e o que segue taxa diferente da predefinida."
                )
                for _cl in CLASSES:
                    _mapa = IVA_MAPA.get(_cl["cod"])
                    if not _mapa:
                        continue
                    st.markdown(
                        f"**{_cl['nome']}**, predefinida a "
                        f"**{_cl['iva']}%**  \n"
                        f"<span class='sg-cartao__cod'>COICOP 2018 "
                        f"01.1.{_cl['cod'][5]} · {_cl['oficial']}</span>",
                        unsafe_allow_html=True,
                    )
                    _linhas = []
                    for _t, _txt in _mapa["taxas"]:
                        _marca = ", predefinida" if _t == _cl["iva"] else ""
                        _linhas.append(f"- **{_t}%**{_marca} · {_txt}")
                    if _mapa.get("nota"):
                        _linhas.append(f"- *{_mapa['nota']}*")
                    st.markdown("\n".join(_linhas))
                st.caption(f"Fonte: {IVA_MAPA_FONTE}. Levantamento da UPE sobre as "
                           "classes da COICOP 2018.")

            if not _comp_iva.empty:
                with bloco_metodologia("O apuramento, subclasse a subclasse",
                                       chaves="inequívoca predominante indeterminada COICOP verba"):
                    st.markdown(
                        "Cada linha é uma subclasse da COICOP 2018, com o ponderador que o Eurostat "
                        "lhe atribui e a verba do Código do IVA que a sustenta. **É aqui que se vê "
                        "de onde vêm os números do quadro acima**, e onde se vê o que não foi "
                        "possível determinar."
                    )
                    _pesos_sub = dados.get("pesos_subclasses") or {}

                    def _peso_comp(spec):
                        if isinstance(spec, str):
                            return float(_pesos_sub.get(spec) or 0.0), spec
                        pai, filhos = spec
                        resto = float(_pesos_sub.get(pai) or 0.0) - sum(
                            float(_pesos_sub.get(f) or 0.0) for f in filhos)
                        return max(resto, 0.0), f"{pai} menos {', '.join(filhos)}"

                    # Grau de certeza em texto, e não em símbolos: é uma coluna de
                    # leitura, e a distinção entre os três casos não deve depender
                    # de reconhecer um ícone.
                    _marca = {"certa": "Inequívoca", "predominante": "Predominante",
                              "mista": "Indeterminada"}
                    _linhas_sub = []
                    for _cl in CLASSES:
                        for _c in IVA_COMPONENTES.get(_cl["cod"], []):
                            _p, _cod = _peso_comp(_c["peso"])
                            _linhas_sub.append({
                                "Grupo": _cl["nome"],
                                "Subclasse": _cod,
                                "Ponderador (‰)": _p,
                                # Uma parcela indeterminada não fica sem taxa: fica
                                # com o **intervalo** em que a lei a situa. Há uma,
                                # os cereais de pequeno-almoço, cujo intervalo não
                                # inclui a taxa reduzida.
                                "Taxa": (f"{_c['taxa']}%" if _c["taxa"] is not None
                                         else "{} a {}%".format(*_c.get("entre", (6, 23)))),
                                "Atribuição": _marca.get(_c["certeza"], ""),
                                "O que sustenta a atribuição": _c["desc"].replace("**", ""),
                            })
                    st.dataframe(
                        pd.DataFrame(_linhas_sub), width="stretch", hide_index=True,
                        column_config={"Ponderador (‰)": st.column_config.NumberColumn(format="%.2f")})
                    st.caption(
                        "**Inequívoca**, a subclasse cai inteira numa verba. "
                        "**Predominante**, é maioritariamente de uma taxa, mas não só. "
                        "**Indeterminada**, atravessa taxas em proporção **não determinável**: "
                        "a coluna “Taxa” mostra o **intervalo em que a lei a situa**, e o peso vai "
                        "para a parcela indeterminada, não é arbitrado.  \n"
                        f"Fonte: {IVA_COMPONENTES_FONTE}."
                    )
                    st.success(
                        "**Cada atribuição foi verificada verba a verba contra o texto legal "
                        "consolidado.** O caso mais consequente é o dos **cereais de "
                        "pequeno-almoço**, que a lei situa entre **13% e 23%**: a Lista I não "
                        "tem verba alguma para eles e a Lista II (1.12) cobre apenas os “flocos "
                        "prensados simples de cereais e leguminosas sem adições de açúcar”."
                    )
                    with bloco_metodologia(
                            "O que a Autoridade Tributária já decidiu "
                            "(informações vinculativas)",
                            chaves="AT fichas vinculativas pão preparados despacho"):
                        st.markdown(
                            "As informações vinculativas da AT (artigo 68.º do Código de "
                            "Procedimento e de Processo Tributário, CPPT) são a via para "
                            "fechar as atribuições que aqui aparecem como **predominantes**: são "
                            "questões de leitura das Listas, não de estatística. Cada ficha decide "
                            "sobre produtos concretos, e o que decide vincula a Administração.\n"
                        )
                        for _f in AT_FICHAS:
                            st.markdown(
                                f"**Processo {_f['processo']}**, despacho de {_f['despacho']}, "
                                f"{_f['orgao']}. *{_f['assunto']}.*"
                            )
                            # Em lista e não em quadro. Eram duas colunas, um
                            # código e um parágrafo, o que já é uma lista de
                            # definições e não dados tabulares. E os textos
                            # marcam a **cláusula decisiva** de cada ficha, que
                            # é o que interessa reter: num quadro esse negrito
                            # saía com os asteriscos à vista, porque uma célula
                            # não interpreta markdown (relatado pela Inês,
                            # 01.09.2026). Apagar as marcas resolvia o defeito
                            # e perdia a informação; deixá-las num contentor que
                            # as entende resolve os dois.
                            st.markdown("\n".join(
                                f"- `{_c}` · {_t}" for _c, _t in _f["decide"]))
                        st.success(
                            "**O princípio que sustenta este quadro**, na formulação da ficha "
                            f"24929: “{PRINCIPIO_LISTA_TAXATIVA}”\n\n"
                            "É a justificação do método usado aqui, percorrer as Listas e atribuir "
                            "a taxa normal a tudo o que não esteja lá de forma inequívoca. E "
                            "explica por que os **preparados** caem quase sempre fora: “as "
                            "categorias 1.3 e 1.6 não incluem qualquer tipo de preparados; quando "
                            "assim é, por exemplo a verba 1.1 da Lista I, estes são especificamente "
                            "referidos”."
                        )
                        st.caption(
                            "**Uma tensão que se regista e não se resolve.** A ficha 28176 "
                            "caracteriza a verba 1.1.1 como abrangendo os cereais “em grão, ou em "
                            "flocos”, o que sugeriria 6% para os flocos simples. Mas a verba 1.12 "
                            "da Lista II é texto legal específico para “flocos prensados simples "
                            "de cereais e leguminosas sem adições de açúcar”, a 13%. Entende-se "
                            "que o texto específico prevalece, e que a caracterização da ficha é "
                            "contextual, a decisão que ela toma é sobre *preparados*, não sobre "
                            "flocos simples. É o único ponto do quadro onde outra leitura é "
                            "defensável, e por isso está escrito."
                        )
                        st.info(
                            "**Regra geral que explica muitas atribuições à taxa normal.** O artigo "
                            "18.º, n.º 4 do Código do IVA determina que, num produto composto, se as "
                            "mercadorias mantêm a sua individualidade se aplica **a taxa mais "
                            "elevada** de entre as que lhes caberiam; se a perdem, a que "
                            "corresponder ao produto resultante. É por isso que tantos “preparados” "
                            "acabam a 23% mesmo contendo ingredientes que, isolados, estariam a 6%."
                        )
                    st.info("""
        **O que a COICOP 2018 permitiu e a anterior não permitia.** Três cortes novos resolvem as
        maiores ambiguidades: **Pão** (`CP011131`) separado de **Outros produtos de padaria**
        (`CP011139`), o que reparte a maior classe do cabaz; **Azeite** (`CP011513`) separado dos
        restantes óleos vegetais, o que isola exatamente a verba da Lista II; e **carne seca ou
        fumada** separada da carne fresca. Na nomenclatura anterior estes produtos partilhavam
        subclasse, e a repartição era simplesmente impossível.
                    """)


        # A tabela integral da inflação por quintil vivia no simulador, ao lado do
        # gráfico da afetação orçamental, e era o elemento mais denso da secção:
        # das três colunas, só a primeira sustenta o argumento; as outras duas são
        # contexto do IPC, que é matéria de metodologia (decisão da Inês,
        # 13.08.2026). O simulador ficou com as barras da coluna que usa.
        with bloco_metodologia("Inflação por quintil no “IVA zero” de 2023 (a tabela completa)",
                               chaves="quintis repercussão Banco de Portugal"):
            st.markdown(
                "Taxa de variação **em cadeia** em maio de 2023, em pontos percentuais. A "
                "primeira coluna são as rubricas alimentares abrangidas pela isenção, é a "
                "que o simulador representa em barras. As outras duas situam-na: o conjunto "
                "dos bens alimentares, e o índice de preços no consumidor total."
            )
            st.dataframe(
                pd.DataFrame(
                    IVA_ZERO_INFLACAO_QUINTIL,
                    columns=["Quintil", "Bens alimentares afetados",
                             "Bens alimentares", "IPC total"]),
                width="stretch", hide_index=True,
                column_config={
                    c: st.column_config.NumberColumn(format="%+.1f p.p.")
                    for c in ("Bens alimentares afetados", "Bens alimentares", "IPC total")
                })
            # O quintil de maior alívio sai da série, não está escrito à mão: é o
            # mesmo cuidado da nota no simulador.
            _qm = [r for r in IVA_ZERO_INFLACAO_QUINTIL if r[0] != "Total de famílias"]
            _pico_m = min(_qm, key=lambda r: r[1]) if _qm else None
            _aviso_m = ""
            if _pico_m is not None and _qm and _pico_m[0] != _qm[0][0]:
                _aviso_m = (
                    f"O alívio não é monótono ao longo da distribuição: o maior valor absoluto "
                    f"está no **{_pico_m[0]}**, não no primeiro quintil. O que a série sustenta "
                    f"é o contraste entre os extremos, não um gradiente.  \n")
            st.caption(f"{_aviso_m}**Fonte:** {IVA_ZERO_QUINTIS_FONTE}.")

        bloco("03 · Bases, ponderação e escalas de equivalência")

        # Estava no separador UE-27, antes do primeiro número da vista do esforço.
        # É a definição de um indicador e a explicação de uma divergência entre
        # bases: matéria de metodologia (decisão da Inês, 13.08.2026).
        with bloco_metodologia("O coeficiente de Engel e os seus dois valores",
                               chaves="Engel orçamento despesa total"):
            _eng_m = intervalo_engel((dados.get("engel") or {}).get("PT"))
            st.markdown(f"""
    É a **fração do consumo total das famílias que vai para alimentação**. Chama-se assim por
    **Ernst Engel**, o estatístico que em 1857 formulou a regularidade que ainda hoje se verifica:
    *quanto menor o rendimento, maior a proporção do orçamento afeta à alimentação*.

    É um dos indicadores mais antigos e mais robustos de bem-estar económico, e comparável entre
    países sem conversão cambial, por ser um rácio.

    **Porque é que o separador UE-27 mostra um valor e o separador “Despesa e composição” mostra
    um intervalo.** O coeficiente pode medir-se em duas bases, e elas não coincidem:
    **{percentagem(_eng_m['idf'], sinal=False)}** no IDF 2022/2023 do INE,
    **{percentagem(_eng_m['contas'], sinal=False) if _eng_m['contas'] is not None else '—'}** nas
    Contas Nacionais de {_eng_m['ano_contas'] or '—'}. As Contas Nacionais registam, por agregado,
    mais despesa alimentar do que o inquérito, e o coeficiente diverge porque **o numerador
    diverge mais do que o denominador**. É a mesma divergência entre bases que leva a aplicação a
    apresentar a despesa mensal como intervalo, e não como ponto.

    Na comparação europeia usam-se **as Contas Nacionais**, e só elas, porque são a única base
    construída da mesma maneira em todos os países da UE, o IDF não tem equivalente europeu com
    esta desagregação. O nível é discutível; a **comparação entre países** é o que aquele quadro
    serve, e essa é válida porque todos os países entram pela mesma via.
            """)

        with bloco_metodologia("Duas bases de ponderação e respetiva aplicação",
                               chaves="IHPC IDF turistas quotas desvio estrutura"):
            st.markdown("""
    A aplicação usa **duas** estruturas de ponderação, e não é indiferente qual se aplica a quê.
    A regra é simples:

    | | Ponderador | Responde a |
    |---|---|---|
    | **Estrutura e distribuição** | IDF 2022/2023, por quintil | Quem gasta o quê, e que parte do orçamento leva |
    | **Movimento dos preços** | IHPC, revisto anualmente | Quanto subiu cada grupo, e quanto contribuiu |

    A razão é conceptual, não de conveniência. O Documento Metodológico do IPC afirma que **o IHPC
    inclui a despesa de não residentes** no território económico. Para medir preços isso é
    irrelevante, um quilo de pão sobe o mesmo para quem lá vive e para quem está de passagem.
    Para medir a *estrutura de consumo das famílias portuguesas*, não é: mistura dois universos.

    O IDF não tem esse problema (mede agregados residentes, por inquérito direto) e é a única
    fonte aberta que desce ao quintil de rendimento. Em contrapartida é **quinquenal**, pelo que a
    sua estrutura envelhece entre vagas. É o IHPC, revisto todos os anos, que garante que o
    movimento dos preços acompanha a substituição de produtos.

    A tabela de **“Quem está mais exposto”**, no separador Despesa e composição, sai dos quadros
    **Q.2.11** do INE, que dão a despesa alimentar por quintil de rendimento equivalente ao nível
    do grupo de produtos e em euros.

    **O período de referência do IDF não é um ano civil.** A recolha decorreu entre **3 de
    fevereiro de 2022 e 5 de fevereiro de 2023, em 26 quinzenas seguidas**, com cada agregado
    inquirido ao longo de 14 dias; e o INE **não corrige os valores para uma data comum**
    (Metainformação do IDF, V.6.1.1 e V.7.4, “Ajustamentos dos dados: não aplicável”). Os valores
    publicados são, portanto, uma média aos preços desses doze meses.

    Por isso a atualização ao mês corrente parte da média do índice na janela **fevereiro de 2022
    a janeiro de 2023**, e não de um ano civil. Não é um detalhe:@EFEITO_JANELA@
            """.replace("@EFEITO_JANELA@",
                        (f" indexar a partir de {IDF_JANELA_RECOLHA[1][:4]} subestimaria hoje "
                         f"o valor atual em **{euro(_ganho_janela)}/mês**, "
                         f"{percentagem(_ganho_janela / _idf_2023 * 100, sinal=False)}.")
                        if (abs(_ganho_janela) > 0.005 and _idf_2023) else
                        " a escolha da base de indexação move o valor de topo da aplicação."))

            _cmp = comparar_ponderadores(dados["pesos"], dados["variacoes_classe"])
            if _cmp["inflacao_idf"] is not None and _cmp["inflacao_ihpc"] is not None:
                st.markdown("**O que a escolha muda, medido**")
                m1, m2, m3 = st.columns(3)
                m1.metric("Inflação alimentar (ponderação IHPC)",
                          percentagem(_cmp["inflacao_ihpc"], sinal=False))
                m2.metric("Inflação alimentar (ponderação IDF)",
                          percentagem(_cmp["inflacao_idf"], sinal=False))
                m3.metric("Diferença atribuível à ponderação",
                          pontos(_cmp["diferenca"]))

                _dv = _cmp["desvios"].copy()
                _dv["Grupo"] = _dv["classe"]
                _dv = _dv[["Grupo", "quota_ihpc", "quota_idf", "desvio"]]
                _dv.columns = ["Grupo", "Quota IHPC (%)", "Quota IDF (%)", "Desvio (p.p.)"]
                st.dataframe(
                    _dv.sort_values("Desvio (p.p.)", key=abs, ascending=False),
                    width="stretch", hide_index=True,
                    column_config={
                        "Quota IHPC (%)": st.column_config.NumberColumn(format="%.1f"),
                        "Quota IDF (%)": st.column_config.NumberColumn(format="%.1f"),
                        "Desvio (p.p.)": st.column_config.NumberColumn(format="%+.2f"),
                    })
                st.caption(
                    f"Desvio médio absoluto entre as duas estruturas: "
                    f"**{pontos(_cmp['desvio_medio'], sinal=False)}** · "
                    f"máximo: **{pontos(_cmp['desvio_maximo'], sinal=False)}** · "
                    "As quotas são calculadas dentro da alimentação, sobre a soma dos nove grupos."
                )
                st.caption(
                    "Parte deste desvio é a inclusão de turistas no IHPC, parte é a diferença de "
                    "anos de referência entre as duas fontes. Os dados abertos disponíveis não "
                    "permitem separar as duas causas, não existe exercício nacional de "
                    "conciliação entre inquérito e Contas Nacionais."
                )

            st.info("""
    **Uma terceira base foi ponderada e rejeitada.** Estudou-se acrescentar um instrumento que
    lesse a evolução dos ponderadores do IHPC deflacionados pelo índice de preços de cada grupo,
    para isolar mudanças de *quantidade* consumida das mudanças de preço. Não avançou: o
    Documento Metodológico do IPC estabelece que “a amostra e estrutura de ponderação referem-se
    sempre a dezembro do ano n−1” e que os ponderadores **já incorporam** a variação de preços
    até esse momento. Deflacioná-los pela média anual do índice desconta duas vezes uma parte do
    efeito-preço e nenhuma vez outra parte. A direção do resultado pode manter-se; a magnitude
    não é defensável. Medir alterações de quantidade exigiria dados de volume que nenhuma destas
    fontes publica.
            """)

        with bloco_metodologia("Escalas de equivalência",
                               chaves="OCDE modificada per capita raiz quadrada adultos equivalentes"):
            st.markdown(
                "Duas pessoas não gastam o dobro de uma: há partilha de compras, aquisição em "
                "maiores quantidades e menor desperdício. As escalas traduzem essa partilha em "
                "coeficientes."
            )
            st.dataframe(pd.DataFrame([
                {"Escala": ESCALAS[k]["nome"], "1.º adulto": ESCALAS[k]["primeiro"],
                 "Adulto adicional": ESCALAS[k]["adulto"], "Criança (<14)": ESCALAS[k]["crianca"],
                 "Nota": ESCALAS[k]["nota"]}
                for k in ESCALAS
            ]), width="stretch", hide_index=True)
            st.latex(r"eq(A,C) = 1 + \alpha \cdot (A - 1) + \beta \cdot C")

            st.markdown("""
    **Como a escala é aplicada, e uma propriedade que convém ter presente.**

    O ponto de partida é a despesa do agregado médio nacional. A escala não calcula a despesa a
    partir do zero: **ajusta** desse agregado médio para o agregado em análise, e é aplicada aos
    **dois lados** do rácio, ao numerador e ao denominador.

    Daqui decorre uma propriedade que importa reter: como o denominador também depende da escala,
    **o efeito de mudar de escala inverte-se** conforme o agregado seja maior ou menor do que a
    média nacional.

    Coeficientes menores significam que cada pessoa a mais custa menos, o que **comprime as
    diferenças** entre agregados de dimensão diferente. Um agregado menor do que a média
    aproxima-se dela por cima (o valor sobe); um agregado maior aproxima-se dela por baixo
    (o valor desce). O ponto de viragem é exatamente a dimensão média.

    Não é um artefacto do cálculo: é o que qualquer normalização por escala de equivalência
    produz. É também a razão pela qual a aplicação apresenta sempre um intervalo, e não um valor
    único.
            """)
            st.markdown("---")
            st.markdown("**Porque não se usa a norma da UE por defeito, o teste**")
            st.markdown("""
    A escala OCDE modificada é a norma europeia para o *rendimento*, e foi construída para o
    consumo total, em que a partilha da habitação gera fortes economias de escala. Na alimentação
    essas economias são mais fracas, por a partilha de refeições não gerar poupança equivalente à
    da partilha da habitação.

    A ressalva não fica pelo qualitativo: **o IDF 2022/2023 permite medi-la.** O teste
    restringe-se a agregados **sem crianças dependentes**, onde a escala é mais limpa, e compara o
    rácio de despesa observado entre “2 ou mais adultos” e “1 adulto” com o rácio que cada escala
    prevê para essa mesma composição.
            """)

            _te = testar_escalas()
            if not _te.empty:
                _tab_e = pd.DataFrame([{
                    "Escala": r.nome.split(" (")[0],
                    "Rácio previsto": r.previsto,
                    "Desvio na alimentação": r.desvio_alimentar,
                    "Desvio na despesa total": r.desvio_total,
                } for r in _te.itertuples()])
                st.dataframe(
                    _tab_e, width="stretch", hide_index=True,
                    column_config={
                        # Duas casas no máximo em toda a aplicação: esta coluna
                        # arredondava a três (decisão da Inês, 13.08.2026).
                        "Rácio previsto": st.column_config.NumberColumn(format="%.2f"),
                        "Desvio na alimentação": st.column_config.NumberColumn(format="%+.1f%%"),
                        "Desvio na despesa total": st.column_config.NumberColumn(format="%+.1f%%"),
                    })
                # Duas casas no máximo, como no resto da aplicação
                # (decisão da Inês, 13.08.2026): eram os dois únicos números
                # com três.
                _r_al = numero(ESCALAS_TESTE_RACIO["alimentar"], 2)
                _r_to = numero(ESCALAS_TESTE_RACIO["total"], 2)
                st.caption(
                    f"Rácio observado: **{_r_al}** na alimentação e **{_r_to}** na despesa total. "
                    f"Desvio positivo = a escala **subestima** o custo dos agregados maiores. "
                    f"Fonte: {ESCALAS_TESTE_FONTE}."
                )

                _mod = _te[_te["escala"] == "ocde_modificada"]
                _org = _te[_te["escala"] == "ocde_original"]
                if not _mod.empty and not _org.empty:
                    _dm = float(_mod["desvio_alimentar"].iloc[0])
                    _dmt = float(_mod["desvio_total"].iloc[0])
                    _do = float(_org["desvio_alimentar"].iloc[0])
                    st.success(f"""
    **A ressalva confirma-se, e o controlo sobre a despesa total reforça a robustez do teste.**

    Na alimentação, a escala OCDE modificada **subestima** o custo dos agregados maiores em
    **{('%+.1f' % _dm).replace('.', ',')}%**. Na despesa total, aquilo para que a escala foi
    desenhada, o desvio **inverte-se**, para {('%+.1f' % _dmt).replace('.', ',')}%. O problema
    não é da escala em geral: é da alimentação em particular.

    Das três, a **OCDE original** é a que fica mais perto do observado
    ({('%+.1f' % _do).replace('.', ',')}% contra {('%+.1f' % _dm).replace('.', ',')}%), o que
    confirma empiricamente a escolha por defeito desta ferramenta, que de outro modo assentaria
    apenas num argumento teórico.
                    """)
                    st.caption(
                        f"**Precisão.** As duas restrições disponíveis nos quadros do IDF são "
                        f"ligeiramente inconsistentes entre si (adultos equivalentes médios "
                        f"reconstruídos: 1,435 contra 1,407 publicados). Consoante a que se "
                        f"privilegie, a subestimação fica entre **{ESCALAS_TESTE_INTERVALO[0]}% e "
                        f"{ESCALAS_TESTE_INTERVALO[1]}%**. O resultado é robusto no sinal e na "
                        f"ordem de grandeza, não no algarismo."
                    )

                # ---- circularidade do pressuposto, declarada e medida ----
                _sens = sensibilidade_escalas()
                if not _sens.empty:
                    _n_pressuposto = ESCALAS_TESTE_COMPOSICAO[1][0]
                    st.warning(f"""
    **Há uma circularidade neste teste, e é preciso dizê-lo.** O grupo “3 ou mais adultos” não tem
    contagem publicada: os **{numero(_n_pressuposto, 3)} adultos** usados no cálculo foram deduzidos
    admitindo que o quadro Q.2.8 do INE aplica a **escala OCDE modificada**, que é depois uma das
    três escalas avaliadas. O teste não é, portanto, inteiramente independente daquilo que avalia.
                    """)
                    _tab_s = pd.DataFrame([{
                        "Adultos no grupo “3 ou +”": (
                            numero(r.adultos_3mais, 3)
                            + (", pressuposto" if r.e_o_pressuposto else "")),
                        "Per capita": percentagem(r.desvio_per_capita),
                        "OCDE original": percentagem(r.desvio_ocde_original),
                        "OCDE modificada": percentagem(r.desvio_ocde_modificada),
                        "Mais próxima do observado": ESCALAS[r.mais_proxima]["nome"].split(" (")[0],
                        "Controlo inverte": "sim" if r.controlo_inverte else "não",
                    } for r in _sens.itertuples()])
                    st.dataframe(_tab_s, width="stretch", hide_index=True)

                    _todas_subestimam = bool(_sens["modificada_subestima"].all())
                    _todas_invertem = bool(_sens["controlo_inverte"].all())
                    _min_d = float(_sens["desvio_ocde_modificada"].min())
                    _max_d = float(_sens["desvio_ocde_modificada"].max())
                    _n_original = int((_sens["mais_proxima"] == "ocde_original").sum())
                    # Os dois pontos de rutura estavam inscritos à mão, ao lado
                    # de números calculados em direto (auditoria, E9). São
                    # bissecção sobre constantes que a aplicação já tem.
                    _rut = pontos_de_rutura_das_escalas()
                    _min_c, _max_c = float(_sens["adultos_3mais"].min()), float(_sens["adultos_3mais"].max())
                    _txt_rut = ""
                    if _rut["ultrapassagem"] is not None:
                        _txt_rut = (f"só acima de **{numero(_rut['ultrapassagem'], 2)} adultos em "
                                    f"média** é que a modificada passaria à frente")
                        if _rut["anulacao"] is not None:
                            _txt_rut += (f", e o desvio só se anularia com "
                                         f"**{numero(_rut['anulacao'], 2)} adultos**, valor sem "
                                         f"sentido para um grupo “3 ou mais”")
                        _txt_rut += ". "
                    st.caption(
                        f"**As duas conclusões sobrevivem ao pressuposto.** Em todos os cenários "
                        f"testados, de {numero(_min_c, 1)} a {numero(_max_c, 1)} adultos, a OCDE "
                        f"modificada continua a subestimar o custo alimentar "
                        f"{'(sempre)' if _todas_subestimam else '(nem sempre)'}, entre "
                        f"{percentagem(_min_d)} e {percentagem(_max_d)}, e o controlo da despesa "
                        f"total continua a inverter o sinal "
                        f"{'em todos' if _todas_invertem else 'nem sempre'}. A OCDE original é a "
                        f"mais próxima do observado em {_n_original} dos {len(_sens)} cenários; "
                        f"{_txt_rut}A direção do resultado não depende do pressuposto; a "
                        f"magnitude depende."
                    )


        # ---- gráfico do cruzamento das escalas ----
        with bloco_metodologia("Divergência e cruzamento das três escalas",
                               chaves="cruzamento dimensão média divergência"):
            st.markdown(f"""
Cada escala responde de forma diferente à mesma questão: **qual o acréscimo de despesa por cada
pessoa adicional?**

| Escala | 1.ª pessoa | Cada pessoa adicional |
|---|---|---|
| Per capita | 1,0 | **1,0**, sem partilha |
| OCDE original | 1,0 | **0,7**, desconto moderado |
| OCDE modificada | 1,0 | **0,5**, desconto forte |

As três escalas **partem do mesmo ponto de referência**, a despesa do agregado médio português,
com **{('%.2f' % dim_efetiva).replace('.', ',')} pessoas**. A escala não calcula a despesa a
partir do zero: distribui a partir dessa referência. É por essa razão que **as três se cruzam
exatamente nessa dimensão**.
            """)

            tam = [1, 1.5, 2, 2.5, 3, 4, 5, 6]
            figS = go.Figure()
            cores_s = {"per_capita": "#7a5ea8", "ocde_original": VERDE,
                       "ocde_modificada": DOURADO}
            for chave in ESCALAS:
                e_ = ESCALAS[chave]
                eq_med = e_["primeiro"] + e_["adulto"] * (max(dim_efetiva, 1.0) - 1)
                por_unidade = valor_medio_agregado / eq_med if eq_med else 0
                ys = [por_unidade * (e_["primeiro"] + e_["adulto"] * (n - 1)) for n in tam]
                figS.add_trace(go.Scatter(
                    x=tam, y=ys, name=e_["nome"].split(" (")[0],
                    line=dict(color=cores_s[chave], width=2.6),
                    hovertemplate="%{x} pessoas: %{y:.0f} €<extra>"
                                  + e_["nome"].split(" (")[0] + "</extra>"))
            figS.add_vline(
                x=dim_efetiva, line_width=2, line_dash="dash", line_color="#64748b",
                annotation_text=f"agregado médio: {('%.2f' % dim_efetiva).replace('.', ',')}",
                annotation_position="top")
            figS.update_layout(height=340, margin=dict(t=46, b=40, l=10, r=10),
                               xaxis_title="Pessoas no agregado (todas com 14+ anos)",
                               yaxis_title="Despesa alimentar mensal (€)",
                               legend=dict(orientation="h", y=1.22, x=0),
                               hovermode="x unified")
            grafico(figS)

            st.info("""
**Leitura do gráfico**

**À esquerda do cruzamento**, agregados **menores** do que a média: a OCDE modificada produz
valores **mais altos**. Se cada pessoa adicional acresce pouco (0,5), ter menos pessoas do que a
média **reduz pouco** a despesa, e o valor mantém-se próximo do médio. Na escala per capita, em
que cada pessoa conta pela totalidade, ter menos pessoas **reduz muito mais** a despesa.

**À direita**, agregados **maiores**: a relação inverte-se. Se cada pessoa adicional acresce
pouco, acrescentar pessoas **aumenta pouco** a despesa, e a OCDE modificada passa a produzir os
valores mais baixos.

**Em resumo:** desconto forte **comprime** as diferenças, aproximando todos os agregados da
média; desconto fraco **amplifica-as**. O cruzamento está sempre na dimensão média, porque é aí
que não há nada a descontar nem a acrescentar.
            """)



        with bloco_metodologia("Rendimento e salários: distinção entre bruto e líquido",
                               chaves="EU-SILC salário médio salário mínimo RMMG bruto líquido"):
            # O exemplo “920 € legal, 1 073 € difundido” estava inscrito à mão e
            # envelhece de seis em seis meses, quando o Eurostat publica o
            # semestre seguinte. Sai da série (auditoria de 12.08.2026, L16).
            _sm_meto = (dados.get("salario") or {}).get("PT")
            if _sm_meto:
                _exemplo_rmmg = (
                    f"Em **{_sm_meto['periodo']}**, o Eurostat difundiu "
                    f"**{euro(_sm_meto['valor'], 0)}** e o valor legal correspondente da RMMG é de "
                    f"**{euro(round(_sm_meto['valor'] * 12 / 14), 0)}/mês**, o quociente por "
                    f"14/12, arredondado ao euro porque a RMMG é fixada em euros inteiros.")
            else:
                _exemplo_rmmg = ("A série do salário mínimo não está disponível nesta sessão, "
                                 "pelo que o exemplo numérico não é apresentado.")
            st.markdown("""
    Três fontes distintas alimentam os indicadores de esforço. **A diferença entre bruto e líquido
    não é um detalhe: muda o resultado de forma material** e, se ignorada, leva a subestimar a
    pressão sobre quem aufere menos.

    | Fonte | Conjunto | O que é | Natureza | Frequência |
    |---|---|---|---|---|
    | Rendimento das famílias | [`ilc_di03`](https://ec.europa.eu/eurostat/databrowser/view/ilc_di03/default/table) | Rendimento monetário do agregado, todas as fontes | **Líquido** | Anual |
    | Salário médio | [`nama_10_a10`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a10/default/table) ÷ [`nama_10_a10_e`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a10_e/default/table) | Massa salarial ÷ trabalhadores por conta de outrem | **Bruto** | Anual |
    | Salário mínimo | [`earn_mw_cur`](https://ec.europa.eu/eurostat/databrowser/view/earn_mw_cur/default/table) | RMMG em duodécimos de 14 mensalidades | **Bruto** | Semestral (janeiro e julho) |

    **Rendimento das famílias.** Vem do EU-SILC e é o mais completo: inclui salários, pensões,
    prestações sociais, rendimentos de capital e transferências, deduzidos impostos e contribuições.
    É publicado **por unidade de consumo equivalente**, já dividido pelas unidades do agregado,
    segundo a escala OCDE modificada. Para obter o rendimento de um agregado concreto, multiplica-se
    pelas suas unidades equivalentes.

    Estão disponíveis a **média** e a **mediana**. A aplicação usa a média por defeito, porque a
    despesa alimentar também é uma média, combinar média com mediana inflacionaria o rácio.

    **Salário médio.** Calculado a partir das Contas Nacionais: massa salarial (remunerações e
    salários) dividida pelo número de trabalhadores por conta de outrem. É uma remuneração
    **bruta**, antes de imposto e contribuições do trabalhador.

    **Não é “o salário médio” no sentido corrente.** O divisor conta **todos** os trabalhadores por
    conta de outrem, incluindo os que trabalham **a tempo parcial**, e o numerador exclui as
    contribuições sociais a cargo do empregador. O resultado fica portanto **abaixo** da remuneração
    de um trabalhador a tempo inteiro, e não é comparável com as estatísticas de ganho médio que
    convertem tudo a equivalentes a tempo completo.

    Duas vantagens sobre as séries de remunerações líquidas: os códigos são estáveis, e fica na
    **mesma base estatística** da despesa alimentar usada como âncora, o que evita mais uma mistura
    de universos. Sendo bruto, é comparável com o salário mínimo, mas **não** com o rendimento
    líquido do EU-SILC.

    **Salário mínimo.** O Eurostat **não** publica o valor legal. Publica a retribuição mínima
    mensal garantida convertida em **duodécimos de 14 mensalidades**, o valor legal multiplicado
    por 14/12, para que os países com 12, 13 ou 14 pagamentos anuais fiquem comparáveis.
    @EXEMPLO_RMMG@

    A aplicação usa o valor do Eurostat, e usa-o de propósito: a despesa alimentar é mensal e
    recorrente, pelo que a base correta para o peso no orçamento é a **média mensal do rendimento
    anual**, com os subsídios distribuídos pelos 12 meses. Usar o valor legal atribuiria ao mês de
    dezembro um esforço alimentar que na prática se dilui. O que estava errado era o rótulo, não
    o número: a aplicação chamava-lhe “valor legal”, e não é.

    É **bruto**: não desconta a contribuição do trabalhador para a Segurança Social nem o imposto
    retido, nem inclui prestações familiares. O rendimento efetivamente disponível de quem aufere o
    mínimo é **inferior** ao valor apresentado, logo, o esforço alimentar real é **superior** ao
    que este rácio indica.

    É por essa razão que a aplicação assinala as duas naturezas com cores distintas e adverte que
    não são diretamente comparáveis entre si.

    **Quem come e quem aufere não são o mesmo conjunto.** O multiplicador de salários é o número de
    pessoas que **efetivamente auferem rendimento**, nunca o total do agregado. E há um caso em que
    a diferença é decisiva: **os jovens entre os 14 e os 18 anos**.

    Para a escala de equivalência, uma pessoa de 15 ou 17 anos conta como adulta, come como
    adulta, e é isso que a escala mede. Mas não aufere rendimento. Um agregado de dois pais e dois
    adolescentes tem **quatro pessoas com peso alimentar de adulto e dois rendimentos**.

    É a composição em que o esforço alimentar é mais elevado, e precisamente a que os indicadores
    médios menos revelam. A aplicação assinala-a quando ocorre.
            """.replace("@EXEMPLO_RMMG@", _exemplo_rmmg))


        # Os três blocos seguintes estavam no separador Despesa e composição, por
        # baixo do gráfico do esforço. Dois são metodologia, o que os números
        # assumem, e porque é que as escalas divergem, e o terceiro é contexto
        # sobre a distribuição salarial. O aviso que não podia sair de lá, que os
        # valores são limites superiores, ficou no (i) do título da secção
        # (decisão da Inês, 13.08.2026).
        # Vinte linhas sobre **uma** das três referências, mais dez de nota de
        # fonte. O conteúdo é bom e fica; deixa é de ser a primeira coisa que
        # se lê a seguir ao gráfico (Inês, 13.08.2026).
        with bloco_metodologia("Posição do salário mínimo na distribuição salarial",
                               chaves="Banco de Portugal distribuição salarial mediana"):
            st.markdown(
                "Não é o agregado típico, é o **limiar inferior** da distribuição. Mas "
                "está longe de ser um caso extremo: em 2025 a RMMG equivalia a **91% do "
                "salário mediano** do setor privado (índice de Kaitz), contra 87% em "
                "2019, e o rácio entre a mediana e o percentil 10 da distribuição salarial "
                "era de apenas **1,1**. A concentração é tal que, nos microdados da "
                "Segurança Social, **o segundo decil da distribuição salarial não chega a "
                "ter observações distintas**. Serve para dimensionar o limiar inferior, "
                "não para caracterizar a generalidade das famílias, mas esse limiar está "
                "muito mais perto do meio da distribuição do que se supõe."
            )
            st.caption(
                "Fonte: Banco de Portugal, *Boletim Económico* de junho de 2026, Caixa 5, "
                "“A distribuição dos salários dos trabalhadores por conta de outrem”, com "
                "base em microdados da Segurança Social. Abrange o **setor privado** "
                "(exclui a Administração Pública) e considera vínculos a tempo completo "
                "com 30 dias declarados e remuneração igual ou superior a 80% da RMMG. "
                "Pelo *Structure of Earnings Survey* do Eurostat, que só inquire empresas "
                "com 10 ou mais trabalhadores, o índice de Kaitz português era de 69% em "
                "2024, ainda assim o **mais elevado da área do euro**."
            )

        with bloco_metodologia("Pressupostos subjacentes a estes valores",
                               chaves="majorante limites superiores esforço"):
            if base_chave == "contas":
                if _racio_cn_silc is not None:
                    _frase_racio = (
                        f"O consumo total por agregado das Contas Nacionais "
                        f"({_eng_cn['ano']}) é **{numero(_racio_cn_silc, 2)} vezes** o "
                        f"rendimento do EU-SILC ({rendimentos[indic_r]['PT']['ano']}) para "
                        f"um agregado da dimensão média, rácio que implicaria taxa de "
                        f"poupança fortemente negativa.")
                else:
                    _frase_racio = (
                        "O consumo por agregado das Contas Nacionais é estruturalmente "
                        "superior ao rendimento do EU-SILC, rácio que implicaria taxa de "
                        "poupança negativa. (O valor exato não é calculável nesta sessão.)")
                st.error(f"""
**São limites superiores, não estimativas.** O **numerador** (a despesa alimentar) vem das
**Contas Nacionais**; o **denominador** (o rendimento) vem do **EU-SILC**. São universos
estatísticos diferentes: as Contas Nacionais incluem rendas imputadas, consumo de instituições
sem fins lucrativos e consumo no território, incluindo o de não residentes; o EU-SILC mede
rendimento monetário líquido dos residentes.

{_frase_racio}
**Combinar as duas bases sobrestima o esforço.**

Leia as **diferenças entre composições** e a **direção** como informativas; o **nível** como
majorante.

*Escolhendo a base **IDF** em “Despesa e composição”, esta incompatibilidade reduz-se substancialmente,
o IDF e o EU-SILC são ambos inquéritos a agregados residentes.*
                """)
            else:
                st.warning("""
**Bases estatísticas próximas, mas não idênticas.** Com a base **IDF**, o **numerador** (a
despesa alimentar) e o **denominador** (o rendimento do EU-SILC) vêm ambos de **inquéritos a
agregados residentes**, o que elimina a maior parte da incompatibilidade que afeta a base das
Contas Nacionais.

Subsistem diferenças: são inquéritos distintos, com amostras, períodos de referência e critérios
de imputação próprios, e ambos sub-reportam. O rácio continua a dever ler-se como **ordem de
grandeza**, não como medição.

Leia as **diferenças entre composições** e a **direção** como informativas; o **nível** com
reserva.
                """)
            st.markdown(f"""
**1 · As crianças não auferem rendimento.** O número de salários multiplica-se pelos
**adultos com rendimento** indicados acima, nunca pelo total de pessoas. Um casal com dois
filhos e dois salários continua a ter dois salários, mas quatro pessoas a alimentar, e é
essa assimetria que faz o esforço subir.

**2 · Bruto e líquido não se misturam.** Só o **rendimento do EU-SILC** é líquido, já
descontados impostos e contribuições, e somadas as prestações. O **salário médio** e o
**salário mínimo** são **brutos**: é o que consta do contrato ou do diploma, antes de
qualquer desconto. Como o rendimento efetivamente disponível é inferior aos valores brutos,
o esforço real sobre eles é **superior** ao que aqui aparece.

**3 · O agregado está num valor central da distribuição.** Agregados abaixo dele têm esforço
**superior** ao apresentado, e é justamente aí que a pressão alimentar mais se faz sentir.
A medida por escalão de rendimento está na secção **“Quem está mais exposto”**, mais acima
nesta página, a partir dos quadros Q.2.11 do IDF 2022/2023.

**4 · As três escalas cruzam-se na dimensão média, e é isso que explica o resultado
contraintuitivo.** Ver o gráfico logo abaixo deste bloco.

**5 · Numerador e denominador usam escalas diferentes.** A despesa alimentar é ajustada pela
escala que escolheu em “Despesa e composição” (**{ESCALAS[escala_chave]["nome"].split(" (")[0]}**); o
rendimento do EU-SILC tem de usar a **OCDE modificada**, que é a que esse inquérito aplica.
A consequência é mensurável:
            """)

            # Tabela calculada com os dados da sessão. Era um quadro de
            # valores fixos rotulado “ilustrativos”, ao lado de números
            # calculados em direto: o leitor não distinguia uns dos outros
            # (auditoria de 10.08.2026, C2).
            if tem_rend and indic_r:
                _r_anual = rendimentos[indic_r]["PT"]["valor"]
                _casos = [("1 adulto", 1, 0), ("Casal", 2, 0), ("Casal + 2", 2, 2)]
                _linhas_esc = []
                for _ch, _esc in ESCALAS.items():
                    _linha = {"Escala usada na despesa": _esc["nome"].split(" (")[0]}
                    if _ch == "ocde_modificada":
                        _linha["Escala usada na despesa"] += " (igual à do rendimento)"
                    for _rot, _a, _c in _casos:
                        _desp = despesa_do_agregado(
                            media_agregado, dim_efetiva, _a, _c, _ch)
                        _ue = unidades_equivalentes(_a, _c, "ocde_modificada")
                        _rend_mes = _r_anual * _ue / 12
                        _linha[_rot] = (f"{_desp / _rend_mes * 100:.1f}%"
                                        .replace(".", ",") if _rend_mes else "—")
                    _linhas_esc.append(_linha)
                st.dataframe(pd.DataFrame(_linhas_esc),
                             width="stretch", hide_index=True)
                st.caption(
                    f"Calculado com os dados desta sessão: âncora "
                    f"**{base_ancora['nome']}** ({euro(media_agregado)}/mês para o agregado "
                    f"médio) e rendimento equivalente "
                    f"{'médio' if indic_r == 'MEAN_EI' else 'mediano'} do EU-SILC de "
                    f"{rendimentos[indic_r]['PT']['ano']}. Muda com a âncora que escolher."
                )
            else:
                st.info(
                    "O quadro comparativo das escalas precisa do rendimento do EU-SILC, "
                    "que não está disponível nesta sessão."
                )

            st.markdown("""
Se as duas escalas coincidirem, **o esforço é constante** seja qual for a composição, ambos
os lados escalam de forma idêntica. A subida com o número de pessoas resulta, portanto, da
**diferença entre as escalas**. Isso não invalida a leitura, porque a alimentação tem
economias de escala genuinamente mais fracas do que o consumo total; mas a **magnitude**
depende da escala escolhida.

**Utilização recomendada:** a **direção** do resultado é robusta; o **valor exato** é condicional
à escala adotada. A sensibilidade pode ser testada alterando a escala em “Despesa e composição”.
            """)

        bloco("04 · Dados, atualização e rastreabilidade")

        with bloco_metodologia("Como a aplicação se mantém atualizada",
                               chaves="cache recarregar publicação calendário"):
            st.markdown("""
    **Os dados seguem três regimes distintos**, e a diferença entre eles determina o que está
    atualizado sozinho e o que exige que alguém intervenha.

    **(i) Em direto, a cada arranque.** As séries do Eurostat não estão gravadas em lado nenhum: em
    cada arranque a aplicação pede-as e usa **a observação mais recente de cada uma**. É o regime da
    esmagadora maioria dos números, e é dele que trata o resto deste bloco.

    **(ii) Recolhas versionadas, com data de extração.** O **cabaz da DECO PROteste** e o
    **Observatório de Preços do GPP** não têm interface de acesso automatizado. São recolhidos por
    script para ficheiros guardados no repositório, e só mudam quando alguém corre o script e regista
    o resultado. Cada um dos dois separadores mostra a data da recolha em vigor, e avisa quando ela
    envelhece ou quando a fonte deixa de publicar.

    **(iii) Constantes transcritas de publicações oficiais.** Alguns valores estão inscritos no
    código, com fonte e data, porque a origem é um documento e não uma série consultável: o **IDF
    2022/2023** do INE, o **SOFI** da FAO, a avaliação do **Banco de Portugal** ao IVA zero de 2023,
    que calibra a repercussão, e os **Censos 2021**, que servem de recuo ao número de agregados.
    Mudam por revisão editorial, à cadência da publicação que os origina.

    **Como escolhe o valor mais recente.** Para cada série, ordena as observações por período e fica
    com a última. Isso funciona qualquer que seja a periodicidade, mensal (`2026-06`), semestral
    (`2026S1`) ou anual (`2026`), porque a codificação de períodos do Eurostat é ordenável.
    A consequência prática: **quando o Eurostat publicar um mês novo, a aplicação passa a usá-lo sem
    qualquer alteração ao código**.

    **Janela de pedido.** As séries anuais e semestrais são pedidas com **oito anos** de margem. É
    folgado de propósito: se uma publicação atrasar, continua a haver observações no intervalo e a
    aplicação não fica sem dados. As séries mensais usam janelas mais curtas, por serem densas.

    **Cache de seis horas.** Os dados ficam guardados em memória durante seis horas, para não repetir
    pedidos desnecessários, as séries mudam no máximo uma vez por mês. O botão **Recarregar do
    Eurostat**, no topo da página, limpa a cache e força um pedido novo.

    **O período de cada valor está sempre visível.** Cada indicador mostra o seu período de
    referência (“Salário mínimo (2026S1)”, “Contas Nacionais 2024”) para que nunca se confunda a
    data da consulta com a data do dado.
            """)
            st.info("""
    **Quando esperar dados novos**

    | Dado | Publicação |
    |---|---|
    | Estimativa rápida do índice (só agregados) | Último dia útil do mês de referência |
    | **Índice completo, com todas as classes** | **Cerca do dia 17 do mês seguinte** |
    | Ponderadores | Com os dados de janeiro, em fevereiro |
    | Salário mínimo | Janeiro e julho |
    | Rendimento e salário médio (EU-SILC) | Anual, com cerca de um ano de desfasamento |
    | Contas Nacionais (âncora em euros) | Anual, com cerca de dois anos de desfasamento |
    | Paridades de poder de compra | Junho do ano seguinte |

    O separador mostra sempre o último mês disponível no topo da aplicação. Se um valor parecer
    desatualizado, é porque a fonte ainda não publicou, não porque a aplicação não o foi buscar.
            """)
            st.warning("""
    **Alteração metodológica de fevereiro de 2026, e o que ela custou a esta aplicação.**
    A partir dos dados de janeiro de 2026, o índice passou a ser compilado segundo a **ECOICOP
    versão 2** (alinhada com a COICOP 2018), com período de referência **2025 = 100**. As séries
    com a classificação anterior não foram apenas rebaseadas: **foram arquivadas em conjuntos
    próprios, que deixaram de avançar**. O Eurostat inscreveu-o no título (“HICP) monthly data
    (index) **(1996-2025)**”.

    Os conjuntos antigos continuam a responder normalmente, com dados bem formados, apenas
    parados em dezembro de 2025, **respondem sem avançar**, e um pedido a um deles não devolve
    erro nenhum. A aplicação usa `prc_hicp_minr` e `prc_hicp_iw`, os conjuntos vivos, e as
    classes trazem as designações da COICOP 2018.

    Daqui decorre a regra que a vigilância de frescura aplica: **uma série que responde não é
    uma série que avança**, e a verificação tem de cobrir também as fontes com API.
            """)

        with bloco_metodologia("Origem dos dados (conjuntos utilizados e ligações)",
                               chaves="Eurostat conjuntos prc_hicp nama ligações"):
            # O confronto entre o EU-LFS e os Censos no ano em que ambos existem
            # estava inscrito à mão. Sai da série guardada nesta sessão.
            _lfs_comum = (dados.get("agregados_serie") or {}).get(str(AGREGADOS_ANO))
            _dif_comum = (abs(_lfs_comum / AGREGADOS_CENSOS - 1) * 100
                          if _lfs_comum else None)
            st.markdown("""
    O quadro seguinte reúne os conjuntos pedidos em direto ao **Eurostat**, que difunde as
    estatísticas compiladas pelos institutos nacionais, no caso português, o **INE**. As ligações
    abrem diretamente o conjunto no Data Browser do Eurostat. Os dados dos outros dois regimes, as
    recolhas por script e as constantes transcritas, estão identificados mais abaixo e nos
    separadores onde são usados.

    | Elemento | Conjunto | O que mede | Frequência |
    |---|---|---|---|
    | Ponderadores por grupo | [`prc_hicp_iw`](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_iw/default/table) | Fração de cada mil euros de consumo total (‰) | Anual |
    | Índice de preços | [`prc_hicp_minr`](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_minr/default/table) | Nível do índice (unidade `@UNID_INDICE@`), não são euros | Mensal |
    | Variação homóloga | [`prc_hicp_minr`](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_minr/default/table) | Subida face ao mesmo mês do ano anterior (unidade `RCH_A`, %) | Mensal |
    | Despesa alimentar (âncora) | [`nama_10_cp18`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_cp18/default/table) | Despesa efetiva em euros (Contas Nacionais, COICOP 2018) | Anual |
    | Dimensão do agregado | [`ilc_lvph01`](https://ec.europa.eu/eurostat/databrowser/view/ilc_lvph01/default/table) | N.º médio de pessoas por agregado | Anual |
    | N.º de agregados | [`lfst_hhnhtych`](https://ec.europa.eu/eurostat/databrowser/view/lfst_hhnhtych/default/table) | Total de agregados familiares (milhares), série anual | Anual |
    | Nível de preços comparado | [`prc_ppp_ind_1`](https://ec.europa.eu/eurostat/databrowser/view/prc_ppp_ind_1/default/table) | Quão caros são os alimentos, categoria `@CAT_PPP@` (UE-27 = 100) | Anual |
    | Rendimento das famílias | [`ilc_di03`](https://ec.europa.eu/eurostat/databrowser/view/ilc_di03/default/table) | Rendimento líquido equivalente, médio e mediano | Anual |
    | Salário médio | [`nama_10_a10`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_a10/default/table) ÷ `nama_10_a10_e` | Remuneração média **bruta** dos trabalhadores por conta de outrem | Anual |
    | Salário mínimo | [`earn_mw_cur`](https://ec.europa.eu/eurostat/databrowser/view/earn_mw_cur/default/table) | RMMG em duodécimos de 14 mensalidades, **bruta** | Semestral |

    **Parâmetros que não são dados oficiais**

    | Parâmetro | Origem | Nota |
    |---|---|---|
    | Taxa **atual** de cada grupo | **Apurada**, não editável | É a **taxa média efetiva**, calculada dos ponderadores por subclasse da COICOP 2018 e das Listas I e II. Não é um parâmetro do utilizador: é um facto medido |
    | Taxa **do cenário** | Parâmetro do utilizador | Limitada às taxas que existem no Código do IVA, isenção, 6%, 13% e 23% |
    | Adultos com rendimento | Parâmetro do utilizador | Multiplicador dos salários; as crianças não entram |
    | Repercussão | **Calibrada**, @RHO@ % por defeito, ajustável | Já não é uma hipótese de trabalho: é derivada da avaliação do Banco de Portugal ao “IVA zero” de 2023, sobre a medida idêntica no mesmo país. Banda @RHO_LO@ % a @RHO_HI@ % |

    **Dois números de agregados, para dois usos diferentes.** O denominador da âncora das Contas
    Nacionais é o número de agregados **do ano da despesa**, hoje @ANO_DESPESA@, e é por isso que
    a aplicação usa @AGREG_ANCORA@ agregados nesse cálculo. A extrapolação nacional do simulador de
    IVA usa o **ano mais recente**, @ANO_AGREGADOS@, com @AGREG_RECENTE@ agregados, porque o que se
    extrapola é o efeito de uma medida sobre o país de hoje. Usar o número mais recente também no
    denominador da âncora baixá-la-ia por razão nenhuma: os agregados cresceram, e a despesa não os
    acompanhou porque é de outro ano.

    **Recuo do n.º de agregados:** se o conjunto anual do Eurostat não estiver disponível ou
    devolver um valor implausível, a aplicação usa o valor censitário, **@CENSOS@** agregados
    domésticos privados (@CENSOS_FONTE@, [INE](https://www.ine.pt)).

    **Recuo da dimensão média do agregado:** se o `ilc_lvph01` não responder, entra a constante
    **@DIM_RECUO@ pessoas** (@DIM_FONTE@), e a aplicação passa a dizê-lo. É o número que
    divide a despesa média nacional, pelo que **todos os valores em euros dependem dele**.

    As duas fontes do n.º de agregados não medem o mesmo universo: o Inquérito ao Emprego é uma
    amostra e exclui alojamentos coletivos, pelo que lê sistematicamente abaixo do recenseamento
    exaustivo. Em @ANO_COMUM@, ano em que ambos existem, **@LFS_COMUM@** contra **@CENSOS@**,
    menos @DIF_COMUM@ %.

    **Período de referência do IDF:** @IDF_JANELA_FONTE@.
            """
            # Os valores da repercussão vêm do `config` e não são escritos à mão:
            # o bloco não pode ser f-string (contém chavetas literais), por isso
            # substituem-se por marcador.
            .replace("@RHO@", numero(REPERCUSSAO_PADRAO * 100, 0))
            .replace("@RHO_LO@", numero(REPERCUSSAO_BANDA[0] * 100, 1))
            .replace("@RHO_HI@", numero(REPERCUSSAO_BANDA[1] * 100, 0))
            # O ano da despesa estava inscrito à mão (“hoje 2022”) e a migração
            # para o `nama_10_cp18` (E16) deixou-o para trás: passou a ser 2024, e
            # este parágrafo contradizia a barra de estado da própria aplicação
            # (auditoria de 12.08.2026, K7).
            # O denominador é sempre o da âncora das Contas Nacionais, seja qual
            # for a base escolhida na barra lateral: é dela que o parágrafo fala.
            .replace("@ANO_DESPESA@", str(dados.get("despesa_ano") or "—"))
            .replace("@ANO_AGREGADOS@", str(dados.get("agregados_ano") or "—"))
            .replace("@AGREG_ANCORA@", numero(_den_contas["valor"]))
            .replace("@AGREG_RECENTE@", numero(agregados))
            # Restantes números que estavam inscritos à mão neste quadro: a
            # unidade do índice, a categoria das PPP efetivamente obtida, o
            # recuo censitário e o confronto de 2021 entre EU-LFS e Censos,
            # todos disponíveis em constantes ou nos dados da sessão
            # (auditoria de 12.08.2026, L16).
            .replace("@UNID_INDICE@", str(dados.get("base_indice") or "—"))
            .replace("@CAT_PPP@", str(dados.get("pli_cat")
                                      or eurostat.PPP_CATEGORIA_PREFERIDA))
            .replace("@CENSOS@", numero(AGREGADOS_CENSOS))
            .replace("@CENSOS_FONTE@", AGREGADOS_FONTE)
            .replace("@DIM_RECUO@", numero(DIMENSAO_RECUO, 1))
            .replace("@DIM_FONTE@", DIMENSAO_RECUO_FONTE)
            .replace("@ANO_COMUM@", str(AGREGADOS_ANO))
            .replace("@LFS_COMUM@", numero(_lfs_comum) if _lfs_comum else "—")
            .replace("@DIF_COMUM@", numero(_dif_comum, 1) if _dif_comum is not None else "—")
            .replace("@IDF_JANELA_FONTE@", IDF_JANELA_FONTE))
            st.info(
                "**Sobre os ponderadores.** Somam 1 000 ‰ sobre **todo** o cabaz do índice, não "
                "sobre a alimentação. Os nove grupos alimentares somam apenas o peso da alimentação "
                "no consumo total. Por isso o cálculo normaliza pela soma dos nove, e não pelos 1 000 ‰."
            )

        with bloco_metodologia("Ver os dados em bruto (endereços exatos desta sessão)",
                               chaves="endereços URL API pedidos"):
            st.markdown("""
Cada número da aplicação vem de um pedido concreto ao Eurostat. Os endereços abaixo são os que
foram efetivamente usados **nesta sessão**, abrem no navegador e descarregam o ficheiro em
bruto, exatamente os mesmos dados que a aplicação leu.

Servem para **verificar qualquer valor** sem depender da aplicação, e para reproduzir o cálculo
em Excel ou noutra ferramenta.
            """)
            _end = dados.get("enderecos") or []
            if not _end:
                st.info("Sem endereços registados nesta sessão.")
            else:
                # Faltava aqui o `ilc_mdes03`: a privação alimentar aparecia com
                # o código em bruto no lugar da descrição. E cinco pedidos
                # distintos ao `prc_hicp_minr`, índice, variações, série longa
                # de PT, agregados especiais, saíam todos com o **mesmo**
                # rótulo, num painel que existe para distinguir a proveniência
                # de cada número (auditoria de 12.08.2026, L12).
                _rot = {
                    "prc_hicp_iw": "Ponderadores, coluna “Ponderador ‰”",
                    "prc_hicp_minr": ("Índice de preços e variação homóloga, "
                                      "atualiza a âncora ao mês corrente e alimenta "
                                      "a coluna “Variação %”"),
                    "nama_10_cp18": "Despesa alimentar e consumo total, âncora em euros",
                    "ilc_lvph01": "Dimensão média do agregado",
                    "lfst_hhnhtych": "Número de agregados familiares",
                    "ilc_di03": "Rendimento equivalente das famílias",
                    "ilc_mdes03": "Privação alimentar severa (EU-SILC)",
                    "earn_mw_cur": "Salário mínimo",
                    "nama_10_a10": "Massa salarial, numerador do salário médio",
                    "nama_10_a10_e": "Trabalhadores por conta de outrem, denominador",
                    "prc_ppp_ind_1": "Nível de preços comparado",
                }

                def _chave_do_pedido(dataset: str, url: str) -> str:
                    """A chave SDMX ou os filtros que distinguem este pedido."""
                    corte = url.split(f"/{dataset}/")
                    if len(corte) > 1:
                        return corte[1].split("?")[0]
                    pergunta = url.split("?")
                    if len(pergunta) > 1:
                        uteis = [p for p in pergunta[1].split("&")
                                 if not p.startswith(("format=", "lang="))]
                        return "&".join(uteis)
                    return ""

                _repetidos = {d for d, _u, _v in _end
                              if sum(1 for x, _y, _z in _end if x == d) > 1}
                for _i, (_ds, _url, _via) in enumerate(_end, 1):
                    _detalhe = ""
                    if _ds in _repetidos:
                        _chave = _chave_do_pedido(_ds, _url)
                        if _chave:
                            _detalhe = f"  \nPedido {_i} · seleção `{_chave[:120]}`"
                    st.markdown(
                        f"**{_rot.get(_ds, _ds)}**  \n"
                        f"`{_ds}` · via **{_via}** · [abrir os dados em bruto]({_url})"
                        + _detalhe)
                st.caption(
                    "Cada endereço é o do pedido que **produziu efetivamente** o número, "
                    "não o de uma tentativa. Quando a via SDMX falha, a aplicação recorre à "
                    "API Statistics e é esse o endereço que aqui aparece.  \n"
                    "Um mesmo conjunto pode aparecer várias vezes: são pedidos diferentes ao "
                    "mesmo conjunto (classes, agregados, países ou janelas distintas), e a "
                    "linha “seleção” mostra o que os separa.  \n"
                    "Formato SDMX-CSV: uma linha por observação, com as dimensões em colunas "
                    "(`coicop18`, `geo`, `TIME_PERIOD`) e o valor em `OBS_VALUE`. A via "
                    "Statistics devolve JSON-stat."
                )

        with bloco_metodologia("Como se obtém cada coluna da tabela detalhada",
                               chaves="quota contributo exemplo numérico"):
            st.markdown("""
A tabela do primeiro separador tem cinco colunas calculadas. Cada uma vem de um sítio concreto.

**Código**, a classe COICOP, de `CP0111` a `CP0119`. Não é calculado: é a nomenclatura
oficial. `CP0111` é pão e cereais, `CP0112` carne, e assim por diante.

**Ponderador (‰)**, vem tal e qual de `prc_hicp_iw`, sem transformação. Diz quantos de cada
mil euros do consumo total das famílias vão para aquele grupo. Se pão e cereais tiver 28,1 ‰,
significa 2,81% do consumo total, e, dentro da alimentação, 28,1 dividido pela soma dos nove.

**Quota**, o ponderador do grupo dividido pela soma dos nove ponderadores. É a fração da
despesa **alimentar** que cabe àquele grupo. A soma das nove quotas dá 100%.

**Valor (€)**, a despesa alimentar mensal do agregado, multiplicada pela quota do grupo.
            """)
            st.latex(r"V_i = \text{despesa total} \times \frac{w_i}{\sum_j w_j}")
            st.markdown("""
**Variação (%)**, vem tal e qual de `prc_hicp_minr`, sem transformação. É a variação homóloga
oficial daquele grupo: de quanto subiram os preços face ao mesmo mês do ano anterior.

**Contributo (€)**, quantos euros do agravamento dos últimos doze meses se devem àquele grupo.
Se o grupo vale hoje *Vᵢ* e os preços subiram *gᵢ* por cento, há um ano valia *Vᵢ/(1+gᵢ)*:
            """)
            st.latex(r"\text{contributo}_i = V_i - \frac{V_i}{1+g_i} = V_i \cdot \frac{g_i}{1+g_i}")
            st.info("""
**Exemplo numérico.** Para uma despesa alimentar mensal de **400 €**, com o grupo “carne” a
registar um ponderador de 42,3 ‰ numa soma de 195,0 ‰:

1. **Quota** = 42,3 ÷ 195,0 = **21,7%**
2. **Valor** = 400 € × 0,217 = **86,77 €**
3. **Variação** = 4,8% (lida diretamente do Eurostat)
4. **Contributo** = 86,77 × 0,048 ÷ 1,048 = **3,97 €**

Interpretação: do acréscimo de despesa mensal face ao ano anterior, **3,97 €**
devem-se à carne. Somando os nove contributos obtém-se exatamente o agravamento total, é uma
propriedade verificada por teste automático.
            """)
            st.warning("""
**O que não é calculado a partir de preços.** Nenhuma coluna resulta de observar preços de
produtos. Os ponderadores e as variações vêm prontos do Eurostat; o único cálculo é a
repartição de um valor total por essas proporções. É por isso que a tabela é uma
**reconstituição**, e não uma medição.
            """)

        with bloco_metodologia("Estado de atualização das séries",
                               chaves="vigilância frescura prazo desfasamento"):
            st.markdown("""
    **Uma série que responde não é uma série que avança.** Um conjunto arquivado devolve HTTP 200
    e dados bem formados, apenas parou. Sem esta verificação, um conjunto nessas condições passa
    despercebido indefinidamente: nada na resposta o denuncia.

    O prazo de cada série é o seu **desfasamento normal de publicação mais um ciclo**, e não um
    prazo uniforme: as Contas Nacionais têm dois anos de atraso por construção, e está certo que
    tenham. O que este quadro procura é a série que **parou**, não a série que é lenta.
            """)
            if _fresc.empty:
                st.info("Sem séries a vigiar nesta sessão.")
            else:
                # A idade conta a partir do **fim** do período. Numa série anual
                # cujo período é o ano corrente, os ponderadores de 2026, o
                # salário mínimo de 2026-S2, esse fim ainda não chegou, e a
                # coluna mostrava **idades negativas**: “−141 dias”. O sinal está
                # certo aritmeticamente e é absurdo como idade
                # (auditoria de 12.08.2026, L8). Passa a distinguir-se o período
                # ainda a decorrer, que não tem idade nenhuma.
                _tab_f = pd.DataFrame([{
                    # Estado em texto, e não em símbolos: é a coluna que decide
                    # se os números se podem citar.
                    "Estado": ("Parou" if r.desatualizada
                               else ("Não verificável" if not r.verificada
                                     else ("A decorrer"
                                           if (r.dias is not None and r.dias < 0)
                                           else "Dentro do prazo"))),
                    "Série": r.serie,
                    "Conjunto": r.conjunto,
                    "Cadência": r.cadencia,
                    "Último período": r.periodo,
                    "Idade (dias)": (None if r.dias is None else max(int(r.dias), 0)),
                    "Prazo (dias)": r.limite_dias,
                    "Porquê este prazo": r.porque,
                } for r in _fresc.itertuples()])
                st.dataframe(_tab_f, width="stretch", hide_index=True)
                st.caption(
                    "**Parou**, a série deixou de avançar. **Dentro do prazo**, está a "
                    "publicar como esperado. **A decorrer**, o período mais recente ainda "
                    "está a decorrer: a série está à frente da data corrente e a idade é "
                    "zero. **Não verificável**, período não interpretável; não é acusação, "
                    "mas também não é confirmação. A idade conta a partir do **fim** do "
                    "período, que é a leitura mais favorável à fonte."
                )

        with bloco_metodologia("Registo das ligações desta sessão",
                               chaves="SDMX Statistics API pedidos"):
            st.dataframe(pd.DataFrame(dados["registo"],
                                      columns=["Dados pedidos", "Via de acesso usada",
                                               "N.º de observações"]),
                         width="stretch", hide_index=True)
            st.info("""
    **“SDMX” não é um método de ponderação, é a via de acesso aos dados.**

    SDMX (*Statistical Data and Metadata eXchange*) é a norma internacional de troca de dados
    estatísticos, usada pelo Eurostat, INE, BCE e FMI. Aqui designa apenas **por que porta a
    aplicação foi buscar os números**:

    - **SDMX 2.1**, o filtro segue no próprio endereço, pelo que o Eurostat devolve exatamente as
      séries pedidas. É a via preferida.
    - **API Statistics**, os filtros seguem como parâmetros. Usada se a primeira falhar.

    Ambas devolvem **os mesmos números oficiais**. A via usada não afeta os resultados; consta aqui
    apenas para diagnóstico.
            """)

        bloco("05 · Nomenclatura, âmbito e limitações")

        with bloco_metodologia("Distinção entre despesa alimentar e cabaz",
                               chaves="DECO nomenclatura designação"):
            st.markdown("""
Os dois termos designam objetos diferentes, e a aplicação usa apenas o primeiro para o que
mede. “Cabaz” aparece só quando se fala de cabazes **de terceiros** ou do “cabaz zero” de 2023.

| | **Cabaz** | **Despesa alimentar** |
|---|---|---|
| O que é | Lista de produtos com quantidades definidas | Quanto uma família gasta em alimentação |
| Como se obtém | Somando os preços dos artigos da lista | Repartindo despesa efetiva por grupos |
| Unidade natural | Um ato de compra | Um mês |
| Quantidades | Fixas e conhecidas | Não existem, só euros |

Esta aplicação **não tem cabaz nenhum**: não conhece quantidades, não observa preços de
produtos, não tem lista de artigos. Tem despesa em euros e variações de preço oficiais.
A designação cabaz não corresponde, por isso, ao que a ferramenta mede.

            """)
        with bloco_metodologia("De onde vem a classificação COICOP",
                               chaves="ECOICOP classes designações revisão 2018"):
            st.markdown("""
    A **COICOP** (*Classification of Individual Consumption According to Purpose*) é uma
    classificação das **Nações Unidas** (Divisão de Estatística), não do Eurostat. Serve para
    organizar a despesa de consumo das famílias **por finalidade**, e é usada mundialmente nas
    Contas Nacionais e nos inquéritos às despesas.

    A União Europeia adota-a numa versão própria, a **ECOICOP** (*European COICOP*), tornada
    obrigatória para o índice de preços pelo Regulamento (UE) 2016/792. É por isso que os mesmos
    códigos aparecem no INE, no Eurostat e nos institutos de todos os Estados-Membros: não é uma
    convenção do Eurostat, é uma norma internacional que o Eurostat implementa.

    A hierarquia relevante aqui:

    | Nível | Código | Designação |
    |---|---|---|
    | Divisão | 01 | Produtos alimentares e bebidas não alcoólicas |
    | Grupo | 01.1 | Produtos alimentares |
    | Classes | 01.1.1 a 01.1.9 | As nove do quadro abaixo |

    Estas nove classes são usadas nesta aplicação porque são o **nível mais fino em que o Eurostat
    publica simultaneamente ponderadores e índices** para todos os Estados-Membros. Qualquer outro
    agrupamento (fresco contra processado, saudável contra não saudável) exigiria microdados que
    não existem em acesso público.

    **A aplicação usa a COICOP versão 2018 (ECOICOP ver.2)**, em vigor no índice desde janeiro de
    2026. As designações abaixo são as **do INE**, não uma tradução desta ferramenta: estão
    transcritas do anexo do relatório do IDF 2022/2023. A forma curta é a usada nos cartões e nos
    gráficos, onde não cabe a designação completa.
            """)
            st.dataframe(pd.DataFrame([
                {"Código": f"01.1.{c['cod'][5]}",
                 "Forma curta": c["nome"],
                 "Designação oficial (INE, COICOP 2018)": c["oficial"]}
                for c in CLASSES
            ]), width="stretch", hide_index=True)
            st.caption(f"Fonte das designações: {CLASSES_FONTE}.")
            st.info("""
    **A revisão mudou o conteúdo das classes, não só os nomes.** Os códigos `CP0111` a `CP0119`
    sobreviveram, mas o que está dentro deles mudou, a classe 01.1.2 passou a incluir animais
    vivos, a 01.1.6 os frutos de casca rija, a 01.1.7 os tubérculos e as leguminosas, a 01.1.9 os
    alimentos pré-preparados. Os rótulos da versão anterior, “Pão e cereais”, “Fruta”,
    “Legumes e hortícolas”, deixaram por isso de descrever o que a classe contém.

    Há um efeito lateral que vale a pena registar: **o IDF 2022/2023 já usava a COICOP 2018**,
    enquanto o índice ainda estava na versão 1. Durante esse período a aplicação cruzava as duas
    (estrutura de despesa numa classificação, variação de preços na outra), sob o mesmo rótulo.
    Com a migração, as duas fontes passaram a estar **na mesma classificação**.
            """)

        with bloco_metodologia("O limiar dos 14 anos nas escalas de equivalência",
                               chaves="14 anos crianças adultos OCDE limiar"):
            st.markdown("""
    O limiar dos 14 anos **não é uma escolha desta aplicação nem a definição demográfica de
    criança**. É o limiar inscrito nas próprias escalas de equivalência:

    - **Escala OCDE modificada**, norma do Eurostat para o rendimento: 1,0 ao primeiro adulto,
      0,5 a cada pessoa adicional **com 14 ou mais anos**, 0,3 a cada pessoa **com menos de 14**.
    - **Escala OCDE original**: 1,0 / 0,7 / 0,5, com o mesmo limiar.

    Alterar o limiar para 15, 16 ou 18 anos invalidaria os coeficientes, que foram estimados com
    aquela fronteira. Para usar outra idade seria preciso outra escala, estimada em conformidade.

    Isto é distinto das definições demográficas do INE, que variam consoante o contexto: nas
    estatísticas demográficas “jovens” são frequentemente os 0-14 anos; na proteção de menores, a
    menoridade vai até aos 18. São conceitos com finalidades diferentes, e não se misturam com os
    limiares das escalas de equivalência.

    **Consequência prática que importa reter.** Entre os 14 e os 18 anos, uma pessoa conta como
    adulta para efeitos de peso alimentar (e com razão, porque come como adulta) mas não aufere
    rendimento. Por isso a aplicação separa as duas contagens: **pessoas com 14 ou mais anos**
    determina a despesa; **quantas auferem rendimento** determina o denominador do esforço. Não são
    o mesmo número, e confundi-los subestima a pressão sobre as famílias com adolescentes.
            """)

        with bloco_metodologia("Limitações a declarar em qualquer uso",
                               chaves="limitações ressalvas privação severa SOFI amostragem"):
            st.markdown("""
    1. **A decomposição não é observação.** É uma imputação de um valor total por ponderadores
       oficiais; não substitui a recolha de preços produto a produto.
    2. **Não há quantidades físicas.** A ferramenta mede despesa e variação de preço, não quilos
       nem litros. Para raciocinar em quantidades seria necessário o IDEF/INE ou dados de transação.
    3. **A âncora parte de uma média nacional.** Não distingue escalão de rendimento nem região.
    4. **As escalas de equivalência são aproximações, e há um viés quantificável.** Construídas
       para o consumo total; além disso, o agregado médio nacional é modelado como composto **apenas
       por adultos**, porque a dimensão média é publicada sem decomposição etária. Como o agregado
       médio real inclui menores, que pesam menos na escala, o denominador fica **sobrestimado em
       cerca de 4 a 5%**, e todos os valores por agregado saem **subestimados na mesma proporção**.
       O viés é sistemático e na mesma direção para todas as composições, pelo que não afeta as
       comparações entre elas.
    5. **Desfasamento das Contas Nacionais.** A âncora assenta num ano com cerca de dois anos de
       desfasamento, atualizado por índice de preços.
    6. **A taxa de partida de cada grupo é apurada, não predefinida.** O Código do IVA classifica
       por produto; a aplicação trabalha por grupo COICOP. Cada grupo entra na simulação com a
       sua **taxa média efetiva**, apurada dos ponderadores por subclasse, e não com a taxa
       predominante. Subsiste como aproximação a parcela **indeterminada** do
       apuramento e a atribuição por predominância; a sensibilidade a ambas está apresentada como
       intervalo. Ver o painel “Repartição da despesa alimentar pelas taxas legais de IVA”, no
       separador do simulador de IVA.
    7. **A repercussão está calibrada, mas continua a ser o parâmetro decisivo.** Parte de
       @RHO_LIM@ %, derivado da avaliação do Banco de Portugal ao “IVA zero” de 2023, a
       medida idêntica, no mesmo país.
       Mesmo calibrado, é o número que mais move o resultado: qualquer valor do simulador é
       condicional a ele e deve ser apresentado como intervalo. E a estimativa vem de uma medida
       **temporária e mediática**, avaliada ao longo de quatro meses, uma alteração permanente
       e discreta pode repercutir-se menos.
    8. **A extrapolação agregada é ilustrativa.** Não é uma estimativa de custo orçamental.
            """
            # O valor por defeito da repercussão sai do `config`, como em todo o
            # resto da aplicação. Estava inscrito à mão neste ponto, e é o
            # padrão que as auditorias já apanharam quatro vezes (C2/E9/K8/L16).
            .replace("@RHO_LIM@", numero(REPERCUSSAO_PADRAO * 100, 0)))
            st.warning("""
    **9 · O preço usado não é o preço que uma família concreta paga.** Há duas razões distintas,
    e ambas devem ser declaradas:

    **Dispersão entre operadores.** O índice é uma **média nacional ponderada** de uma amostra de
    estabelecimentos (grande distribuição, comércio tradicional, canais especializados), com
    peso atribuído a cada canal e região segundo o consumo real. Mas os operadores praticam preços
    muito diferentes entre si: quem compre sempre em *discount* enfrenta níveis abaixo desta
    média; quem viva em zona de baixa densidade, acima. O índice capta bem a **variação**; o
    **nível** de cada família oscila em torno dele, e essa dispersão não é visível aqui.

    **Preço de prateleira e preço pago.** O critério do INE é preciso e vale a pena citá-lo em vez
    de o aproximar. O Documento Metodológico do IPC (2023) determina que os descontos entram no
    índice **“desde que de aplicação generalizada aos consumidores”**. Daqui decorre uma linha
    divisória nítida:

    | Tipo de desconto | Entra no índice? |
    |---|---|
    | Promoção aberta a qualquer cliente, campanha de folheto, redução de preço em loja | **Sim** |
    | Cartão de fidelização, cupão, talão, desconto em cartão | **Não**, é condicional |

    *O critério entre aspas é citação literal (INE, Documento Metodológico do IPC, 2023, pp. 26 e
    40). A arrumação dos tipos de desconto no quadro é leitura desta ferramenta: o documento fixa a
    regra, não classifica casos concretos.*

    Não é, portanto, que a recolha falhe descontos ao acaso: exclui **por regra** os que dependem
    de o consumidor aderir a um programa. O desvio entre preço registado e preço pago é o que
    resulta desses descontos condicionais, e **tende a crescer** à medida que os programas de
    fidelização se difundem, o que significa que o índice pode sobrestimar ligeiramente a
    aceleração do preço efetivamente pago.

    Só dados de transação (e-fatura ou *scanner data*) permitiriam medir o preço realmente pago
    e a sua dispersão entre operadores e territórios. O IPC **não usa scanner data**: a recolha
    automatizada é por *web scraping* em cadeias de implantação nacional.
            """)
            st.warning("""
    **Os ponderadores do IHPC incluem turistas, confirmado em fonte primária.** O Documento
    Metodológico do IPC (INE, 2023) é explícito: “O IHPC inclui a despesa realizada pelos não
    residentes ("turistas") no território económico e exclui a despesa dos residentes no exterior,
    originando uma estrutura de ponderação diferente da utilizada no IPC.”

    Em Portugal, dado o peso do turismo, a diferença não é trivial. **Não afeta as variações de
    preço** (essas medem o mesmo movimento independentemente de quem compra) mas afeta qualquer
    leitura de **estrutura de consumo** feita sobre eles, e afeta o nível de qualquer valor obtido
    por repartição.

    É por isso que a aplicação separa as duas funções: o **IHPC** dá o movimento dos preços, o
    **IDF** dá a estrutura e a distribuição. O INE publica ponderadores do IPC em conceito
    nacional, mas apenas em ine.pt; o Eurostat só difunde os do IHPC.
            """)
            # Estava numa caixa de aviso no separador Despesa e composição, sob os
            # gráficos de acessibilidade. São limitações, e as limitações estão
            # todas aqui (decisão da Inês, 13.08.2026).
            st.markdown("""
    **10 · O custo da dieta saudável não é uma âncora de despesa.** É um **mínimo normativo**, o
    preço da dieta mais barata que cumpre os requisitos nutricionais, não o que as famílias
    gastam. Compará-lo com a despesa alimentar do topo do separador Despesa e composição seria
    confrontar objetos diferentes. Acresce que vem em **PPP$**, não em euros: converter exigiria a
    paridade de poder de compra do consumo privado, e mesmo assim não o tornaria comparável com
    despesa efetiva.

    **11 · A privação severa é auto-reportada**, de inquérito por amostragem, e o Eurostat não
    publica intervalos de confiança para esta série. Variações de duas ou três décimas entre anos
    não devem ser lidas como tendência.

    **12 · O SOFI é publicado em PDF, não em API**, ao contrário de tudo o resto nesta
    ferramenta, os seus valores estão inscritos no código e têm de ser atualizados à mão a cada
    edição anual.
            """)

        with bloco_metodologia("Base legal e documentação",
                               chaves="regulamento legislação EUR-Lex metadados"):
            st.markdown("""
    **Quadro legal do índice**

    - [Regulamento (UE) 2016/792](https://eur-lex.europa.eu/legal-content/PT/TXT/?uri=CELEX%3A32016R0792), quadro legal do IHPC
    - Regulamento de Execução (UE) 2020/1148, especificações metodológicas e técnicas
    - Regulamento (CE) n.º 1445/2007, regras comuns das Paridades de Poder de Compra

    **Documentação metodológica**

    - [Eurostat, HICP methodology](https://ec.europa.eu/eurostat/statistics-explained/index.php/HICP_methodology)
    - [Metadados do IHPC](https://ec.europa.eu/eurostat/cache/metadata/en/prc_hicp_esms.htm)
    - [Derivação dos ponderadores do IHPC](https://ec.europa.eu/eurostat/documents/10186/10693286/Derivation-of-HICP-weights-for-2022.pdf)
    - [Metadados das Paridades de Poder de Compra](https://ec.europa.eu/eurostat/cache/metadata/en/prc_ppp_esms.htm)
    - [Níveis comparativos de preços, Statistics Explained](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Comparative_price_levels_of_consumer_goods_and_services)

    **Classificação**

    - COICOP, Divisão de Estatística das Nações Unidas
    - ECOICOP, versão europeia, obrigatória por regulamento

    **Fontes nacionais**

    - [INE](https://www.ine.pt), Índice de Preços no Consumidor, Censos 2021, Inquérito às Despesas das Famílias
            """)

        # ---- o índice, escrito no lugar guardado lá em cima ----
        # A caixa de procura é criada aqui, e não no topo, porque é aqui que o
        # índice já existe. O Streamlit devolve o valor escrito na mesma
        # execução, pelo que a lista abaixo dela responde de imediato.
        with _slot_indice:
            _q = st.text_input(
                "Procurar na metodologia",
                key="busca_metodologia",
                placeholder="Procurar por assunto: escalas, IVA, turistas…",
                label_visibility="collapsed")
            indice_metodologia(_q)

# ==========================================================================
# Rodapé institucional
# ==========================================================================
st.markdown(f"""
<footer class="sg-rodape">
  <div class="sg-rodape__l">
    <div>
      <p class="sg-rodape__org">{ORGANISMO}</p>
      <p class="sg-rodape__uni">Suporte à Decisão · {UNIDADE}</p>
    </div>
    <p class="sg-rodape__app">Despesa alimentar das famílias · {date.today().year}</p>
  </div>
  <p class="sg-rodape__nota">{RODAPE}</p>
</footer>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Voltar ao topo
# --------------------------------------------------------------------------
# Emitido no fim e não junto ao cabeçalho: sendo `position: fixed`, o sítio no
# documento não altera onde aparece, e aqui fica arrumado com o resto do que é
# moldura da página em vez de conteúdo.
#
# O rótulo vai em `aria-label` porque a seta é desenhada em CSS e o elemento não
# tem texto: sem ele, um leitor de ecrã anunciaria uma ligação sem nome. O
# `title` dá a mesma informação a quem usa rato e hesita.
st.markdown(
    '<a class="sg-subir" href="#topo" aria-label="Voltar ao topo do documento" '
    'title="Voltar ao topo"></a>',
    unsafe_allow_html=True)
