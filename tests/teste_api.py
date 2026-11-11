from src.api_client import (montar_url, rota_de_item, rotas_da_resposta,
                            valor_da_tabela)
from src.models import Rota
from src.objectives import PESOS
from src.scoring import avaliar_notas

# Resposta no formato da documentação da OSRM (distance em metros, duration em s)
RESPOSTA = {
    "code": "Ok",
    "routes": [
        {"distance": 12500.4, "duration": 1000.0},
        {"distance": 9800.0, "duration": 1500.0},
        {"distance": 15000.0, "duration": 1100.0},
    ],
    "waypoints": [],
}


def test_montar_url_usa_longitude_primeiro():
    url = montar_url((-34.87, -8.06), (-34.92, -8.12), alternativas=3)
    assert url == (
        "http://router.project-osrm.org/route/v1/driving/"
        "-34.87,-8.06;-34.92,-8.12?alternatives=3&overview=false"
    )


def test_valor_da_tabela_volta_ao_inicio():
    assert valor_da_tabela((1, 2, 3), 0) == 1
    assert valor_da_tabela((1, 2, 3), 3) == 1


def test_rota_de_item_converte_metros_em_km():
    rota = rota_de_item((1, {"distance": 12500.0}))
    assert rota.nome == "Rota 1" and rota.distancia_km == 12.5


def test_rotas_da_resposta():
    rotas = rotas_da_resposta(RESPOSTA)
    assert len(rotas) == 3
    assert tuple(map(lambda r: r.nome, rotas)) == ("Rota 1", "Rota 2", "Rota 3")
    assert all(map(lambda r: isinstance(r, Rota), rotas))


def test_resposta_com_erro_vira_tupla_vazia():
    assert rotas_da_resposta({"code": "NoRoute", "message": "sem rota"}) == ()
    assert rotas_da_resposta({}) == ()


def test_mesma_resposta_gera_as_mesmas_rotas():
    assert rotas_da_resposta(RESPOSTA) == rotas_da_resposta(RESPOSTA)


def test_rotas_da_api_entram_no_calculo_da_nota():
    notas = avaliar_notas(PESOS, rotas_da_resposta(RESPOSTA))
    assert len(notas) == 3