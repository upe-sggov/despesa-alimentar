"""
Testes do registo mediático e dos seus apuramentos.

A maioria destes testes guarda a **integridade do registo**, e não uma fórmula:
o risco aqui não é uma conta errada, é uma entrada mal preenchida que passa
despercebida no meio de trinta e nove. Um caso com um sinal inventado, uma
narrativa a apontar para um caso que não existe, uma ligação que deixou de ser
uma ligação, tudo isso sai daqui em vez de sair no ecrã.

Executar:  python -m pytest tests/ -v
"""
from datetime import date

import pytest

from src import media


# ------------------------------------------------------- integridade do registo
def test_identificadores_sao_unicos():
    ids = [c["id"] for c in media.CASOS]
    assert len(ids) == len(set(ids))


def test_todos_os_casos_tem_os_campos_obrigatorios():
    obrigatorios = {"id", "registo", "frente", "data", "orgao", "tipo_emissor",
                    "titulo", "afirmacao", "contraponto", "fonte", "sinal",
                    "classe", "ancora", "replicacao", "contexto_titulo",
                    "ligacao", "nota"}
    for caso in media.CASOS:
        em_falta = obrigatorios - set(caso)
        assert not em_falta, f"{caso['id']} sem {sorted(em_falta)}"


def test_vocabulario_controlado_e_respeitado():
    for caso in media.CASOS:
        assert caso["sinal"] in media.SINAIS, caso["id"]
        assert caso["classe"] in media.CLASSES, (caso["id"], caso["classe"])
        assert caso["tipo_emissor"] in media.TIPOS_EMISSOR, caso["id"]
        assert caso["ancora"] in media.ANCORAS, (caso["id"], caso["ancora"])


def test_datas_estao_dentro_do_periodo_declarado():
    inicio, fim = media.PERIODO
    for caso in media.CASOS:
        quando = date.fromisoformat(caso["data"])
        assert inicio <= quando <= fim, f"{caso['id']} em {caso['data']}"


def test_frentes_sao_as_tres_declaradas():
    assert {c["frente"] for c in media.CASOS} == {1, 2, 3}


def test_replicacao_e_pelo_menos_um():
    """Uma peça publicada por zero órgãos não existe."""
    for caso in media.CASOS:
        assert caso["replicacao"] >= 1, caso["id"]


def test_ligacoes_sao_ligacoes_ou_ausentes():
    """
    Recortes de imprensa em papel não têm URL, e é legítimo. O que não é
    legítimo é um campo de ligação com texto que não é uma ligação, porque o
    separador desenha-o como tal.
    """
    for caso in media.CASOS:
        if caso["ligacao"] is not None:
            assert caso["ligacao"].startswith("https://"), caso["id"]


def test_contexto_no_titulo_usa_o_vocabulario():
    for caso in media.CASOS:
        assert caso["contexto_titulo"] in {"titulo", "corpo", None}, caso["id"]


# ------------------------------------------------------------------ narrativas
def test_narrativas_cobrem_todos_os_casos():
    """
    Nenhum caso pode ficar órfão: se não pertence a nenhuma narrativa, não
    aparece no separador e o levantamento perde-o sem aviso.
    """
    nas_narrativas = {i for n in media.NARRATIVAS for i in n["casos"]}
    assert nas_narrativas == {c["id"] for c in media.CASOS}


def test_narrativas_nao_repetem_casos_entre_si():
    vistos: list[str] = []
    for n in media.NARRATIVAS:
        vistos.extend(n["casos"])
    assert len(vistos) == len(set(vistos))


def test_casos_da_narrativa_devolve_casos_reais():
    for n in media.NARRATIVAS:
        casos = media.casos_da_narrativa(n["id"])
        assert [c["id"] for c in casos] == n["casos"]


def test_narrativa_inexistente_levanta():
    with pytest.raises(KeyError):
        media.casos_da_narrativa(99)


# ------------------------------------------------------------------ apuramentos
def test_por_sinal_soma_o_total_de_casos():
    assert sum(media.por_sinal().values()) == len(media.CASOS)


def test_por_tipo_emissor_soma_o_total_de_casos():
    assert sum(media.por_tipo_emissor().values()) == len(media.CASOS)


def test_dependencia_de_fonte_conta_so_a_frente_pedida():
    apurado = media.dependencia_de_fonte(1)
    assert apurado["total"] == len([c for c in media.CASOS if c["frente"] == 1])
    assert apurado["ancorados"] == len(apurado["ids"])
    assert 0.0 <= apurado["proporcao"] <= 1.0


def test_dependencia_de_fonte_so_conta_casos_ancorados_na_deco():
    for ident in media.dependencia_de_fonte(1)["ids"]:
        assert media.por_id(ident)["ancora"] == "deco"


def test_contexto_no_titulo_reparte_todos_os_casos_da_frente():
    apurado = media.contexto_no_titulo(1)
    total = len(apurado["titulo"]) + len(apurado["corpo"]) + len(apurado["ausente"])
    assert total == len([c for c in media.CASOS if c["frente"] == 1])


