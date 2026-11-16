import json
import urllib.request
from dataclasses import replace
from functools import reduce
from itertools import chain

from src.models import VIA_SEM_NOME, RotaReal

BASE_URL = "https://router.project-osrm.org/route/v1/driving"
USER_AGENT = "SimuladorDeRotas-ProjetoFaculdade/1.0"

formatar_coordenada = lambda ponto: f"{ponto[1]},{ponto[0]}"

montar_url = lambda pontos, alternativas=3: (
    f"{BASE_URL}/{';'.join(map(formatar_coordenada, pontos))}?alternatives={alternativas}"
    "&overview=full&geometries=geojson&steps=true")

ponto_medio = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

pontos_de_desvio = lambda origem, destino, fracao=0.3: (
    lambda meio, dlat, dlon: (
        (meio[0] - dlon * fracao, meio[1] + dlat * fracao),
        (meio[0] + dlon * fracao, meio[1] - dlat * fracao))
)(ponto_medio(origem, destino), destino[0] - origem[0], destino[1] - origem[1])

ja_existe = lambda acc, rota: any(map(
    lambda u: round(u.distancia_km, 1) == round(rota.distancia_km, 1), acc))

unicas = lambda rotas: reduce(
    lambda acc, r: acc if ja_existe(acc, r) else acc + (r,), rotas, ())

sem_repetidas = lambda rotas: tuple(map(
    lambda item: replace(item[1], nome=f"Rota {item[0]}"),
    enumerate(unicas(rotas), start=1)))

passos_da_rota = lambda dados: tuple(chain.from_iterable(
    map(lambda leg: leg.get("steps", []), dados.get("legs", []))))

somar_rua = lambda acc, passo: (
    lambda nome: {**acc, nome: acc.get(nome, 0.0) + passo.get("distance", 0.0)}
)(passo.get("name") or VIA_SEM_NOME)

ruas_da_rota = lambda dados: tuple(sorted(
    reduce(somar_rua, passos_da_rota(dados), {}).items(),
    key=lambda item: item[1], reverse=True))

juntar_trecho = lambda acc, trecho: (
    acc[:-1] + ((trecho[0], acc[-1][1] + trecho[1]),)
    if acc and acc[-1][0] == trecho[0]
    else acc + (trecho,)
)

trajeto_da_rota = lambda dados: reduce(
    juntar_trecho,
    tuple(map(
        lambda passo: (passo.get("name") or VIA_SEM_NOME, passo.get("distance", 0.0)),
        filter(lambda passo: passo.get("distance", 0.0) > 0, passos_da_rota(dados)))),
    (),
)

geometria_da_rota = lambda dados: tuple(map(
    lambda c: (c[1], c[0]), dados["geometry"]["coordinates"]))

rota_de_item = lambda item: RotaReal(
    nome=f"Rota {item[0]}",
    distancia_km=item[1]["distance"] / 1000,
    duracao_min=item[1]["duration"] / 60,
    geometria=geometria_da_rota(item[1]),
    ruas=ruas_da_rota(item[1]),
    trajeto=trajeto_da_rota(item[1]),
)

rotas_da_resposta = lambda resposta: (
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


rotas_extras = lambda origem, destino, alternativas, diretas: (
    ()
    if len(diretas) >= alternativas or not diretas
    else tuple(chain.from_iterable(map(
        lambda desvio: rotas_da_resposta(buscar_resposta(montar_url((origem, desvio, destino), 0))),
        pontos_de_desvio(origem, destino))))
)

buscar_rotas = lambda origem, destino, alternativas=3: (
    lambda diretas: sem_repetidas(diretas + rotas_extras(origem, destino, alternativas, diretas))
)(rotas_da_resposta(buscar_resposta(montar_url((origem, destino), alternativas))))
