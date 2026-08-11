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

    # o caso que o padrão antigo estragava
    etiqueta = f"{percentagem(101.4, sinal=False)}  ({pontos(1.4, casas=1)})"
    assert etiqueta == "101,4 %  (+1,4 p.p.)"
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
