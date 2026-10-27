from src.estado import Estado


# Metodo que verifica se dois estados iguais sao reconhecidos
def test_estados_iguais():
    estado1 = Estado("Beira", {"SUP1"}, 120, 250000)
    estado2 = Estado("Beira", {"SUP1"}, 120, 250000)

    assert estado1 == estado2


# Metodo que verifica se estados diferentes sao distinguidos
def test_estados_diferentes():
    estado1 = Estado("Beira", {"SUP1"}, 120, 250000)
    estado2 = Estado("Beira", {"SUP2"}, 120, 250000)

    assert estado1 != estado2


# Metodo que verifica a consistencia do hash
def test_hash_estados_iguais():
    estado1 = Estado("Beira", {"SUP1"}, 120, 250000)
    estado2 = Estado("Beira", {"SUP1"}, 120, 250000)

    assert hash(estado1) == hash(estado2)


# Metodo que verifica o uso dos estados num conjunto
def test_estados_visitados():
    estado1 = Estado("Beira", {"SUP1"}, 120, 250000)
    estado2 = Estado("Beira", {"SUP1"}, 120, 250000)

    visitados = {estado1}

    assert estado2 in visitados


# Metodo que verifica se o estado guarda as entregas sem alteracoes externas
def test_entregas_protegidas():
    estado = Estado("Beira", {"SUP1"}, 120, 250000)

    entregas = estado.get_entregas_concluidas()
    entregas.add("SUP2")

    assert estado.get_entregas_concluidas() == {"SUP1"}