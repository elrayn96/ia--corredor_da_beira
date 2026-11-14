"""Testes sem janelas; demonstração: python -m testes.test_mapa_rodoviario."""

import pytest

from src.accao import Accao
from src.estado import Estado
from src.gerador import carregar_rede, gerar_instancia
from src.interface.mapa_rodoviario import preparar_posicoes, segmentos_percurso
from src.interface.painel_configuracao import ALGORITMOS, validar_configuracao


def test_percurso_preserva_ordem_e_ignora_operacoes_locais():
    estados = [Estado(n) for n in ("Beira", "Dondo", "Dondo", "Beira")]
    accoes = [Accao("deslocar"), Accao("entregar"), Accao("deslocar")]
    assert segmentos_percurso(estados, accoes) == [
        ("Beira", "Dondo"),
        ("Dondo", "Beira"),
    ]


def test_percurso_vazio_e_incoerente():
    assert segmentos_percurso([], []) == []
    with pytest.raises(ValueError):
        segmentos_percurso([Estado("Beira")], [Accao("deslocar")])


def test_posicoes_rede_real_estaveis():
    localidades = carregar_rede()["localidades"]
    posicoes = preparar_posicoes(localidades)
    assert set(posicoes) == {l["nome"] for l in localidades}
    assert posicoes == preparar_posicoes(list(reversed(localidades)))
    assert preparar_posicoes([{"nome": "Teste", "x": 10, "y": 20}]) == {
        "Teste": (10, 20)
    }


@pytest.mark.parametrize("algoritmo", ALGORITMOS.values())
def test_contrato_configuracao(tmp_path, algoritmo):
    caminho = tmp_path / "instancia.json"
    caminho.write_text("{}", encoding="utf-8")
    config = validar_configuracao(caminho, algoritmo, "h1", "1,5", "0")
    assert set(config) == {
        "caminho_instancia",
        "algoritmo",
        "heuristica",
        "peso",
        "limite",
    }
    assert config["peso"] == (1.5 if algoritmo == "a_star_ponderada" else None)
    assert config["limite"] == (0 if algoritmo in ("lds", "ids") else None)


@pytest.mark.parametrize("peso", ["0", "-1", "nan", "inf", "texto"])
def test_peso_invalido(tmp_path, peso):
    caminho = tmp_path / "instancia.json"
    caminho.touch()
    with pytest.raises(ValueError):
        validar_configuracao(caminho, "a_star_ponderada", "h1", peso, "0")


@pytest.mark.parametrize("limite", ["-1", "1.5", "texto"])
def test_limite_invalido(tmp_path, limite):
    caminho = tmp_path / "instancia.json"
    caminho.touch()
    with pytest.raises(ValueError):
        validar_configuracao(caminho, "ids", None, "", limite)


def demonstrar():
    """Janela manual isolada; não executa algoritmos nem grava instâncias."""
    import tkinter as tk
    from tkinter import messagebox, ttk

    from src.interface.mapa_rodoviario import MapaRodoviario
    from src.interface.painel_configuracao import PainelConfiguracao

    raiz = tk.Tk()
    raiz.title("Adila · Configuração e mapa rodoviário")
    raiz.geometry("1500x900")
    mapa = MapaRodoviario(raiz)
    painel = PainelConfiguracao(raiz, ao_alterar_instancia=mapa.mostrar_instancia)
    painel.pack(side="left", fill="y")
    mapa.pack(side="right", fill="both", expand=True)
    mapa.mostrar_rede(carregar_rede())
    mapa.mostrar_instancia(gerar_instancia())
    barra = ttk.Frame(painel)
    barra.grid(row=9, column=0, columnspan=2, pady=12)

    def validar():
        try:
            messagebox.showinfo(
                "Configuração", str(painel.obter_configuracao()), parent=raiz
            )
        except ValueError as erro:
            messagebox.showerror("Configuração inválida", str(erro), parent=raiz)

    ttk.Button(barra, text="Ver configuração", command=validar).pack(fill="x")
    ttk.Button(
        barra,
        text="Destacar percurso de exemplo",
        command=lambda: mapa.destacar_percurso(
            [Estado(n) for n in ("Beira", "Dondo", "Nhamatanda", "Dondo", "Beira")],
            [Accao("deslocar") for _ in range(4)],
        ),
    ).pack(fill="x", pady=4)
    ttk.Button(barra, text="Limpar percurso", command=mapa.limpar_percurso).pack(
        fill="x"
    )
    raiz.mainloop()


if __name__ == "__main__":
    demonstrar()
