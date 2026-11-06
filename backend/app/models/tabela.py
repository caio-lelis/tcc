"""Formatos de dados de uma tabela anexada (RF01, RF10)."""
from typing import Any

from pydantic import BaseModel


class Coluna(BaseModel):
    nome: str  # nome normalizado, usado no banco e no prompt
    nome_original: str  # cabeçalho como veio no CSV
    tipo: str  # tipo inferido pelo DuckDB (INTEGER, DATE, VARCHAR...)


class TabelaInfo(BaseModel):
    """Metadados de uma tabela: é o que o contexto C0 mostra ao modelo."""

    nome: str
    colunas: list[Coluna]
    linhas: int
    amostra: list[dict[str, Any]]  # primeiras linhas, já em formato JSON


class ResultadoIngestao(BaseModel):
    """O que mudou ao anexar ou reanexar um CSV (RF10)."""

    tabela: TabelaInfo
    nova: bool  # True se a tabela não existia antes
    colunas_novas: list[str] = []  # ficarão "sem descrição"
    colunas_removidas: list[str] = []  # descrições ficarão órfãs
    colunas_tipo_alterado: list[str] = []
