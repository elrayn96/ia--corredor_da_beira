"""Testes da integracao desenvolvida por Armando."""
import pytest
from src.servicos.carregar_instancia import carregar_instancia

def test_carregar_instancia_real():
    problema = carregar_instancia()
    assert problema.get_origem() == "Beira"
    assert len(problema.get_supermercados()) == 7
    assert len(problema.get_estradas()) >= 15

from src.servicos.validar_solucao import validar_solucao

def test_validacao_sem_solucao():
    assert validar_solucao(carregar_instancia(), None)["valida"] is False

from src.servicos.executar_busca import executar_busca

def test_algoritmo_invalido():
    with pytest.raises(ValueError, match="Algoritmo desconhecido"):
        executar_busca({"algoritmo": "nao_existe"})
