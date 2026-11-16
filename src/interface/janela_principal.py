import tkinter as tk
from tkinter import ttk, messagebox
from concurrent.futures import ThreadPoolExecutor
from src.servicos.executar_busca import executar_busca
from src.servicos.carregar_instancia import INSTANCIA_PADRAO
from src.interface.tema import AZUL_ESCURO, FUNDO, configurar_estilos

class JanelaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cadeia de Frio | Corredor da Beira")
        self.geometry("1100x720")
        self.minsize(850, 560)
        self.configure(background=FUNDO)
        configurar_estilos(self)
        self._executor = ThreadPoolExecutor(max_workers=1)
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
        self.configuracao = ttk.LabelFrame(self.aba_operacao, text="Parametros da procura", padding=12)
        self.configuracao.pack(side="left", fill="y", padx=(0, 12))
        self.instancia_var = tk.StringVar(value=str(INSTANCIA_PADRAO))
        self.algoritmo_var = tk.StringVar(value="a_star")
        self.heuristica_var = tk.StringVar(value="h1")
        self.peso_var = tk.StringVar(value="1.5")
        self.limite_var = tk.StringVar(value="15")
        for titulo, variavel in (("Instancia", self.instancia_var), ("Peso", self.peso_var),
                                 ("Limite maximo", self.limite_var)):
            ttk.Label(self.configuracao, text=titulo).pack(anchor="w", pady=(8, 2))
            ttk.Entry(self.configuracao, textvariable=variavel, width=38).pack(fill="x")
        ttk.Label(self.configuracao, text="Algoritmo").pack(anchor="w", pady=(8, 2))
        ttk.Combobox(self.configuracao, textvariable=self.algoritmo_var,
                     values=("a_star", "gulosa", "a_star_ponderada", "bfs", "dfs", "ucs", "ids"),
                     state="readonly", width=35).pack(fill="x")
        ttk.Label(self.configuracao, text="Heuristica").pack(anchor="w", pady=(8, 2))
        ttk.Combobox(self.configuracao, textvariable=self.heuristica_var,
                     values=("h0", "h1", "h2"), state="readonly", width=35).pack(fill="x")
        self.botao_executar = ttk.Button(self.configuracao, text="Executar procura", command=self.iniciar_busca)
        self.botao_executar.pack(fill="x", pady=16)
        self.area_resultados = ttk.LabelFrame(self.aba_operacao, text="Resultados", padding=12)
        self.area_resultados.pack(side="left", fill="both", expand=True)
        ttk.Label(self.area_resultados, text="Aguardando execucao...").pack(anchor="w")
        self._criar_aba_arvore()
        ttk.Label(self.aba_comparacao, text="Painel de comparacao: Naeem").pack(anchor="w")

    def obter_configuracao(self):
        return {"instancia": self.instancia_var.get(),
                "algoritmo": self.algoritmo_var.get(),
                "heuristica": self.heuristica_var.get(),
                "peso": float(self.peso_var.get()),
                "limite": int(self.limite_var.get()),
                "limite_maximo": int(self.limite_var.get())}

    def iniciar_busca(self):
        try:
            configuracao = self.obter_configuracao()
        except ValueError as erro:
            messagebox.showerror("Parametros invalidos", str(erro))
            return
        self.botao_executar.state(["disabled"])
        self._mostrar_estado("Procura em execucao...")
        futuro = self._executor.submit(executar_busca, configuracao)
        self._verificar_execucao(futuro)

    def _verificar_execucao(self, futuro):
        if not futuro.done():
            self.after(150, self._verificar_execucao, futuro)
            return
        self.botao_executar.state(["!disabled"])
        try:
            self.ultimo_resultado = futuro.result()
        except Exception as erro:
            self._mostrar_estado(f"Erro na procura: {erro}")
            return
        self._mostrar_resultado(self.ultimo_resultado)
        self._actualizar_arvore(self.ultimo_resultado.get("eventos", []))

    def _mostrar_estado(self, texto):
        for filho in self.area_resultados.winfo_children():
            filho.destroy()
        ttk.Label(self.area_resultados, text=texto, wraplength=500).pack(anchor="w")

    def _mostrar_resultado(self, resultado):
        solucao = resultado["solucao"]
        if solucao is None:
            self._mostrar_estado("Nao foi encontrada uma solucao.")
            return
        self._mostrar_estado(f"Estado: {resultado['estado_execucao']} | Custo: {solucao.custo_total} min")
        texto = tk.Text(self.area_resultados, wrap="word", height=18)
        texto.pack(fill="both", expand=True, pady=8)
        for numero, accao in enumerate(solucao.get_accoes(), 1):
            texto.insert("end", f"{numero}. {accao}\n")
        texto.configure(state="disabled")

    def destroy(self):
        self._executor.shutdown(wait=False, cancel_futures=True)
        super().destroy()

    def _criar_aba_arvore(self):
        try:
            from src.interface.arvore_busca import ArvoreBusca
        except ImportError:
            ttk.Label(self.aba_arvore, text="Aguardando integracao do modulo do Elias").pack(anchor="w")
            self.visualizador_arvore = None
            return
        self.visualizador_arvore = ArvoreBusca(self.aba_arvore)
        self.visualizador_arvore.pack(fill="both", expand=True)

    def _actualizar_arvore(self, eventos):
        if self.visualizador_arvore is not None:
            self.visualizador_arvore.carregar_eventos(eventos)
