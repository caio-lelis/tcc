"""Registro de execuções (RNF02).

Cada pergunta respondida vira uma linha JSON num arquivo JSONL, só por
acréscimo (nada é reescrito):

    experimento/execucoes/<rodada>.jsonl      execuções do harness
    experimento/execucoes/uso/AAAA-MM-DD.jsonl perguntas feitas pela interface

O registro fica fora do DuckDB pelo mesmo motivo do contexto (D-09): nenhuma
consulta gerada pelo modelo consegue lê-lo. E abre direto no pandas para a
análise estatística.

Cada linha guarda o commit do código que rodou (versao_codigo). Junto com o
hash do contexto e o hash do prompt, isso permite provar qual código, com qual
contexto e qual prompt, produziu cada número do trabalho (D-04).
"""
import subprocess
import threading
from datetime import date
from functools import cache
from pathlib import Path

from app import config
from app.models.registro import Execucao, Origem
from app.services.ingestao import normalizar_nome

_trava = threading.Lock()


@cache
def versao_codigo() -> str:
    """Commit atual do repositório; '-modificado' se há alterações não commitadas no código."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=config.RAIZ,
            capture_output=True, text=True, check=True, timeout=5,
        ).stdout.strip()
        alteracoes = subprocess.run(
            ["git", "status", "--porcelain", "--", "backend/app"], cwd=config.RAIZ,
            capture_output=True, text=True, check=True, timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "desconhecida"
    return f"{commit}-modificado" if alteracoes else commit


def caminho_registro(origem: Origem, rodada: str | None = None, dia: date | None = None) -> Path:
    if origem == "experimento":
        if not rodada:
            raise ValueError("Execuções do experimento precisam do nome da rodada.")
        return config.PASTA_EXECUCOES / f"{normalizar_nome(rodada)}.jsonl"
    return config.PASTA_EXECUCOES / "uso" / f"{(dia or date.today()).isoformat()}.jsonl"


def registrar(execucao: Execucao, arquivo: Path | None = None) -> Path:
    """Acrescenta a execução ao arquivo (padrão: definido pela origem e rodada)."""
    arquivo = arquivo or caminho_registro(execucao.origem, execucao.rodada)
    linha = execucao.model_dump_json() + "\n"
    with _trava:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        with arquivo.open("a", encoding="utf-8", newline="\n") as f:
            f.write(linha)
    return arquivo


def ler(arquivo: Path) -> list[Execucao]:
    if not arquivo.exists():
        return []
    with arquivo.open(encoding="utf-8") as f:
        return [Execucao.model_validate_json(linha) for linha in f if linha.strip()]
