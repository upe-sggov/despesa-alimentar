"""
Testes dos cálculos analíticos.

Executar:  python -m pytest tests/ -v
"""
import pandas as pd
import pytest

from src.calculos import decompor, resumo_iva, simular_iva
from src.config import CODIGOS


@pytest.fixture
def decomposicao():
    pesos = {c: 100.0 for c in CODIGOS}        # nove classes com peso igual
    variacoes = {c: 10.0 for c in CODIGOS}     # todas a +10 %
    return decompor(900.0, pesos, variacoes)


def test_quotas_somam_um(decomposicao):
    assert decomposicao["quota"].sum() == pytest.approx(1.0)


def test_valores_somam_o_cabaz(decomposicao):
    assert decomposicao["valor"].sum() == pytest.approx(900.0)


def test_contributo_e_aditivo(decomposicao):
    """A soma dos contributos tem de igualar a variação do total."""
    total = decomposicao["valor"].sum()
    antes = sum(r.valor / (1 + r.variacao / 100) for r in decomposicao.itertuples())
    assert decomposicao["contributo"].sum() == pytest.approx(total - antes)


def test_contributo_conhecido():
    """100 € que cresceram 25 % valiam 80 € há um ano: contributo de 20 €."""
    df = decompor(100.0, {"CP0111": 1.0}, {"CP0111": 25.0})
    assert df.loc[df["codigo"] == "CP0111", "contributo"].iloc[0] == pytest.approx(20.0)


def test_variacao_em_falta_nao_quebra():
    df = decompor(100.0, {c: 1.0 for c in CODIGOS}, {})
    assert df["contributo"].isna().all()
    assert df["valor"].sum() == pytest.approx(100.0)


# ------------------------------------------------------------ simulação de IVA
def _uma_classe(valor, iva):
    return pd.DataFrame([{
        "codigo": "CP0111", "classe": "Teste", "emoji": "🍞", "cor": "#000",
        "valor": valor, "iva_defeito": iva,
    }])


def test_base_sem_iva():
    sim = simular_iva(_uma_classe(106.0, 6), {"CP0111": 6}, {"CP0111": 6}, 1.0)
    assert sim["base"].iloc[0] == pytest.approx(100.0)


def test_repercussao_integral():
    """106 € a 6 % passando a 0 %, com repercussão total, dá 100 €."""
    sim = simular_iva(_uma_classe(106.0, 6), {"CP0111": 6}, {"CP0111": 0}, 1.0)
    assert sim["novo_valor"].iloc[0] == pytest.approx(100.0)


def test_repercussao_nula_nao_altera_preco():
    sim = simular_iva(_uma_classe(106.0, 6), {"CP0111": 6}, {"CP0111": 0}, 0.0)
    assert sim["novo_valor"].iloc[0] == pytest.approx(106.0)
    assert sim["iva_depois"].iloc[0] == pytest.approx(0.0)
    assert sim["margem"].iloc[0] == pytest.approx(-6.0)


def test_repercussao_parcial_reparte():
    """Com 40 %, o consumidor poupa 2,40 € e a margem capta 3,60 €."""
    sim = simular_iva(_uma_classe(106.0, 6), {"CP0111": 6}, {"CP0111": 0}, 0.4)
    assert -sim["efetivo"].iloc[0] == pytest.approx(2.40)
    assert -sim["margem"].iloc[0] == pytest.approx(3.60)


def test_subida_de_taxa():
    sim = simular_iva(_uma_classe(106.0, 6), {"CP0111": 6}, {"CP0111": 23}, 1.0)
    assert sim["novo_valor"].iloc[0] == pytest.approx(123.0)


def test_receita_perdida_e_independente_da_repercussao():
    """O Estado perde o mesmo em qualquer cenário; muda quem fica com o dinheiro."""
    perdas = []
    for rho in (0.0, 0.4, 1.0):
        sim = simular_iva(_uma_classe(106.0, 6), {"CP0111": 6}, {"CP0111": 0}, rho)
        perdas.append(resumo_iva(sim, 106.0, 52, 1)["receita_mes"])
    assert all(p == pytest.approx(-6.0) for p in perdas)


# --------------------------------- inversão do efeito da escala
def test_efeito_da_escala_inverte_na_dimensao_media():
    """
    Como a escala é aplicada ao agregado em análise e ao agregado médio de
    referência, o efeito de trocar de escala inverte-se conforme o agregado seja
    menor ou maior do que a média nacional. Não é um erro: é o que qualquer
    normalização por escala de equivalência produz.
    """
    from src.calculos import despesa_do_agregado

    media, dim = 665.70, 2.5

    # agregado MENOR do que a média: coeficientes menores dão valor MAIOR
    casal_orig = despesa_do_agregado(media, dim, 2, 0, "ocde_original")
    casal_modi = despesa_do_agregado(media, dim, 2, 0, "ocde_modificada")
    assert casal_modi > casal_orig

    # agregado MAIOR do que a média: coeficientes menores dão valor MENOR
    familia_orig = despesa_do_agregado(media, dim, 2, 3, "ocde_original")
    familia_modi = despesa_do_agregado(media, dim, 2, 3, "ocde_modificada")
    assert familia_modi < familia_orig

    # o valor é sempre crescente no número de pessoas, seja qual for a escala
    for escala in ("per_capita", "ocde_original", "ocde_modificada"):
        serie = [despesa_do_agregado(media, dim, 1, c, escala) for c in range(0, 5)]
        assert serie == sorted(serie)


def test_esforco_constante_quando_escalas_coincidem():
    """
    Se a despesa e o rendimento usarem a mesma escala de equivalência, o esforço
    alimentar é constante seja qual for a composição do agregado — ambos os lados
    escalam de forma idêntica. A variação observada na aplicação resulta, portanto,
    da diferença entre a escala escolhida para a despesa e a OCDE modificada, que
    o EU-SILC impõe ao rendimento. Propriedade a preservar.
    """
    from src.calculos import despesa_do_agregado, unidades_equivalentes

    media, dim, rendimento_eq = 422.54, 2.4, 11500.0
    esforcos = []
    for adultos, criancas in [(1, 0), (2, 0), (2, 2), (2, 4), (3, 1)]:
        desp = despesa_do_agregado(media, dim, adultos, criancas, "ocde_modificada")
        rend = rendimento_eq * unidades_equivalentes(adultos, criancas, "ocde_modificada") / 12
        esforcos.append(desp / rend * 100)
    assert max(esforcos) - min(esforcos) < 1e-9

    # com escalas diferentes, o esforço tem de crescer com a dimensão
    crescentes = []
    for adultos, criancas in [(1, 0), (2, 0), (2, 2), (2, 4)]:
        desp = despesa_do_agregado(media, dim, adultos, criancas, "ocde_original")
        rend = rendimento_eq * unidades_equivalentes(adultos, criancas, "ocde_modificada") / 12
        crescentes.append(desp / rend * 100)
    assert crescentes == sorted(crescentes)


# ------------------------------------------------ achados da auditoria
def test_receita_constante_apenas_na_isencao_total():
    """
    A receita cessante é independente da repercussão **apenas** quando a taxa do
    cenário é zero. Numa redução parcial, uma repercussão menor mantém o preço
    final mais alto e, portanto, a base tributável maior: o Estado recupera parte
    do que o operador retém. Auditoria de 27.07.2026.
    """
    import pandas as pd
    from src.calculos import resumo_iva, simular_iva

    def um(valor, iva):
        return pd.DataFrame([{"codigo": "X", "classe": "T", "emoji": "", "cor": "#000",
                              "valor": valor, "iva_defeito": iva}])

    # isenção total: receita cessante idêntica para qualquer repercussão
    receitas = [resumo_iva(simular_iva(um(106.0, 23), {"X": 23}, {"X": 0}, r),
                           106.0, 12, 1)["receita_mes"] for r in (0.0, 0.5, 1.0)]
    assert max(receitas) - min(receitas) < 1e-9

    # redução parcial: a receita cessante depende da repercussão
    parciais = [resumo_iva(simular_iva(um(106.0, 23), {"X": 23}, {"X": 6}, r),
                           106.0, 12, 1)["receita_mes"] for r in (0.0, 0.5, 1.0)]
    assert max(parciais) - min(parciais) > 0.5
    # e é decrescente: menos repercussão -> menos receita perdida
    assert parciais == sorted(parciais, reverse=True)


def test_vies_do_agregado_medio_e_sistematico():
    """
    Modelar o agregado médio como composto só por adultos sobrestima o
    denominador e subestima todos os valores por agregado. O viés tem de ser
    proporcional — igual para todas as composições — para não contaminar as
    comparações entre elas. Auditoria de 27.07.2026.
    """
    from src.calculos import despesa_do_agregado

    media = 422.54
    dim_modelo, dim_corrigida = 2.4, 2.28   # ajuste por presença de menores
    racios = []
    for adultos, criancas in [(1, 0), (2, 0), (2, 2), (3, 1), (2, 4)]:
        a = despesa_do_agregado(media, dim_modelo, adultos, criancas, "ocde_original")
        b = despesa_do_agregado(media, dim_corrigida, adultos, criancas, "ocde_original")
        racios.append(b / a)
    assert max(racios) - min(racios) < 1e-9      # viés proporcional
    assert racios[0] > 1.0                        # e no sentido de subestimação


def test_sensibilidade_das_escalas_ao_pressuposto_circular():
    """
    Os 3,288 adultos do grupo «3 ou mais» foram deduzidos assumindo a escala
    OCDE modificada, que é depois uma das escalas avaliadas. A circularidade é
    real; o que o teste fixa é que as **conclusões** não dependem dela dentro
    do intervalo plausível. Auditoria de 10.08.2026, D3.
    """
    from src.calculos import sensibilidade_escalas

    df = sensibilidade_escalas()
    assert not df.empty
    assert df["e_o_pressuposto"].sum() == 1, "o cenário de base tem de estar assinalado"

    # em todo o intervalo plausível a direção mantém-se
    plausivel = df[df["adultos_3mais"] <= 3.5]
    assert plausivel["modificada_subestima"].all()
    assert plausivel["controlo_inverte"].all()
    assert (plausivel["mais_proxima"] == "ocde_original").all()

    # e a magnitude é que se move — se não se movesse, o teste não provava nada
    amplitude = (df["desvio_ocde_modificada"].max()
                 - df["desvio_ocde_modificada"].min())
    assert amplitude > 3.0


def test_idade_fonte_avisa_so_quando_deve():
    """
    O SOFI e o Observatório envelhecem sem a aplicação dar erro. Na dúvida
    sobre a referência, não se acusa a fonte. Auditoria de 10.08.2026, D4.
    """
    from datetime import date

    from src.calculos import idade_fonte

    hoje = date(2026, 8, 11)

    # data ISO, dentro e fora do prazo
    assert idade_fonte("2026-08-10", 60, hoje)["dias"] == 1
    assert idade_fonte("2026-08-10", 60, hoje)["desatualizada"] is False
    assert idade_fonte("2026-05-01", 60, hoje)["desatualizada"] is True

    # ano: tomado como 31 de dezembro, a leitura mais favorável à fonte
    r = idade_fonte(2025, 730, hoje)
    assert r["data"] == date(2025, 12, 31)
    assert r["desatualizada"] is False
    assert idade_fonte(2023, 730, hoje)["desatualizada"] is True

    # referência ilegível: não acusa
    for mau in (None, "", "não sei", "2026-13-45"):
        r = idade_fonte(mau, 60, hoje)
        assert r["data"] is None
        assert r["desatualizada"] is False


def test_formatadores_nao_estragam_o_texto_a_volta():
    """
    O padrão antigo aplicava `.replace(".", ",")` à frase inteira. Numa etiqueta
    como «101.4 %  (+1.4 p.p.)» isso convertia também o sufixo, produzindo
    «p,p,». Os formatadores tocam só no número. Auditoria de 10.08.2026, C5.
    """
    from src.config import milhoes, numero, percentagem, pontos

    # O separador de milhares é um espaço **inquebrável**, como em `euro()`:
    # impede que «4 562 100» parta ao fim da linha.
    nb = " "
    assert numero(4_562_100) == f"4{nb}562{nb}100"
    assert numero(2.5, 1) == "2,5"
    assert numero(None) == "—"

    assert milhoes(984.24) == "984,2 M€"
    assert milhoes(-2460.5) == f"-2{nb}460,5 M€"

    assert pontos(1.4, casas=1) == "+1,4 p.p."
    assert pontos(-0.12) == "-0,12 p.p."
    assert pontos(0.5, sinal=False) == "0,50 p.p."
    assert pontos(3.0, sufixo=" pontos") == "+3,00 pontos"

    # O símbolo cola ao número (Livro de Estilo da SGGov, E.3), mas o sufixo dos
    # pontos percentuais mantém o espaço: são abreviaturas, não símbolos.
    assert percentagem(25.0, sinal=False) == "25,0%"

    # o caso que o padrão antigo estragava
    etiqueta = f"{percentagem(101.4, sinal=False)}  ({pontos(1.4, casas=1)})"
    assert etiqueta == "101,4%  (+1,4 p.p.)"
    assert "p,p," not in etiqueta


def test_mapa_do_iva_cobre_as_nove_classes_e_e_coerente():
    """
    O levantamento das Listas I e II tem de cobrir todas as classes e as taxas
    citadas têm de existir no Código do IVA. Auditoria de 10.08.2026, D2.
    """
    from src.config import CODIGOS, IVA_MAPA, POR_CODIGO

    assert set(IVA_MAPA) == set(CODIGOS)
    legais = {0, 6, 13, 23}
    for cod, mapa in IVA_MAPA.items():
        taxas = mapa["taxas"]
        assert len(taxas) >= 2, f"{cod}: classe declarada homogénea — nenhuma é"
        vistas = []
        for taxa, texto in taxas:
            assert taxa in legais, f"{cod}: taxa {taxa} não existe no CIVA"
            assert texto.strip()
            vistas.append(taxa)
        assert vistas == sorted(vistas), f"{cod}: taxas fora de ordem"
        assert len(vistas) == len(set(vistas)), f"{cod}: taxa repetida"
        # a predefinida de `CLASSES` tem de constar do levantamento, senão as
        # duas fontes de verdade podem divergir sem ninguém dar por isso
        assert POR_CODIGO[cod]["iva"] in vistas, (
            f"{cod}: a taxa predefinida ({POR_CODIGO[cod]['iva']} %) não consta "
            "do levantamento das Listas")


def test_engel_e_um_intervalo_ancorado_no_valor_do_ine():
    """
    O extremo inferior tem de ser **a constante publicada pelo INE**, a mesma
    que alimenta a coluna «Peso no orçamento» da tabela por quintil. Se fosse
    recalculado (2 872 / 23 900 = 12,017 %), o cartão diria 12,0 % por
    arredondamento mas deixaria de ser garantidamente o número da tabela.
    Auditoria de 10.08.2026, B4.
    """
    from src.calculos import intervalo_engel
    from src.config import IDF_PESO_ALIMENTAR

    idf = float(IDF_PESO_ALIMENTAR["total"])

    r = intervalo_engel({"quota": 16.37, "ano": "2022"})
    assert r["minimo"] == idf
    assert r["maximo"] == pytest.approx(16.37)
    assert r["so_idf"] is False

    # sem Contas Nacionais, o intervalo colapsa no valor do IDF
    for ausente in (None, {}, {"quota": None, "ano": "2022"}):
        r = intervalo_engel(ausente)
        assert r["so_idf"] is True
        assert r["minimo"] == r["maximo"] == idf

    # a ordem não pode ser assumida: se as Contas Nacionais ficassem abaixo,
    # o intervalo tem de continuar bem orientado
    r = intervalo_engel({"quota": 9.0, "ano": "2022"})
    assert r["minimo"] == pytest.approx(9.0)
    assert r["maximo"] == idf


