"""Cliente do modelo de linguagem (RF04, RF08): as duas chamadas da Seção 3.4.

1. gerar():      prompt montado (C0/C1/C2) -> SQL + sugestão de gráfico
2. interpretar(): pergunta + resultado OBTIDO -> texto curto

A interpretação só acontece depois da execução, para que o texto descreva
os números retornados pelo banco, e não valores imaginados pelo modelo.

As duas chamadas pedem saída estruturada (esquema JSON estrito) e NÃO enviam
temperatura, que os modelos GPT-5.6 recusam (D-15). O esforço de raciocínio
é fixado por config.ESFORCO_RACIOCINIO.

ModeloFalso tem a mesma interface e é usado nos testes: nenhum teste chama a API (D-12).
"""
import json
import time
from functools import cache
from pathlib import Path
from typing import Any, Callable, Protocol

import openai

from app import config
from app.models.contexto import PromptMontado
from app.models.resposta import (
    ErroModelo, RespostaGeracao, RespostaInterpretacao, ResultadoConsulta, SugestaoGrafico, UsoModelo,
)
from app.services.construtor_contexto import PASTA_PROMPTS

ESQUEMA_GERACAO = {
    "type": "object",
    "additionalProperties": False,
    "required": ["sql", "grafico"],
    "properties": {
        "sql": {"type": "string"},
        "grafico": {
            "type": "object",
            "additionalProperties": False,
            "required": ["tipo", "x", "y", "serie"],
            "properties": {
                "tipo": {"type": "string", "enum": ["linha", "barra", "indicador", "tabela"]},
                "x": {"type": ["string", "null"]},
                "y": {"type": "array", "items": {"type": "string"}},
                "serie": {"type": ["string", "null"]},
            },
        },
    },
}

ESQUEMA_INTERPRETACAO = {
    "type": "object",
    "additionalProperties": False,
    "required": ["texto"],
    "properties": {"texto": {"type": "string"}},
}


@cache
def instrucoes_interpretacao() -> str:
    return (Path(PASTA_PROMPTS) / "instrucoes_interpretacao.md").read_text(encoding="utf-8").strip()


def calcular_custo(modelo: str, tokens_entrada: int, tokens_saida: int) -> float | None:
    """Custo em US$. Aceita o nome com versão datada (ex.: gpt-5.6-terra-2026-10-01)."""
    for nome, (preco_entrada, preco_saida) in config.PRECOS.items():
        if modelo == nome or modelo.startswith(f"{nome}-"):
            return round(tokens_entrada * preco_entrada / 1e6 + tokens_saida * preco_saida / 1e6, 6)
    return None


def montar_entrada_interpretacao(pergunta: str, resultado: ResultadoConsulta) -> str:
    """Texto da 2ª chamada: a pergunta e, no máximo, config.LINHAS_INTERPRETACAO linhas."""
    limite = config.LINHAS_INTERPRETACAO
    linhas = resultado.linhas[:limite]
    cortado = resultado.truncado or len(resultado.linhas) > limite

    partes = [f"Pergunta: {pergunta.strip()}", ""]
    if not resultado.linhas:
        partes.append("Resultado: nenhuma linha.")
    else:
        aviso = " (resultado cortado: há mais linhas que as mostradas)" if cortado else ""
        partes.append(f"Resultado ({len(linhas)} linha(s){aviso}):")
        partes.append(" | ".join(resultado.colunas))
        partes += [" | ".join("NULL" if v is None else str(v) for v in linha) for linha in linhas]
    return "\n".join(partes)


# ---------------------------------------------------------------- interface

class ClienteLLM(Protocol):
    def gerar(self, prompt: PromptMontado) -> RespostaGeracao: ...
    def interpretar(self, pergunta: str, resultado: ResultadoConsulta) -> RespostaInterpretacao: ...


# ---------------------------------------------------------------- OpenAI

