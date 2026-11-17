"""Controlos de configuracao independentes da janela principal."""

import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.gerador import carregar_json, gerar_problema
from src.interface.icones import carregar_icone

ALGORITMOS = {
    "BFS": "bfs",
    "DFS": "dfs",
    "IDS": "ids",
    "LDS": "lds",
    "UCS": "ucs",
    "Gulosa": "busca_gulosa",
    "A*": "a_star",
    "A* ponderada": "a_star_ponderada",
}
HEURISTICAS = ("h0", "h1", "h2")


def validar_configuracao(caminho_instancia, algoritmo, heuristica, peso, limite):
    """Valida os parametros e devolve o contrato do servico de execucao."""
    if not caminho_instancia or not Path(caminho_instancia).is_file():
        raise ValueError("Seleccione um ficheiro de instancia existente.")

    if algoritmo not in ALGORITMOS.values():
        raise ValueError("Seleccione um algoritmo valido.")

    informada = algoritmo in (
        "busca_gulosa",
        "a_star",
        "a_star_ponderada",
    )

    if informada and heuristica not in HEURISTICAS:
        raise ValueError("Seleccione uma heuristica valida.")

    try:
        peso_normalizado = (
            float(str(peso).replace(",", "."))
            if algoritmo == "a_star_ponderada"
            else None
        )

        limite_normalizado = (
            int(str(limite))
            if algoritmo in ("ids", "lds")
            else None
        )
    except (TypeError, ValueError):
        raise ValueError(
            "Verifique o peso e o limite de profundidade."
        ) from None

    if peso_normalizado is not None and not (0 < peso_normalizado < float("inf")):
        raise ValueError("O peso deve ser finito e positivo.")

    if limite_normalizado is not None and limite_normalizado < 0:
        raise ValueError("O limite nao pode ser negativo.")

    return {
        "caminho_instancia": str(Path(caminho_instancia).resolve()),
        "algoritmo": algoritmo,
        "heuristica": heuristica if informada else "h0",
        "peso": peso_normalizado,
        "limite": limite_normalizado,
        "limite_maximo": limite_normalizado,
    }

