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


def _peso_mst_em_cache(problema, vertices: set[str]) -> float:
    """Reutiliza a MST para conjuntos de localidades já avaliados.

    O estado também contém tempo e combustível, por isso a busca pode chegar
    muitas vezes ao mesmo conjunto de localidades relevantes. A MST depende
    apenas desse conjunto e da rede rodoviária, não dos restantes campos do
    estado.
    """
    cache = getattr(problema, "_cache_pesos_mst", None)
    if cache is None:
        cache = {}
        problema._cache_pesos_mst = cache

    chave = frozenset(vertices)
    if chave not in cache:
        cache[chave] = peso_mst(vertices, matriz_distancias(problema))
    return cache[chave]


def h2(estado, problema) -> float:
    """Combina h1, MST e o tempo obrigatório das descargas pendentes.

    O enunciado pede a MST das cidades pendentes e da Beira. Incluímos também
    a localidade actual: toda solução precisa de ligar esse ponto aos restantes,
    portanto a estimativa continua admissível e pode ficar mais informada.

    O máximo entre h1 e a MST reúne dois limites inferiores para a viagem. Ao
    resultado soma-se a duração obrigatória de cada descarga pendente.
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
        _peso_mst_em_cache(problema, vertices)
    )
    duracao_entrega = float(getattr(problema, "DURACAO_ENTREGA", 30.0))
    descargas = duracao_entrega * len(pendentes)
    return max(h1(estado, problema), mst_minutos) + descargas
