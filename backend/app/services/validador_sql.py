"""Validador de SQL (RNF01): primeira camada de proteção.

Aceita apenas UM comando, e ele precisa ser de leitura (SELECT, incluindo
WITH ... SELECT, UNION, FROM ... e DESCRIBE/SUMMARIZE de consultas).

A análise usa o parser do PRÓPRIO DuckDB (D-14), sem executar nada. Assim o
validador e o executor nunca discordam sobre o que é SQL válido: um parser
externo poderia recusar uma consulta que o DuckDB executaria normalmente,
e isso apareceria no experimento como erro do modelo.

A segunda camada (conexão somente leitura e sem acesso a arquivos) fica no
executor e protege mesmo que algo passe por aqui.
"""
import duckdb

from app.models.resposta import FalhaConsulta

_ACEITOS = {duckdb.StatementType.SELECT}


def validar(sql: str) -> str:
    """Devolve o SQL pronto para executar ou levanta FalhaConsulta."""
    texto = (sql or "").strip().rstrip(";").strip()
    if not texto:
        raise FalhaConsulta("recusada", "Nenhuma consulta foi gerada.")

    try:
        comandos = duckdb.connect(":memory:").extract_statements(texto)
    except duckdb.ParserException as erro:
        raise FalhaConsulta("invalida", f"Erro de sintaxe: {erro}") from erro

    if len(comandos) != 1:
        raise FalhaConsulta("recusada", f"Esperado um único comando; recebidos {len(comandos)}.")
    tipo = comandos[0].type
    if tipo not in _ACEITOS:
        raise FalhaConsulta("recusada", f"Apenas consultas de leitura são permitidas (recebido: {tipo.name}).")
    return texto
