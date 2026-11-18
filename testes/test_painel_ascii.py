"""Testes da visualização ASCII sem criar janelas Tkinter."""

from src.accao import Accao
from src.estado import Estado
from src.interface.painel_ascii import formatar_solucao_ascii
from src.solucao import Solucao


def test_ascii_mostra_estados_accoes_e_dados_operacionais():
    estados = [
        Estado("Beira", tempo=0, combustivel=300),
        Estado("Dondo", tempo=30, combustivel=260),
        Estado("Dondo", {"Dondo"}, tempo=35, combustivel=260),
    ]
    solucao = Solucao(
        [
            Accao("deslocar", destino="Dondo"),
            Accao("entregar", supermercado="Dondo"),
        ],
        estados,
        35,
    )

    texto = formatar_solucao_ascii(solucao, mensagem="Solução encontrada.")

    assert "SOLUÇÃO PASSO A PASSO" in texto
    assert "[00] Beira" in texto
    assert "+-- DESLOCAR (destino=Dondo)" in texto
    assert "[02] Dondo" in texto
    assert "entregas=Dondo" in texto


def test_ascii_mostra_interrupcao_e_ultimo_estado():
    ultimo = Estado("Inchope", {"Dondo"}, tempo=420, combustivel=175)

    texto = formatar_solucao_ascii(
        None,
        "interrompida",
        "Tempo máximo de execução atingido.",
        ultimo,
    )

    assert "EXECUÇÃO: INTERROMPIDA" in texto
    assert "Não existe um percurso completo" in texto
    assert "ÚLTIMO ESTADO EXPLORADO" in texto
    assert "[00] Inchope" in texto
