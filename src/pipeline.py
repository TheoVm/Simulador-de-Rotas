<<<<<<< HEAD
"""Do conjunto de rotas ao ranking: map (tempo) -> filter -> map (nota) -> sorted."""
from src.filters import filtrar_rotas
from src.objectives import PESOS
from src.scoring import com_tempo, pontuar_todas

CASAS_DECIMAIS = 3  # arredondamento da nota, para que empates possam acontecer


def chave_ranking(rp) -> tuple:
    """Nota arredondada; empate: menor tempo, menor trânsito, menor distância."""
    return (
        round(rp.pontuacao, CASAS_DECIMAIS),
        rp.rota.tempo_min,
        rp.rota.congestionamento,
        rp.rota.distancia_km,
        rp.rota.nome,
    )


def avaliar(rotas, limites, pesos=PESOS) -> tuple:
    validas = filtrar_rotas(limites, map(com_tempo, rotas))
    return tuple(sorted(pontuar_todas(pesos, validas), key=chave_ranking))
=======
from functools import partial

from src.filters import dentro_dos_limites
from src.models import Resultado, Rota
from src.osm_client import semaforos_na_rota
from src.recommend import ranquear, resumir
from src.scoring import avaliar_notas, com_tempo, compor

AMARELO_S = 4.0
IMPACTO_TRANSITO = 0.06


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


def rota_analisada(regioes: tuple, tabela, periodo: str, semaforos: tuple, rota_real) -> Rota:
    linhas = tuple(map(
        lambda ponto: tabela[(regiao_mais_proxima(regioes, ponto).nome, periodo)],
        amostrar(rota_real.geometria)))
    cong = media(tuple(map(lambda l: l.indice_congestionamento, linhas)))
    verde = media(tuple(map(lambda l: l.semaforo_verde_s, linhas)))
    vermelho = media(tuple(map(lambda l: l.semaforo_vermelho_s, linhas)))
    qtd = semaforos_na_rota(rota_real.geometria, semaforos)
    minutos = (rota_real.duracao_min * (1 + IMPACTO_TRANSITO * cong)
               + atraso_semaforos_min(qtd, verde, vermelho))
    principais = ", ".join(map(lambda r: r[0], rota_real.ruas[:2]))
    return Rota(
        nome=f"{rota_real.nome} via {principais} [{qtd} semáforos]",
        distancia_km=round(rota_real.distancia_km, 2),
        velocidade_media_kmh=round(rota_real.distancia_km / minutos * 60, 2),
        congestionamento=round(cong, 1),
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
>>>>>>> fabac52a5051cf674e7ed2313454b0396c607f68
