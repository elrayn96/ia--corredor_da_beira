from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Estado:
    """Situação imutável e hashable do camião."""

    localidade: str
    entregas_concluidas: frozenset
    tempo: int
    combustivel: int

    def __init__(self, localidade, entregas_concluidas=None, tempo=0, combustivel=300000):
        if tempo < 0 or combustivel < 0:
            raise ValueError('Tempo e combustivel nao podem ser negativos')
        object.__setattr__(self, "localidade", localidade)
        object.__setattr__(self, "entregas_concluidas", frozenset(entregas_concluidas or ()))
        object.__setattr__(self, "tempo", int(tempo))
        object.__setattr__(self, "combustivel", int(combustivel))

    def get_localidade(self):
        return self.localidade

    def get_entregas_concluidas(self):
        return set(self.entregas_concluidas)

    def get_tempo(self):
        return self.tempo

    def get_combustivel(self):
        return self.combustivel

    def __repr__(self):
        return (f'Estado(localidade={self.localidade!r}, entregas={sorted(self.entregas_concluidas)!r}, '
                f'tempo={self.tempo}, combustivel={self.combustivel})')