def test_denominador_da_ancora_emparelha_o_ano_da_despesa():
    """
    A despesa das Contas Nacionais é de 2022. Dividi-la pelos agregados de 2025
    dá um valor 9,1 % mais baixo por razão nenhuma: a população de agregados
    cresceu, a despesa não a acompanhou porque é de outro ano. O denominador
    tem de ser do ano do numerador. Auditoria de 10.08.2026, B2.
    """
    from src.calculos import agregados_do_ano
    from src.config import AGREGADOS_CENSOS

    serie = {"2021": 3_939_900, "2022": 4_102_600,
             "2024": 4_473_300, "2025": 4_562_100}

    # ano presente na série: usa-o, sem desfasamento
    r = agregados_do_ano(serie, "2022")
    assert r["valor"] == 4_102_600
    assert r["desfasamento"] == 0
    assert r["ano"] == "2022"

    # ano ausente: o mais próximo, com o desfasamento declarado
    r = agregados_do_ano(serie, "2023")
    assert r["desfasamento"] == 1
    assert r["valor"] in (4_102_600, 4_473_300)

    # sem série: recorre aos Censos e continua a declarar o desfasamento
    r = agregados_do_ano({}, "2022")
    assert r["valor"] == AGREGADOS_CENSOS
    assert r["desfasamento"] == 1

    # e o emparelhamento tem mesmo de importar — senão o teste não prova nada
    milhoes = 27_318.0
    emparelhado = milhoes * 1e6 / serie["2022"] / 12
    mais_recente = milhoes * 1e6 / serie["2025"] / 12
    assert abs(mais_recente / emparelhado - 1) > 0.08


def test_candidatas_do_nivel_de_precos_sao_todas_alimentares():
    """
    A aplicação usa a primeira categoria que responda. Se uma reserva não
    alimentar entrar na lista, uma falha da preferida faz a aplicação
    apresentar o nível de preços de todo o consumo sob o título «alimentos» —
    e a conclusão inverte-se de «acima» para «abaixo» da média europeia, sem
    erro nenhum. Auditoria de 10.08.2026, B3.

    No `prc_ppp_ind_1`, o ramo alimentar é `A0101*`. Fora dele estão, entre
    outros, `E011` (consumo final das famílias) e `A01` (consumo individual
    efetivo), que já estiveram nesta lista.
    """
    from src.eurostat import PPP_CATEGORIA_PREFERIDA, PPP_CATEGORIAS_ALIMENTOS

    assert PPP_CATEGORIAS_ALIMENTOS, "a lista não pode ficar vazia"
    for codigo in PPP_CATEGORIAS_ALIMENTOS:
        assert codigo.startswith("A0101"), f"{codigo} não é uma categoria alimentar"
    for proibido in ("E011", "A01", "CP011", "0101"):
        assert proibido not in PPP_CATEGORIAS_ALIMENTOS

    # a preferida tem de estar na lista e ser a primeira a ser tentada
    assert PPP_CATEGORIA_PREFERIDA in PPP_CATEGORIAS_ALIMENTOS
    assert next(iter(PPP_CATEGORIAS_ALIMENTOS)) == PPP_CATEGORIA_PREFERIDA


def test_extrapolacao_nacional_nao_depende_da_composicao():
    """
    O total nacional tem de sair do agregado **médio**. Se sair da despesa já
    ajustada a uma composição, o país inteiro passa a ser contado como se fosse
    todo composto dessa maneira — e o número muda com um parâmetro de leitura.
    Auditoria de 10.08.2026, A3.
    """
    from src.calculos import despesa_do_agregado

    media, dim, agregados = 255.01, 2.4, 4_149_096
    pesos = {c: 100.0 for c in CODIGOS}
    variacoes = {c: 3.0 for c in CODIGOS}
    atuais, cenario = {c: 6.0 for c in CODIGOS}, {c: 0.0 for c in CODIGOS}

    def nacional(despesa_base):
        sim = simular_iva(decompor(despesa_base, pesos, variacoes),
                          atuais, cenario, 1.0)
        return resumo_iva(sim, despesa_base, 12, agregados)["poupanca_agregada_milhoes"]

    correto = nacional(media)

    # a via correta: o agregado médio, seja qual for a composição no ecrã
    for adultos, criancas in [(1, 0), (2, 0), (3, 2), (5, 0)]:
        assert nacional(media) == pytest.approx(correto)

    # e a via errada tem mesmo de divergir — senão o teste não prova nada
    errados = [nacional(despesa_do_agregado(media, dim, a, c, "ocde_original"))
               for a, c in [(2, 0), (5, 0)]]
    assert min(errados) < correto * 0.95
    assert max(errados) > correto * 1.5


# ------------------------------------------------- cabaz por quintil (IDF)
def test_quintis_reproduzem_o_quadro_do_ine():
    """Os niveis vem do Q.2.11.a; nao sao derivados nem reescalados."""
    from src.calculos import cabaz_quintis
    from src.config import IDF_ALIMENTAR_QUINTIL

    df = cabaz_quintis({c: 5.0 for c in CODIGOS}).set_index("quintil")
    for chave, anual in IDF_ALIMENTAR_QUINTIL.items():
        assert df.loc[chave, "despesa_mensal"] == pytest.approx(anual / 12)


def test_quintis_classes_somam_o_total_publicado():
    """A soma das nove classes tem de fechar com o total 01.1, a menos do
    arredondamento do proprio quadro do INE (1 EUR/ano)."""
    from src.config import CLASSES, IDF_ALIMENTAR_QUINTIL, IDF_CLASSES_QUINTIL

    for chave, total in IDF_ALIMENTAR_QUINTIL.items():
        soma = sum(IDF_CLASSES_QUINTIL[c["cod"]][chave] for c in CLASSES)
        assert abs(soma - total) <= 1, chave


def test_quintis_inflacao_uniforme_e_igual_em_todos():
    """Se todas as classes variam o mesmo, a estrutura de consumo e irrelevante:
    todos os quintis tem de dar a mesma taxa."""
    from src.calculos import cabaz_quintis

    df = cabaz_quintis({c: 4.0 for c in CODIGOS})
    assert df["inflacao"].round(10).nunique() == 1
    assert df["inflacao"].iloc[0] == pytest.approx(4.0)


def test_quintis_esforco_e_agravamento_sobre_orcamento():
    from src.calculos import cabaz_quintis

    df = cabaz_quintis({c: 4.0 for c in CODIGOS})
    for r in df.itertuples():
        assert r.agravamento_orcamento == pytest.approx(
            r.agravamento / r.despesa_total_mensal * 100)


def test_quintis_variacoes_em_falta_nao_quebram():
    from src.calculos import cabaz_quintis

    df = cabaz_quintis({})
    assert df["inflacao"].isna().all()
    assert df["despesa_mensal"].gt(0).all()


def test_composicao_quintis_quotas_somam_um():
    from src.calculos import composicao_quintis

    quotas = composicao_quintis().groupby("quintil")["quota"].sum()
    assert quotas.between(0.999, 1.001).all()


def test_comparar_ponderadores_identifica_a_diferenca():
    """Com ponderadores IHPC iguais aos do IDF, a diferenca tem de ser nula."""
    from src.calculos import comparar_ponderadores
    from src.config import CLASSES, IDF_CLASSES_QUINTIL

    pesos_iguais = {c["cod"]: float(IDF_CLASSES_QUINTIL[c["cod"]]["total"]) for c in CLASSES}
    r = comparar_ponderadores(pesos_iguais, {c: 3.0 for c in CODIGOS})
    assert r["diferenca"] == pytest.approx(0.0)
    assert r["desvio_maximo"] == pytest.approx(0.0)

    pesos_torcidos = dict(pesos_iguais)
    pesos_torcidos["CP0111"] *= 3
    r2 = comparar_ponderadores(pesos_torcidos, {**{c: 3.0 for c in CODIGOS}, "CP0111": 20.0})
    assert r2["inflacao_ihpc"] > r2["inflacao_idf"]
    assert r2["desvio_maximo"] > 5.0


# ------------------------------------------- vies de substituicao (Tornqvist)
def _serie_classes(valores_por_ano, unit="I15"):
    """indice_classes sintetico: {ano: {cod: valor}} -> DataFrame como o Eurostat."""
    linhas = []
    for ano, porcod in valores_por_ano.items():
        for cod, v in porcod.items():
            linhas.append({"unit": unit, "coicop": cod, "geo": "PT",
                           "time": f"{ano}-12", "valor": float(v)})
    return pd.DataFrame(linhas)


def _serie_pesos(pesos_por_ano):
    linhas = []
    for ano, porcod in pesos_por_ano.items():
        for cod, v in porcod.items():
            linhas.append({"coicop": cod, "geo": "PT",
                           "time": str(ano), "valor": float(v)})
    return pd.DataFrame(linhas)


def test_indices_iguais_quando_todos_os_precos_sobem_o_mesmo():
    """Se todas as classes sobem na mesma proporcao nao ha substituicao possivel:
    os dois indices tem de coincidir, quaisquer que sejam os ponderadores."""
    from src.calculos import indices_comparados

    idx = _serie_classes({
        2020: {c: 100.0 for c in CODIGOS},
        2021: {c: 110.0 for c in CODIGOS},
        2022: {c: 121.0 for c in CODIGOS},
    })
    pesos = _serie_pesos({
        2020: {c: 100.0 for c in CODIGOS},
        2021: {c: (200.0 if c == "CP0111" else 50.0) for c in CODIGOS},
        2022: {c: (10.0 if c == "CP0112" else 300.0) for c in CODIGOS},
    })
    r = indices_comparados(idx, pesos).set_index("ano")
    assert r.loc[2022, "laspeyres_fixo"] == pytest.approx(121.0)
    assert r.loc[2022, "tornqvist"] == pytest.approx(121.0)
    assert r["vies"].abs().max() == pytest.approx(0.0, abs=1e-9)


def test_cabaz_fixo_sobrestima_quando_o_peso_migra_para_o_barato():
    """Substituicao a serio: o preco de uma classe dispara e o seu ponderador
    cai. O cabaz fixo, que mantem o peso antigo, tem de dar mais alto."""
    from src.calculos import indices_comparados

    caro, barato = "CP0111", "CP0112"
    idx = _serie_classes({
        2020: {c: 100.0 for c in CODIGOS},
        2021: {c: (200.0 if c == caro else 100.0) for c in CODIGOS},
        2022: {c: (300.0 if c == caro else 100.0) for c in CODIGOS},
    })
    pesos = _serie_pesos({
        2020: {c: (500.0 if c == caro else 10.0) for c in CODIGOS},
        2021: {c: (500.0 if c == caro else 10.0) for c in CODIGOS},
        2022: {c: (10.0 if c == caro else 500.0) for c in CODIGOS},
        2023: {c: (10.0 if c == caro else 500.0) for c in CODIGOS},
    })
    r = indices_comparados(idx, pesos).set_index("ano")
    assert r.loc[2022, "laspeyres_fixo"] > r.loc[2022, "tornqvist"]
    assert r.loc[2022, "vies"] > 0
    assert r.loc[2020, "laspeyres_fixo"] == pytest.approx(100.0)
    assert r.loc[2020, "tornqvist"] == pytest.approx(100.0)


def test_indices_nao_misturam_bases_do_indice():
    """Duas unidades na mesma serie: usar as duas produziria racios sem sentido.
    So uma pode sobreviver ao filtro."""
    from src.calculos import _dezembros

    a = _serie_classes({2020: {c: 100.0 for c in CODIGOS},
                        2021: {c: 110.0 for c in CODIGOS}}, unit="I15")
    b = _serie_classes({2020: {c: 80.0 for c in CODIGOS},
                        2021: {c: 88.0 for c in CODIGOS}}, unit="I05")
    dez = _dezembros(pd.concat([a, b], ignore_index=True))
    assert dez.loc[2020, "CP0111"] == pytest.approx(100.0)   # ficou o I15


def test_os_dois_indices_datam_o_dezembro_base_pelo_mesmo_ponderador():
    """O ponderador do ano y refere-se a **dezembro de y-1** (Documento
    Metodologico do IPC). O Tornqvist ja respeitava isso; o Laspeyres de base
    fixa usava `quotas.loc[base]`, um ano ao lado. O mesmo dezembro ficava
    representado por dois vetores diferentes nos dois indices cuja diferenca e
    o que o painel mede (auditoria E4)."""
    from src.calculos import indices_comparados

    caro, barato = "CP0111", "CP0112"
    idx = _serie_classes({
        2020: {c: 100.0 for c in CODIGOS},
        2021: {c: (150.0 if c == caro else 100.0) for c in CODIGOS},
        2022: {c: (200.0 if c == caro else 100.0) for c in CODIGOS},
    })
    # O ponderador de 2020 (dezembro de 2019) e muito diferente do de 2021
    # (dezembro de 2020, o verdadeiro momento-base). Se o Laspeyres usasse o
    # errado, o indice divergiria.
    pesos = _serie_pesos({
        2020: {c: (900.0 if c == caro else 10.0) for c in CODIGOS},
        2021: {c: (10.0 if c == caro else 900.0) for c in CODIGOS},
        2022: {c: (10.0 if c == caro else 900.0) for c in CODIGOS},
        2023: {c: (10.0 if c == caro else 900.0) for c in CODIGOS},
    })
    r = indices_comparados(idx, pesos).set_index("ano")

    # Com o ponderador certo — o de 2021, quase todo no «barato», que nao sobe —
    # o cabaz fixo fica proximo do Tornqvist.
    assert r.loc[2022, "laspeyres_fixo"] == pytest.approx(r.loc[2022, "tornqvist"], abs=1.0)

    # E a via errada tem de **divergir**, senao este teste nao testa nada:
    # com o ponderador de 2020 o cabaz fixo seguiria o «caro» e dispararia.
    from src.calculos import _dezembros
    dez = _dezembros(idx)
    w = pesos.copy()
    w["ano"] = w["time"].astype(str).str[:4].astype(int)
    w = w.pivot_table(index="ano", columns="coicop", values="valor", aggfunc="last")
    quotas = w.div(w.sum(axis=1), axis=0)
    errado = float((quotas.loc[2020] * (dez.loc[2022] / dez.loc[2020])).sum()) * 100
    assert errado > r.loc[2022, "laspeyres_fixo"] + 40


def test_ano_base_do_vies_e_fixo_e_nao_desliza_com_a_janela():
    """Era o primeiro ano da janela pedida ao Eurostat, que e `ano - 6`: a 1 de
    janeiro o ano-base deslizava sozinho e a metrica «vies acumulado desde
    dez/20» passava a medir outro periodo com o mesmo nome (auditoria E14)."""
    from src.calculos import indices_comparados
    from src.config import ANO_BASE_VIES

    anos = [ANO_BASE_VIES - 1, ANO_BASE_VIES, ANO_BASE_VIES + 1, ANO_BASE_VIES + 2]
    idx = _serie_classes({a: {c: 100.0 + 10 * i for c in CODIGOS}
                          for i, a in enumerate(anos)})
    pesos = _serie_pesos({a: {c: 100.0 for c in CODIGOS} for a in anos + [anos[-1] + 1]})

    r = indices_comparados(idx, pesos)
    # A janela comeca um ano antes, mas a base tem de ser a fixada.
    assert r.attrs["ano_base"] == ANO_BASE_VIES
    assert int(r["ano"].iloc[0]) == ANO_BASE_VIES
    assert r["laspeyres_fixo"].iloc[0] == pytest.approx(100.0)
    # E o ano anterior fica de fora, senao a base teria deslizado.
    assert (ANO_BASE_VIES - 1) not in list(r["ano"])


