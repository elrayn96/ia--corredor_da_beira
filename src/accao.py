class Accao:
    # Uma accao tem um tipo e os parametros necessarios para a executar
    TIPOS = {'deslocar', 'entregar', 'abastecer', 'esperar'}

	# Os parametros podem coner razoes que justificam a accao, como abastecer, ou esperar a espera de janela,
	# ou deslocar-se para algum destino, abastecer por ter conbustivel insuficeiente...
    def __init__(self, tipo, **parametros):
        if tipo not in self.TIPOS:
            raise ValueError(f'Tipo de accao invalido: {tipo}')
        self.__tipo = tipo
        self.__parametros = dict(parametros)

    def get_tipo(self):
        return self.__tipo

    def get_parametros(self):
        return dict(self.__parametros)

	# O parametro padrao serve como retorno, caso o parametro com nome dado nao exista (serve para nao lancar excessao);
    def get_parametro(self, nome, padrao=None):
        return self.__parametros.get(nome, padrao)

    def __repr__(self):
        return f'Accao(tipo={self.__tipo!r}, parametros={self.__parametros!r})'
