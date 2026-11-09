import pytest

from src.accao import Accao


# Metodo que verifica a criacao de uma accao valida
def test_accao_valida():
    accao = Accao("deslocar", destino="Dondo")

    assert accao.get_tipo() == "deslocar"
    assert accao.get_parametro("destino") == "Dondo"


# Metodo que verifica a rejeicao de um tipo invalido
def test_accao_invalida():
    with pytest.raises(ValueError):
        Accao("voar", destino="Dondo")


# Metodo que verifica o valor padrao de um parametro
def test_parametro_padrao():
    accao = Accao("esperar", minutos=30)

    assert accao.get_parametro("destino", "Nao definido") == "Nao definido"


# Metodo que verifica a proteccao do dicionario de parametros
def test_parametros_protegidos():
    accao = Accao("deslocar", destino="Dondo")

    parametros = accao.get_parametros()
    parametros["destino"] = "Chimoio"

    assert accao.get_parametro("destino") == "Dondo"