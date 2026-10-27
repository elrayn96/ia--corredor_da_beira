import pytest

from src.problema import Problema


@pytest.fixture
def problema():
    estradas = {
        "Beira": {
            "Dondo": {"distancia": 30, "piso": 3}
        },
        "Dondo": {
            "Beira": {"distancia": 30, "piso": 3}
        }
    }

    estradas = {
        "Beira": {
            "Dondo": {"distancia": 30, "piso": 3}
        },
        "Dondo": {
            "Beira": {"distancia": 30, "piso": 3}
        },
        "Inchope": {},
        "Chimoio": {},
        "Manica": {},
        "Gondola": {},
        "Caia": {},
        "Nhamatanda": {}
    }

    supermercados = {
        "Dondo": {"abertura": "08:00", "fecho": "18:00"},
        "Inchope": {"abertura": "08:00", "fecho": "18:00"},
        "Chimoio": {"abertura": "08:00", "fecho": "18:00"},
        "Manica": {"abertura": "08:00", "fecho": "18:00"},
        "Gondola": {"abertura": "08:00", "fecho": "18:00"},
        "Caia": {"abertura": "08:00", "fecho": "18:00"},
        "Nhamatanda": {"abertura": "08:00", "fecho": "18:00"}
    }

    return Problema(estradas, supermercados)


def test_estado_inicial(problema):
    estado = problema.get_estado_inicial()

    assert estado.get_localidade() == "Beira"
    assert estado.get_entregas_concluidas() == set()
    assert estado.get_tempo() == 0
    assert estado.get_combustivel() == 300000


def test_objectivo_inicial_falso(problema):
    estado = problema.get_estado_inicial()

    assert problema.teste_objectivo(estado) is False


def test_objectivo_com_todas_entregas(problema):
    estado = problema.criar_estado(
        "Beira",
        {
            "Dondo", "Inchope", "Chimoio",
            "Manica", "Gondola", "Caia",
            "Nhamatanda"
        },
        700,
        100000
    )

    assert problema.teste_objectivo(estado) is True


def test_objectivo_sem_regresso(problema):
    estado = problema.criar_estado(
        "Dondo",
        {
            "Dondo", "Inchope", "Chimoio",
            "Manica", "Gondola", "Caia",
            "Nhamatanda"
        },
        700,
        100000
    )

    assert problema.teste_objectivo(estado) is False


def test_deslocacao_para_dondo(problema):
    estado = problema.get_estado_inicial()

    sucessores = problema.get_sucessores(estado)

    deslocacoes = [
        (accao, novo, custo)
        for accao, novo, custo in sucessores
        if accao.get_tipo() == "deslocar"
    ]

    assert len(deslocacoes) == 1

    accao, novo, custo = deslocacoes[0]

    assert novo.get_localidade() == "Dondo"
    assert custo == 26
    assert novo.get_tempo() == 26
    assert novo.get_combustivel() == 289500


def test_sem_combustivel_para_deslocar(problema):
    estado = problema.criar_estado(
        "Beira",
        set(),
        0,
        5000
    )

    sucessores = problema.get_sucessores(estado)

    deslocacoes = [
        accao
        for accao, novo, custo in sucessores
        if accao.get_tipo() == "deslocar"
    ]

    assert deslocacoes == []