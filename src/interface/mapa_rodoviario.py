"""Mapa esquematico da rede: nao representa coordenadas geograficas."""

import math
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

# Verde da solução coerente com Elias; localidades douradas como na referência.
CORES = {
    "localidade": "#ffcb45",
    "supermercado": "#ffe08a",
    "origem": "#8fd19e",
    "solucao": "#4caf50",
    "estrada": "#888888",
}

# Posições locais estáveis, apenas para leitura da rede; não são latitude/longitude.
POSICOES = {
    "Beira": (88, 20),
    "Dondo": (82, 30),
    "Nhamatanda": (77, 46),
    "Inchope": (56, 45),
    "Gorongosa": (63, 72),
    "Gondola": (37, 42),
    "Chimoio": (33, 55),
    "Manica": (8, 56),
    "Catandica": (15, 80),
    "Muxunguè": (38, 75),
    "Caia": (94, 69),
    "Mafambisse": (96, 54),
    "Mutua": (46, 14),
    "Lamego": (46, 27),
    "Vanduzi": (18, 44),
}

PISOS = {
    1: ("#ff4149", "Muito degradado", 40),
    2: ("#ff8a35", "Degradado", 55),
    3: ("#ffd447", "Razoável", 70),
    4: ("#81e34e", "Bom", 80),
    5: ("#338aff", "Muito bom", 90),
}


def preparar_posicoes(localidades):
    """Prefere coordenadas x/y dos dados, depois o esquema local fixo."""
    total = max(len(localidades), 1)
    return {
        l["nome"]: (
            (l["x"], l["y"])
            if "x" in l and "y" in l
            else POSICOES.get(
                l["nome"],
                (math.cos(2 * math.pi * i / total), math.sin(2 * math.pi * i / total)),
            )
        )
        for i, l in enumerate(localidades)
    }


def obter_localidade(estado):
    if isinstance(estado, dict):
        return estado["localidade"]
    if hasattr(estado, "get_localidade"):
        return estado.get_localidade()
    return estado.localidade


def segmentos_percurso(estados, accoes):
    """Aceita o Estado actual e estados com atributo publico localidade."""
    estados, accoes = list(estados), list(accoes)
    if estados and len(estados) != len(accoes) + 1:
        raise ValueError("O percurso deve ter um estado a mais que as accoes.")
    if not estados and accoes:
        raise ValueError("As accoes precisam dos estados do percurso.")
    nomes = [obter_localidade(estado) for estado in estados]
    segmentos = []
    for a, b, accao in zip(nomes, nomes[1:], accoes):
        tipo = accao.get("tipo") if isinstance(accao, dict) else accao.get_tipo()
        if tipo == "deslocar":
            segmentos.append((a, b))
    return segmentos


def supermercados_da_instancia(instancia):
    """Normaliza supermercados dos formatos gerado e directo."""
    supermercados = instancia.get("supermercados", [])
    if isinstance(supermercados, dict):
        return {
            localidade: {"localidade": localidade, **dados}
            for localidade, dados in supermercados.items()
        }
    return {supermercado["localidade"]: supermercado for supermercado in supermercados}


