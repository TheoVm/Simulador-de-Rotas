from src.filters import filtrar_rotas, rota_valida
from src.models import Limites, Rota

LIMITES = Limites(tempo_max=60, congestionamento_max=8)


def rota(nome="A", tempo=30, cong=5):
    return Rota(nome, 10, 40, cong, tempo_min=tempo)


def test_rota_dentro_dos_limites():
    assert rota_valida(LIMITES, rota())


def test_rota_no_limite_exato_passa():
    assert rota_valida(LIMITES, rota(tempo=60, cong=8))


def test_descartada_por_tempo():
    assert not rota_valida(LIMITES, rota(tempo=61))


def test_descartada_por_congestionamento():
    assert not rota_valida(LIMITES, rota(cong=8.1))


def test_filtrar_mantem_so_as_adequadas():
    rotas = (rota("A"), rota("B", tempo=90), rota("C", cong=9))
    assert filtrar_rotas(LIMITES, rotas) == (rotas[0],)