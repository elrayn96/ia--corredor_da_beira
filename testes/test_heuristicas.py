from itertools import pairwise, permutations
from math import isclose

from src.estado import Estado
from src.heuristicas.distancia import (
    h0,
    h1,
    matriz_distancias,
    tempo_a_velocidade_maxima,
)
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
            distancias[a][b] for a, b in pairwise(cidades)
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


def test_h2_calculo_conhecido():
    problema = ProblemaHeuristica()
    assert isclose(h2(Estado("B"), problema), 300.0)


def test_h2_inclui_a_localidade_actual_na_mst():
    problema = ProblemaHeuristica()
    grafo = problema.get_estradas()
    grafo["X"] = {}
    for cidade in ("A", "B", "C"):
        grafo["X"][cidade] = {"distancia": 1}
        grafo[cidade]["X"] = {"distancia": 1}

    # MST de {A, B, C} = 2 km; ao incluir X passa a 3 km.
    # h2 = 3/90*60 + duas descargas de 30 minutos = 62 minutos.
    assert isclose(h2(Estado("X"), problema), 62.0)


def test_h2_domina_h1():
    problema = ProblemaHeuristica()
    for local in problema.get_estradas():
        for concluidas in (set(), {"A"}, {"C"}, {"A", "C"}):
            estado = Estado(local, concluidas)
            assert h2(estado, problema) >= h1(estado, problema)


def test_h2_e_consistente_nas_transicoes_do_exemplo():
    problema = ProblemaHeuristica()
    grafo = problema.get_estradas()
    supermercados = set(problema.get_supermercados())

    for local in grafo:
        for concluidas in (set(), {"A"}, {"C"}, {"A", "C"}):
            estado = Estado(local, concluidas)
            valor_actual = h2(estado, problema)

            for vizinha, estrada in grafo[local].items():
                seguinte = Estado(vizinha, concluidas)
                custo = tempo_a_velocidade_maxima(estrada["distancia"])
                assert valor_actual <= custo + h2(seguinte, problema) + 1e-9

            if local in supermercados - concluidas:
                seguinte = Estado(local, concluidas | {local})
                assert valor_actual <= 30.0 + h2(seguinte, problema) + 1e-9


def test_h2_reutiliza_mst_para_o_mesmo_conjunto_de_vertices():
    problema = ProblemaHeuristica()
    h2(Estado("B", tempo=0, combustivel=300000), problema)
    quantidade_inicial = len(problema._cache_pesos_mst)

    h2(Estado("B", tempo=120, combustivel=100000), problema)

    assert len(problema._cache_pesos_mst) == quantidade_inicial


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
