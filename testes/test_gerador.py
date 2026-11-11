import json
from datetime import datetime

import pytest

from src import gerador


@pytest.fixture
def instancia():
    return gerador.gerar_instancia()


def test_estrutura_da_instancia(instancia):
    assert set(instancia) == {
        'nome', 'semente', 'rede', 'estadoInicial', 'parametros',
        'postosAbastecimento', 'supermercados'
    }
    assert instancia['estadoInicial'] == {
        'localidade': 'Beira', 'horaPartida': '05:00',
        'combustivelLitros': 300
    }


def test_supermercados(instancia):
    supermercados = instancia['supermercados']
    nomes = [s['localidade'] for s in supermercados]
    localidades = [l['nome'] for l in gerador.carregar_rede()['localidades']]

    assert len(supermercados) == 7
    assert len(set(nomes)) == 7
    assert 'Beira' not in nomes
    assert len({s['id'] for s in supermercados}) == 7

    for supermercado in supermercados:
        assert supermercado['localidade'] in localidades
        abertura = datetime.strptime(supermercado['abertura'], '%H:%M')
        fecho = datetime.strptime(supermercado['fecho'], '%H:%M')
        assert abertura < fecho


def test_mesma_semente_gera_mesma_instancia():
    primeira = gerador.gerar_instancia(semente=123)
    segunda = gerador.gerar_instancia(semente=123)
    assert primeira == segunda
    assert primeira['semente'] == 123


@pytest.mark.parametrize('quantidade', [0, 6, 8, -1, 7.0, True, '7', None])
def test_quantidade_invalida(quantidade):
    with pytest.raises(ValueError):
        gerador.gerar_instancia(quantidade_supermercados=quantidade)


def test_localidades_insuficientes():
    # Nomes repetidos não contam como localidades distintas.
    localidades = [{'nome': 'Dondo'}] * 7
    with pytest.raises(ValueError):
        gerador.selecionar_supermercados(localidades)


def test_conversao_das_estradas(instancia):
    rede = gerador.carregar_rede()
    dados = gerador.converter_para_busca(instancia, rede)
    for estrada in rede['estradas']:
        origem = estrada['origem']
        destino = estrada['destino']
        esperado = {'distancia': estrada['distanciaKm'], 'piso': estrada['piso']}
        assert dados['estradas'][origem][destino] == esperado
        assert dados['estradas'][destino][origem] == esperado

    # A Beira deve manter os dois destinos, sem substituir um pelo outro.
    assert set(dados['estradas']['Beira']) == {'Dondo', 'Mutua'}


def test_conversao_dos_supermercados(instancia):
    dados = gerador.converter_para_busca(instancia)
    assert len(dados['supermercados']) == 7
    for supermercado in instancia['supermercados']:
        assert dados['supermercados'][supermercado['localidade']] == {
            'abertura': supermercado['abertura'],
            'fecho': supermercado['fecho']
        }


def test_gravacao_do_json(instancia, monkeypatch):
    pasta_testes = gerador.PASTA_DADOS / 'instancias_testes'
    monkeypatch.setattr(gerador, 'PASTA_INSTANCIAS', pasta_testes)
    resultado, caminho = gerador.gerar_problema(nome_ficheiro='teste.json')

    with caminho.open(encoding='utf-8') as ficheiro:
        assert json.load(ficheiro) == resultado
    assert resultado == instancia
    print(caminho)
