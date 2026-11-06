"""Formatos da execução de uma consulta (RNF01, RNF04)."""
from typing import Any, Literal

from pydantic import BaseModel

CategoriaFalha = Literal["recusada", "invalida", "tempo_esgotado"]
"""Por que uma consulta não produziu resultado (Seção 4.6.4 + D-13):

- recusada:        barrada por segurança (não é leitura, mais de um comando,
                   tentativa de acessar arquivos). Categoria própria (D-13).
- invalida:        o DuckDB não conseguiu executar (sintaxe, tabela ou coluna
                   inexistente, conversão de tipo). = "consulta inválida".
- tempo_esgotado:  passou do limite de tempo (RNF04).
"""


class ResultadoConsulta(BaseModel):
    sql: str
    colunas: list[str]
    tipos: list[str]
    linhas: list[list[Any]]  # já em formato JSON (datas como texto ISO)
    truncado: bool  # True se havia mais linhas que o limite (RNF04)
    tempo_ms: float


class FalhaConsulta(Exception):
    """Consulta que não produziu resultado. O fluxo informa ao usuário e NÃO tenta de novo (Seção 3.4)."""

    def __init__(self, categoria: CategoriaFalha, mensagem: str):
        super().__init__(mensagem)
        self.categoria = categoria
        self.mensagem = mensagem