class ClienteOpenAI:
    def __init__(self, modelo: str | None = None, esforco: str | None = None, sdk: Any = None):
        self.modelo = modelo or config.OPENAI_MODEL
        self.esforco = esforco if esforco is not None else config.ESFORCO_RACIOCINIO
        self._sdk = sdk or openai.OpenAI(api_key=config.OPENAI_API_KEY)

    def _chamar(self, instrucoes: str, entrada: str, nome: str, esquema: dict) -> tuple[dict, UsoModelo]:
        argumentos: dict[str, Any] = {
            "model": self.modelo,
            "instructions": instrucoes,
            "input": entrada,
            "text": {"format": {"type": "json_schema", "name": nome, "schema": esquema, "strict": True}},
        }
        if self.esforco:
            argumentos["reasoning"] = {"effort": self.esforco}

        inicio = time.perf_counter()
        try:
            resposta = self._sdk.responses.create(**argumentos)
        except openai.OpenAIError as erro:
            raise ErroModelo(f"{type(erro).__name__}: {erro}") from erro
        tempo_ms = (time.perf_counter() - inicio) * 1000

        try:
            dados = json.loads(resposta.output_text)
        except (TypeError, json.JSONDecodeError) as erro:
            raise ErroModelo(f"Resposta fora do formato JSON: {resposta.output_text!r:.200}") from erro

        uso = resposta.usage
        detalhes = getattr(uso, "output_tokens_details", None)
        modelo = getattr(resposta, "model", None) or self.modelo
        return dados, UsoModelo(
            modelo=modelo,
            tokens_entrada=uso.input_tokens,
            tokens_saida=uso.output_tokens,
            tokens_raciocinio=getattr(detalhes, "reasoning_tokens", None),
            custo_usd=calcular_custo(modelo, uso.input_tokens, uso.output_tokens),
            tempo_ms=round(tempo_ms, 1),
        )

    def gerar(self, prompt: PromptMontado) -> RespostaGeracao:
        dados, uso = self._chamar(prompt.sistema, prompt.usuario, "consulta", ESQUEMA_GERACAO)
        return RespostaGeracao(sql=dados["sql"], grafico=SugestaoGrafico(**dados["grafico"]), uso=uso)

    def interpretar(self, pergunta: str, resultado: ResultadoConsulta) -> RespostaInterpretacao:
        entrada = montar_entrada_interpretacao(pergunta, resultado)
        dados, uso = self._chamar(instrucoes_interpretacao(), entrada, "interpretacao", ESQUEMA_INTERPRETACAO)
        return RespostaInterpretacao(texto=dados["texto"], uso=uso)


# ---------------------------------------------------------------- modelo falso (testes)

class ModeloFalso:
    """Devolve respostas pré-definidas e registra o que recebeu. Custo zero."""

    def __init__(self, sql: str | Callable[[PromptMontado], str] = "SELECT 1 AS valor",
                 grafico: SugestaoGrafico | None = None, texto: str = "Resultado de teste."):
        self.sql = sql
        self.grafico = grafico or SugestaoGrafico(tipo="indicador", x=None, y=["valor"])
        self.texto = texto
        self.prompts: list[PromptMontado] = []
        self.interpretacoes: list[tuple[str, ResultadoConsulta]] = []

    @staticmethod
    def _uso() -> UsoModelo:
        return UsoModelo(modelo="falso", tokens_entrada=0, tokens_saida=0, custo_usd=0.0, tempo_ms=0.0)

    def gerar(self, prompt: PromptMontado) -> RespostaGeracao:
        self.prompts.append(prompt)
        sql = self.sql(prompt) if callable(self.sql) else self.sql
        return RespostaGeracao(sql=sql, grafico=self.grafico, uso=self._uso())

    def interpretar(self, pergunta: str, resultado: ResultadoConsulta) -> RespostaInterpretacao:
        self.interpretacoes.append((pergunta, resultado))
        return RespostaInterpretacao(texto=self.texto, uso=self._uso())


def obter_cliente() -> ClienteLLM:
    return ClienteOpenAI()
