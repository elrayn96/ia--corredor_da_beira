"""A interface isola a busca num processo compatível com o Windows."""

import multiprocessing
import queue
from pathlib import Path

from src.interface.janela_principal import _executar_em_processo


def test_processo_de_busca_devolve_progresso_e_resultado():
    raiz = Path(__file__).resolve().parents[1]
    configuracao = {
        "caminho_instancia": str(
            raiz / "dados" / "instancias_experimentais" / "pequena_01.json"
        ),
        "algoritmo": "a_star",
        "heuristica": "h2",
        "peso": None,
        "limite": None,
        "limite_segundos": 10,
    }
    contexto = multiprocessing.get_context("spawn")
    fila = contexto.Queue(maxsize=48)
    cancelar = contexto.Event()
    processo = contexto.Process(
        target=_executar_em_processo,
        args=(configuracao, fila, cancelar),
    )
    processo.start()
    resultado = None
    while resultado is None:
        try:
            tipo, _configuracao, conteudo = fila.get(timeout=15)
        except queue.Empty:
            processo.terminate()
            processo.join(timeout=2)
            raise AssertionError("O processo não devolveu resultado") from None
        if tipo == "resultado":
            resultado = conteudo
        elif tipo == "falha":
            raise AssertionError(conteudo)
    processo.join(timeout=5)

    assert not processo.is_alive()
    assert resultado["estado_execucao"] == "concluida"
    assert resultado["solucao"] is not None


def test_processo_pode_ser_cancelado_sem_bloquear_interface():
    raiz = Path(__file__).resolve().parents[1]
    configuracao = {
        "caminho_instancia": str(
            raiz / "dados" / "instancias_experimentais" / "media_01.json"
        ),
        "algoritmo": "bfs",
        "heuristica": "h0",
        "peso": None,
        "limite": None,
        "limite_segundos": 60,
    }
    contexto = multiprocessing.get_context("spawn")
    fila = contexto.Queue(maxsize=48)
    cancelar = contexto.Event()
    processo = contexto.Process(
        target=_executar_em_processo,
        args=(configuracao, fila, cancelar),
    )
    processo.start()
    resultado = None
    while resultado is None:
        try:
            tipo, _configuracao, conteudo = fila.get(timeout=15)
        except queue.Empty:
            processo.terminate()
            processo.join(timeout=2)
            raise AssertionError("O cancelamento não devolveu resultado") from None
        if tipo == "progresso":
            cancelar.set()
        elif tipo == "resultado":
            resultado = conteudo
        elif tipo == "falha":
            raise AssertionError(conteudo)
    processo.join(timeout=5)

    assert not processo.is_alive()
    assert resultado["estado_execucao"] == "interrompida"
    assert resultado["motivo_termino"] == "cancelamento_utilizador"
    assert resultado["ultimo_estado"] is not None
