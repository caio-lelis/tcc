"""Formato de uma execução registrada (RNF02, Seção 4.4.3)."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.contexto import Configuracao
from app.models.resposta import SugestaoGrafico, UsoModelo

StatusExecucao = Literal["sucesso", "recusada", "invalida", "tempo_esgotado", "erro_modelo"]
"""sucesso = a consulta rodou (o acerto é julgado depois, contra o gabarito);
recusada / invalida / tempo_esgotado = falhas da consulta (D-13);
erro_modelo = falha de infraestrutura (rede, saldo): refazer, não contar como erro."""

Origem = Literal["interface", "experimento"]


class ResultadoRegistrado(BaseModel):
    colunas: list[str]
    linhas: list[list[Any]]
    truncado: bool


class UsoRegistrado(BaseModel):
    geracao: UsoModelo | None = None
    interpretacao: UsoModelo | None = None


class Execucao(BaseModel):
    """Uma pergunta respondida (ou não) pelo Data Talk. Uma linha no arquivo JSONL."""

    id: str
    quando: datetime  # UTC
    origem: Origem
    rodada: str | None = None  # só no experimento
    pergunta_id: str | None = None  # só no experimento
    repeticao: int | None = None  # só no experimento

    pergunta: str
    configuracao: Configuracao
    modelo: str  # modelo configurado (o devolvido pela API fica em uso)
    esforco: str | None
    hash_contexto: str
    hash_prompt: str
    prompt_sistema: str
    prompt_usuario: str

    sql: str | None = None
    grafico_sugerido: SugestaoGrafico | None = None
    status: StatusExecucao
    erro: str | None = None
    resultado: ResultadoRegistrado | None = None
    tempo_consulta_ms: float | None = None
    texto: str | None = None

    uso: UsoRegistrado = Field(default_factory=UsoRegistrado)
    custo_total_usd: float | None = None
    tempo_total_ms: float
    versao_codigo: str  # commit do Data Talk que rodou ("-modificado" se havia alterações locais)
