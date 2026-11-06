"""Repositório de contexto: descrições (RF02) e regras de negócio (RF03).

O contexto fica num arquivo JSON separado do DuckDB, por dois motivos:
1. uma consulta gerada pelo modelo nunca consegue ler as regras como se fossem dados;
2. o arquivo pode ser versionado e congelado antes do experimento.

As pendências (colunas sem descrição, descrições órfãs) são calculadas na hora,
comparando o contexto com as tabelas atuais. Descrições de colunas que sumiram
NÃO são apagadas: a coluna pode voltar numa próxima versão do CSV (RF10).
"""
import hashlib
import json
import os
import threading

from app import config
from app.models.contexto import (
    Contexto, ContextoCompleto, DescricaoTabela, Pendencias, Regra, RegraEntrada,
)
from app.models.tabela import TabelaInfo
from app.services import ingestao

_trava = threading.Lock()


class ErroContexto(ValueError):
    """Pedido inválido: tabela, coluna ou regra inexistente."""


# ---------------------------------------------------------------- arquivo

def carregar() -> Contexto:
    caminho = config.ARQUIVO_CONTEXTO
    if not caminho.exists():
        return Contexto()
    return Contexto.model_validate_json(caminho.read_text(encoding="utf-8"))


def _salvar(contexto: Contexto) -> None:
    """Grava num arquivo temporário e troca: o JSON nunca fica pela metade."""
    caminho = config.ARQUIVO_CONTEXTO
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".json.tmp")
    temporario.write_text(contexto.model_dump_json(indent=2), encoding="utf-8")
    os.replace(temporario, caminho)


def calcular_hash(contexto: Contexto) -> str:
    """Impressão digital do contexto: mesmo conteúdo -> mesmo hash, em qualquer máquina."""
    canonico = json.dumps(contexto.model_dump(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------- pendências (RF10)

def calcular_pendencias(contexto: Contexto, tabelas: list[TabelaInfo]) -> Pendencias:
    pendencias = Pendencias()
    atuais = {t.nome: [c.nome for c in t.colunas] for t in tabelas}

    for nome, colunas in atuais.items():
        descricao = contexto.tabelas.get(nome, DescricaoTabela())
        if not descricao.descricao.strip():
            pendencias.tabelas_sem_descricao.append(nome)
        sem = [c for c in colunas if not descricao.colunas.get(c, "").strip()]
        if sem:
            pendencias.colunas_sem_descricao[nome] = sem

    for nome, descricao in contexto.tabelas.items():
        if nome not in atuais:
            pendencias.tabelas_orfas.append(nome)
            continue
        orfas = [c for c in descricao.colunas if c not in atuais[nome]]
        if orfas:
            pendencias.colunas_orfas[nome] = orfas

    return pendencias


def obter_completo() -> ContextoCompleto:
    contexto = carregar()
    return ContextoCompleto(
        contexto=contexto,
        pendencias=calcular_pendencias(contexto, ingestao.listar_tabelas()),
        hash=calcular_hash(contexto),
    )


# ---------------------------------------------------------------- descrições (RF02)

def definir_descricao(tabela: str, nova: DescricaoTabela) -> DescricaoTabela:
    """Atualiza a descrição de uma tabela e de suas colunas.

    - a descrição da tabela é substituída;
    - as colunas enviadas são mescladas com as já existentes;
    - coluna enviada com texto vazio tem a descrição apagada;
    - descrições órfãs (de colunas que sumiram) são mantidas.
    """
    info = ingestao.descrever_tabela(tabela)
    if info is None:
        raise ErroContexto(f"Tabela {tabela!r} não existe.")
    existentes = {c.nome for c in info.colunas}
    desconhecidas = sorted(set(nova.colunas) - existentes)
    if desconhecidas:
        raise ErroContexto(f"Colunas inexistentes em {tabela!r}: {', '.join(desconhecidas)}")

    with _trava:
        contexto = carregar()
        atual = contexto.tabelas.get(tabela, DescricaoTabela())
        colunas = dict(atual.colunas)
        for coluna, texto in nova.colunas.items():
            if texto.strip():
                colunas[coluna] = texto.strip()
            else:
                colunas.pop(coluna, None)
        contexto.tabelas[tabela] = DescricaoTabela(descricao=nova.descricao.strip(), colunas=colunas)
        _salvar(contexto)
        return contexto.tabelas[tabela]


# ---------------------------------------------------------------- regras (RF03)

def _validar_tabelas(nomes: list[str]) -> None:
    existentes = {t.nome for t in ingestao.listar_tabelas()}
    desconhecidas = sorted(set(nomes) - existentes)
    if desconhecidas:
        raise ErroContexto(f"Tabelas inexistentes: {', '.join(desconhecidas)}")


def listar_regras() -> list[Regra]:
    return carregar().regras


def adicionar_regra(entrada: RegraEntrada) -> Regra:
    _validar_tabelas(entrada.tabelas)
    with _trava:
        contexto = carregar()
        proximo_id = max((r.id for r in contexto.regras), default=0) + 1
        regra = Regra(id=proximo_id, **entrada.model_dump(exclude={"texto"}), texto=entrada.texto.strip())
        contexto.regras.append(regra)
        _salvar(contexto)
        return regra


def atualizar_regra(regra_id: int, entrada: RegraEntrada) -> Regra:
    _validar_tabelas(entrada.tabelas)
    with _trava:
        contexto = carregar()
        for i, regra in enumerate(contexto.regras):
            if regra.id == regra_id:
                contexto.regras[i] = Regra(id=regra_id, **entrada.model_dump(exclude={"texto"}), texto=entrada.texto.strip())
                _salvar(contexto)
                return contexto.regras[i]
    raise ErroContexto(f"Regra {regra_id} não existe.")


def remover_regra(regra_id: int) -> None:
    with _trava:
        contexto = carregar()
        restantes = [r for r in contexto.regras if r.id != regra_id]
        if len(restantes) == len(contexto.regras):
            raise ErroContexto(f"Regra {regra_id} não existe.")
        contexto.regras = restantes
        _salvar(contexto)
