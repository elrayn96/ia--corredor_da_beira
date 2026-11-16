"""Conversao dos JSON reais do grupo para o contrato de Problema."""
import json
from pathlib import Path
from src.problema import Problema

RAIZ = Path(__file__).resolve().parents[2]
INSTANCIA_PADRAO = RAIZ / "dados/instancias_testes/teste.json"

def carregar_instancia(caminho=INSTANCIA_PADRAO):
    caminho = Path(caminho or INSTANCIA_PADRAO).resolve()
    with caminho.open(encoding="utf-8") as ficheiro:
        dados = json.load(ficheiro)
    if "rede" not in dados or "supermercados" not in dados:
        raise ValueError("Formato de instancia desconhecido")
    referencia = dados["rede"]["estradas"]
    caminho_estradas = (caminho.parent / referencia).resolve()
    with caminho_estradas.open(encoding="utf-8") as ficheiro:
        rede = json.load(ficheiro)
    estradas = {}
    for aresta in rede["estradas"]:
        a, b = aresta["origem"], aresta["destino"]
        atributos = {"distancia": aresta["distanciaKm"], "piso": aresta["piso"]}
        estradas.setdefault(a, {})[b] = atributos.copy()
        estradas.setdefault(b, {})[a] = atributos.copy()
    supermercados = {}
    for supermercado in dados["supermercados"]:
        localidade = supermercado["localidade"]
        if localidade in supermercados:
            raise ValueError(f"Supermercados duplicados em {localidade}")
        supermercados[localidade] = {"abertura": supermercado["abertura"],
                                    "fecho": supermercado["fecho"]}
    origem = dados.get("estadoInicial", {}).get("localidade", "Beira")
    return Problema(estradas, supermercados, origem)
