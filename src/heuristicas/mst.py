"""Heurística h2 baseada numa árvore geradora mínima."""

from __future__ import annotations

from math import inf

from src.heuristicas.distancia import (
    entregas_concluidas,
    h1,
    localidade_do_estado,
    matriz_distancias,
    origem_do_problema,
    supermercados_do_problema,
    tempo_a_velocidade_maxima,
)


def peso_mst(
    vertices: set[str],
    distancias: dict[str, dict[str, float]],
) -> float:
    """Calcula com Prim o peso da MST no fecho métrico das localidades."""
    if len(vertices) <= 1:
        return 0.0

    inicio = next(iter(vertices))
    visitados = {inicio}
    melhor = {v: distancias[inicio][v] for v in vertices - visitados}
    total = 0.0

    while len(visitados) < len(vertices):
        candidato = min(
            (v for v in vertices if v not in visitados),
            key=lambda v: melhor.get(v, inf),
        )
        peso = melhor.get(candidato, inf)
        if peso == inf:
            return inf
        total += peso
        visitados.add(candidato)
        for vertice in vertices - visitados:
            melhor[vertice] = min(
                melhor.get(vertice, inf),
                distancias[candidato][vertice],
            )
    return total


def h2(estado, problema) -> float:
    """Combina h1, MST e o tempo obrigatório das descargas pendentes.

    Toda rota completa liga a localidade actual, os clientes pendentes e a
    Beira; portanto, a MST desses vértices limita inferiormente a distância.
    Somam-se 30 minutos por entrega, um custo obrigatório e independente da
    viagem. O máximo entre h1 e MST preserva admissibilidade e faz h2 dominar
    h1 antes de acrescentar as descargas.
    """
    pendentes = (
        set(supermercados_do_problema(problema))
        - entregas_concluidas(estado)
    )
    vertices = pendentes | {
        localidade_do_estado(estado),
        origem_do_problema(problema),
    }
    mst_minutos = tempo_a_velocidade_maxima(
        peso_mst(vertices, matriz_distancias(problema))
    )
    descargas = 30.0 * len(pendentes)
    return max(h1(estado, problema), mst_minutos) + descargas
