import json
from itertools import pairwise

import pytest

from src.interface.janela_principal import JanelaPrincipal
from src.servicos.executar_busca import executar_busca
from src.servicos.validar_solucao import validar_solucao


@pytest.fixture
def caminho_instancia(tmp_path):
    localidades = ["Beira"] + [f"C{i}" for i in range(1, 8)]
    estradas = {localidade: {} for localidade in localidades}
    for origem, destino in pairwise(localidades):
        estradas[origem][destino] = {"distancia": 1, "piso": 5}
    estradas[localidades[-1]]["Beira"] = {"distancia": 1, "piso": 5}
    supermercados = {
        localidade: {"abertura": "05:00", "fecho": "19:00"}
        for localidade in localidades[1:]
    }
    caminho = tmp_path / "instancia_directa.json"
    caminho.write_text(
        json.dumps(
            {
                "origem": "Beira",
                "estradas": estradas,
                "supermercados": supermercados,
            }
        ),
        encoding="utf-8",
    )
    return caminho


def configuracao(caminho, algoritmo="a_star", heuristica="h2"):
    return {
        "caminho_instancia": str(caminho),
        "algoritmo": algoritmo,
        "heuristica": heuristica,
        "peso": 1.5 if algoritmo == "a_star_ponderada" else None,
        "limite": 3 if algoritmo in ("lds", "ids") else None,
    }


def test_janela_principal_tem_contrato_sem_criar_raiz_tk():
    assert issubclass(JanelaPrincipal, object)
    assert callable(JanelaPrincipal._iniciar_busca)


@pytest.mark.parametrize(
    "algoritmo",
    ["bfs", "dfs", "lds", "ids", "ucs", "busca_gulosa", "a_star", "a_star_ponderada"],
)
def test_servico_executa_todos_os_algoritmos(
    caminho_instancia, algoritmo, monkeypatch
):
    class ProblemaPequeno:
        @staticmethod
        def get_estado_inicial():
            return "S"

        @staticmethod
        def get_sucessores(estado):
            return {
                "S": [("S->A", "A", 1)],
                "A": [("A->G", "G", 1)],
            }.get(estado, [])

        @staticmethod
        def teste_objectivo(estado):
            return estado == "G"

    monkeypatch.setattr(
        "src.servicos.executar_busca.carregar_problema",
        lambda caminho: ProblemaPequeno(),
    )
    resultado = executar_busca(
        configuracao(caminho_instancia, algoritmo, heuristica="h0")
    )
    assert resultado["estado_execucao"] == "concluida"
    assert resultado["solucao"] is not None
    assert resultado["eventos"]
    assert set(resultado["estatisticas"]) == {
        "nos_gerados",
        "nos_expandidos",
        "max_fronteira",
        "nos_reexpandidos",
        "comprimento_caminho",
        "tempo_segundos",
        "memoria_pico_bytes",
    }


def test_servico_notifica_observador(caminho_instancia):
    observados = []
    resultado = executar_busca(
        configuracao(caminho_instancia), observador=observados.append
    )
    assert observados == resultado["eventos"]


def test_solucao_devolvida_e_valida(caminho_instancia):
    from src.servicos.executar_busca import carregar_problema

    resultado = executar_busca(configuracao(caminho_instancia))
    problema = carregar_problema(caminho_instancia)
    valida, erros = validar_solucao(problema, resultado["solucao"])
    assert valida
    assert erros == []


def test_erro_e_convertido_em_resultado(tmp_path):
    resultado = executar_busca(configuracao(tmp_path / "inexistente.json"))
    assert resultado["estado_execucao"] == "erro"
    assert resultado["solucao"] is None
    assert resultado["mensagem"]


def test_validar_solucao_nula(caminho_instancia):
    from src.servicos.executar_busca import carregar_problema

    assert validar_solucao(carregar_problema(caminho_instancia), None)[0] is False
