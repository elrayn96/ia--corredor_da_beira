"""Regressões do cancelamento cooperativo e do limite dos eventos."""

import threading
import time

from src.estado import Estado
from src.servicos import executar_busca as modulo


def _config(tmp_path):
    caminho = tmp_path / "caso.json"
    caminho.write_text("{}", encoding="utf-8")
    return {
        "caminho_instancia": str(caminho),
        "algoritmo": "bfs",
        "heuristica": "h0",
        "peso": None,
        "limite": None,
    }


def test_cancelamento_por_evento(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo, "carregar_problema", lambda _: object())

    def fake_execucao(_problema, _configuracao, _estatisticas, observador):
        for i in range(3000):
            observador({
                "tipo": "expandir", "no_id": i,
                "estado": Estado("Dondo", tempo=i, combustivel=200),
            })

    monkeypatch.setattr(modulo, "_executar_algoritmo", fake_execucao)
    parar = threading.Event()
    observados = []

    def acompanhar(evento):
        observados.append(evento)
        if len(observados) == 4:
            parar.set()

    resultado = modulo.executar_busca(
        _config(tmp_path), observador=acompanhar, cancelar=parar
    )
    assert resultado["estado_execucao"] == "interrompida"
    assert resultado["motivo_termino"] == "cancelamento_utilizador"
    assert resultado["ultimo_estado"].get_localidade() == "Dondo"
    assert len(observados) == 4
    assert resultado["estatisticas"]["nos_expandidos"] == 4


def test_eventos_sao_limitados_sem_perder_contagem(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo, "carregar_problema", lambda _: object())

    def fake_execucao(_problema, _configuracao, _estatisticas, observador):
        for i in range(1600):
            observador({"tipo": "gerar", "no_id": i})

    monkeypatch.setattr(modulo, "_executar_algoritmo", fake_execucao)
    resultado = modulo.executar_busca(_config(tmp_path))
    assert resultado["estado_execucao"] == "sem_solucao"
    assert resultado["total_eventos"] == 1600
    assert len(resultado["eventos"]) == modulo.LIMITE_EVENTOS_GUARDADOS
    assert resultado["estatisticas"]["nos_gerados"] == 1600


def test_limite_tempo_guarda_motivo_e_ultimo_estado(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo, "carregar_problema", lambda _: object())

    def fake_execucao(_problema, _configuracao, _estatisticas, observador):
        observador({"tipo": "expandir", "estado": Estado("Inchope")})
        time.sleep(0.003)
        observador({"tipo": "expandir", "estado": Estado("Chimoio")})

    monkeypatch.setattr(modulo, "_executar_algoritmo", fake_execucao)
    resultado = modulo.executar_busca(_config(tmp_path), limite_segundos=0.001)

    assert resultado["estado_execucao"] == "interrompida"
    assert resultado["motivo_termino"] == "limite_tempo"
    assert resultado["ultimo_estado"].get_localidade() == "Inchope"