def test_ano_base_indisponivel_recua_e_declara():
    from src.calculos import indices_comparados
    from src.config import ANO_BASE_VIES

    anos = [ANO_BASE_VIES + 3, ANO_BASE_VIES + 4, ANO_BASE_VIES + 5]
    idx = _serie_classes({a: {c: 100.0 + 10 * i for c in CODIGOS}
                          for i, a in enumerate(anos)})
    pesos = _serie_pesos({a: {c: 100.0 for c in CODIGOS} for a in anos + [anos[-1] + 1]})

    r = indices_comparados(idx, pesos)
    assert r.attrs["ano_base"] == anos[0]                # recuou
    assert r.attrs["ano_base_pedido"] == ANO_BASE_VIES   # e diz qual pedia
    assert r.attrs["ano_base"] != r.attrs["ano_base_pedido"]


def test_indices_comparados_sem_dados_devolve_vazio():
    from src.calculos import indices_comparados

    assert indices_comparados(pd.DataFrame(), pd.DataFrame()).empty
    idx = _serie_classes({2020: {c: 100.0 for c in CODIGOS}})
    pesos = _serie_pesos({2020: {c: 100.0 for c in CODIGOS}})
    assert indices_comparados(idx, pesos).empty          # um so ano: nao ha elo


# ------------------------------------------- escalas de equivalencia (teste)
def test_escala_modificada_subestima_alimentacao_e_sobrestima_o_total():
    """O sinal tem de inverter-se entre alimentacao e despesa total. E esse
    contraste que mostra que o problema e da alimentacao, nao da escala."""
    from src.calculos import testar_escalas

    df = testar_escalas().set_index("escala")
    assert df.loc["ocde_modificada", "desvio_alimentar"] > 0
    assert df.loc["ocde_modificada", "desvio_total"] < 0


def test_escala_ordem_dos_racios_previstos():
    """Coeficientes maiores tem de prever racios maiores, sem excecao."""
    from src.calculos import testar_escalas

    df = testar_escalas().set_index("escala")
    assert (df.loc["per_capita", "previsto"]
            > df.loc["ocde_original", "previsto"]
            > df.loc["ocde_modificada", "previsto"])


def test_escala_mais_proxima_e_a_ocde_original():
    from src.calculos import escala_mais_proxima, testar_escalas

    assert escala_mais_proxima() == "ocde_original"
    df = testar_escalas().set_index("escala")
    # e tem de o ser por margem folgada face a norma da UE
    assert (df.loc["ocde_original", "erro_absoluto"]
            < df.loc["ocde_modificada", "erro_absoluto"])


def test_escala_desvio_bate_com_o_apuramento_documentado():
    """O levantamento regista ~+10 % de subestimacao na alimentacao (2.13)."""
    from src.calculos import testar_escalas

    df = testar_escalas().set_index("escala")
    assert df.loc["ocde_modificada", "desvio_alimentar"] == pytest.approx(10.3, abs=0.3)


# ------------------------------------- preservacao de dimensoes (eurostat)
def test_jsonstat_preserva_a_dimensao_extra():
    """Sem `extra`, tres niveis de pobreza colapsariam numa serie so, sem forma
    de os distinguir. E um erro silencioso — por isso tem teste."""
    from src.eurostat import _descodifica_jsonstat

    js = {
        "id": ["rskpovth", "geo", "time"],
        "size": [2, 1, 2],
        "dimension": {
            "rskpovth": {"category": {"index": {"TOTAL": 0, "B_60": 1}}},
            "geo": {"category": {"index": {"PT": 0}}},
            "time": {"category": {"index": {"2024": 0, "2025": 1}}},
        },
        # ordem row-major: (TOTAL,2024) (TOTAL,2025) (B_60,2024) (B_60,2025)
        "value": [2.5, 1.9, 5.1, 5.5],
    }
    df = _descodifica_jsonstat(js, extra="rskpovth")
    assert "rskpovth" in df.columns
    p = df.pivot_table(index="time", columns="rskpovth", values="valor")
    assert p.loc["2025", "TOTAL"] == pytest.approx(1.9)
    assert p.loc["2025", "B_60"] == pytest.approx(5.5)
    assert p.loc["2024", "B_60"] == pytest.approx(5.1)


def test_jsonstat_sem_extra_mantem_as_colunas_de_sempre():
    from src.eurostat import COLUNAS, _descodifica_jsonstat

    js = {
        "id": ["geo", "time"],
        "size": [1, 1],
        "dimension": {
            "geo": {"category": {"index": {"PT": 0}}},
            "time": {"category": {"index": {"2025": 0}}},
        },
        "value": [1.9],
    }
    assert list(_descodifica_jsonstat(js).columns) == COLUNAS


def test_jsonstat_recusa_dimensao_extra_inexistente():
    """Melhor falhar do que devolver series empilhadas em silencio."""
    from src.eurostat import ErroEurostat, _descodifica_jsonstat

    js = {
        "id": ["geo", "time"],
        "size": [1, 1],
        "dimension": {
            "geo": {"category": {"index": {"PT": 0}}},
            "time": {"category": {"index": {"2025": 0}}},
        },
        "value": [1.9],
    }
    with pytest.raises(ErroEurostat):
        _descodifica_jsonstat(js, extra="rskpovth")


# ------------------------------------- ECOICOP versao 2 (auditoria E1 e E2)
def _js_coicop18():
    """Resposta com a dimensao de classificacao chamada `coicop18`."""
    return {
        "id": ["coicop18", "geo", "time"],
        "size": [2, 1, 2],
        "dimension": {
            "coicop18": {"category": {"index": {"CP0111": 0, "CP0112": 1}}},
            "geo": {"category": {"index": {"PT": 0}}},
            "time": {"category": {"index": {"2026-05": 0, "2026-06": 1}}},
        },
        # row-major: (CP0111,05) (CP0111,06) (CP0112,05) (CP0112,06)
        "value": [3.4, 2.5, 5.1, 4.3],
    }


def test_dimensao_coicop18_e_normalizada_para_coicop():
    """Na ECOICOP v2 a dimensao chama-se `coicop18`. Declarada, tem de chegar
    ao resto da aplicacao com o nome de sempre."""
    from src.eurostat import _descodifica_jsonstat

    df = _descodifica_jsonstat(_js_coicop18(), dim_coicop="coicop18")
    assert set(df["coicop"]) == {"CP0111", "CP0112"}
    p = df.pivot_table(index="time", columns="coicop", values="valor")
    assert p.loc["2026-06", "CP0111"] == pytest.approx(2.5)
    assert p.loc["2026-06", "CP0112"] == pytest.approx(4.3)


def test_sem_declarar_a_classificacao_as_classes_colapsam():
    """A via errada tem de **divergir**, senao este teste nao testa nada: era
    exatamente assim que a migracao falhava em silencio (auditoria E1)."""
    from src.eurostat import _descodifica_jsonstat

    df = _descodifica_jsonstat(_js_coicop18())          # sem declarar
    assert set(df["coicop"]) == {""}                    # tudo numa classe so
    assert df.groupby("coicop")["valor"].last().shape == (1,)


def test_classificacao_declarada_e_ausente_e_erro():
    """Melhor falhar do que juntar as nove classes numa."""
    from src.eurostat import ErroEurostat, _descodifica_jsonstat

    with pytest.raises(ErroEurostat):
        _descodifica_jsonstat(_js_coicop18(), dim_coicop="coicop")


def test_conjuntos_do_ihpc_sao_os_correntes_e_nao_os_arquivados():
    """Os tres conjuntos da ECOICOP v1 pararam em dezembro de 2025 e continuam
    a responder com HTTP 200 — nao podem voltar a entrar por distracao."""
    import inspect

    from src import eurostat

    assert eurostat.HICP_MENSAL == "prc_hicp_minr"
    assert eurostat.HICP_PONDERADORES == "prc_hicp_iw"

    assert eurostat.CONTAS_NACIONAIS == "nama_10_cp18"

    fonte = "".join(
        inspect.getsource(getattr(eurostat, f))
        for f in ("ponderadores", "indice_precos", "indice_classes", "variacoes",
                  "despesa_alimentar", "despesa_total_consumo",
                  "despesa_alimentar_paises")
    )
    for arquivado in ("prc_hicp_midx", "prc_hicp_manr", "prc_hicp_inw",
                      "nama_10_co3_p3"):
        assert arquivado not in fonte, f"{arquivado} foi arquivado"

    # A unidade tem de ir explicita: sem ela a resposta traz niveis e taxas
    # misturados na mesma coluna de valores.
    assert "I25" in eurostat.HICP_UNIDADES_INDICE
    assert eurostat.HICP_UNIDADE_VARIACAO == "RCH_A"
    assert "{'+'.join(unidades)}" in inspect.getsource(eurostat.indice_classes)
    assert "dim_coicop=\"coicop18\"" in fonte, "a dimensao tem de ser declarada"


def test_agregado_de_enquadramento_usa_o_codigo_da_ecoicop2():
    """`CP00` devolve HTTP 400 no conjunto corrente; o codigo passou a `TOTAL`."""
    from src.config import AGREGADOS, COD_AGREGADOS

    assert "TOTAL" in COD_AGREGADOS
    assert "CP00" not in COD_AGREGADOS
    todos = [a for a in AGREGADOS if a["cod"] == "TOTAL"]
    assert len(todos) == 1 and todos[0]["grupo"] == "enquadramento"


def test_classes_tem_designacao_oficial_da_coicop_2018():
    """As designacoes sao as do INE, nao uma traducao desta ferramenta."""
    from src.config import CLASSES, POR_CODIGO

    assert len(CLASSES) == 9
    for c in CLASSES:
        assert c["oficial"].strip(), f"{c['cod']} sem designacao oficial"
    oficiais = {c["oficial"] for c in CLASSES}
    assert len(oficiais) == 9, "designacoes oficiais repetidas"

    # Duas ancoras verificaveis no anexo do IDF 2022/2023, que sao precisamente
    # as classes cujo conteudo mudou mais entre versoes.
    assert POR_CODIGO["CP0112"]["oficial"].startswith("Animais vivos")
    assert POR_CODIGO["CP0119"]["oficial"].startswith("Alimentos pré-preparados")

    # E os rotulos da ECOICOP v1 nao podem sobreviver.
    antigos = {"Pão e cereais", "Fruta", "Legumes e hortícolas",
               "Açúcar e doces", "Outros alimentos", "Peixe e marisco"}
    assert not ({c["nome"] for c in CLASSES} & antigos)


# ------------------- composicao por taxa de IVA, ao nivel da subclasse
def _pesos_sub_sinteticos():
    """Ponderadores por subclasse com a forma dos reais, incluindo o corte a
    seis digitos que isola o azeite dentro dos oleos vegetais."""
    from src.config import IVA_SUBCLASSES

    p = {c: 1.0 for c in IVA_SUBCLASSES}
    p["CP01151"] = 5.0          # oleos vegetais
    p["CP011513"] = 4.0         # dos quais azeite -> resto 1.0 a 13 %
    return p


def test_composicao_iva_reparte_a_classe_pelas_taxas():
    from src.calculos import composicao_iva

    df = composicao_iva(_pesos_sub_sinteticos()).set_index("codigo")
    # Oleos e gorduras: azeite + manteiga + margarina + banha a 6 %, e o resto
    # dos oleos vegetais a 13 %.
    assert df.loc["CP0115", "taxa_6"] == pytest.approx(4.0 + 1.0 + 1.0 + 1.0)
    assert df.loc["CP0115", "taxa_13"] == pytest.approx(1.0)
    assert df.loc["CP0115", "indeterminado"] == pytest.approx(0.0)


def test_resto_do_pai_nunca_e_negativo():
    """Se os filhos somarem mais do que o pai — arredondamento —, o resto tem
    de ser zero e nao um peso negativo."""
    from src.calculos import composicao_iva

    p = _pesos_sub_sinteticos()
    p["CP011513"] = 9.0         # filho maior que o pai
    df = composicao_iva(p).set_index("codigo")
    assert df.loc["CP0115", "taxa_13"] == pytest.approx(0.0)


def test_parcela_indeterminada_nao_e_arbitrada():
    """As subclasses que atravessam taxas nao podem ser empurradas para uma
    delas: o valor do apuramento esta em declarar o que nao se sabe."""
    from src.calculos import composicao_iva
    from src.config import IVA_COMPONENTES

    df = composicao_iva(_pesos_sub_sinteticos()).set_index("codigo")
    for cod, componentes in IVA_COMPONENTES.items():
        mistas = sum(1 for c in componentes if c["taxa"] is None)
        if mistas:
            assert df.loc[cod, "indeterminado"] > 0, f"{cod} devia ter parcela mista"
    # Peixe tem quatro subclasses mistas (marisco): e a classe mais indeterminada.
    assert df.loc["CP0113", "indeterminado"] == pytest.approx(4.0)


def test_componentes_somam_a_classe_e_nao_repetem_pesos():
    """Um pai listado junto com os filhos contaria duas vezes. A soma dos
    componentes tem de reproduzir o ponderador publicado da classe."""
    from src.calculos import composicao_iva

    p = _pesos_sub_sinteticos()
    # Ponderador publicado de cada classe = soma dos seus componentes.
    esperado = {}
    df = composicao_iva(p).set_index("codigo")
    for cod in df.index:
        esperado[cod] = df.loc[cod, "peso"]
        assert df.loc[cod, "peso"] == pytest.approx(
            df.loc[cod, "taxa_6"] + df.loc[cod, "taxa_13"]
            + df.loc[cod, "taxa_23"] + df.loc[cod, "indeterminado"])
    assert len(esperado) == 9


def test_resumo_mede_o_erro_do_pressuposto_por_classe():
    """O ponto do apuramento e este: dizer quanto a simulacao por classe
    sobrestima a base a taxa reduzida."""
    from src.calculos import composicao_iva, resumo_composicao_iva

    r = resumo_composicao_iva(composicao_iva(_pesos_sub_sinteticos()))
    # O assumido tem de exceder o apurado — e por margem, senao o apuramento
    # nao tinha valido a pena.
    assert r["assumido_6_pct"] > r["apurado_6_max_pct"]
    assert r["apurado_6_min_pct"] <= r["apurado_6_max_pct"]
    # O maximo e o minimo diferem exatamente pela parcela indeterminada.
    assert (r["apurado_6_max_pct"] - r["apurado_6_min_pct"]) == pytest.approx(
        r["indeterminado_pct"])


def test_o_erro_da_aproximacao_muda_de_sinal_com_o_cenario():
    """Comparar so a base a taxa reduzida dava a impressao de que o simulador
    sobrestima sempre. Nao e verdade: numa isencao total **subestima**, porque
    credita a pastelaria e a charcutaria com 6 % quando suportam 23 %."""
    from src.calculos import composicao_iva, resumo_composicao_iva

    r = resumo_composicao_iva(composicao_iva(_pesos_sub_sinteticos()))

    # Direcao 1: base a taxa reduzida — o modelo assume mais do que ha.
    assert r["assumido_6_pct"] > r["apurado_6_max_pct"]

    # Direcao 2: IVA contido — o modelo fica **abaixo** do apurado.
    assert r["iva_apurado_min_pct"] > r["iva_modelo_pct"]
    assert r["iva_apurado_max_pct"] >= r["iva_apurado_min_pct"]

    # E as duas afirmacoes sao mesmo sobre grandezas diferentes: se fossem a
    # mesma, teriam o mesmo sinal.
    assert (r["assumido_6_pct"] - r["apurado_6_min_pct"]) > 0
    assert (r["iva_modelo_pct"] - r["iva_apurado_min_pct"]) < 0


