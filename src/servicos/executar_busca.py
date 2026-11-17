"""Serviço comum que liga configurações, domínio, buscas e métricas."""

from __future__ import annotations

import math
import threading
import time
import tracemalloc
from pathlib import Path

from src.buscas.informadas import a_star, a_star_ponderada, busca_gulosa
from src.buscas.nao_informadas import bfs, dfs, ids, lds, ucs
from src.gerador import carregar_json, carregar_rede, converter_para_busca
from src.heuristicas import h0, h1, h2
from src.problema import Problema

ALGORITMOS = {
    "bfs": bfs,
    "dfs": dfs,
    "lds": lds,
    "ids": ids,
    "ucs": ucs,
    "busca_gulosa": busca_gulosa,
    "a_star": a_star,
    "a_star_ponderada": a_star_ponderada,
}
HEURISTICAS = {"h0": h0, "h1": h1, "h2": h2}
INFORMADAS = {"busca_gulosa", "a_star", "a_star_ponderada"}
COM_LIMITE = {"dfs", "lds", "ids"}
LIMITE_EVENTOS_GUARDADOS = 1200


class BuscaCancelada(Exception):
    """Interrupção cooperativa solicitada pelo utilizador."""


def normalizar_configuracao(configuracao):
    """Valida o contrato partilhado sem depender de componentes Tkinter."""
    if not isinstance(configuracao, dict):
        raise TypeError("A configuração deve ser um dicionário.")
    obrigatorias = {
        "caminho_instancia",
        "algoritmo",
        "heuristica",
        "peso",
        "limite",
    }
    em_falta = sorted(obrigatorias - set(configuracao))
    if em_falta:
        raise ValueError(f"Configuração sem as chaves: {em_falta}")

    caminho = Path(configuracao["caminho_instancia"])
    if not caminho.is_file():
        raise ValueError("O ficheiro de instância não existe.")
    algoritmo = configuracao["algoritmo"]
    if algoritmo not in ALGORITMOS:
        raise ValueError(f"Algoritmo desconhecido: {algoritmo!r}")

    heuristica = configuracao["heuristica"] if algoritmo in INFORMADAS else None
    if algoritmo in INFORMADAS and heuristica not in HEURISTICAS:
        raise ValueError(f"Heurística desconhecida: {heuristica!r}")

    peso = configuracao["peso"] if algoritmo == "a_star_ponderada" else None
    if peso is not None:
        if isinstance(peso, bool) or not isinstance(peso, (int, float)):
            raise ValueError("O peso deve ser numérico.")
        peso = float(peso)
        if peso <= 0 or not math.isfinite(peso):
            raise ValueError("O peso deve ser finito e positivo.")

    limite = configuracao["limite"] if algoritmo in COM_LIMITE else None
    if limite is not None and (
        isinstance(limite, bool) or not isinstance(limite, int) or limite < 0
    ):
        raise ValueError("O limite deve ser um inteiro não negativo.")

    return {
        "caminho_instancia": str(caminho.resolve()),
        "algoritmo": algoritmo,
        "heuristica": heuristica,
        "peso": peso,
        "limite": limite,
    }


def carregar_problema(caminho_instancia):
    """Carrega tanto o formato gerado como o formato directo do domínio."""
    instancia = carregar_json(caminho_instancia)
    supermercados = instancia.get("supermercados")
    estradas = instancia.get("estradas")

    if isinstance(estradas, dict) and isinstance(supermercados, dict):
        dados = {"estradas": estradas, "supermercados": supermercados}
        origem = instancia.get("origem", "Beira")
    elif isinstance(supermercados, list):
        dados = converter_para_busca(instancia, carregar_rede())
        origem = instancia.get("estadoInicial", {}).get("localidade", "Beira")
    else:
        raise TypeError("Formato de instância não reconhecido.")
    return Problema(dados["estradas"], dados["supermercados"], origem)


def _executar_algoritmo(problema, configuracao, estatisticas, observador):
    algoritmo = configuracao["algoritmo"]
    funcao = ALGORITMOS[algoritmo]
    comuns = {"estatisticas": estatisticas, "observador": observador}
    if algoritmo in COM_LIMITE:
        return funcao(problema, configuracao["limite"], **comuns)
    if algoritmo == "a_star_ponderada":
        return funcao(
            problema,
            HEURISTICAS[configuracao["heuristica"]],
            configuracao["peso"],
            **comuns,
        )
    if algoritmo in INFORMADAS:
        return funcao(
            problema, HEURISTICAS[configuracao["heuristica"]], **comuns
        )
    return funcao(problema, **comuns)


