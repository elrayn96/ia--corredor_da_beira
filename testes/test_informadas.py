"""Testes unitários das buscas informadas"""

import pytest

from src.buscas.informadas import aStar, aStarPonderada, buscaGulosa

class ProblemaGrafo:

    def __init__(self, arestas, inicio, objetivo):
        self.arestas = arestas
        self.inicio = inicio
        self.objetivo = objetivo

    def getEstadoInicial(self):
        return self.inicio

    def getSucessores(self, estado):
        return [
            (f"{estado}->{v}", v, c) for v, c in self.arestas.get(estado, [])
        ]

    def testeObjectivo(self, estado):
        return estado == self.objetivo
    

# No final deve dar:
# S->A (1), A->G (10)  : Custo 11
# S->B (4), B->G (3)   : Custo 7 (optimo)

ARESTAS = {"S": [("A", 1), ("B", 4)], "A": [("G",10)], "B": [("G", 3)]}
H_TABELA = {"S": 7, "A": 1, "B": 3, "G": 6}


def h0(estado, problema):
    return 0

def h_admissivel(estado, problema):
    return H_TABELA[estado]

@pytest.fixture
def problema():
    return ProblemaGrafo(ARESTAS, "S", "G")

def test_astar_h0_encontra_optimo(problema):
    sol = aStar(problema, h0)
    assert sol.custo_total == 7
    assert sol.estados == ["S", "B", "G"]

