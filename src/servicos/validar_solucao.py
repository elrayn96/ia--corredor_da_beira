"""Validação independente de uma solução através da interface do domínio."""

from __future__ import annotations


def _mesma_accao(primeira, segunda):
    return (
        primeira.get_tipo() == segunda.get_tipo()
        and primeira.get_parametros() == segunda.get_parametros()
    )


def validar_solucao(problema, solucao):
    """Devolve ``(valida, erros)`` sem lançar erro para soluções inválidas."""
    erros = []
    if solucao is None:
        return False, ["A solução é nula."]
    try:
        estados = solucao.get_estados()
        accoes = solucao.get_accoes()
        custo_declarado = solucao.get_custo_total()
    except AttributeError:
        return False, ["O objecto não respeita o contrato de Solucao."]

    if len(estados) != len(accoes) + 1:
        erros.append("O número de estados deve ser o número de acções mais um.")
        return False, erros
    if not estados or estados[0] != problema.get_estado_inicial():
        erros.append("O primeiro estado não é o estado inicial do problema.")

    custo_calculado = 0
    for indice, (anterior, accao, seguinte) in enumerate(
        zip(estados, accoes, estados[1:]), 1
    ):
        correspondencias = [
            custo
            for accao_valida, estado_valido, custo in problema.get_sucessores(anterior)
            if estado_valido == seguinte and _mesma_accao(accao_valida, accao)
        ]
        if not correspondencias:
            erros.append(f"Transição inválida no passo {indice}.")
        else:
            custo_calculado += correspondencias[0]

    if estados and not problema.teste_objectivo(estados[-1]):
        erros.append("O estado final não satisfaz o objectivo.")
    if custo_calculado != custo_declarado:
        erros.append(
            f"Custo declarado ({custo_declarado}) diferente do calculado "
            f"({custo_calculado})."
        )
    return not erros, erros