class PainelConfiguracao(ttk.Frame):
    """Selecção de instâncias e parâmetros, sem modificar o serviço."""

    def __init__(self, parent, ao_alterar_instancia=None):
        super().__init__(parent, padding=8, style="Cartao.TFrame")
        self._caminho_instancia = ""
        self._ao_alterar_instancia = ao_alterar_instancia
        self._nome = tk.StringVar(value="Nenhuma instância seleccionada")
        self._detalhes_instancia = tk.StringVar(value="Gera ou carrega uma instância para começar.")
        self._algoritmo = tk.StringVar(value="A*")
        self._heuristica = tk.StringVar(value="h1")
        self._peso = tk.StringVar(value="1,5")
        self._limite = tk.StringVar(value="30")
        self._limite_tempo = tk.StringVar(value="40")
        self._sem_limite = tk.BooleanVar(value=False)
        self._imagens = []
        self._bloqueado = False
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)

        self._titulo = ttk.Label(self, text="Configuração", style="Secao.TLabel")
        self._titulo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        icone_carregar = carregar_icone(self, "carregar")
        icone_gerar = carregar_icone(self, "gerar")
        self._imagens.extend((icone_carregar, icone_gerar))
        self._botao_carregar = ttk.Button(
            self, text="Carregar instância", image=icone_carregar, compound="left",
            style="Secundario.TButton", command=self._carregar
        )
        self._botao_carregar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=3)
        self._botao_gerar = ttk.Button(
            self, text="Gerar nova instância", image=icone_gerar, compound="left",
            style="Gerar.TButton", command=self._gerar_instancia
        )
        self._botao_gerar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(3, 9))

        cartao = ttk.Frame(self, style="Instancia.TFrame", padding=10)
        cartao.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        ttk.Label(cartao, text="INSTÂNCIA SELECCIONADA", style="InstanciaTitulo.TLabel").pack(anchor="w")
        ttk.Label(
            cartao, textvariable=self._nome, style="InstanciaNome.TLabel", wraplength=235
        ).pack(anchor="w", pady=(5, 3))
        ttk.Label(
            cartao, textvariable=self._detalhes_instancia,
            style="InstanciaDetalhe.TLabel", wraplength=235
        ).pack(anchor="w")

        self._campos = {}
        self._rotulos = {}
        for linha, (rotulo, variavel, opcoes) in enumerate(
            (
                ("Algoritmo", self._algoritmo, tuple(ALGORITMOS)),
                ("Heurística", self._heuristica, HEURISTICAS),
                ("Peso", self._peso, None),
                ("Limite (IDS/LDS)", self._limite, None),
            ), 4,
        ):
            etiqueta = ttk.Label(self, text=rotulo, style="Cartao.TLabel")
            etiqueta.grid(row=linha, column=0, sticky="w", pady=7)
            self._rotulos[rotulo] = etiqueta
            campo = (
                ttk.Combobox(self, textvariable=variavel, values=opcoes,
                             state="readonly", style="Moderno.TCombobox", width=14)
                if opcoes else ttk.Entry(self, textvariable=variavel, width=15, style="Moderno.TEntry")
            )
            campo.grid(row=linha, column=1, sticky="ew", padx=(8, 0), pady=3)
            self._campos[rotulo] = campo
        self._ajuda_heuristica = ttk.Label(
            self, text="h0: zero  ·  h1: distância  ·  h2: estimativa MST",
            style="Ajuda.TLabel", wraplength=255, justify="left"
        )
        self._ajuda_heuristica.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(self, text="Tempo máximo (s)", style="Cartao.TLabel").grid(
            row=9, column=0, sticky="w", pady=(9, 3))
        self._campo_tempo = ttk.Entry(
            self, textvariable=self._limite_tempo, style="Moderno.TEntry", width=15
        )
        self._campo_tempo.grid(row=9, column=1, sticky="ew", padx=(8, 0))
        self._checkbox_tempo = ttk.Checkbutton(
            self, text="Sem limite de tempo", variable=self._sem_limite,
            command=self._actualizar_campos
        )
        self._checkbox_tempo.grid(row=10, column=0, columnspan=2, sticky="w", pady=(2, 7))
        self._algoritmo.trace_add("write", self._actualizar_campos)
        self._heuristica.trace_add("write", self._actualizar_campos)
        self._actualizar_campos()

    def definir_bloqueado(self, bloqueado):
        """Protege a instância e as opções enquanto a busca está activa."""
        self._bloqueado = bool(bloqueado)
        for botao in (self._botao_carregar, self._botao_gerar):
            botao.state(["disabled"] if bloqueado else ["!disabled"])
        self._checkbox_tempo.state(["disabled"] if bloqueado else ["!disabled"])
        self._actualizar_campos()

    def obter_configuracao(self):
        configuracao = validar_configuracao(
            self._caminho_instancia,
            ALGORITMOS[self._algoritmo.get()],
            self._heuristica.get(),
            self._peso.get(),
            self._limite.get(),
        )
        if self._sem_limite.get():
            configuracao["limite_segundos"] = None
        else:
            try:
                segundos = float(self._limite_tempo.get().replace(",", "."))
            except ValueError:
                raise ValueError("Introduza um tempo máximo válido em segundos.") from None
            if not 0 < segundos <= 86400:
                raise ValueError("O tempo máximo deve estar entre 0 e 86400 segundos.")
            configuracao["limite_segundos"] = segundos
        return configuracao

    def carregar_instancia(self, caminho):
        instancia = carregar_json(caminho)
        if not isinstance(instancia, dict) or not instancia.get("supermercados"):
            raise ValueError("A instância deve conter supermercados.")
        if self._ao_alterar_instancia:
            self._ao_alterar_instancia(instancia)
        self._caminho_instancia = str(Path(caminho).resolve())
        self._nome.set(str(instancia.get("nome", "Instância")))
        self._detalhes_instancia.set(
            f"{len(instancia['supermercados'])} supermercados  ·  "
            f"Semente: {instancia.get('semente', 'não indicada')}\n"
            f"Ficheiro: {Path(caminho).name}\n"
            "Viabilidade: ainda não verificada"
        )

    def _actualizar_campos(self, *_):
        algoritmo = self._algoritmo.get()
        activos = {
            "Algoritmo": True,
            "Heurística": algoritmo in ("Gulosa", "A*", "A* ponderada"),
            "Peso": algoritmo == "A* ponderada",
            "Limite (IDS/LDS)": algoritmo in ("IDS", "LDS"),
        }
        for nome, campo in self._campos.items():
            activo = activos[nome] and not self._bloqueado
            campo.configure(state=("readonly" if isinstance(campo, ttk.Combobox)
                                   else "normal") if activo else "disabled")
        # Heurística não é sequer apresentada às buscas não informadas.
        if algoritmo in ("Gulosa", "A*", "A* ponderada"):
            self._rotulos["Heurística"].grid()
            self._campos["Heurística"].grid()
        else:
            self._rotulos["Heurística"].grid_remove()
            self._campos["Heurística"].grid_remove()
        descricoes = {
            "h0": "h0 — heurística nula: não estima o custo restante.",
            "h1": "h1 — distância: aproximação ao destino por distâncias.",
            "h2": "h2 — MST: estimativa baseada em árvore geradora mínima.",
        }
        informada = algoritmo in ("Gulosa", "A*", "A* ponderada")
        if informada:
            self._ajuda_heuristica.configure(
                text=descricoes.get(self._heuristica.get(), "Seleccione uma heurística.")
            )
            self._ajuda_heuristica.grid()
        else:
            self._ajuda_heuristica.grid_remove()
        self._campo_tempo.configure(
            state="disabled" if self._bloqueado or self._sem_limite.get()
            else "normal"
        )

    def _gerar_instancia(self):
        """Gera e carrega automaticamente uma nova instância."""
        try:
            semente = time.time_ns() // 1000000
            nome = f"instancia_{semente}.json"

            _, caminho = gerar_problema(
                semente=semente,
                nome_ficheiro=nome,
            )

            self.carregar_instancia(caminho)


        except (OSError, ValueError, KeyError, TypeError) as erro:
            messagebox.showerror(
                "Erro ao gerar instância",
                str(erro),
                parent=self,
            )

    def _carregar(self):
        caminho = filedialog.askopenfilename(
            parent=self,
            title="Carregar instância",
            filetypes=[("Instâncias JSON", "*.json")],
        )
        if caminho:
            try:
                self.carregar_instancia(caminho)
            except (OSError, ValueError, KeyError, TypeError) as erro:
                messagebox.showerror("Instância inválida", str(erro), parent=self)
