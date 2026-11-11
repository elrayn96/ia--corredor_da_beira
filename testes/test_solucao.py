import pytest

from src.estado import Estado
from src.accao import Accao
from src.solucao import Solucao


@pytest.fixture
def dados_solucao():
    estado_inicial = Estado("Beira", set(), 0, 300000)

    estado_final = Estado(
        "Dondo",
        set(),
        26,
        289500
    )

    accao = Accao("deslocar", destino="Dondo")

    return estado_inicial, estado_final, accao


# 1. Verificar a criacao de uma solucao valida
def test_solucao_valida(dados_solucao):
    inicial, final, accao = dados_solucao

    solucao = Solucao(
        [accao],
        [inicial, final],
        26
    )

    assert len(solucao.get_accoes()) == 1
    assert len(solucao.get_estados()) == 2
    assert solucao.get_custo_total() == 26


# 2. Verificar uma solucao sem accoes
def test_solucao_sem_accoes():
    estado = Estado("Beira", set(), 0, 300000)

    solucao = Solucao([], [estado], 0)

    assert solucao.get_accoes() == []
    assert solucao.get_estados() == [estado]
    assert solucao.get_custo_total() == 0


# 3. Rejeitar quantidade inconsistente de estados
def test_quantidade_estados_invalida(dados_solucao):
    inicial, final, accao = dados_solucao

    with pytest.raises(ValueError):
        Solucao(
            [accao],
            [inicial],
            26
        )


# 4. Rejeitar custo negativo
def test_custo_negativo(dados_solucao):
    inicial, final, accao = dados_solucao

    with pytest.raises(ValueError):
        Solucao(
            [accao],
            [inicial, final],
            -10
        )


# 5. Verificar a proteccao das listas internas
def test_listas_protegidas(dados_solucao):
    inicial, final, accao = dados_solucao

    solucao = Solucao(
        [accao],
        [inicial, final],
        26
    )

    accoes = solucao.get_accoes()
    estados = solucao.get_estados()

    accoes.clear()
    estados.clear()

    assert len(solucao.get_accoes()) == 1
    assert len(solucao.get_estados()) == 2