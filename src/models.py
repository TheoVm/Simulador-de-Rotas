"""Dados imutáveis (frozen=True): depois de criados, nenhum valor muda."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Rota:
    nome: str
    distancia_km: float
    velocidade_media_kmh: float
    congestionamento: float  # 0 (livre) a 10 (parado), valor fictício
    tempo_min: float = 0.0   # calculado: distância / velocidade * 60


@dataclass(frozen=True)
class Pesos:
    distancia: float
    tempo: float
    congestionamento: float


@dataclass(frozen=True)
class Maximos:
    distancia: float
    tempo: float
    congestionamento: float


@dataclass(frozen=True)
class RotaPontuada:
    rota: Rota
    pontuacao: float  # menor = melhor