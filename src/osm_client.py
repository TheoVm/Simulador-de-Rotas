import json
import re
import time
import urllib.parse
import urllib.request
from itertools import chain, pairwise
from math import cos, hypot, radians
from operator import itemgetter

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
USER_AGENT = "SimuladorDeRotas-ProjetoFaculdade/1.0"
CIDADES_RMR = ("recife", "olinda", "jaboatão", "jaboatao", "camaragibe")

# O complemento é a palavra-chave seguida de número ou de uma letra só ("apt 301", "bloco B").
# Assim "Casa Forte" (bairro) não é confundido com "casa 2" (complemento).
PADRAO_COMPLEMENTO = re.compile(
    r",?\s*\b(apt|apto|ap|apartamento|bloco|bl|sala|casa)\b\.?\s*(\d\w*|[a-z]\b)",
    re.IGNORECASE)

remover_complemento = lambda texto: PADRAO_COMPLEMENTO.sub("", texto).strip(" ,")

sufixo_da_cidade = lambda texto: (
    ", Pernambuco, Brasil"
    if any(map(lambda c: c in texto.lower(), CIDADES_RMR))
    else ", Recife, Pernambuco, Brasil")

limpar_endereco = lambda texto: (
    lambda sem_complemento: sem_complemento + sufixo_da_cidade(sem_complemento)
)(remover_complemento(texto))

parametros_nominatim = lambda endereco: urllib.parse.urlencode(
    {"q": limpar_endereco(endereco), "format": "jsonv2", "limit": 1, "countrycodes": "br"})

montar_url_nominatim = lambda endereco: f"{NOMINATIM_URL}?{parametros_nominatim(endereco)}"

local_da_resposta = lambda resposta: (
    ()
    if not resposta
    else (float(resposta[0]["lat"]), float(resposta[0]["lon"]), resposta[0]["display_name"])
)

pontos_das_rotas = lambda rotas: tuple(chain.from_iterable(map(lambda rota: rota.geometria, rotas)))

caixa_dos_pontos = lambda pontos, margem: (
    lambda lats, lons: (min(lats) - margem, min(lons) - margem, max(lats) + margem, max(lons) + margem)
)(tuple(map(itemgetter(0), pontos)), tuple(map(itemgetter(1), pontos)))

caixa_da_geometria = lambda rotas, margem=0.002: caixa_dos_pontos(pontos_das_rotas(rotas), margem)

montar_consulta_semaforos = lambda caixa: (
    '[out:json][timeout:60];node["highway"="traffic_signals"]({0},{1},{2},{3});out;'.format(*caixa))

semaforos_da_resposta = lambda resposta: tuple(map(
    lambda e: (e["lat"], e["lon"]),
    filter(lambda e: e.get("type") == "node", resposta.get("elements", []))))

_plano = lambda ponto, lat_ref: (
    ponto[1] * cos(radians(lat_ref)) * 111_320.0, ponto[0] * 110_540.0)

posicao_no_segmento = lambda p, a, b: (
    lambda dx, dy: (
        lambda comprimento2: 0.0 if comprimento2 == 0
        else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / comprimento2))
    )(dx * dx + dy * dy)
)(b[0] - a[0], b[1] - a[1])

distancia_no_plano = lambda p, a, b: (
    lambda t: hypot(p[0] - (a[0] + t * (b[0] - a[0])), p[1] - (a[1] + t * (b[1] - a[1])))
)(posicao_no_segmento(p, a, b))

distancia_ponto_segmento_m = lambda ponto, a, b: distancia_no_plano(
    *map(lambda q: _plano(q, ponto[0]), (ponto, a, b)))

distancia_ponto_rota_m = lambda geometria, ponto: min(
    map(lambda seg: distancia_ponto_segmento_m(ponto, *seg), pairwise(geometria)),
    default=float("inf"))

semaforos_na_rota = lambda geometria, semaforos, limite_m=25.0: len(tuple(filter(
    lambda s: distancia_ponto_rota_m(geometria, s) <= limite_m, semaforos)))


# Borda impura: precisa de try/except, que não existe como expressão (não dá para ser lambda).
def buscar_json(url: str, dados: bytes = None, timeout: int = 60):
    try:
        pedido = urllib.request.Request(url, data=dados, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
            return json.load(resposta)
    except Exception:
        return None


# Borda impura: faz a requisição e espera 1 s (a política do Nominatim pede no máximo 1 pedido por segundo).
def buscar_local(endereco: str) -> tuple:
    time.sleep(1)
    return local_da_resposta(buscar_json(montar_url_nominatim(endereco)))


partes_do_endereco = lambda texto: tuple(filter(None, map(str.strip, texto.split(","))))

# Do mais específico ao mais genérico: completo, rua+número+cidade, rua+bairro+cidade, rua+cidade.
variantes_do_endereco = lambda texto: (
    lambda partes: tuple(dict.fromkeys(map(", ".join, (
        partes,
        partes[:2] + partes[-1:],
        partes[:1] + partes[2:],
        partes[:1] + partes[-1:],
    ))))
)(partes_do_endereco(texto))

geocodificar = lambda endereco: next(
    filter(None, map(buscar_local, variantes_do_endereco(endereco))), ())

corpo_overpass = lambda rotas: urllib.parse.urlencode(
    {"data": montar_consulta_semaforos(caixa_da_geometria(rotas))}).encode()

primeira_resposta = lambda corpo: next(filter(
    lambda r: r is not None,
    map(lambda url: buscar_json(url, dados=corpo, timeout=25), OVERPASS_URLS)), None)

semaforos_ou_none = lambda resposta: None if resposta is None else semaforos_da_resposta(resposta)

buscar_semaforos = lambda rotas: semaforos_ou_none(primeira_resposta(corpo_overpass(rotas)))