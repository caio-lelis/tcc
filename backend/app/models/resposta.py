"""Formatos da execução de uma consulta (RNF01, RNF04)."""
from typing import Any, Literal

from pydantic import BaseModel, Field

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


class SugestaoGrafico(BaseModel):
    """Sugestão do modelo na chamada de geração; conferida depois contra o resultado (RF09)."""

    tipo: Literal["linha", "barra", "indicador", "tabela"]
    x: str | None = None
    y: list[str] = []


class GraficoFinal(BaseModel):
    """Gráfico conferido contra o resultado (RF09)."""

    tipo: Literal["linha", "barra", "indicador", "tabela"]
    x: str | None = None
    y: list[str] = []
    origem: Literal["modelo", "regra"]  # a sugestão do modelo foi aceita ou caiu nas regras
    echarts: dict[str, Any] | None = None  # configuração para linha e barra
    indicador: dict[str, Any] | None = None  # {"rotulo", "valor"} para indicador


class UsoModelo(BaseModel):
    """Custo de uma chamada ao modelo, para o registro (RNF02)."""

    modelo: str  # nome devolvido pela API (pode trazer a versão datada)
    tokens_entrada: int
    tokens_saida: int  # inclui os tokens de raciocínio
    tokens_raciocinio: int | None = None
    custo_usd: float | None = None  # None se o preço do modelo não estiver em config.PRECOS
    tempo_ms: float


class RespostaGeracao(BaseModel):
    """1ª chamada (Seção 3.4, passo 3): SQL + sugestão de gráfico."""

    sql: str
    grafico: SugestaoGrafico
    uso: UsoModelo


class RespostaInterpretacao(BaseModel):
    """2ª chamada (Seção 3.4, passo 7): texto que descreve o resultado obtido."""

    texto: str
    uso: UsoModelo


class ErroModelo(Exception):
    """Falha na comunicação com a API (rede, saldo, limite de uso, formato).

    NÃO é erro do modelo no experimento: é falha de infraestrutura, e a
    execução deve ser refeita, não contada como resposta errada.
    """


class FalhaConsulta(Exception):
    """Consulta que não produziu resultado. O fluxo informa ao usuário e NÃO tenta de novo (Seção 3.4)."""

    def __init__(self, categoria: CategoriaFalha, mensagem: str):
        super().__init__(mensagem)
        self.categoria = categoria
        self.mensagem = mensagem


class Pergunta(BaseModel):
    """Corpo de POST /perguntas."""

    pergunta: str = Field(min_length=1)
    configuracao: Literal["C0", "C1", "C2"] | None = None  # RF06; padrão: config.CONFIGURACAO_PADRAO
    avancado: bool = False  # RF05: só no modo avançado a resposta traz o SQL


class RespostaFinal(BaseModel):
    """O que o usuário recebe (Seção 3.6): texto + gráfico + tabela; SQL só no modo avançado."""

    id: str  # id da execução no registro
    status: str  # sucesso | recusada | invalida | tempo_esgotado | erro_modelo
    mensagem: str | None = None  # explicação em português quando não há resposta
    configuracao: str
    texto: str | None = None
    grafico: GraficoFinal | None = None
    colunas: list[str] = []
    linhas: list[list[Any]] = []
    truncado: bool = False
    sql: str | None = None
