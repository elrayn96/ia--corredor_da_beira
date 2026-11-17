"""Verifica a exportação vectorial e raster da árvore."""
from xml.etree import ElementTree

import pytest

from src.interface.arvore_busca import ModeloArvore, exportar_arvore


def _evento(tipo, numero, pai=None):
    return {"tipo": tipo, "passo": numero, "no_id": numero,
            "pai_id": pai, "estado": {"localidade": f"Local{numero}"},
            "accao": None, "profundidade": 0, "g": 0,
            "h": None, "f": None}


def test_exportar_svg_com_todos_os_filhos(tmp_path):
    modelo = ModeloArvore([
        _evento("inicio", 0), _evento("expandir", 0),
        _evento("gerar", 1, 0), _evento("gerar", 2, 0),
    ])
    destino = tmp_path / "arvore.svg"
    exportar_arvore(modelo, 3, destino)
    assert destino.stat().st_size > 1000
    root = ElementTree.parse(destino).getroot()
    assert root.tag.endswith("svg")
    xml = destino.read_text(encoding="utf-8")
    assert "Local0" in xml and "Local1" in xml and "Local2" in xml


def test_exportar_png_300_dpi(tmp_path):
    modelo = ModeloArvore([_evento("inicio", 0)])
    destino = tmp_path / "arvore.png"
    exportar_arvore(modelo, 0, destino)
    assert destino.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_exportar_rejeita_arvore_vazia(tmp_path):
    with pytest.raises(ValueError, match="Não há uma árvore"):
        exportar_arvore(None, 0, tmp_path / "arvore.svg")
