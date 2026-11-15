from functools import reduce

from src.models import Resumo

ranquear = lambda notas: tuple(sorted(notas, key=lambda n: n.pontuacao))

escolher_melhor = lambda notas: reduce(
    lambda melhor, atual: atual if atual.pontuacao < melhor.pontuacao else melhor, notas
)

resumo_do_melhor = lambda total, melhor: Resumo(
    nome=melhor.rota.nome,
    distancia_km=round(melhor.rota.distancia_km, 2),
    tempo_min=round(melhor.rota.tempo_min, 1),
    congestionamento=melhor.rota.congestionamento,
    pontuacao=round(melhor.pontuacao, 3),
    total_ranking=total,
)

resumir = lambda notas: None if not notas else resumo_do_melhor(len(notas), escolher_melhor(notas))
