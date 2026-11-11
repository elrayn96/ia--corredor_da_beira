"""Integração: Problema -> heurísticas -> buscas -> Solucao.

Usa sete clientes (exigência de Problema), numa rede linear pequena.
Não executa a instância real, que pode demorar muito tempo.
"""

import pytest

from src.buscas.informadas import a_star, a_star_ponderada, busca_gulosa
from src.heuristicas import h0, h1, h2
from src.problema import Problema
from src.solucao import Solucao


@pytest.fixture
def problema_pequeno():
    localidades = ["Beira"] + [f"C{i}" for i in range(1, 8)]
    estradas = {nome: {} for nome in localidades}
    for origem, destino in zip(localidades, localidades[1:]):
        atributos = {"distancia": 1, "piso": 5}
        estradas[origem][destino] = atributos.copy()
    estradas[localidades[-1]]["Beira"] = {"distancia": 1, "piso": 5}
    supermercados = {
        nome: {"abertura": "05:00", "fecho": "19:00"}
        for nome in localidades[1:]
    }
    return Problema(estradas, supermercados)


def validar_solucao(problema, solucao):
    assert isinstance(solucao, Solucao)
    estados = solucao.get_estados()
    accoes = solucao.get_accoes()
    assert len(estados) == len(accoes) + 1
    assert estados[0] == problema.get_estado_inicial()
    assert problema.teste_objectivo(estados[-1])

    custo_acumulado = 0
    for anterior, accao, seguinte in zip(estados, accoes, estados[1:]):
        transicoes = problema.get_sucessores(anterior)
        correspondencias = [
            custo for acao_valida, estado_valido, custo in transicoes
            if acao_valida.get_tipo() == accao.get_tipo()
            and acao_valida.get_parametros() == accao.get_parametros()
            and estado_valido == seguinte
        ]
        assert correspondencias, (
            f"Transição inválida: {anterior!r} -> {accao!r} -> {seguinte!r}"
        )
        custo_acumulado += correspondencias[0]
    assert custo_acumulado == solucao.get_custo_total()


@pytest.mark.parametrize("heuristica", [h0, h1, h2], ids=["h0", "h1", "h2"])
def test_a_star_retorna_solucao_valida(problema_pequeno, heuristica):
    solucao = a_star(problema_pequeno, heuristica)
    validar_solucao(problema_pequeno, solucao)


def test_gulosa_retorna_solucao_valida(problema_pequeno):
    solucao = busca_gulosa(problema_pequeno, h2)
    validar_solucao(problema_pequeno, solucao)


def test_a_star_ponderada_retorna_solucao_valida(problema_pequeno):
    solucao = a_star_ponderada(problema_pequeno, h2, peso=1.5)
    validar_solucao(problema_pequeno, solucao)
