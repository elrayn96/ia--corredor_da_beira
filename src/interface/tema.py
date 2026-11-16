FUNDO = "#f4f7fb"
PAINEL = "#ffffff"
AZUL_ESCURO = "#14283f"
AZUL = "#2563a6"
TEXTO = "#203047"
SUCESSO = "#2e7d5b"
CORES_ARVORE = {"fronteira": "#cfe8ff", "expandido": "#ffe08a",
                "descartado": "#d9d9d9", "objectivo": "#8fd19e",
                "solucao": "#4caf50"}

def configurar_estilos(raiz):
    from tkinter import ttk
    estilo = ttk.Style(raiz)
    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")
    estilo.configure("TFrame", background=FUNDO)
    estilo.configure("TLabel", background=FUNDO, foreground=TEXTO)
    estilo.configure("Cabecalho.TLabel", background=AZUL_ESCURO,
                     foreground="white", font=("Arial", 17, "bold"))
    estilo.configure("Titulo.TLabel", font=("Arial", 11, "bold"))
    estilo.configure("TButton", padding=(10, 6))
