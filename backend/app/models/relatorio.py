"""Formatos dos relatórios ao vivo (funcionalidade além do escopo do TCC).

Um relatório é uma lista de blocos editáveis. O SQL de cada resultado NÃO faz parte
do bloco: fica guardado no servidor, e o navegador nunca o envia nem o recebe.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.resposta import GraficoFinal

LIMITE_BLOCOS = 200


class Bloco(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    tipo: Literal["titulo", "texto", "resultado"]
    texto: str = Field(default="", max_length=50_000)

    # só em blocos do tipo "resultado": a foto dos dados no momento em que foi anexado
    pergunta: str | None = None
    grafico: GraficoFinal | None = None
    colunas: list[str] = []
    linhas: list[list[Any]] = []
    truncado: bool = False
    visao: Literal["grafico", "tabela"] = "grafico"
    dados_em: datetime | None = None  # quando estes números foram consultados


class Relatorio(BaseModel):
    id: str
    titulo: str
    blocos: list[Bloco]
    revisao: int  # sobe a cada gravação: evita que uma aba antiga apague trabalho novo
    criado_em: datetime
    atualizado_em: datetime


class ResumoRelatorio(BaseModel):
    id: str
    titulo: str
    quantidade_blocos: int
    quantidade_versoes: int
    atualizado_em: datetime


class Versao(BaseModel):
    numero: int
    tamanho: int  # bytes do PDF
    criado_em: datetime


class NovoRelatorio(BaseModel):
    titulo: str = Field(default="Relatório sem título", min_length=1, max_length=200)


class EdicaoRelatorio(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    blocos: list[Bloco] = Field(max_length=LIMITE_BLOCOS)
    revisao: int


class NovoAnexo(BaseModel):
    """Resposta do assistente a anexar. O SQL é buscado no registro pelo id da execução."""

    execucao_id: str = Field(min_length=1, max_length=64)
    texto: str = Field(default="", max_length=50_000)
    grafico: GraficoFinal | None = None
    colunas: list[str] = []
    linhas: list[list[Any]] = []
    truncado: bool = False


class NovaVersao(BaseModel):
    """Gráficos já desenhados pelo navegador em SVG: bloco -> um SVG por painel."""

    graficos: dict[str, list[str]] = {}
