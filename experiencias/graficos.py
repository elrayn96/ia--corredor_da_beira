"""Geração dos três gráficos obrigatórios a partir do CSV."""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import median

import matplotlib.pyplot as plt
import numpy as np

NIVEIS = ("pequena", "media", "grande")
FAMILIAS = (
    ("Não informadas", ("bfs", "dfs", "ids", "ucs")),
    ("Busca gulosa", ("busca_gulosa",)),
    ("A*", ("a_star",)),
    ("A* ponderado", ("a_star_ponderada",)),
)
ORDEM_CONFIGURACOES = (
    ("bfs", "h0", None),
    ("dfs", "h0", None),
    ("ids", "h0", None),
    ("ucs", "h0", None),
    ("busca_gulosa", "h1", None),
    ("busca_gulosa", "h2", None),
    ("a_star", "h0", None),
    ("a_star", "h1", None),
    ("a_star", "h2", None),
    ("a_star_ponderada", "h2", "1.25"),
    ("a_star_ponderada", "h2", "1.5"),
    ("a_star_ponderada", "h2", "2"),
    ("a_star_ponderada", "h2", "3"),
)


def _numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _peso_normalizado(valor):
    numero = _numero(valor)
    return f"{numero:g}" if numero is not None else None


def _chave(linha):
    return (
        linha.get("algoritmo", ""),
        linha.get("heuristica") or "h0",
        _peso_normalizado(linha.get("peso")),
    )


def _rotulo(chave):
    algoritmo, heuristica, peso = chave
    nomes = {
        "bfs": "BFS",
        "dfs": "DFS",
        "ids": "IDS",
        "ucs": "UCS",
        "busca_gulosa": "Gulosa",
        "a_star": "A*",
        "a_star_ponderada": "A* pond.",
    }
    rotulo = nomes.get(algoritmo, algoritmo)
    if algoritmo in {"busca_gulosa", "a_star", "a_star_ponderada"}:
        rotulo += f" {heuristica}"
    if peso is not None:
        rotulo += f" (w={peso.replace('.', ',')})"
    return rotulo


def _configuracoes_presentes(linhas):
    presentes = {_chave(linha) for linha in linhas}
    conhecidas = [chave for chave in ORDEM_CONFIGURACOES if chave in presentes]
    return conhecidas + sorted(presentes - set(conhecidas))


def _etiquetas_niveis(linhas):
    etiquetas = []
    for nivel in NIVEIS:
        dimensoes = [
            _numero(linha.get("dimensao"))
            for linha in linhas
            if linha.get("nivel") == nivel
            and _numero(linha.get("dimensao")) is not None
        ]
        dimensao = int(median(dimensoes)) if dimensoes else 0
        etiquetas.append(f"{nivel.capitalize()}\n{dimensao} arestas")
    return etiquetas


def _aplicar_estilo(figura, titulo, subtitulo):
    figura.suptitle(titulo, fontsize=17, fontweight="bold", x=0.06, y=0.985, ha="left")
    figura.text(0.06, 0.935, subtitulo, fontsize=10.5, color="#475569", ha="left")
    figura.text(
        0.06,
        0.018,
        "Linha: mediana de 10 instâncias  •  Faixa: 25.º–75.º percentil",
        fontsize=9,
        color="#64748b",
        ha="left",
    )


def _grafico_recursos(linhas, campo, titulo, eixo_y, destino, logaritmico=True):
    figura, eixos = plt.subplots(2, 2, figsize=(13.5, 8.4), sharex=True)
    _aplicar_estilo(
        figura,
        titulo,
        "Resultados agregados por nível; interrupções contam nas métricas de recursos.",
    )
    etiquetas_x = _etiquetas_niveis(linhas)
    cores = plt.get_cmap("tab10").colors

    for eixo, (familia, algoritmos) in zip(eixos.flat, FAMILIAS, strict=True):
        configs = [
            chave
            for chave in _configuracoes_presentes(linhas)
            if chave[0] in algoritmos
        ]
        for indice, chave in enumerate(configs):
            valores_nivel = []
            for nivel in NIVEIS:
                valores = [
                    _numero(linha.get(campo))
                    for linha in linhas
                    if linha.get("nivel") == nivel and _chave(linha) == chave
                ]
                valores_nivel.append(
                    [valor for valor in valores if valor is not None and valor > 0]
                )
            x_validos, medias, inferiores, superiores = [], [], [], []
            for x, valores in enumerate(valores_nivel):
                if valores:
                    x_validos.append(x)
                    medias.append(median(valores))
                    inferiores.append(float(np.percentile(valores, 25)))
                    superiores.append(float(np.percentile(valores, 75)))
            if not x_validos:
                continue
            cor = cores[indice % len(cores)]
            eixo.plot(
                x_validos,
                medias,
                color=cor,
                marker="o",
                linewidth=2.2,
                markersize=5.5,
                label=_rotulo(chave),
            )
            eixo.fill_between(x_validos, inferiores, superiores, color=cor, alpha=0.12)

        eixo.set_title(familia, fontsize=12.5, fontweight="bold", loc="left")
        eixo.set_xticks(range(len(NIVEIS)), etiquetas_x, fontsize=9.5)
        eixo.grid(True, which="major", axis="y", alpha=0.22)
        eixo.spines[["top", "right"]].set_visible(False)
        if logaritmico:
            eixo.set_yscale("log")
        identificadores, rotulos = eixo.get_legend_handles_labels()
        if identificadores:
            eixo.legend(
                identificadores,
                rotulos,
                loc="best",
                fontsize=8.5,
                frameon=False,
                ncol=2,
            )

    figura.supylabel(eixo_y, fontsize=11, x=0.018)
    figura.subplots_adjust(
        left=0.075, right=0.98, top=0.86, bottom=0.11, hspace=0.34, wspace=0.18
    )
    figura.savefig(destino, dpi=220, facecolor="white")
    plt.close(figura)


