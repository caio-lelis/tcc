"""Configuração comum dos testes.

Os testes nunca usam a chave real nem o banco real: a chave é um valor falso
(definido antes de importar o app) e cada teste ganha um banco DuckDB próprio
numa pasta temporária.
"""
import os
from pathlib import Path

import pytest

os.environ.setdefault("OPENAI_API_KEY", "chave-falsa-de-teste")  # load_dotenv não sobrescreve

from app import config  # noqa: E402

PASTA_EXEMPLO = Path(__file__).resolve().parents[2] / "dados" / "exemplo"


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    caminho = tmp_path / "teste.duckdb"
    monkeypatch.setattr(config, "BANCO_DUCKDB", caminho)
    monkeypatch.setattr(config, "ARQUIVO_CONTEXTO", tmp_path / "contexto.json")
    return caminho


@pytest.fixture
def csv_exemplo():
    """Lê um CSV do modelo de partida: csv_exemplo('contratos') -> bytes."""
    return lambda nome: (PASTA_EXEMPLO / f"{nome}.csv").read_bytes()
