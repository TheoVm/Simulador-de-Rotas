import csv
from types import MappingProxyType

from src.models import LinhaTransito


def ler_csv(caminho: str) -> tuple:
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        return tuple(csv.DictReader(arquivo))


def linha_de_dict(d: dict) -> LinhaTransito:
    return LinhaTransito(
        regiao=d["regiao"], periodo=d["periodo"],
        indice_congestionamento=float(d["indice_congestionamento"]),
        semaforo_verde_s=float(d["semaforo_verde_s"]),
        semaforo_vermelho_s=float(d["semaforo_vermelho_s"]),
        fonte=d["fonte"],
    )


def carregar_transito(caminho: str):
    return MappingProxyType(dict(map(
        lambda l: ((l.regiao, l.periodo), l),
        map(linha_de_dict, ler_csv(caminho)))))
