"""Janela principal da aplicação do Corredor da Beira."""

from __future__ import annotations

import logging
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
from src.interface.tema import configurar_estilos
from src.servicos.executar_busca import executar_busca

logger = logging.getLogger(__name__)


class JanelaPrincipal(tk.Tk):
    """Coordena os painéis; os algoritmos permanecem nos serviços."""

    def __init__(self):
        super().__init__()
        self.title("Cadeia de Frio no Corredor da Beira")
        self.geometry("1450x900")
        self.configure(bg="#F3F6F8")
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
        configurar_estilos(self)

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
        cabecalho = tk.Frame(
            self,
            bg="#064D38",
            height=66,
        )
        cabecalho.pack(fill="x")
        cabecalho.pack_propagate(False)

        ttk.Label(
            cabecalho,
            text="❄  Cadeia de Frio no Corredor da Beira",
            style="Cabecalho.TLabel",
        ).pack(side="left", padx=12)

        self._estado = tk.StringVar(
            value="Seleccione uma instância para começar."
        )

        ttk.Label(
            cabecalho,
            textvariable=self._estado,
            style="Estado.TLabel",
        ).pack(side="right", padx=18)

        corpo = tk.Frame(self, bg="#F3F6F8")
        corpo.pack(fill="both", expand=True, padx=10, pady=10)
        lateral = ttk.Frame(corpo, padding=12, style="Cartao.TFrame", width=285)
        lateral.pack(side="left", fill="y", padx=(0, 10))
        lateral.pack_propagate(False)
        principal = ttk.Frame(corpo, style="Cartao.TFrame")
        principal.pack(side="left", fill="both", expand=True)

        self._configuracao = PainelConfiguracao(
            lateral, ao_alterar_instancia=self._ao_carregar_instancia
        )
        self._configuracao.pack(fill="x")
        self._botao_executar = ttk.Button(
            lateral,
            text="▶  Executar busca",
            style="Executar.TButton",
            command=self._iniciar_busca,
        )
        self._botao_executar.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Button(
            lateral, text="Limpar resultados", style="Secundario.TButton", command=self._limpar_resultados
        ).pack(fill="x", padx=8, pady=4)
        self._progresso = ttk.Progressbar(lateral, orient="horizontal", mode="indeterminate", style="Horizontal.TProgressbar")
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
        try:
            resultado = executar_busca(configuracao)
            self._fila.put(("resultado", configuracao, resultado))

        except Exception:
            logger.exception(
                "Falha inesperada durante a execução da busca."
            )
            self._fila.put(
                (
                    "falha",
                    configuracao,
                    ("Ocorreu um erro inesperado durante a busca. "
                    "Consulte o terminal para mais detalhes."),
                )
            )

    def _consultar_fila(self):
        try:
            tipo, configuracao, conteudo = self._fila.get_nowait()

        except queue.Empty:
            if self._em_execucao:
                self.after(80, self._consultar_fila)
            return

        self._em_execucao = False
        self._progresso.stop()
        self._botao_executar.state(["!disabled"])

        if tipo == "falha":
            self._estado.set("Erro inesperado na busca.")
            messagebox.showerror(
                "Erro na execução",
                conteudo,
                parent=self,
            )
            return

        try:
            self._apresentar_resultado(configuracao, conteudo)

        except Exception:
            logger.exception(
                "Falha ao apresentar os resultados da busca."
            )
            self._estado.set("Erro ao apresentar os resultados.")
            messagebox.showerror(
                "Erro de apresentação",
                "Não foi possível apresentar os resultados. "
                "Consulte o terminal.",
                parent=self,
            )

    def _apresentar_resultado(self, configuracao, resultado):
        solucao = resultado["solucao"]
        estatisticas = resultado["estatisticas"]
        self._painel_resultados.mostrar_resultados(solucao, estatisticas)
        eventos = resultado.get("eventos") or []
        self._arvore.carregar_eventos(eventos)
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
        if eventos:
            self._separadores.select(self._arvore)
            self._arvore.reiniciar_visualizacao()
        else:
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
