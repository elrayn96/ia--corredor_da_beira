"""Execução reproduzível de uma configuração através do serviço comum."""

from __future__ import annotations

from src.servicos.executar_busca import executar_busca


def executar_experiencia(configuracao):
    """Executa um caso e devolve um registo pronto para comparar/exportar."""
    resultado = executar_busca(configuracao)
    solucao = resultado["solucao"]
    registo = {
        "caminho_instancia": configuracao.get("caminho_instancia"),
        "semente": configuracao.get("semente"),
        "algoritmo": configuracao.get("algoritmo"),
        "heuristica": configuracao.get("heuristica"),
        "peso": configuracao.get("peso"),
        "limite": configuracao.get("limite"),
        "estado_execucao": resultado["estado_execucao"],
        "mensagem": resultado["mensagem"],
        "custo_total": None if solucao is None else solucao.get_custo_total(),
        **resultado["estatisticas"],
        "solucao": solucao,
        "eventos": resultado["eventos"],
    }
    return registo
