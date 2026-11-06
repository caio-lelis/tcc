"""Testes do validador de SQL e do executor (RNF01, RNF04)."""
import duckdb
import pytest

from app import config
from app.models.resposta import FalhaConsulta
from app.services.executor import conectar_leitura, executar
from app.services.ingestao import ingerir_csv
from app.services.validador_sql import validar
from tests.conftest import PASTA_EXEMPLO


def _categoria(funcao, sql):
    with pytest.raises(FalhaConsulta) as erro:
        funcao(sql)
    return erro.value.categoria


@pytest.fixture
def contratos(csv_exemplo):
    ingerir_csv(csv_exemplo("contratos"), "contratos.csv")


# ---------------------------------------------------------------- validador: aceita leitura

@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "select count(*) from contratos;",
    "WITH v AS (SELECT * FROM contratos) SELECT COUNT(*) FROM v",
    "SELECT 1 UNION ALL SELECT 2",
    "FROM contratos LIMIT 1",
    "  SELECT 1 ;  ",
])
def test_aceita_consultas_de_leitura(sql):
    assert validar(sql) == sql.strip().rstrip(";").strip()


# ---------------------------------------------------------------- validador: recusa (D-13)

@pytest.mark.parametrize("sql", [
    "DELETE FROM contratos",
    "UPDATE contratos SET valor = 0",
    "INSERT INTO contratos VALUES (1)",
    "DROP TABLE contratos",
    "CREATE TABLE x AS SELECT 1",
    "ALTER TABLE contratos ADD COLUMN x INT",
    "COPY contratos TO 'saida.csv'",
    "ATTACH 'outro.duckdb'",
    "INSTALL httpfs",
    "SET threads = 1",
    "PRAGMA version",
    "EXPLAIN SELECT 1",
    "SELECT 1; DROP TABLE contratos",
    "",
    "   ;  ",
])
def test_recusa_o_que_nao_e_uma_unica_leitura(sql):
    assert _categoria(validar, sql) == "recusada"


def test_erro_de_sintaxe_e_invalida_e_nao_recusada():
    assert _categoria(validar, "SELEC * FROM contratos") == "invalida"


# ---------------------------------------------------------------- executor

def test_executa_e_devolve_colunas_tipos_e_linhas(contratos):
    r = executar("SELECT status, COUNT(*) AS total FROM contratos GROUP BY status ORDER BY status")
    assert r.colunas == ["status", "total"]
    assert r.tipos == ["VARCHAR", "BIGINT"]
    assert r.linhas == [["A", 150], ["C", 47], ["E", 57]]
    assert not r.truncado and r.tempo_ms >= 0


def test_exemplo_ancora_da_regra_de_negocio(contratos):
    """As três leituras de 'quantas vendas em março?' (docs/decisoes.md)."""
    ingenua = executar("SELECT COUNT(*) FROM contratos WHERE data_criacao BETWEEN '2026-03-01' AND '2026-03-31'")
    por_status = executar("SELECT COUNT(*) FROM contratos WHERE status = 'A' "
                          "AND data_criacao BETWEEN '2026-03-01' AND '2026-03-31'")
    pela_regra = executar("SELECT COUNT(*) FROM contratos WHERE data_assinatura BETWEEN '2026-03-01' AND '2026-03-31' "
                          "AND NOT (data_cancelamento IS NOT NULL "
                          "AND date_diff('day', data_assinatura, data_cancelamento) <= 7)")
    assert (ingenua.linhas, por_status.linhas, pela_regra.linhas) == ([[20]], [[9]], [[12]])


def test_datas_saem_como_texto(contratos):
    r = executar("SELECT data_criacao FROM contratos WHERE id = 1")
    assert r.linhas == [["2026-04-18"]]


def test_corta_no_limite_de_linhas_e_avisa(contratos, monkeypatch):
    monkeypatch.setattr(config, "LIMITE_LINHAS", 10)
    r = executar("SELECT id FROM contratos ORDER BY id")
    assert len(r.linhas) == 10 and r.truncado
    assert r.linhas[-1] == [10]

    exato = executar("SELECT id FROM contratos ORDER BY id LIMIT 10")
    assert not exato.truncado


def test_interrompe_consulta_demorada(contratos, monkeypatch):
    monkeypatch.setattr(config, "LIMITE_SEGUNDOS", 0.2)
    sql = "SELECT COUNT(*) FROM range(100000000) a, range(100000) b WHERE (a.range * b.range) % 7 = 3"
    assert _categoria(executar, sql) == "tempo_esgotado"


def test_tabela_ou_coluna_inexistente_e_invalida(contratos):
    assert _categoria(executar, "SELECT * FROM vendas") == "invalida"
    assert _categoria(executar, "SELECT receita FROM contratos") == "invalida"


def test_sem_banco_e_invalida():
    assert _categoria(executar, "SELECT 1") == "invalida"


# ---------------------------------------------------------------- segunda camada

def test_leitura_de_arquivo_e_recusada_pelo_banco(contratos):
    """Passa no validador (é um SELECT), mas o banco bloqueia o acesso a arquivos."""
    caminho = (PASTA_EXEMPLO / "clientes.csv").as_posix()
    assert _categoria(executar, f"SELECT * FROM read_csv('{caminho}')") == "recusada"
    assert _categoria(executar, f"SELECT * FROM '{caminho}'") == "recusada"


def test_conexao_e_somente_leitura_e_travada(contratos):
    with conectar_leitura() as con:
        with pytest.raises(duckdb.Error):
            con.execute("CREATE TABLE invasora (a INT)")
        with pytest.raises(duckdb.Error):
            con.execute("SET enable_external_access = true")
