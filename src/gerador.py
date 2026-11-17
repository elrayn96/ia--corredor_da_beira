import json
import random
from copy import deepcopy
from datetime import datetime
from itertools import pairwise
from pathlib import Path

RAIZ_PROJECTO = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ_PROJECTO / "dados"
PASTA_INSTANCIAS = PASTA_DADOS / "instancias"

FICHEIRO_LOCALIDADES = PASTA_DADOS / "localidades.json"
FICHEIRO_ESTRADAS = PASTA_DADOS / "estradas.json"


def carregar_json(caminho):
    """
    Carrega um ficheiro JSON e devolve os seus dados.
    """
    with open(caminho, "r", encoding="utf-8") as ficheiro:
        return json.load(ficheiro)


def carregar_rede():
    """
    Carrega localidades.json e estradas.json.

    Retorna:
        dict com:
        - localidades
        - estradas
        - velocidadesPorPiso
    """
    dados_localidades = carregar_json(FICHEIRO_LOCALIDADES)
    dados_estradas = carregar_json(FICHEIRO_ESTRADAS)

    return {
        "localidades": dados_localidades["localidades"],
        "estradas": dados_estradas["estradas"],
        "velocidadesPorPiso": dados_estradas["velocidadesPorPiso"]
    }


def validar_horario(horario):
    """
    Verifica se o horário está no formato HH:MM.
    """
    try:
        datetime.strptime(horario, "%H:%M")
        return True
    except ValueError:
        return False


def selecionar_supermercados(localidades, quantidade=7, semente=202601):
    """
    Selecciona exactamente 7 localidades distintas como supermercados.

    Lança ValueError se a quantidade não for 7 ou se não houver
    localidades distintas suficientes.

    A Beira não é seleccionada porque é o ponto de partida e retorno.

    A utilização de uma semente torna a selecção reproduzível.
    """
    if type(quantidade) is not int or quantidade != 7:
        raise ValueError("A quantidade de supermercados deve ser exactamente 7.")

    nomes_disponiveis = list(dict.fromkeys(
        localidade["nome"]
        for localidade in localidades
        if localidade["nome"] != "Beira"
    ))

    if quantidade > len(nomes_disponiveis):
        raise ValueError(
            "A quantidade de supermercados é maior que o número "
            "de localidades distintas disponíveis."
        )

    gerador = random.Random(semente)
    return gerador.sample(nomes_disponiveis, quantidade)


def gerar_janelas_horario(supermercados):
    """
    Cria os dados dos supermercados com identificador, nome
    e janela horária.

    Cada supermercado recebe um ID único no formato SM01, SM02, ...
    """
    horas_abertura = [
        "06:00",
        "07:00",
        "08:00",
        "09:00",
        "10:00",
        "11:00",
        "12:00"
    ]

    horas_fecho = [
        "10:00",
        "11:30",
        "13:00",
        "14:30",
        "16:00",
        "17:30",
        "19:00"
    ]

    supermercados_com_janela = []

    for i, localidade in enumerate(supermercados):
        abertura = horas_abertura[i]
        fecho = horas_fecho[i]

        if not validar_horario(abertura) or not validar_horario(fecho):
            raise ValueError("Foi gerado um horário inválido.")

        supermercados_com_janela.append({
            "id": f"SM{i + 1:02d}",
            "nome": f"Supermercado {i + 1}",
            "localidade": localidade,
            "abertura": abertura,
            "fecho": fecho
        })

    return supermercados_com_janela


def gerar_instancia(semente=202601, quantidade_supermercados=7):
    """
    Gera uma instância do problema com base na rede carregada.

    Retorna um dicionário pronto para ser guardado em JSON.
    """
    rede = carregar_rede()

    supermercados = selecionar_supermercados(
        rede["localidades"],
        quantidade=quantidade_supermercados,
        semente=semente
    )

    supermercados = gerar_janelas_horario(supermercados)

    instancia = {
        "nome": f"instancia_{semente}",
        "semente": semente,

        "rede": {
            "localidades": "../localidades.json",
            "estradas": "../estradas.json"
        },

        "estadoInicial": {
            "localidade": "Beira",
            "horaPartida": "05:00",
            "combustivelLitros": 300
        },

        "parametros": {
            "duracaoFrioHoras": 14,
            "consumoLitrosPorKm": 0.35,
            "tempoDescargaMin": 30,
            "tempoAbastecimentoMin": 20,
            "inicioRestricaoCirculacao": "22:00",
            "fimRestricaoCirculacao": "05:00"
        },

        "postosAbastecimento": [
            "Beira",
            "Inchope",
            "Chimoio"
        ],

        "supermercados": supermercados
    }

    return instancia


