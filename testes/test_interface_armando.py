"""Testes sem necessidade de criar janelas Tkinter."""
from src.interface.janela_principal import JanelaPrincipal
from src.interface.tema import CORES_ARVORE

def test_janela_tem_contratos_basicos():
    for metodo in ("obter_configuracao", "iniciar_busca", "_actualizar_arvore"):
        assert hasattr(JanelaPrincipal, metodo)

def test_cores_iguais_as_do_elias():
    assert CORES_ARVORE["fronteira"] == "#cfe8ff"
    assert CORES_ARVORE["solucao"] == "#4caf50"
