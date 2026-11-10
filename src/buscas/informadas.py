"""Buscas informadas: Gulosa, A*, e A* Ponderada."""

import heapq
import time
from itertools import count

from src.solucao import Solucao


def _estado_inicial(problema):
    return problema.get_estado_inicial()

def _sucessores(problema, estado):
    return problema.get_sucessores(estado)

def _e_objectivo(problema, estado):
    return problema.teste_objectivo(estado)


"""Classe que representa um nó na árvore de busca."""
class _No:

    __slots__ = ("accao", "estado", "g", "pai")

    def __init__(self, estado, pai, accao, g):
        self.estado = estado
        self.pai = pai
        self.accao = accao
        self.g = g


"""Função que reconstrói o caminho"""
def _reconstruir(no):
    estados, accoes = [], []
    while no is not None:
        estados.append(no.estado)
        if no.pai is not None:
            accoes.append(no.accao)
        no = no.pai
    estados.reverse()
    accoes.reverse()
    return accoes, estados


"""Solução provisória. Usada enquanto não tiver src/solucao.py"""


def _criar_solução(accoes, estados, custo_total):
    return Solucao(accoes=accoes, estados=estados, custo_total=custo_total)


def _valor_h(heuristica, estado, problema):
    if heuristica is None:
        return 0
    return heuristica(estado, problema)


"""Busca de melhor-primeiro em grafo"""
def _melhor_primeiro(problema, heuristica, prioridade, reabrir, estatisticas):
    inicio = time.perf_counter()
    inicial = _estado_inicial(problema)
    h_ini = _valor_h(heuristica, inicial, problema)

    contador = count()
    raiz = _No(inicial, None, None, 0)
    fronteira = [(prioridade(0, h_ini), h_ini, next(contador), raiz)]
    g_melhor = {inicial: 0}
    expandidos = {}

    gerados = 1
    n_expandidos = 0
    max_fronteira = 1
    resultado = None

    while fronteira:
        _, _, _, no = heapq.heappop(fronteira)
        estado = no.estado

        if no.g > g_melhor[estado]:
            continue
        if estado in expandidos and expandidos[estado] <= no.g:
            continue

        if _e_objectivo(problema, estado):
            accoes, estados = _reconstruir(no)
            resultado = _criar_solução(accoes, estados, no.g)
            break

        expandidos[estado] = no.g
        n_expandidos += 1

        for accao, seguinte, custo in _sucessores(problema, estado):
            gerados += 1
            novo_g = no.g + custo
            if seguinte in g_melhor and (not reabrir or novo_g >= g_melhor[seguinte]):
                continue
            g_melhor[seguinte] = novo_g
            h = _valor_h(heuristica, seguinte, problema)
            novo = _No(seguinte, no, accao, novo_g)
            heapq.heappush(
                fronteira, (prioridade(novo_g, h), h, next(contador), novo)
            )

        max_fronteira = max(max_fronteira, len(fronteira))

    if estatisticas is not None:
        estatisticas["nos_gerados"] = gerados
        estatisticas["nos_expandidos"] = n_expandidos
        estatisticas["max_fronteira"] = max_fronteira
        estatisticas["tempo"] = time.perf_counter() - inicio
    return resultado


def busca_gulosa(problema, heuristica, estatisticas=None):
    return _melhor_primeiro(
        problema, heuristica, lambda g, h: h, False, estatisticas
    )

def a_star(problema, heuristica, estatisticas=None):
    return _melhor_primeiro(
        problema, heuristica, lambda g, h: g + h, True, estatisticas
    )

def a_star_ponderada(problema, heuristica, peso, estatisticas=None):
    if not isinstance(peso, (int, float)) or isinstance(peso, bool) or peso <= 0:
        raise ValueError("O peso da A* ponderada deve ser um número real positivo.")
    return _melhor_primeiro(
        problema, heuristica, lambda g, h: g + peso * h, True, estatisticas
    )