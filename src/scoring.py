from dataclasses import replace
from functools import partial, reduce
from operator import mul

from src.models import Maximos, Pesos, Rota, RotaPontuada


def calcular_tempo_min(distancia_km: float, velocidade_kmh: float) -> float:
    return distancia_km / velocidade_kmh * 60


def com_tempo(rota: Rota) -> Rota:
    return replace(
        rota,
        tempo_min=calcular_tempo_min(rota.distancia_km, rota.velocidade_media_kmh),
    )


def compor(*funcoes):
    return lambda valor: reduce(lambda acc, f: f(acc), funcoes, valor)


def normalizar(maximo: float, valor: float) -> float:
    return 0.0 if maximo == 0 else valor / maximo


def calcular_maximos(rotas) -> Maximos:
    return reduce(
        lambda acc, r: Maximos(
            distancia=max(acc.distancia, r.distancia_km),
            tempo=max(acc.tempo, r.tempo_min),
            congestionamento=max(acc.congestionamento, r.congestionamento),
        ),
        rotas,
        Maximos(0.0, 0.0, 0.0),
    )


def normalizar_rota(maximos: Maximos, rota: Rota) -> tuple:
    return (
        normalizar(maximos.distancia, rota.distancia_km),
        normalizar(maximos.tempo, rota.tempo_min),
        normalizar(maximos.congestionamento, rota.congestionamento),
    )


def ponderar(pesos: Pesos, valores: tuple) -> tuple:
    return tuple(
        map(mul, valores, (pesos.distancia, pesos.tempo, pesos.congestionamento))
    )


def pontuar(pesos: Pesos, maximos: Maximos, rota: Rota) -> float:
    calcular = compor(
        partial(normalizar_rota, maximos),
        partial(ponderar, pesos),
        sum,
    )
    return calcular(rota)


def pontuar_rota(pesos: Pesos, maximos: Maximos, rota: Rota) -> RotaPontuada:
    return RotaPontuada(rota=rota, pontuacao=pontuar(pesos, maximos, rota))


def avaliar_notas(pesos: Pesos, rotas) -> tuple:
    com_tempos = tuple(map(com_tempo, rotas))
    maximos = calcular_maximos(com_tempos)
    return tuple(map(partial(pontuar_rota, pesos, maximos), com_tempos))