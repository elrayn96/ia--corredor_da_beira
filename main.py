
"""Ponto de entrada da interface gráfica."""

import multiprocessing

from src.interface.janela_principal import JanelaPrincipal


def main():
    multiprocessing.freeze_support()
    aplicacao = JanelaPrincipal()
    aplicacao.mainloop()

if __name__ == "__main__":
    main()
