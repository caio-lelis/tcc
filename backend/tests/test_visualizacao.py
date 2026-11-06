"""Testes da conferência do gráfico (RF09, Seção 3.6)."""
from app.models.resposta import ResultadoConsulta, SugestaoGrafico
from app.services.visualizacao import montar_grafico


def _r(colunas, tipos, linhas):
    return ResultadoConsulta(sql="", colunas=colunas, tipos=tipos, linhas=linhas, truncado=False, tempo_ms=0)


UM_VALOR = _r(["vendas"], ["BIGINT"], [[12]])
POR_MES_DATA = _r(["mes", "vendas"], ["DATE", "BIGINT"], [["2026-01-01", 8], ["2026-02-01", 10], ["2026-03-01", 12]])
POR_MES_TEXTO = _r(["mes", "vendas"], ["VARCHAR", "BIGINT"], [["2026-01", 8], ["2026-02", 10]])
POR_CLOSER = _r(["closer", "vendas", "receita"], ["VARCHAR", "BIGINT", "DOUBLE"], [["Ana", 5, 1000.0], ["Bia", 7, 2000.5]])
SO_TEXTO = _r(["nome", "uf"], ["VARCHAR", "VARCHAR"], [["Ana", "DF"]])
VAZIO = _r(["vendas"], ["BIGINT"], [])


# ---------------------------------------------------------------- sugestão do modelo aceita

def test_aceita_indicador_sugerido():
    g = montar_grafico(SugestaoGrafico(tipo="indicador", y=["vendas"]), UM_VALOR)
    assert (g.tipo, g.origem) == ("indicador", "modelo")
    assert g.indicador == {"rotulo": "vendas", "valor": 12}
    assert g.echarts is None


def test_aceita_linha_com_data_e_gera_echarts_interativo():
    g = montar_grafico(SugestaoGrafico(tipo="linha", x="mes", y=["vendas"]), POR_MES_DATA)
    assert (g.tipo, g.origem) == ("linha", "modelo")
    e = g.echarts
    assert e["xAxis"]["data"] == ["2026-01-01", "2026-02-01", "2026-03-01"]
    assert e["series"] == [{"name": "vendas", "type": "line", "data": [8, 10, 12]}]
    assert e["tooltip"]["trigger"] == "axis" and e["dataZoom"] and e["legend"]["data"] == ["vendas"]


def test_mes_em_texto_conta_como_tempo():
    g = montar_grafico(SugestaoGrafico(tipo="linha", x="mes", y=["vendas"]), POR_MES_TEXTO)
    assert (g.tipo, g.origem) == ("linha", "modelo")


def test_aceita_barra_com_duas_series():
    g = montar_grafico(SugestaoGrafico(tipo="barra", x="closer", y=["vendas", "receita"]), POR_CLOSER)
    assert g.origem == "modelo"
    assert [s["type"] for s in g.echarts["series"]] == ["bar", "bar"]


def test_tabela_sugerida_e_sempre_aceita():
    g = montar_grafico(SugestaoGrafico(tipo="tabela"), POR_CLOSER)
    assert (g.tipo, g.origem, g.echarts) == ("tabela", "modelo", None)


# ---------------------------------------------------------------- sugestão inválida -> regras

def test_coluna_inexistente_cai_na_regra():
    g = montar_grafico(SugestaoGrafico(tipo="barra", x="vendedor", y=["total"]), POR_CLOSER)
    assert (g.tipo, g.x, g.y, g.origem) == ("barra", "closer", ["vendas", "receita"], "regra")


def test_linha_sem_coluna_de_tempo_vira_barra():
    g = montar_grafico(SugestaoGrafico(tipo="linha", x="closer", y=["vendas"]), POR_CLOSER)
    assert (g.tipo, g.origem) == ("barra", "regra")


def test_indicador_com_varias_linhas_vira_linha_no_tempo():
    g = montar_grafico(SugestaoGrafico(tipo="indicador", y=["vendas"]), POR_MES_DATA)
    assert (g.tipo, g.x, g.origem) == ("linha", "mes", "regra")


def test_eixo_y_de_texto_e_invalido():
    g = montar_grafico(SugestaoGrafico(tipo="barra", x="vendas", y=["closer"]), POR_CLOSER)
    assert g.origem == "regra"


def test_regra_um_valor_vira_indicador():
    g = montar_grafico(SugestaoGrafico(tipo="linha", x="x", y=["y"]), UM_VALOR)
    assert (g.tipo, g.origem) == ("indicador", "regra")


def test_sem_coluna_numerica_vira_tabela():
    g = montar_grafico(SugestaoGrafico(tipo="barra", x="nome", y=["uf"]), SO_TEXTO)
    assert (g.tipo, g.origem) == ("tabela", "regra")


def test_resultado_vazio_vira_tabela():
    g = montar_grafico(SugestaoGrafico(tipo="indicador", y=["vendas"]), VAZIO)
    assert g.tipo == "tabela"
