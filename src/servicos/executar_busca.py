"""Ponto unico de execucao das procuras, independente da GUI."""
import time
import tracemalloc
from src.buscas import informadas, nao_informadas
from src.heuristicas.distancia import h0, h1
from src.heuristicas.mst import h2
from src.servicos.carregar_instancia import carregar_instancia
from src.servicos.validar_solucao import validar_solucao

HEURISTICAS = {"h0": h0, "h1": h1, "h2": h2}

def executar_busca(configuracao, observador=None):
    """Devolve solucao, estatisticas, eventos e estado_execucao."""
    configuracao = dict(configuracao)
    problema = configuracao.get("problema")
    if problema is None:
        problema = carregar_instancia(configuracao.get("instancia") or None)
    algoritmo = str(configuracao.get("algoritmo", "a_star")).lower()
    heuristica = HEURISTICAS.get(str(configuracao.get("heuristica", "h1")).lower())
    if heuristica is None:
        raise ValueError("Heuristica desconhecida")
    estatisticas = {}
    eventos = []
    def observar(evento):
        eventos.append(evento)
        if observador is not None:
            observador(evento)
    inicio = time.perf_counter()
    tracemalloc.start()
    try:
        if algoritmo in ("a_star", "astar", "a*"):
            solucao = informadas.a_star(problema, heuristica, estatisticas=estatisticas,
                                        **_observador_se_disponivel(informadas.a_star, observar))
        elif algoritmo in ("gulosa", "busca_gulosa"):
            solucao = informadas.busca_gulosa(problema, heuristica, estatisticas=estatisticas,
                                              **_observador_se_disponivel(informadas.busca_gulosa, observar))
        elif algoritmo in ("a_star_ponderada", "ponderada"):
            peso = float(configuracao.get("peso", 1.5))
            solucao = informadas.a_star_ponderada(problema, heuristica, peso,
                                                  estatisticas=estatisticas,
                                                  **_observador_se_disponivel(informadas.a_star_ponderada, observar))
        elif algoritmo in ("bfs", "dfs", "ucs", "ids"):
            if algoritmo == "ids":
                funcao = getattr(nao_informadas, "ids", None)
                if funcao is None:
                    raise ValueError("IDS nao disponivel nesta versao")
                solucao = funcao(problema, int(configuracao.get("limite_maximo", 15)))
            else:
                solucao = getattr(nao_informadas, algoritmo)(problema)
        else:
            raise ValueError(f"Algoritmo desconhecido: {algoritmo}")
        memoria_pico = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    estatisticas.setdefault("tempo_segundos", time.perf_counter() - inicio)
    estatisticas.setdefault("memoria_pico_bytes", memoria_pico)
    estatisticas.setdefault("expandidos", estatisticas.get("nos_expandidos"))
    estatisticas.setdefault("gerados", estatisticas.get("nos_gerados"))
    estado_execucao = "sem_solucao" if solucao is None else "concluido"
    if solucao is not None:
        validacao = validar_solucao(problema, solucao)
        if not validacao["valida"]:
            estado_execucao = "solucao_invalida"
        estatisticas["validacao"] = validacao
    return {"solucao": solucao, "estatisticas": estatisticas,
            "eventos": eventos, "estado_execucao": estado_execucao}

def _observador_se_disponivel(funcao, observador):
    import inspect
    return {"observador": observador} if "observador" in inspect.signature(funcao).parameters else {}
