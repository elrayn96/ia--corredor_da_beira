"""Árvore de busca passo a passo (Tkinter + Matplotlib).

A árvore mostra os nós gerados pela busca (estado, g, h e f), e não o mapa
físico das localidades. Recebe os eventos definidos em
src/buscas/eventos_busca.py.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib import rc_context
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from src.interface.icones import carregar_icone

LIMITE_EVENTOS_PADRAO = 450
INTERVALO_PADRAO_MS = 700
MAXIMO_CARACTERES_ROTULO = 12
MARGEM = 1.0

ESTADO_POR_TIPO = {
    "inicio": "fronteira",
    "gerar": "fronteira",
    "reabrir": "fronteira",
    "expandir": "expandido",
    "descartar": "descartado",
    "objectivo": "objectivo",
}

CORES = {
    "fronteira": "#cfe8ff",
    "expandido": "#ffe08a",
    "descartado": "#d9d9d9",
    "objectivo": "#8fd19e",
    "solucao": "#4caf50",
}

NOMES = {
    "fronteira": "Fronteira",
    "expandido": "Expandido",
    "descartado": "Descartado",
    "objectivo": "Objectivo",
    "solucao": "Caminho da solução",
}


def formatar_numero(valor):
    """Devolve o número como texto curto; None aparece como '-'."""
    if valor is None:
        return "-"
    if isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() else f"{valor:.2f}"
    return str(valor)


def rotulo_estado(estado):
    """Devolve um rótulo curto com a localidade do estado."""
    if isinstance(estado, dict):
        texto = estado.get("localidade", estado)
    elif hasattr(estado, "get_localidade"):
        texto = estado.get_localidade()
    else:
        texto = getattr(estado, "localidade", estado)

    return str(texto)[:MAXIMO_CARACTERES_ROTULO]


def calcular_posicoes(nos, filhos, raizes):
    """Calcula (x, y) de cada nó. Folhas ficam da esquerda para a direita
    e cada pai fica ao centro dos filhos. Não usa recursão."""
    posicoes = {}
    proximo_x = 0
    for raiz in raizes:
        pilha = [(raiz, False)]
        while pilha:
            no_id, visitado = pilha.pop()
            y = -nos[no_id]["profundidade"]
            if visitado:
                xs = [posicoes[filho][0] for filho in filhos[no_id]]
                posicoes[no_id] = (sum(xs) / len(xs), y)
            elif not filhos[no_id]:
                posicoes[no_id] = (proximo_x, y)
                proximo_x += 1
            else:
                pilha.append((no_id, True))
                pilha.extend((filho, False) for filho in reversed(filhos[no_id]))
    # Folhas espaçadas pelo tamanho real do rótulo, sem sacrificar a estrutura.
    return {no_id: (x * 3.2, y * 2.1) for no_id, (x, y) in posicoes.items()}


class ModeloArvore:
    """Dados da árvore construídos a partir da lista de eventos."""

    def __init__(self, eventos, limite_eventos=LIMITE_EVENTOS_PADRAO,
                 mostrar_heuristica=True):
        self.mostrar_heuristica = mostrar_heuristica
        self.total_original = len(eventos)
        self.eventos = list(eventos[: max(limite_eventos, 0)])
        self.truncado = self.total_original > len(self.eventos)
        self.nos = {}
        self.filhos = {}
        self.raizes = []
        self._construir()
        self.posicoes = calcular_posicoes(self.nos, self.filhos, self.raizes)
        self.passos = self._agrupar_expansoes()

    def _agrupar_expansoes(self):
        """Uma expansão e todos os filhos gerados representam um único passo."""
        if not self.eventos:
            return []
        finais = []
        houve_expansao = False
        for indice, evento in enumerate(self.eventos):
            tipo = evento["tipo"]
            if tipo == "expandir":
                if houve_expansao and indice > 0:
                    finais.append(indice - 1)
                houve_expansao = True
            elif tipo == "objectivo":
                finais.append(indice)
        finais.append(len(self.eventos) - 1)
        return sorted(set(finais))

    def _construir(self):
        for passo, evento in enumerate(self.eventos):
            no_id = evento["no_id"]
            if no_id in self.nos:
                continue
            pai_id = evento["pai_id"]
            pai = self.nos.get(pai_id)
            profundidade = 0 if pai is None else pai["profundidade"] + 1
            self.nos[no_id] = {
                "estado": evento["estado"],
                "pai_id": pai_id,
                "profundidade": profundidade,
                "g": evento["g"],
                "h": evento["h"],
                "f": evento["f"],
                "passo": passo,
            }
            self.filhos[no_id] = []
            if pai_id in self.filhos:
                self.filhos[pai_id].append(no_id)
            else:
                self.raizes.append(no_id)

    def nos_visiveis(self, indice):
        """Nós já criados até ao passo indicado (inclusive)."""
        return [no_id for no_id, no in self.nos.items() if no["passo"] <= indice]

    def estados_no_passo(self, indice):
        """Estado de cada nó no passo indicado: fronteira, expandido,
        descartado, objectivo ou solucao (caminho até ao objectivo)."""
        estados = {}
        objectivo = None
        for evento in self.eventos[: indice + 1]:
            estados[evento["no_id"]] = ESTADO_POR_TIPO.get(evento["tipo"], "fronteira")
            if evento["tipo"] == "objectivo":
                objectivo = evento["no_id"]
        atual = objectivo
        while atual in self.nos:
            if atual != objectivo:
                estados[atual] = "solucao"
            atual = self.nos[atual]["pai_id"]
        return estados

    def descricao_passo(self, indice):
        evento = self.eventos[indice]
        valores = f"g={formatar_numero(evento['g'])}"
        if self.mostrar_heuristica:
            valores += (f", h={formatar_numero(evento['h'])}, "
                        f"f={formatar_numero(evento['f'])}")
        return (f"Evento {indice + 1} de {len(self.eventos)}: {evento['tipo']} "
                f"{rotulo_estado(evento['estado'])} ({valores})")


def _desenhar_ligacoes(eixo, modelo, visiveis):
    for no_id in visiveis:
        pai_id = modelo.nos[no_id]["pai_id"]
        if pai_id in visiveis:
            x, y = modelo.posicoes[no_id]
            pai_x, pai_y = modelo.posicoes[pai_id]
            eixo.plot([pai_x, x], [pai_y, y], color="#888888", linewidth=0.8, zorder=1)


def _desenhar_nos(eixo, modelo, visiveis, estados, atual):
    for no_id in visiveis:
        no = modelo.nos[no_id]
        x, y = modelo.posicoes[no_id]
        rotulo = f"{rotulo_estado(no['estado'])} #{no_id}\ng={formatar_numero(no['g'])}"
        if modelo.mostrar_heuristica:
            rotulo += (f" h={formatar_numero(no['h'])} "
                       f"f={formatar_numero(no['f'])}")
        eixo.text(
            x,
            y,
            rotulo,
            ha="center",
            va="center",
            fontsize=6,
            zorder=2,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": CORES[estados.get(no_id, "fronteira")],
                "edgecolor": "#d62728" if no_id == atual else "#555555",
                "linewidth": 2.5 if no_id == atual else 0.8,
            },
        )


def desenhar_arvore(eixo, modelo, indice):
    """Desenha a árvore tal como está no passo indicado."""
    eixo.clear()
    eixo.set_axis_off()
    if modelo is None or not modelo.eventos:
        eixo.text(0.5, 0.5, "Sem eventos para mostrar.", ha="center", va="center",
                  transform=eixo.transAxes)
        return
    visiveis = set(modelo.nos_visiveis(indice))
    estados = modelo.estados_no_passo(indice)
    _desenhar_ligacoes(eixo, modelo, visiveis)
    _desenhar_nos(eixo, modelo, visiveis, estados, modelo.eventos[indice]["no_id"])
    # Zoom automático para os nós existentes no passo actual; usar todas
    # as folhas futuras tornava a árvore minúscula e ilegível.
    xs = [modelo.posicoes[no_id][0] for no_id in visiveis]
    ys = [modelo.posicoes[no_id][1] for no_id in visiveis]
    margem_x = max(MARGEM, (max(xs) - min(xs)) * 0.12)
    # Uma vista totalmente ajustada a centenas de nós tornaria os rótulos
    # ilegíveis. Mantém uma janela com cerca de 14 folhas em foco; o restante
    # pode ser explorado por arrasto, zoom ou pelo botão Ajustar.
    if max(xs) - min(xs) > 14 * 3.2:
        actual = modelo.eventos[indice]["no_id"]
        centro = modelo.posicoes.get(actual, (sum(xs) / len(xs), 0))[0]
        eixo.set_xlim(centro - 7 * 3.2, centro + 7 * 3.2)
    else:
        eixo.set_xlim(min(xs) - margem_x, max(xs) + margem_x)
    eixo.set_ylim(min(ys) - MARGEM, max(ys) + MARGEM)
    eixo.legend(
        handles=[Patch(facecolor=CORES[chave], label=NOMES[chave]) for chave in CORES],
        loc="upper right",
        fontsize=7,
    )
    eixo.set_title(modelo.descricao_passo(indice), fontsize=9)


def exportar_arvore(modelo, indice, caminho):
    """Exporta todos os nós mostrados até ao passo, não só a vista ampliada.

    SVG e PDF são vectoriais. PNG fica limitado para evitar ficheiros enormes.
    A figura temporária é isolada do canvas Tkinter.
    """
    if modelo is None or not modelo.eventos:
        raise ValueError("Não há uma árvore de busca para exportar.")
    if not 0 <= indice < len(modelo.eventos):
        raise ValueError("Passo inválido para exportação.")

    destino = str(caminho)
    extensao = destino.rsplit(".", 1)[-1].lower()
    if extensao not in {"svg", "pdf", "png"}:
        raise ValueError("Utilize SVG, PDF ou PNG.")

    visiveis = modelo.nos_visiveis(indice)
    xs = [modelo.posicoes[n][0] for n in visiveis]
    ys = [modelo.posicoes[n][1] for n in visiveis]
    largura_dados = max(xs) - min(xs)
    altura_dados = max(ys) - min(ys)
    # Reservar espaço suficiente para etiquetas e ramificações.
    # SVG/PDF podem ser ampliados pelo docente sem perda de nitidez.
    largura = min(100.0 if extensao != "png" else 24.0,
                  max(12.0, largura_dados / 3.2 * 0.85))
    altura = min(90.0 if extensao != "png" else 18.0,
                 max(7.0, altura_dados / 2.1 * 0.85 + 3.0))
    figura = Figure(figsize=(largura, altura), dpi=100, facecolor="white")
    try:
        eixo = figura.add_subplot(111)
        desenhar_arvore(eixo, modelo, indice)
        margem_x = max(3.0, largura_dados * 0.025)
        margem_y = max(2.0, altura_dados * 0.05)
        eixo.set_xlim(min(xs) - margem_x, max(xs) + margem_x)
        eixo.set_ylim(min(ys) - margem_y, max(ys) + margem_y)
        figura.subplots_adjust(left=0.015, right=0.985, top=0.955, bottom=0.025)
        # Manter texto SVG como texto seleccionável em vez de contornos.
        with rc_context({"svg.fonttype": "none"}):
            figura.savefig(destino, format=extensao,
                           dpi=300 if extensao == "png" else 100,
                           facecolor="white")
    finally:
        figura.clear()


class ArvoreBusca(ttk.Frame):
    """Painel que mostra, passo a passo, a árvore de busca."""

    def __init__(self, parent, limite_eventos=LIMITE_EVENTOS_PADRAO,
                 intervalo_ms=INTERVALO_PADRAO_MS):
        super().__init__(parent)
        self._limite_eventos = limite_eventos
        self._intervalo_ms = intervalo_ms
        self._eventos = []
        self._modelo = None
        self._indice = 0
        self._passo = 0
        self._mostrar_heuristica = True
        self._zoom = 1.0
        self._vista = None
        self._arrasto = None
        self._a_reproduzir = False
        self._id_after = None
        self._criar_widgets()
        self._desenhar()

    def _criar_widgets(self):
        self._aviso = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._aviso, foreground="#B45309").pack(
            side="top", fill="x", padx=9
        )
        barra = ttk.Frame(self, style="Cartao.TFrame", padding=(12, 8))
        barra.pack(side="top", fill="x")
        self._botoes = {}
        self._imagens = []
        for nome, icone, comando in (
            ("Anterior", "anterior", self.anterior),
            ("Reproduzir", "reproduzir", self.alternar_reproducao),
            ("Reiniciar", "reiniciar", self.reiniciar_visualizacao),
            ("Seguinte", "seguinte", self.seguinte),
            ("Aumentar", "mais", self.ampliar),
            ("Diminuir", "menos", self.reduzir),
            ("Ajustar", "ajustar", self.ajustar_vista),
        ):
            imagem = carregar_icone(self, icone, 19)
            self._imagens.append(imagem)
            botao = ttk.Button(barra, image=imagem, command=comando,
                               style="Secundario.TButton", width=3)
            botao.pack(side="left", padx=3)
            self._botoes[nome] = botao
        # A exportação SVG é vectorial; não perde nitidez ao ampliar.
        self._botao_exportar = ttk.Button(
            barra, text="Exportar árvore", command=self.exportar_imagem,
            style="Secundario.TButton",
        )
        self._botao_exportar.pack(side="left", padx=(13, 3))
        self._botao_fullscreen = ttk.Button(
            barra, text="Ecrã inteiro", command=self.abrir_ecran_inteiro,
            style="Secundario.TButton",
        )
        self._botao_fullscreen.pack(side="left", padx=3)
        self._contador = tk.StringVar(value="Sem eventos")
        ttk.Label(barra, textvariable=self._contador, style="Cartao.TLabel").pack(
            side="right", padx=8
        )
        instrucoes = ttk.Label(
            self, text="Roda do rato: zoom  |  Arrastar: mover  |  Cada passo expande um nó e apresenta os seus filhos",
            style="Ajuda.TLabel",
        )
        instrucoes.pack(side="top", anchor="w", padx=12, pady=(3, 3))
        self._figura = Figure(figsize=(8, 5), dpi=90, facecolor="#FFFFFF")
        self._eixo = self._figura.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figura, master=self)
        self._canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        self._canvas.mpl_connect("scroll_event", self._ao_scroll)
        self._canvas.mpl_connect("button_press_event", self._ao_press)
        self._canvas.mpl_connect("motion_notify_event", self._ao_mover)
        self._canvas.mpl_connect("button_release_event", self._ao_soltar)

    def exportar_imagem(self):
        """Permite guardar a árvore visível até ao passo actual em alta qualidade."""
        if self._modelo is None or not self._modelo.eventos:
            messagebox.showinfo("Exportar árvore", "Execute primeiro uma busca.",
                                parent=self)
            return
        caminho = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar árvore de busca",
            initialfile=f"arvore_passo_{self._passo + 1}.svg",
            defaultextension=".svg",
            filetypes=[("SVG vectorial (recomendado)", "*.svg"),
                       ("PDF vectorial", "*.pdf"),
                       ("PNG 300 dpi", "*.png")],
        )
        if not caminho:
            return
        try:
            exportar_arvore(self._modelo, self._indice, caminho)
        except (OSError, ValueError, RuntimeError) as erro:
            messagebox.showerror("Falha na exportação", str(erro), parent=self)
        else:
            messagebox.showinfo("Árvore exportada", f"Ficheiro guardado em:\n{caminho}",
                                parent=self)

    def abrir_ecran_inteiro(self):
        """Abre uma vista ampliada real; Esc fecha e devolve à janela principal."""
        if getattr(self, "_janela_fullscreen", None) is not None and self._janela_fullscreen.winfo_exists():
            self._janela_fullscreen.lift()
            return
        janela = tk.Toplevel(self)
        janela.title("Árvore de busca – Ecrã inteiro")
        janela.configure(background="#FFFFFF")
        self._janela_fullscreen = janela
        topo = ttk.Frame(janela, padding=(10, 5))
        topo.pack(fill="x")
        ttk.Label(topo, text="Árvore de busca – arraste com a barra de navegação para mover",
                  style="Cartao.TLabel").pack(side="left", padx=8)
        ttk.Button(topo, text="Exportar árvore", command=self.exportar_imagem,
                   style="Secundario.TButton").pack(side="right", padx=6)
        ttk.Button(topo, text="Sair (Esc)", command=janela.destroy,
                   style="Secundario.TButton").pack(side="right")
        figura = Figure(figsize=(12, 8), dpi=100, facecolor="#FFFFFF")
        eixo = figura.add_subplot(111)
        desenhar_arvore(eixo, self._modelo, self._indice)
        canvas = FigureCanvasTkAgg(figura, master=janela)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        ferramentas = NavigationToolbar2Tk(canvas, janela, pack_toolbar=False)
        ferramentas.update()
        ferramentas.pack(fill="x")
        canvas.draw_idle()
        janela.bind("<Escape>", lambda _evento: janela.destroy())
        janela.protocol("WM_DELETE_WINDOW", janela.destroy)
        try:
            janela.attributes("-fullscreen", True)
        except tk.TclError:
            try:
                janela.state("zoomed")
            except tk.TclError:
                janela.geometry("1200x800")
        janela.focus_set()

    def definir_algoritmo(self, algoritmo):
        self._mostrar_heuristica = algoritmo in {
            "busca_gulosa", "a_star", "a_star_ponderada"
        }
        if self._modelo is not None:
            self._modelo.mostrar_heuristica = self._mostrar_heuristica
            self._desenhar()

    def _alterar_zoom(self, factor, centro=None):
        limites = self._vista or (self._eixo.get_xlim(), self._eixo.get_ylim())
        (x0, x1), (y0, y1) = limites
        cx, cy = centro if centro is not None else ((x0 + x1) / 2, (y0 + y1) / 2)
        self._vista = ((cx + (x0 - cx) * factor, cx + (x1 - cx) * factor),
                       (cy + (y0 - cy) * factor, cy + (y1 - cy) * factor))
        self._desenhar()

    def ampliar(self):
        self._alterar_zoom(0.76)

    def reduzir(self):
        self._alterar_zoom(1.32)

    def ajustar_vista(self):
        self._vista = None
        self._desenhar()

    def _ao_scroll(self, evento):
        if evento.inaxes is self._eixo:
            self._alterar_zoom(0.78 if evento.button == "up" else 1.28,
                               (evento.xdata, evento.ydata))

    def _ao_press(self, evento):
        if evento.inaxes is self._eixo and evento.button == 1:
            self._arrasto = (evento.xdata, evento.ydata)

    def _ao_mover(self, evento):
        if self._arrasto is None or evento.inaxes is not self._eixo:
            return
        dx = self._arrasto[0] - evento.xdata
        dy = self._arrasto[1] - evento.ydata
        (x0, x1), (y0, y1) = self._vista or (
            self._eixo.get_xlim(), self._eixo.get_ylim()
        )
        self._vista = ((x0 + dx, x1 + dx), (y0 + dy, y1 + dy))
        self._desenhar()

    def _ao_soltar(self, _evento):
        self._arrasto = None

    def alternar_reproducao(self):
        if self._a_reproduzir:
            self.pausar()
        else:
            self.reproduzir()

    # --- contrato público ------------------------------------------------

    def carregar_eventos(self, eventos):
        """Recebe a lista de eventos de uma busca e mostra o primeiro passo."""
        self.pausar()
        self._eventos = list(eventos or [])
        self._reconstruir_modelo()

    def mostrar_passo(self, indice):
        """Mostra a árvore no passo indicado (0 é o primeiro)."""
        total = self._total()
        if total:
            self._indice = max(0, min(indice, total - 1))
            self._passo = next((j for j, fim in enumerate(self._modelo.passos)
                                if fim >= self._indice), self._total_passos() - 1)
        self._vista = None
        self._desenhar()

    def reiniciar_visualizacao(self):
        """Pára a reprodução e volta ao primeiro passo."""
        self.pausar()
        self._indice = 0
        self._passo = 0
        self._vista = None
        self._desenhar()

    # --- controlos --------------------------------------------------------

    def anterior(self):
        self.pausar()
        self._passo = max(0, self._passo - 1)
        self._mostrar_passo_agrupado()

    def seguinte(self):
        self.pausar()
        self._passo = min(self._total_passos() - 1, self._passo + 1)
        self._mostrar_passo_agrupado()

    def _total_passos(self):
        return len(self._modelo.passos) if self._modelo else 0

    def _mostrar_passo_agrupado(self):
        if self._modelo and self._modelo.passos:
            self._indice = self._modelo.passos[self._passo]
        self._vista = None
        self._desenhar()

    def reproduzir(self):
        if self._a_reproduzir or self._passo >= self._total_passos() - 1:
            return
        self._a_reproduzir = True
        self._actualizar_botoes()
        self._id_after = self.after(self._intervalo_ms, self._passo_automatico)

    def pausar(self):
        self._parar_temporizador()
        self._a_reproduzir = False
        self._actualizar_botoes()

    def definir_limite_eventos(self, limite):
        """Muda o máximo de eventos mostrados e reconstrói a árvore."""
        if not isinstance(limite, int) or limite < 1:
            raise ValueError("O limite de eventos tem de ser um inteiro positivo.")
        self._limite_eventos = limite
        self.pausar()
        self._reconstruir_modelo()

    def destroy(self):
        self._parar_temporizador()
        super().destroy()

    # --- interior ---------------------------------------------------------

    def _total(self):
        return len(self._modelo.eventos) if self._modelo else 0

    def _reconstruir_modelo(self):
        self._modelo = None
        if self._eventos:
            self._modelo = ModeloArvore(self._eventos, self._limite_eventos,
                                       self._mostrar_heuristica)
        self._indice = 0
        self._passo = 0
        self._vista = None
        if self._modelo and self._modelo.truncado:
            self._aviso.set(
                f"Aviso: a mostrar só os primeiros {len(self._modelo.eventos)} "
                f"de {self._modelo.total_original} eventos."
            )
        else:
            self._aviso.set("")
        self._desenhar()

    def _passo_automatico(self):
        self._id_after = None
        if not self._a_reproduzir:
            return
        self._passo = min(self._passo + 1, self._total_passos() - 1)
        self._mostrar_passo_agrupado()
        if self._passo >= self._total_passos() - 1:
            self.pausar()
        else:
            self._id_after = self.after(self._intervalo_ms, self._passo_automatico)

    def _parar_temporizador(self):
        if self._id_after is not None:
            self.after_cancel(self._id_after)
            self._id_after = None

    def _desenhar(self):
        desenhar_arvore(self._eixo, self._modelo, self._indice)
        if self._vista is not None:
            self._eixo.set_xlim(*self._vista[0])
            self._eixo.set_ylim(*self._vista[1])
        self._canvas.draw_idle()
        self._actualizar_botoes()

    def _actualizar_botoes(self):
        total = self._total_passos()
        self._contador.set(f"Passo {self._passo + 1}/{total}" if total else "Sem eventos")
        estados = {
            "Anterior": total > 0 and self._passo > 0,
            "Seguinte": total > 0 and self._passo < total - 1,
            "Reproduzir": total > 0 and (self._a_reproduzir or self._passo < total - 1),
            "Reiniciar": total > 0,
        }
        for nome, activo in estados.items():
            self._botoes[nome].state(["!disabled"] if activo else ["disabled"])
        self._botao_exportar.state(["!disabled"] if total else ["disabled"])
        # A mesma superfície alterna visualmente entre reprodução e pausa.
        nome_icone = "pausar" if self._a_reproduzir else "reproduzir"
        if getattr(self, "_icone_play_actual", None) != nome_icone:
            imagem = carregar_icone(self, nome_icone, 19)
            self._imagens.append(imagem)
            self._botoes["Reproduzir"].configure(image=imagem)
            self._icone_play_actual = nome_icone
