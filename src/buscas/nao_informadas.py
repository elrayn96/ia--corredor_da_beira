"""Buscas não informadas com métricas e eventos opcionais."""

from __future__ import annotations

import heapq
import time
from collections import deque
from itertools import count

from src.buscas.eventos_busca import emitir_evento
from src.contrato_busca import No, caminho, e_objectivo, estado_inicial, sucessores
from src.solucao import Solucao


class _Emissor:
    def __init__(self, observador):
        self.observador = observador
        self.passo = 0

    def emitir(self, tipo, no):
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
            "h": 0,
            "f": no.g,
        }
        self.passo += 1
        emitir_evento(self.observador, evento)


def _solucao(no):
    nos = caminho(no)
    return Solucao([item.accao for item in nos[1:]],
                   [item.estado for item in nos], no.g)


def _registar(estatisticas, contadores, inicio):
    if estatisticas is None:
        return
    estatisticas.update(
        {
            "nos_gerados": contadores["gerados"],
            "nos_expandidos": contadores["expandidos"],
            "max_fronteira": contadores["max_fronteira"],
            "nos_reexpandidos": contadores["reexpandidos"],
            "tempo": time.perf_counter() - inicio,
        }
    )


def _novo_contador():
    return {
        "gerados": 0, "expandidos": 0, "max_fronteira": 0,
        "reexpandidos": 0, "estados_expandidos": set(),
    }


def bfs(problema, estatisticas=None, observador=None):
    """Busca em largura com teste de objectivo na geração."""
    inicio = time.perf_counter()
    ids = count()
    emissor = _Emissor(observador)
    contadores = _novo_contador()
    raiz = No(estado_inicial(problema), None, None, 0, next(ids))
    fronteira = deque([raiz])
    visitados = {raiz.estado}
    contadores.update(gerados=1, max_fronteira=1)
    emissor.emitir("inicio", raiz)

    if e_objectivo(problema, raiz.estado):
        emissor.emitir("objectivo", raiz)
        _registar(estatisticas, contadores, inicio)
        return _solucao(raiz)

    while fronteira:
        no = fronteira.popleft()
        emissor.emitir("expandir", no)
        contadores["expandidos"] += 1
        for accao, seguinte, custo in sucessores(problema, no.estado):
            novo = No(seguinte, no, accao, no.g + custo, next(ids))
            contadores["gerados"] += 1
            if seguinte in visitados:
                emissor.emitir("descartar", novo)
                continue
            visitados.add(seguinte)
            emissor.emitir("gerar", novo)
            if e_objectivo(problema, seguinte):
                emissor.emitir("objectivo", novo)
                _registar(estatisticas, contadores, inicio)
                return _solucao(novo)
            fronteira.append(novo)
        contadores["max_fronteira"] = max(
            contadores["max_fronteira"], len(fronteira)
        )

    _registar(estatisticas, contadores, inicio)
    return None


def dfs(problema, limite=None, estatisticas=None, observador=None):
    """DFS com controlo de ciclos no caminho e limite configurável."""
    if limite is not None and limite < 0:
        raise ValueError("O limite não pode ser negativo")
    inicio = time.perf_counter()
    ids = count()
    emissor = _Emissor(observador)
    contadores = _novo_contador()
    raiz = No(estado_inicial(problema), None, None, 0, next(ids))
    fronteira = [raiz]
    contadores.update(gerados=1, max_fronteira=1)
    emissor.emitir("inicio", raiz)

    while fronteira:
        no = fronteira.pop()
        if e_objectivo(problema, no.estado):
            emissor.emitir("objectivo", no)
            _registar(estatisticas, contadores, inicio)
            return _solucao(no)
        if limite is not None and no.profundidade >= limite:
            emissor.emitir("descartar", no)
            continue
        emissor.emitir("expandir", no)
        contadores["expandidos"] += 1

        for accao, seguinte, custo in reversed(list(sucessores(problema, no.estado))):
            novo = No(seguinte, no, accao, no.g + custo, next(ids))
            contadores["gerados"] += 1
            if _contem_no_caminho(no, seguinte):
                emissor.emitir("descartar", novo)
                continue
            emissor.emitir("gerar", novo)
            fronteira.append(novo)
        contadores["max_fronteira"] = max(
            contadores["max_fronteira"], len(fronteira)
        )

    _registar(estatisticas, contadores, inicio)
    return None