def test_todas_as_nove_classes_tem_componentes_com_verba():
    from src.config import CODIGOS, IVA_COMPONENTES

    assert set(IVA_COMPONENTES) == set(CODIGOS)
    for cod, componentes in IVA_COMPONENTES.items():
        assert componentes, cod
        for c in componentes:
            assert c["certeza"] in ("certa", "predominante", "mista"), cod
            assert c["desc"].strip(), cod
            # Uma subclasse mista nao pode ter taxa, e vice-versa: sao a mesma
            # afirmacao dita duas vezes, e divergiriam em silencio.
            assert (c["taxa"] is None) == (c["certeza"] == "mista"), f"{cod} {c['peso']}"
            if c["taxa"] is not None:
                assert c["taxa"] in (6, 13, 23), cod


def test_taxa_efetiva_e_identica_a_simular_escalao_a_escalao():
    """É esta identidade que justifica o método: usar a taxa média efetiva não
    e aproximacao da simulacao por escalao — e a mesma conta. Se deixar de o
    ser, o metodo deixa de estar justificado."""
    from src.calculos import (composicao_iva, decompor, resumo_iva, simular_iva,
                              taxas_efetivas)

    pesos_sub = _pesos_sub_sinteticos()
    comp = composicao_iva(pesos_sub)
    pesos = comp.set_index("codigo")["peso"].to_dict()
    t_ef = taxas_efetivas(comp)
    despesa = 281.06

    # O referencial reconstroi os escaloes a partir do `IVA_COMPONENTES`, e nao
    # das colunas agregadas: assim continua a ser uma verificacao independente
    # do que `composicao_iva` calcula. A parcela indeterminada de cada
    # componente entra a taxa predefinida do grupo **confinada ao seu intervalo
    # legal** - e os cereais de pequeno-almoco nunca a 6 %.
    from src.config import IVA_COMPONENTES

    def _w(spec):
        if isinstance(spec, str):
            return float(pesos_sub.get(spec) or 0.0)
        pai, filhos = spec
        return max(float(pesos_sub.get(pai) or 0.0)
                   - sum(float(pesos_sub.get(f) or 0.0) for f in filhos), 0.0)

    def escaloes_da_classe(r):
        """(taxa atual, peso) de cada escalao da classe, indeterminados incluidos."""
        fora = [(6, float(r["taxa_6"])), (13, float(r["taxa_13"])),
                (23, float(r["taxa_23"]))]
        for c in IVA_COMPONENTES[r["codigo"]]:
            if c["taxa"] is not None:
                continue
            w = _w(c["peso"])
            if w <= 0:
                continue
            lo, hi = c.get("entre", (6, 23))
            fora.append((min(max(int(r["iva_defeito"]), lo), hi), w))
        return fora

    def por_escalao(cenario, rho):
        tot = {"mecanico": 0.0, "efetivo": 0.0, "iva_antes": 0.0, "iva_depois": 0.0}
        total = comp["peso"].sum()
        for _, r in comp.iterrows():
            valor = despesa * r["peso"] / total
            t1 = cenario[r["codigo"]]
            for t0, w in escaloes_da_classe(r):
                if w <= 0:
                    continue
                v = valor * w / r["peso"]
                base = v / (1 + t0 / 100)
                mec = base * (1 + t1 / 100) - v
                tot["mecanico"] += mec
                tot["efetivo"] += rho * mec
                tot["iva_antes"] += v - base
                tot["iva_depois"] += (v + rho * mec) * (t1 / 100) / (1 + t1 / 100)
        return tot

    cenarios = [
        ({c: 0.0 for c in CODIGOS}, 1.0),                    # isencao total
        ({c: 0.0 for c in CODIGOS}, 0.4),                    # isencao parcial
        ({c: 13.0 for c in CODIGOS}, 0.4),                   # subida
        ({c: (0.0 if i % 2 else 23.0) for i, c in enumerate(CODIGOS)}, 0.7),
    ]
    for cenario, rho in cenarios:
        esc = por_escalao(cenario, rho)
        res = resumo_iva(simular_iva(decompor(despesa, pesos, {}), t_ef, cenario, rho),
                         despesa, 12, 1)
        for campo in ("mecanico", "efetivo", "iva_antes", "iva_depois"):
            assert res[campo] == pytest.approx(esc[campo], abs=1e-9), campo


def test_taxa_efetiva_excede_a_predefinida_onde_ha_produtos_a_23():
    """Nos grupos predefinidos a 6 % que contem produtos a 23 %, a taxa efetiva
    tem de ser maior — e e essa diferenca que corrige a subestimacao."""
    from src.calculos import composicao_iva, taxas_efetivas
    from src.config import POR_CODIGO

    comp = composicao_iva(_pesos_sub_sinteticos()).set_index("codigo")
    t_ef = taxas_efetivas(comp.reset_index())
    for cod, r in comp.iterrows():
        defeito = POR_CODIGO[cod]["iva"]
        if defeito == 6 and r["taxa_23"] > 0:
            assert t_ef[cod] > 6.0, cod
        if r["taxa_6"] == 0 and r["taxa_13"] == 0 and r["indeterminado"] == 0:
            assert t_ef[cod] == pytest.approx(23.0), cod


def test_destino_do_indeterminado_da_os_extremos():
    """A parcela nao repartivel tem de produzir um intervalo, nao um ponto."""
    from src.calculos import composicao_iva, taxas_efetivas

    comp = composicao_iva(_pesos_sub_sinteticos())
    baixo = taxas_efetivas(comp, indeterminado="reduzida")
    alto = taxas_efetivas(comp, indeterminado="normal")
    central = taxas_efetivas(comp)
    com_indet = [r["codigo"] for _, r in comp.iterrows() if r["indeterminado"] > 0]
    assert com_indet, "o cenario de teste devia ter parcelas indeterminadas"
    for cod in com_indet:
        assert baixo[cod] < alto[cod], cod
        assert min(baixo[cod], alto[cod]) <= central[cod] <= max(baixo[cod], alto[cod])


# ------------------------- rigor de apresentacao (auditoria E8, E9, E13)
def test_formatadores_aplicam_se_ao_numero_e_nao_a_frase():
    """As f-strings adjacentes concatenam em tempo de compilacao: um
    `.replace(".", ",")` no fim apanha a frase inteira. O C5 fechou nove
    ocorrencias e uma sobreviveu (auditoria E8)."""
    from src.config import numero, percentagem

    sev_pobres, sev = 5.5, 1.9
    etiqueta = (f"Em 2025, **{percentagem(sev_pobres, sinal=False)}** entre quem está em "
                f"risco de pobreza, contra **{percentagem(sev, sinal=False)}** no total — "
                f"**{numero(sev_pobres / sev, 1)}×** mais.")
    assert "5,5%" in etiqueta and "1,9%" in etiqueta and "2,9×" in etiqueta
    # O texto a volta fica intacto: nenhum ponto virou virgula onde nao devia.
    assert "Em 2025," in etiqueta
    assert etiqueta.endswith("mais.")

    # E a via antiga tem de estragar mesmo, senao o teste nao prova nada.
    antiga = (f"Em 2025, risco n.º 1 — **{sev_pobres / sev:.1f}×**".replace(".", ","))
    assert "n,º" in antiga


def test_pontos_de_rutura_das_escalas_sao_calculados():
    """Estavam inscritos a mao — «3,58» e «4,5» — ao lado de numeros calculados
    em direto, sem que o leitor os distinguisse (auditoria E9)."""
    from src.calculos import pontos_de_rutura_das_escalas

    r = pontos_de_rutura_das_escalas()
    # Reproduzem os valores que estavam fixos na interface.
    assert r["ultrapassagem"] == pytest.approx(3.58, abs=0.01)
    assert r["anulacao"] == pytest.approx(4.53, abs=0.02)
    # E a ordem tem sentido: a modificada passa a frente antes de se anular.
    assert r["ultrapassagem"] < r["anulacao"]


def test_pontos_de_rutura_devolvem_none_quando_nao_ha_mudanca_de_sinal():
    from src.calculos import pontos_de_rutura_das_escalas

    r = pontos_de_rutura_das_escalas(limites=(2.0, 2.5))
    assert r["anulacao"] is None


def test_ranking_vazio_nao_levanta_keyerror():
    """`pd.DataFrame([])` nao tem coluna `geo`, e o `.map` seguinte rebentava
    com um erro tecnico onde devia estar uma explicacao (auditoria E13)."""
    from src.config import PAISES

    bench = {"PT": {"2026-05": 3.1}}
    ultimo = "2026-06"                       # nenhum pais tem observacao aqui
    ranking = pd.DataFrame(
        [{"geo": g, "valor": v[ultimo]} for g, v in bench.items()
         if v.get(ultimo) is not None],
        columns=["geo", "valor"])
    ranking["pais"] = ranking["geo"].map(PAISES)       # nao pode levantar
    assert ranking.dropna(subset=["pais"]).empty


# --------------------------- cobertura declarada (auditoria E10 e E11)
def test_decompor_declara_as_classes_sem_ponderador():
    """Faltando um ponderador, as outras oito absorvem 100 % da despesa e cada
    quota sai inflacionada. O erro e silencioso — por isso tem de ser
    declarado (auditoria E10)."""
    from src.calculos import decompor

    pesos = {c: 100.0 for c in CODIGOS}
    pesos.pop("CP0115")                       # uma classe sem ponderador
    df = decompor(400.0, pesos, {c: 2.0 for c in CODIGOS})

    assert df.attrs["classes_sem_ponderador"] == ["CP0115"]
    # E a consequencia tem de ser real, senao nao valia a pena declarar:
    # as oito restantes ficam com 1/8 em vez de 1/9.
    assert df["quota"].sum() == pytest.approx(1.0)
    assert df.set_index("codigo").loc["CP0111", "quota"] == pytest.approx(1 / 8)


def test_decompor_declara_as_classes_sem_variacao():
    from src.calculos import decompor

    variacoes = {c: 2.0 for c in CODIGOS}
    del variacoes["CP0113"]
    df = decompor(400.0, {c: 100.0 for c in CODIGOS}, variacoes)

    assert df.attrs["classes_sem_variacao"] == ["CP0113"]
    assert df.attrs["classes_sem_ponderador"] == []      # quotas intactas
    assert df["quota"].sum() == pytest.approx(1.0)


def test_quintis_declaram_a_cobertura_do_agravamento():
    """O agravamento soma so as classes com variacao; o orcamento e sempre o
    total. Sem declarar a cobertura, a coluna que fecha o argumento sobre a
    regressividade subestima em silencio (auditoria E11)."""
    from src.calculos import cabaz_quintis
    from src.config import IDF_CLASSES_QUINTIL

    completo = cabaz_quintis({c: 3.0 for c in CODIGOS})
    # Cobertura total = 1 exato. O denominador e a soma das nove classes, e nao
    # o total publicado: os dois diferem ate 1 EUR/ano por arredondamento do
    # quadro do INE, e isso nao e falta de cobertura.
    assert completo.attrs["cobertura_minima"] == pytest.approx(1.0, abs=1e-9)
    assert completo.attrs["classes_sem_variacao"] == []

    parcial = cabaz_quintis({c: 3.0 for c in CODIGOS if c != "CP0112"})
    assert parcial.attrs["classes_sem_variacao"] == ["CP0112"]
    soma_nove = sum(IDF_CLASSES_QUINTIL[c]["total"] for c in CODIGOS)
    esperado = 1 - IDF_CLASSES_QUINTIL["CP0112"]["total"] / soma_nove
    cob_total = parcial.set_index("quintil").loc["total", "cobertura"]
    assert cob_total == pytest.approx(esperado, abs=1e-9)
    assert parcial.attrs["cobertura_minima"] < 0.85      # a carne pesa muito

    # E o agravamento tem mesmo de encolher — a declaracao nao e decorativa.
    a_completo = completo.set_index("quintil").loc["total", "agravamento"]
    a_parcial = parcial.set_index("quintil").loc["total", "agravamento"]
    assert a_parcial < a_completo


# ------------------------ proveniencia dos ficheiros exportados (auditoria E6)
def _csv_com_fonte(*a, **k):
    """Importa a funcao do app sem disparar a recolha de dados do Streamlit."""
    import importlib.util
    import pathlib
    import sys

    raiz = pathlib.Path(__file__).resolve().parent.parent
    fonte = (raiz / "app.py").read_text(encoding="utf-8")
    # A funcao e autonoma: extrai-se o bloco e executa-se isolado, para o teste
    # nao depender do Streamlit nem da rede.
    inicio = fonte.index("FONTE_EUROSTAT =")
    fim = fonte.index("def cartao_classe")
    espaco = {"pd": pd, "datetime": __import__("datetime").datetime}
    exec(compile(fonte[inicio:fim], "app.py", "exec"), espaco)
    return espaco["csv_com_fonte"](*a, **k)


def test_csv_do_observatorio_nao_se_declara_eurostat():
    """O cabecalho era fixo e dizia «Fonte dos dados: Eurostat» em todos os
    ficheiros — incluindo o do Observatorio do GPP, que nunca passou pelo
    Eurostat. Sao ficheiros que circulam sozinhos (auditoria E6)."""
    df = pd.DataFrame({"produto": ["Pescada"], "preco": [5.4]})
    dados = {"enderecos": [("prc_hicp_minr", "https://x", "SDMX 2.1")]}

    bruto = _csv_com_fonte(df, "Observatorio", dados,
                           fonte="GPP - Gabinete de Planeamento", conjuntos=[]).decode("utf-8-sig")
    assert "Fonte dos dados: GPP - Gabinete de Planeamento" in bruto
    assert "Eurostat" not in bruto.split("\n")[2]


def test_csv_declara_os_conjuntos_que_responderam_e_nao_uma_lista_fixa():
    df = pd.DataFrame({"a": [1]})
    dados = {"enderecos": [("prc_hicp_minr", "https://x", "SDMX 2.1"),
                           ("nama_10_cp18", "https://y", "SDMX 2.1"),
                           ("prc_hicp_minr", "https://z", "SDMX 2.1")]}
    bruto = _csv_com_fonte(df, "Teste", dados).decode("utf-8-sig")
    linha = [l for l in bruto.split("\n") if l.startswith("# Conjuntos")][0]
    assert "prc_hicp_minr" in linha and "nama_10_cp18" in linha
    assert linha.count("prc_hicp_minr") == 1            # sem repeticoes
    # E os conjuntos arquivados nao podem reaparecer por lista fixa.
    assert "prc_hicp_midx" not in bruto
    assert "nama_10_co3_p3" not in bruto


# --------------------------- rastreabilidade dos enderecos (auditoria E5)
def test_tentativa_falhada_nao_entra_na_lista_de_verificacao():
    """O painel «enderecos exatos desta sessao» promete que servem para
    verificar qualquer valor. Registar a **tentativa** em vez do resultado
    fazia com que oferecesse ligacoes que devolviam HTTP 400 (auditoria E5)."""
    import pandas as pd

    from src import eurostat

    def _sdmx_falha(*a, **k):
        raise eurostat.ErroEurostat("400 Client Error")

    def _stats_ok(*a, **k):
        return pd.DataFrame({"unit": [""], "coicop": [""], "geo": ["PT"],
                             "time": ["2026"], "valor": [1.0]}), "https://exemplo/stats?x=1"

    originais = (eurostat._via_sdmx, eurostat._via_stats, list(eurostat.ENDERECOS))
    try:
        eurostat._via_sdmx, eurostat._via_stats = _sdmx_falha, _stats_ok
        eurostat.ENDERECOS.clear()
        # Conjunto real, com chave e filtros validos: desde a guarda estrutural
        # do K4, um pedido malformado falha antes de chegar as vias, e este
        # teste e sobre o registo do endereco, nao sobre a estrutura.
        eurostat.obter("ilc_lvph01", "A.AVG.PT",
                       {"freq": "A", "unit": "AVG", "geo": "PT"})
        registados = list(eurostat.ENDERECOS)
    finally:
        eurostat._via_sdmx, eurostat._via_stats = originais[0], originais[1]
        eurostat.ENDERECOS[:] = originais[2]

    assert len(registados) == 1
    conjunto, url, via = registados[0]
    assert conjunto == "ilc_lvph01"
    assert via == "API Statistics"          # a via que produziu o numero
    assert url == "https://exemplo/stats?x=1"
    assert "sdmx" not in url.lower()        # a tentativa falhada nao entra


