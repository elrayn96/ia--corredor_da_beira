"""Testes da integracao desenvolvida por Armando."""
import pytest
from src.servicos.carregar_instancia import carregar_instancia

def test_carregar_instancia_real():
    problema = carregar_instancia()
    assert problema.get_origem() == "Beira"
    assert len(problema.get_supermercados()) == 7
    assert len(problema.get_estradas()) >= 15
