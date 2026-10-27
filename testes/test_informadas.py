"""Testes das buscas informadas"""

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


