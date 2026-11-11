from src.models import Maximos, Pesos, Rota
from src.objectives import PESOS
from src.scoring import (avaliar_notas, calcular_maximos, calcular_tempo_min,
                         com_tempo, compor, normalizar, ponderar, pontuar)


def test_calcular_tempo():
    assert calcular_tempo_min(30, 60) == 30
    assert calcular_tempo_min(10, 40) == 15


def test_com_tempo_nao_altera_a_original():
    original = Rota("A", 30, 60, 5)
    nova = com_tempo(original)
    assert nova.tempo_min == 30 and original.tempo_min == 0.0


def test_normalizar():
    assert normalizar(10, 5) == 0.5
    assert normalizar(0, 0) == 0.0


def test_compor_aplica_na_ordem():
    assert compor(lambda x: x + 1, lambda x: x * 2)(3) == 8


def test_calcular_maximos():
    rotas = (Rota("A", 10, 40, 2, 15), Rota("B", 20, 40, 6, 30))
    assert calcular_maximos(rotas) == Maximos(20, 30, 6)


def test_ponderar():
    assert ponderar(Pesos(1, 2, 3), (1.0, 1.0, 1.0)) == (1.0, 2.0, 3.0)


def test_pesos_somam_um_e_tempo_domina():
    assert round(PESOS.tempo + PESOS.congestionamento + PESOS.distancia, 9) == 1
    assert PESOS.tempo > PESOS.congestionamento > PESOS.distancia


def test_rota_com_valores_maximos_vale_a_soma_dos_pesos():
    rota = Rota("A", 10, 40, 10, tempo_min=15)
    assert round(pontuar(PESOS, Maximos(10, 15, 10), rota), 9) == 1.0


def test_pontuar_nao_altera_entrada():
    rota = Rota("A", 10, 40, 5, tempo_min=15)
    pontuar(PESOS, Maximos(10, 15, 5), rota)
    assert rota == Rota("A", 10, 40, 5, tempo_min=15)


def test_avaliar_notas_rota_melhor_em_tudo_tem_nota_menor():
    rapida = Rota("Rapida", 5, 60, 1)    # 5 min
    lenta = Rota("Lenta", 20, 20, 8)     # 60 min
    notas = avaliar_notas(PESOS, (rapida, lenta))
    assert notas[0].pontuacao < notas[1].pontuacao


def test_avaliar_notas_mantem_a_ordem_e_a_quantidade():
    rotas = (Rota("A", 5, 60, 1), Rota("B", 20, 20, 8), Rota("C", 9, 30, 4))
    notas = avaliar_notas(PESOS, rotas)
    assert tuple(map(lambda n: n.rota.nome, notas)) == ("A", "B", "C")


def test_avaliar_notas_sem_rotas():
    assert avaliar_notas(PESOS, ()) == ()