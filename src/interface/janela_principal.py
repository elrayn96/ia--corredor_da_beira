"""Janela principal: execução responsiva, cancelamento e progresso real."""

from __future__ import annotations

import logging
import multiprocessing
import queue
import time
import tkinter as tk
from tkinter import messagebox, ttk

from src.gerador import carregar_rede, gerar_demonstracao_validada
from src.interface.arvore_busca import ArvoreBusca
from src.interface.icones import carregar_icone
from src.interface.mapa_rodoviario import MapaRodoviario
from src.interface.painel_ascii import PainelASCII
from src.interface.painel_comparacao import PainelComparacao
from src.interface.painel_configuracao import PainelConfiguracao
from src.interface.painel_resultados import PainelResultados
from src.interface.tema import configurar_estilos
from src.servicos.executar_busca import executar_busca

logger = logging.getLogger(__name__)
LIMITE_TEMPO_GUI = 60  # Limite do enunciado, alterável no painel.


def _resumir_estado(estado):
    """Converte o estado corrente num valor pequeno e serializável."""
    if estado is None:
        return None
    if isinstance(estado, dict):
        return estado
    return {
        "localidade": estado.get_localidade(),
        "tempo": estado.get_tempo(),
        "combustivel": estado.get_combustivel(),
        "entregas_concluidas": tuple(estado.get_entregas_concluidas()),
    }


