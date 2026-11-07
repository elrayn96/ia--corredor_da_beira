import json
import random
from pathlib import Path
from datetime import datetime

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