def _contem_no_caminho(no, estado):
    while no is not None:
        if no.estado == estado:
            return True
        no = no.pai
    return False


def _busca_limitada(problema, limite, emissor, ids, contadores):
    raiz = No(estado_inicial(problema), None, None, 0, next(ids))
    fronteira = [raiz]
    menor_profundidade = {raiz.estado: 0}
    contadores["gerados"] += 1
    contadores["max_fronteira"] = max(contadores["max_fronteira"], 1)
    emissor.emitir("inicio", raiz)

    while fronteira:
        no = fronteira.pop()
        if no.profundidade > menor_profundidade.get(no.estado, no.profundidade):
            emissor.emitir("descartar", no)
            continue
        if e_objectivo(problema, no.estado):
            emissor.emitir("objectivo", no)
            return no
        if no.profundidade >= limite:
            emissor.emitir("descartar", no)
            continue

        emissor.emitir("expandir", no)
        if no.estado in contadores["estados_expandidos"]:
            contadores["reexpandidos"] += 1
        contadores["estados_expandidos"].add(no.estado)
        contadores["expandidos"] += 1
        for accao, seguinte, custo in reversed(list(sucessores(problema, no.estado))):
            novo = No(seguinte, no, accao, no.g + custo, next(ids))
            contadores["gerados"] += 1
            if _contem_no_caminho(no, seguinte):
                emissor.emitir("descartar", novo)
                continue
            if menor_profundidade.get(seguinte, novo.profundidade + 1) <= novo.profundidade:
                emissor.emitir("descartar", novo)
                continue
            menor_profundidade[seguinte] = novo.profundidade
            emissor.emitir("gerar", novo)
            fronteira.append(novo)
        contadores["max_fronteira"] = max(
            contadores["max_fronteira"], len(fronteira)
        )
    return None


def lds(problema, limite, estatisticas=None, observador=None):
    if limite < 0:
        raise ValueError("O limite não pode ser negativo")
    inicio = time.perf_counter()
    contadores = _novo_contador()
    no = _busca_limitada(
        problema, limite, _Emissor(observador), count(), contadores
    )
    _registar(estatisticas, contadores, inicio)
    return None if no is None else _solucao(no)


def ids(problema, limite_maximo, estatisticas=None, observador=None):
    if limite_maximo < 0:
        raise ValueError("O limite máximo não pode ser negativo")
    inicio = time.perf_counter()
    contadores = _novo_contador()
    emissor = _Emissor(observador)
    ids_nos = count()
    for limite in range(limite_maximo + 1):
        no = _busca_limitada(problema, limite, emissor, ids_nos, contadores)
        if no is not None:
            _registar(estatisticas, contadores, inicio)
            return _solucao(no)
    _registar(estatisticas, contadores, inicio)
    return None


def ucs(problema, estatisticas=None, observador=None):
    """Busca de custo uniforme com descarte de entradas obsoletas."""
    inicio = time.perf_counter()
    ids = count()
    desempate = count()
    emissor = _Emissor(observador)
    contadores = _novo_contador()
    raiz = No(estado_inicial(problema), None, None, 0, next(ids))
    fronteira = [(0, next(desempate), raiz)]
    custos = {raiz.estado: 0}
    contadores.update(gerados=1, max_fronteira=1)
    emissor.emitir("inicio", raiz)

    while fronteira:
        custo_actual, _, no = heapq.heappop(fronteira)
        if custo_actual > custos[no.estado]:
            emissor.emitir("descartar", no)
            continue
        if e_objectivo(problema, no.estado):
            emissor.emitir("objectivo", no)
            _registar(estatisticas, contadores, inicio)
            return _solucao(no)
        emissor.emitir("expandir", no)
        contadores["expandidos"] += 1

        for accao, seguinte, custo in sucessores(problema, no.estado):
            novo_g = no.g + custo
            novo = No(seguinte, no, accao, novo_g, next(ids))
            contadores["gerados"] += 1
            if novo_g >= custos.get(seguinte, float("inf")):
                emissor.emitir("descartar", novo)
                continue
            reabrir = seguinte in custos
            custos[seguinte] = novo_g
            emissor.emitir("reabrir" if reabrir else "gerar", novo)
            heapq.heappush(fronteira, (novo_g, next(desempate), novo))
        contadores["max_fronteira"] = max(
            contadores["max_fronteira"], len(fronteira)
        )

    _registar(estatisticas, contadores, inicio)
    return None
