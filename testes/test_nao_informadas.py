
import pytest

from src.buscas.nao_informadas import bfs, dfs, ids, lds, ucs


class ProblemaGrafo:
    def __init__(self, arestas, inicio, objetivo):
        self.arestas = arestas
        self.inicio = inicio
        self.objetivo = objetivo

    def get_estado_inicial(self):
        return self.inicio

    def get_sucessores(self, estado):
        return [
            (f"{estado}->{destino}", destino, custo)
            for destino, custo in self.arestas.get(estado, [])
        ]

    def teste_objectivo(self, estado):
        return estado == self.objetivo


ARESTAS = {
    "S": [("A", 1), ("B", 4)],
    "A": [("G", 10)],
    "B": [("G", 3)],
}


@pytest.fixture
def problema():
    return ProblemaGrafo(ARESTAS, "S", "G")


@pytest.mark.parametrize("algoritmo", [bfs, dfs, ucs])
def test_encontra_solucao(problema, algoritmo):
    solucao = algoritmo(problema)

    assert solucao is not None
    assert solucao.get_estados()[0] == "S"
    assert solucao.get_estados()[-1] == "G"
    assert len(solucao.get_estados()) == len(solucao.get_accoes()) + 1


def test_bfs_encontra_menor_numero_acoes(problema):
    solucao = bfs(problema)

    assert len(solucao.get_accoes()) == 2
    assert solucao.get_estados() == ["S", "A", "G"]
    assert solucao.get_custo_total() == 11


def test_dfs_encontra_solucao(problema):
    solucao = dfs(problema)

    assert solucao is not None
    assert solucao.get_estados() == ["S", "A", "G"]
    assert solucao.get_custo_total() == 11


def test_ucs_encontra_menor_custo(problema):
    solucao = ucs(problema)

    assert solucao.get_custo_total() == 7
    assert solucao.get_estados() == ["S", "B", "G"]
    assert solucao.get_accoes() == ["S->B", "B->G"]


def test_lds_respeita_limite(problema):
    assert lds(problema, 0) is None
    assert lds(problema, 1) is None

    solucao = lds(problema, 2)

    assert solucao is not None
    assert len(solucao.get_accoes()) == 2


def test_ids_encontra_solucao(problema):
    assert ids(problema, 1) is None

    solucao = ids(problema, 2)

    assert solucao is not None
    assert len(solucao.get_accoes()) == 2
    assert solucao.get_estados()[-1] == "G"


@pytest.mark.parametrize("algoritmo", [bfs, dfs, ucs])
def test_sem_solucao(algoritmo):
    problema = ProblemaGrafo(
        {"S": [("A", 1)], "A": []},
        "S",
        "G"
    )

    assert algoritmo(problema) is None


def test_lds_ids_sem_solucao():
    problema = ProblemaGrafo(
        {"S": [("A", 1)], "A": []},
        "S",
        "G"
    )

    assert lds(problema, 3) is None
    assert ids(problema, 3) is None


@pytest.mark.parametrize("algoritmo", [bfs, dfs, ucs])
def test_estado_inicial_ja_e_objetivo(algoritmo):
    problema = ProblemaGrafo({}, "G", "G")

    solucao = algoritmo(problema)

    assert solucao.get_custo_total() == 0
    assert solucao.get_accoes() == []
    assert solucao.get_estados() == ["G"]


def test_lds_ids_estado_inicial_objetivo():
    problema = ProblemaGrafo({}, "G", "G")

    for solucao in [lds(problema, 0), ids(problema, 0)]:
        assert solucao is not None
        assert solucao.get_custo_total() == 0
        assert solucao.get_estados() == ["G"]


@pytest.mark.parametrize("algoritmo", [bfs, dfs, ucs])
def test_ciclos_nao_bloqueiam_busca(algoritmo):
    arestas = {
        "S": [("A", 1)],
        "A": [("S", 1), ("G", 1)]
    }

    problema = ProblemaGrafo(arestas, "S", "G")
    solucao = algoritmo(problema)

    assert solucao is not None
    assert solucao.get_custo_total() == 2


def test_lds_ids_com_ciclos():
    arestas = {
        "S": [("A", 1)],
        "A": [("S", 1), ("G", 1)]
    }

    problema = ProblemaGrafo(arestas, "S", "G")

    assert lds(problema, 2).get_custo_total() == 2
    assert ids(problema, 2).get_custo_total() == 2


@pytest.mark.parametrize("algoritmo", [lds, ids])
def test_limite_negativo(algoritmo, problema):
    with pytest.raises(ValueError):
        algoritmo(problema, -1)
