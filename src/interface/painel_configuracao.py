"""Controlos de configuração independentes da janela principal."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.gerador import carregar_json

ALGORITMOS = {
    "BFS": "bfs",
    "DFS": "dfs",
    "LDS": "lds",
    "IDS": "ids",
    "UCS": "ucs",
    "Gulosa": "busca_gulosa",
    "A*": "a_star",
    "A* ponderada": "a_star_ponderada",
}
HEURISTICAS = ("h0", "h1", "h2")


def validar_configuracao(caminho_instancia, algoritmo, heuristica, peso, limite):
    """Valida e normaliza apenas os parâmetros aplicáveis ao algoritmo."""
    if not caminho_instancia or not Path(caminho_instancia).is_file():
        raise ValueError("Seleccione um ficheiro de instância existente.")
    if algoritmo not in ALGORITMOS.values():
        raise ValueError("Seleccione um algoritmo válido.")
    informada = algoritmo in ("busca_gulosa", "a_star", "a_star_ponderada")
    if informada and heuristica not in HEURISTICAS:
        raise ValueError("Seleccione uma heurística válida.")
    try:
        peso = (
            float(str(peso).replace(",", "."))
            if algoritmo == "a_star_ponderada"
            else None
        )
        limite = int(str(limite)) if algoritmo in ("lds", "ids") else None
    except (TypeError, ValueError):
        raise ValueError("Verifique o peso e os limites de profundidade.") from None
    if peso is not None and not 0 < peso < float("inf"):
        raise ValueError("O peso deve ser um número finito positivo.")
    if limite is not None and limite < 0:
        raise ValueError("Os limites de profundidade não podem ser negativos.")
    return {
        "caminho_instancia": str(caminho_instancia),
        "algoritmo": algoritmo,
        "heuristica": heuristica if informada else None,
        "peso": peso,
        "limite": limite,
    }


class PainelConfiguracao(ttk.Frame):
    """Emite a instância seleccionada através de um callback opcional."""

    def __init__(self, parent, ao_alterar_instancia=None):
        super().__init__(parent, padding=8)
        self._caminho_instancia = ""
        self._ao_alterar_instancia = ao_alterar_instancia
        self._nome = tk.StringVar(value="Sem instância seleccionada.")
        self._algoritmo = tk.StringVar(value="A*")
        self._heuristica = tk.StringVar(value="h1")
        self._peso = tk.StringVar(value="1,5")
        self._limite = tk.StringVar(value="30")
        ttk.Label(self, text="Configuração").grid(row=0, column=0, sticky="w")
        ttk.Label(self, textvariable=self._nome, wraplength=260).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=8
        )
        ttk.Button(self, text="Carregar instância", command=self._carregar).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=3
        )
        self._campos = {}
        for linha, (rotulo, variavel, opcoes) in enumerate(
            (
                ("Algoritmo", self._algoritmo, tuple(ALGORITMOS)),
                ("Heurística", self._heuristica, HEURISTICAS),
                ("Peso", self._peso, None),
                ("Limite (LDS / IDS)", self._limite, None),
            ),
            3,
        ):
            ttk.Label(self, text=rotulo).grid(row=linha, column=0, sticky="w", pady=5)
            campo = (
                ttk.Combobox(
                    self,
                    textvariable=variavel,
                    values=opcoes,
                    state="readonly",
                    width=17,
                )
                if opcoes
                else ttk.Entry(self, textvariable=variavel, width=19)
            )
            campo.grid(row=linha, column=1, sticky="ew", padx=(8, 0))
            self._campos[rotulo] = campo
        self.columnconfigure(1, weight=1)
        self._algoritmo.trace_add("write", self._actualizar_campos)
        self._actualizar_campos()

    def obter_configuracao(self):
        return validar_configuracao(
            self._caminho_instancia,
            ALGORITMOS[self._algoritmo.get()],
            self._heuristica.get(),
            self._peso.get(),
            self._limite.get(),
        )

    def carregar_instancia(self, caminho):
        instancia = carregar_json(caminho)
        if not isinstance(instancia, dict) or not instancia.get("supermercados"):
            raise ValueError("A instância deve conter supermercados.")
        if self._ao_alterar_instancia:
            self._ao_alterar_instancia(instancia)
        self._caminho_instancia = str(Path(caminho).resolve())
        self._nome.set(
            f"{instancia.get('nome', 'Instância')} · "
            f"{len(instancia['supermercados'])} supermercados"
        )

    def _actualizar_campos(self, *_):
        algoritmo = self._algoritmo.get()
        for nome, activo in {
            "Heurística": algoritmo in ("Gulosa", "A*", "A* ponderada"),
            "Peso": algoritmo == "A* ponderada",
            "Limite (LDS / IDS)": algoritmo in ("LDS", "IDS"),
        }.items():
            self._campos[nome].configure(
                state=("readonly" if nome == "Heurística" else "normal")
                if activo
                else "disabled"
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
