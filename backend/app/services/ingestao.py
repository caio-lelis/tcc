"""Ingestão de CSV no DuckDB (RF01) e atualização de tabelas (RF10).

Cada CSV vira uma tabela. Os nomes de tabela e de colunas são normalizados
(minúsculas, sem acento, com "_") para que o SQL gerado pelo modelo não
precise lidar com espaços e acentos.

Este é o único componente que abre o banco em modo de escrita. As consultas
geradas pelo modelo passam pelo executor, que abre o banco somente leitura.
"""
import csv
import re
import tempfile
import threading
import unicodedata
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from app import config
from app.models.tabela import Coluna, ResultadoIngestao, TabelaInfo

# DuckDB permite um único processo escrevendo no arquivo; o lock evita que
# duas requisições da API abram conexões de escrita ao mesmo tempo.
trava_banco = threading.Lock()

_DELIMITADORES = ",;\t|"
_DECIMAL_COM_VIRGULA = re.compile(r"^-?\d+,\d+$")


class ErroIngestao(ValueError):
    """CSV que não pôde ser carregado (vazio, sem cabeçalho, nome inválido...)."""


# ---------------------------------------------------------------- nomes

def normalizar_nome(texto: str) -> str:
    """'Data Criação' -> 'data_criacao'. Garante um identificador SQL simples."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    nome = re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")
    if not nome:
        raise ErroIngestao(f"Nome inválido: {texto!r}")
    if nome[0].isdigit():
        nome = f"t_{nome}"
    return nome


def _nomes_unicos(originais: list[str]) -> list[str]:
    """Normaliza cabeçalhos e resolve repetidos: 'Valor', 'valor' -> valor, valor_2."""
    vistos: dict[str, int] = {}
    resultado = []
    for original in originais:
        base = normalizar_nome(original)
        vistos[base] = vistos.get(base, 0) + 1
        resultado.append(base if vistos[base] == 1 else f"{base}_{vistos[base]}")
    return resultado


def _citar(identificador: str) -> str:
    return '"' + identificador.replace('"', '""') + '"'


# ---------------------------------------------------------------- leitura do CSV

def _texto_utf8(conteudo: bytes) -> str:
    """CSVs exportados no Brasil muitas vezes vêm em Latin-1 (Excel)."""
    for codificacao in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return conteudo.decode(codificacao)
        except UnicodeDecodeError:
            continue
    raise ErroIngestao("Codificação do arquivo não reconhecida.")


def _opcoes_leitura(texto: str) -> dict[str, str]:
    """Detecta o separador e, para CSV com ';', a vírgula decimal (padrão brasileiro)."""
    amostra = "\n".join(texto.splitlines()[:50])
    try:
        delimitador = csv.Sniffer().sniff(amostra, delimiters=_DELIMITADORES).delimiter
    except csv.Error:
        delimitador = ","
    opcoes = {"delim": delimitador}
    if delimitador != ",":
        campos = (c.strip().strip('"') for linha in csv.reader(amostra.splitlines()[1:], delimiter=delimitador) for c in linha)
        if any(_DECIMAL_COM_VIRGULA.match(c) for c in campos):
            opcoes["decimal_separator"] = ","
    return opcoes


def para_json(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (date, datetime, time)):
        return valor.isoformat()
    return valor


# ---------------------------------------------------------------- metadados

def _colunas_atuais(con: duckdb.DuckDBPyConnection, tabela: str) -> dict[str, str]:
    linhas = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'main' AND table_name = ? ORDER BY ordinal_position",
        [tabela],
    ).fetchall()
    return dict(linhas)


def _info(con: duckdb.DuckDBPyConnection, tabela: str, nomes_originais: dict[str, str] | None = None) -> TabelaInfo:
    tipos = _colunas_atuais(con, tabela)
    nomes_originais = nomes_originais or _ler_nomes_originais(con, tabela)
    linhas = con.execute(f"SELECT COUNT(*) FROM {_citar(tabela)}").fetchone()[0]
    cursor = con.execute(f"SELECT * FROM {_citar(tabela)} LIMIT ?", [config.LINHAS_AMOSTRA])
    cabecalho = [d[0] for d in cursor.description]
    amostra = [{c: para_json(v) for c, v in zip(cabecalho, linha)} for linha in cursor.fetchall()]
    return TabelaInfo(
        nome=tabela,
        colunas=[Coluna(nome=n, nome_original=nomes_originais.get(n, n), tipo=t) for n, t in tipos.items()],
        linhas=linhas,
        amostra=amostra,
    )


def _gravar_nomes_originais(con: duckdb.DuckDBPyConnection, tabela: str, mapa: dict[str, str]) -> None:
    """Guarda o cabeçalho original como comentário de cada coluna, dentro do próprio banco."""
    for nome, original in mapa.items():
        texto = original.replace("'", "''")  # COMMENT não aceita parâmetro "?"
        con.execute(f"COMMENT ON COLUMN {_citar(tabela)}.{_citar(nome)} IS '{texto}'")


def _ler_nomes_originais(con: duckdb.DuckDBPyConnection, tabela: str) -> dict[str, str]:
    linhas = con.execute(
        "SELECT column_name, comment FROM duckdb_columns() WHERE table_name = ? AND comment IS NOT NULL",
        [tabela],
    ).fetchall()
    return dict(linhas)


# ---------------------------------------------------------------- API do serviço

def ingerir_csv(conteudo: bytes, nome_arquivo: str, nome_tabela: str | None = None,
                caminho_banco: Path | None = None) -> ResultadoIngestao:
    """Carrega um CSV como tabela. Se a tabela já existe, substitui e informa o que mudou (RF10)."""
    caminho_banco = caminho_banco or config.BANCO_DUCKDB
    tabela = normalizar_nome(nome_tabela or Path(nome_arquivo).stem)

    texto = _texto_utf8(conteudo)
    if not texto.strip():
        raise ErroIngestao("O arquivo está vazio.")
    opcoes = _opcoes_leitura(texto)

    with tempfile.TemporaryDirectory() as pasta_tmp:
        arquivo = Path(pasta_tmp) / "entrada.csv"
        arquivo.write_bytes(texto.encode("utf-8"))  # bytes: sem conversão de fim de linha no Windows
        args = ", ".join(f"{k} = '{v}'" for k, v in opcoes.items())
        caminho_sql = arquivo.as_posix().replace("'", "''")
        leitura = f"read_csv('{caminho_sql}', header = true, sample_size = -1, {args})"

        caminho_banco.parent.mkdir(parents=True, exist_ok=True)
        with trava_banco, duckdb.connect(str(caminho_banco)) as con:
            try:
                nomes_duckdb = [linha[0] for linha in con.execute(f"DESCRIBE SELECT * FROM {leitura}").fetchall()]
            except duckdb.Error as erro:
                raise ErroIngestao(f"Não foi possível ler o CSV: {erro}") from erro

            # O DuckDB já renomeia cabeçalhos repetidos ("valor" -> "valor_1"); para guardar
            # o original de verdade, lemos o cabeçalho direto do arquivo.
            cabecalho = next(csv.reader([texto.splitlines()[0]], delimiter=opcoes["delim"]))
            originais = [c.strip() for c in cabecalho] if len(cabecalho) == len(nomes_duckdb) else nomes_duckdb

            normalizados = _nomes_unicos(originais)
            anteriores = _colunas_atuais(con, tabela)
            selecao = ", ".join(f"{_citar(d)} AS {_citar(n)}" for d, n in zip(nomes_duckdb, normalizados))
            con.execute(f"CREATE OR REPLACE TABLE {_citar(tabela)} AS SELECT {selecao} FROM {leitura}")

            mapa = dict(zip(normalizados, originais))
            _gravar_nomes_originais(con, tabela, mapa)
            info = _info(con, tabela, mapa)

    atuais = {c.nome: c.tipo for c in info.colunas}
    return ResultadoIngestao(
        tabela=info,
        nova=not anteriores,
        colunas_novas=[c for c in atuais if anteriores and c not in anteriores],
        colunas_removidas=[c for c in anteriores if c not in atuais],
        colunas_tipo_alterado=[c for c in atuais if c in anteriores and anteriores[c] != atuais[c]],
    )


def listar_tabelas(caminho_banco: Path | None = None) -> list[TabelaInfo]:
    caminho_banco = caminho_banco or config.BANCO_DUCKDB
    if not caminho_banco.exists():
        return []
    with trava_banco, duckdb.connect(str(caminho_banco), read_only=True) as con:
        nomes = [n for (n,) in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
        ).fetchall()]
        return [_info(con, n) for n in nomes]


def descrever_tabela(nome: str, caminho_banco: Path | None = None) -> TabelaInfo | None:
    return next((t for t in listar_tabelas(caminho_banco) if t.nome == nome), None)


def remover_tabela(nome: str, caminho_banco: Path | None = None) -> bool:
    caminho_banco = caminho_banco or config.BANCO_DUCKDB
    if not caminho_banco.exists():
        return False
    with trava_banco, duckdb.connect(str(caminho_banco)) as con:
        existia = bool(_colunas_atuais(con, nome))
        con.execute(f"DROP TABLE IF EXISTS {_citar(nome)}")
        return existia
