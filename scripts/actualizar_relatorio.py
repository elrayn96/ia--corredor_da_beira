#!/usr/bin/env python3
"""Actualiza o DOCX oficial com resultados reproduzíveis da bateria."""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches
from docx.text.paragraph import Paragraph


def numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def substituir_em_xml(documento, antigo, novo):
    for no in documento.element.body.iter():
        if no.tag in {qn("w:t"), qn("m:t")} and no.text and antigo in no.text:
            no.text = no.text.replace(antigo, novo)


def remover_capa_duplicada(documento):
    """Remove a primeira das duas capas idênticas do documento de origem."""
    corpo = documento.element.body
    ocorrencias = []
    for indice, elemento in enumerate(list(corpo)):
        texto = "".join(no.text or "" for no in elemento.iter() if no.tag == qn("w:t"))
        if "UNIVERSIDADE EDUARDO MONDLANE" in texto:
            ocorrencias.append(indice)
    if len(ocorrencias) >= 2:
        for elemento in list(corpo)[: ocorrencias[1]]:
            corpo.remove(elemento)


def inserir_paragrafo_depois(paragrafo):
    novo_elemento = OxmlElement("w:p")
    paragrafo._p.addnext(novo_elemento)
    return Paragraph(novo_elemento, paragrafo._parent)


def media(linhas, campo):
    valores = [numero(linha.get(campo)) for linha in linhas]
    valores = [valor for valor in valores if valor is not None]
    return None if not valores else statistics.fmean(valores)


def fmt(valor, casas=1):
    if valor is None:
        return "—"
    return f"{valor:,.{casas}f}".replace(",", " ").replace(".", ",")


def chave_linha(linha):
    return (
        linha.get("algoritmo", ""),
        linha.get("heuristica", ""),
        numero(linha.get("peso")),
    )


def preencher_tabela_resultados(tabela, linhas):
    grupos = defaultdict(list)
    for linha in linhas:
        grupos[chave_linha(linha)].append(linha)
    mapa = {
        1: ("bfs", "h0", None),
        2: ("dfs", "h0", None),
        3: ("ids", "h0", None),
        4: ("ucs", "h0", None),
        5: ("busca_gulosa", "h1", None),
        6: ("busca_gulosa", "h2", None),
        7: ("a_star", "h1", None),
        8: ("a_star", "h2", None),
        9: ("a_star_ponderada", "h2", 1.5),
        14: ("a_star_ponderada", "h2", 1.25),
        15: ("a_star_ponderada", "h2", 2.0),
        16: ("a_star_ponderada", "h2", 3.0),
    }
    tabela.cell(0, 4).text = "Custo/óptimo"
    for indice, chave in mapa.items():
        items = grupos.get(chave, [])
        resolvidas = [x for x in items if x.get("estado_execucao") == "concluida"]
        valores = (
            f"{len(resolvidas)}/{len(items)}",
            fmt(media(resolvidas, "custo_total")),
            fmt(media(resolvidas, "razao_custo_optimo"), 3),
            fmt(media(items, "nos_expandidos"), 0),
            fmt(media(items, "nos_gerados"), 0),
            fmt(media(items, "max_fronteira"), 0),
            fmt(media(items, "tempo_segundos"), 3),
            fmt((media(items, "memoria_pico_bytes") or 0) / 1024**2, 2),
        )
        for coluna, valor in enumerate(valores, 2):
            tabela.cell(indice, coluna).text = valor
    for indice in (10, 11, 12, 13):
        for coluna in range(2, 10):
            tabela.cell(indice, coluna).text = "Não exigido"


