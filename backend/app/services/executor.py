"""Executor (RNF01, RNF04): roda a consulta validada no DuckDB.

Segunda camada de proteção: a conexão é aberta
- somente leitura (read_only): o banco recusa qualquer escrita;
- sem acesso externo (enable_external_access = false): nenhuma função
  consegue ler arquivos do computador ou da rede;
- com a configuração travada (lock_configuration): a consulta não consegue
  religar o acesso externo.

Limites (RNF04): no máximo config.LIMITE_LINHAS linhas devolvidas (avisando
quando cortou) e no máximo config.LIMITE_SEGUNDOS segundos de execução.
"""
import threading
import time

import duckdb

from app import config
from app.models.resposta import FalhaConsulta, ResultadoConsulta
from app.services.ingestao import para_json, trava_banco
from app.services.validador_sql import validar

_CONFIG_SEGURA = {"enable_external_access": False, "lock_configuration": True}


def conectar_leitura() -> duckdb.DuckDBPyConnection:
    if not config.BANCO_DUCKDB.exists():
        raise FalhaConsulta("invalida", "Nenhuma tabela foi anexada ainda.")
    return duckdb.connect(str(config.BANCO_DUCKDB), read_only=True, config=_CONFIG_SEGURA)


def executar(sql: str) -> ResultadoConsulta:
    """Valida e executa. Levanta FalhaConsulta (recusada, invalida ou tempo_esgotado)."""
    texto = validar(sql)
    limite = config.LIMITE_LINHAS

    with trava_banco, conectar_leitura() as con:
        cronometro = threading.Timer(config.LIMITE_SEGUNDOS, con.interrupt)
        inicio = time.perf_counter()
        cronometro.start()
        try:
            cursor = con.execute(texto)
            linhas = cursor.fetchmany(limite + 1)
        except duckdb.PermissionException as erro:
            raise FalhaConsulta("recusada", f"Acesso não permitido: {erro}") from erro
        except duckdb.InterruptException as erro:
            raise FalhaConsulta("tempo_esgotado", f"A consulta passou de {config.LIMITE_SEGUNDOS} s.") from erro
        except duckdb.Error as erro:
            raise FalhaConsulta("invalida", str(erro)) from erro
        finally:
            cronometro.cancel()
        tempo_ms = (time.perf_counter() - inicio) * 1000

        descricao = cursor.description or []

    return ResultadoConsulta(
        sql=texto,
        colunas=[d[0] for d in descricao],
        tipos=[str(d[1]) for d in descricao],
        linhas=[[para_json(v) for v in linha] for linha in linhas[:limite]],
        truncado=len(linhas) > limite,
        tempo_ms=round(tempo_ms, 2),
    )