def converter_para_busca(instancia, rede=None):
    """
    Converte uma instância gerada para os mapas usados pelas buscas.

    Se rede não for fornecida, carrega a rede base do projecto.
    As estradas são consideradas bidireccionais. Cada localidade contém
    todos os seus vizinhos, incluindo um mapa vazio se não tiver ligações.

    Retorna:
        {
            'estradas': {localidade: {vizinho: {'distancia': km, 'piso': 1..5}}},
            'supermercados': {localidade: {'abertura': 'HH:MM', 'fecho': 'HH:MM'}}
        }

    Não altera a instância nem a rede recebidas.
    """
    if rede is None:
        rede = carregar_rede()

    estradas = {localidade["nome"]: {} for localidade in rede["localidades"]}

    for estrada in rede["estradas"]:
        origem = estrada["origem"]
        destino = estrada["destino"]
        atributos = {
            "distancia": estrada["distanciaKm"],
            "piso": estrada["piso"]
        }
        estradas[origem][destino] = atributos
        estradas[destino][origem] = atributos.copy()
    locais = [
        supermercado["localidade"]
        for supermercado in instancia["supermercados"]
    ]

    if len(locais) != len(set(locais)):
        raise ValueError(
            "Supermercados duplicados na instância."
        )
    supermercados = {
        supermercado["localidade"]: {
            "abertura": supermercado["abertura"],
            "fecho": supermercado["fecho"]
        }
        for supermercado in instancia["supermercados"]
    }

    return {"estradas": estradas, "supermercados": supermercados}


def guardar_instancia(instancia, nome_ficheiro="instancia_teste_01.json"):
    """
    Guarda uma instância na pasta dados/instancias.
    """
    PASTA_INSTANCIAS.mkdir(parents=True, exist_ok=True)

    caminho = PASTA_INSTANCIAS / nome_ficheiro

    with open(caminho, "w", encoding="utf-8") as ficheiro:
        json.dump(
            instancia,
            ficheiro,
            ensure_ascii=False,
            indent=2
        )

    return caminho


def gerar_problema(
    semente=202601,
    quantidade_supermercados=7,
    nome_ficheiro="instancia_teste_01.json"
):
    """
    Função principal do gerador.

    Coordena:
    1. carregamento da rede;
    2. selecção dos supermercados;
    3. criação das janelas horárias;
    4. geração da instância;
    5. gravação do ficheiro JSON.

    Retorna:
        instancia, caminho_do_ficheiro
    """
    instancia = gerar_instancia(
        semente=semente,
        quantidade_supermercados=quantidade_supermercados
    )

    caminho = guardar_instancia(
        instancia,
        nome_ficheiro=nome_ficheiro
    )

    return instancia, caminho


if __name__ == "__main__":
    instancia, caminho = gerar_problema()

    print("Instância gerada com sucesso.")
    print(f"Ficheiro: {caminho}")
    print("Supermercados seleccionados:")

    for supermercado in instancia["supermercados"]:
        print(
            f"- {supermercado['localidade']}: "
            f"{supermercado['abertura']} - {supermercado['fecho']}"
        )



# Percurso de demonstração, construído para a rede distribuída com o projecto.
# Não altera a distribuição aleatória do gerador normal.
PERCURSO_DEMONSTRACAO = (
    "Beira", "Dondo", "Nhamatanda", "Inchope", "Gondola",
    "Vanduzi", "Manica", "Chimoio", "Inchope",
    "Nhamatanda", "Dondo", "Beira",
)
DESTINOS_DEMONSTRACAO = (
    "Dondo", "Nhamatanda", "Inchope", "Gondola",
    "Vanduzi", "Manica", "Chimoio",
)


def gerar_demonstracao_validada(semente=202601, nome_ficheiro=None):
    """Guarda uma instância com percurso testemunha verificado pelo domínio.

    Devolve (instancia, caminho, solucao). Não significa que qualquer
    algoritmo consiga descobrir a solução antes do seu limite de tempo.
    """
    from src.problema import Problema
    from src.solucao import Solucao

    instancia = gerar_instancia(semente=semente)
    instancia["nome"] = f"demonstracao_{semente}"
    instancia["supermercados"] = gerar_janelas_horario(DESTINOS_DEMONSTRACAO)
    problema = Problema(**converter_para_busca(instancia))
    estado = problema.get_estado_inicial()
    estados = [estado]
    accoes = []
    custo_total = 0

    for destino in PERCURSO_DEMONSTRACAO[1:]:
        sucessores = problema.get_sucessores(estado)
        movimentos = [
            (accao, seguinte, custo)
            for accao, seguinte, custo in sucessores
            if accao.get_tipo() == "deslocar"
            and accao.get_parametro("destino") == destino
        ]
        if not movimentos:
            raise ValueError(f"Percurso de demonstração inválido: {destino}")
        accao, estado, custo = movimentos[0]
        estados.append(estado)
        accoes.append(accao)
        custo_total += custo

        if destino in DESTINOS_DEMONSTRACAO and destino not in estado.get_entregas_concluidas():
            entregas = [
                item for item in problema.get_sucessores(estado)
                if item[0].get_tipo() == "entregar"
            ]
            if not entregas:
                esperas = [
                    item for item in problema.get_sucessores(estado)
                    if item[0].get_tipo() == "esperar"
                ]
                if not esperas:
                    raise ValueError(f"Não é possível entregar em {destino}")
                accao, estado, custo = esperas[0]
                estados.append(estado)
                accoes.append(accao)
                custo_total += custo
                entregas = [
                    item for item in problema.get_sucessores(estado)
                    if item[0].get_tipo() == "entregar"
                ]
            if not entregas:
                raise ValueError(f"Entrega impossível em {destino}")
            accao, estado, custo = entregas[0]
            estados.append(estado)
            accoes.append(accao)
            custo_total += custo

    if not problema.teste_objectivo(estado):
        raise ValueError("O percurso demonstrativo não atingiu o objectivo")
    solucao = Solucao(accoes, estados, custo_total)
    nome_ficheiro = nome_ficheiro or f"demonstracao_{semente}.json"
    caminho = guardar_instancia(instancia, nome_ficheiro)
    return instancia, caminho, solucao


