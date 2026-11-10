
from collections import deque
from itertools import count
import heapq

from src.solucao import Solucao


def reconstruir_solucao(estado_final, predecessores, custo_total):
    acoes = []
    estados = []
    estado = estado_final

    while estado is not None:
        estados.append(estado)
        anterior = predecessores[estado]

        if anterior is not None:
            estado_pai, accao = anterior
            acoes.append(accao)
            estado = estado_pai
        else:
            estado = None

    estados.reverse()
    acoes.reverse()

    return Solucao(acoes, estados, custo_total)


def bfs(problema):
    estado_inicial = problema.get_estado_inicial()

    fila = deque([estado_inicial])
    visitados = {estado_inicial}
    predecessores = {estado_inicial: None}
    custos = {estado_inicial: 0}

    while fila:
        estado_actual = fila.popleft()

        if problema.teste_objectivo(estado_actual):
            return reconstruir_solucao(
                estado_actual,
                predecessores,
                custos[estado_actual]
            )

        for accao, estado_seguinte, custo in problema.get_sucessores(estado_actual):
            if estado_seguinte not in visitados:
                visitados.add(estado_seguinte)
                predecessores[estado_seguinte] = (estado_actual, accao)
                custos[estado_seguinte] = custos[estado_actual] + custo
                fila.append(estado_seguinte)

    return None


def dfs(problema):
    estado_inicial = problema.get_estado_inicial()

    pilha = [estado_inicial]
    visitados = set()
    predecessores = {estado_inicial: None}
    custos = {estado_inicial: 0}

    while pilha:
        estado_actual = pilha.pop()

        if estado_actual in visitados:
            continue

        visitados.add(estado_actual)

        if problema.teste_objectivo(estado_actual):
            return reconstruir_solucao(
                estado_actual,
                predecessores,
                custos[estado_actual]
            )

        for accao, estado_seguinte, custo in reversed(
            problema.get_sucessores(estado_actual)
        ):
            if (
                estado_seguinte not in visitados
                and estado_seguinte not in predecessores
            ):
                predecessores[estado_seguinte] = (estado_actual, accao)
                custos[estado_seguinte] = custos[estado_actual] + custo
                pilha.append(estado_seguinte)

    return None


def lds(problema, limite):
    if limite < 0:
        raise ValueError("O limite nao pode ser negativo")

    estado_inicial = problema.get_estado_inicial()
    pilha = [(estado_inicial, 0, [], [estado_inicial], 0)]

    while pilha:
        estado_actual, profundidade, acoes, estados, custo_total = pilha.pop()

        if problema.teste_objectivo(estado_actual):
            return Solucao(acoes, estados, custo_total)

        if profundidade >= limite:
            continue

        sucessores = problema.get_sucessores(estado_actual)

        for accao, estado_seguinte, custo in reversed(sucessores):
            if estado_seguinte not in estados:
                novas_acoes = acoes + [accao]
                novos_estados = estados + [estado_seguinte]
                novo_custo = custo_total + custo

                pilha.append((
                    estado_seguinte,
                    profundidade + 1,
                    novas_acoes,
                    novos_estados,
                    novo_custo
                ))

    return None


def ids(problema, limite_maximo):
    if limite_maximo < 0:
        raise ValueError("O limite maximo nao pode ser negativo")

    for limite in range(limite_maximo + 1):
        solucao = lds(problema, limite)

        if solucao is not None:
            return solucao

    return None


def ucs(problema):
    estado_inicial = problema.get_estado_inicial()

    fila_prioridade = []
    contador = count()

    heapq.heappush(
        fila_prioridade,
        (0, next(contador), estado_inicial)
    )

    custos = {estado_inicial: 0}
    predecessores = {estado_inicial: None}

    while fila_prioridade:
        custo_actual, _, estado_actual = heapq.heappop(fila_prioridade)

        if custo_actual > custos[estado_actual]:
            continue

        if problema.teste_objectivo(estado_actual):
            return reconstruir_solucao(
                estado_actual,
                predecessores,
                custo_actual
            )

        for accao, estado_seguinte, custo in problema.get_sucessores(estado_actual):
            novo_custo = custo_actual + custo

            if (
                estado_seguinte not in custos
                or novo_custo < custos[estado_seguinte]
            ):
                custos[estado_seguinte] = novo_custo
                predecessores[estado_seguinte] = (estado_actual, accao)

                heapq.heappush(
                    fila_prioridade,
                    (novo_custo, next(contador), estado_seguinte)
                )

    return None
