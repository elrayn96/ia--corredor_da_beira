"""Verifica que a demonstração contém uma rota real e viável."""

from src.gerador import converter_para_busca, gerar_demonstracao_validada
from src.problema import Problema


def test_demonstracao_reconstroi_solucao_valida(monkeypatch, tmp_path):
    monkeypatch.setattr("src.gerador.PASTA_INSTANCIAS", tmp_path)
    instancia, caminho, solucao = gerar_demonstracao_validada(semente=202601)
    assert caminho.is_file()
    assert len(instancia["supermercados"]) == 7
    assert solucao.get_custo_total() == 830
    problema = Problema(**converter_para_busca(instancia))
    assert problema.teste_objectivo(solucao.get_estados()[-1])
