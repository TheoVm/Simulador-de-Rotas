import os
import re
import time
from functools import partial

from src.api_client import buscar_rotas
from src.loader import carregar_transito
from src.models import Maximos
from src.objectives import OBJETIVOS
from src.osm_client import buscar_semaforos, geocodificar
from src.pipeline import executar
from src.regioes import PERIODOS, REGIOES

CSV_TRANSITO = os.path.join("data", "processed", "transito_recife.csv")
FORMATO = "Rua/Avenida, número, Bairro, Cidade"
EXEMPLO = "Rua Marechal Deodoro, 432, Boa Vista, Recife"
PADRAO_ENDERECO = re.compile(
    r"^[^,]+?[,\s]\s*(\d+[A-Za-z]?(-\w+)?|s/n)\s*(,\s*[^,]+){1,2}$", re.IGNORECASE)
MAX_TEMPO_MIN = 120.0
MAX_CONGESTIONAMENTO = 8.5


endereco_valido = lambda texto: bool(PADRAO_ENDERECO.match(texto.strip()))

endereco_ou_none = lambda texto: texto.strip() if endereco_valido(texto) else None

opcao_ou_none = lambda opcoes, texto: (
    lambda escolha: opcoes[int(escolha) - 1]
    if escolha.isdecimal() and 1 <= int(escolha) <= len(opcoes)
    else None
)(texto.strip())

indice_ou_none = lambda total, texto: (
    lambda escolha: int(escolha) if escolha.isdecimal() and 0 <= int(escolha) <= total else None
)(texto.strip())

eh_sim = lambda texto: texto.strip().lower() in ("s", "sim")

formatar_menu = lambda titulo, opcoes: (
    f"\n{titulo}\n"
    + "\n".join(map(lambda item: f"  {item[0]}) {item[1]}", enumerate(opcoes, start=1))))

formatar_linha = lambda posicao_nota: (
    lambda posicao, nota: (
        f"{posicao:>2}. {nota.rota.nome}\n    "
        f"{nota.rota.distancia_km:.2f} km | {nota.rota.tempo_min:.1f} min | "
        f"trânsito {nota.rota.congestionamento:.1f} | nota {nota.pontuacao:.3f}")
)(*posicao_nota)

formatar_ranking = lambda ranking: "\n".join(map(formatar_linha, enumerate(ranking, start=1)))

formatar_recomendacao = lambda s: (
    "" if s is None else
    f"\n\nRecomendada: {s.nome}\n  {s.distancia_km} km, {s.tempo_min} min, "
    f"trânsito {s.congestionamento} (nota {s.pontuacao})")

formatar_resultado = lambda resultado, objetivo, periodo: (
    f"Objetivo: {objetivo} | período: {periodo}\n{resultado.mensagem}\n\n"
    f"{formatar_ranking(resultado.ranking)}{formatar_recomendacao(resultado.resumo)}")

formatar_metros = lambda metros: f"{metros / 1000:.2f} km" if metros >= 1000 else f"{metros:.0f} m"

formatar_trecho = lambda item: (
    lambda posicao, trecho: f"  {posicao:>2}. {trecho[0]} ({formatar_metros(trecho[1])})"
)(*item)

formatar_trajeto = lambda nota, origem, destino: (
    f"\nTrajeto — {nota.rota.nome}\n"
    f"Origem : {origem}\n"
    + ("\n".join(map(formatar_trecho, enumerate(nota.rota.trajeto, start=1)))
       if nota.rota.trajeto else "  (trajeto indisponível)")
    + f"\nDestino: {destino}")

def perguntar(pergunta: str, converter, mensagem_erro: str):
    resposta = converter(input(pergunta))
    if resposta is not None:
        return resposta
    print(mensagem_erro)
    return perguntar(pergunta, converter, mensagem_erro)


def ler_endereco(rotulo: str) -> str:
    return perguntar(f"{rotulo} ({FORMATO}): ", endereco_ou_none,
                     f"  Formato inválido. Use: {FORMATO}\n  Exemplo: {EXEMPLO}")


def ler_opcao(titulo: str, opcoes: tuple) -> str:
    print(formatar_menu(titulo, opcoes))
    return perguntar(f"Escolha 1-{len(opcoes)}: ", partial(opcao_ou_none, opcoes),
                     f"  Digite um número de 1 a {len(opcoes)}.")


def perguntar_sim_nao(pergunta: str) -> bool:
    return eh_sim(input(f"{pergunta} [s/n]: "))


def explorar(resultado, origem: str, destino: str) -> None:
    total = len(resultado.ranking)
    if total == 0:
        return
    escolha = perguntar(
        f"\nDigite o número da rota para ver as ruas (1-{total}) ou 0 para continuar: ",
        partial(indice_ou_none, total),
        f"  Digite um número de 0 a {total}.")
    if escolha == 0:
        return
    print(formatar_trajeto(resultado.ranking[escolha - 1], origem, destino))
    explorar(resultado, origem, destino)


def simular(tabela) -> None:
    print(f"\nInforme os endereços no formato: {FORMATO}")
    print(f"Exemplo: {EXEMPLO}\n")
    origem_txt = ler_endereco("Origem ")
    destino_txt = ler_endereco("Destino")
    objetivo = ler_opcao("Objetivo:", tuple(OBJETIVOS))
    periodo = ler_opcao("Período do dia:", PERIODOS)

    print("\nBuscando endereços...")
    origem = geocodificar(origem_txt)
    time.sleep(1)
    destino = geocodificar(destino_txt)
    if not origem or not destino:
        print("Endereço não encontrado (ou sem internet). Confira o bairro e a cidade.")
        return
    print(f"Origem : {origem[2]}\nDestino: {destino[2]}\n")

    print("Buscando rotas e semáforos...")
    rotas_reais = buscar_rotas(origem[:2], destino[:2])
    semaforos = buscar_semaforos(rotas_reais) if rotas_reais else ()
    if semaforos is None:
        print("Aviso: não foi possível obter os semáforos do OSM; usando semáforos estimados.\n")

    resultado = executar(
        REGIOES, tabela, periodo, semaforos or (), rotas_reais, OBJETIVOS[objetivo],
        Maximos(distancia=float("inf"), tempo=MAX_TEMPO_MIN, congestionamento=MAX_CONGESTIONAMENTO),
    )
    print("\n" + formatar_resultado(resultado, objetivo, periodo))
    explorar(resultado, origem[2], destino[2])


def sessao(tabela) -> None:
    simular(tabela)
    if perguntar_sim_nao("\nNova consulta?"):
        sessao(tabela)


def main() -> None:
    try:
        tabela = carregar_transito(CSV_TRANSITO)
    except FileNotFoundError:
        print(f"Arquivo {CSV_TRANSITO} não encontrado. Ele faz parte do repositório; restaure-o.")
        return

    print("=== Simulador de Escolha de Rotas — RMR Recife ===")
    try:
        sessao(tabela)
    except (KeyboardInterrupt, EOFError):
        print()
    print("Até logo!")


if __name__ == "__main__":
    main()
