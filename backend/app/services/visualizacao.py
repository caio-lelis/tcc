"""Gerador de visualização (RF09, Seção 3.6).

O modelo sugere um gráfico ANTES de conhecer o resultado (chamada de geração),
então a sugestão é conferida contra as colunas e os valores realmente
retornados. Se ela não servir, valem as regras abaixo (D-19):

  um número, ou poucos números numa linha só   -> indicador(es)
  tempo + medida(s)                            -> linha, uma série por medida
  tempo + grupo + medida  ("formato longo")    -> linha, uma série por grupo
  categoria + medida(s)                        -> barras (horizontais em rankings)
  categoria + grupo + medida                   -> barras agrupadas
  qualquer outro caso                          -> tabela

Regras de leitura que valem sempre:
- no máximo 8 séries no mesmo gráfico; mais do que isso as cores deixam de
  ser distinguíveis, e o resultado vai para a tabela;
- medidas de escalas muito diferentes nunca dividem o mesmo eixo: cada uma
  ganha o seu gráfico (nada de dois eixos y);
- rankings (barras sem tempo) são ordenados do maior para o menor e ficam
  horizontais quando há muitas categorias ou nomes longos.

O backend decide a forma e organiza os dados; o frontend só desenha.
"""
import re
from typing import Any

from app.models.resposta import GraficoFinal, Indicador, ResultadoConsulta, Serie, SugestaoGrafico

MAX_SERIES = 8
MAX_INDICADORES = 4
RAZAO_ESCALAS = 10  # maior/menor máximo entre medidas acima disso -> gráficos separados
CATEGORIAS_HORIZONTAL = 8
ROTULO_LONGO = 14

_NUMERICOS = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT",
              "UINTEGER", "UBIGINT", "UHUGEINT", "FLOAT", "DOUBLE", "REAL", "DECIMAL")
_TEMPORAIS = ("DATE", "TIMESTAMP", "TIME")
_PARECE_DATA = re.compile(r"^\d{4}-\d{2}(-\d{2})?")  # 2026-03, 2026-03-01, 2026-03-01T...
# colunas numéricas que são dimensão, não medida (ano = 2026 não se soma)
_NOME_DE_DIMENSAO = re.compile(r"(^|_)(ano|mes|dia|semana|trimestre|year|month|week|id)($|_)")


# ---------------------------------------------------------------- papéis das colunas

def _valores(r: ResultadoConsulta, coluna: str) -> list[Any]:
    i = r.colunas.index(coluna)
    return [linha[i] for linha in r.linhas]


def _eh_medida(r: ResultadoConsulta, coluna: str) -> bool:
    tipo = r.tipos[r.colunas.index(coluna)].upper()
    return tipo.startswith(_NUMERICOS) and not _NOME_DE_DIMENSAO.search(coluna.lower())


def _eh_temporal(r: ResultadoConsulta, coluna: str) -> bool:
    tipo = r.tipos[r.colunas.index(coluna)].upper()
    if tipo.startswith(_TEMPORAIS):
        return True
    valores = [v for v in _valores(r, coluna) if v is not None]
    if valores and all(isinstance(v, str) and _PARECE_DATA.match(v) for v in valores):
        return True  # meses agregados costumam vir como texto ('2026-03')
    return re.search(r"(^|_)(ano|year)($|_)", coluna.lower()) is not None


def _medidas(r: ResultadoConsulta) -> list[str]:
    return [c for c in r.colunas if _eh_medida(r, c)]


def _dimensoes(r: ResultadoConsulta) -> list[str]:
    return [c for c in r.colunas if not _eh_medida(r, c)]


def _distintos(valores: list[Any]) -> list[Any]:
    return list(dict.fromkeys(valores))


def _sem_repeticao(r: ResultadoConsulta, colunas: list[str]) -> bool:
    chaves = [tuple(linha[r.colunas.index(c)] for c in colunas) for linha in r.linhas]
    return len(chaves) == len(set(chaves))


# ---------------------------------------------------------------- sugestão do modelo

def _sugestao_valida(s: SugestaoGrafico, r: ResultadoConsulta) -> bool:
    if s.tipo == "tabela":
        return True
    medidas = set(_medidas(r))
    if not s.y or not set(s.y) <= medidas:
        return False
    if s.tipo == "indicador":
        return len(r.linhas) == 1 and len(s.y) <= MAX_INDICADORES
    if s.x not in r.colunas or s.x in s.y or _eh_medida(r, s.x):
        return False  # o eixo x é uma dimensão (tempo, categoria), nunca uma medida
    if s.serie is not None:
        if s.serie not in r.colunas or s.serie in (s.x, *s.y) or len(s.y) != 1:
            return False
        if not _sem_repeticao(r, [s.x, s.serie]):
            return False
    elif not _sem_repeticao(r, [s.x]):
        return False  # eixo x repetido sem grupo: formato longo não percebido pelo modelo
    if s.tipo == "linha" and not _eh_temporal(r, s.x):
        return False
    return True


# ---------------------------------------------------------------- regras

