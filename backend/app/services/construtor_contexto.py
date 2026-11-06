"""Construtor de contexto (RF06): monta o prompt nas configurações C0, C1 e C2.

É o ÚNICO componente cujo comportamento muda entre as configurações do
experimento (Seção 3.3). As instruções gerais são lidas de um arquivo e são
idênticas nas três (D-03); só o bloco de contexto muda (Tab. 6):

    C0  esquema em CREATE TABLE + amostra de linhas            (D-01)
    C1  C0 + descrições de tabelas e colunas como comentários --
    C2  C1 + todas as regras de negócio e métricas             (D-02)

A saída é determinística: mesmas tabelas + mesmo contexto + mesma pergunta
= mesmo texto = mesmo hash (D-04).
"""
import hashlib
from functools import cache
from pathlib import Path
from typing import Any

from app.models.contexto import Configuracao, Contexto, DescricaoTabela, PromptMontado
from app.models.tabela import TabelaInfo
from app.services import repositorio

PASTA_PROMPTS = Path(__file__).resolve().parents[1] / "prompts"
LIMITE_TEXTO_AMOSTRA = 60  # caracteres por valor na amostra

_ROTULO_REGRA = {"regra": "Regra", "metrica": "Métrica"}


@cache
def instrucoes_gerais() -> str:
    return (PASTA_PROMPTS / "instrucoes_geracao.md").read_text(encoding="utf-8").strip()


# ---------------------------------------------------------------- formatação

def _linha_unica(texto: str) -> str:
    """Comentários SQL de uma linha: quebras de linha viram espaço."""
    return " ".join(texto.split())


def _valor_amostra(valor: Any) -> str:
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "true" if valor else "false"  # como no SQL, não "True" do Python
    texto = _linha_unica(str(valor))
    if len(texto) > LIMITE_TEXTO_AMOSTRA:
        texto = texto[: LIMITE_TEXTO_AMOSTRA - 1] + "…"
    return texto.replace("*/", "* /")  # não pode fechar o bloco de comentário


def _bloco_amostra(tabela: TabelaInfo) -> list[str]:
    if not tabela.amostra:
        return ["/* Amostra: tabela vazia */"]
    colunas = [c.nome for c in tabela.colunas]
    linhas = [" | ".join(colunas)]
    linhas += [" | ".join(_valor_amostra(linha.get(c)) for c in colunas) for linha in tabela.amostra]
    return [f"/* Amostra ({len(tabela.amostra)} de {tabela.linhas} linhas):", *linhas, "*/"]


def _bloco_tabela(tabela: TabelaInfo, descricao: DescricaoTabela | None) -> str:
    """CREATE TABLE com descrições do C1 como comentários (descricao=None no C0)."""
    abertura = f"CREATE TABLE {tabela.nome} ("
    if descricao and descricao.descricao.strip():
        abertura += f"  -- {_linha_unica(descricao.descricao)}"
    linhas = [abertura]

    for i, coluna in enumerate(tabela.colunas):
        separador = "," if i < len(tabela.colunas) - 1 else ""
        linha = f"  {coluna.nome} {coluna.tipo}{separador}"
        texto = descricao.colunas.get(coluna.nome, "") if descricao else ""
        if texto.strip():
            linha += f"  -- {_linha_unica(texto)}"
        linhas.append(linha)

    linhas.append(");")
    linhas += _bloco_amostra(tabela)
    return "\n".join(linhas)


def _bloco_regras(contexto: Contexto) -> str:
    if not contexto.regras:
        return ""
    linhas = ["-- Regras de negócio e definições de métricas:"]
    for numero, regra in enumerate(sorted(contexto.regras, key=lambda r: r.id), start=1):
        linhas.append(f"-- {numero}. {_ROTULO_REGRA[regra.tipo]}: {_linha_unica(regra.texto)}")
    return "\n".join(linhas)


# ---------------------------------------------------------------- montagem

def montar_contexto(configuracao: Configuracao, tabelas: list[TabelaInfo], contexto: Contexto) -> str:
    """Bloco de contexto (esquema + descrições + regras) conforme a configuração."""
    com_descricoes = configuracao in ("C1", "C2")
    blocos = [
        _bloco_tabela(t, contexto.tabelas.get(t.nome, DescricaoTabela()) if com_descricoes else None)
        for t in sorted(tabelas, key=lambda t: t.nome)
    ]
    if configuracao == "C2":
        regras = _bloco_regras(contexto)
        if regras:
            blocos.append(regras)
    return "\n\n".join(blocos)


def montar_prompt(pergunta: str, configuracao: Configuracao, tabelas: list[TabelaInfo],
                  contexto: Contexto) -> PromptMontado:
    """Prompt completo da chamada de geração. O contexto vem antes da pergunta,
    para que o início do texto seja igual entre perguntas (aproveita o cache de prompt)."""
    if not tabelas:
        raise ValueError("Nenhuma tabela anexada: não há o que consultar.")
    sistema = instrucoes_gerais()
    usuario = (
        "Esquema do banco de dados:\n\n"
        f"{montar_contexto(configuracao, tabelas, contexto)}\n\n"
        f"Pergunta: {pergunta.strip()}"
    )
    hash_prompt = hashlib.sha256(f"{sistema}\n\x00\n{usuario}".encode("utf-8")).hexdigest()[:12]
    return PromptMontado(
        configuracao=configuracao,
        sistema=sistema,
        usuario=usuario,
        hash_prompt=hash_prompt,
        hash_contexto=repositorio.calcular_hash(contexto),
    )