def _metricas_vazias():
    return {
        "nos_gerados": 0,
        "nos_expandidos": 0,
        "max_fronteira": 0,
        "nos_reexpandidos": 0,
        "comprimento_caminho": 0,
        "tempo_segundos": 0.0,
        "memoria_pico_bytes": 0,
    }


def executar_busca(configuracao, observador=None, cancelar=None, limite_segundos=None):
    """Executa uma busca e devolve sempre o dicionário de resultado comum."""
    eventos = []
    estatisticas_brutas = {}
    metricas = _metricas_vazias()
    inicio = time.perf_counter()
    cancelar = cancelar if cancelar is not None else threading.Event()
    total_eventos = 0
    ultimo_estado = None
    contagem_eventos = {"gerar": 0, "expandir": 0}
    fronteira_observada = {"actual": 0, "maxima": 0}
    iniciou_tracemalloc = not tracemalloc.is_tracing()
    if iniciou_tracemalloc:
        tracemalloc.start()
    pico_inicial = tracemalloc.get_traced_memory()[1]

    def registar_evento(evento):
        nonlocal total_eventos, ultimo_estado
        if cancelar.is_set():
            raise BuscaCancelada("Busca cancelada pelo utilizador.")
        if limite_segundos is not None and time.perf_counter() - inicio > limite_segundos:
            raise BuscaCancelada("Tempo máximo de execução atingido.")
        total_eventos += 1
        tipo = evento.get("tipo")
        if evento.get("estado") is not None:
            ultimo_estado = evento["estado"]
        if tipo in contagem_eventos:
            contagem_eventos[tipo] += 1
        if tipo == "inicio":
            fronteira_observada["actual"] += 1
        elif tipo in {"expandir", "objectivo"}:
            fronteira_observada["actual"] = max(
                0, fronteira_observada["actual"] - 1
            )
        elif tipo in {"gerar", "reabrir"}:
            fronteira_observada["actual"] += 1
        fronteira_observada["maxima"] = max(
            fronteira_observada["maxima"], fronteira_observada["actual"]
        )
        # Mantém uma amostra inicial e os eventos mais recentes, sem memória ilimitada.
        if len(eventos) < LIMITE_EVENTOS_GUARDADOS:
            eventos.append(evento)
        elif evento.get("tipo") == "objectivo":
            eventos[-1] = evento
        if observador is not None:
            observador(evento)

    try:
        config = normalizar_configuracao(configuracao)
        problema = carregar_problema(config["caminho_instancia"])
        solucao = _executar_algoritmo(
            problema, config, estatisticas_brutas, registar_evento
        )
        estado_execucao = "concluida" if solucao is not None else "sem_solucao"
        mensagem = (
            "Solução encontrada."
            if solucao is not None
            else "A busca terminou sem encontrar solução."
        )
    except BuscaCancelada as erro:
        solucao = None
        estado_execucao = "interrompida"
        mensagem = str(erro)
        motivo_termino = (
            "limite_tempo"
            if mensagem == "Tempo máximo de execução atingido."
            else "cancelamento_utilizador"
        )
    except (OSError, ValueError, TypeError, KeyError) as erro:
        solucao = None
        estado_execucao = "erro"
        mensagem = str(erro)
    finally:
        tempo = time.perf_counter() - inicio
        pico_final = tracemalloc.get_traced_memory()[1]
        if iniciou_tracemalloc:
            tracemalloc.stop()

    metricas.update(
        {
            "nos_gerados": int(max(estatisticas_brutas.get("nos_gerados", 0),
                                   contagem_eventos["gerar"])),
            "nos_expandidos": int(max(estatisticas_brutas.get("nos_expandidos", 0),
                                     contagem_eventos["expandir"])),
            "max_fronteira": int(
                estatisticas_brutas.get("max_fronteira", 0)
                or fronteira_observada["maxima"]
            ),
            "nos_reexpandidos": int(
                estatisticas_brutas.get("nos_reexpandidos", 0)
            ),
            "comprimento_caminho": (
                0 if solucao is None else len(solucao.get_accoes())
            ),
            "tempo_segundos": float(tempo),
            "memoria_pico_bytes": int(max(0, pico_final - pico_inicial)),
        }
    )
    return {
        "solucao": solucao,
        "estatisticas": metricas,
        "eventos": eventos,
        "total_eventos": total_eventos,
        "estado_execucao": estado_execucao,
        "mensagem": mensagem,
        "motivo_termino": locals().get("motivo_termino"),
        "ultimo_estado": ultimo_estado,
    }
