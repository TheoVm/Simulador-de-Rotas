from functools import reduce

from src.models import Resumo


def ranquear(notas) -> tuple:
    return tuple(sorted(notas, key=lambda n: n.pontuacao))


def escolher_melhor(notas):
    return reduce(lambda melhor, atual: atual if atual.pontuacao < melhor.pontuacao else melhor, notas)


def resumir(notas):
    return None if not notas else (lambda m: Resumo(
        nome=m.rota.nome,
        distancia_km=round(m.rota.distancia_km, 2),
        tempo_min=round(m.rota.tempo_min, 1),
        congestionamento=m.rota.congestionamento,
        pontuacao=round(m.pontuacao, 3),
        total_ranking=len(notas),
    ))(escolher_melhor(notas))
