"""Valida uma solucao reproduzindo as transicoes do Problema."""

def validar_solucao(problema, solucao):
    """Devolve um resultado explicito sem alterar o objecto de solucao."""
    if solucao is None:
        return {"valida": False, "motivo": "Nenhuma solucao encontrada"}
    estados = solucao.get_estados()
    accoes = solucao.get_accoes()
    if not estados or estados[0] != problema.get_estado_inicial():
        return {"valida": False, "motivo": "Estado inicial incorrecto"}
    if len(estados) != len(accoes) + 1:
        return {"valida": False, "motivo": "Numero de estados inconsistente"}
    custo = 0
    for indice, accao in enumerate(accoes):
        possibilidades = problema.get_sucessores(estados[indice])
        transicao = next(((seguinte, valor) for candidata, seguinte, valor in possibilidades
                          if candidata == accao and seguinte == estados[indice + 1]), None)
        if transicao is None:
            return {"valida": False, "motivo": f"Transicao invalida no passo {indice + 1}"}
        custo += transicao[1]
    if not problema.teste_objectivo(estados[-1]):
        return {"valida": False, "motivo": "Estado final nao satisfaz o objectivo"}
    if custo != solucao.get_custo_total():
        return {"valida": False, "motivo": "Custo total inconsistente"}
    return {"valida": True, "motivo": "Solucao valida", "custo_total": custo}
