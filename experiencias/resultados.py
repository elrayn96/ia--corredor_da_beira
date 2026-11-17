"""Serialização estável dos resultados experimentais."""

from __future__ import annotations

import csv
from pathlib import Path

CABECALHOS = (
    "caminho_instancia",
    "semente",
    "algoritmo",
    "heuristica",
    "peso",
    "limite",
    "estado_execucao",
    "mensagem",
    "custo_total",
    "custo_optimo",
    "razao_custo_optimo",
    "comprimento_caminho",
    "nos_gerados",
    "nos_expandidos",
    "nos_reexpandidos",
    "max_fronteira",
    "tempo_segundos",
    "memoria_pico_bytes",
)


def guardar_resultados_csv(resultados, caminho):
    """Grava apenas campos escalares, sempre na mesma ordem e em UTF-8."""
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8-sig") as ficheiro:
        escritor = csv.DictWriter(ficheiro, fieldnames=CABECALHOS, extrasaction="ignore")
        escritor.writeheader()
        for resultado in resultados:
            escritor.writerow({chave: resultado.get(chave) for chave in CABECALHOS})
