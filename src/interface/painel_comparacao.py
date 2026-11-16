"""Tabela e gráficos comparativos de execuções de busca."""

from __future__ import annotations

from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

COLUNAS = (
    "algoritmo",
    "heuristica",
    "estado_execucao",
    "custo_total",
    "nos_expandidos",
    "tempo_segundos",
    "memoria_pico_bytes",
)
TITULOS = (
    "Algoritmo",
    "Heurística",
    "Estado",
    "Custo",
    "Expandidos",
    "Tempo (s)",
    "Memória (bytes)",
)


def _valor_resultado(resultado, chave, padrao=None):
    if chave in resultado:
        return resultado.get(chave)
    return resultado.get("estatisticas", {}).get(chave, padrao)


def preparar_comparacao(resultados):
    """Normaliza registos de experiências e resultados directos do serviço."""
    linhas = []
    for indice, resultado in enumerate(resultados, 1):
        solucao = resultado.get("solucao")
        custo = _valor_resultado(resultado, "custo_total")
        if custo is None and solucao is not None:
            custo = solucao.get_custo_total()
        linha = {
            "algoritmo": resultado.get("algoritmo", f"Execução {indice}"),
            "heuristica": resultado.get("heuristica") or "—",
            "estado_execucao": resultado.get("estado_execucao", "concluida"),
            "custo_total": custo,
            "nos_expandidos": _valor_resultado(resultado, "nos_expandidos", 0),
            "tempo_segundos": _valor_resultado(resultado, "tempo_segundos", 0.0),
            "memoria_pico_bytes": _valor_resultado(
                resultado, "memoria_pico_bytes", 0
            ),
            "mensagem": resultado.get("mensagem", ""),
        }
        linhas.append(linha)
    return linhas


class PainelComparacao(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._linhas = []
        self._criar_widgets()

    def _criar_widgets(self):
        tabela_frame = ttk.Frame(self, padding=8)
        tabela_frame.pack(fill="x")
        self._tabela = ttk.Treeview(
            tabela_frame, columns=COLUNAS, show="headings", height=7
        )
        for coluna, titulo in zip(COLUNAS, TITULOS):
            self._tabela.heading(coluna, text=titulo)
            self._tabela.column(coluna, width=125, anchor="center")
        barra = ttk.Scrollbar(
            tabela_frame, orient="vertical", command=self._tabela.yview
        )
        self._tabela.configure(yscrollcommand=barra.set)
        self._tabela.pack(side="left", fill="x", expand=True)
        barra.pack(side="right", fill="y")

        self._figura = Figure(figsize=(9, 5), dpi=100, constrained_layout=True)
        self._eixos = self._figura.subplots(2, 2)
        self._canvas = FigureCanvasTkAgg(self._figura, master=self)
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=4)
        self._desenhar()

    def mostrar_comparacao(self, resultados):
        self._linhas = preparar_comparacao(resultados)
        for item in self._tabela.get_children():
            self._tabela.delete(item)
        for linha in self._linhas:
            valores = []
            for chave in COLUNAS:
                valor = linha[chave]
                if valor is None:
                    valor = "—"
                elif chave == "tempo_segundos":
                    valor = f"{float(valor):.6f}"
                valores.append(valor)
            self._tabela.insert("", "end", values=valores)
        self._desenhar()

    def limpar(self):
        self.mostrar_comparacao([])

    def _desenhar(self):
        especificacoes = (
            ("custo_total", "Custo total"),
            ("nos_expandidos", "Nós expandidos"),
            ("tempo_segundos", "Tempo (s)"),
            ("memoria_pico_bytes", "Memória de pico (bytes)"),
        )
        rotulos = [
            f"{linha['algoritmo']}\n{linha['heuristica']}" for linha in self._linhas
        ]
        cores = [
            "#4c78a8" if linha["estado_execucao"] == "concluida" else "#d95f59"
            for linha in self._linhas
        ]
        for eixo, (chave, titulo) in zip(self._eixos.flat, especificacoes):
            eixo.clear()
            valores = [float(linha[chave] or 0) for linha in self._linhas]
            eixo.bar(rotulos, valores, color=cores)
            eixo.set_title(titulo)
            eixo.tick_params(axis="x", labelsize=7)
            eixo.grid(axis="y", alpha=0.25)
            if not self._linhas:
                eixo.text(
                    0.5,
                    0.5,
                    "Sem resultados para comparar.",
                    ha="center",
                    va="center",
                    transform=eixo.transAxes,
                )
        self._canvas.draw_idle()
