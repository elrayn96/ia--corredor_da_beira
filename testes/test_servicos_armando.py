
"""Testes da integração desenvolvida por Armando."""


from src.servicos.carregar_instancia import carregar_instancia
from src.servicos.executar_busca import executar_busca
from src.servicos.validar_solucao import validar_solucao


def test_carregar_instancia_real():
    problema = carregar_instancia()
    assert problema.get_origem() == "Beira"
    assert len(problema.get_supermercados()) == 7
    assert len(problema.get_estradas()) >= 15


def test_validacao_sem_solucao():
    valida, erros = validar_solucao(carregar_instancia(), None)

    assert valida is False
    assert erros


def test_algoritmo_invalido():
    configuracao = {
        "caminho_instancia": __file__,
        "algoritmo": "nao_existe",
        "heuristica": None,
        "peso": None,
        "limite": None,
    }

    resultado = executar_busca(configuracao)

    assert resultado["estado_execucao"] == "erro"
    assert "Algoritmo desconhecido" in resultado["mensagem"]
