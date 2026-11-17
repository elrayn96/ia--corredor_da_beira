"""Janela principal: execução responsiva, cancelamento e progresso real."""

from __future__ import annotations

import logging
import queue
import threading
import time
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
LIMITE_TEMPO_GUI = 40  # segundos; evita buscas ilimitadas em computadores lentos.


class IndicadorActividade(tk.Canvas):
    """Indicador circular leve, animado apenas durante a busca."""

    def __init__(self, parent, fundo="#FFFFFF"):
        super().__init__(parent, width=25, height=25, bg=fundo,
                         highlightthickness=0, bd=0)
        self._timer = None
        self._angulo = 0

    def iniciar(self):
        if self._timer is None:
            self._animar()

    def parar(self):
        if self._timer is not None:
            self.after_cancel(self._timer)
            self._timer = None
        self.delete("all")

    def _animar(self):
        self.delete("all")
        self.create_arc(3, 3, 22, 22, start=self._angulo, extent=255,
                        style="arc", width=3, outline="#086B47")
        self._angulo = (self._angulo + 26) % 360
        self._timer = self.after(75, self._animar)


class JanelaPrincipal(tk.Tk):
    """Coordena os painéis sem bloquear a thread gráfica."""

    def __init__(self):
        super().__init__()
        self.title("Cadeia de Frio no Corredor da Beira")
        self.geometry("1450x900")
        self.minsize(1100, 700)
        self.configure(bg="#F3F6F8")
        self._fila = queue.Queue(maxsize=48)
        self._resultados = []
        self._em_execucao = False
        self._cancelar = threading.Event()
        self._ultimo_progresso = 0.0
        self._inicio_busca = None
        self._poll_id = None
        self._criar_estilo()
        self._criar_menu()
        self._criar_conteudo()
        self._mapa.mostrar_rede(carregar_rede())
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self.after_idle(self._maximizar)

    def _maximizar(self):
        try:
            self.state("zoomed")  # Windows
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)  # Linux / WM compatível
            except tk.TclError:
                pass

    def _criar_estilo(self):
        configurar_estilos(self)

    def _criar_menu(self):
        """Menu leve com hover/pressed, mantendo Ficheiro e Ajuda."""
        barra = tk.Frame(self, bg="#EDF3F1", height=36)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        ficheiro = tk.Menu(self, tearoff=False, bg="#FFFFFF", fg="#17212B")
        ficheiro.add_command(label="Sair", command=self._fechar)
        ajuda = tk.Menu(self, tearoff=False, bg="#FFFFFF", fg="#17212B")
        ajuda.add_command(
            label="Sobre",
            command=lambda: messagebox.showinfo(
                "Sobre", "Inteligência Artificial I - Grupo 01\n"
                "Cadeia de frio no Corredor da Beira", parent=self,
            ),
        )
        for nome, menu in (("Ficheiro", ficheiro), ("Ajuda", ajuda)):
            botao = tk.Menubutton(
                barra, text=nome, menu=menu, bg="#EDF3F1", fg="#17212B",
                activebackground="#D6EBE1", activeforeground="#064D38",
                relief="flat", bd=0, padx=16, pady=7,
                font=("Segoe UI", 10), cursor="hand2",
            )
            botao.pack(side="left", padx=(4, 0))
            botao.bind("<Enter>", lambda evento: evento.widget.configure(bg="#D6EBE1"))
            botao.bind("<Leave>", lambda evento: evento.widget.configure(bg="#EDF3F1"))
        self._menu_ficheiro = ficheiro
        self._menu_ajuda = ajuda

    def _criar_conteudo(self):
        cabecalho = tk.Frame(self, bg="#064D38", height=66)
        cabecalho.pack(fill="x")
        cabecalho.pack_propagate(False)
        ttk.Label(cabecalho, text="❄  Cadeia de Frio no Corredor da Beira",
                  style="Cabecalho.TLabel").pack(side="left", padx=12)
        self._estado = tk.StringVar(value="Pronto para começar")
        self._status = tk.Label(
            cabecalho, textvariable=self._estado, bg="#106548", fg="white",
            font=("Segoe UI", 10), padx=16, pady=9, relief="flat",
        )
        self._status.pack(side="right", padx=18)

        corpo = tk.Frame(self, bg="#F3F6F8")
        corpo.pack(fill="both", expand=True, padx=10, pady=10)
        lateral = ttk.Frame(corpo, padding=10, style="Cartao.TFrame", width=274)
        lateral.pack(side="left", fill="y", padx=(0, 10))
        lateral.pack_propagate(False)
        principal = ttk.Frame(corpo, style="Cartao.TFrame")
        principal.pack(side="left", fill="both", expand=True)

        self._configuracao = PainelConfiguracao(
            lateral, ao_alterar_instancia=self._ao_carregar_instancia
        )
        self._configuracao.pack(fill="x")
        self._botao_executar = ttk.Button(
            lateral, text="▶  Executar busca", style="Executar.TButton",
            command=self._iniciar_busca,
        )
        self._botao_executar.pack(fill="x", padx=8, pady=(13, 5))
        self._botao_limpar = ttk.Button(
            lateral, text="⌫  Limpar resultados", style="Secundario.TButton",
            command=self._limpar_resultados,
        )
        self._botao_limpar.pack(fill="x", padx=8, pady=(3, 8))
        actividade = ttk.Frame(lateral, style="Cartao.TFrame")
        actividade.pack(fill="x", padx=8, pady=(2, 0))
        self._spinner = IndicadorActividade(actividade)
        self._spinner.pack(side="left", padx=(0, 7))
        self._progresso_texto = tk.StringVar(
            value="Ao executar, verá aqui os passos da busca."
        )
        ttk.Label(
            actividade, textvariable=self._progresso_texto,
            style="Ajuda.TLabel", wraplength=205, justify="left",
        ).pack(side="left", fill="x", expand=True)
        # Mantido para compatibilidade com testes e integrações existentes.
        self._progresso = ttk.Progressbar(
            lateral, orient="horizontal", mode="indeterminate",
            style="Horizontal.TProgressbar",
        )
        # O spinner é o indicador visível, não uma percentagem enganadora.

        self._separadores = ttk.Notebook(principal)
        self._separadores.pack(fill="both", expand=True)
        self._mapa = MapaRodoviario(self._separadores)
        self._painel_resultados = PainelResultados(self._separadores)
        self._arvore = ArvoreBusca(self._separadores)
        self._comparacao = PainelComparacao(self._separadores)
        self._separadores.add(self._mapa, text="◫  Mapa")
        self._separadores.add(self._painel_resultados, text="▥  Resultados")
        self._separadores.add(self._arvore, text="♧  Árvore de busca")
        self._separadores.add(self._comparacao, text="▤  Comparação")

    def _ao_carregar_instancia(self, instancia):
        self._mapa.mostrar_instancia(instancia)
        self._estado.set("✓  Instância seleccionada · pronto para executar")

    def obter_configuracao(self):
        return self._configuracao.obter_configuracao()

    def iniciar_busca(self):
        return self._iniciar_busca()

    def _actualizar_arvore(self, eventos):
        self._arvore.carregar_eventos(eventos)

    def _iniciar_busca(self):
        if self._em_execucao:
            self._cancelar_busca()
            return
        try:
            configuracao = self._configuracao.obter_configuracao()
        except (ValueError, KeyError) as erro:
            messagebox.showerror("Configuração inválida", str(erro), parent=self)
            return
        self._em_execucao = True
        self._cancelar.clear()
        self._inicio_busca = time.perf_counter()
        self._configuracao.definir_bloqueado(True)
        self._botao_limpar.state(["disabled"])
        self._botao_executar.configure(text="■  Cancelar busca", style="Cancelar.TButton")
        self._spinner.iniciar()
        self._estado.set("◌  Busca em execução")
        self._progresso_texto.set("A preparar problema e a iniciar o algoritmo...")
        # Separadores continuam acessíveis para consulta; as configurações ficam bloqueadas.
        threading.Thread(
            target=self._executar_em_fundo, args=(configuracao,), daemon=True
        ).start()
        self._agendar_consulta()

    def _cancelar_busca(self):
        if not self._em_execucao:
            return
        self._cancelar.set()
        self._botao_executar.state(["disabled"])
        self._estado.set("A interromper a busca...")
        self._progresso_texto.set("A aguardar a próxima verificação do algoritmo.")

    def _executar_em_fundo(self, configuracao):
        contadores = {"gerar": 0, "expandir": 0, "descartar": 0}
        ultimo_envio = time.perf_counter()

        def acompanhar(evento):
            nonlocal ultimo_envio
            tipo = evento.get("tipo")
            if tipo in contadores:
                contadores[tipo] += 1
            agora = time.perf_counter()
            if agora - ultimo_envio >= 0.30 or tipo == "objectivo":
                ultimo_envio = agora
                try:
                    self._fila.put_nowait(("progresso", None, (
                        contadores.copy(), tipo, agora - self._inicio_busca
                    )))
                except queue.Full:
                    pass

        try:
            resultado = executar_busca(
                configuracao, observador=acompanhar,
                cancelar=self._cancelar, limite_segundos=LIMITE_TEMPO_GUI,
            )
            self._fila.put(("resultado", configuracao, resultado))
        except Exception:
            logger.exception("Falha inesperada durante a busca")
            self._fila.put(("falha", configuracao,
                            "Erro inesperado. Consulte o terminal."))

    def _agendar_consulta(self):
        if self._poll_id is None:
            self._poll_id = self.after(100, self._consultar_fila)

    def _consultar_fila(self):
        self._poll_id = None
        for _ in range(40):
            try:
                tipo, configuracao, conteudo = self._fila.get_nowait()
            except queue.Empty:
                break
            if tipo == "progresso":
                contadores, evento, decorrido = conteudo
                self._progresso_texto.set(
                    f"{contadores['expandir']:,} expandidos · "
                    f"{contadores['gerar']:,} gerados\n"
                    f"Último evento: {evento} · {decorrido:.1f} s"
                )
                continue
            self._finalizar_execucao()
            if tipo == "falha":
                self._estado.set("Erro na busca")
                messagebox.showerror("Erro na execução", conteudo, parent=self)
            else:
                try:
                    self._apresentar_resultado(configuracao, conteudo)
                except Exception:
                    logger.exception("Falha ao apresentar resultados")
                    self._estado.set("Erro ao apresentar resultados")
                    messagebox.showerror("Erro de apresentação",
                                         "Consulte o terminal.", parent=self)
            break
        if self._em_execucao:
            self._agendar_consulta()

    def _finalizar_execucao(self):
        self._em_execucao = False
        self._spinner.parar()
        self._progresso.stop()
        self._configuracao.definir_bloqueado(False)
        self._botao_limpar.state(["!disabled"])
        self._botao_executar.state(["!disabled"])
        self._botao_executar.configure(
            text="▶  Executar busca", style="Executar.TButton"
        )

    def _apresentar_resultado(self, configuracao, resultado):
        solucao = resultado["solucao"]
        estatisticas = resultado["estatisticas"]
        self._painel_resultados.mostrar_resultados(solucao, estatisticas)
        eventos = resultado.get("eventos") or []
        self._arvore.carregar_eventos(eventos)
        self._mapa.limpar_percurso()
        if solucao is not None:
            self._mapa.destacar_percurso(solucao.get_estados(), solucao.get_accoes())
        registo = {
            **configuracao, **estatisticas,
            "estado_execucao": resultado["estado_execucao"],
            "mensagem": resultado["mensagem"],
            "custo_total": None if solucao is None else solucao.get_custo_total(),
            "solucao": solucao,
        }
        self._resultados.append(registo)
        self._comparacao.mostrar_comparacao(self._resultados)
        self._estado.set(resultado["mensagem"])
        self._progresso_texto.set(
            f"{estatisticas['nos_expandidos']:,} nós expandidos · "
            f"{estatisticas['tempo_segundos']:.2f} s\n"
            f"{resultado['estado_execucao']} · {resultado.get('total_eventos', 0):,} eventos"
        )
        if solucao is not None:
            self._separadores.select(self._mapa)
        elif eventos:
            self._separadores.select(self._arvore)
            # Pré-visualização do ramo de exploração, em vez da raiz isolada.
            self._arvore.mostrar_passo(min(35, len(eventos) - 1))
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
        self._progresso_texto.set("Ao executar, verá aqui os passos da busca.")
        self._estado.set("Resultados limpos")

    def _fechar(self):
        self._cancelar.set()
        self._spinner.parar()
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        self.destroy()