# ------------------------------- frescura das series com API (auditoria E3)
def test_fim_do_periodo_reconhece_as_codificacoes_do_eurostat():
    from datetime import date

    from src.calculos import fim_do_periodo

    assert fim_do_periodo("2026") == date(2026, 12, 31)
    assert fim_do_periodo("2026-06") == date(2026, 6, 30)
    assert fim_do_periodo("2026M06") == date(2026, 6, 30)
    assert fim_do_periodo("2026-02") == date(2026, 2, 28)      # ano comum
    assert fim_do_periodo("2024-02") == date(2024, 2, 29)      # bissexto
    assert fim_do_periodo("2026-S1") == date(2026, 6, 30)
    assert fim_do_periodo("2026-S2") == date(2026, 12, 31)
    assert fim_do_periodo("2026-Q2") == date(2026, 6, 30)
    # Ilegivel devolve None — quem chama trata como «nao sei», nunca como velho.
    for lixo in ("", None, "trimestre", "2026-13", "26-06"):
        assert fim_do_periodo(lixo) is None


def test_serie_arquivada_e_apanhada_e_serie_lenta_nao_e():
    """O E1 passou sete meses despercebido porque a serie respondia. O prazo tem
    de ser o desfasamento **normal** de cada serie: um prazo uniforme acusaria
    as Contas Nacionais, que tem dois anos de atraso por construcao."""
    from datetime import date

    from src.calculos import frescura_das_series

    from src.config import LIMITES_FRESCURA

    hoje = date(2026, 8, 11)
    lim_mes = LIMITES_FRESCURA["indice"][0]
    lim_cn = LIMITES_FRESCURA["contas_nacionais"][0]
    series = [
        # 1. o caso real: indice mensal parado em dezembro de 2025
        {"serie": "Índice de preços", "periodo": "2025-12", "limite_dias": lim_mes,
         "cadencia": "mensal", "conjunto": "prc_hicp_midx"},
        # 2. o mesmo indice, ja migrado
        {"serie": "Índice de preços", "periodo": "2026-06", "limite_dias": lim_mes,
         "cadencia": "mensal", "conjunto": "prc_hicp_minr"},
        # 3. a segunda ocorrencia, apanhada por esta verificacao (E16)
        {"serie": "Contas Nacionais", "periodo": "2022", "limite_dias": lim_cn,
         "cadencia": "anual", "conjunto": "nama_10_co3_p3"},
        # 4. o conjunto que a substituiu — lento, mas a avancar
        {"serie": "Contas Nacionais", "periodo": "2024", "limite_dias": lim_cn,
         "cadencia": "anual", "conjunto": "nama_10_cp18"},
    ]
    df = frescura_das_series(series, hoje=hoje)
    assert list(df["desatualizada"]) == [True, False, True, False]
    # E a idade tem de ser medida, nao adivinhada: 2025-12 fecha a 31/12/2025.
    assert df.loc[0, "dias"] == 223
    assert df.loc[0, "conjunto"] == "prc_hicp_midx"


def test_periodo_ilegivel_nao_acusa_nem_confirma():
    from datetime import date

    from src.calculos import frescura_das_series

    df = frescura_das_series(
        [{"serie": "X", "periodo": "sei lá", "limite_dias": 60}],
        hoje=date(2026, 8, 11))
    assert not bool(df.loc[0, "desatualizada"])
    assert not bool(df.loc[0, "verificada"])


def test_prazos_de_frescura_cobrem_as_series_vigiadas():
    """Cada prazo tem de vir com a razao escrita ao lado — sem isso ninguem
    sabe se um valor foi pensado ou copiado."""
    from src.config import LIMITES_FRESCURA

    for chave, (dias, porque) in LIMITES_FRESCURA.items():
        assert isinstance(dias, int) and dias > 0, chave
        assert len(porque) > 30, f"{chave} sem justificação"
    # As duas mensais sao as que falharam: tem de ser as mais apertadas.
    mensais = {LIMITES_FRESCURA["indice"][0], LIMITES_FRESCURA["variacoes"][0]}
    assert max(mensais) < min(v[0] for k, v in LIMITES_FRESCURA.items()
                              if k not in ("indice", "variacoes"))


# --------------------------------------------- Observatorio de Precos (GPP)
def _obs_df(registos):
    """registos: (produto, fase, 'YYYY-MM-DD', preco)"""
    return pd.DataFrame([
        {"setor": "teste", "produto": p, "produto_id": 1, "serie_id": 1,
         "fase": f, "unidade": "EUR/kg", "periodo": 1,
         "inicio": pd.Timestamp(d), "preco": v}
        for p, f, d, v in registos
    ])


def test_observatorio_restringe_ao_periodo_comum():
    """A serie de producao acaba antes da de consumo. Se cada fase fosse medida
    no seu proprio intervalo, as variacoes nao seriam comparaveis."""
    from src.observatorio import variacoes

    df = _obs_df([
        ("X", "consumo",  "2022-01-01", 1.00),
        ("X", "consumo",  "2023-01-01", 1.50),
        ("X", "consumo",  "2024-01-01", 3.00),   # produção já não cobre este
        ("X", "producao", "2022-01-01", 0.50),
        ("X", "producao", "2023-01-01", 1.00),
    ])
    r = variacoes(df).iloc[0]
    assert r["n_periodos"] == 2
    assert r["fim"] == pd.Timestamp("2023-01-01")
    assert r["consumo_var"] == pytest.approx(50.0)    # 1,00 -> 1,50, nao 200 %
    assert r["producao_var"] == pytest.approx(100.0)


def test_observatorio_diferenca_nao_e_soma_das_variacoes():
    """A variacao da diferenca calcula-se sobre a diferenca, nao por subtracao
    das duas variacoes."""
    from src.observatorio import variacoes

    df = _obs_df([
        ("X", "consumo",  "2022-01-01", 2.00),
        ("X", "consumo",  "2023-01-01", 3.00),
        ("X", "producao", "2022-01-01", 1.00),
        ("X", "producao", "2023-01-01", 1.20),
    ])
    r = variacoes(df).iloc[0]
    # diferenca: 1,00 -> 1,80  =>  +80 %
    assert r["diferenca_var"] == pytest.approx(80.0)


def test_observatorio_classifica_divergencia():
    """Producao a cair e consumo a subir e o padrao que importa isolar."""
    from src.observatorio import variacoes

    df = _obs_df([
        ("X", "consumo",  "2022-01-01", 1.00),
        ("X", "consumo",  "2023-01-01", 1.30),
        ("X", "producao", "2022-01-01", 1.00),
        ("X", "producao", "2023-01-01", 0.80),
    ])
    assert variacoes(df).iloc[0]["padrao"] == "Divergência"


def test_observatorio_produto_sem_producao_nao_inventa_comparacao():
    from src.observatorio import variacoes

    df = _obs_df([
        ("X", "consumo", "2022-01-01", 1.00),
        ("X", "consumo", "2023-01-01", 1.40),
    ])
    r = variacoes(df).iloc[0]
    assert bool(r["tem_producao"]) is False
    assert r["padrao"] == "Sem série de produção"
    assert r["consumo_var"] == pytest.approx(40.0)
    assert pd.isna(r.get("producao_var", float("nan")))


def test_observatorio_sem_dados_devolve_vazio():
    from src.observatorio import variacoes

    assert variacoes(pd.DataFrame()).empty


# ------------------------------------------- repercussao calibrada (BdP, 2023)
def test_efeito_mecanico_reproduz_o_publicado_pelo_banco_de_portugal():
    """
    O BdP publica -18,7 % como efeito mecanico da isencao dos oleos alimentares,
    que estavam a 23 % (WAPP de 22.11.2023, p. 5). Se a nossa aritmetica de
    imposto nao reproduzir esse numero, a derivacao da repercussao nao vale nada.
    """
    from src.calculos import efeito_mecanico_pct

    assert efeito_mecanico_pct(23, 0) == pytest.approx(-18.70, abs=0.005)
    assert efeito_mecanico_pct(6, 0) == pytest.approx(-5.66, abs=0.005)
    # E o sentido inverso: repor 6 % sobre um bem isento encarece 6 %.
    assert efeito_mecanico_pct(0, 6) == pytest.approx(6.0)


def test_repercussao_derivada_e_nao_citada():
    """
    Nenhum rho da tabela e citado do BdP: todos sao o quociente entre a variacao
    observada e a mecanica, ambas publicadas. Este teste fixa essa derivacao.
    """
    from src.calculos import estimativas_repercussao

    df = estimativas_repercussao()
    assert len(df) == 4
    for _, r in df.iterrows():
        assert r["rho"] == pytest.approx(r["observado"] / r["mecanico"])
    esperado = [4.0 / 4.2, 3.5 / 4.2, 6.0 / 5.66, 24.5 / 18.70]
    assert list(df["rho"]) == pytest.approx(esperado)


def test_repercussao_padrao_tem_suporte_numa_estimativa_portuguesa():
    """
    O valor por defeito nao pode voltar a ser um numero de trabalho sem fonte.
    Tem de coincidir com uma das estimativas de diferenca-nas-diferencas, que
    sao as que tem contrafactual estatisticamente validado.
    """
    from src.calculos import estimativas_repercussao, repercussao_banda

    lo, central, hi = repercussao_banda()
    did = [r["rho"] for _, r in estimativas_repercussao().iterrows()
           if "diferenca" in r["estimativa"].lower()
           or "diferença" in r["estimativa"].lower()]
    assert len(did) == 2
    assert central == pytest.approx(max(did), abs=0.005)
    assert lo == pytest.approx(min(did), abs=0.005)
    assert lo < central <= hi <= 1.0


def test_a_repercussao_antiga_esta_fora_da_banda_com_suporte():
    """
    Os 40 % que vigoraram ate 12.08.2026 nao eram conservadores: nenhuma
    estimativa portuguesa sobre a medida identica os sustenta. Guarda contra o
    valor antigo regressar por descuido.
    """
    from src.calculos import repercussao_banda

    lo, central, _ = repercussao_banda()
    assert 0.40 < lo
    assert central / 0.40 == pytest.approx(2.38, abs=0.01)


def test_distribuicao_do_iva_zero_e_menos_focalizada_que_as_alternativas():
    """
    A conclusao que a aplicacao passa a mostrar: a reducao do IVA entrega mais
    aos 20 % mais ricos do que aos 20 % mais pobres, e e a menos focalizada das
    quatro medidas de 2023 avaliadas pelo BdP.
    """
    from src.config import IVA_ZERO_AFETACAO_ORCAMENTAL

    por_medida = {m: (pobres, ricos)
                  for m, pobres, ricos in IVA_ZERO_AFETACAO_ORCAMENTAL}
    pobres, ricos = por_medida["Redução do IVA"]
    assert ricos > pobres
    outras = [p for m, p, _ in IVA_ZERO_AFETACAO_ORCAMENTAL if m != "Redução do IVA"]
    assert all(p > pobres for p in outras)


# ------------------------------- banda das parcelas atribuidas por predominancia
def _comp_sintetica():
    """
    Uma classe de 100: 50 de leitura inequivoca a 6 %, 40 atribuidos por
    predominancia (20 a 6 % e 20 a 23 %) e 10 indeterminados. A predominancia
    esta repartida de proposito - se estivesse toda numa taxa, um dos extremos
    coincidiria com o valor central e o teste nao provava nada.
    """
    return pd.DataFrame([{
        "codigo": "CP0111", "classe": "Teste", "emoji": "🍞", "iva_defeito": 6,
        "peso": 100.0, "peso_publicado": 100.0,
        "taxa_6": 70.0, "taxa_13": 0.0, "taxa_23": 20.0,
        "indeterminado": 10.0, "por_predominancia": 40.0,
        "certa_6": 50.0, "certa_13": 0.0, "certa_23": 0.0,
    }])


def test_predominancia_conserva_o_peso_da_classe():
    """
    Mover a parcela de predominancia entre taxas nao pode criar nem destruir
    peso: as parcelas certas mais a predominancia mais o indeterminado tem de
    dar sempre o mesmo total.
    """
    r = _comp_sintetica().iloc[0]
    certas = r["certa_6"] + r["certa_13"] + r["certa_23"]
    assert certas + r["por_predominancia"] + r["indeterminado"] == pytest.approx(r["peso"])
    assert r["taxa_6"] + r["taxa_13"] + r["taxa_23"] + r["indeterminado"] == pytest.approx(r["peso"])


def test_banda_da_predominancia_enquadra_o_valor_central():
    from src.calculos import taxas_efetivas

    comp = _comp_sintetica()
    central = taxas_efetivas(comp)["CP0111"]
    baixo = taxas_efetivas(comp, predominancia="reduzida")["CP0111"]
    alto = taxas_efetivas(comp, predominancia="normal")["CP0111"]
    assert baixo < central < alto
    # Com toda a predominancia a 6 % e o indeterminado na predefinida (6 %),
    # a classe fica inteiramente a 6 %.
    assert baixo == pytest.approx(6.0)


def test_composicao_separa_o_que_e_certo_do_que_e_juizo():
    """
    A banda so pode cobrir a predominancia se a composicao a mantiver separada
    do que resiste a qualquer leitura. Estas colunas sao o que torna isso
    possivel - sem elas a parcela de juizo fica indistinguivel da certa.
    """
    from src.calculos import composicao_iva
    from src.config import IVA_COMPONENTES

    pesos = {}
    for comps in IVA_COMPONENTES.values():
        for c in comps:
            alvo = c["peso"] if isinstance(c["peso"], str) else c["peso"][0]
            pesos[alvo] = 10.0
    df = composicao_iva(pesos)
    for col in ("certa_6", "certa_13", "certa_23", "por_predominancia"):
        assert col in df.columns
    # As certas mais a predominancia tem de reconstituir exatamente as parcelas
    # por taxa - nenhum peso se perde na separacao.
    certas = df["certa_6"] + df["certa_13"] + df["certa_23"]
    por_taxa = df["taxa_6"] + df["taxa_13"] + df["taxa_23"]
    assert (certas + df["por_predominancia"]).sum() == pytest.approx(por_taxa.sum())
    assert df["por_predominancia"].sum() > 0


def test_taxas_efetivas_sem_colunas_certas_nao_rebenta():
    """Compatibilidade: uma composicao antiga, sem as colunas novas, ainda serve."""
    from src.calculos import taxas_efetivas

    comp = _comp_sintetica().drop(columns=["certa_6", "certa_13", "certa_23"])
    assert taxas_efetivas(comp, predominancia="normal")["CP0111"] == pytest.approx(
        taxas_efetivas(comp)["CP0111"])


# ---------------------------- intervalo legal das parcelas indeterminadas (G1)
def test_intervalo_legal_declarado_e_valido():
    """`entre` so pode conter taxas que existam no Codigo do IVA, por ordem."""
    from src.config import IVA_COMPONENTES

    for cod, comps in IVA_COMPONENTES.items():
        for c in comps:
            if c["certeza"] != "mista":
                assert "entre" not in c, f"{cod} {c['peso']}: so as mistas tem intervalo"
                continue
            lo, hi = c.get("entre", (6, 23))
            assert lo in (6, 13, 23) and hi in (6, 13, 23), f"{cod} {c['peso']}"
            assert lo < hi, f"{cod} {c['peso']}"


