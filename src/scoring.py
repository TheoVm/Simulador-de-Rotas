"""Cálculo da nota de cada rota. Só funções puras: mesma entrada, mesma saída,
sem print, sem arquivo e sem alterar nada que veio de fora."""
from dataclasses import replace
from functools import partial, reduce
from operator import mul

from src.models import Maximos, Pesos, Rota, RotaPontuada


def calcular_tempo_min(distancia_km: float, velocidade_kmh: float) -> float:
    """tempo (min) = distância / velocidade média * 60"""
    return distancia_km / velocidade_kmh * 60


def com_tempo(rota: Rota) -> Rota:
    """Devolve uma Rota NOVA com o tempo calculado (a original não muda)."""
    return replace(
        rota,
        tempo_min=calcular_tempo_min(rota.distancia_km, rota.velocidade_media_kmh),
    )


def compor(*funcoes):
    """Composição: compor(f, g, h)(x) == h(g(f(x))) — aplica na ordem dada."""
    return lambda valor: reduce(lambda acc, f: f(acc), funcoes, valor)


def normalizar(maximo: float, valor: float) -> float:
    """Coloca o valor na escala 0..1 (evita divisão por zero)."""
    return 0.0 if maximo == 0 else valor / maximo


def calcular_maximos(rotas) -> Maximos:
    """reduce: percorre as rotas guardando o maior valor de cada critério."""
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
    """Devolve (distância, tempo, trânsito) na escala 0..1."""
    return (
        normalizar(maximos.distancia, rota.distancia_km),
        normalizar(maximos.tempo, rota.tempo_min),
        normalizar(maximos.congestionamento, rota.congestionamento),
    )


def ponderar(pesos: Pesos, valores: tuple) -> tuple:
    """Multiplica cada valor normalizado pelo peso do critério."""
    return tuple(
        map(mul, valores, (pesos.distancia, pesos.tempo, pesos.congestionamento))
    )


def pontuar(pesos: Pesos, maximos: Maximos, rota: Rota) -> float:
    """normalizar -> ponderar -> somar (menor = melhor)."""
    calcular = compor(
        partial(normalizar_rota, maximos),
        partial(ponderar, pesos),
        sum,
    )
    return calcular(rota)


def pontuar_rota(pesos: Pesos, maximos: Maximos, rota: Rota) -> RotaPontuada:
    return RotaPontuada(rota=rota, pontuacao=pontuar(pesos, maximos, rota))


def avaliar_notas(pesos: Pesos, rotas) -> tuple:
    """Rotas -> notas: calcula o tempo (map), os máximos (reduce) e a nota (map)."""
    com_tempos = tuple(map(com_tempo, rotas))
    maximos = calcular_maximos(com_tempos)
    return tuple(map(partial(pontuar_rota, pesos, maximos), com_tempos))