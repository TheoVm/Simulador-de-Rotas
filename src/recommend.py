"""reduce: melhor nota, menos trânsito e mais curta.

menor_por é uma função de ordem superior: recebe a "chave" de comparação.
As três saídas usam a MESMA função, só muda a chave.
"""
from functools import reduce

from src.models import Recomendacao, Resumo
from src.pipeline import avaliar, chave_ranking


def menor_por(chave, itens):
    return reduce(lambda a, b: b if chave(b) < chave(a) else a, itens)


def chave_transito(rp) -> tuple:
    r = rp.rota
    return (r.congestionamento, r.tempo_min, r.distancia_km, r.nome)


def chave_curta(rp) -> tuple:
    r = rp.rota
    return (r.distancia_km, r.tempo_min, r.congestionamento, r.nome)


def resumir(ranking, total_recebidas):
    return (
        None
        if not ranking
        else Resumo(
            melhor_nota=menor_por(chave_ranking, ranking),
            menos_transito=menor_por(chave_transito, ranking),
            mais_curta=menor_por(chave_curta, ranking),
            total_recebidas=total_recebidas,
            total_validas=len(ranking),
            total_descartadas=total_recebidas - len(ranking),
        )
    )


def recomendar(rotas, limites, top_n=3) -> Recomendacao:
    ranking = avaliar(rotas, limites)
    return Recomendacao(
        ranking=ranking[:top_n],
        resumo=resumir(ranking, len(rotas)),
    )