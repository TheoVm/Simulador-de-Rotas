from types import MappingProxyType

from src.models import Pesos

OBJETIVOS = MappingProxyType({
    "mais_rapido": Pesos(distancia=0.1, tempo=0.6, congestionamento=0.3),
    "mais_curto": Pesos(distancia=0.6, tempo=0.3, congestionamento=0.1),
    "menos_transito": Pesos(distancia=0.1, tempo=0.3, congestionamento=0.6),
})

PESOS = OBJETIVOS["mais_rapido"]
