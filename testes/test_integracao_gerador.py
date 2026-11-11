"""Integração: dados da Adila -> Problema do Armando -> heurísticas do Naeem."""

import math

import pytest

from src.estado import Estado
from src.gerador import converter_para_busca, gerar_instancia
from src.heuristicas import h0, h1, h2
from src.problema import Problema


@pytest.fixture(scope="module")
def problema_gerado():
    instancia = gerar_instancia(semente=202601)
    dados = converter_para_busca(instancia)
    return Problema(**dados)


def test_instancia_gerada_cria_problema_valido(problema_gerado):
    inicial = problema_gerado.get_estado_inicial()
    assert isinstance(inicial, Estado)
    assert inicial.get_localidade() == "Beira"
    assert len(problema_gerado.get_supermercados()) == 7
    assert not problema_gerado.teste_objectivo(inicial)


def test_estradas_geradas_produzem_sucessores(problema_gerado):
    inicial = problema_gerado.get_estado_inicial()
    sucessores = problema_gerado.get_sucessores(inicial)
    assert sucessores, "O estado inicial deveria permitir pelo menos uma acção"
    for accao, seguinte, custo in sucessores:
        assert accao is not None
        assert isinstance(seguinte, Estado)
        assert custo >= 0
        assert seguinte.get_tempo() == inicial.get_tempo() + custo


@pytest.mark.parametrize("heuristica", [h0, h1, h2], ids=["h0", "h1", "h2"])
def test_heuristicas_aceitam_problema_real(problema_gerado, heuristica):
    valor = heuristica(problema_gerado.get_estado_inicial(), problema_gerado)
    assert isinstance(valor, (int, float))
    assert math.isfinite(valor)
    assert valor >= 0


def test_h2_domina_h1_na_instancia_gerada(problema_gerado):
    inicial = problema_gerado.get_estado_inicial()
    assert h2(inicial, problema_gerado) >= h1(inicial, problema_gerado)
