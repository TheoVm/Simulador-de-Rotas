from dataclasses import replace
from functools import partial, reduce
from operator import mul

from src.models import Maximos, Pesos, Rota, RotaPontuada

calcular_tempo_min = lambda distancia_km, velocidade_kmh: distancia_km / velocidade_kmh * 60

com_tempo = lambda rota: replace(
    rota,
    tempo_min=calcular_tempo_min(rota.distancia_km, rota.velocidade_media_kmh),
)

compor = lambda *funcoes: lambda valor: reduce(lambda acc, f: f(acc), funcoes, valor)

normalizar = lambda maximo, valor: 0.0 if maximo == 0 else valor / maximo

calcular_maximos = lambda rotas: reduce(
    lambda acc, r: Maximos(
        distancia=max(acc.distancia, r.distancia_km),
        tempo=max(acc.tempo, r.tempo_min),
        congestionamento=max(acc.congestionamento, r.congestionamento),
    ),
    rotas,
    Maximos(0.0, 0.0, 0.0),
)

normalizar_rota = lambda maximos, rota: (
    normalizar(maximos.distancia, rota.distancia_km),
    normalizar(maximos.tempo, rota.tempo_min),
    normalizar(maximos.congestionamento, rota.congestionamento),
)

ponderar = lambda pesos, valores: tuple(
    map(mul, valores, (pesos.distancia, pesos.tempo, pesos.congestionamento))
)

pontuar = lambda pesos, maximos, rota: compor(
    partial(normalizar_rota, maximos),
    partial(ponderar, pesos),
    sum,
)(rota)

pontuar_rota = lambda pesos, maximos, rota: RotaPontuada(
    rota=rota, pontuacao=pontuar(pesos, maximos, rota)
)

avaliar_notas = lambda pesos, rotas: (
    lambda com_tempos: tuple(
        map(partial(pontuar_rota, pesos, calcular_maximos(com_tempos)), com_tempos)
    )
)(tuple(map(com_tempo, rotas)))
