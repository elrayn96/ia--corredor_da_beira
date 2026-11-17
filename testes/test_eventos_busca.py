"""Testes dos eventos de busca (sequência, identificadores e compatibilidade).

Usam um grafo pequeno, sem depender do código dos colegas nem de janelas.
Correr na raiz do projecto:  python -m pytest testes/test_eventos_busca.py -v
"""

import pytest

from src.buscas.eventos_busca import CHAVES_EVENTO, emitir_evento
from src.buscas.informadas import a_star, a_star_ponderada, busca_gulosa


class ProblemaGrafo:
    """Problema de teste com a mesma interface que o Problema real."""

    def __init__(self, arestas, inicio, objectivo):
        self.arestas = arestas
        self.inicio = inicio
        self.objectivo = objectivo

    def get_estado_inicial(self):
        return self.inicio

    def get_sucessores(self, estado):
        return [
            (f"{estado}->{v}", v, c) for v, c in self.arestas.get(estado, [])
        ]

    def teste_objectivo(self, estado):
        return estado == self.objectivo


# S->A (1), A->G (10) custa 11; S->B (4), B->G (3) custa 7 (óptimo).
# G é descoberto duas vezes: primeiro por A (custo 11), depois por B (custo 7).
ARESTAS = {"S": [("A", 1), ("B", 4)], "A": [("G", 10)], "B": [("G", 3)]}
H_TABELA = {"S": 7, "A": 1, "B": 3, "G": 0}

BUSCAS = [
    pytest.param(busca_gulosa, (), id="gulosa"),
    pytest.param(a_star, (), id="a_star"),
    pytest.param(a_star_ponderada, (2,), id="ponderada"),
]


def h_admissivel(estado, problema):
    return H_TABELA[estado]


@pytest.fixture
def problema():
    return ProblemaGrafo(ARESTAS, "S", "G")


def correr(busca, problema, extra=()):
    """Corre a busca e devolve (solução, lista de eventos)."""
    eventos = []
    solucao = busca(problema, h_admissivel, *extra, observador=eventos.append)
    return solucao, eventos


def tipos(eventos):
    return [evento["tipo"] for evento in eventos]


# --- emitir_evento -------------------------------------------------------

def test_emitir_evento_sem_observador_nao_faz_nada():
    assert emitir_evento(None, {}) is None


def test_emitir_evento_rejeita_tipo_invalido():
    evento = dict.fromkeys(CHAVES_EVENTO)
    evento["tipo"] = "voar"
    with pytest.raises(ValueError, match="Tipo de evento inválido"):
        emitir_evento(lambda e: None, evento)


def test_emitir_evento_rejeita_chaves_em_falta():
    with pytest.raises(ValueError, match="Evento sem as chaves"):
        emitir_evento(lambda e: None, {"tipo": "inicio"})


# --- formato e sequência -------------------------------------------------

@pytest.mark.parametrize(("busca", "extra"), BUSCAS)
def test_todos_os_eventos_tem_as_chaves_do_contrato(problema, busca, extra):
    _, eventos = correr(busca, problema, extra)
    assert eventos
    for evento in eventos:
        assert set(CHAVES_EVENTO) <= set(evento)


@pytest.mark.parametrize(("busca", "extra"), BUSCAS)
def test_passos_sao_sequenciais_a_partir_de_zero(problema, busca, extra):
    _, eventos = correr(busca, problema, extra)
    assert [e["passo"] for e in eventos] == list(range(len(eventos)))


@pytest.mark.parametrize(("busca", "extra"), BUSCAS)
def test_comeca_em_inicio_e_acaba_em_objectivo(problema, busca, extra):
    _, eventos = correr(busca, problema, extra)
    assert tipos(eventos)[0] == "inicio"
    assert tipos(eventos)[-1] == "objectivo"
    assert eventos[0]["no_id"] == 0
    assert eventos[0]["pai_id"] is None
    assert eventos[0]["accao"] is None
    assert eventos[0]["profundidade"] == 0


def test_ordem_real_das_expansoes_no_a_star(problema):
    _, eventos = correr(a_star, problema)
    expandidos = [e["estado"] for e in eventos if e["tipo"] == "expandir"]
    assert expandidos == ["S", "A", "B"]


def test_objectivo_aparece_so_quando_sai_da_fronteira(problema):
    solucao, eventos = correr(a_star, problema)
    objectivo = eventos[-1]
    assert objectivo["g"] == solucao.custo_total == 7
    assert objectivo["profundidade"] == 2


def test_sem_solucao_nao_emite_objectivo():
    problema = ProblemaGrafo({"S": [("A", 1)], "A": []}, "S", "G")
    solucao, eventos = correr(a_star, problema)
    assert solucao is None
    assert "objectivo" not in tipos(eventos)
    assert tipos(eventos)[0] == "inicio"


# --- identificadores -----------------------------------------------------

@pytest.mark.parametrize(("busca", "extra"), BUSCAS)
def test_no_id_unico_nos_nos_criados(problema, busca, extra):
    _, eventos = correr(busca, problema, extra)
    ids = [e["no_id"] for e in eventos if e["tipo"] in ("inicio", "gerar", "reabrir")]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize(("busca", "extra"), BUSCAS)
def test_pai_id_refere_um_no_ja_criado(problema, busca, extra):
    _, eventos = correr(busca, problema, extra)
    criados = set()
    for evento in eventos:
        if evento["tipo"] in ("inicio", "gerar", "reabrir"):
            if evento["pai_id"] is not None:
                assert evento["pai_id"] in criados
            criados.add(evento["no_id"])


def test_mesmo_estado_pode_ter_dois_no_id(problema):
    _, eventos = correr(a_star, problema)
    ids_de_g = {e["no_id"] for e in eventos if e["estado"] == "G"}
    assert len(ids_de_g) == 2


def test_a_star_reabre_estado_com_custo_melhor(problema):
    _, eventos = correr(a_star, problema)
    reabertos = [e for e in eventos if e["tipo"] == "reabrir"]
    assert len(reabertos) == 1
    assert reabertos[0]["estado"] == "G"
    assert reabertos[0]["g"] == 7


def test_gulosa_nunca_reabre(problema):
    _, eventos = correr(busca_gulosa, problema)
    assert "reabrir" not in tipos(eventos)


# --- valores g, h, f -----------------------------------------------------

def test_f_e_g_mais_h_no_a_star(problema):
    _, eventos = correr(a_star, problema)
    assert all(e["f"] == e["g"] + e["h"] for e in eventos)


def test_f_e_g_mais_peso_vezes_h_na_ponderada(problema):
    _, eventos = correr(a_star_ponderada, problema, (2,))
    assert all(e["f"] == e["g"] + 2 * e["h"] for e in eventos)


def test_f_e_h_na_gulosa(problema):
    _, eventos = correr(busca_gulosa, problema)
    assert all(e["f"] == e["h"] for e in eventos)


# --- compatibilidade -----------------------------------------------------

@pytest.mark.parametrize(("busca", "extra"), BUSCAS)
def test_resultado_igual_com_e_sem_observador(problema, busca, extra):
    est_sem, est_com = {}, {}
    sem = busca(problema, h_admissivel, *extra, estatisticas=est_sem)
    com = busca(
        problema,
        h_admissivel,
        *extra,
        estatisticas=est_com,
        observador=lambda evento: None,
    )
    assert sem.custo_total == com.custo_total
    assert sem.estados == com.estados
    for chave in ("nos_gerados", "nos_expandidos", "max_fronteira"):
        assert est_sem[chave] == est_com[chave]