class MapaRodoviario(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Cartao.TFrame")
        self._rede = {"localidades": [], "estradas": []}
        self._segmentos = []
        self._aresta_seleccionada = None
        self._ultima_explorada = None
        self._supermercados = {}
        self._origem = "Beira"
        self._posicoes = {}
        cabecalho = ttk.Frame(self, padding=(16, 12), style="Cartao.TFrame")
        cabecalho.pack(fill="x")
        ttk.Label(
            cabecalho,
            text="Rede Rodoviária — Cadeia de Frio no Corredor da Beira",
            font=("Segoe UI", 14, "bold"),
            style="Cartao.TLabel",
            wraplength=900,
        ).pack(anchor="w")
        ttk.Label(
            cabecalho, text="Localidades, ligações, distâncias (km) e estado do piso",
            style="Cartao.TLabel"
        ).pack(anchor="w")
        corpo = ttk.Panedwindow(self, orient="horizontal")
        corpo.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        area_mapa = tk.Frame(corpo, bg="#173c37")
        lateral = ttk.Frame(corpo, padding=8, width=340, style="Cartao.TFrame")
        corpo.add(area_mapa, weight=5)
        corpo.add(lateral, weight=2)
        self._divisao_mapa = corpo
        self._criar_legendas(lateral)
        self.after_idle(self._ajustar_paineis)
        self._figura = Figure(figsize=(9, 7), dpi=100, facecolor="#173c37")
        self._figura.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
        self._eixo = self._figura.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figura, master=area_mapa)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._barra = NavigationToolbar2Tk(self._canvas, area_mapa, pack_toolbar=False)
        # A barra de ferramentas fica disponível no código, mas oculta por padrão.
        # O mapa ganha espaço vertical; pode ser reactivada quando necessário.
        self._detalhes = ttk.Label(
            self, text="Seleccione uma localidade para ver os detalhes."
        )
        self._detalhes.pack(fill="x", padx=6, pady=4)
        self._canvas.mpl_connect("pick_event", self._seleccionar)
        self._desenhar()

    def _ajustar_paineis(self):
        largura = self._divisao_mapa.winfo_width()
        if largura > 650:
            self._divisao_mapa.sashpos(0, max(360, largura - 385))

    def mostrar_exploracao(self, localidade):
        """Assinala a localidade expandida, sem a confundir com uma solução."""
        if localidade in self._posicoes and localidade != self._ultima_explorada:
            self._ultima_explorada = localidade
            self._detalhes.configure(text=f"Em exploração: {localidade} (não é a rota final)")
            self._desenhar()

    def limpar_exploracao(self):
        if self._ultima_explorada is not None:
            self._ultima_explorada = None
            self._desenhar()

    def _criar_legendas(self, parent):
        legenda = ttk.LabelFrame(parent, text="Legenda", padding=10, style="Cartao.TLabelframe")
        legenda.pack(fill="x", pady=(0, 10))
        for texto, cor in (
            ("Localidade", "#b17e00"),
            ("Posto de abastecimento", "#416e60"),
            ("Supermercado", "#b17e00"),
            ("→  Caminho da solução", CORES["solucao"]),
        ):
            ttk.Label(legenda, text=texto, foreground=cor).pack(anchor="w", pady=2)
        pisos = ttk.LabelFrame(
            parent, text="Estado do piso e velocidade média", padding=10, style="Cartao.TLabelframe"
        )
        pisos.pack(fill="x", pady=(0, 8))
        for piso, (cor, nome, velocidade) in PISOS.items():
            linha = ttk.Frame(pisos)
            linha.pack(fill="x", pady=3)
            ttk.Label(
                linha, text="━━", foreground=cor, font=("Segoe UI", 12, "bold")
            ).pack(side="left")
            ttk.Label(linha, text=f" {piso} · {nome} · {velocidade} km/h").pack(
                side="left"
            )
        ligacoes = ttk.LabelFrame(parent, text="Lista de ligações (arestas)", padding=8, style="Cartao.TLabelframe")
        ligacoes.pack(fill="both", expand=True)
        self._tabela = ttk.Treeview(
            ligacoes,
            columns=("origem", "destino", "km", "piso"),
            show="headings",
            height=15,
        )
        for chave, titulo, largura in (
            ("origem", "Origem", 86),
            ("destino", "Destino", 86),
            ("km", "km", 42),
            ("piso", "Piso", 44),
        ):
            self._tabela.heading(chave, text=titulo)
            self._tabela.column(chave, width=largura, minwidth=35, anchor="center")
        scroll = ttk.Scrollbar(ligacoes, orient="vertical", command=self._tabela.yview)
        self._tabela.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self._tabela.pack(fill="both", expand=True)
        self._tabela.bind("<<TreeviewSelect>>", self._seleccionar_aresta)
        # Informação metodológica preservada em tooltip ou documentação futura.

    def mostrar_rede(self, rede):
        nomes = [localidade["nome"] for localidade in rede["localidades"]]
        if len(set(nomes)) != len(nomes):
            raise ValueError("A rede contém localidades repetidas.")
        for estrada in rede["estradas"]:
            if estrada["origem"] not in nomes or estrada["destino"] not in nomes:
                raise ValueError("Uma estrada refere uma localidade desconhecida.")
        self._rede = rede
        self._posicoes = preparar_posicoes(rede["localidades"])
        self._segmentos = []
        self._aresta_seleccionada = None
        self._ultima_explorada = None
        self._supermercados = {}
        self._tabela.delete(*self._tabela.get_children())
        for estrada in rede["estradas"]:
            self._tabela.insert(
                "",
                "end",
                values=(
                    estrada["origem"],
                    estrada["destino"],
                    estrada["distanciaKm"],
                    estrada["piso"],
                ),
            )
        self._desenhar()

    def mostrar_instancia(self, instancia):
        self._supermercados = supermercados_da_instancia(instancia)
        self._origem = instancia.get("origem") or instancia.get(
            "estadoInicial", {}
        ).get("localidade", "Beira")
        self.limpar_percurso()

    def destacar_percurso(self, estados, accoes):
        estados = list(estados)
        segmentos = segmentos_percurso(estados, accoes)
        ligacoes = {
            frozenset((e["origem"], e["destino"])) for e in self._rede["estradas"]
        }
        if any(obter_localidade(e) not in self._posicoes for e in estados):
            raise ValueError("O percurso contém uma localidade desconhecida.")
        if any(frozenset(segmento) not in ligacoes for segmento in segmentos):
            raise ValueError("O percurso contém uma ligação inexistente.")
        self._segmentos = segmentos
        self._desenhar()

    def limpar_percurso(self):
        self._segmentos = []
        self._detalhes.configure(text="Seleccione uma localidade para ver os detalhes.")
        self._desenhar()

    def _desenhar(self):
        eixo = self._eixo
        eixo.clear()
        eixo.set_axis_off()
        eixo.set_facecolor("#173c37")
        # Fundo cartográfico desenhado localmente, sem imagem com estradas duplicadas.
        if self._posicoes == preparar_posicoes(self._rede["localidades"]) and all(
            "x" not in l and l["nome"] in POSICOES for l in self._rede["localidades"]
        ):
            eixo.add_patch(
                Polygon(
                    [
                        (0, 0),
                        (64, 0),
                        (73, 10),
                        (84, 17),
                        (90, 25),
                        (85, 33),
                        (90, 43),
                        (100, 53),
                        (110, 58),
                        (110, 95),
                        (0, 95),
                    ],
                    facecolor="#344b35",
                    zorder=0,
                )
            )
            eixo.add_patch(
                Polygon(
                    [
                        (64, 0),
                        (73, 10),
                        (84, 17),
                        (90, 25),
                        (85, 33),
                        (90, 43),
                        (100, 53),
                        (110, 58),
                        (110, 0),
                    ],
                    facecolor="#123d55",
                    edgecolor="#709887",
                    lw=1,
                    zorder=0,
                )
            )
            eixo.text(
                88,
                5,
                "Oceano Índico",
                color="#b7d7df",
                fontsize=10,
                style="italic",
                ha="center",
            )
            for x, y, nome in (
                (12, 24, "MANICA"),
                (65, 18, "SOFALA"),
                (56, 88, "TETE"),
                (91, 85, "ZAMBÉZIA"),
            ):
                eixo.text(
                    x, y, nome, color="#c1c9b5", fontsize=10, alpha=0.6, ha="center"
                )
            eixo.text(103, 91, "N", color="white", ha="center")
            eixo.annotate(
                "",
                xy=(103, 89),
                xytext=(103, 81),
                ha="center",
                color="white",
                arrowprops={"arrowstyle": "->", "color": "white"},
            )
        for estrada in self._rede["estradas"]:
            a, b = (self._posicoes[estrada[chave]] for chave in ("origem", "destino"))
            eixo.plot(
                [a[0], b[0]],
                [a[1], b[1]],
                color=PISOS.get(estrada["piso"], (CORES["estrada"],))[0],
                lw=2.2,
                zorder=1,
            )
            eixo.text(
                (a[0] + b[0]) / 2,
                (a[1] + b[1]) / 2,
                f"{estrada['distanciaKm']} | {estrada['piso']}",
                fontsize=7,
                ha="center",
                zorder=2,
                color="#17251f",
                bbox={
                    "facecolor": "#f4f4ed",
                    "edgecolor": "none",
                    "boxstyle": "round,pad=.18",
                    "alpha": 0.95,
                },
            )
        if self._aresta_seleccionada is not None:
            origem, destino = self._aresta_seleccionada
            if origem in self._posicoes and destino in self._posicoes:
                a, b = self._posicoes[origem], self._posicoes[destino]
                eixo.plot([a[0], b[0]], [a[1], b[1]],
                          color="#FFFFFF", lw=7, alpha=0.9, zorder=2)
                eixo.plot([a[0], b[0]], [a[1], b[1]],
                          color="#086B47", lw=4, zorder=2.1)
        for numero, (origem, destino) in enumerate(self._segmentos, 1):
            a, b = self._posicoes[origem], self._posicoes[destino]
            # Contorno branco: percurso distinguível mesmo sobre estradas verdes.
            eixo.plot([a[0], b[0]], [a[1], b[1]], color="#FFFFFF",
                      lw=8, alpha=0.90, zorder=4.5, solid_capstyle="round")
            eixo.annotate(
                "", xy=b, xytext=a,
                arrowprops={"arrowstyle": "-|>", "color": "#008C48",
                            "lw": 4.5, "mutation_scale": 14},
                zorder=5,
            )
            eixo.text(
                a[0] * 0.65 + b[0] * 0.35,
                a[1] * 0.65 + b[1] * 0.35,
                str(numero),
                bbox={"facecolor": "#FFFFFF", "alpha": 0.90, "edgecolor": "none",
                      "boxstyle": "round,pad=.2"},
                fontsize=9,
                fontweight="bold",
                color="#004D30",
            )
        if self._ultima_explorada in self._posicoes:
            x, y = self._posicoes[self._ultima_explorada]
            eixo.scatter(x, y, s=780, facecolors="none", edgecolors="#FFFFFF",
                         linewidths=3.5, zorder=5)
            eixo.scatter(x, y, s=580, facecolors="none", edgecolors="#FFCA56",
                         linewidths=3, zorder=5.1)
        for nome, (x, y) in self._posicoes.items():
            tipo = (
                "origem"
                if nome == self._origem
                else ("supermercado" if nome in self._supermercados else "localidade")
            )
            localidade = next(l for l in self._rede["localidades"] if l["nome"] == nome)
            artista = eixo.scatter(
                x,
                y,
                s=160,
                c="#ffcb45" if tipo == "localidade" else CORES[tipo],
                edgecolors="#fff5c6",
                marker="s" if localidade.get("abastecimento") else "o",
                picker=6,
                zorder=3,
            )
            artista.set_gid(nome)
            eixo.annotate(
                nome,
                (x, y),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                zorder=4,
                bbox={
                    "facecolor": "#f4f4ed",
                    "edgecolor": "#b5bdb0",
                    "boxstyle": "round,pad=.3",
                },
            )
        if not self._posicoes:
            eixo.text(
                0.5,
                0.5,
                "Sem rede para mostrar.",
                ha="center",
                transform=eixo.transAxes,
            )
        xs = [p[0] for p in self._posicoes.values()] or [-1, 1]
        ys = [p[1] for p in self._posicoes.values()] or [-1, 1]
        margem = max(max(xs) - min(xs), max(ys) - min(ys), 1) * 0.12
        eixo.set_xlim(min(xs) - margem, max(xs) + margem)
        eixo.set_ylim(min(ys) - margem, max(ys) + margem)
        eixo.set_aspect("equal")
        eixo.legend(
            handles=[
                Line2D([], [], marker="o", linestyle="", color=CORES[t], label=n)
                for t, n in (
                    ("localidade", "Localidade"),
                    ("supermercado", "Supermercado"),
                    ("origem", "Origem / regresso"),
                    ("solucao", "Caminho da solução"),
                )
            ]
            + [
                Line2D(
                    [],
                    [],
                    marker="s",
                    linestyle="",
                    color="#555555",
                    label="Posto de abastecimento",
                )
            ],
            loc="lower center",
            fontsize=7,
            ncol=3,
        )
        self._canvas.draw_idle()

    def _seleccionar_aresta(self, _evento=None):
        seleccionados = self._tabela.selection()
        if not seleccionados:
            return
        valores = self._tabela.item(seleccionados[0], "values")
        if len(valores) < 2:
            return
        self._aresta_seleccionada = (valores[0], valores[1])
        self._detalhes.configure(text=f"Ligação seleccionada: {valores[0]} → {valores[1]}")
        self._desenhar()

    def _seleccionar(self, evento):
        nome = evento.artist.get_gid()
        if nome not in self._posicoes:
            return
        localidade = next(l for l in self._rede["localidades"] if l["nome"] == nome)
        texto = f"{nome} · Abastecimento: {'Sim' if localidade.get('abastecimento') else 'Não'}"
        supermercado = self._supermercados.get(nome)
        if supermercado:
            nome_supermercado = supermercado.get(
                "nome",
                f"Supermercado em {nome}",
            )
            texto += (
                f" · {nome_supermercado}: "
                f"{supermercado['abertura']}–{supermercado['fecho']}"
            )
        self._detalhes.configure(text=texto)
