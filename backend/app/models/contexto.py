"""Formatos do contexto de negócio escrito pelo usuário (RF02, RF03)."""
from typing import Literal

from pydantic import BaseModel, Field


class DescricaoTabela(BaseModel):
    """O que o usuário escreve sobre uma tabela: vai para o contexto C1."""

    descricao: str = ""
    colunas: dict[str, str] = {}  # nome da coluna -> descrição


class RegraEntrada(BaseModel):
    """Regra de negócio ou definição de métrica: vai para o contexto C2."""

    texto: str = Field(min_length=1)
    tipo: Literal["regra", "metrica"] = "regra"
    tabelas: list[str] = []  # só para organizar na tela; no C2 vão todas as regras


class Regra(RegraEntrada):
    id: int


class Contexto(BaseModel):
    """Conteúdo do arquivo contexto.json."""

    tabelas: dict[str, DescricaoTabela] = {}
    regras: list[Regra] = []


class Pendencias(BaseModel):
    """Diferenças entre o contexto e as tabelas atuais (RF10). Calculadas, nunca salvas."""

    tabelas_sem_descricao: list[str] = []
    colunas_sem_descricao: dict[str, list[str]] = {}
    tabelas_orfas: list[str] = []  # descritas, mas não existem mais
    colunas_orfas: dict[str, list[str]] = {}


Configuracao = Literal["C0", "C1", "C2"]
"""Nível de contexto (Tab. 6): C0 esquema; C1 + descrições; C2 + regras."""


class PromptMontado(BaseModel):
    """O que é enviado ao modelo na chamada de geração (Seção 3.4, passo 3)."""

    configuracao: Configuracao
    sistema: str  # instruções gerais: idênticas nas três configurações (D-03)
    usuario: str  # bloco de contexto + pergunta
    hash_prompt: str  # impressão digital de sistema + usuario (D-04)
    hash_contexto: str  # impressão digital do contexto cadastrado


class ContextoCompleto(BaseModel):
    contexto: Contexto
    pendencias: Pendencias
    hash: str  # impressão digital do contexto, registrada em cada execução (RNF02)
