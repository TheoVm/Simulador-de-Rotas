"""Descartar rotas inadequadas (filter + função pura)."""
from functools import partial

from src.models import Limites, Rota


def rota_valida(limites: Limites, rota: Rota) -> bool:
    """Pura: True se a rota respeita os dois limites."""
    return (
        rota.tempo_min <= limites.tempo_max
        and rota.congestionamento <= limites.congestionamento_max
    )


def filtrar_rotas(limites: Limites, rotas) -> tuple:
    """filter com os limites já fixados (partial)."""
    return tuple(filter(partial(rota_valida, limites), rotas))