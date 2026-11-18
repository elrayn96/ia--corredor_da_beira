"""Contrato genérico comum exigido para os algoritmos de procura.

O projecto histórico usa alguns nomes ``get_*``. Os adaptadores no fim deste
módulo preservam essa API enquanto tornam explícito o contrato académico.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class No:
    """Nó partilhado pelas estratégias de procura."""

    estado: Any
    pai: No | None
    accao: Any
    g: float
    no_id: int = 0
    profundidade: int = field(init=False)

    def __post_init__(self):
        self.profundidade = 0 if self.pai is None else self.pai.profundidade + 1


def caminho(no: No) -> list[No]:
    """Reconstrói, da raiz ao objectivo, os nós que terminam em ``no``."""
    nos = []
    actual = no
    while actual is not None:
        nos.append(actual)
        actual = actual.pai
    nos.reverse()
    return nos


class Problema(ABC):
    """Interface abstracta independente do domínio."""

    @abstractmethod
    def estado_inicial(self):
        raise NotImplementedError

    @abstractmethod
    def accoes(self, estado):
        raise NotImplementedError

    @abstractmethod
    def resultado(self, estado, accao):
        raise NotImplementedError

    @abstractmethod
    def custo(self, estado, accao, estado_seguinte):
        raise NotImplementedError

    @abstractmethod
    def e_objectivo(self, estado):
        raise NotImplementedError

    @abstractmethod
    def heuristica(self, estado, nome):
        raise NotImplementedError

    def sucessores(self, estado):
        """Implementação comum da relação sucessora a partir do contrato."""
        for accao in self.accoes(estado):
            seguinte = self.resultado(estado, accao)
            yield accao, seguinte, self.custo(estado, accao, seguinte)


def estado_inicial(problema):
    """Aceita o contrato novo e os pequenos problemas legados dos testes."""
    metodo = getattr(problema, "estado_inicial", None)
    return metodo() if metodo is not None else problema.get_estado_inicial()


def sucessores(problema, estado):
    metodo = getattr(problema, "sucessores", None)
    if metodo is not None:
        return metodo(estado)
    legado = getattr(problema, "get_sucessores", None)
    if legado is not None:
        return legado(estado)
    return (
        (accao, seguinte, problema.custo(estado, accao, seguinte))
        for accao in problema.accoes(estado)
        for seguinte in (problema.resultado(estado, accao),)
    )


def e_objectivo(problema, estado):
    metodo = getattr(problema, "e_objectivo", None)
    return metodo(estado) if metodo is not None else problema.teste_objectivo(estado)
