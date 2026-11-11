"""Heurísticas h0 e h1 baseadas em menores distâncias rodoviárias."""

from __future__ import annotations

import heapq
from math import inf

VELOCIDADE_MAXIMA_KMH = 90.0


def tempo_a_velocidade_maxima(distancia_km: float) -> float:
    """Converte quilómetros em minutos usando a velocidade mais favorável."""
    return float(distancia_km) / VELOCIDADE_MAXIMA_KMH * 60.0


def _valor(objeto, atributo: str, getter: str):
    """Aceita tanto a interface por atributos como a interface por getters."""
    if hasattr(objeto, atributo):
        return getattr(objeto, atributo)
    return getattr(objeto, getter)()


def localidade_do_estado(estado) -> str:
    return _valor(estado, "localidade", "get_localidade")


def entregas_concluidas(estado) -> set[str]:
    return set(_valor(estado, "entregas_concluidas", "get_entregas_concluidas"))


def origem_do_problema(problema) -> str:
    return _valor(problema, "origem", "get_origem")


def supermercados_do_problema(problema) -> dict:
    return dict(_valor(problema, "supermercados", "get_supermercados"))


def estradas_do_problema(problema) -> dict:
    return _valor(problema, "estradas", "get_estradas")


def menores_distancias(grafo: dict, origem: str) -> dict[str, float]:
    """Calcula por Dijkstra as menores distâncias em quilómetros."""
    distancias = {cidade: inf for cidade in grafo}
    distancias[origem] = 0.0
    fronteira = [(0.0, origem)]

    while fronteira:
        distancia, cidade = heapq.heappop(fronteira)
        if distancia != distancias[cidade]:
            continue
        for vizinha, estrada in grafo[cidade].items():
            nova = distancia + float(estrada["distancia"])
            if nova < distancias[vizinha]:
                distancias[vizinha] = nova
                heapq.heappush(fronteira, (nova, vizinha))
    return distancias


def matriz_distancias(problema) -> dict[str, dict[str, float]]:
    """Obtém o fecho métrico do grafo e reutiliza-o nas avaliações seguintes."""
    cache = getattr(problema, "_cache_distancias", None)
    if cache is None:
        grafo = estradas_do_problema(problema)
        cache = {
            cidade: menores_distancias(grafo, cidade)
            for cidade in grafo
        }
        problema._cache_distancias = cache
    return cache


def h0(estado, problema=None) -> float:
    """Heurística nula, equivalente à procura de custo uniforme."""
    return 0.0


def h1(estado, problema) -> float:
    """Estima o maior percurso obrigatório actual-cliente-Beira.

    Para cada entrega pendente ``c``, qualquer solução precisa de alcançar ``c``
    e terminar na Beira. Logo, ``d(actual,c) + d(c,Beira)`` é um limite
    inferior. O máximo destes limites continua admissível. Distâncias são
    convertidas em minutos a 90 km/h; esperas, descargas, combustível e outras
    restrições são ignorados deliberadamente.
    """
    distancias = matriz_distancias(problema)
    actual = localidade_do_estado(estado)
    base = origem_do_problema(problema)
    pendentes = (
        set(supermercados_do_problema(problema))
        - entregas_concluidas(estado)
    )

    if not pendentes:
        return tempo_a_velocidade_maxima(distancias[actual][base])

    quilometros = max(
        distancias[actual][cliente] + distancias[cliente][base]
        for cliente in pendentes
    )
    return tempo_a_velocidade_maxima(quilometros)
