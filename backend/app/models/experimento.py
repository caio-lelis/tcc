"""Formatos do experimento de acurácia (RF07, Seções 3.9 e 4.5 a 4.6).

Três arquivos, três momentos:

    perguntas.yaml            banco escrito à mão (Tab. 7 + consultas alternativas, D-16)
    perguntas.congelado.json  banco congelado: o mesmo conteúdo + resultado esperado + hashes
    <rodada>.revisao.yaml     decisões manuais: casos limítrofes e categoria de cada erro
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.models.contexto import Configuracao, Contexto

Estrato = Literal["simples", "juncao", "regra", "ambigua"]
"""Tipo de dificuldade (Seção 4.5): simples, com junção de tabelas, dependente de
regra de negócio ou ambígua."""

CategoriaErro = Literal[
    "esquema", "juncao", "filtro_regra", "agregacao", "data_periodo", "interpretacao",
    "invalida", "recusada", "tempo_esgotado",
]
"""Taxonomia da Seção 4.6.4, mais "recusada" (D-13) e "tempo_esgotado" (RNF04).
As três últimas saem do status da execução; as demais são atribuídas na revisão."""

ESTRATOS: tuple[Estrato, ...] = ("simples", "juncao", "regra", "ambigua")
CONFIGURACOES: tuple[Configuracao, ...] = ("C0", "C1", "C2")


# ---------------------------------------------------------------- banco de perguntas

class Alternativa(BaseModel):
    """Interpretação errada plausível (D-16): precisa dar resultado DIFERENTE do gabarito."""

    descricao: str = Field(min_length=1)  # ex.: "conta pela data de criação"
    sql: str = Field(min_length=1)
    categoria: CategoriaErro | None = None  # erro que esta interpretação representa


class ItemPergunta(BaseModel):
    """Um item do banco de perguntas (Tab. 7)."""

    id: str = Field(min_length=1)
    pergunta: str = Field(min_length=1)
    estrato: Estrato
    sql_gabarito: str = Field(min_length=1)
    ordenada: bool = False  # True quando a pergunta pede uma ordem (ex.: ranking)
    regra_envolvida: str | None = None
    consultas_alternativas: list[Alternativa] = []
    observacao: str | None = None


class BancoPerguntas(BaseModel):
    perguntas: list[ItemPergunta] = Field(min_length=1)

    @model_validator(mode="after")
    def _ids_unicos(self):
        ids = [p.id for p in self.perguntas]
        repetidos = sorted({i for i in ids if ids.count(i) > 1})
        if repetidos:
            raise ValueError(f"ids repetidos no banco de perguntas: {', '.join(repetidos)}")
        return self


# ---------------------------------------------------------------- banco congelado

class Tabela(BaseModel):
    """Resultado de uma consulta: só o que entra na comparação."""

    colunas: list[str]
    linhas: list[list[Any]]


class AlternativaCongelada(Alternativa):
    resultado: Tabela


class ItemCongelado(ItemPergunta):
    resultado_esperado: Tabela
    consultas_alternativas: list[AlternativaCongelada] = []


class BancoCongelado(BaseModel):
    """Banco pronto para o experimento (Seção 4.5): não muda depois da primeira execução."""

    congelado_em: datetime  # UTC
    versao_codigo: str
    hash_banco: str  # impressão digital das perguntas, gabaritos e resultados esperados
    hash_contexto: str  # contexto (C1 e C2) em vigor no congelamento
    contexto: Contexto  # cópia do contexto congelado (D-09)
    perguntas: list[ItemCongelado]


# ---------------------------------------------------------------- verificação

class Problema(BaseModel):
    """Achado da verificação do banco. "erro" impede o congelamento; "aviso" não."""

    gravidade: Literal["erro", "aviso"]
    pergunta_id: str | None = None
    mensagem: str


# ---------------------------------------------------------------- revisão manual

class Revisao(BaseModel):
    """Decisão manual sobre uma execução (Seções 4.6.3 e 4.6.4)."""

    execucao: str  # id da execução no registro
    acerto: bool | None = None  # só para casos limítrofes: substitui o veredito automático
    categoria: CategoriaErro | None = None
    justificativa: str = Field(min_length=1)


# ---------------------------------------------------------------- avaliação

class Avaliacao(BaseModel):
    """Veredito de uma execução (uma linha do CSV de análise)."""

    rodada: str
    execucao: str
    pergunta_id: str
    estrato: Estrato
    configuracao: Configuracao
    repeticao: int
    status: str
    acerto: bool
    acerto_automatico: bool
    limitrofe: str | None = None  # por que vale uma revisão manual
    categoria: CategoriaErro | None = None  # definida (status ou revisão)
    categoria_sugerida: CategoriaErro | None = None  # da alternativa que coincidiu (D-16)
    alternativa: str | None = None  # descrição da alternativa que coincidiu
    justificativa: str | None = None
    custo_usd: float | None = None
    tempo_total_ms: float | None = None


class VereditoPergunta(BaseModel):
    """Uma pergunta numa configuração: maioria das repetições (Seção 4.6.3)."""

    pergunta_id: str
    estrato: Estrato
    configuracao: Configuracao
    repeticoes: int  # repetições válidas encontradas
    acertos: int
    acerto: bool  # maioria
    consistente: bool  # todas as repetições com o mesmo veredito (Q4)
    completo: bool  # tem todas as repetições previstas


class Resumo(BaseModel):
    rodada: str
    repeticoes_previstas: int
    execucoes: int
    refeitas: int  # falhas de infraestrutura (erro_modelo), fora da conta
    faltando: list[str]  # "P01/C2/r3"
    vereditos: list[VereditoPergunta]
    acuracia: dict[str, float | None]  # Q1: por configuração
    acuracia_por_estrato: dict[str, dict[str, float | None]]  # Q2: estrato -> configuração
    erros_por_categoria: dict[str, dict[str, int]]  # Q3: configuração -> categoria ("sem_categoria" = revisar)
    consistencia: dict[str, float | None]  # Q4: por configuração
    limitrofes: int  # execuções que pedem revisão manual e ainda não têm
    custo_usd: float
