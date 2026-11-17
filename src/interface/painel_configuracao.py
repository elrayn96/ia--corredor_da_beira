"""Controlos de configuracao independentes da janela principal."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.gerador import carregar_json, gerar_problema

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
        ttk.Button(self, text="Carregar instância", style="Secundario.TButton", command=self._carregar).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=3
        )
        ttk.Button(
            self,
            text="Gerar nova instância",
            style="Gerar.TButton",
            command=self._gerar_instancia,
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=3)
        self._campos = {}
        for linha, (rotulo, variavel, opcoes) in enumerate(
            (
                ("Algoritmo", self._algoritmo, tuple(ALGORITMOS)),
                ("Heurística", self._heuristica, HEURISTICAS),
                ("Peso", self._peso, None),
                ("Limite (IDS)", self._limite, None),
            ),
            4,
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
            "Limite (IDS)": algoritmo in ("IDS", "LDS"),
        }.items():
            self._campos[nome].configure(
                state=("readonly" if nome == "Heurística" else "normal")
                if activo
                else "disabled"
            )

    def _gerar_instancia(self):
        """Gera e carrega automaticamente uma nova instância."""
        try:
            from datetime import datetime

            semente = int(datetime.now().timestamp() * 1000)
            nome = f"instancia_{semente}.json"

            _, caminho = gerar_problema(
                semente=semente,
                nome_ficheiro=nome,
            )

            self.carregar_instancia(caminho)

            messagebox.showinfo(
                "Instância gerada",
                f"Instância criada com sucesso:\n{caminho}",
                parent=self,
            )

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
