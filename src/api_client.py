"""Importação das rotas pela API OSRM (roteador que usa dados do OpenStreetMap).

Tudo aqui é PURO, menos a função `buscar_resposta`, que é a única que fala
com a internet (a "borda" de entrada do programa).

A API só entrega a DISTÂNCIA de cada rota alternativa. A velocidade média e o
congestionamento são fictícios: vêm de tabelas fixas, escolhidas pela posição da
rota. Assim o resultado é sempre o mesmo para a mesma resposta (nada de random).
"""
import json
import urllib.request

from src.models import Rota

BASE_URL = "http://router.project-osrm.org/route/v1/driving"

VELOCIDADES_KMH = (40.0, 50.0, 30.0, 60.0, 45.0)
CONGESTIONAMENTOS = (3.0, 6.5, 8.0, 2.0, 5.0)


# ---------- partes puras ----------

def formatar_coordenada(ponto: tuple) -> str:
    """(longitude, latitude) -> 'lon,lat' (a OSRM pede longitude primeiro)."""
    longitude, latitude = ponto
    return f"{longitude},{latitude}"


def montar_url(origem: tuple, destino: tuple, alternativas: int = 3) -> str:
    coordenadas = ";".join(map(formatar_coordenada, (origem, destino)))
    return f"{BASE_URL}/{coordenadas}?alternatives={alternativas}&overview=false"


def valor_da_tabela(tabela: tuple, indice: int) -> float:
    """Pega o valor pela posição, voltando ao início quando a tabela acaba."""
    return tabela[indice % len(tabela)]


def rota_de_item(item: tuple) -> Rota:
    """(posição, rota da API) -> Rota. A API dá a distância em metros."""
    posicao, dados = item
    return Rota(
        nome=f"Rota {posicao}",
        distancia_km=dados["distance"] / 1000,
        velocidade_media_kmh=valor_da_tabela(VELOCIDADES_KMH, posicao - 1),
        congestionamento=valor_da_tabela(CONGESTIONAMENTOS, posicao - 1),
    )


def rotas_da_resposta(resposta: dict) -> tuple:
    """Resposta da OSRM -> tupla de Rota. Resposta com erro vira tupla vazia."""
    return (
        ()
        if resposta.get("code") != "Ok"
        else tuple(map(rota_de_item, enumerate(resposta["routes"], start=1)))
    )


# ---------- borda impura (internet) ----------

def buscar_resposta(url: str, timeout: int = 10) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resposta:
        return json.load(resposta)


def buscar_rotas(origem: tuple, destino: tuple, alternativas: int = 3) -> tuple:
    """Junta tudo: monta a URL, busca na API e converte em Rotas."""
    return rotas_da_resposta(buscar_resposta(montar_url(origem, destino, alternativas)))