def _por_regra(r: ResultadoConsulta) -> SugestaoGrafico:
    medidas, dimensoes = _medidas(r), _dimensoes(r)
    if not medidas:
        return SugestaoGrafico(tipo="tabela")
    if len(r.linhas) == 1 and len(dimensoes) <= 1 and len(medidas) <= MAX_INDICADORES:
        return SugestaoGrafico(tipo="indicador", y=medidas)
    if len(dimensoes) == 1:
        x = dimensoes[0]
        return SugestaoGrafico(tipo="linha" if _eh_temporal(r, x) else "barra", x=x, y=medidas)
    if len(dimensoes) == 2 and len(medidas) == 1:
        temporais = [d for d in dimensoes if _eh_temporal(r, d)]
        if temporais:
            x = temporais[0]
        else:  # o eixo x fica com a dimensão de mais valores; o grupo, com a de menos
            x = max(dimensoes, key=lambda d: len(_distintos(_valores(r, d))))
        serie = next(d for d in dimensoes if d != x)
        return SugestaoGrafico(tipo="linha" if _eh_temporal(r, x) else "barra", x=x, y=medidas, serie=serie)
    return SugestaoGrafico(tipo="tabela")


# ---------------------------------------------------------------- construção

def _numero(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _rotulo(v: Any) -> str:
    return "—" if v is None else str(v)


def _tabela(origem: str, motivo: str | None = None) -> GraficoFinal:
    return GraficoFinal(tipo="tabela", origem=origem, motivo=motivo)


def _construir(s: SugestaoGrafico, r: ResultadoConsulta, origem: str) -> GraficoFinal:
    if s.tipo == "tabela":
        motivo = None if origem == "modelo" else "O resultado não tem um formato que um gráfico mostre melhor que a tabela."
        return _tabela(origem, motivo)

    if s.tipo == "indicador":
        linha = dict(zip(r.colunas, r.linhas[0]))
        return GraficoFinal(tipo="indicador", origem=origem, y=s.y,
                            indicadores=[Indicador(rotulo=c, valor=linha[c]) for c in s.y])

    temporal = _eh_temporal(r, s.x)
    xs = _distintos(_valores(r, s.x))
    if temporal:
        xs = sorted(xs, key=lambda v: (v is None, str(v)))
    posicao = {x: i for i, x in enumerate(xs)}

    if s.serie:
        grupos = _distintos(_valores(r, s.serie))
        if len(grupos) > MAX_SERIES:
            return _tabela(origem, f"São {len(grupos)} grupos; mais de {MAX_SERIES} cores no mesmo gráfico deixam de ser distinguíveis.")
        valores = {g: [None] * len(xs) for g in grupos}
        ix, ig, iy = (r.colunas.index(c) for c in (s.x, s.serie, s.y[0]))
        for linha in r.linhas:
            valores[linha[ig]][posicao[linha[ix]]] = _numero(linha[iy])
        total = lambda g: sum(v for v in valores[g] if v is not None)  # noqa: E731
        series = [Serie(nome=_rotulo(g), valores=valores[g]) for g in sorted(grupos, key=total, reverse=True)]
    else:
        if len(s.y) > MAX_SERIES:
            return _tabela(origem, f"São {len(s.y)} medidas; mais de {MAX_SERIES} no mesmo gráfico deixam de ser distinguíveis.")
        ix = r.colunas.index(s.x)
        series = []
        for c in s.y:  # valores na posição da sua categoria (o eixo de tempo pode ter sido reordenado)
            valores, ic = [None] * len(xs), r.colunas.index(c)
            for linha in r.linhas:
                valores[posicao[linha[ix]]] = _numero(linha[ic])
            series.append(Serie(nome=c, valores=valores))
        if not temporal and len(series) == 1:  # ranking: do maior para o menor
            ordem = sorted(range(len(xs)), key=lambda i: (series[0].valores[i] is None, -(series[0].valores[i] or 0)))
            xs = [xs[i] for i in ordem]
            series = [Serie(nome=series[0].nome, valores=[series[0].valores[i] for i in ordem])]

    categorias = [_rotulo(x) for x in xs]
    maximos = [max((abs(v) for v in serie.valores if v is not None), default=0) for serie in series]
    escalas_separadas = (not s.serie and len(series) > 1 and min(maximos) > 0
                         and max(maximos) / min(maximos) > RAZAO_ESCALAS)
    horizontal = (s.tipo == "barra" and not temporal and
                  (len(categorias) > CATEGORIAS_HORIZONTAL or max(map(len, categorias), default=0) > ROTULO_LONGO))

    return GraficoFinal(
        tipo=s.tipo, origem=origem, x=s.x, y=s.y, serie=s.serie,
        orientacao="horizontal" if horizontal else "vertical",
        categorias=categorias, series=series, escalas_separadas=escalas_separadas,
    )


def montar_grafico(sugestao: SugestaoGrafico, resultado: ResultadoConsulta) -> GraficoFinal:
    if not resultado.linhas:
        return _tabela("modelo" if sugestao.tipo == "tabela" else "regra")
    if _sugestao_valida(sugestao, resultado):
        return _construir(sugestao, resultado, "modelo")
    return _construir(_por_regra(resultado), resultado, "regra")