def actualizar(caminho_docx, caminho_csv, grafico, destino, testes):
    documento = Document(caminho_docx)
    with Path(caminho_csv).open(encoding="utf-8-sig", newline="") as ficheiro:
        linhas = list(csv.DictReader(ficheiro))

    substituicoes = {
        "Inteligencia Artificical I": "Inteligência Artificial I",
        "Julaya, Naem Elisas": "Julaya, Naeem",
        "Julaya, Naeem Osama": "Julaya, Naeem",
        "Carlos, Lucia das Dores": "Carlos, Lúcia",
        "Cossa, Elias": "Cossa Júnior, Elias",
        "Massingue, Armando Alberto": "Massingue, Armando",
        "Modesto, Adila da Gloria Ricardo": "Modesto, Adila",
        "Modesto, Adila da Gloria": "Modesto, Adila",
        "182 testes": f"{testes} testes",
        "182 testes pytest": f"{testes} testes pytest",
        "Type equation here.": "|S| ≤ |L| × 2^7 × N_T × N_F",
        "2128 combinações": "2^7 = 128 combinações",
        "Error! Bookmark not defined.": "ver Anexo D",
        "A bateria experimental global de comparação de algoritmos permanece por realizar": "A bateria experimental global foi executada de forma reproduzível",
        "a execução de uma campanha experimental reproduzível com limites de recursos e registo estatístico": "a repetição da campanha experimental noutras máquinas para estudar a variabilidade",
    }
    for antigo, novo in substituicoes.items():
        substituir_em_xml(documento, antigo, novo)

    documento.paragraphs[59].text = (
        "O projecto modela a distribuição de produtos refrigerados no Corredor da "
        "Beira como um problema de procura. O estado imutável inclui localidade, "
        "entregas concluídas, tempo e combustível. Foram implementadas BFS, DFS, IDS, "
        "UCS, Gulosa, A* e A* Ponderada, além de LDS, com as heurísticas h0, h1 e h2. "
        "A solução integra geradores reproduzíveis, uma instância base com percurso "
        "validado, trinta instâncias experimentais viáveis, testes automatizados e uma "
        "interface que apresenta mapa, árvore, solução e métricas. A bateria compara os "
        "algoritmos sob limites de 60 segundos e 2 GB e exporta CSV e gráficos."
    )

    total = len(linhas)
    concluidas = sum(x.get("estado_execucao") == "concluida" for x in linhas)
    interrompidas = sum(x.get("estado_execucao") == "interrompida" for x in linhas)
    documento.paragraphs[300].text = (
        "A instância base e as instâncias experimentais usam a semente obrigatória "
        "202601. Um único gerador pseudo-aleatório é inicializado com esse valor e o "
        "seu estado avança para produzir dez casos distintos por nível. A instância "
        "base possui um percurso testemunha validado pelas transições do domínio."
    )
    documento.paragraphs[301].text = (
        f"A suite automatizada executada com pytest contém {testes} testes. Inclui domínio, "
        "algoritmos, heurísticas, interface, serviços, contrato abstracto, imutabilidade, "
        "limites, reexpansões, admissibilidade e geração experimental."
    )
    documento.paragraphs[310].text = (
        "A bateria experimental utilizou três níveis de dificuldade, dez instâncias "
        "reproduzíveis por nível e uma única semente 202601. Cada par algoritmo–instância "
        "foi executado em processo isolado, com limite de 60 segundos e 2 GB. Foram "
        "registados custo, comprimento, nós gerados e expandidos, reexpansões, fronteira "
        "máxima, tempo e memória de pico."
    )
    documento.paragraphs[312].text = (
        f"Foram registadas {total} execuções: {concluidas} concluíram com solução e "
        f"{interrompidas} atingiram o limite temporal. A Tabela 5 apresenta médias "
        "calculadas directamente do CSV entregue. Uma execução interrompida é mantida "
        "nos resultados e não é interpretada como prova de inexistência de solução."
    )
    preencher_tabela_resultados(documento.tables[7], linhas)

    for linha_tabela, nivel in ((2, "media"), (3, "grande")):
        amostra = [x for x in linhas if x.get("nivel") == nivel]
        h2_concluida = [
            x
            for x in amostra
            if x.get("algoritmo") == "a_star"
            and x.get("heuristica") == "h2"
            and x.get("estado_execucao") == "concluida"
        ]
        documento.tables[6].cell(linha_tabela, 1).text = fmt(
            media(h2_concluida, "comprimento_caminho"), 1
        )
        h0_items = [
            x
            for x in amostra
            if x.get("algoritmo") == "a_star" and x.get("heuristica") == "h0"
        ]
        documento.tables[6].cell(linha_tabela, 2).text = fmt(
            media(h0_items, "nos_expandidos"), 0
        )
        for coluna, heuristica in ((3, "h1"), (4, "h2")):
            items = [
                x
                for x in amostra
                if x.get("algoritmo") == "a_star" and x.get("heuristica") == heuristica
            ]
            documento.tables[6].cell(linha_tabela, coluna).text = fmt(
                media(items, "nos_expandidos"), 0
            )
        for coluna, heuristica in ((5, "h1"), (6, "h2")):
            items = [
                x
                for x in amostra
                if x.get("algoritmo") == "a_star" and x.get("heuristica") == heuristica
            ]
            documento.tables[6].cell(linha_tabela, coluna).text = fmt(
                media(items, "b_efetivo"), 3
            )
    documento.paragraphs[314].text = (
        "As médias incluem as execuções interrompidas nas métricas de recursos; "
        "custos são calculados apenas para soluções encontradas."
    )

    documento.paragraphs[318].text = (
        "As instâncias pequenas confirmam o funcionamento dos sete algoritmos. À medida "
        "que crescem as alternativas rodoviárias, as buscas não informadas aumentam a "
        "fronteira e atingem o limite com maior frequência. A h2 baseada em MST reduz a "
        "exploração relativamente a h0 e h1. O A* ponderado tende a expandir menos nós, "
        "mas o seu custo deve ser interpretado juntamente com a razão para o óptimo e o "
        "limite teórico w."
    )
    documento.paragraphs[320].text = (
        "O estado não pode ser apenas a cidade actual porque duas visitas à mesma cidade "
        "podem ter entregas concluídas, horários e combustível diferentes. Se essas "
        "componentes fossem removidas, estados operacionalmente distintos seriam tratados "
        "como iguais, eliminando percursos válidos ou aceitando transições inválidas. A "
        "representação completa aumenta o espaço para, no máximo, |L| × 2^7 × N_T × N_F, "
        "mas preserva toda a informação necessária ao princípio de Markov."
    )
    documento.paragraphs[323].text = (
        f"O grupo implementou o domínio, as sete estratégias obrigatórias, o A* "
        f"Ponderado, as heurísticas h0, h1 e h2, a interface e {testes} testes. A "
        "campanha experimental reproduzível compara trinta instâncias e conserva "
        "também as execuções interrompidas. Os resultados confirmam que a informação "
        "heurística reduz a exploração, embora desempenho e custo dependam da instância."
    )
    documento.paragraphs[325].text = (
        "Os dados rodoviários são simulados para fins académicos. Resultados temporais "
        "dependem do computador e o limite de memória rígido é suportado directamente em "
        "sistemas Unix; no Windows, a memória é medida e validada após cada execução."
    )
    documento.paragraphs[327].text = (
        "Como trabalho futuro propõe-se repetir a campanha noutras máquinas, validar os "
        "dados rodoviários com fontes oficiais e estudar técnicas adicionais de dominância "
        "de estados, preservando a optimalidade."
    )
    documento.paragraphs[351].text = (
        "Código relevante: src/contrato_busca.py (Problema, No e caminho); "
        "src/problema.py (domínio); src/buscas/ (sete estratégias); src/heuristicas/ "
        "(h0, h1 e h2); experiencias/bateria.py e experiencias/graficos.py. O código "
        "integral acompanha o relatório no repositório entregue."
    )
    paragrafo_figura = documento.paragraphs[316]
    paragrafo_figura.text = ""
    graficos = (
        Path(grafico),
        Path(grafico).with_name("tempo_vs_dimensao.png"),
        Path(grafico).with_name("custo_vs_optimo.png"),
    )
    paragrafo_actual = paragrafo_figura
    for indice, imagem in enumerate(graficos):
        if indice:
            paragrafo_actual = inserir_paragrafo_depois(paragrafo_actual)
            paragrafo_actual.paragraph_format.page_break_before = True
        paragrafo_actual.paragraph_format.keep_together = True
        paragrafo_actual.add_run().add_picture(str(imagem), width=Inches(5.6))

    documento.add_heading("ANEXO D – LISTA DE VERIFICAÇÃO ANTES DA ENTREGA", level=1)
    for item in (
        "Relatório PDF abre e contém tabelas e gráficos.",
        "CSV e três gráficos estão incluídos.",
        "README contém instruções de instalação e execução.",
        "A pasta .git acompanha o pacote final.",
        "O vídeo e os links foram testados com as permissões do docente.",
    ):
        documento.add_paragraph("☐ " + item)
    remover_capa_duplicada(documento)
    documento.save(destino)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--docx", default="docs/relatorio/IA_RELATORIO_GRUPO_01_LAB.docx"
    )
    parser.add_argument("--csv", default="resultados_experimentais/resultados.csv")
    parser.add_argument(
        "--grafico",
        default="resultados_experimentais/graficos/nos_expandidos_vs_dimensao.png",
    )
    parser.add_argument(
        "--destino", default="docs/relatorio/IA_RELATORIO_GRUPO_01_LAB_ACTUALIZADO.docx"
    )
    parser.add_argument("--testes", type=int, required=True)
    args = parser.parse_args()
    actualizar(args.docx, args.csv, args.grafico, args.destino, args.testes)


if __name__ == "__main__":
    main()
