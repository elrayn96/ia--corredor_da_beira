from math import ceil
from typing import ClassVar

from src.accao import Accao
from src.contrato_busca import Problema as ProblemaAbstrato
from src.estado import Estado


class Problema(ProblemaAbstrato):
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

    def estado_inicial(self):
        return self.get_estado_inicial()

    def criar_estado(self, localidade, entregas_concluidas, tempo, combustivel):
        return Estado(localidade, set(entregas_concluidas), tempo, combustivel)

    def get_origem(self):
        return self.__origem

    def get_supermercados(self):
        return dict(self.__supermercados)

    def get_estradas(self):
        return self.__estradas

    def teste_objectivo(self, estado):
        return (estado.get_localidade() == self.__origem
                and set(self.__supermercados).issubset(estado.get_entregas_concluidas()))

    def e_objectivo(self, estado):
        return self.teste_objectivo(estado)

    def custo_transicao(self, estado, accao, estado_seguinte=None):
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

    def custo(self, estado, accao, estado_seguinte):
        return self.custo_transicao(estado, accao, estado_seguinte)

    @staticmethod
    def _mesma_accao(primeira, segunda):
        return (primeira.get_tipo() == segunda.get_tipo()
                and primeira.get_parametros() == segunda.get_parametros())

    def accoes(self, estado):
        return [accao for accao, _, _ in self.get_sucessores(estado)]

    def resultado(self, estado, accao):
        for candidata, seguinte, _ in self.get_sucessores(estado):
            if self._mesma_accao(candidata, accao):
                return seguinte
        raise ValueError("A acção não é aplicável ao estado informado")

    def heuristica(self, estado, nome):
        from src.heuristicas import h0, h1, h2

        funcoes = {"h0": h0, "h1": h1, "h2": h2}
        try:
            return funcoes[nome](estado, self)
        except KeyError as erro:
            raise ValueError(f"Heurística desconhecida: {nome!r}") from erro

    def sucessores(self, estado):
        return self.get_sucessores(estado)

    @staticmethod
    def __circulacao_permitida(inicio, duracao):
        # A partida ocorre as 05:00; nao circular durante 22:00-05:00
        hora_inicial = (300 + inicio) % 1440
        hora_final = hora_inicial + duracao
        return 300 <= hora_inicial < 1320 and hora_final <= 1320

    def get_sucessores(self, estado):
        # Cada sucessor: (accao, estado_seguinte, custo)
        sucessores = []
        localidade = estado.get_localidade()
        tempo = estado.get_tempo()
        combustivel = estado.get_combustivel()
        entregas = estado.get_entregas_concluidas()
        pendentes = set(self.__supermercados) - entregas

        # Com carga pendente, ultrapassar 14 horas invalida definitivamente o estado.
        if pendentes and tempo >= self.LIMITE_FRIO_MINUTOS:
            return []

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
                novas_entregas = set(entregas)
                novas_entregas.add(localidade)
                custo = self.custo_transicao(estado, accao)
                novo_estado = self.criar_estado(localidade, novas_entregas, tempo + custo, combustivel)
                sucessores.append((accao, novo_estado, custo))

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
        hora_actual = (300 + tempo) % 1440
        if hora_actual >= 1320 or hora_actual < 300:
            espera = (300 - hora_actual) % 1440
            if espera > 0:
                accao = Accao('esperar', minutos=espera)
                novo = self.criar_estado(localidade, entregas, tempo + espera, combustivel)
                sucessores.append((accao, novo, espera))

        # Se nenhuma estrada pode ser concluída antes das 22:00, é permitido
        # aguardar até às 05:00. Isto evita um bloqueio artificial às 21:xx.
        elif not pendentes:
            viagens_possiveis = []
            for via in self.__estradas.get(localidade, {}).values():
                distancia = float(via['distancia'])
                consumo = ceil(distancia * self.CONSUMO)
                duracao = ceil(distancia / self.VELOCIDADES[int(via['piso'])] * 60)
                if consumo <= combustivel:
                    viagens_possiveis.append(self.__circulacao_permitida(tempo, duracao))
            if viagens_possiveis and not any(viagens_possiveis):
                espera = (300 - hora_actual) % 1440
                if espera:
                    accao = Accao('esperar', minutos=espera)
                    novo = self.criar_estado(localidade, entregas, tempo + espera, combustivel)
                    sucessores.append((accao, novo, espera))

        return sucessores
