"""Estilos visuais centralizados da aplicação."""
from tkinter import ttk

VERDE_PRINCIPAL = '#086B47'
VERDE_ESCURO = '#064D38'
VERDE_CLARO = '#E6F4ED'
FUNDO = '#F3F6F8'
PAINEL = '#FFFFFF'
TEXTO = '#17212B'
TEXTO_SECUNDARIO = '#64748B'
BORDA = '#D9E2E8'
AZUL_ESCURO = VERDE_ESCURO
AZUL = VERDE_PRINCIPAL
SUCESSO = VERDE_PRINCIPAL
CORES_ARVORE = {'fronteira':'#cfe8ff','expandido':'#ffe08a','descartado':'#d9d9d9','objectivo':'#8fd19e','solucao':'#4caf50'}


def configurar_estilos(raiz):
    estilo = ttk.Style(raiz)
    if 'clam' in estilo.theme_names():
        estilo.theme_use('clam')
    estilo.configure('TFrame', background=FUNDO)
    estilo.configure('Cartao.TFrame', background=PAINEL)
    estilo.configure('TLabel', background=FUNDO, foreground=TEXTO, font=('Segoe UI',10))
    estilo.configure('Cartao.TLabel', background=PAINEL, foreground=TEXTO, font=('Segoe UI',10))
    estilo.configure('Titulo.TLabel', background=FUNDO, foreground=TEXTO, font=('Segoe UI',14,'bold'))
    estilo.configure('Cabecalho.TLabel', background=VERDE_ESCURO, foreground='white', font=('Segoe UI',17,'bold'), padding=(12,14))
    estilo.configure('Estado.TLabel', background=VERDE_ESCURO, foreground='white', font=('Segoe UI',10), padding=(12,8))
    estilo.configure('TButton', font=('Segoe UI',10), padding=(12,8))
    estilo.configure('Executar.TButton', background=VERDE_PRINCIPAL, foreground='white', font=('Segoe UI',10,'bold'), padding=(12,11), borderwidth=0)
    estilo.map('Executar.TButton', background=[('disabled','#A6B9B0'),('pressed',VERDE_ESCURO),('active',VERDE_ESCURO)], foreground=[('disabled','#F3F6F8'),('!disabled','white')])
    estilo.configure('Gerar.TButton', background=VERDE_CLARO, foreground=VERDE_ESCURO, bordercolor='#B9D9C8', padding=(12,9))
    estilo.map('Gerar.TButton', background=[('active','#D5EEE1'),('pressed','#C7E6D6')])
    estilo.configure('Secundario.TButton', background=PAINEL, foreground=TEXTO, bordercolor=BORDA, padding=(12,9))
    estilo.map('Secundario.TButton', background=[('active','#F1F4F7'),('pressed','#E5EBF0')])
    estilo.configure('TNotebook', background=FUNDO, borderwidth=0)
    estilo.configure('TNotebook.Tab', background='#E9EEF2', foreground=TEXTO, font=('Segoe UI',10), padding=(17,11), borderwidth=1)
    estilo.map('TNotebook.Tab', background=[('selected',VERDE_PRINCIPAL),('active',VERDE_CLARO)], foreground=[('selected','white'),('!selected',TEXTO)])
    estilo.configure('Vertical.TScrollbar', troughcolor='#EDF3F5',
                    background='#BACBC8', arrowcolor='#086B47',
                    borderwidth=0, width=12)
    estilo.map('Vertical.TScrollbar', background=[('active', '#86ACA0'),
                ('pressed', '#609D89')])
    estilo.configure('Horizontal.TScrollbar', troughcolor='#EDF3F5',
                    background='#BACBC8', borderwidth=0)
    estilo.configure('TCombobox', padding=(6,6))
    estilo.configure('TEntry', padding=(6,6))
    estilo.configure('Horizontal.TProgressbar', background=VERDE_PRINCIPAL, troughcolor=BORDA, borderwidth=0, thickness=7)
    estilo.configure('Treeview', background=PAINEL, fieldbackground=PAINEL, foreground=TEXTO, font=('Segoe UI',9), rowheight=27, borderwidth=0)
    estilo.configure('Treeview.Heading', background='#E9EEF2', foreground=TEXTO, font=('Segoe UI',9,'bold'), padding=(5,7))
    estilo.map('Treeview', background=[('selected',VERDE_CLARO)], foreground=[('selected',VERDE_ESCURO)])
    estilo.configure('Cartao.TLabelframe', background=PAINEL, bordercolor=BORDA, relief='solid', borderwidth=1)
    estilo.configure('Cartao.TLabelframe.Label', background=PAINEL, foreground=TEXTO, font=('Segoe UI',10,'bold'))

    # Cartão de selecção destacado e estilos de formulários.
    estilo.configure('Instancia.TFrame', background='#E6F4ED', borderwidth=1,
                    relief='solid')
    estilo.configure('InstanciaTitulo.TLabel', background='#E6F4ED',
                    foreground='#086B47', font=('Segoe UI', 9, 'bold'))
    estilo.configure('InstanciaNome.TLabel', background='#E6F4ED',
                    foreground='#17212B', font=('Segoe UI', 10, 'bold'))
    estilo.configure('InstanciaDetalhe.TLabel', background='#E6F4ED',
                    foreground='#486C5D', font=('Segoe UI', 9))
    estilo.configure('Secao.TLabel', background='#FFFFFF', foreground='#064D38',
                    font=('Segoe UI', 13, 'bold'))
    estilo.configure('Ajuda.TLabel', background='#FFFFFF', foreground='#64748B',
                    font=('Segoe UI', 9))
    estilo.configure('Moderno.TCombobox', padding=(9, 8), font=('Segoe UI', 10),
                    fieldbackground='#FFFFFF', foreground='#17212B')
    estilo.map('Moderno.TCombobox', fieldbackground=[('readonly', '#FFFFFF'),
                ('disabled', '#EDF1F4')], foreground=[('disabled', '#8F9BA7')])
    estilo.configure('Moderno.TEntry', padding=(9, 8), fieldbackground='#FFFFFF',
                    font=('Segoe UI', 10))
    estilo.configure('Cancelar.TButton', background='#B84135', foreground='#FFFFFF',
                    font=('Segoe UI', 10, 'bold'), padding=(12, 11), borderwidth=0)
    estilo.map('Cancelar.TButton', background=[('active', '#92332D'),
               ('pressed', '#762722'), ('disabled', '#B8C5C0')])

    # Fundos de botões verdadeiramente arredondados. As imagens são locais;
    # o elemento ttk preserva os cantos ao esticar apenas a área central.
    import tkinter as tk
    from pathlib import Path

    pasta = Path(__file__).resolve().parents[2] / 'docs' / 'figuras' / 'icones'
    imagens = getattr(raiz, '_imagens_botoes_tema', [])
    for estilo_nome, prefixo, texto in (
        ('Executar.TButton', 'principal', '#FFFFFF'),
        ('Gerar.TButton', 'gerar', '#064D38'),
        ('Secundario.TButton', 'secundario', '#17212B'),
        ('Cancelar.TButton', 'cancelar', '#FFFFFF'),
    ):
        normal, hover, desactivado = (
            tk.PhotoImage(master=raiz, file=str(pasta / f'botao_{nome}.png'))
            for nome in (prefixo, prefixo + '_hover', prefixo + '_disabled')
        )
        imagens.extend((normal, hover, desactivado))
        elemento = f'Fundo.{prefixo}'
        if elemento not in estilo.element_names():
            estilo.element_create(
                elemento, 'image', normal,
                ('disabled', desactivado), ('pressed', hover), ('active', hover),
                border=12, sticky='nsew',
            )
        estilo.layout(estilo_nome, [
            (elemento, {'sticky': 'nsew', 'children': [
                ('Button.padding', {'sticky': 'nsew', 'children': [
                    ('Button.label', {'sticky': 'nsew'})
                ]})
            ]})
        ])
        estilo.configure(estilo_nome, foreground=texto, borderwidth=0)
    raiz._imagens_botoes_tema = imagens
