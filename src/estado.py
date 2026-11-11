class Estado:
    # Representa a situacao do camiao num determinado instante
    def __init__(self, localidade, entregas_concluidas=None, tempo=0, combustivel=300000):
        if tempo < 0 or combustivel < 0:
            raise ValueError('Tempo e combustivel nao podem ser negativos')
        self.__localidade = localidade
        self.__entregas_concluidas = frozenset(entregas_concluidas or set())
        self.__tempo = int(tempo)
        self.__combustivel = int(combustivel)

    def get_localidade(self):
        return self.__localidade

    def get_entregas_concluidas(self):
        return set(self.__entregas_concluidas)

    def get_tempo(self):
        return self.__tempo

    def get_combustivel(self):
        return self.__combustivel

    def __eq__(self, outro):
        if not isinstance(outro, Estado):
            return NotImplemented
        return self.__chave() == outro.__chave()

    def __hash__(self):
        return hash(self.__chave())

    def __chave(self):
        return (self.__localidade, self.__entregas_concluidas, self.__tempo, self.__combustivel)

    def __repr__(self):
        return (f'Estado(localidade={self.__localidade!r}, entregas={sorted(self.__entregas_concluidas)!r}, '
                f'tempo={self.__tempo}, combustivel={self.__combustivel})')
