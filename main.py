import json
from pathlib import Path

from src.problema import Problema


def carregarInstancia(caminho):
    # Le os dados da instancia; o formato deve ser acordado com a Adila
    with open(caminho, 'r', encoding='utf-8') as ficheiro:
        dados = json.load(ficheiro)
    return Problema(dados['estradas'], dados['supermercados'], dados.get('origem', 'Beira'))


def mostrarSolucao(solucao):
    if solucao is None:
        print('Nao foi encontrada uma solucao.')
        return
    print(f'Custo total: {solucao.getCustoTotal()} minutos')
    for numero, accao in enumerate(solucao.getAcoes(), 1):
        print(f'{numero}. {accao}')


def main():
    # Integrar os algoritmos quando os modulos dos colegas estiverem disponiveis
    caminho = Path('dados/instancias/instancia_teste.json')
    if not caminho.exists():
        print(f'Instancia ainda nao disponivel: {caminho}')
        return
    try:
        problema = carregarInstancia(caminho)
    except (OSError, ValueError, KeyError, TypeError) as erro:
        print(f'Erro ao carregar a instancia: {erro}')
        return
    print('Instancia carregada. Estado inicial:')
    print(problema.getEstadoInicial())
    print('Sucessores iniciais:', len(problema.getSucessores(problema.getEstadoInicial())))
    print('A chamada dos algoritmos sera integrada quando as interfaces estiverem prontas.')


if __name__ == '__main__':
    main()
