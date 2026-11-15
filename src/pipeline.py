"""Do conjunto de rotas ao ranking: map (tempo) -> filter -> map (nota) -> sorted."""
from src.filters import filtrar_rotas
from src.objectives import PESOS
from src.scoring import com_tempo, pontuar_todas

CASAS_DECIMAIS = 3  # arredondamento da nota, para que empates possam acontecer


def chave_ranking(rp) -> tuple:
    """Nota arredondada; empate: menor tempo, menor trânsito, menor distância."""
    return (
        round(rp.pontuacao, CASAS_DECIMAIS),
        rp.rota.tempo_min,
        rp.rota.congestionamento,
        rp.rota.distancia_km,
        rp.rota.nome,
    )


def avaliar(rotas, limites, pesos=PESOS) -> tuple:
    validas = filtrar_rotas(limites, map(com_tempo, rotas))
    return tuple(sorted(pontuar_todas(pesos, validas), key=chave_ranking))