class Solucao:
    # Guarda o percurso encontrado por um algoritmo de busca
    def __init__(self, acoes, estados, custoTotal):
        if len(estados) != len(acoes) + 1:
            raise ValueError('O percurso deve ter um estado a mais do que accoes')
        if custoTotal < 0:
            raise ValueError('O custo total nao pode ser negativo')
        self.__acoes = tuple(acoes)
        self.__estados = tuple(estados)
        self.__custoTotal = custoTotal

    def get_acoes(self):
        return list(self.__acoes)

    def get_estados(self):
        return list(self.__estados)

    def get_custo_total(self):
        return self.__custoTotal

    def __repr__(self):
        return f'Solucao(acoes={len(self.__acoes)}, estados={len(self.__estados)}, custoTotal={self.__custoTotal})'
