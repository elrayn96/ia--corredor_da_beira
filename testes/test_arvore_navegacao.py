"""Regressões da navegação por expansões completas na árvore de busca."""

from src.interface.arvore_busca import ModeloArvore, calcular_posicoes


def evento(tipo, numero, pai=None):
    return {
        "tipo": tipo, "passo": numero, "no_id": numero,
        "pai_id": pai, "estado": {"localidade": str(numero)},
        "accao": None, "profundidade": 0, "g": 0,
        "h": None, "f": None,
    }


def test_expandir_apresenta_todos_os_filhos_num_unico_passo():
    eventos = [
        evento("inicio", 0),
        evento("expandir", 0),
        evento("gerar", 1, 0),
        evento("gerar", 2, 0),
        evento("expandir", 1, 0),
        evento("gerar", 3, 1),
    ]
    modelo = ModeloArvore(eventos)
    assert modelo.passos == [3, 5]
    assert set(modelo.nos_visiveis(modelo.passos[0])) == {0, 1, 2}
    assert set(modelo.nos_visiveis(modelo.passos[1])) == {0, 1, 2, 3}


def test_rotulo_nao_mostra_heuristica_para_busca_nao_informada():
    modelo = ModeloArvore([evento("inicio", 0)], mostrar_heuristica=False)
    assert "h=" not in modelo.descricao_passo(0)
    assert "f=" not in modelo.descricao_passo(0)


def test_folhas_separadas_por_distancia_adequada():
    nos = {0: {"profundidade": 0}, 1: {"profundidade": 1}, 2: {"profundidade": 1}}
    filhos = {0: [1, 2], 1: [], 2: []}
    posicoes = calcular_posicoes(nos, filhos, [0])
    assert posicoes[2][0] - posicoes[1][0] >= 3
