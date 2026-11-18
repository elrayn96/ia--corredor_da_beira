import csv
import textwrap

from experiencias.bateria import (
    LIMITE_MEMORIA_BYTES,
    _carregar_checkpoint,
    _executar_caso,
    _guardar_checkpoint,
)
from experiencias.executar import executar_experiencia
from experiencias.graficos import _rotulo, gerar_graficos
from experiencias.resultados import CABECALHOS, guardar_resultados_csv
from src.interface.painel_comparacao import preparar_comparacao


def test_executar_experiencia_preserva_configuracao(monkeypatch):
    class SolucaoFalsa:
        @staticmethod
        def get_custo_total():
            return 42

        @staticmethod
        def get_accoes():
            return []

    monkeypatch.setattr(
        "experiencias.executar.executar_busca",
        lambda configuracao, **_limites: {
            "solucao": SolucaoFalsa(),
            "estatisticas": {
                "nos_gerados": 10,
                "nos_expandidos": 5,
                "max_fronteira": 3,
                "tempo_segundos": 0.1,
                "memoria_pico_bytes": 2048,
            },
            "eventos": [],
            "estado_execucao": "concluida",
            "mensagem": "ok",
        },
    )
    config = {
        "caminho_instancia": "instancia.json",
        "semente": 202601,
        "algoritmo": "a_star",
        "heuristica": "h2",
        "peso": None,
        "limite": None,
    }
    resultado = executar_experiencia(config)
    assert resultado["algoritmo"] == "a_star"
    assert resultado["heuristica"] == "h2"
    assert resultado["semente"] == 202601
    assert resultado["custo_total"] == 42
    assert resultado["comprimento_caminho"] == 0


def test_guardar_resultados_csv(tmp_path):
    caminho = tmp_path / "subpasta" / "resultados.csv"
    guardar_resultados_csv(
        [
            {
                "algoritmo": "a_star",
                "heuristica": "h2",
                "estado_execucao": "concluida",
                "custo_total": 42,
                "nos_expandidos": 5,
            }
        ],
        caminho,
    )
    with caminho.open(encoding="utf-8-sig", newline="") as ficheiro:
        leitor = csv.DictReader(ficheiro)
        linhas = list(leitor)
    assert tuple(leitor.fieldnames) == CABECALHOS
    assert linhas[0]["algoritmo"] == "a_star"
    assert linhas[0]["custo_total"] == "42"


def test_preparar_comparacao_distingue_erro_e_sem_solucao():
    linhas = preparar_comparacao(
        [
            {
                "algoritmo": "a_star",
                "heuristica": "h2",
                "estado_execucao": "erro",
                "mensagem": "falhou",
            },
            {
                "algoritmo": "bfs",
                "estado_execucao": "sem_solucao",
                "estatisticas": {"nos_expandidos": 12},
            },
        ]
    )
    assert linhas[0]["estado_execucao"] == "erro"
    assert linhas[0]["custo_total"] is None
    assert linhas[1]["heuristica"] == "—"
    assert linhas[1]["nos_expandidos"] == 12


def test_checkpoint_da_bateria_e_atomico_e_compativel(tmp_path):
    caminho = tmp_path / ".bateria_parcial.json"
    resultados = [{"nivel": "pequena", "indice": 1, "algoritmo": "bfs"}]
    _guardar_checkpoint(caminho, "abc123", 60, resultados)

    assert _carregar_checkpoint(caminho, "abc123", 60) == resultados
    assert _carregar_checkpoint(caminho, "outra", 60) == []
    assert _carregar_checkpoint(caminho, "abc123", 30) == []
    assert not caminho.with_suffix(".json.tmp").exists()


def test_bateria_define_limite_de_memoria_de_dois_gib():
    assert LIMITE_MEMORIA_BYTES == 2 * 1024**3


def test_bateria_nao_inicia_sem_limite(monkeypatch):
    def recusar(_limite):
        raise OSError("Limite indisponível")

    monkeypatch.setattr("experiencias.bateria.aplicar_limite", recusar)
    resposta = _executar_caso({"algoritmo": "bfs"}, 60, 100)
    assert resposta["estado_execucao"] == "erro"
    assert "Limite indisponível" in resposta["mensagem"]


def test_alocacao_e_recusada_no_processo_filho():
    import subprocess
    import sys
    from pathlib import Path

    codigo = textwrap.dedent("""
        from src.servicos.limite_memoria import aplicar_limite

        aplicar_limite(256 * 1024**2)

        try:
            bytearray(320 * 1024**2)
        except MemoryError:
            print('alocação recusada')
        else:
            raise AssertionError('O sistema permitiu exceder o limite')
    """)

    subprocess.run(
        [sys.executable, "-c", codigo],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        timeout=30,
    )


def test_graficos_usam_rotulos_legiveis_e_criam_as_tres_figuras(tmp_path):
    assert _rotulo(("a_star_ponderada", "h2", "1.25")) == "A* pond. h2 (w=1,25)"
    caminho = tmp_path / "resultados.csv"
    guardar_resultados_csv(
        [
            {
                "algoritmo": "a_star",
                "heuristica": "h2",
                "estado_execucao": "concluida",
                "custo_total": 10,
                "custo_optimo": 10,
                "razao_custo_optimo": 1,
                "nos_expandidos": 20,
                "tempo_segundos": 0.1,
                "nivel": nivel,
                "dimensao": dimensao,
            }
            for nivel, dimensao in zip(("pequena", "media", "grande"), (4, 16, 25))
        ],
        caminho,
    )

    criados = gerar_graficos(caminho, tmp_path / "graficos")

    assert [item.name for item in criados] == [
        "nos_expandidos_vs_dimensao.png",
        "tempo_vs_dimensao.png",
        "custo_vs_optimo.png",
    ]
    assert all(item.stat().st_size > 10_000 for item in criados)
