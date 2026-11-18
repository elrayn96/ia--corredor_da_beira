"""Bateria reproduzível exigida pelo enunciado do projecto."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from experiencias.analise import factor_ramificacao_efectivo
from experiencias.executar import executar_experiencia
from experiencias.graficos import gerar_graficos
from experiencias.resultados import CABECALHOS
from src.gerador import gerar_instancias_experimentais

RAIZ = Path(__file__).resolve().parent.parent
PASTA_INSTANCIAS = RAIZ / "dados" / "instancias_experimentais"
PASTA_RESULTADOS = RAIZ / "resultados_experimentais"
FICHEIRO_CHECKPOINT = PASTA_RESULTADOS / ".bateria_parcial.json"


def _assinatura_instancias(caminhos):
    resumo = hashlib.sha256()
    for caminho in caminhos:
        resumo.update(Path(caminho).read_bytes())
    return resumo.hexdigest()


def _chave_execucao(item):
    return (
        item.get("nivel"), int(item.get("indice", 0)), item.get("algoritmo"),
        item.get("heuristica"), item.get("peso"), item.get("limite"),
    )


def _carregar_checkpoint(destino, assinatura, limite_segundos):
    destino = Path(destino)
    if not destino.is_file():
        return []
    try:
        dados = json.loads(destino.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return []
    if (
        dados.get("assinatura_instancias") != assinatura
        or dados.get("limite_segundos") != limite_segundos
    ):
        return []
    return dados.get("resultados", [])


def _guardar_checkpoint(destino, assinatura, limite_segundos, resultados):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + ".tmp")
    temporario.write_text(
        json.dumps(
            {
                "assinatura_instancias": assinatura,
                "limite_segundos": limite_segundos,
                "resultados": resultados,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    temporario.replace(destino)


def configuracoes(caminho):
    base = {"caminho_instancia": str(caminho), "peso": None, "limite": None}
    yield base | {"algoritmo": "bfs", "heuristica": "h0"}
    yield base | {"algoritmo": "dfs", "heuristica": "h0", "limite": 40}
    yield base | {"algoritmo": "ids", "heuristica": "h0", "limite": 40}
    yield base | {"algoritmo": "ucs", "heuristica": "h0"}
    for heuristica in ("h1", "h2"):
        yield base | {"algoritmo": "busca_gulosa", "heuristica": heuristica}
    for heuristica in ("h0", "h1", "h2"):
        yield base | {"algoritmo": "a_star", "heuristica": heuristica}
    for peso in (1.25, 1.5, 2, 3):
        yield base | {
            "algoritmo": "a_star_ponderada", "heuristica": "h2", "peso": peso
        }


def _executar_caso(configuracao, limite_segundos, limite_memoria_bytes):
    """Executa um caso num processo isolado e devolve apenas dados escalares."""
    try:
        import resource

        resource.setrlimit(
            resource.RLIMIT_AS, (limite_memoria_bytes, limite_memoria_bytes)
        )
    except (ImportError, OSError, ValueError):
        # Windows não expõe resource.RLIMIT_AS; nesse sistema a memória de
        # pico continua a ser medida e o excesso é marcado após a execução.
        pass
    try:
        registo = executar_experiencia(configuracao, limite_segundos)
        registo.pop("solucao", None)
        registo.pop("eventos", None)
        if registo.get("memoria_pico_bytes", 0) > limite_memoria_bytes:
            registo["estado_execucao"] = "falhou"
            registo["mensagem"] = "Limite de 2 GB excedido."
        return registo
    except MemoryError:
        return {
            **configuracao, "estado_execucao": "falhou",
            "mensagem": "Limite de 2 GB excedido.", "custo_total": None,
        }
    except Exception as erro:  # noqa: BLE001 - cada ensaio tem de gerar uma linha
        return {
            **configuracao, "estado_execucao": "erro",
            "mensagem": f"{type(erro).__name__}: {erro}", "custo_total": None,
        }


def executar_bateria(
    limite_segundos=60, quantidade_por_nivel=10, trabalhadores=None,
    retomar=True,
):
    caminhos = gerar_instancias_experimentais(
        PASTA_INSTANCIAS, quantidade_por_nivel=quantidade_por_nivel
    )
    trabalhos = []
    for caminho in caminhos:
        instancia = json.loads(caminho.read_text(encoding="utf-8"))
        for configuracao in configuracoes(caminho):
            configuracao["semente"] = instancia["semente"]
            trabalhos.append((configuracao, instancia))

    assinatura = _assinatura_instancias(caminhos)
    resultados = (
        _carregar_checkpoint(FICHEIRO_CHECKPOINT, assinatura, limite_segundos)
        if retomar else []
    )
    concluidas = {_chave_execucao(item) for item in resultados}
    trabalhos = [
        trabalho for trabalho in trabalhos
        if _chave_execucao({
            **trabalho[0], "nivel": trabalho[1]["nivel"],
            "indice": trabalho[1]["indice"],
        }) not in concluidas
    ]
    if resultados:
        print(
            f"A retomar {len(resultados)} de "
            f"{quantidade_por_nivel * 3 * 13} execuções guardadas.",
            flush=True,
        )
    trabalhadores = trabalhadores or min(4, os.cpu_count() or 1)
    limite_memoria = 2 * 1024 ** 3
    with ProcessPoolExecutor(max_workers=trabalhadores) as executor:
        futuros = {
            executor.submit(
                _executar_caso, config, limite_segundos, limite_memoria
            ): instancia
            for config, instancia in trabalhos
        }
        total = quantidade_por_nivel * 3 * 13
        for futuro in as_completed(futuros):
            instancia = futuros[futuro]
            registo = futuro.result()
            registo.update(
                nivel=instancia["nivel"], dimensao=instancia["dimensao"],
                indice=instancia["indice"],
                caminho_instancia=str(
                    Path("dados/instancias_experimentais")
                    / Path(registo["caminho_instancia"]).name
                ),
            )
            resultados.append(registo)
            _guardar_checkpoint(
                FICHEIRO_CHECKPOINT, assinatura, limite_segundos, resultados
            )
            print(
                f"[{len(resultados):03d}/{total}] {instancia['nome']} · "
                f"{registo.get('algoritmo')} · {registo.get('estado_execucao')}",
                flush=True,
            )

    por_instancia = {}
    for item in resultados:
        chave = (item["nivel"], item["indice"])
        por_instancia.setdefault(chave, []).append(item)
    resultados_finais = []
    for resultados_instancia in por_instancia.values():
        optimos = [
            item["custo_total"] for item in resultados_instancia
            if item["algoritmo"] == "a_star" and item["heuristica"] == "h2"
            and item["custo_total"] is not None
        ]
        custo_optimo = optimos[0] if optimos else None
        for item in resultados_instancia:
            item["custo_optimo"] = custo_optimo
            custo = item["custo_total"]
            item["razao_custo_optimo"] = (
                None if custo is None or custo_optimo is None else custo / custo_optimo
            )
            item["b_efetivo"] = factor_ramificacao_efectivo(
                item.get("nos_expandidos", 0), item.get("comprimento_caminho") or 0
            )
        resultados_finais.extend(resultados_instancia)
    resultados_finais.sort(
        key=lambda x: (x["nivel"], x["indice"], x.get("algoritmo", ""),
                       x.get("heuristica") or "", x.get("peso") or 0)
    )
    return resultados_finais


def guardar(resultados, destino):
    extras = ("nivel", "dimensao", "indice", "b_efetivo")
    cabecalhos = CABECALHOS + extras
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8-sig", newline="") as ficheiro:
        escritor = csv.DictWriter(
            ficheiro, fieldnames=cabecalhos, extrasaction="ignore",
            lineterminator="\n",
        )
        escritor.writeheader()
        escritor.writerows(resultados)
    return destino


def guardar_tabela_ponderada(resultados, destino):
    campos = (
        "nivel", "indice", "semente", "peso", "custo_total", "custo_optimo",
        "razao_custo_optimo", "limite_teorico", "respeita_limite",
    )
    linhas = []
    for item in resultados:
        if item.get("algoritmo") != "a_star_ponderada":
            continue
        razao = item.get("razao_custo_optimo")
        peso = item.get("peso")
        linhas.append({
            **item,
            "limite_teorico": peso,
            "respeita_limite": (
                "N/A" if razao is None else bool(float(razao) <= float(peso) + 1e-9)
            ),
        })
    destino = Path(destino)
    with destino.open("w", encoding="utf-8-sig", newline="") as ficheiro:
        escritor = csv.DictWriter(
            ficheiro, fieldnames=campos, extrasaction="ignore",
            lineterminator="\n",
        )
        escritor.writeheader()
        escritor.writerows(linhas)
    return destino


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=float, default=60)
    parser.add_argument("--quantidade-por-nivel", type=int, default=10)
    parser.add_argument("--trabalhadores", type=int, default=None)
    parser.add_argument(
        "--reiniciar", action="store_true",
        help="ignora um checkpoint compatível e reinicia todas as execuções",
    )
    args = parser.parse_args()
    resultados = executar_bateria(
        args.limite, args.quantidade_por_nivel, args.trabalhadores,
        retomar=not args.reiniciar,
    )
    csv_final = guardar(resultados, PASTA_RESULTADOS / "resultados.csv")
    guardar_tabela_ponderada(
        resultados, PASTA_RESULTADOS / "a_star_ponderada_vs_limite.csv"
    )
    gerar_graficos(csv_final, PASTA_RESULTADOS / "graficos")
    FICHEIRO_CHECKPOINT.unlink(missing_ok=True)
    print(csv_final)


if __name__ == "__main__":
    main()
