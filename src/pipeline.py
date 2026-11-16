from functools import partial
from itertools import pairwise
from math import ceil

from src.filters import dentro_dos_limites
from src.models import VIA_SEM_NOME, Resultado, Rota
from src.osm_client import semaforos_na_rota
from src.recommend import ranquear, resumir
from src.scoring import avaliar_notas, com_tempo, compor

AMARELO_S = 4.0
IMPACTO_TRANSITO = 0.06
INTERVALO_SEMAFORO_M = 300.0


def distancia_aprox_m(a: tuple, b: tuple) -> float:
    return ((a[0] - b[0]) ** 2 + ((a[1] - b[1]) * 0.99) ** 2) ** 0.5 * 111_000


def regiao_mais_proxima(regioes: tuple, ponto: tuple):
    return min(regioes, key=lambda r: distancia_aprox_m((r.latitude, r.longitude), ponto))


def amostrar(geometria: tuple, quantidade: int = 40) -> tuple:
    passo = max(1, len(geometria) // quantidade)
    return geometria[::passo] + geometria[-1:]


def media(valores: tuple) -> float:
    return sum(valores) / len(valores)


def atraso_semaforos_min(qtd: int, verde_s: float, vermelho_s: float) -> float:
    ciclo = verde_s + vermelho_s + AMARELO_S
    return qtd * vermelho_s ** 2 / (2 * ciclo) / 60


def semaforos_por_distancia(metros: float) -> int:
    return max(0, ceil(metros / INTERVALO_SEMAFORO_M) - 1)


def troca_com_semaforo(par: tuple) -> bool:
    return all(map(lambda trecho: trecho[0] != VIA_SEM_NOME, par))


def trocas_de_rua(trajeto: tuple) -> int:
    return len(tuple(filter(troca_com_semaforo, pairwise(trajeto))))


def semaforos_estimados(trajeto: tuple, distancia_m: float) -> int:
    return (trocas_de_rua(trajeto) + sum(map(lambda trecho: semaforos_por_distancia(trecho[1]), trajeto))
            if trajeto
            else semaforos_por_distancia(distancia_m))


def rota_analisada(regioes: tuple, tabela, periodo: str, semaforos: tuple, rota_real) -> Rota:
    linhas = tuple(map(
        lambda ponto: tabela[(regiao_mais_proxima(regioes, ponto).nome, periodo)],
        amostrar(rota_real.geometria)))
    cong = media(tuple(map(lambda l: l.indice_congestionamento, linhas)))
    verde = media(tuple(map(lambda l: l.semaforo_verde_s, linhas)))
    vermelho = media(tuple(map(lambda l: l.semaforo_vermelho_s, linhas)))
    reais = semaforos_na_rota(rota_real.geometria, semaforos)
    usou_estimativa = reais == 0
    qtd = semaforos_estimados(rota_real.trajeto, rota_real.distancia_km * 1000) if usou_estimativa else reais
    rotulo = "semáforos estimados" if usou_estimativa else "semáforos"
    minutos = (rota_real.duracao_min * (1 + IMPACTO_TRANSITO * cong)
               + atraso_semaforos_min(qtd, verde, vermelho))
    principais = ", ".join(map(lambda r: r[0], rota_real.ruas[:2]))
    return Rota(
        nome=f"{rota_real.nome} via {principais} [{qtd} {rotulo}]",
        distancia_km=round(rota_real.distancia_km, 2),
        velocidade_media_kmh=round(rota_real.distancia_km / minutos * 60, 2),
        congestionamento=round(cong, 1),
        trajeto=rota_real.trajeto,
    )


def processar(pesos, limites, rotas: tuple) -> tuple:
    return compor(
        lambda rs: tuple(map(com_tempo, rs)),
        lambda rs: tuple(filter(partial(dentro_dos_limites, limites), rs)),
        partial(avaliar_notas, pesos),
        ranquear,
    )(rotas)


def executar(regioes, tabela, periodo, semaforos, rotas_reais, pesos, limites) -> Resultado:
    candidatas = tuple(map(partial(rota_analisada, regioes, tabela, periodo, semaforos), rotas_reais))
    ranking = processar(pesos, limites, candidatas)
    return Resultado(
        ranking=ranking,
        resumo=resumir(ranking),
        mensagem=(
            "Nenhuma rota encontrada (confira os endereços e a internet)."
            if not candidatas
            else "Todas as rotas foram descartadas pelos limites informados."
            if not ranking
            else f"{len(ranking)} de {len(candidatas)} rotas dentro dos limites."
        ),
    )
