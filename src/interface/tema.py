
"""Identidade visual da aplicação Cadeia de Frio."""

from tkinter import ttk

VERDE_PRINCIPAL = "#086B47"
VERDE_ESCURO = "#064D38"
VERDE_CLARO = "#E6F4ED"

FUNDO = "#F3F6F8"
PAINEL = "#FFFFFF"
TEXTO = "#17212B"
TEXTO_SECUNDARIO = "#64748B"
BORDA = "#D9E2E8"

# Compatibilidade com componentes que utilizam os nomes antigos.
AZUL_ESCURO = VERDE_ESCURO
AZUL = VERDE_PRINCIPAL
SUCESSO = VERDE_PRINCIPAL

FONTE = "Segoe UI"

# Preservar as cores semânticas da árvore.
CORES_ARVORE = {
    "fronteira": "#cfe8ff",
    "expandido": "#ffe08a",
    "descartado": "#d9d9d9",
    "objectivo": "#8fd19e",
    "solucao": "#4caf50",
}


def configurar_estilos(raiz):
    """Configura os estilos partilhados pelos widgets ttk."""
    estilo = ttk.Style(raiz)

    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")

    estilo.configure(
        "TFrame",
        background=FUNDO,
    )

    estilo.configure(
        "Cartao.TFrame",
        background=PAINEL,
    )

    estilo.configure(
        "TLabel",
        background=FUNDO,
        foreground=TEXTO,
        font=(FONTE, 10),
    )

    estilo.configure(
        "Cartao.TLabel",
        background=PAINEL,
        foreground=TEXTO,
        font=(FONTE, 10),
    )

    estilo.configure(
        "Titulo.TLabel",
        background=FUNDO,
        foreground=TEXTO,
        font=(FONTE, 15, "bold"),
    )

    estilo.configure(
        "Cabecalho.TLabel",
        background=VERDE_ESCURO,
        foreground="#FFFFFF",
        font=(FONTE, 17, "bold"),
        padding=(16, 14),
    )

    estilo.configure(
        "Estado.TLabel",
        background=VERDE_ESCURO,
        foreground="#FFFFFF",
        font=(FONTE, 10),
        padding=(12, 8),
    )

    estilo.configure(
        "TButton",
        font=(FONTE, 10),
        padding=(12, 9),
    )

    estilo.configure(
        "Executar.TButton",
        background=VERDE_PRINCIPAL,
        foreground="#FFFFFF",
        font=(FONTE, 10, "bold"),
        padding=(14, 11),
        borderwidth=0,
    )

    estilo.map(
        "Executar.TButton",
        background=[
            ("disabled", "#A6B9B0"),
            ("pressed", VERDE_ESCURO),
            ("active", VERDE_ESCURO),
        ],
        foreground=[
            ("disabled", "#F3F6F8"),
            ("!disabled", "#FFFFFF"),
        ],
    )

    estilo.configure(
        "Gerar.TButton",
        background=VERDE_CLARO,
        foreground=VERDE_ESCURO,
        bordercolor="#B9D9C8",
        padding=(12, 9),
    )

    estilo.map(
        "Gerar.TButton",
        background=[
            ("pressed", "#C7E6D6"),
            ("active", "#D5EEE1"),
        ],
    )

    estilo.configure(
        "Secundario.TButton",
        background=PAINEL,
        foreground=TEXTO,
        bordercolor=BORDA,
        padding=(12, 9),
    )

    estilo.map(
        "Secundario.TButton",
        background=[
            ("pressed", "#E5EBF0"),
            ("active", "#F1F4F7"),
        ],
    )

    estilo.configure(
        "TNotebook",
        background=FUNDO,
        borderwidth=0,
    )

    estilo.configure(
        "TNotebook.Tab",
        background="#E9EEF2",
        foreground=TEXTO,
        font=(FONTE, 10),
        padding=(18, 11),
    )

    estilo.map(
        "TNotebook.Tab",
        background=[
            ("selected", VERDE_PRINCIPAL),
            ("active", VERDE_CLARO),
        ],
        foreground=[
            ("selected", "#FFFFFF"),
            ("!selected", TEXTO),
        ],
    )

    estilo.configure(
        "TCombobox",
        padding=(7, 6),
    )

    estilo.configure(
        "TEntry",
        padding=(7, 6),
    )

    estilo.configure(
        "Horizontal.TProgressbar",
        background=VERDE_PRINCIPAL,
        troughcolor=BORDA,
        borderwidth=0,
        thickness=7,
    )

    estilo.configure(
        "Treeview",
        font=(FONTE, 9),
        rowheight=27,
        background=PAINEL,
        fieldbackground=PAINEL,
        foreground=TEXTO,
    )

    estilo.configure(
        "Treeview.Heading",
        font=(FONTE, 9, "bold"),
        background="#E9EEF2",
        foreground=TEXTO,
        padding=(6, 7),
    )

    estilo.map(
        "Treeview",
        background=[("selected", VERDE_CLARO)],
        foreground=[("selected", VERDE_ESCURO)],
    )