def test_cereais_de_pequeno_almoco_nunca_ficam_a_taxa_reduzida():
    """
    A Lista I nao tem verba para cereais de pequeno-almoco; a Lista II (1.12)
    cobre os flocos simples sem acucar a 13 %. O intervalo legal e 13-23 %, e o
    valor central nao pode cair nos 6 % predefinidos do grupo dos cereais - era
    o que acontecia ate 12.08.2026.
    """
    from src.config import IVA_COMPONENTES

    cereais = {c["peso"]: c for c in IVA_COMPONENTES["CP0111"] if isinstance(c["peso"], str)}
    assert cereais["CP01114"]["entre"] == (13, 23)


def test_parcela_indeterminada_entra_pelo_intervalo_do_seu_componente():
    """
    Uma classe predefinida a 6 % com uma unica parcela indeterminada entre 13 e
    23 % tem de produzir taxa efetiva de 13 % no minimo, 23 % no maximo e 13 %
    no valor central - nunca 6 %.
    """
    from src.calculos import composicao_iva, taxas_efetivas
    from src.config import IVA_COMPONENTES

    # So a subclasse dos cereais de pequeno-almoco tem peso.
    pesos = {c["peso"]: 0.0 for c in IVA_COMPONENTES["CP0111"] if isinstance(c["peso"], str)}
    pesos["CP01114"] = 100.0
    comp = composicao_iva(pesos)
    linha = comp[comp["codigo"] == "CP0111"]
    assert float(linha["indeterminado"].iloc[0]) == pytest.approx(100.0)

    central = taxas_efetivas(comp)["CP0111"]
    baixo = taxas_efetivas(comp, indeterminado="reduzida")["CP0111"]
    alto = taxas_efetivas(comp, indeterminado="normal")["CP0111"]
    assert baixo == pytest.approx(13.0)
    assert alto == pytest.approx(23.0)
    assert central == pytest.approx(13.0)
    assert central > 6.0


def test_a_fonte_legal_esta_identificada_com_versao():
    """
    Uma citacao do Codigo do IVA sem versao nao e verificavel: as Listas mudam
    quase todos os anos.
    """
    from src.config import CIVA_FONTE

    assert "2026" in CIVA_FONTE
    assert "Lista" in CIVA_FONTE


# --------------------- conceito das Contas Nacionais, verificado a 12.08.2026
def test_fonte_da_ancora_das_contas_nao_aponta_para_conjunto_arquivado():
    """
    `nama_10_co3_p3` foi arquivado com a passagem a COICOP 2018. A citacao da
    fonte tinha ficado a apontar para ele - uma fonte parada oferecida como
    verificacao e pior do que nenhuma.
    """
    from src.config import BASES_ANCORA

    fonte = BASES_ANCORA["contas"]["fonte"]
    assert "nama_10_cp18" in fonte
    assert "co3_p3" not in fonte


def test_conceito_das_contas_esta_declarado_e_e_o_interno():
    from src.config import CONCEITO_CONTAS_NACIONAIS as C

    assert C["conceito"] == "interno"
    assert C["verificado"] == "2026-08-12"
    # A prova tem de citar os dois agregados confrontados, senao nao e prova.
    assert "nama_10_cp18" in C["prova"] and "P31_S14" in C["prova"]
    assert "2020" in C["prova"]


def test_a_ancora_das_contas_nao_atribui_a_divergencia_aos_turistas():
    """
    A explicacao antiga dizia que as Contas Nacionais sobrestimam por incluirem
    nao residentes. A verificacao de 2020 mostrou que nos alimentos em casa esse
    efeito e pequeno - CP111 caiu 36,6 % e CP011 subiu 3,1 %. Este teste impede
    o regresso da explicacao errada.

    A segunda asserçao seguia a palavra "sub-declaracao". A metainformacao
    nacional do `nama_10_cp18` (ESMS de Portugal, 18.1) tornou a explicacao mais
    precisa: o INE confrontou o inquerito com o IVA, com o volume de negocios do
    retalho e com informacao setorial, concluiu que estava subavaliado, e fixou
    o valor no equilibrio do QERU. O teste passa a exigir esse mecanismo, que e
    o que substitui a atribuicao aos turistas (20.08.2026).
    """
    from src.config import BASES_ANCORA, CONCEITO_CONTAS_NACIONAIS

    porque = BASES_ANCORA["contas"]["porque"]
    assert "não é sobretudo por causa dos não residentes" in porque
    assert "QERU" in porque and "subavaliados" in porque
    assert "Pequeno" in CONCEITO_CONTAS_NACIONAIS["efeito_nos_alimentos"]

    # O outro lado do par tem de declarar a mesma coisa pela mesma via: e o
    # compilador que conclui que o inquerito subestima, nao uma inferencia
    # nossa. Sem isto, a base por defeito da aplicacao ficava sem fundamento
    # declarado no unico sitio onde a interface o mostra.
    porque_idf = BASES_ANCORA["idf"]["porque"]
    assert "Subestima" in porque_idf
    assert "INE" in porque_idf and "subavaliados" in porque_idf


# --------------------- doutrina da AT (informacoes vinculativas), 12.08.2026
def test_fichas_da_at_estao_identificadas_e_ligadas_a_subclasses():
    """
    Uma ficha doutrinaria sem processo e data nao e verificavel, e uma que nao
    diga sobre que subclasses decide nao serve para auditar o quadro.
    """
    from src.config import AT_FICHAS, IVA_COMPONENTES, _codigos_de_componente

    assert AT_FICHAS
    todos = {c for comps in IVA_COMPONENTES.values() for comp in comps
             for c in _codigos_de_componente(comp)}
    for f in AT_FICHAS:
        assert f["processo"].strip()
        assert f["despacho"].startswith("20")
        assert f["decide"], f["processo"]
        for cod, texto in f["decide"]:
            assert cod in todos, f"{f['processo']}: {cod} nao existe no quadro"
            assert len(texto) > 40


def test_a_fonte_do_quadro_cita_o_civa_e_as_fichas():
    from src.config import IVA_COMPONENTES_FONTE

    assert "Listas I e II" in IVA_COMPONENTES_FONTE
    assert "28176" in IVA_COMPONENTES_FONTE
    assert "prc_hicp_iw" in IVA_COMPONENTES_FONTE


def test_subclasses_decididas_pela_at_citam_a_ficha():
    """
    Se a AT decidiu sobre uma subclasse, a justificacao tem de o dizer - senao a
    doutrina fica no config e nao chega a quem le a aplicacao.
    """
    from src.config import AT_FICHAS, IVA_COMPONENTES

    por_codigo = {}
    for comps in IVA_COMPONENTES.values():
        for c in comps:
            chave = c["peso"] if isinstance(c["peso"], str) else c["peso"][0]
            por_codigo[chave] = c
    for f in AT_FICHAS:
        for cod, _ in f["decide"]:
            assert f["processo"] in por_codigo[cod]["desc"], cod


def test_fruta_moida_deixou_de_ser_juizo_e_passou_a_doutrina():
    """A ficha 28176 e direta: a verba 1.6.4 exclui a moagem."""
    from src.config import IVA_COMPONENTES

    cp01169 = next(c for c in IVA_COMPONENTES["CP0116"] if c["peso"] == "CP01169")
    assert cp01169["certeza"] == "certa"
    assert cp01169["taxa"] == 23


def test_pastelaria_deixou_de_ser_juizo_e_passou_a_doutrina():
    """
    Era a maior parcela por predominancia do cabaz (7,06 %). A ficha 16563 e
    direta: a verba 1.1.5 nao abrange "quaisquer outros produtos afins do pao,
    ou de pastelaria fina".
    """
    from src.config import IVA_COMPONENTES

    cp = next(c for c in IVA_COMPONENTES["CP0111"] if c["peso"] == "CP011139")
    assert cp["certeza"] == "certa"
    assert cp["taxa"] == 23


def test_o_pao_deixou_de_ser_certo_porque_a_doutrina_o_dividiu():
    """
    Correcao no sentido contrario, e igualmente importante: a mesma ficha exclui
    da verba o pao pre-cozido congelado e a massa de pao congelada. A subclasse
    nao e homogenea, e "certa" prometia mais do que entrega.
    """
    from src.config import IVA_COMPONENTES

    cp = next(c for c in IVA_COMPONENTES["CP0111"] if c["peso"] == "CP011131")
    assert cp["certeza"] == "predominante"
    assert cp["taxa"] == 6
    assert "pré-cozido congelado" in cp["desc"]


def test_principio_da_lista_taxativa_esta_citado_literalmente():
    """
    E a justificacao doutrinaria do metodo inteiro: percorrer as Listas e
    atribuir a taxa normal a tudo o que nao esteja la de forma inequivoca.
    """
    from src.config import PRINCIPIO_LISTA_TAXATIVA, PRINCIPIO_LISTA_TAXATIVA_FONTE

    assert "taxativamente" in PRINCIPIO_LISTA_TAXATIVA
    assert "interpretação extensiva" in PRINCIPIO_LISTA_TAXATIVA
    assert "24929" in PRINCIPIO_LISTA_TAXATIVA_FONTE


def test_ha_fichas_de_mais_do_que_um_ano_e_todas_ligadas():
    """As quatro fichas cobrem anos diferentes; nenhuma pode ficar orfa."""
    from src.config import AT_FICHAS

    assert len(AT_FICHAS) >= 4
    anos = {f["despacho"][:4] for f in AT_FICHAS}
    assert len(anos) >= 3


# ------------- janela da variacao homologa acompanha a do indice (12.08.2026)
def test_variacao_de_portugal_pedida_na_mesma_janela_do_indice():
    """
    O cursor do separador Historico oferece as opcoes do **indice**, que recua
    ate ao ano-base do vies. Se a variacao for pedida numa janela mais curta, a
    linha vermelha aparece truncada sem aviso - eram 48 meses sem linha.

    Este teste le a fonte porque a ligacao entre as duas janelas e uma decisao
    de quem pede os dados, e nao ha forma de a observar sem rede.
    """
    import io
    from pathlib import Path

    fonte = io.open(Path(__file__).resolve().parent.parent / "app.py",
                    encoding="utf-8-sig").read()
    assert "var_pt_longo" in fonte
    # A serie longa de PT tem de usar a janela do indice, nao a da variacao.
    i = fonte.index("var_pt_longo, via16")
    trecho = fonte[i:i + 260]
    assert "desde_indice" in trecho, trecho
    assert "desde_variacao" not in trecho


# --------------------- linha de proveniencia dos graficos, 20.08.2026
def _proveniencia(*a, **k):
    """
    Extrai `proveniencia` do app e executa-a isolada, no mesmo molde do
    `_csv_com_fonte`: a funcao so depende dos formatadores de data do config,
    logo nao precisa do Streamlit nem da rede.
    """
    from pathlib import Path

    from src.config import mes_extenso, mes_homologo

    fonte = (Path(__file__).resolve().parent.parent / "app.py").read_text(
        encoding="utf-8")
    inicio = fonte.index("def proveniencia(")
    fim = fonte.index("\ndef ", inicio + 1)
    espaco = {"mes_extenso": mes_extenso, "mes_homologo": mes_homologo}
    exec(compile(fonte[inicio:fim], "app.py", "exec"), espaco)
    return espaco["proveniencia"](*a, **k)


def _dados_de_teste():
    return {"mes_variacoes": "2026-06", "ano_pesos": "2026"}


def test_a_proveniencia_declara_as_tres_datas():
    """
    O periodo de referencia estava a tres ecras dos numeros que o usam. A linha
    tem de trazer as tres datas que o grafico combina, e nao so a mais recente:
    a janela homologa, o ano dos ponderadores e o mes a que o nivel esta
    indexado.
    """
    base = {"nome": "IDF 2022/2023", "ano_base": "2022/2023"}
    linha = _proveniencia(_dados_de_teste(), base, mes_indice="2026-06")

    assert "junho de 2026" in linha
    assert "junho de 2025" in linha          # o outro extremo da janela
    assert "Ponderadores de 2026" in linha
    assert "IDF 2022/2023" in linha
    # O nome do IDF ja traz o periodo; repetido dava "IDF 2022/2023 (2022/2023)".
    assert "(2022/2023)" not in linha
    # O das Contas Nacionais nao traz, e ai o ano tem de aparecer.
    cn = _proveniencia(_dados_de_teste(), {"nome": "Contas Nacionais", "ano_base": 2024},
                       mes_indice="2026-06")
    assert "Contas Nacionais (2024)" in cn


def test_a_proveniencia_nao_mostra_codigos_de_conjunto():
    """
    Os codigos do Eurostat vivem no separador da metodologia, com a ligacao para
    o databrowser. No corpo fica o nome da coisa: quem usa a aplicacao nao sabe
    o que e um `prc_hicp_minr` e nao tem de saber (decisao da Ines, 20.08.2026).

    Os cabecalhos dos CSV sao a excecao deliberada, e por isso nao entram aqui:
    esses ficheiros saem da aplicacao e circulam sem o ecra ao lado.
    """
    base = {"nome": "Contas Nacionais", "ano_base": 2024}
    linha = _proveniencia(_dados_de_teste(), base, mes_indice="2026-06")

    for codigo in ("prc_hicp", "nama_10", "ilc_", "lfst_", "earn_mw", "CP011"):
        assert codigo not in linha, f"{codigo} nao pode aparecer no corpo: {linha}"
    assert "índice harmonizado de preços no consumidor" in linha


def test_a_proveniencia_acompanha_a_base_escolhida():
    """
    A ultima parte da linha muda com a base da barra lateral. E a razao de a
    frase ser produzida por uma funcao e nao escrita em cada legenda: escrita a
    mao, ficaria a dizer IDF num ecra que mostra Contas Nacionais.
    """
    dados = _dados_de_teste()
    idf = _proveniencia(dados, {"nome": "IDF 2022/2023", "ano_base": "2022/2023"},
                        mes_indice="2026-06")
    cn = _proveniencia(dados, {"nome": "Contas Nacionais", "ano_base": 2024},
                       mes_indice="2026-06")

    assert "IDF 2022/2023" in idf and "Contas Nacionais" not in idf
    assert "Contas Nacionais" in cn and "IDF" not in cn


def test_a_proveniencia_omite_a_janela_quando_nao_ha_variacao():
    """
    A composicao da despesa nao mostra variacao nenhuma. Anunciar ali uma janela
    homologa seria dizer que o grafico responde a uma pergunta que nao responde.
    """
    base = {"nome": "IDF 2022/2023", "ano_base": "2022/2023"}
    linha = _proveniencia(_dados_de_teste(), base, mes_indice="2026-06",
                          variacao=False)

    assert "face a" not in linha
    assert "junho de 2025" not in linha
    assert "a preços de junho de 2026" in linha
    assert "Ponderadores de 2026" in linha


def test_a_proveniencia_sobrevive_a_falta_de_dados():
    """Sem mes e sem ponderadores, a linha encolhe em vez de estourar."""
    linha = _proveniencia({}, None)

    assert linha.startswith("Fonte: Eurostat")
    assert "None" not in linha


def test_ha_recurso_se_a_serie_longa_falhar():
    """Se o pedido extra falhar, o grafico tem de continuar a funcionar."""
    import io
    from pathlib import Path

    fonte = io.open(Path(__file__).resolve().parent.parent / "app.py",
                    encoding="utf-8-sig").read()
    i = fonte.index("if not var_pt_longo.empty:")
    trecho = fonte[i:i + 420]
    assert "else:" in trecho
    assert "var_df[" in trecho


def test_o_grafico_avisa_quando_a_variacao_nao_cobre_o_intervalo():
    """A linha truncada tem de ser dita, nao descoberta."""
    import io
    from pathlib import Path

    fonte = io.open(Path(__file__).resolve().parent.parent / "app.py",
                    encoding="utf-8-sig").read()
    assert "len(var_sel) < len(idx_sel)" in fonte


