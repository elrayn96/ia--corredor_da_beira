"""Ícones PNG desenhados a partir de vectores SVG locais, sem emojis."""
import tkinter as tk
from pathlib import Path

ICONS_DIR = Path(__file__).resolve().parents[2] / 'docs' / 'figuras' / 'icones'

def carregar_icone(widget, nome, tamanho=20):
    """Carrega ícone próprio; mantém a imagem associada ao widget."""
    caminho = ICONS_DIR / f'{nome}.png'
    imagem = tk.PhotoImage(master=widget, file=str(caminho))
    if tamanho != 24:
        # São ícones vectoriais rasterizados a 24 px; Tk preserva a dimensão.
        pass
    return imagem
