import json
import re
import urllib.parse
import urllib.request
from itertools import chain, pairwise
from math import cos, hypot, radians

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
USER_AGENT = "SimuladorDeRotas-ProjetoFaculdade/1.0"
CIDADES_RMR = ("recife", "olinda", "jaboatão", "jaboatao", "camaragibe")


def limpar_endereco(texto: str) -> str:
    sem_complemento = re.sub(
        r",?\s*\b(apt|apto|ap|apartamento|bloco|bl|sala|casa)\b\.?\s*\w+", "",
        texto, flags=re.IGNORECASE).strip(" ,")
    tem_cidade = any(map(lambda c: c in sem_complemento.lower(), CIDADES_RMR))
    sufixo = ", Pernambuco, Brasil" if tem_cidade else ", Recife, Pernambuco, Brasil"
    return sem_complemento + sufixo


def montar_url_nominatim(endereco: str) -> str:
    parametros = urllib.parse.urlencode(
        {"q": limpar_endereco(endereco), "format": "jsonv2", "limit": 1, "countrycodes": "br"})
    return f"{NOMINATIM_URL}?{parametros}"


def local_da_resposta(resposta) -> tuple:
    return (
        ()
        if not resposta
        else (float(resposta[0]["lat"]), float(resposta[0]["lon"]), resposta[0]["display_name"])
    )


def caixa_da_geometria(rotas: tuple, margem: float = 0.002) -> tuple:
    pontos = tuple(chain.from_iterable(map(lambda rota: rota.geometria, rotas)))
    lats, lons = tuple(map(lambda p: p[0], pontos)), tuple(map(lambda p: p[1], pontos))
    return (min(lats) - margem, min(lons) - margem, max(lats) + margem, max(lons) + margem)


def montar_consulta_semaforos(caixa: tuple) -> str:
    s, w, n, e = caixa
    return f'[out:json][timeout:60];node["highway"="traffic_signals"]({s},{w},{n},{e});out;'


def semaforos_da_resposta(resposta: dict) -> tuple:
    return tuple(map(lambda e: (e["lat"], e["lon"]),
                     filter(lambda e: e.get("type") == "node", resposta.get("elements", []))))


def _plano(ponto: tuple, lat_ref: float) -> tuple:
    return (ponto[1] * cos(radians(lat_ref)) * 111_320.0, ponto[0] * 110_540.0)


def distancia_ponto_segmento_m(ponto: tuple, a: tuple, b: tuple) -> float:
    px, py = _plano(ponto, ponto[0])
    ax, ay = _plano(a, ponto[0])
    bx, by = _plano(b, ponto[0])
    dx, dy = bx - ax, by - ay
    comprimento2 = dx * dx + dy * dy
    t = 0.0 if comprimento2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / comprimento2))
    return hypot(px - (ax + t * dx), py - (ay + t * dy))


def distancia_ponto_rota_m(geometria: tuple, ponto: tuple) -> float:
    return min(map(lambda seg: distancia_ponto_segmento_m(ponto, *seg), pairwise(geometria)),
               default=float("inf"))


def semaforos_na_rota(geometria: tuple, semaforos: tuple, limite_m: float = 25.0) -> int:
    return len(tuple(filter(lambda s: distancia_ponto_rota_m(geometria, s) <= limite_m, semaforos)))


def buscar_json(url: str, dados: bytes = None, timeout: int = 60):
    try:
        pedido = urllib.request.Request(url, data=dados, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
            return json.load(resposta)
    except Exception:
        return None


def geocodificar(endereco: str) -> tuple:
    return local_da_resposta(buscar_json(montar_url_nominatim(endereco)))


def buscar_semaforos(rotas: tuple):
    corpo = urllib.parse.urlencode({"data": montar_consulta_semaforos(caixa_da_geometria(rotas))}).encode()
    respostas = map(lambda url: buscar_json(url, dados=corpo, timeout=25), OVERPASS_URLS)
    resposta = next(filter(lambda r: r is not None, respostas), None)
    return None if resposta is None else semaforos_da_resposta(resposta)