# ==========================================================================
# Quarta auditoria — 12.08.2026
# ==========================================================================
def _fonte(nome):
    """Codigo-fonte de um ficheiro do projeto, para os testes de doutrina."""
    import io
    from pathlib import Path
    return io.open(Path(__file__).resolve().parent.parent / nome,
                   encoding="utf-8-sig").read()


def _fonte_viva(nome):
    """
    O mesmo, **sem as linhas de comentario**.

    Os comentarios deste projeto citam de proposito os valores errados que
    foram corrigidos — e um teste que proiba um numero pelo nome apanharia a
    explicacao em vez da ocorrencia. O que se proibe e o numero **no que a
    aplicacao mostra**, nao na memoria de porque deixou de la estar.
    """
    return "\n".join(l for l in _fonte(nome).splitlines()
                     if not l.lstrip().startswith("#"))


# ---- K11 · dependencias fixadas e API depreciada -------------------------
def test_nao_ha_api_depreciada_do_streamlit():
    """
    `use_container_width` tem data de remocao anunciada — «after 2025-12-31» —
    que ja passou. Enquanto la esteve, a aplicacao dependia da tolerancia da
    biblioteca e nao de uma garantia (auditoria de 12.08.2026, K11).
    """
    fonte = _fonte("app.py")
    assert "use_container_width" not in fonte, (
        "use_container_width voltou ao app.py; usar width='stretch'/'content'")
    # E a substituicao tem de ter sido feita, nao apagada. O limiar era 40
    # quando cada `st.plotly_chart` trazia o seu `width="stretch"`. O redesign
    # de 12.08.2026 encaminhou os graficos por um unico ajudante `grafico()`,
    # que aplica a linguagem visual comum e chama `st.plotly_chart` uma so vez
    # — o parametro passou a estar la, e nao em catorze sitios. O limiar
    # acompanha essa centralizacao; o que o teste guarda continua a ser o
    # mesmo: que a migracao nao foi desfeita por apagamento.
    assert fonte.count('width="stretch"') >= 25
    # E que os graficos continuam a passar todos pelo ajudante, em vez de
    # voltarem a chamar o Streamlit diretamente com a API antiga.
    assert fonte.count("st.plotly_chart(") == 1, (
        "os graficos devem ser apresentados por `grafico()`, que centraliza "
        "o estilo e a chamada a st.plotly_chart")


def test_dependencias_tem_limite_superior():
    """
    Sem limite superior, uma reinstalacao num ambiente limpo pode partir a
    aplicacao sem ninguem lhe tocar — e o Community Cloud reinstala a cada
    arranque (auditoria de 12.08.2026, K11).
    """
    linhas = [l.strip() for l in _fonte("requirements.txt").splitlines()
              if l.strip() and not l.strip().startswith("#")]
    assert linhas, "requirements.txt sem dependencias"
    for l in linhas:
        assert "<" in l, f"dependencia sem limite superior: {l!r}"
    # numpy e usado em src/calculos.py e era dependencia implicita do pandas.
    assert any(l.startswith("numpy") for l in linhas), (
        "numpy e importado em src/calculos.py e tem de estar declarado")


# ---- K3 + K10 · chaves SDMX e listas de candidatos -----------------------
def _pedido(funcao, *args, **kwargs):
    """
    Captura o pedido que uma funcao de acesso **faria**, sem tocar na rede.

    Substitui `eurostat.obter` e devolve `(dataset, chave, filtros)`. E a forma
    de testar a chave sem depender do Eurostat estar de pe — e sem depender de
    a via de recurso a salvar, que foi exactamente o que escondeu o K3.
    """
    from src import eurostat

    apanhado = {}

    def espia(dataset, chave, filtros, **kw):
        apanhado.update(dataset=dataset, chave=chave, filtros=filtros)
        return pd.DataFrame({"geo": ["PT"], "time": ["2026"], "valor": [1.0]}), "espia"

    original = eurostat.obter
    eurostat.obter = espia
    try:
        funcao(*args, **kwargs)
    finally:
        eurostat.obter = original
    return apanhado["dataset"], apanhado["chave"], apanhado["filtros"]


def test_chave_da_dimensao_do_agregado_tem_os_filtros_certos():
    """
    `A.AVG.TOTAL.PT` tinha um segmento a mais e devolvia HTTP 400 em todas as
    sessoes (auditoria de 12.08.2026, K3).
    """
    from src import eurostat

    ds, chave, filtros = _pedido(eurostat.dimensao_agregado, 2018)
    assert ds == "ilc_lvph01"
    assert chave == "A.AVG.PT"
    # A via de recurso tem de declarar todas as dimensoes: sem `unit`, o dia em
    # que o conjunto tiver duas unidades devolve duas series empilhadas.
    assert "unit" in filtros


def test_chave_do_salario_minimo_tem_os_filtros_certos():
    from src import eurostat

    ds, chave, filtros = _pedido(eurostat.salario_minimo, ["PT", "ES"], 2018)
    assert ds == "earn_mw_cur"
    assert chave == "S.EUR.PT+ES"
    assert "freq" in filtros
    # A frequencia e `S`, nao `S1` — era o outro erro das tres candidatas.
    assert chave.startswith("S.")


def test_salario_minimo_nao_pede_agregados_europeus():
    """
    Nao ha salario minimo europeu, e um geo inexistente **invalida o pedido
    inteiro** — nao e ignorado. Era a segunda razao para esta ligacao nunca
    chegar a via preferida, encontrada ao aplicar o K3.
    """
    from src import eurostat

    _ds, chave, filtros = _pedido(
        eurostat.salario_minimo, ["PT", "EU27_2020", "ES"], 2018)
    assert "EU27_2020" not in chave
    assert "EU27_2020" not in filtros["geo"]
    assert chave == "S.EUR.PT+ES"
    # E se so vierem agregados, e erro explicito e nao um pedido vazio.
    with pytest.raises(eurostat.ErroEurostat):
        eurostat.salario_minimo(["EU27_2020"], 2018)


def test_salario_minimo_nao_e_uma_lista_de_candidatos():
    """
    As tres candidatas nao podiam discriminar entre si: os filtros da via
    Statistics nao dependem da chave, pelo que a primeira iteracao devolvia
    sempre e as outras duas eram inalcancaveis (auditoria de 12.08.2026, K10).
    """
    from src import eurostat

    assert not hasattr(eurostat, "SM_CANDIDATOS"), (
        "a lista de candidatos do salario minimo voltou")
    fonte = _fonte("src/eurostat.py")
    i = fonte.index("def salario_minimo(")
    corpo = fonte[i:fonte.index("\ndef ", i + 10)]
    assert "for chave in" not in corpo, (
        "salario_minimo voltou a percorrer candidatos; usar uma chave verificada")


# ---- K4 · a guarda estrutural que fecha a classe -------------------------
def test_todas_as_ligacoes_batem_certo_com_a_estrutura_declarada():
    """
    Percorre **todas** as funcoes de acesso e confronta o pedido que cada uma
    faria com `DIMENSOES`. E o teste que apanha a familia inteira: chave com o
    numero errado de segmentos (K3), filtro com nomes de dimensao que ja nao
    existem (K4), dimensao nao filtrada.
    """
    from src import eurostat

    chamadas = [
        (eurostat.ponderadores, (["CP0111"],), {}),
        (eurostat.ponderadores_subclasses, (["CP01111"],), {}),
        (eurostat.indice_classes, (["CP0111"], "2019-01"), {}),
        (eurostat.indice_precos, ("CP011", "2019-01"), {}),
        (eurostat.variacoes, (["CP011"], ["PT"], "2023-01"), {}),
        (eurostat.despesa_alimentar, (2018,), {}),
        (eurostat.despesa_total_consumo, (["PT"], 2018), {}),
        (eurostat.despesa_alimentar_paises, (["PT"], 2018), {}),
        (eurostat.dimensao_agregado, (2018,), {}),
        (eurostat.numero_agregados, (2018,), {}),
        (eurostat.privacao_alimentar, (["PT"], 2018), {}),
        (eurostat.nivel_precos, (["PT"], "A010101", 2018), {}),
        (eurostat.salario_minimo, (["PT"], 2018), {}),
        (eurostat.rendimento, (["PT"], 2018), {}),
    ]
    for funcao, args, kwargs in chamadas:
        ds, chave, filtros = _pedido(funcao, *args, **kwargs)
        dims = eurostat.DIMENSOES.get(ds)
        assert dims is not None, f"{funcao.__name__}: {ds} nao esta em DIMENSOES"
        assert len(chave.split(".")) == len(dims), (
            f"{funcao.__name__}: chave «{chave}» tem {len(chave.split('.'))} "
            f"segmentos, {ds} tem {len(dims)} dimensoes")
        nomes = set(filtros) - {"sinceTimePeriod"}
        assert nomes == set(dims), (
            f"{funcao.__name__}: filtros {sorted(nomes)} != dimensoes "
            f"{sorted(dims)} de {ds}")


def test_a_guarda_trava_os_erros_que_existiam():
    """
    Exige que a **via errada seja recusada**. Sem esta metade, a guarda podia
    ser removida sem que nenhum teste desse por isso.
    """
    from src import eurostat

    maus = [
        # K3 — chave com um segmento a mais
        ("ilc_lvph01", "A.AVG.TOTAL.PT", {"freq": "A", "unit": "AVG", "geo": "PT"}),
        # K3 — a frequencia era S1 e havia um segmento a mais
        ("earn_mw_cur", "S1.EUR.MW.PT", {"freq": "S", "currency": "EUR", "geo": "PT"}),
        # K4 — nomes de dimensao anteriores a COICOP 2018
        ("prc_ppp_ind_1", "A.PLI_EU27_2020.A010101.PT",
         {"freq": "A", "na_item": "PLI_EU27_2020", "ppp_cat": "A010101", "geo": "PT"}),
        # dimensao nao filtrada: a via de recurso devolveria tudo empilhado
        ("ilc_lvph01", "A.AVG.PT", {"freq": "A", "geo": "PT"}),
        # conjunto arquivado, sem estrutura declarada
        ("prc_hicp_midx", "M.I15.CP011.PT",
         {"freq": "M", "unit": "I15", "coicop": "CP011", "geo": "PT"}),
    ]
    for ds, chave, filtros in maus:
        with pytest.raises(eurostat.ErroEurostat):
            eurostat._verificar_estrutura(ds, chave, filtros)


def test_conjuntos_arquivados_nao_tem_estrutura_declarada():
    """
    A tabela `DIMENSOES` e tambem uma lista branca: um conjunto arquivado nao
    pode voltar a ser pedido sem alguem o declarar de proposito.
    """
    from src import eurostat

    for arquivado in ("prc_hicp_midx", "prc_hicp_manr", "prc_hicp_inw",
                      "nama_10_co3_p3"):
        assert arquivado not in eurostat.DIMENSOES


# ---- K2 · frescura do Observatorio medida na ultima observacao -----------
def test_frescura_do_observatorio_mede_a_serie_e_nao_a_recolha():
    """
    A verificacao media a data em que o script correu. Correr o script sobre
    uma fonte que nao publicou nao torna os dados recentes — e era exactamente
    esse o estado real: recolha de 2 dias, serie de 86, limite de 60, e nenhum
    aviso (auditoria de 12.08.2026, K2).
    """
    from datetime import date

    from src.calculos import frescura_do_observatorio

    hoje = date(2026, 8, 12)
    f = frescura_do_observatorio("2026-05-18", "2026-08-10", 60, hoje=hoje)
    assert f["serie"]["dias"] == 86
    assert f["recolha"]["dias"] == 2
    assert f["parada"] is True
    assert f["fonte_parou"] is True
    assert f["periodos_em_falta"] == 3

    # E a via antiga — medir a recolha — **nao** teria disparado. Sem esta
    # metade, o teste passaria com a correcao revertida.
    from src.calculos import idade_fonte
    assert idade_fonte("2026-08-10", 60, hoje=hoje)["desatualizada"] is False


def test_frescura_do_observatorio_distingue_de_quem_e_a_falha():
    """
    A resposta e diferente conforme a causa: se ninguem recolheu, correr o
    script resolve; se a fonte parou, nao resolve nada.
    """
    from datetime import date

    from src.calculos import frescura_do_observatorio

    hoje = date(2026, 8, 12)

    em_dia = frescura_do_observatorio("2026-08-01", "2026-08-10", 60, hoje=hoje)
    assert not em_dia["parada"] and not em_dia["recolha_velha"]

    ninguem_recolhe = frescura_do_observatorio("2026-05-18", "2026-05-20", 60, hoje=hoje)
    assert ninguem_recolhe["parada"] and ninguem_recolhe["recolha_velha"]
    assert ninguem_recolhe["fonte_parou"] is False      # a falha e de quem recolhe

    fonte_parou = frescura_do_observatorio("2026-05-18", "2026-08-10", 60, hoje=hoje)
    assert fonte_parou["fonte_parou"] is True           # a falha e da fonte

    so_recolha = frescura_do_observatorio("2026-08-01", "2026-05-20", 60, hoje=hoje)
    assert so_recolha["recolha_velha"] and not so_recolha["parada"]


def test_frescura_do_observatorio_nao_acusa_o_que_nao_percebe():
    """Na duvida nao se acusa a fonte — como em `idade_fonte`."""
    from src.calculos import frescura_do_observatorio

    f = frescura_do_observatorio(None, "nao e data", 60)
    assert f["parada"] is False
    assert f["fonte_parou"] is False
    assert f["periodos_em_falta"] is None


def _ocorrencias(fonte: str, alvo: str):
    """Todas as posicoes de `alvo`, e nao so a primeira."""
    i = fonte.find(alvo)
    while i != -1:
        yield i
        i = fonte.find(alvo, i + 1)


def _argumentos(fonte: str, i: int) -> list[str]:
    """
    Os argumentos de topo da chamada que comeca em `i`, em texto.

    Conta parenteses, chavetas e parenteses retos para nao se enganar com
    `_meta.get("x")` nem com `_var["a"]["b"]`. Nao trata de virgulas dentro de
    literais de texto, que nestas chamadas nao existem; se vierem a existir, e
    aqui que se acrescenta.
    """
    abre = fonte.index("(", i)
    profundidade, inicio, args = 0, abre + 1, []
    for j in range(abre, len(fonte)):
        c = fonte[j]
        if c in "([{":
            profundidade += 1
        elif c in ")]}":
            profundidade -= 1
            if profundidade == 0:
                args.append(fonte[inicio:j])
                return [a.strip() for a in args]
        elif c == "," and profundidade == 1:
            args.append(fonte[inicio:j])
            inicio = j + 1
    raise AssertionError("chamada sem fecho de parenteses")