def _executar_em_processo(configuracao, fila, cancelar):
    """Executa CPU intensiva fora do processo Tk, inclusive no Windows."""
    contadores = {"gerar": 0, "expandir": 0, "descartar": 0}
    inicio = time.perf_counter()
    ultimo_envio = inicio

    def acompanhar(evento):
        nonlocal ultimo_envio
        tipo = evento.get("tipo")
        if tipo in contadores:
            contadores[tipo] += 1
        agora = time.perf_counter()
        if agora - ultimo_envio >= 0.25 or tipo == "objectivo":
            ultimo_envio = agora
            try:
                fila.put_nowait((
                    "progresso", None,
                    (
                        contadores.copy(), tipo, agora - inicio,
                        _resumir_estado(evento.get("estado")),
                    ),
                ))
            except queue.Full:
                pass

    try:
        resultado = executar_busca(
            configuracao, observador=acompanhar, cancelar=cancelar,
            limite_segundos=configuracao.get(
                "limite_segundos", LIMITE_TEMPO_GUI
            ),
        )
        fila.put(("resultado", configuracao, resultado))
    except Exception as erro:  # noqa: BLE001 - fronteira do processo filho
        fila.put((
            "falha", configuracao,
            f"{type(erro).__name__}: {erro}",
        ))


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
        self._contexto_mp = multiprocessing.get_context("spawn")
        self._fila = None
        self._resultados = []
        self._em_execucao = False
        self._cancelar = None
        self._processo = None
        self._configuracao_activa = None
        self._contadores_actuais = {"gerar": 0, "expandir": 0, "descartar": 0}
        self._ultimo_estado_progresso = None
        self._max_fronteira_actual = 0
        self._polls_processo_morto = 0
        self._ultimo_progresso = 0.0
        self._ultima_actualizacao_mapa = 0.0
        self._inicio_busca = None
        self._imagens = []
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
        """Cria um menu superior personalizado com efeitos interactivos."""

        self._menu_superior = tk.Frame(
            self,
            bg="#FFFFFF",
            height=42,
        )
        self._menu_superior.pack(fill="x")
        self._menu_superior.pack_propagate(False)

        def criar_menu_item(titulo, opcoes):
            menu_dropdown = tk.Menu(
                self,
                tearoff=False,
                bg="#FFFFFF",
                fg="#17212B",
                activebackground="#E6F4ED",
                activeforeground="#064D38",
                font=("Segoe UI", 10),
                borderwidth=1,
                relief="solid",
                activeborderwidth=0,
            )

            for texto, comando in opcoes:
                menu_dropdown.add_command(
                    label=texto,
                    command=comando,
                )

            item = tk.Menubutton(
                self._menu_superior,
                text=titulo,
                menu=menu_dropdown,
                direction="below",
                bg="#FFFFFF",
                fg="#17212B",
                activebackground="#E6F4ED",
                activeforeground="#064D38",
                font=("Segoe UI", 10),
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                padx=16,
                pady=7,
                cursor="hand2",
            )
            item.pack(side="left", padx=(5, 0), pady=3)

            def ao_entrar(event):
                item.configure(
                    bg="#E6F4ED",
                    fg="#064D38",
                    font=("Segoe UI", 10, "bold"),
                )

            def ao_sair(event):
                item.configure(
                    bg="#FFFFFF",
                    fg="#17212B",
                    font=("Segoe UI", 10),
                )

            def ao_pressionar(event):
                item.configure(bg="#C7E6D6")

            item.bind("<Enter>", ao_entrar)
            item.bind("<Leave>", ao_sair)
            item.bind("<ButtonPress-1>", ao_pressionar)

            return item

        criar_menu_item(
            "Ficheiro",
            [
                ("Gerar demonstração viável", self._gerar_demonstracao),
                ("Sair", self._fechar),
            ],
        )

        criar_menu_item(
            "Ajuda",
            [
                (
                    "Sobre",
                    lambda: messagebox.showinfo(
                        "Sobre",
                        "Inteligência Artificial I - Grupo 01\n"
                        "Cadeia de frio no Corredor da Beira",
                        parent=self,
                    ),
                ),
            ],
        )

        tk.Frame(
            self._menu_superior,
            bg="#D9E2E8",
            height=1,
        ).pack(side="bottom", fill="x")

    
    def _criar_conteudo(self):
        cabecalho = tk.Frame(self, bg="#064D38", height=66)
        cabecalho.pack(fill="x")
        cabecalho.pack_propagate(False)
        self._icone_frio = carregar_icone(self, "frio")
        tk.Label(cabecalho, image=self._icone_frio, bg="#064D38").pack(
            side="left", padx=(17, 2))
        ttk.Label(cabecalho, text="Cadeia de Frio no Corredor da Beira",
                  style="Cabecalho.TLabel").pack(side="left", padx=4)
        self._estado = tk.StringVar(value="Pronto para começar")
        self._status = tk.Label(
            cabecalho, textvariable=self._estado, bg="#106548", fg="white",
            font=("Segoe UI", 10), padx=16, pady=9, relief="flat",
        )
        self._status.pack(side="right", padx=18)

        corpo = tk.Frame(self, bg="#F3F6F8")
        corpo.pack(fill="both", expand=True, padx=10, pady=10)
        # Coluna lateral deslocável, inclusive em ecrãs de 1366 × 768.
        coluna_lateral = tk.Frame(corpo, bg="#FFFFFF", width=292)
        coluna_lateral.pack(side="left", fill="y", padx=(0, 10))
        coluna_lateral.pack_propagate(False)
        self._lateral_canvas = tk.Canvas(
            coluna_lateral, bg="#FFFFFF", bd=0, highlightthickness=0,
        )
        self._lateral_scroll = ttk.Scrollbar(
            coluna_lateral, orient="vertical",
            command=self._lateral_canvas.yview,
        )
        self._lateral_canvas.configure(yscrollcommand=self._lateral_scroll.set)
        self._lateral_scroll.pack(side="right", fill="y")
        self._lateral_canvas.pack(side="left", fill="both", expand=True)
        lateral = ttk.Frame(self._lateral_canvas, padding=6, style="Cartao.TFrame")
        janela_lateral = self._lateral_canvas.create_window(
            (0, 0), window=lateral, anchor="nw",
        )
        lateral.bind(
            "<Configure>",
            lambda _evento: self._lateral_canvas.configure(
                scrollregion=self._lateral_canvas.bbox("all")
            ),
        )
        self._lateral_canvas.bind(
            "<Configure>",
            lambda evento: self._lateral_canvas.itemconfigure(
                janela_lateral, width=evento.width,
            ),
        )
        principal = ttk.Frame(corpo, style="Cartao.TFrame")
        principal.pack(side="left", fill="both", expand=True)

        self._configuracao = PainelConfiguracao(
            lateral, ao_alterar_instancia=self._ao_carregar_instancia
        )
        self._configuracao.pack(fill="x")
        self._icone_executar = carregar_icone(self, "executar")
        self._icone_cancelar = carregar_icone(self, "cancelar")
        self._icone_limpar = carregar_icone(self, "limpar")
        self._botao_executar = ttk.Button(
            lateral, text="Executar busca", image=self._icone_executar,
            compound="left", style="Executar.TButton",
            command=self._iniciar_busca,
        )
        self._botao_executar.pack(fill="x", padx=8, pady=(13, 5))
        self._botao_limpar = ttk.Button(
            lateral, text="Limpar resultados", image=self._icone_limpar,
            compound="left", style="Secundario.TButton",
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
        self._ascii = PainelASCII(self._separadores)
        self._arvore = ArvoreBusca(self._separadores)
        self._comparacao = PainelComparacao(self._separadores)
        for painel, titulo, nome in (
            (self._mapa, "Mapa", "mapa"),
            (self._painel_resultados, "Resultados", "resultados"),
            (self._ascii, "ASCII", "resultados"),
            (self._arvore, "Árvore de busca", "arvore"),
            (self._comparacao, "Comparação", "comparacao"),
        ):
            imagem = carregar_icone(self, nome)
            self._imagens.append(imagem)
            self._separadores.add(painel, text=f"  {titulo}  ",
                                   image=imagem, compound="left")

    def _gerar_demonstracao(self):
        """Mostra um percurso testemunha, diferente de uma busca calculada."""
        if self._em_execucao:
            return
        try:
            _instancia, caminho, solucao = gerar_demonstracao_validada()
            self._configuracao.carregar_instancia(caminho)
            self._mapa.destacar_percurso(solucao.get_estados(), solucao.get_accoes())
            self._ascii.mostrar_resultado(
                solucao,
                "concluida",
                "Percurso de demonstração; não é um resultado de busca.",
            )
            self._estado.set(
                f"Demonstração validada: percurso de referência de "
                f"{solucao.get_custo_total():.0f} min. Não é um resultado de busca."
            )
            self._separadores.select(self._mapa)
        except (OSError, ValueError, KeyError, TypeError) as erro:
            messagebox.showerror("Demonstração indisponível", str(erro), parent=self)

    def _ao_carregar_instancia(self, instancia):
        self._mapa.mostrar_instancia(instancia)
        self._estado.set("Instância seleccionada. Pronto para executar.")

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
        self._fila = self._contexto_mp.Queue(maxsize=48)
        self._cancelar = self._contexto_mp.Event()
        self._configuracao_activa = configuracao
        self._contadores_actuais = {"gerar": 0, "expandir": 0, "descartar": 0}
        self._ultimo_estado_progresso = None
        self._max_fronteira_actual = 0
        self._polls_processo_morto = 0
        self._inicio_busca = time.perf_counter()
        self._arvore.definir_algoritmo(configuracao["algoritmo"])
        self._mapa.limpar_exploracao()
        self._mapa.limpar_percurso()
        self._separadores.select(self._mapa)
        self._iniciar_sobreposicao()
        self._configuracao.definir_bloqueado(True)
        self._botao_limpar.state(["disabled"])
        self._botao_executar.configure(
            text="Terminar algoritmo", image=self._icone_cancelar,
            style="Cancelar.TButton"
        )
        self._spinner.iniciar()
        self._estado.set("Busca em execução")
        self._progresso_texto.set("A preparar problema e a iniciar o algoritmo...")
        # Separadores continuam acessíveis para consulta; as configurações ficam bloqueadas.
        self._processo = self._contexto_mp.Process(
            target=_executar_em_processo,
            args=(configuracao, self._fila, self._cancelar),
            daemon=True,
        )
        self._processo.start()
        self._agendar_consulta()

    def _cancelar_busca(self):
        if not self._em_execucao:
            return
        self._cancelar.set()
        self._botao_executar.state(["disabled"])
        self._estado.set("Cancelamento solicitado pelo utilizador")
        self._progresso_texto.set(
            "A terminar o algoritmo e a recolher o último estado explorado."
        )
        self.after(2000, self._forcar_cancelamento, self._processo)

    def _forcar_cancelamento(self, processo):
        """Garante que o botão Terminar não fica dependente do algoritmo."""
        if not self._em_execucao or processo is not self._processo:
            return
        if not processo.is_alive():
            return
        processo.terminate()
        processo.join(timeout=0.5)
        decorrido = time.perf_counter() - self._inicio_busca
        contadores = self._contadores_actuais
        resultado = {
            "solucao": None,
            "estatisticas": {
                "nos_gerados": contadores["gerar"],
                "nos_expandidos": contadores["expandir"],
                "nos_reexpandidos": 0,
                "max_fronteira": self._max_fronteira_actual,
                "comprimento_caminho": 0,
                "tempo_segundos": decorrido,
                "memoria_pico_bytes": 0,
            },
            "eventos": [],
            "total_eventos": sum(contadores.values()),
            "estado_execucao": "interrompida",
            "mensagem": "Busca cancelada pelo utilizador.",
            "motivo_termino": "cancelamento_utilizador",
            "ultimo_estado": self._ultimo_estado_progresso,
        }
        configuracao = self._configuracao_activa
        self._finalizar_execucao()
        self._apresentar_resultado(configuracao, resultado)

    def _agendar_consulta(self):
        if self._poll_id is None:
            self._poll_id = self.after(100, self._consultar_fila)

    def _consultar_fila(self):
        self._poll_id = None
        if self._fila is None:
            return
        for _ in range(40):
            try:
                tipo, configuracao, conteudo = self._fila.get_nowait()
            except queue.Empty:
                break
            if tipo == "progresso":
                contadores, evento, decorrido, estado = conteudo
                self._contadores_actuais = contadores
                self._ultimo_estado_progresso = estado
                self._max_fronteira_actual = max(
                    self._max_fronteira_actual,
                    max(0, contadores["gerar"] - contadores["expandir"]),
                )
                localidade = None if estado is None else estado.get("localidade")
                if (localidade and evento in {"expandir", "objectivo"}
                        and time.perf_counter() - self._ultima_actualizacao_mapa > 0.8):
                    self._mapa.mostrar_exploracao(localidade)
                    self._ultima_actualizacao_mapa = time.perf_counter()
                self._progresso_texto.set(
                    f"{contadores['expandir']:,} expandidos · "
                    f"{contadores['gerar']:,} gerados\n"
                    f"Último estado: {localidade or '—'} · "
                    f"{evento} · {decorrido:.1f} s"
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
        if (
            self._em_execucao and self._processo is not None
            and not self._processo.is_alive()
        ):
            self._polls_processo_morto += 1
            if self._polls_processo_morto >= 10:
                self._finalizar_execucao()
                self._estado.set("O processo de busca terminou inesperadamente")
                messagebox.showerror(
                    "Erro na execução",
                    "O processo terminou sem devolver um resultado.",
                    parent=self,
                )
                return
        else:
            self._polls_processo_morto = 0
        if self._em_execucao:
            self._agendar_consulta()

    def _iniciar_sobreposicao(self):
        """Indicador não modal sobre o mapa, preservando acesso ao Cancelar."""
        if getattr(self, "_sobreposicao", None) is None:
            self._sobreposicao = tk.Frame(
                self._mapa._canvas.get_tk_widget(), bg="#E6F4ED",
                highlightbackground="#8CBBA5", highlightthickness=1,
            )
            self._spinner_mapa = IndicadorActividade(self._sobreposicao, "#E6F4ED")
            self._spinner_mapa.pack(side="left", padx=(15, 10), pady=12)
            tk.Label(
                self._sobreposicao, text="A explorar estados...",
                bg="#E6F4ED", fg="#064D38",
                font=("Segoe UI", 12, "bold"),
            ).pack(side="left", padx=(0, 15))
        self._sobreposicao.place(relx=0.5, rely=0.14, anchor="center")
        self._sobreposicao.lift()
        self._spinner_mapa.iniciar()

    def _parar_sobreposicao(self):
        if getattr(self, "_sobreposicao", None) is not None:
            self._spinner_mapa.parar()
            self._sobreposicao.place_forget()

    def _finalizar_execucao(self):
        self._em_execucao = False
        self._spinner.parar()
        self._parar_sobreposicao()
        self._progresso.stop()
        self._configuracao.definir_bloqueado(False)
        self._botao_limpar.state(["!disabled"])
        self._botao_executar.state(["!disabled"])
        self._botao_executar.configure(
            text="Executar busca", image=self._icone_executar,
            style="Executar.TButton"
        )
        processo = self._processo
        self._processo = None
        if processo is not None:
            self.after(100, self._recolher_processo, processo)

    def _recolher_processo(self, processo):
        if processo.is_alive():
            self.after(100, self._recolher_processo, processo)
        else:
            processo.join(timeout=0)

    def _apresentar_resultado(self, configuracao, resultado):
        solucao = resultado["solucao"]
        estatisticas = resultado["estatisticas"]
        self._painel_resultados.mostrar_resultados(
            solucao, estatisticas,
            resultado.get("estado_execucao"), resultado.get("mensagem"),
            resultado.get("ultimo_estado"),
        )
        self._ascii.mostrar_resultado(
            solucao,
            resultado.get("estado_execucao"),
            resultado.get("mensagem"),
            resultado.get("ultimo_estado"),
        )
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
        elif resultado["estado_execucao"] == "interrompida":
            self._separadores.select(self._painel_resultados)
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
        self._ascii.limpar()
        self._arvore.carregar_eventos([])
        self._comparacao.limpar()
        self._mapa.limpar_percurso()
        self._mapa.limpar_exploracao()
        self._progresso_texto.set("Ao executar, verá aqui os passos da busca.")
        self._estado.set("Resultados limpos")

    def _fechar(self):
        if self._cancelar is not None:
            self._cancelar.set()
        if self._processo is not None and self._processo.is_alive():
            self._processo.terminate()
            self._processo.join(timeout=0.5)
        self._spinner.parar()
        self._parar_sobreposicao()
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        self.destroy()
