import json
import urllib.request
from dataclasses import replace
from functools import reduce
from itertools import chain

from src.models import VIA_SEM_NOME, RotaReal

BASE_URL = "https://router.project-osrm.org/route/v1/driving"
USER_AGENT = "SimuladorDeRotas-ProjetoFaculdade/1.0"


def formatar_coordenada(ponto: tuple) -> str:
    latitude, longitude = ponto
    return f"{longitude},{latitude}"


def montar_url(pontos: tuple, alternativas: int = 3) -> str:
    coordenadas = ";".join(map(formatar_coordenada, pontos))
    return (f"{BASE_URL}/{coordenadas}?alternatives={alternativas}"
            "&overview=full&geometries=geojson&steps=true")


def pontos_de_desvio(origem: tuple, destino: tuple, fracao: float = 0.3) -> tuple:
    meio = ((origem[0] + destino[0]) / 2, (origem[1] + destino[1]) / 2)
    dlat, dlon = destino[0] - origem[0], destino[1] - origem[1]
    return ((meio[0] - dlon * fracao, meio[1] + dlat * fracao),
            (meio[0] + dlon * fracao, meio[1] - dlat * fracao))


def sem_repetidas(rotas: tuple) -> tuple:
    unicas = reduce(
        lambda acc, r: acc if any(map(lambda u: round(u.distancia_km, 1) == round(r.distancia_km, 1), acc))
        else acc + (r,),
        rotas, ())
    return tuple(map(lambda item: replace(item[1], nome=f"Rota {item[0]}"), enumerate(unicas, start=1)))


def passos_da_rota(dados: dict) -> tuple:
    return tuple(chain.from_iterable(map(lambda leg: leg.get("steps", []), dados.get("legs", []))))


def somar_rua(acc: dict, passo: dict) -> dict:
    nome = passo.get("name") or VIA_SEM_NOME
    return {**acc, nome: acc.get(nome, 0.0) + passo.get("distance", 0.0)}


def ruas_da_rota(dados: dict) -> tuple:
    por_rua = reduce(somar_rua, passos_da_rota(dados), {})
    return tuple(sorted(por_rua.items(), key=lambda item: item[1], reverse=True))


def juntar_trecho(acc: tuple, trecho: tuple) -> tuple:
    nome, metros = trecho
    return (acc[:-1] + ((nome, acc[-1][1] + metros),)
            if acc and acc[-1][0] == nome
            else acc + (trecho,))


def trajeto_da_rota(dados: dict) -> tuple:
    trechos = tuple(map(
        lambda passo: (passo.get("name") or VIA_SEM_NOME, passo.get("distance", 0.0)),
        filter(lambda passo: passo.get("distance", 0.0) > 0, passos_da_rota(dados))))
    return reduce(juntar_trecho, trechos, ())


def geometria_da_rota(dados: dict) -> tuple:
    return tuple(map(lambda c: (c[1], c[0]), dados["geometry"]["coordinates"]))


def rota_de_item(item: tuple) -> RotaReal:
    posicao, dados = item
    return RotaReal(
        nome=f"Rota {posicao}",
        distancia_km=dados["distance"] / 1000,
        duracao_min=dados["duration"] / 60,
        geometria=geometria_da_rota(dados),
        ruas=ruas_da_rota(dados),
        trajeto=trajeto_da_rota(dados),
    )


def rotas_da_resposta(resposta: dict) -> tuple:
    return (
        ()
        if resposta.get("code") != "Ok"
        else tuple(map(rota_de_item, enumerate(resposta["routes"], start=1)))
    )


def buscar_resposta(url: str, timeout: int = 30) -> dict:
    try:
        pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
            return json.load(resposta)
    except Exception:
        return {}


def buscar_rotas(origem: tuple, destino: tuple, alternativas: int = 3) -> tuple:
    diretas = rotas_da_resposta(buscar_resposta(montar_url((origem, destino), alternativas)))
    extras = (() if len(diretas) >= alternativas or not diretas else tuple(chain.from_iterable(map(
        lambda desvio: rotas_da_resposta(buscar_resposta(montar_url((origem, desvio, destino), 0))),
        pontos_de_desvio(origem, destino)))))
    return sem_repetidas(diretas + extras)
