"""Cálculos teóricos usados na análise experimental."""

from __future__ import annotations


def factor_ramificacao_efectivo(nos_expandidos, profundidade, tolerancia=1e-10):
    """Resolve N + 1 = 1 + b + ... + b**d por bissecção."""
    if profundidade <= 0 or nos_expandidos <= 0:
        return 0.0
    alvo = nos_expandidos + 1

    def soma(b):
        if abs(b - 1.0) < 1e-12:
            return profundidade + 1
        return (b ** (profundidade + 1) - 1) / (b - 1)

    inferior, superior = 0.0, max(2.0, alvo ** (1 / profundidade) + 1)
    while soma(superior) < alvo:
        superior *= 2
    for _ in range(200):
        meio = (inferior + superior) / 2
        if soma(meio) < alvo:
            inferior = meio
        else:
            superior = meio
        if superior - inferior <= tolerancia:
            break
    return (inferior + superior) / 2


def exemplo_distancia_vs_tempo():
    """Contra-exemplo concreto da rede: menos km não significa menos tempo."""
    return {
        "origem": "Beira",
        "destino": "Catandica",
        "menor_distancia": {
            "percurso": "Beira-Dondo-Nhamatanda-Inchope-Chimoio-Catandica",
            "quilometros": 460,
            "minutos": 398,
        },
        "menor_tempo": {
            "percurso": "Beira-Dondo-Nhamatanda-Gorongosa-Muxunguè-Catandica",
            "quilometros": 480,
            "minutos": 386,
        },
    }