def test_a_frescura_recebe_sempre_a_serie_primeiro_e_a_recolha_depois():
    """
    `frescura_do_observatorio` distingue duas falhas que se parecem: a fonte
    parou de publicar, ou a recolha e que nao correu. So as distingue se lhe
    derem as duas datas pela ordem certa - a da ultima observacao da serie
    primeiro, a da recolha depois. Ja houve uma versao que passava so a recolha.

    Este teste seguia `_fim` a 160 caracteres da **primeira** ocorrencia. Em
    342d5f7 a seccao "Evolucao do Cabaz" acrescentou uma segunda chamada, para a
    serie da DECO, 1 550 linhas acima da do Observatorio. A primeira ocorrencia
    passou a ser essa, o teste comecou a falhar por a variavel ali se chamar
    outra coisa (esta correta: e a data do ultimo ponto da serie), e a chamada
    do Observatorio deixou de estar protegida sem nada acusar.

    Ancorar uma verificacao na primeira ocorrencia de um texto e fragil: basta
    aparecer outra antes para a guarda mudar de alvo em silencio. Passa a
    verificar **todas** as chamadas, e a propriedade e formulada pelo que ela e,
    e nao pelo nome que a variavel tem em cada sitio (20.08.2026).
    """
    fonte = _fonte("app.py")
    chamadas = list(_ocorrencias(fonte, "frescura_do_observatorio("))

    # Duas hoje, DECO e Observatorio. Se alguem as remover, o teste tem de dar
    # por isso em vez de passar a verificar o vazio.
    assert len(chamadas) >= 2, chamadas

    for i in chamadas:
        args = _argumentos(fonte, i)
        assert len(args) >= 2, args
        assert "extraido_em" not in args[0], (
            f"o primeiro argumento e a data da serie, nao a da recolha: {args[0]}")
        assert "extraido_em" in args[1], (
            f"o segundo argumento e a data da recolha: {args[1]}")

    # E a chamada antiga, que media so a recolha, nao pode voltar.
    assert 'idade_fonte(_obs_meta.get("extraido_em")' not in fonte


# ---- K5 · tudo o que o cursor filtra usa a janela do cursor --------------
def test_os_agregados_especiais_usam_a_janela_do_indice():
    """
    O cursor do separador Historico e definido pela janela do **indice**, que
    desde o E14 recua ate ANO_BASE_VIES. Este grafico e filtrado por esse
    cursor e era pedido com `ano - anos_historico`: doze meses do intervalo
    escolhido ficavam sem dados, sem aviso (auditoria de 12.08.2026, K5).
    """
    fonte = _fonte("app.py")
    i = fonte.index("agr_esp_df, via12")
    trecho = fonte[i:i + 220]
    assert "desde_indice" in trecho, trecho
    assert "anos_historico" not in trecho, trecho


def test_todas_as_series_filtradas_pelo_cursor_usam_a_mesma_janela():
    """
    A regra geral, que e o que impede a proxima ocorrencia: as series que o
    cursor filtra pedem-se com `desde_indice`. A janela curta
    (`desde_variacao`) so serve a comparacao europeia, que nao tem cursor.
    """
    fonte = _fonte("app.py")
    inicio = fonte.index("def carregar_dados(")
    corpo = fonte[inicio:fonte.index("def _atualizar_por_indice", inicio)]

    # As duas series de Portugal que o cursor filtra.
    for marca in ("var_pt_longo, via16", "agr_esp_df, via12"):
        j = corpo.index(marca)
        assert "desde_indice" in corpo[j:j + 220], marca

    # `desde_variacao` existe uma vez so, no pedido largo da comparacao europeia.
    assert corpo.count("desde_variacao") == 2      # a atribuicao e um uso
    j = corpo.index("var_df, via3")
    assert "desde_variacao" in corpo[j:j + 200]


def test_o_grafico_dos_agregados_avisa_quando_nao_cobre_o_intervalo():
    """A truncagem tem de ser dita, como ja acontece na variacao homologa."""
    fonte = _fonte("app.py")
    assert "len(meses_esp) < len(_esperados)" in fonte


# ---- K6 · o isolamento entre separadores tem de ser real -----------------
def test_nao_ha_formatadores_locais_duplicados():
    """
    `_pct` era `percentagem(v, sinal=False)` e `_num` era `numero(v, 1)`:
    formatadores redundantes, definidos a meio de um separador. O `_pct` era
    usado por mais dois separadores, o que fazia uma falha no primeiro arrastar
    os outros (auditoria de 12.08.2026, K6).
    """
    fonte = _fonte("app.py")
    assert "def _pct(" not in fonte
    assert "def _num(" not in fonte
    # E as chamadas foram convertidas, nao apagadas.
    assert fonte.count("sinal=False") >= 20


def test_nenhum_separador_usa_nome_definido_noutro():
    """
    A regra geral, e o que impede a proxima ocorrencia. O `painel()` promete que
    «os restantes separadores continuam a funcionar»; uma funcao definida a meio
    de um separador e usada noutro torna essa promessa falsa, com um NameError
    que nao explica nada a quem o ve.
    """
    import ast

    arvore = ast.parse(_fonte("app.py"))

    # Os blocos `with abaN:` de primeiro nivel.
    blocos = []
    for no in arvore.body:
        if isinstance(no, ast.With):
            alvos = [i.context_expr for i in no.items]
            if any(isinstance(a, ast.Name) and a.id.startswith("aba") for a in alvos):
                blocos.append(no)
    assert len(blocos) >= 5, "nao encontrei os blocos dos separadores"

    for bloco in blocos:
        fim = max(getattr(n, "end_lineno", bloco.lineno) for n in ast.walk(bloco))
        definidas = {n.name: n.lineno for n in ast.walk(bloco)
                     if isinstance(n, ast.FunctionDef)}
        for nome, linha_def in definidas.items():
            usos = [n.lineno for n in ast.walk(arvore)
                    if isinstance(n, ast.Name) and n.id == nome
                    and isinstance(n.ctx, ast.Load)]
            fora = [l for l in usos if not (bloco.lineno <= l <= fim)]
            assert not fora, (
                f"«{nome}», definida na linha {linha_def} dentro do separador que "
                f"comeca na linha {bloco.lineno}, e usada fora dele nas linhas "
                f"{fora}. Formatadores e auxiliares partilhados pertencem a "
                f"src/config.py — ver K6.")


# ---- K7 + K8 · nenhum numero derivado inscrito a mao ---------------------
def test_o_ano_da_despesa_nao_esta_inscrito_a_mao():
    """
    A Metodologia dizia «o ano da despesa — hoje 2022» quando a migracao para o
    nama_10_cp18 (E16) o tinha passado a 2024. Contradizia a barra de estado da
    propria aplicacao (auditoria de 12.08.2026, K7).
    """
    vivo = _fonte_viva("app.py")
    assert "hoje 2022" not in vivo
    assert "@ANO_DESPESA@" in vivo             # o marcador existe...
    assert '.replace("@ANO_DESPESA@"' in vivo  # ...e e substituido


def test_a_comparacao_entre_bases_e_calculada():
    """
    Os quatro numeros do bloco «isto nao e custo orcamental» estavam inscritos a
    mao, dois deles ao lado de numeros calculados em directo — e o valor das
    Contas Nacionais estava escrito ao lado do sitio de onde podia vir. E a
    terceira ocorrencia do padrao do C2 e do E9 (auditoria de 12.08.2026, K8).
    """
    vivo = _fonte_viva("app.py")
    for inscrito in ("15 400 M€", "28 188 M€", "33 038 M€", "1,8 e 2,1 vezes"):
        assert inscrito not in vivo, f"numero inscrito a mao: {inscrito}"

    # O confronto numerico entre a base do simulador e a despesa das Contas
    # Nacionais saiu da nota «isto nao e custo orcamental» a 13.08.2026: era
    # aparelho metodologico no meio de uma advertencia que tem de se ler em
    # tres segundos. Com ele saiu o calculo que o alimentava.
    #
    # O que este teste guardava eram duas coisas, e so uma delas desapareceu.
    # A proibicao dos numeros inscritos a mao **fica**, e e a que interessa: se
    # o confronto voltar, tem de voltar calculado. A exigencia de que as duas
    # linhas de calculo existam passa a ser condicional a o bloco existir.
    if "_base_sim_milhoes" in vivo:
        assert "_base_sim_milhoes = agregados * media_agregado * 12 / 1e6" in vivo
        assert "_racio_bases = _cn_milhoes / _base_sim_milhoes" in vivo


# ---- K9 · a variacao da receita nao e a receita --------------------------
def test_a_receita_de_iva_e_rotulada_como_variacao():
    """
    O indicador mostra `iva_depois - iva_antes` — uma variacao — sob um rotulo
    que se lia como nivel. O cartao agregado ja lhe chamava «Variacao de receita
    implicita» (auditoria de 12.08.2026, K9).

    O que o K9 fixou foi o **rotulo**, e e so isso que se exige aqui. A
    assercao prendia tambem a posicao do indicador na fila (`c[4]`), e passou a
    falhar quando o redesenho visual de 14.08.2026 promoveu a nova despesa a
    indicador de capa e a fila passou de cinco para quatro. A posicao e materia
    de apresentacao; o rotulo e que era o defeito.
    """
    fonte = _fonte("app.py")
    assert '.metric("Variação da receita de IVA por mês"' in fonte
    assert '.metric("Receita de IVA por mês"' not in fonte


# ---- K12 · a vigilancia cobre todas as series obtidas --------------------
def test_a_vigilancia_cobre_as_series_que_alimentam_a_aplicacao():
    """
    Tres series obtidas ficavam de fora: a serie longa de PT (que alimenta todo
    o separador Historico desde 11.08), os agregados especiais, e os
    ponderadores por subclasse — que sao a base de **todo** o apuramento do IVA
    (auditoria de 12.08.2026, K12).
    """
    fonte = _fonte("app.py")
    i = fonte.index("vigilancia = []")
    bloco = fonte[i:fonte.index("return {", i)]
    for serie in ("Variação homóloga PT (série longa)",
                  "Agregados especiais do índice",
                  "Ponderadores por subclasse"):
        assert serie in bloco, f"serie fora da vigilancia: {serie}"
    # As tres tem de reutilizar limites ja justificados em config.py.
    from src.config import LIMITES_FRESCURA
    assert LIMITES_FRESCURA["variacoes"][0] == 60
    assert LIMITES_FRESCURA["ponderadores"][0] == 450


# ---- K13 · classes com periodos diferentes, declaradas ------------------
def test_o_desalinhamento_de_periodos_e_detectado_e_declarado():
    """
    Cada classe entra com a sua ultima observacao, mas o rotulo mostrado e o
    maximo de todas. O desalinhamento nao era detectado (auditoria K13).

    **Nao se filtra pelo periodo comum**, ao contrario do que o diagnostico
    recomendava: deixar cair uma classe tira-lhe o ponderador e as oito
    restantes absorvem 100 % da despesa — pior do que usar o ponderador do ano
    anterior, que muda pouco. Mantem-se o recuo e declara-se.
    """
    fonte = _fonte_viva("app.py")
    assert "pesos_desalinhados" in fonte
    assert "variacoes_desalinhadas" in fonte
    # ... e chegam a interface, nao ficam so no dicionario de dados.
    assert 'dados.get("pesos_desalinhados")' in fonte
    assert 'dados.get("variacoes_desalinhadas")' in fonte

    # A logica em si, reproduzida: uma classe um mes atras tem de ser apanhada.
    linhas = pd.DataFrame([
        {"coicop": "CP0111", "time": "2026-06", "valor": 2.5},
        {"coicop": "CP0112", "time": "2026-06", "valor": 4.3},
        {"coicop": "CP0113", "time": "2026-05", "valor": 9.9},   # ficou atras
    ]).sort_values("time")
    mes = linhas["time"].max()
    desalinhadas = {c: str(p) for c, p
                    in linhas.groupby("coicop")["time"].last().items()
                    if str(p) != str(mes)}
    assert desalinhadas == {"CP0113": "2026-05"}
    # E a classe **continua no calculo**, com o valor que tem.
    valores = linhas.groupby("coicop")["valor"].last().to_dict()
    assert len(valores) == 3 and valores["CP0113"] == 9.9


# ---- K14 · a prosa do Engel nao assume a ordem dos extremos --------------
def test_a_legenda_do_engel_deriva_a_ordem_em_vez_de_a_assumir():
    """
    `intervalo_engel` devolve min e max sem presumir qual das bases e a maior —
    ha um teste que o exige desde o B4. A prosa por baixo da tabela presumia
    (auditoria de 12.08.2026, K14).
    """
    fonte = _fonte_viva("app.py")
    assert '_idf_e_inferior = _eng["idf"] <= _eng["contas"]' in fonte
    # As palavras «inferior» e «superior» deixam de estar fixas na frase.
    i = fonte.index("_idf_e_inferior =")
    trecho = fonte[i:i + 900]
    assert "{_pos_idf}" in trecho and "{_pos_cn}" in trecho

    # E a funcao continua a nao assumir, nos dois sentidos.
    from src.calculos import intervalo_engel
    from src.config import IDF_PESO_ALIMENTAR
    idf = float(IDF_PESO_ALIMENTAR["total"])
    acima = intervalo_engel({"ano": "2024", "quota": idf + 5})
    assert (acima["minimo"], acima["maximo"]) == (idf, idf + 5)
    abaixo = intervalo_engel({"ano": "2024", "quota": idf - 5})
    assert (abaixo["minimo"], abaixo["maximo"]) == (idf - 5, idf)


# ---- K1 · a taxa de capa e a oficial, e a aditividade fica declarada -----
def test_a_taxa_de_capa_e_a_oficial_do_cp011():
    """
    Decisao da Ines, 12.08.2026: numa ferramenta que apoia o Gabinete em debate
    publico, o numero de capa tem de ser o que qualquer pessoa pode verificar no
    INE. A capa mostrava uma taxa **reconstituida** da decomposicao, que difere
    da oficial em cerca de 0,15 p.p. (auditoria de 12.08.2026, K1).
    """
    vivo = _fonte_viva("app.py")
    # A taxa oficial e obtida e chega ao dicionario de dados...
    assert '"variacao_oficial": variacao_oficial' in vivo
    # ... e e ela que vai para o indicador de topo.
    assert '_var_of = dados.get("variacao_oficial")' in vivo
    assert "percentagem(_taxa_capa)" in vivo
    # A reconstituida deixou de ser o que o indicador mostra.
    assert 'percentagem(resumo["variacao_implicita"]),' not in vivo


def test_a_taxa_oficial_e_do_mesmo_mes_das_variacoes_por_classe():
    """
    Comparar a oficial de um mes com contributos de outro seria pior do que o
    problema que se corrigiu.
    """
    vivo = _fonte_viva("app.py")
    i = vivo.index("variacao_oficial, mes_var_oficial = None, None")
    trecho = vivo[i:i + 420]
    assert "mes_variacoes" in trecho, trecho


def test_a_divergencia_entre_as_duas_agregacoes_esta_declarada():
    """
    A aditividade continua a valer, mas a taxa que ela implica nao e a oficial.
    Tem de estar escrito onde os contributos aparecem, e nao so no tooltip.
    """
    vivo = _fonte_viva("app.py")
    assert "Os nove contributos somam exatamente" in vivo
    assert "de há um ano" in vivo and "período corrente" in vivo


def test_a_reconstituida_pondera_pelos_valores_de_ha_um_ano():
    """
    A explicacao dada ao leitor tem de ser verdadeira, e e verificavel: a taxa
    implicita da decomposicao **e** a media das taxas ponderada pelos valores do
    periodo anterior. Se deixasse de ser, a nota na interface passava a mentir.
    """
    from src.calculos import decompor, resumo_decomposicao

    pesos = {"CP0111": 40.0, "CP0112": 40.0, "CP0113": 20.0}
    variacoes = {"CP0111": 2.5, "CP0112": 4.3, "CP0113": 10.7}
    df = decompor(300.0, pesos, variacoes)
    r = resumo_decomposicao(df, 300.0)

    com = df.dropna(subset=["contributo"])
    num = sum(l.valor / (1 + l.variacao / 100) * l.variacao for l in com.itertuples())
    den = sum(l.valor / (1 + l.variacao / 100) for l in com.itertuples())
    assert r["variacao_implicita"] == pytest.approx(num / den)

    # E **diverge** da media ponderada pelos valores correntes, que e a
    # construcao da taxa oficial. Sem esta metade, o teste nao mostrava que as
    # duas agregacoes sao mesmo diferentes.
    corrente = sum(l.quota * l.variacao for l in com.itertuples())
    assert corrente > r["variacao_implicita"]
    assert abs(corrente - r["variacao_implicita"]) > 0.05
