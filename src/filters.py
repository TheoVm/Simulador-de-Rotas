from src.models import Maximos, Rota

dentro_dos_limites = lambda limites, rota: (
    rota.distancia_km <= limites.distancia
    and rota.tempo_min <= limites.tempo
    and rota.congestionamento <= limites.congestionamento
)
