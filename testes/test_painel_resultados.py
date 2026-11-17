
from tkinter import ttk

from src.accao import Accao
from src.estado import Estado
from src.interface.painel_resultados import (
    PainelResultados,
    preparar_metricas,
    preparar_resultados,
)
from src.solucao import Solucao


def criar_solucao_exemplo():
    estados = [
        Estado("Beira", tempo=0, combustivel=100),
        Estado("Dondo", tempo=30, combustivel=80),
        Estado(
            "Dondo",
            entregas_concluidas={"Dondo"},
            tempo=35,
            combustivel=80,
        ),
        Estado(
            "Dondo",
            entregas_concluidas={"Dondo"},
            tempo=45,
            combustivel=80,
        ),
        Estado(
            "Dondo",
            entregas_concluidas={"Dondo"},
            tempo=50,
            combustivel=100,
        ),
    ]

    accoes = [
        Accao("deslocar", destino="Dondo"),
        Accao("entregar", supermercado="Dondo"),
        Accao("esperar", minutos=10),
        Accao("abastecer"),
    ]

    return Solucao(
        accoes=accoes,
        estados=estados,
        custo_total=50,
    )


def test_painel_tem_contrato_obrigatorio():
    assert issubclass(PainelResultados, ttk.Frame)
    assert callable(PainelResultados.mostrar_resultados)
    assert callable(PainelResultados.limpar)


def test_resumo_da_solucao():
    solucao = criar_solucao_exemplo()

    dados = preparar_resultados(solucao, {})

    assert dados["custo"] == 50
    assert dados["numero_estados"] == 5
    assert dados["numero_accoes"] == 4
    assert dados["entregas"] == 1
    assert dados["esperas"] == 1
    assert dados["abastecimentos"] == 1


def test_tabela_de_accoes():
    solucao = criar_solucao_exemplo()

    dados = preparar_resultados(solucao, {})

    assert len(dados["linhas"]) == 4

    assert dados["linhas"][0] == (
        1,
        "deslocar",
        "Beira",
        "Dondo",
        30,
        80,
    )

    assert dados["linhas"][1][1] == "entregar"
    assert dados["linhas"][2][1] == "esperar"
    assert dados["linhas"][3][1] == "abastecer"


def test_percurso_e_estado_final():
    solucao = criar_solucao_exemplo()

    dados = preparar_resultados(solucao, {})

    assert dados["percurso"].startswith("Beira → Dondo")
    assert "Localidade: Dondo" in dados["estado_final"]
    assert "Tempo: 50" in dados["estado_final"]
    assert "Combustível: 100" in dados["estado_final"]
    assert "Entregas concluídas: 1" in dados["estado_final"]


def test_metricas_obrigatorias():
    estatisticas = {
        "nos_gerados": 20,
        "nos_expandidos": 10,
        "max_fronteira": 5,
        "tempo_segundos": 0.25,
        "memoria_pico_bytes": 4096,
    }

    dados = preparar_metricas(estatisticas)

    assert dados["nos_gerados"] == "20"
    assert dados["nos_expandidos"] == "10"
    assert dados["max_fronteira"] == "5"
    assert dados["tempo_segundos"] == "0.250000"
    assert dados["memoria_pico_bytes"] == "4096"


def test_metricas_ausentes():
    dados = preparar_metricas(None)

    assert all(
        valor == "—"
        for valor in dados.values()
    )


def test_sem_solucao():
    dados = preparar_resultados(None, {})

    assert dados["custo"] == "—"
    assert dados["estado_final"] == "Sem solução"
    assert dados["linhas"] == []


def test_interrupcao_mostra_motivo_e_ultimo_estado():
    ultimo = Estado(
        "Inchope", entregas_concluidas={"Dondo"}, tempo=420, combustivel=175
    )
    dados = preparar_resultados(
        None, {}, "interrompida", "Tempo máximo de execução atingido.", ultimo
    )

    assert dados["estado_execucao"] == "interrompida"
    assert dados["mensagem"] == "Tempo máximo de execução atingido."
    assert "Localidade: Inchope" in dados["estado_final"]
    assert "Entregas concluídas: 1" in dados["estado_final"]
