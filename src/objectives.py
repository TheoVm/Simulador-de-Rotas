"""Pesos do objetivo: percurso em MENOR TEMPO.

Ordem: tempo > trânsito > distância (somam 1).
"""
from src.models import Pesos

PESOS = Pesos(distancia=0.1, tempo=0.6, congestionamento=0.3)