def _rede_directa_experimental(nivel, gerador):
    """Cria uma rede de dificuldade crescente preservando um percurso viável."""
    rede = converter_para_busca(gerar_instancia())
    completa = rede["estradas"]
    if nivel == "pequena":
        # Caso controlado: corredor dirigido sem alternativas. A ligação final
        # Chimoio-Beira é um dado simulado, identificado apenas nesta bateria,
        # e permite que até BFS/DFS/IDS terminem como exige o enunciado.
        percurso = (
            "Beira", "Dondo", "Nhamatanda", "Inchope", "Gondola",
            "Vanduzi", "Manica", "Chimoio", "Beira",
        )
        estradas = {nome: {} for nome in completa}
        for origem, destino in pairwise(percurso):
            if destino in completa.get(origem, {}):
                dados = deepcopy(completa[origem][destino])
            else:
                dados = {"distancia": 200, "piso": 5, "simulada": True}
            dados["distancia"] = max(
                1, round(float(dados["distancia"]) + gerador.randint(-2, 2), 1)
            )
            estradas[origem][destino] = dados
        return estradas
    pares_percurso = {
        frozenset((a, b)) for a, b in pairwise(PERCURSO_DEMONSTRACAO)
    }
    extras = []
    for origem, vizinhos in completa.items():
        for destino, dados in vizinhos.items():
            if origem < destino and frozenset((origem, destino)) not in pares_percurso:
                extras.append((origem, destino, dados))
    gerador.shuffle(extras)
    quantidade_extra = {"pequena": 0, "media": 8, "grande": len(extras)}[nivel]
    escolhidas = list(extras[:quantidade_extra])
    for par in pares_percurso:
        origem, destino = tuple(par)
        dados = completa[origem][destino]
        escolhidas.append((origem, destino, dados))

    estradas = {nome: {} for nome in completa}
    for origem, destino, dados_originais in escolhidas:
        dados = deepcopy(dados_originais)
        # Pequena variação reproduzível mantém as instâncias distintas sem
        # alterar a estrutura geográfica nem a classificação do piso.
        dados["distancia"] = max(1, round(float(dados["distancia"]) + gerador.randint(-2, 2), 1))
        estradas[origem][destino] = dados
        estradas[destino][origem] = deepcopy(dados)
    return estradas


def gerar_instancias_experimentais(
    pasta=None, semente_base=202601, quantidade_por_nivel=10
):
    """Gera 10 instâncias viáveis por nível a partir da semente do grupo.

    Os níveis mantêm as sete entregas e as quinze localidades do P1. A
    dificuldade cresce pelo número de alternativas rodoviárias, evitando
    alterar as regras do domínio apenas para produzir resultados favoráveis.
    """
    pasta = Path(pasta) if pasta else PASTA_DADOS / "instancias_experimentais"
    pasta.mkdir(parents=True, exist_ok=True)
    supermercados = {
        item["localidade"]: {
            "abertura": item["abertura"], "fecho": item["fecho"]
        }
        for item in gerar_janelas_horario(DESTINOS_DEMONSTRACAO)
    }
    caminhos = []
    for numero_nivel, nivel in enumerate(("pequena", "media", "grande")):
        for indice in range(quantidade_por_nivel):
            semente = semente_base + numero_nivel * 100 + indice
            gerador = random.Random(semente)
            estradas = _rede_directa_experimental(nivel, gerador)
            instancia = {
                "nome": f"{nivel}_{indice + 1:02d}",
                "nivel": nivel,
                "indice": indice + 1,
                "semente_base": semente_base,
                "semente": semente,
                "dimensao": sum(len(v) for v in estradas.values()) // 2,
                "origem": "Beira",
                "estadoInicial": {
                    "localidade": "Beira", "horaPartida": "05:00",
                    "combustivelLitros": 300,
                },
                "postosAbastecimento": ["Beira", "Inchope", "Chimoio"],
                "estradas": estradas,
                "supermercados": supermercados,
            }
            caminho = pasta / f"{nivel}_{indice + 1:02d}.json"
            caminho.write_text(
                json.dumps(instancia, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            caminhos.append(caminho)
    return caminhos
