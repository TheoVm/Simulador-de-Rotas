import csv
import io
from pathlib import Path
from types import MappingProxyType

from src.models import LinhaTransito

ler_csv = lambda caminho: tuple(
    csv.DictReader(io.StringIO(Path(caminho).read_text(encoding="utf-8")))
)

linha_de_dict = lambda d: LinhaTransito(
    regiao=d["regiao"], periodo=d["periodo"],
    indice_congestionamento=float(d["indice_congestionamento"]),
    semaforo_verde_s=float(d["semaforo_verde_s"]),
    semaforo_vermelho_s=float(d["semaforo_vermelho_s"]),
    fonte=d["fonte"],
)

carregar_transito = lambda caminho: MappingProxyType(dict(map(
    lambda l: ((l.regiao, l.periodo), l),
    map(linha_de_dict, ler_csv(caminho)))))
