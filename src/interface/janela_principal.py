import tkinter as tk
from tkinter import ttk
from src.interface.tema import AZUL_ESCURO, FUNDO, configurar_estilos

class JanelaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cadeia de Frio | Corredor da Beira")
        self.geometry("1100x720")
        self.minsize(850, 560)
        self.configure(background=FUNDO)
        configurar_estilos(self)
        self._construir()

    def _construir(self):
        cabecalho = tk.Frame(self, bg=AZUL_ESCURO, padx=18, pady=14)
        cabecalho.pack(fill="x")
        ttk.Label(cabecalho, text="Cadeia de Frio — Corredor da Beira",
                  style="Cabecalho.TLabel").pack(anchor="w")
        self.conteudo = ttk.Frame(self, padding=14)
        self.conteudo.pack(fill="both", expand=True)
        self.abas = ttk.Notebook(self.conteudo)
        self.abas.pack(fill="both", expand=True)
        self.aba_operacao = ttk.Frame(self.abas, padding=12)
        self.aba_arvore = ttk.Frame(self.abas, padding=12)
        self.aba_comparacao = ttk.Frame(self.abas, padding=12)
        self.abas.add(self.aba_operacao, text="Operacao e percurso")
        self.abas.add(self.aba_arvore, text="Arvore de procura")
        self.abas.add(self.aba_comparacao, text="Comparacao")
        ttk.Label(self.aba_operacao, text="Area de operacao", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self.aba_arvore, text="Visualizacao disponivel apos integracao do Elias").pack(anchor="w")
        ttk.Label(self.aba_comparacao, text="Painel de comparacao: Naeem").pack(anchor="w")
