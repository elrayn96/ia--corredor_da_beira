from math import ceil
from typing import ClassVar

from src.accao import Accao
from src.estado import Estado


class Problema:
    # Coordena as regras da cadeia de frio e fornece sucessores aos algoritmos
    VELOCIDADES: ClassVar[dict[int, int]] = {
        1: 40,
        2: 55,
        3: 70,
        4: 80,
        5: 90,
    }

    POSTOS_ABASTECIMENTO: ClassVar[set[str]] = {
        "Beira",
        "Inchope",
        "Chimoio",
    } # Em funcao do PISO
    CAPACIDADE = 300000  # mililitros
    CONSUMO = 350  # mililitros por quilometro
    LIMITE_FRIO = 14
    LIMITE_FRIO_MINUTOS = LIMITE_FRIO * 60 
    DURACAO_ENTREGA = 30
    DURACAO_ABASTECIMENTO = 20
    QUANTIDADE_SUPERMERCADOS = 7

    def __init__(self, estradas, supermercados, origem='Beira'):
        # estradas: {localidade: {vizinho: {'distancia': km, 'piso': 1..5}}}, EH O GRAFO inteiro
        # supermercados: {localidade: {'abertura': 'HH:MM', 'fecho': 'HH:MM'}}
        self.__estradas = estradas
        self.__supermercados = supermercados
        self.__origem = origem
        if origem not in estradas:
            raise ValueError('A localidade de origem nao consta da rede')


        if len(supermercados) != self.QUANTIDADE_SUPERMERCADOS:
            raise ValueError('A instancia deve conter exactamente sete supermercados')
        for localidade, dados in supermercados.items():
            if localidade not in estradas:
                raise ValueError(f'Supermercado fora da rede: {localidade}')
            if self.__minutos(dados['fecho']) < self.__minutos(dados['abertura']):
                raise ValueError('A janela de entrega nao pode atravessar a meia-noite')

    @staticmethod # indica que o metodo nao depende da instancia, por  isso nao precisa de self como parametro
    def __minutos(horario):
        horas, minutos = map(int, horario.split(':'))
        if not 0 <= horas < 24 or not 0 <= minutos < 60:
            raise ValueError('Horario invalido')
        return horas * 60 + minutos

    def get_estado_inicial(self):
        return Estado(self.__origem, set(), 0, self.CAPACIDADE)

    def criar_estado(self, localidade, entregasConcluidas, tempo, combustivel):
        return Estado(localidade, set(entregasConcluidas), tempo, combustivel)

    def get_origem(self):
        return self.__origem

    def get_supermercados(self):
        return dict(self.__supermercados)

    def get_estradas(self):
        return self.__estradas

    def teste_objectivo(self, estado):
        return (estado.get_localidade() == self.__origem
                and set(self.__supermercados).issubset(estado.get_entregas_concluidas()))

    def custo_transicao(self, estado, accao, estadoSeguinte=None):
        # Calcula o custo de cada accao em minutos
        tipo = accao.get_tipo()
        if tipo == 'deslocar':
            destino = accao.get_parametro('destino')
            via = self.__estradas[estado.get_localidade()][destino] # Pega um vizinho ({destino})especifico da localidade actual
            return ceil(float(via['distancia']) / self.VELOCIDADES[int(via['piso'])] * 60)
        if tipo == 'entregar':
            return self.DURACAO_ENTREGA
        if tipo == 'abastecer':
            return self.DURACAO_ABASTECIMENTO
        if tipo == 'esperar':
            return int(accao.get_parametro('minutos'))
        raise ValueError('Accao desconhecida')

    @staticmethod
    def __circulacao_permitida(inicio, duracao):
        # A partida ocorre as 05:00; nao circular durante 22:00-05:00
        horaInicial = (300 + inicio) % 1440
        horaFinal = horaInicial + duracao
        return 300 <= horaInicial < 1320 and horaFinal <= 1320

    def get_sucessores(self, estado):
        # Cada sucessor: (accao, estadoSeguinte, custo)
        sucessores = []
        localidade = estado.get_localidade()
        tempo = estado.get_tempo()
        combustivel = estado.get_combustivel()
        entregas = estado.get_entregas_concluidas()

        # Deslocacoes para localidades directamente ligadas
        for destino, via in self.__estradas.get(localidade, {}).items():
            distancia = float(via['distancia'])
            if distancia < 0 or int(via['piso']) not in self.VELOCIDADES:
                continue
            consumo = ceil(distancia * self.CONSUMO)
            accao = Accao('deslocar', destino=destino)
            custo = self.custo_transicao(estado, accao)
            if consumo <= combustivel and self.__circulacao_permitida(tempo, custo):
                novo = self.criar_estado(destino, entregas, tempo + custo, combustivel - consumo)
                sucessores.append((accao, novo, custo))

        # Entregar apenas no supermercado pendente e dentro da janela
        if localidade in self.__supermercados and localidade not in entregas:
            dados = self.__supermercados[localidade]
            abertura = self.__minutos(dados['abertura']) - 300
            fecho = self.__minutos(dados['fecho']) - 300
            if abertura <= tempo and tempo + self.DURACAO_ENTREGA <= min(fecho, self.LIMITE_FRIO_MINUTOS):
                accao = Accao('entregar', supermercado=localidade)
                novasEntregas = set(entregas)
                novasEntregas.add(localidade)
                custo = self.custo_transicao(estado, accao)
                novoEstado = self.criar_estado(localidade, novasEntregas, tempo + custo, combustivel)
                sucessores.append((accao, novoEstado, custo))

            # Esperar pela abertura, sem ultrapassar o limite do frio, se o camiao chega antes da loja abrir
            if tempo < abertura and abertura + self.DURACAO_ENTREGA <= min(fecho, self.LIMITE_FRIO_MINUTOS):
                accao = Accao('esperar', minutos=abertura - tempo)
                custo = self.custo_transicao(estado, accao)
                novo = self.criar_estado(localidade, entregas, tempo + custo, combustivel)
                sucessores.append((accao, novo, custo))

        # Abastecer apenas nos postos autorizados, ate ao tanque cheio
        if localidade in self.POSTOS_ABASTECIMENTO and combustivel < self.CAPACIDADE:
            accao = Accao('abastecer')
            custo = self.custo_transicao(estado, accao)
            novo = self.criar_estado(localidade, entregas, tempo + custo, self.CAPACIDADE)
            sucessores.append((accao, novo, custo))

        # Esperar ate a reabertura da circulacao, quando necessario
        horaActual = (300 + tempo) % 1440
        if horaActual >= 1320 or horaActual < 300:
            espera = (300 - horaActual) % 1440
            if espera > 0:
                accao = Accao('esperar', minutos=espera)
                novo = self.criar_estado(localidade, entregas, tempo + espera, combustivel)
                sucessores.append((accao, novo, espera))

        return sucessores
