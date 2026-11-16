"""Janela principal da aplicação do Corredor da Beira."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from src.gerador import carregar_rede
from src.interface.arvore_busca import ArvoreBusca
from src.interface.mapa_rodoviario import MapaRodoviario
from src.interface.painel_comparacao import PainelComparacao
from src.interface.painel_configuracao import PainelConfiguracao
from src.interface.painel_resultados import PainelResultados
from src.servicos.executar_busca import executar_busca


class JanelaPrincipal(tk.Tk):
    """Coordena os painéis; os algoritmos permanecem nos serviços."""

    def __init__(self):
        super().__init__()
        self.title("Cadeia de Frio no Corredor da Beira")
        self.geometry("1450x900")
        self.minsize(1100, 700)
        self._fila = queue.Queue()
        self._resultados = []
        self._em_execucao = False
        self._criar_estilo()
        self._criar_menu()
        self._criar_conteudo()
        self._mapa.mostrar_rede(carregar_rede())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _criar_estilo(self):
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 15, "bold"))
        estilo.configure("Executar.TButton", font=("Segoe UI", 10, "bold"))

    def _criar_menu(self):
        menu = tk.Menu(self)
        ficheiro = tk.Menu(menu, tearoff=False)
        ficheiro.add_command(label="Sair", command=self.destroy)
        ajuda = tk.Menu(menu, tearoff=False)
        ajuda.add_command(
            label="Sobre",
            command=lambda: messagebox.showinfo(
                "Sobre",
                "Inteligência Artificial I - Grupo 01\n"
                "Cadeia de frio no Corredor da Beira",
                parent=self,
            ),
        )
        menu.add_cascade(label="Ficheiro", menu=ficheiro)
        menu.add_cascade(label="Ajuda", menu=ajuda)
        self.configure(menu=menu)

    def _criar_conteudo(self):
        cabecalho = ttk.Frame(self, padding=(12, 8))
        cabecalho.pack(fill="x")
        ttk.Label(
            cabecalho,
            text="Cadeia de Frio no Corredor da Beira",
            style="Titulo.TLabel",
        ).pack(side="left")
        self._estado = tk.StringVar(value="Seleccione uma instância para começar.")
        ttk.Label(cabecalho, textvariable=self._estado).pack(side="right")

        corpo = ttk.Panedwindow(self, orient="horizontal")
        corpo.pack(fill="both", expand=True)
        lateral = ttk.Frame(corpo, padding=8, width=310)
        principal = ttk.Frame(corpo)
        corpo.add(lateral, weight=1)
        corpo.add(principal, weight=5)

        self._configuracao = PainelConfiguracao(
            lateral, ao_alterar_instancia=self._ao_carregar_instancia
        )
        self._configuracao.pack(fill="x")
        self._botao_executar = ttk.Button(
            lateral,
            text="Executar busca",
            style="Executar.TButton",
            command=self._iniciar_busca,
        )
        self._botao_executar.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Button(
            lateral, text="Limpar resultados", command=self._limpar_resultados
        ).pack(fill="x", padx=8, pady=4)
        self._progresso = ttk.Progressbar(lateral, mode="indeterminate")
        self._progresso.pack(fill="x", padx=8, pady=8)

        self._separadores = ttk.Notebook(principal)
        self._separadores.pack(fill="both", expand=True)
        self._mapa = MapaRodoviario(self._separadores)
        self._painel_resultados = PainelResultados(self._separadores)
        self._arvore = ArvoreBusca(self._separadores)
        self._comparacao = PainelComparacao(self._separadores)
        self._separadores.add(self._mapa, text="Mapa")
        self._separadores.add(self._painel_resultados, text="Resultados")
        self._separadores.add(self._arvore, text="Árvore de busca")
        self._separadores.add(self._comparacao, text="Comparação")

    
    def _ao_carregar_instancia(self, instancia):
        self._mapa.mostrar_instancia(instancia)
        self._estado.set(
            f"Instância carregada: {instancia.get('nome', 'sem nome')}"
        )

    def obter_configuracao(self):
        """Obtém a configuração seleccionada no painel."""
        return self._configuracao.obter_configuracao()

    def iniciar_busca(self):
        """Inicia a busca usando o fluxo existente."""
        return self._iniciar_busca()

    def _actualizar_arvore(self, eventos):
        """Actualiza a visualização da árvore de busca."""
        self._arvore.carregar_eventos(eventos)

    def _iniciar_busca(self):
        if self._em_execucao:
            return
        try:
            configuracao = self._configuracao.obter_configuracao()
        except (ValueError, KeyError) as erro:
            messagebox.showerror("Configuração inválida", str(erro), parent=self)
            return
        self._em_execucao = True
        self._botao_executar.state(["disabled"])
        self._progresso.start(12)
        self._estado.set("Busca em execução...")
        threading.Thread(
            target=self._executar_em_fundo,
            args=(configuracao,),
            daemon=True,
        ).start()
        self.after(80, self._consultar_fila)

    def _executar_em_fundo(self, configuracao):
        resultado = executar_busca(configuracao)
        self._fila.put((configuracao, resultado))

    def _consultar_fila(self):
        try:
            configuracao, resultado = self._fila.get_nowait()
        except queue.Empty:
            if self._em_execucao:
                self.after(80, self._consultar_fila)
            return
        self._em_execucao = False
        self._progresso.stop()
        self._botao_executar.state(["!disabled"])
        self._apresentar_resultado(configuracao, resultado)

    def _apresentar_resultado(self, configuracao, resultado):
        solucao = resultado["solucao"]
        estatisticas = resultado["estatisticas"]
        self._painel_resultados.mostrar_resultados(solucao, estatisticas)
        self._arvore.carregar_eventos(resultado["eventos"])
        self._mapa.limpar_percurso()
        if solucao is not None:
            self._mapa.destacar_percurso(
                solucao.get_estados(), solucao.get_accoes()
            )

        registo = {
            **configuracao,
            **estatisticas,
            "estado_execucao": resultado["estado_execucao"],
            "mensagem": resultado["mensagem"],
            "custo_total": (
                None if solucao is None else solucao.get_custo_total()
            ),
            "solucao": solucao,
        }
        self._resultados.append(registo)
        self._comparacao.mostrar_comparacao(self._resultados)
        self._estado.set(resultado["mensagem"])
        self._separadores.select(self._painel_resultados)
        if resultado["estado_execucao"] == "erro":
            messagebox.showerror("Erro na busca", resultado["mensagem"], parent=self)

    def _limpar_resultados(self):
        if self._em_execucao:
            return
        self._resultados.clear()
        self._painel_resultados.limpar()
        self._arvore.carregar_eventos([])
        self._comparacao.limpar()
        self._mapa.limpar_percurso()
        self._estado.set("Resultados limpos.")
