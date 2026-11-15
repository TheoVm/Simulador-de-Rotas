from functools import partial
from operator import attrgetter, itemgetter

from src.filters import dentro_dos_limites
from src.models import Resultado, Rota
from src.osm_client import semaforos_na_rota
from src.recommend import ranquear, resumir
from src.scoring import avaliar_notas, com_tempo, compor

AMARELO_S = 4.0
IMPACTO_TRANSITO = 0.06

distancia_aprox_m = lambda a, b: ((a[0] - b[0]) ** 2 + ((a[1] - b[1]) * 0.99) ** 2) ** 0.5 * 111_000

regiao_mais_proxima = lambda regioes, ponto: min(
    regioes, key=lambda r: distancia_aprox_m((r.latitude, r.longitude), ponto))

amostrar = lambda geometria, quantidade=40: (
    lambda passo: geometria[::passo] + geometria[-1:]
)(max(1, len(geometria) // quantidade))

media = lambda valores: sum(valores) / len(valores)

media_do_campo = lambda campo, linhas: media(tuple(map(attrgetter(campo), linhas)))

atraso_semaforos_min = lambda qtd, verde_s, vermelho_s: (
    qtd * vermelho_s ** 2 / (2 * (verde_s + vermelho_s + AMARELO_S)) / 60)

linhas_da_rota = lambda regioes, tabela, periodo, rota_real: tuple(map(
    lambda ponto: tabela[(regiao_mais_proxima(regioes, ponto).nome, periodo)],
    amostrar(rota_real.geometria)))

minutos_da_rota = lambda rota_real, linhas, qtd: (
    rota_real.duracao_min * (1 + IMPACTO_TRANSITO * media_do_campo("indice_congestionamento", linhas))
    + atraso_semaforos_min(
        qtd,
        media_do_campo("semaforo_verde_s", linhas),
        media_do_campo("semaforo_vermelho_s", linhas)))

ruas_principais = lambda rota_real: ", ".join(map(itemgetter(0), rota_real.ruas[:2]))

nome_da_rota = lambda rota_real, qtd: f"{rota_real.nome} via {ruas_principais(rota_real)} [{qtd} semáforos]"

rota_com_dados = lambda rota_real, linhas, qtd: Rota(
    nome=nome_da_rota(rota_real, qtd),
    distancia_km=round(rota_real.distancia_km, 2),
    velocidade_media_kmh=round(rota_real.distancia_km / minutos_da_rota(rota_real, linhas, qtd) * 60, 2),
    congestionamento=round(media_do_campo("indice_congestionamento", linhas), 1),
)

rota_analisada = lambda regioes, tabela, periodo, semaforos, rota_real: rota_com_dados(
    rota_real,
    linhas_da_rota(regioes, tabela, periodo, rota_real),
    semaforos_na_rota(rota_real.geometria, semaforos),
)

processar = lambda pesos, limites, rotas: compor(
    partial(map, com_tempo),
    partial(filter, partial(dentro_dos_limites, limites)),
    partial(avaliar_notas, pesos),
    ranquear,
)(rotas)

mensagem_do_resultado = lambda candidatas, ranking: (
    "Nenhuma rota encontrada (confira os endereços e a internet)."
    if not candidatas
    else "Todas as rotas foram descartadas pelos limites informados."
    if not ranking
    else f"{len(ranking)} de {len(candidatas)} rotas dentro dos limites."
)

resultado_de = lambda candidatas, ranking: Resultado(
    ranking=ranking,
    resumo=resumir(ranking),
    mensagem=mensagem_do_resultado(candidatas, ranking),
)

executar = lambda regioes, tabela, periodo, semaforos, rotas_reais, pesos, limites: (
    lambda candidatas: resultado_de(candidatas, processar(pesos, limites, candidatas))
)(tuple(map(partial(rota_analisada, regioes, tabela, periodo, semaforos), rotas_reais)))
