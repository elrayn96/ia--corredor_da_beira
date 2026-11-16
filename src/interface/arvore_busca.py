"""Árvore de busca passo a passo (Tkinter + Matplotlib).

A árvore mostra os nós gerados pela busca (estado, g, h e f), e não o mapa
físico das localidades. Recebe os eventos definidos em
src/buscas/eventos_busca.py.
"""

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Patch

LIMITE_EVENTOS_PADRAO = 300
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
    """Texto curto do estado: usa a localidade se existir."""
    localidade = getattr(estado, "localidade", None)
    texto = str(localidade if localidade is not None else estado)
    return texto[:MAXIMO_CARACTERES_ROTULO]


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
    return posicoes


class ModeloArvore:
    """Dados da árvore construídos a partir da lista de eventos."""

    def __init__(self, eventos, limite_eventos=LIMITE_EVENTOS_PADRAO):
        self.total_original = len(eventos)
        self.eventos = list(eventos[: max(limite_eventos, 0)])
        self.truncado = self.total_original > len(self.eventos)
        self.nos = {}
        self.filhos = {}
        self.raizes = []
        self._construir()
        self.posicoes = calcular_posicoes(self.nos, self.filhos, self.raizes)

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
        return (
            f"Passo {indice + 1} de {len(self.eventos)}: {evento['tipo']} "
            f"{rotulo_estado(evento['estado'])} "
            f"(g={formatar_numero(evento['g'])}, h={formatar_numero(evento['h'])}, "
            f"f={formatar_numero(evento['f'])})"
        )


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
        rotulo = (
            f"{rotulo_estado(no['estado'])} #{no_id}\n"
            f"g={formatar_numero(no['g'])} h={formatar_numero(no['h'])} "
            f"f={formatar_numero(no['f'])}"
        )
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
    xs = [x for x, _ in modelo.posicoes.values()]
    ys = [y for _, y in modelo.posicoes.values()]
    eixo.set_xlim(min(xs) - MARGEM, max(xs) + MARGEM)
    eixo.set_ylim(min(ys) - MARGEM, max(ys) + MARGEM)
    eixo.legend(
        handles=[Patch(facecolor=CORES[chave], label=NOMES[chave]) for chave in CORES],
        loc="upper right",
        fontsize=7,
    )
    eixo.set_title(modelo.descricao_passo(indice), fontsize=9)


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
        self._a_reproduzir = False
        self._id_after = None
        self._criar_widgets()
        self._desenhar()

    def _criar_widgets(self):
        self._aviso = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._aviso, foreground="#b45309").pack(
            side="top", fill="x", padx=6
        )
        barra = ttk.Frame(self)
        barra.pack(side="bottom", fill="x", pady=4)
        self._figura = Figure(figsize=(8, 5), dpi=100)
        self._eixo = self._figura.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figura, master=self)
        self._canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        self._botoes = {}
        accoes = (
            ("Anterior", self.anterior),
            ("Seguinte", self.seguinte),
            ("Reproduzir", self.reproduzir),
            ("Pausar", self.pausar),
            ("Reiniciar", self.reiniciar_visualizacao),
        )
        for texto, comando in accoes:
            botao = ttk.Button(barra, text=texto, command=comando)
            botao.pack(side="left", padx=3)
            self._botoes[texto] = botao

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
        self._desenhar()

    def reiniciar_visualizacao(self):
        """Pára a reprodução e volta ao primeiro passo."""
        self.pausar()
        self._indice = 0
        self._desenhar()

    # --- controlos --------------------------------------------------------

    def anterior(self):
        self.pausar()
        self.mostrar_passo(self._indice - 1)

    def seguinte(self):
        self.pausar()
        self.mostrar_passo(self._indice + 1)

    def reproduzir(self):
        if self._a_reproduzir or self._indice >= self._total() - 1:
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
            self._modelo = ModeloArvore(self._eventos, self._limite_eventos)
        self._indice = 0
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
        self._indice = min(self._indice + 1, self._total() - 1)
        self._desenhar()
        if self._indice >= self._total() - 1:
            self.pausar()
        else:
            self._id_after = self.after(self._intervalo_ms, self._passo_automatico)

    def _parar_temporizador(self):
        if self._id_after is not None:
            self.after_cancel(self._id_after)
            self._id_after = None

    def _desenhar(self):
        desenhar_arvore(self._eixo, self._modelo, self._indice)
        self._canvas.draw_idle()
        self._actualizar_botoes()

    def _actualizar_botoes(self):
        total = self._total()
        ha_seguinte = self._indice < total - 1
        activos = {
            "Anterior": total > 0 and self._indice > 0,
            "Seguinte": total > 0 and ha_seguinte,
            "Reproduzir": total > 0 and not self._a_reproduzir and ha_seguinte,
            "Pausar": self._a_reproduzir,
            "Reiniciar": total > 0,
        }
        for nome, activo in activos.items():
            self._botoes[nome].state(["!disabled"] if activo else ["disabled"])