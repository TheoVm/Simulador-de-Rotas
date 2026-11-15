from src.models import Limites, Rota, RotaPontuada
from src.pipeline import avaliar, chave_ranking
from src.recommend import menor_por, recomendar

LIMITES = Limites(tempo_max=60, congestionamento_max=8)
ROTAS = (
    Rota("Rapida", 15, 60, 6),      # 15 min
    Rota("Curta", 5, 10, 6),        # 30 min
    Rota("Livre", 12, 24, 1),       # 30 min
    Rota("Descartada", 3, 2, 2),    # 90 min
)


def nomes(ranking):
    return tuple(map(lambda rp: rp.rota.nome, ranking))


def test_descartada_nao_aparece_no_ranking():
    assert "Descartada" not in nomes(avaliar(ROTAS, LIMITES))


def test_rota_de_menor_tempo_lidera():
    assert nomes(avaliar(ROTAS, LIMITES))[0] == "Rapida"


def test_desempate_usa_tempo_depois_transito_depois_distancia():
    mesma_nota = 0.5
    a = RotaPontuada(Rota("A", 10, 40, 5, 20), mesma_nota)
    b = RotaPontuada(Rota("B", 10, 40, 4, 20), mesma_nota)  # menos trânsito
    c = RotaPontuada(Rota("C", 10, 40, 5, 18), mesma_nota)  # menos tempo
    d = RotaPontuada(Rota("D", 8, 40, 5, 20), mesma_nota)   # menos distância
    ordenadas = tuple(sorted((a, b, c, d), key=chave_ranking))
    assert nomes(ordenadas) == ("C", "B", "D", "A")


def test_menor_por_com_chaves_diferentes():
    itens = (3, 1, 2)
    assert menor_por(lambda x: x, itens) == 1
    assert menor_por(lambda x: -x, itens) == 3


def test_tres_saidas():
    s = recomendar(ROTAS, LIMITES).resumo
    assert s.melhor_nota.rota.nome == "Rapida"
    assert s.menos_transito.rota.nome == "Livre"
    assert s.mais_curta.rota.nome == "Curta"
    assert (s.total_recebidas, s.total_validas, s.total_descartadas) == (4, 3, 1)


def test_sem_rotas_validas():
    rec = recomendar(ROTAS, Limites(1, 1))
    assert rec.resumo is None and rec.ranking == ()


def test_so_uma_rota_valida():
    rec = recomendar((ROTAS[0],), LIMITES)
    assert rec.resumo.melhor_nota == rec.resumo.mais_curta == rec.resumo.menos_transito


def test_sem_nenhuma_rota():
    assert recomendar((), LIMITES).resumo is None


def test_entrada_nao_e_alterada():
    antes = tuple(ROTAS)
    recomendar(ROTAS, LIMITES)
    assert ROTAS == antes and ROTAS[0].tempo_min == 0.0