"""Gerador de visualização (RF09, Seção 3.6).

O modelo sugere um gráfico na chamada de geração, ANTES de conhecer o
resultado. A sugestão pode citar colunas que não existem ou não combinar com
os dados, então ela é conferida contra as colunas efetivamente retornadas.

Se a sugestão for inválida, valem as regras simples da Seção 3.6:
  um único valor numérico           -> indicador
  coluna de tempo + coluna numérica -> linha (evolução no tempo)
  coluna de texto + coluna numérica -> barra
  qualquer outro caso               -> tabela

A saída inclui a configuração do Apache ECharts (um objeto JSON), com zoom,
valores ao passar o cursor e legenda para ocultar séries (RF09).
"""
import re
from typing import Any

from app.models.resposta import GraficoFinal, ResultadoConsulta, SugestaoGrafico

_NUMERICOS = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT",
              "UINTEGER", "UBIGINT", "UHUGEINT", "FLOAT", "DOUBLE", "REAL", "DECIMAL")
_TEMPORAIS = ("DATE", "TIMESTAMP", "TIME")
_PARECE_DATA = re.compile(r"^\d{4}-\d{2}(-\d{2})?")  # 2026-03, 2026-03-01, 2026-03-01T...


# ---------------------------------------------------------------- tipos de coluna

def _eh_numerica(tipo: str) -> bool:
    return tipo.upper().startswith(_NUMERICOS)


def _eh_temporal(resultado: ResultadoConsulta, coluna: str) -> bool:
    tipo = resultado.tipos[resultado.colunas.index(coluna)].upper()
    if tipo.startswith(_TEMPORAIS):
        return True
    # meses agregados costumam vir como texto ('2026-03'): também contam como tempo
    valores = [linha[resultado.colunas.index(coluna)] for linha in resultado.linhas]
    return bool(valores) and all(isinstance(v, str) and _PARECE_DATA.match(v) for v in valores if v is not None)


def _numericas(resultado: ResultadoConsulta) -> list[str]:
    return [c for c, t in zip(resultado.colunas, resultado.tipos) if _eh_numerica(t)]


# ---------------------------------------------------------------- conferência

def _sugestao_valida(s: SugestaoGrafico, r: ResultadoConsulta) -> bool:
    if not r.linhas:
        return s.tipo == "tabela"
    numericas = set(_numericas(r))
    if s.tipo == "tabela":
        return True
    if not s.y or not set(s.y) <= numericas:
        return False
    if s.tipo == "indicador":
        return len(r.linhas) == 1 and len(s.y) == 1
    if s.x not in r.colunas or s.x in s.y:
        return False
    if s.tipo == "linha":
        return _eh_temporal(r, s.x)
    return True  # barra: qualquer coluna no eixo x


def _por_regra(r: ResultadoConsulta) -> SugestaoGrafico:
    numericas = _numericas(r)
    if not r.linhas or not numericas:
        return SugestaoGrafico(tipo="tabela")
    if len(r.linhas) == 1 and len(r.colunas) == 1:
        return SugestaoGrafico(tipo="indicador", y=numericas[:1])
    outras = [c for c in r.colunas if c not in numericas]
    temporais = [c for c in outras if _eh_temporal(r, c)]
    if temporais:
        return SugestaoGrafico(tipo="linha", x=temporais[0], y=numericas)
    if outras:
        return SugestaoGrafico(tipo="barra", x=outras[0], y=numericas)
    return SugestaoGrafico(tipo="tabela")


# ---------------------------------------------------------------- ECharts

def _coluna(r: ResultadoConsulta, nome: str) -> list[Any]:
    i = r.colunas.index(nome)
    return [linha[i] for linha in r.linhas]


def _echarts(tipo: str, x: str, y: list[str], r: ResultadoConsulta) -> dict[str, Any]:
    serie = "line" if tipo == "linha" else "bar"
    opcao: dict[str, Any] = {
        "tooltip": {"trigger": "axis"},  # valores ao passar o cursor
        "legend": {"data": y},  # clicar na legenda oculta a série
        "xAxis": {"type": "category", "name": x, "data": [str(v) for v in _coluna(r, x)]},
        "yAxis": {"type": "value"},
        "series": [{"name": c, "type": serie, "data": _coluna(r, c)} for c in y],
        "dataZoom": [{"type": "inside"}, {"type": "slider"}],  # aproximar regiões
    }
    return opcao


def montar_grafico(sugestao: SugestaoGrafico, resultado: ResultadoConsulta) -> GraficoFinal:
    if _sugestao_valida(sugestao, resultado):
        escolhido, origem = sugestao, "modelo"
    else:
        escolhido, origem = _por_regra(resultado), "regra"

    grafico = GraficoFinal(tipo=escolhido.tipo, x=escolhido.x, y=escolhido.y, origem=origem)
    if escolhido.tipo in ("linha", "barra"):
        grafico.echarts = _echarts(escolhido.tipo, escolhido.x, escolhido.y, resultado)
    elif escolhido.tipo == "indicador":
        grafico.indicador = {"rotulo": escolhido.y[0], "valor": _coluna(resultado, escolhido.y[0])[0]}
    return grafico