def _grafico_custo(linhas, destino):
    configuracoes = _configuracoes_presentes(linhas)
    figura, (eixo_custo, eixo_sucesso) = plt.subplots(1, 2, figsize=(13.5, 8.4))
    figura.suptitle(
        "Qualidade das soluções e taxa de sucesso",
        fontsize=17,
        fontweight="bold",
        x=0.06,
        y=0.985,
        ha="left",
    )
    figura.text(
        0.06,
        0.935,
        "Razão 1,00 é o óptimo; cinzento indica fim do tempo sem solução.",
        fontsize=10.5,
        color="#475569",
        ha="left",
    )

    custos = np.full((len(configuracoes), len(NIVEIS)), np.nan)
    sucessos = np.zeros((len(configuracoes), len(NIVEIS)))
    for i, chave in enumerate(configuracoes):
        for j, nivel in enumerate(NIVEIS):
            grupo = [
                linha
                for linha in linhas
                if _chave(linha) == chave and linha.get("nivel") == nivel
            ]
            razoes = [
                _numero(linha.get("razao_custo_optimo"))
                for linha in grupo
                if _numero(linha.get("razao_custo_optimo")) is not None
            ]
            if razoes:
                custos[i, j] = median(razoes)
            sucessos[i, j] = 100 * len(razoes) / len(grupo) if grupo else 0

    mapa_custos = plt.get_cmap("YlGn").copy()
    mapa_custos.with_extremes(bad="#e2e8f0")
    maximo = max(
        1.05,
        float(np.nanmax(custos)) if np.any(~np.isnan(custos)) else 1.05,
    )
    imagem_custo = eixo_custo.imshow(
        custos, aspect="auto", cmap=mapa_custos, vmin=1, vmax=maximo
    )
    imagem_sucesso = eixo_sucesso.imshow(
        sucessos, aspect="auto", cmap="Blues", vmin=0, vmax=100
    )

    rotulos_y = [_rotulo(chave) for chave in configuracoes]
    rotulos_x = [nivel.capitalize() for nivel in NIVEIS]
    for eixo, titulo in (
        (eixo_custo, "Custo obtido / custo óptimo"),
        (eixo_sucesso, "Execuções que encontraram solução"),
    ):
        eixo.set_title(titulo, fontsize=12.5, fontweight="bold", loc="left", pad=12)
        eixo.set_xticks(range(len(NIVEIS)), rotulos_x, fontsize=10)
        eixo.set_yticks(range(len(configuracoes)))
        eixo.tick_params(length=0)
        eixo.spines[:].set_visible(False)
    eixo_custo.set_yticklabels(rotulos_y, fontsize=9.5)
    eixo_sucesso.set_yticklabels([])

    for i in range(len(configuracoes)):
        for j in range(len(NIVEIS)):
            custo = custos[i, j]
            texto_custo = "—" if np.isnan(custo) else f"{custo:.2f}×".replace(".", ",")
            eixo_custo.text(
                j,
                i,
                texto_custo,
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
            )
            taxa = sucessos[i, j]
            cor = "white" if taxa >= 60 else "#0f172a"
            eixo_sucesso.text(
                j,
                i,
                f"{taxa:.0f}%",
                ha="center",
                va="center",
                fontsize=9,
                color=cor,
                fontweight="bold",
            )

    barra_custo = figura.colorbar(
        imagem_custo,
        ax=eixo_custo,
        orientation="horizontal",
        fraction=0.055,
        pad=0.08,
    )
    barra_custo.set_label("Razão de custo (menor é melhor)", fontsize=9)
    barra_sucesso = figura.colorbar(
        imagem_sucesso,
        ax=eixo_sucesso,
        orientation="horizontal",
        fraction=0.055,
        pad=0.08,
    )
    barra_sucesso.set_label("Taxa de sucesso (%)", fontsize=9)
    figura.subplots_adjust(left=0.17, right=0.98, top=0.86, bottom=0.12, wspace=0.16)
    figura.savefig(destino, dpi=220, facecolor="white")
    plt.close(figura)


def gerar_graficos(caminho_csv, pasta_saida):
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    with Path(caminho_csv).open(encoding="utf-8-sig", newline="") as ficheiro:
        linhas = list(csv.DictReader(ficheiro))

    destinos = [
        pasta / "nos_expandidos_vs_dimensao.png",
        pasta / "tempo_vs_dimensao.png",
        pasta / "custo_vs_optimo.png",
    ]
    _grafico_recursos(
        linhas,
        "nos_expandidos",
        "Esforço de busca por dimensão da instância",
        "Nós expandidos (escala logarítmica)",
        destinos[0],
    )
    _grafico_recursos(
        linhas,
        "tempo_segundos",
        "Tempo de execução por dimensão da instância",
        "Tempo em segundos (escala logarítmica)",
        destinos[1],
    )
    _grafico_custo(linhas, destinos[2])
    return destinos
