from itertools import permutations
from math import isclose

from src.estado import Estado
from src.heuristicas.distancia import h0, h1, matriz_distancias
from src.heuristicas.mst import h2, peso_mst


class ProblemaHeuristica:
    def __init__(self):
        self._origem = "B"
        self._supermercados = {"A": {}, "C": {}}
        self._estradas = {
            "B": {"A": {"distancia": 90}, "C": {"distancia": 300}},
            "A": {"B": {"distancia": 90}, "C": {"distancia": 90}},
            "C": {"A": {"distancia": 90}, "B": {"distancia": 300}},
        }
        self._cache_distancias = None

    def get_origem(self):
        return self._origem

    def get_supermercados(self):
        return dict(self._supermercados)

    def get_estradas(self):
        return self._estradas


def custo_optimo_restante(estado, problema):
    distancias = matriz_distancias(problema)
    local = estado.get_localidade()
    base = problema.get_origem()
    pendentes = set(problema.get_supermercados()) - estado.get_entregas_concluidas()
    if not pendentes:
        return distancias[local][base] / 90 * 60

    melhor = float("inf")
    for ordem in permutations(pendentes):
        cidades = (local,) + ordem + (base,)
        quilometros = sum(
            distancias[a][b] for a, b in zip(cidades, cidades[1:])
        )
        melhor = min(melhor, quilometros / 90 * 60)
    return melhor + 30 * len(pendentes)


def test_h0_e_zero():
    assert h0(Estado("B")) == 0.0


def test_dijkstra_prefere_caminho_indirecto_mais_curto():
    problema = ProblemaHeuristica()
    distancias = matriz_distancias(problema)
    assert distancias["B"]["C"] == 180


def test_h1_calculo_conhecido():
    problema = ProblemaHeuristica()
    assert isclose(h1(Estado("B"), problema), 240.0)


def test_h1_sem_pendentes_estima_apenas_regresso():
    problema = ProblemaHeuristica()
    estado = Estado("A", {"A", "C"})
    assert isclose(h1(estado, problema), 60.0)


def test_peso_mst_conhecido():
    problema = ProblemaHeuristica()
    distancias = matriz_distancias(problema)
    assert peso_mst({"A", "B", "C"}, distancias) == 180


def test_h2_domina_h1():
    problema = ProblemaHeuristica()
    for local in problema.get_estradas():
        for concluidas in (set(), {"A"}, {"C"}, {"A", "C"}):
            estado = Estado(local, concluidas)
            assert h2(estado, problema) >= h1(estado, problema)


def test_admissibilidade_em_todos_os_estados_do_exemplo():
    problema = ProblemaHeuristica()
    for local in problema.get_estradas():
        for concluidas in (set(), {"A"}, {"C"}, {"A", "C"}):
            estado = Estado(local, concluidas)
            optimo = custo_optimo_restante(estado, problema)
            assert h1(estado, problema) <= optimo + 1e-9
            assert h2(estado, problema) <= optimo + 1e-9


def test_objectivo_tem_heuristicas_zero():
    problema = ProblemaHeuristica()
    objectivo = Estado("B", {"A", "C"})
    assert h1(objectivo, problema) == 0.0
    assert h2(objectivo, problema) == 0.0
