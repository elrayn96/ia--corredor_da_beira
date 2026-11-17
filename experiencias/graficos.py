"""Geração dos três gráficos obrigatórios a partir do CSV."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def _numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def gerar_graficos(caminho_csv, pasta_saida):
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    with Path(caminho_csv).open(encoding="utf-8-sig", newline="") as ficheiro:
        linhas = list(csv.DictReader(ficheiro))

    grupos = defaultdict(list)
    for linha in linhas:
        etiqueta = linha["algoritmo"]
        if linha.get("heuristica") not in (None, "", "—"):
            etiqueta += "+" + linha["heuristica"]
        if linha.get("peso") not in (None, "", "None"):
            etiqueta += f"(w={linha['peso']})"
        grupos[etiqueta].append(linha)

    especificacoes = (
        ("nos_expandidos", "Nós expandidos", "nos_expandidos_vs_dimensao.png", True),
        ("tempo_segundos", "Tempo (s)", "tempo_vs_dimensao.png", False),
        ("razao_custo_optimo", "Custo / custo óptimo", "custo_vs_optimo.png", False),
    )
    criados = []
    for campo, eixo_y, nome, logaritmico in especificacoes:
        figura, eixo = plt.subplots(figsize=(10, 6))
        for etiqueta, items in sorted(grupos.items()):
            pontos = []
            for item in items:
                x = _numero(item.get("dimensao"))
                y = _numero(item.get(campo))
                if x is not None and y is not None and y >= 0:
                    pontos.append((x, y))
            if pontos:
                pontos.sort()
                eixo.plot([p[0] for p in pontos], [p[1] for p in pontos],
                          marker="o", alpha=0.75, label=etiqueta)
        if logaritmico:
            eixo.set_yscale("log")
        eixo.set_xlabel("Dimensão da instância (arestas)")
        eixo.set_ylabel(eixo_y)
        eixo.grid(True, alpha=0.25)
        eixo.legend(fontsize=7, ncol=2)
        figura.tight_layout()
        destino = pasta / nome
        figura.savefig(destino, dpi=160)
        plt.close(figura)
        criados.append(destino)
    return criados