def test_o_contexto_de_longo_prazo_vive_sobretudo_fora_do_titulo():
    """
    O achado que sustenta a conclusão do separador. Se algum dia deixar de ser
    verdade, é a conclusão que tem de mudar, e este teste é que dá o aviso.
    """
    apurado = media.contexto_no_titulo(1)
    assert len(apurado["corpo"]) > len(apurado["titulo"])


def test_latencia_causal_vem_ordenada_por_dias():
    dias = [linha["dias"] for linha in media.latencia_causal()]
    assert dias == sorted(dias)


def test_latencia_causal_conta_a_partir_do_choque():
    linha = next(linha for linha in media.latencia_causal() if linha["id"] == "F1 #2")
    esperado = (date(2026, 3, 12) - media.CHOQUE_GEOPOLITICO).days
    assert linha["dias"] == esperado


def test_o_tempo_decorrido_nao_separa_as_boas_atribuicoes_das_mas():
    """
    O apuramento existe para refutar a hipótese fácil. Tem de continuar a haver
    uma atribuição ancorada mais precoce do que alguma atribuição não ancorada:
    é isso que impede a leitura de que basta esperar para acertar.
    """
    linhas = media.latencia_causal()
    ancoradas = [linha["dias"] for linha in linhas if linha["ancorada_em_dados"]]
    soltas = [linha["dias"] for linha in linhas if not linha["ancorada_em_dados"]]
    assert ancoradas and soltas
    assert min(ancoradas) < max(soltas)


def test_replicacao_vem_da_mais_replicada_para_a_menos():
    valores = [c["replicacao"] for c in media.replicacao()]
    assert valores == sorted(valores, reverse=True)
    assert all(v >= 2 for v in valores)


def test_cronologia_vem_ordenada():
    datas = [c["data"] for c in media.cronologia()]
    assert datas == sorted(datas)


def test_por_id_encontra_e_falha_como_deve():
    assert media.por_id("F1 #1")["orgao"] == "Euronews"
    with pytest.raises(KeyError):
        media.por_id("F9 #99")


def test_casos_densos_sao_um_subconjunto_dentro_da_janela():
    inicio, fim = media.JANELA_DENSA
    assert 0 < len(media.CASOS_DENSOS) < len(media.CASOS)
    for caso in media.CASOS_DENSOS:
        assert inicio <= date.fromisoformat(caso["data"]) <= fim


# --------------------------------------------------- afirmações por verificar
def test_por_verificar_agrupa_sem_perder_nada():
    grupos = media.por_verificar_por_responsabilidade()
    assert sum(len(v) for v in grupos.values()) == len(media.POR_VERIFICAR)


def test_ha_afirmacoes_de_responsabilidade_governativa():
    """
    É a categoria que justifica o separador existir num produto para gabinetes.
    Se ficar vazia, o separador perde o seu ponto e alguém tem de reparar nisso.
    """
    assert media.por_verificar_por_responsabilidade().get("governo")


def test_por_verificar_tem_os_campos_que_o_separador_desenha():
    for item in media.POR_VERIFICAR:
        assert {"quem", "quando", "onde", "afirmacao", "estado",
                "contraponto", "responsabilidade"} <= set(item)


# ------------------------------------------------------- indicadores e limites
def test_indicadores_trazem_sempre_uma_cautela():
    """Nenhum destes indicadores pode ser apresentado sem o seu limite."""
    for indicador in media.INDICADORES:
        assert indicador["cautela"].strip()


def test_contradicoes_apontam_para_casos_existentes():
    ids = {c["id"] for c in media.CASOS}
    for contradicao in media.CONTRADICOES:
        for ident in contradicao["casos"]:
            assert ident in ids, ident


def test_o_levantamento_declara_os_seus_limites():
    assert len(media.LIMITES) >= 5
    assert all(limite.strip() for limite in media.LIMITES)


def test_fontes_de_registo_estao_declaradas():
    assert len(media.FONTES_REGISTO) >= 3


# ----------------------------------------------------------------- redes sociais
def test_redes_topo_vem_ordenado_por_interacoes():
    valores = [p["interacoes"] for p in media.REDES_TOPO]
    assert valores == sorted(valores, reverse=True)


def test_redes_topo_so_cita_casos_existentes():
    ids = {c["id"] for c in media.CASOS}
    for publicacao in media.REDES_TOPO:
        if publicacao["caso"] is not None:
            assert publicacao["caso"] in ids


def test_alcance_web_so_cita_casos_existentes():
    ids = {c["id"] for c in media.CASOS}
    for linha in media.ALCANCE_WEB:
        assert linha["caso"] in ids


def test_alcance_web_e_amostra_pequena_e_o_modulo_admite_o():
    """
    Cinco observações não sustentam a relação entre rigor e alcance. Se a
    amostra crescer, o aviso nos limites tem de ser reescrito, e este teste
    obriga a passar por lá.
    """
    assert len(media.ALCANCE_WEB) == 5
    assert any("cinco observações" in limite for limite in media.LIMITES)
