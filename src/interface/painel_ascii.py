"""Visualização textual, simples e ampliável, da solução encontrada."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def _valor_estado(estado, nome, padrao=None):
    if estado is None:
        return padrao
    if isinstance(estado, dict):
        return estado.get(nome, padrao)
    metodo = getattr(estado, f"get_{nome}", None)
    return metodo() if metodo is not None else getattr(estado, nome, padrao)


def _entregas(estado):
    entregas = _valor_estado(estado, "entregas_concluidas", ()) or ()
    return ", ".join(sorted(map(str, entregas))) or "nenhuma"


def _linha_estado(indice, estado):
    return (
        f"[{indice:02d}] {_valor_estado(estado, 'localidade', '—')}\n"
        f"     tempo={_valor_estado(estado, 'tempo', '—')} min | "
        f"combustível={_valor_estado(estado, 'combustivel', '—')} | "
        f"entregas={_entregas(estado)}"
    )


def _descricao_accao(accao):
    tipo = str(accao.get_tipo()).upper()
    parametros = accao.get_parametros()
    detalhes = ", ".join(f"{chave}={valor}" for chave, valor in parametros.items())
    return tipo if not detalhes else f"{tipo} ({detalhes})"


def formatar_solucao_ascii(
    solucao,
    estado_execucao="concluida",
    mensagem=None,
    ultimo_estado=None,
):
    """Produz uma representação textual dos estados e transições da solução."""
    estado_legivel = str(estado_execucao or "sem_solucao").replace("_", " ").upper()
    linhas = ["=" * 78, f"EXECUÇÃO: {estado_legivel}", "=" * 78]
    if mensagem:
        linhas.extend((f"Motivo: {mensagem}", ""))

    if solucao is None:
        linhas.append("Não existe um percurso completo para apresentar.")
        if ultimo_estado is not None:
            linhas.extend(("", "ÚLTIMO ESTADO EXPLORADO", _linha_estado(0, ultimo_estado)))
        return "\n".join(linhas)

    estados = solucao.get_estados()
    accoes = solucao.get_accoes()
    linhas.extend(
        (
            f"Custo total: {solucao.get_custo_total()}",
            f"Estados: {len(estados)} | Acções: {len(accoes)}",
            "",
            "SOLUÇÃO PASSO A PASSO",
            "",
        )
    )
    for indice, estado in enumerate(estados):
        linhas.append(_linha_estado(indice, estado))
        if indice < len(accoes):
            linhas.extend(("      |", f"      +-- {_descricao_accao(accoes[indice])}", "      v"))
    return "\n".join(linhas)


class PainelASCII(ttk.Frame):
    """Separador de texto monoespaçado para leitura e demonstração."""

    def __init__(self, parent):
        super().__init__(parent, style="Cartao.TFrame")
        ttk.Label(
            self,
            text="Solução em texto — aumente a janela ou use Ctrl+C para copiar",
            style="Cartao.TLabel",
        ).pack(fill="x", padx=12, pady=(10, 4))

        contentor = ttk.Frame(self, style="Cartao.TFrame")
        contentor.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        barra_vertical = ttk.Scrollbar(contentor, orient="vertical")
        barra_horizontal = ttk.Scrollbar(contentor, orient="horizontal")
        self.texto = tk.Text(
            contentor,
            wrap="none",
            font=("Consolas", 12),
            padx=14,
            pady=12,
            background="#FCFCFA",
            foreground="#17202A",
            yscrollcommand=barra_vertical.set,
            xscrollcommand=barra_horizontal.set,
        )
        barra_vertical.config(command=self.texto.yview)
        barra_horizontal.config(command=self.texto.xview)
        barra_vertical.pack(side="right", fill="y")
        barra_horizontal.pack(side="bottom", fill="x")
        self.texto.pack(fill="both", expand=True)
        self.limpar()

    def mostrar_resultado(
        self, solucao, estado_execucao=None, mensagem=None, ultimo_estado=None
    ):
        conteudo = formatar_solucao_ascii(
            solucao, estado_execucao, mensagem, ultimo_estado
        )
        self.texto.config(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", conteudo)
        self.texto.config(state="disabled")

    def limpar(self):
        self.texto.config(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert(
            "1.0",
            "A visualização ASCII aparecerá aqui quando a busca terminar.\n\n"
            "O mapa e a árvore continuam disponíveis nos outros separadores.",
        )
        self.texto.config(state="disabled")
