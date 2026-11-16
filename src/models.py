from dataclasses import dataclass

VIA_SEM_NOME = "(via sem nome)"


@dataclass(frozen=True)
class Rota:
    nome: str
    distancia_km: float
    velocidade_media_kmh: float
    congestionamento: float
    tempo_min: float = 0.0
    trajeto: tuple = ()


@dataclass(frozen=True)
class Pesos:
    distancia: float
    tempo: float
    congestionamento: float


@dataclass(frozen=True)
class Maximos:
    distancia: float
    tempo: float
    congestionamento: float


@dataclass(frozen=True)
class RotaPontuada:
    rota: Rota
    pontuacao: float


@dataclass(frozen=True)
class RotaReal:
    nome: str
    distancia_km: float
    duracao_min: float
    geometria: tuple
    ruas: tuple
    trajeto: tuple = ()


@dataclass(frozen=True)
class Regiao:
    nome: str
    latitude: float
    longitude: float
    fator_transito: float


@dataclass(frozen=True)
class LinhaTransito:
    regiao: str
    periodo: str
    indice_congestionamento: float
    semaforo_verde_s: float
    semaforo_vermelho_s: float
    fonte: str


@dataclass(frozen=True)
class Resumo:
    nome: str
    distancia_km: float
    tempo_min: float
    congestionamento: float
    pontuacao: float
    total_ranking: int


@dataclass(frozen=True)
class Resultado:
    ranking: tuple
    resumo: object
    mensagem: str
