from src.models import Maximos, Rota


def dentro_dos_limites(limites: Maximos, rota: Rota) -> bool:
    return (rota.distancia_km <= limites.distancia
            and rota.tempo_min <= limites.tempo
            and rota.congestionamento <= limites.congestionamento)
