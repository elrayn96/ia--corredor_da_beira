class Solucao:
    """Guarda o percurso encontrado por um algoritmo de busca."""

    def __init__(self, accoes, estados, custo_total):
        if len(estados) != len(accoes) + 1:
            raise ValueError("O percurso deve ter um estado a mais do que accoes")

        if custo_total < 0:
            raise ValueError("O custo total nao pode ser negativo")

        self.__accoes = tuple(accoes)
        self.__estados = tuple(estados)
        self.__custo_total = custo_total

    @property
    def accoes(self):
        return list(self.__accoes)

    @property
    def estados(self):
        return list(self.__estados)

    @property
    def custo_total(self):
        return self.__custo_total

    def get_accoes(self):
        return list(self.__accoes)

    def get_estados(self):
        return list(self.__estados)

    def get_custo_total(self):
        return self.__custo_total

    def __repr__(self):
        return (
            f"Solucao(accoes={len(self.__accoes)}, "
            f"estados={len(self.__estados)}, "
            f"custo_total={self.__custo_total})"
        )