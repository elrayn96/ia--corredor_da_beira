"""Buscas informadas: Gulosa, A*, e A* Ponderada."""

import heapq
import time
from collections.abc import Callable
from itertools import count
from typing import NamedTuple

from src.buscas.eventos_busca import emitir_evento
from src.solucao import Solucao


def _estado_inicial(problema):
    return problema.get_estado_inicial()

def _sucessores(problema, estado):
    return problema.get_sucessores(estado)

def _e_objectivo(problema, estado):
    return problema.teste_objectivo(estado)

def _criar_solucao(accoes, estados, custo_total):
    return Solucao(accoes=accoes, estados=estados, custo_total=custo_total)

def _valor_h(heuristica, estado, problema):
    if heuristica is None:
        return 0
    return heuristica(estado, problema)


"""Classe que representa um nó na árvore de busca."""
class _No:

    __slots__ = ("accao", "estado", "g", "no_id", "pai", "profundidade")

    def __init__(self, estado, pai, accao, g, no_id):
        self.estado = estado
        self.pai = pai
        self.accao = accao
        self.g = g
        self.no_id = no_id
        self.profundidade = 0 if pai is None else pai.profundidade +1


class _Estrategia(NamedTuple):
    #Como a busca ordena a fronteira e se reabre estados ja vistos

    prioridade: Callable[[float, float], float]
    reabrir: bool


class _Emissor:
    #Cria e emite os eventos da busca

    def __init__(self, observador):
        self.observador = observador
        self.passo = 0

    @property
    def activo(self):
        return self.observador is not None
    
    def emitir(self, tipo, no, h, f):
        if self.observador is None:
            return
        evento = {
            "tipo": tipo,
            "passo": self.passo,
            "no_id": no.no_id,
            "pai_id": None if no.pai is None else no.pai.no_id,
            "estado": no.estado,
            "accao": no.accao,
            "profundidade": no.profundidade,
            "g": no.g,
            "h": h,
            "f": f
        }
        self.passo += 1
        emitir_evento(self.observador, evento)

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


def _registar_estatisticas(estatisticas, gerados, n_expandidos, max_fronteira, inicio):
    if estatisticas is None:
        return
    estatisticas["nos_gerados"] = gerados
    estatisticas["nos_expandidos"] = n_expandidos
    estatisticas["max_fronteira"] = max_fronteira
    estatisticas["tempo"] = time.perf_counter() - inicio


"""Busca de melhor-primeiro em grafo"""
def _melhor_primeiro(problema, heuristica, estrategia, estatisticas, observador):
    inicio = time.perf_counter()
    emissor = _Emissor(observador)
    ids = count()
    contador = count()

    inicial = _estado_inicial(problema)
    h_ini = _valor_h(heuristica, inicial, problema)
    f_ini = estrategia.prioridade(0, h_ini)

    
    raiz = _No(inicial, None, None, 0, next(ids))
    emissor.emitir("inicio", raiz, h_ini, f_ini)
    
    fronteira = [(f_ini, h_ini, next(contador), raiz)]
    g_melhor = {inicial: 0}
    expandidos = {}

    gerados = 1
    n_expandidos = 0
    max_fronteira = 1
    resultado = None

    while fronteira:
        f, h, _, no = heapq.heappop(fronteira)
        estado = no.estado

        obsoleto = no.g > g_melhor[estado]
        if obsoleto or (estado in expandidos and expandidos[estado] <= no.g):
            emissor.emitir("descartar", no, h, f)
            continue
        if estado in expandidos and expandidos[estado] <= no.g:
            continue

        if _e_objectivo(problema, estado):
            emissor.emitir("objectivo", no, h, f)
            accoes, estados = _reconstruir(no)
            resultado = _criar_solucao(accoes, estados, no.g)
            break

        emissor.emitir("expandir", no, h, f)
        expandidos[estado] = no.g
        n_expandidos += 1

        for accao, seguinte, custo in _sucessores(problema, estado):
            gerados += 1
            novo_g = no.g + custo
            novo = _No(seguinte, no, accao, novo_g, next(ids))
            ja_visto = seguinte in g_melhor
            if ja_visto and (not estrategia.reabrir or novo_g >= g_melhor[seguinte]):
                if emissor.activo:
                    h_seg  = _valor_h(heuristica, seguinte, problema)
                    f_seg = estrategia.prioridade(novo_g, h_seg)
                    emissor.emitir("descartar", novo, h_seg, f_seg)
                continue
            g_melhor[seguinte] = novo_g
            h_seg = _valor_h(heuristica, seguinte, problema)
            f_seg = estrategia.prioridade(novo_g, h_seg)
            emissor.emitir("reabrir" if ja_visto else "gerar", novo, h_seg, f_seg)
            heapq.heappush(fronteira, (f_seg, h_seg, next(contador), novo))

        max_fronteira = max(max_fronteira, len(fronteira))

    _registar_estatisticas(estatisticas, gerados, n_expandidos, max_fronteira, inicio)
    return resultado


def busca_gulosa(problema, heuristica, estatisticas=None, observador=None):
    estrategia = _Estrategia(lambda g, h: h, False)
    return _melhor_primeiro(problema, heuristica, estrategia, estatisticas, observador)

def a_star(problema, heuristica, estatisticas=None, observador=None):
    estrategia = _Estrategia(lambda g, h: g + h, True) 
    return _melhor_primeiro(problema, heuristica, estrategia, estatisticas, observador)

def a_star_ponderada(problema, heuristica, peso, estatisticas=None, observador=None):
    if not isinstance(peso, (int, float)) or isinstance(peso, bool) or peso <= 0:
        raise ValueError("O peso da A* ponderada deve ser um número real positivo.")
    estrategia = _Estrategia(lambda g, h: g + peso * h, True)
    return _melhor_primeiro(
        problema, heuristica, estrategia, estatisticas, observador
    )