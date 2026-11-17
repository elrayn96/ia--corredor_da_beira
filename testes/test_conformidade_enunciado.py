"""Regressões ligadas directamente aos requisitos obrigatórios do enunciado."""

from dataclasses import FrozenInstanceError

import pytest

from experiencias.analise import exemplo_distancia_vs_tempo, factor_ramificacao_efectivo
from src.buscas.informadas import a_star
from src.buscas.nao_informadas import dfs, ids, ucs
from src.contrato_busca import No, caminho
from src.contrato_busca import Problema as ProblemaAbstrato
from src.estado import Estado
from src.gerador import (
    carregar_json,
    converter_para_busca,
    gerar_instancias_experimentais,
)
from src.problema import Problema


def test_selector_resolve_os_tres_niveis_de_instancia():
    from src.interface.painel_configuracao import caminho_instancia_experimental

    assert caminho_instancia_experimental("Pequena", "01").name == "pequena_01.json"
    assert caminho_instancia_experimental("Média", 5).name == "media_05.json"
    assert caminho_instancia_experimental("Grande", "10").name == "grande_10.json"


class Grafo:
    def get_estado_inicial(self):
        return "S"

    def get_sucessores(self, estado):
        return {
            "S": [("S-A", "A", 1)],
            "A": [("A-B", "B", 1)],
            "B": [("B-G", "G", 1)],
        }.get(estado, [])

    def teste_objectivo(self, estado):
        return estado == "G"


def test_contrato_abstracto_no_e_caminho():
    with pytest.raises(TypeError):
        ProblemaAbstrato()
    raiz = No("S", None, None, 0, 1)
    filho = No("G", raiz, "ir", 1, 2)
    assert caminho(filho) == [raiz, filho]
    assert filho.profundidade == 1


def test_estado_e_formalmente_imutavel():
    estado = Estado("Beira")
    with pytest.raises(FrozenInstanceError):
        estado.tempo = 20


def test_dfs_respeita_limite_configuravel():
    assert dfs(Grafo(), limite=2) is None
    assert dfs(Grafo(), limite=3).get_custo_total() == 3


def test_ids_reporta_reexpansoes():
    estatisticas = {}
    assert ids(Grafo(), 3, estatisticas=estatisticas) is not None
    assert estatisticas["nos_reexpandidos"] > 0


def test_a_star_e_ucs_devolvem_o_mesmo_custo():
    problema = Grafo()
    h0 = lambda estado, _problema: 0
    assert a_star(problema, h0).get_custo_total() == ucs(problema).get_custo_total()


@pytest.fixture
def problema_real():
    instancia = carregar_json("dados/instancias_testes/teste.json")
    return Problema(**converter_para_busca(instancia))


def test_carga_pendente_invalida_estado_apos_14_horas(problema_real):
    estado = problema_real.criar_estado(
        "Beira", set(), problema_real.LIMITE_FRIO_MINUTOS + 1,
        problema_real.CAPACIDADE,
    )
    assert problema_real.get_sucessores(estado) == []


def test_pode_esperar_ate_as_cinco_quando_viagem_cruza_as_22(problema_real):
    concluidas = set(problema_real.get_supermercados())
    estado = problema_real.criar_estado(
        "Beira", concluidas, 1000, problema_real.CAPACIDADE
    )
    esperas = [
        (accao, seguinte) for accao, seguinte, _ in problema_real.get_sucessores(estado)
        if accao.get_tipo() == "esperar"
    ]
    assert esperas
    assert esperas[0][1].get_tempo() > estado.get_tempo()


def test_gerador_cria_dez_instancias_viaveis_por_nivel(tmp_path):
    caminhos = gerar_instancias_experimentais(tmp_path)
    assert len(caminhos) == 30
    niveis = [carregar_json(caminho)["nivel"] for caminho in caminhos]
    assert {nivel: niveis.count(nivel) for nivel in set(niveis)} == {
        "pequena": 10, "media": 10, "grande": 10,
    }
    for nivel in ("pequena", "media", "grande"):
        caminho = next(p for p in caminhos if carregar_json(p)["nivel"] == nivel)
        dados = carregar_json(caminho)
        problema = Problema(
            estradas=dados["estradas"], supermercados=dados["supermercados"]
        )
        solucao = a_star(problema, lambda estado, p: p.heuristica(estado, "h2"))
        assert solucao is not None


def test_factor_ramificacao_e_exemplo_distancia_tempo():
    b = factor_ramificacao_efectivo(14, 3)
    assert 1.9 < b < 2.1  # 1 + 2 + 4 + 8 = 15 = N + 1
    exemplo = exemplo_distancia_vs_tempo()
    assert exemplo["menor_distancia"]["quilometros"] < exemplo["menor_tempo"]["quilometros"]
    assert exemplo["menor_distancia"]["minutos"] > exemplo["menor_tempo"]["minutos"]
