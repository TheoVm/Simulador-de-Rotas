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
PADRAO_ENDERECO = re.compile(r"^[^,\d]+,\s*\d+[A-Za-z]?\s*(,\s*[^,]+){1,2}$")
MAX_TEMPO_MIN = 120.0
MAX_CONGESTIONAMENTO = 8.5


def endereco_valido(texto: str) -> bool:
    return bool(PADRAO_ENDERECO.match(texto.strip()))


def formatar_linha(posicao_nota: tuple) -> str:
    posicao, nota = posicao_nota
    r = nota.rota
    return (f"{posicao:>2}. {r.nome}\n    {r.distancia_km:.2f} km | {r.tempo_min:.1f} min | "
            f"trânsito {r.congestionamento:.1f} | nota {nota.pontuacao:.3f}")


def formatar_resultado(resultado, objetivo: str, periodo: str) -> str:
    ranking = "\n".join(map(formatar_linha, enumerate(resultado.ranking, start=1)))
    s = resultado.resumo
    recomendacao = ("" if s is None else
                    f"\n\nRecomendada: {s.nome}\n  {s.distancia_km} km, {s.tempo_min} min, "
                    f"trânsito {s.congestionamento} (nota {s.pontuacao})")
    return (f"Objetivo: {objetivo} | período: {periodo}\n{resultado.mensagem}\n\n"
            f"{ranking}{recomendacao}")


def endereco_ou_none(texto: str):
    return texto.strip() if endereco_valido(texto) else None


def opcao_ou_none(opcoes: tuple, texto: str):
    escolha = texto.strip()
    return opcoes[int(escolha) - 1] if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes) else None


def eh_sim(texto: str) -> bool:
    return texto.strip().lower() in ("s", "sim")


def formatar_menu(titulo: str, opcoes: tuple) -> str:
    itens = "\n".join(map(lambda item: f"  {item[0]}) {item[1]}", enumerate(opcoes, start=1)))
    return f"\n{titulo}\n{itens}"


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
        print("Aviso: não foi possível obter os semáforos do OSM; considerando 0.\n")

    resultado = executar(
        REGIOES, tabela, periodo, semaforos or (), rotas_reais, OBJETIVOS[objetivo],
        Maximos(distancia=float("inf"), tempo=MAX_TEMPO_MIN, congestionamento=MAX_CONGESTIONAMENTO),
    )
    print("\n" + formatar_resultado(resultado, objetivo, periodo))


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
