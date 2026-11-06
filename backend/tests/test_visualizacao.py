"""Testes do gerador de visualização (RF09, Seção 3.6, D-19)."""
from app.models.resposta import ResultadoConsulta, SugestaoGrafico
from app.services.visualizacao import montar_grafico


def _r(colunas, tipos, linhas):
    return ResultadoConsulta(sql="", colunas=colunas, tipos=tipos, linhas=linhas, truncado=False, tempo_ms=0)


def _valores(g):
    return {s.nome: s.valores for s in g.series}


UM_VALOR = _r(["vendas"], ["BIGINT"], [[12]])
DOIS_NUMEROS = _r(["vendas", "receita"], ["BIGINT", "DOUBLE"], [[12, 98575.0]])
POR_MES = _r(["mes", "vendas"], ["DATE", "BIGINT"], [["2026-02-01", 10], ["2026-01-01", 8], ["2026-03-01", 12]])
POR_MES_TEXTO = _r(["mes", "vendas"], ["VARCHAR", "BIGINT"], [["2026-01", 8], ["2026-02", 10]])
POR_CLOSER = _r(["closer", "vendas"], ["VARCHAR", "BIGINT"], [["Ana", 5], ["Bia", 9], ["Caio", 7]])
SO_TEXTO = _r(["nome", "uf"], ["VARCHAR", "VARCHAR"], [["Ana", "DF"]])
VAZIO = _r(["vendas"], ["BIGINT"], [])

# o caso da captura: "Quantas reuniões cada SDR marcou por mês?" (formato longo)
REUNIOES_SDR = _r(
    ["mes", "sdr", "reunioes"], ["DATE", "VARCHAR", "BIGINT"],
    [["2026-01-01", "Diego", 9], ["2026-01-01", "João", 4], ["2026-01-01", "Pedro", 9],
     ["2026-02-01", "Diego", 2], ["2026-02-01", "João", 7], ["2026-02-01", "Pedro", 7],
     ["2026-03-01", "Diego", 5], ["2026-03-01", "João", 7]],  # Pedro sem registro em março
)


# ---------------------------------------------------------------- formato longo (o caso da captura)

def test_formato_longo_vira_uma_linha_por_grupo_mesmo_se_o_modelo_errar():
    sugestao_do_modelo = SugestaoGrafico(tipo="barra", x="mes", y=["reunioes"])  # o que veio na captura
    g = montar_grafico(sugestao_do_modelo, REUNIOES_SDR)

    assert (g.tipo, g.origem, g.x, g.serie) == ("linha", "regra", "mes", "sdr")
    assert g.categorias == ["2026-01-01", "2026-02-01", "2026-03-01"]  # 3 meses, não 8 barras
    assert _valores(g)["Pedro"] == [9.0, 7.0, None]  # sem registro = sem ponto (não zero)
    assert [s.nome for s in g.series] == ["João", "Diego", "Pedro"]  # do maior total (18) para o menor (16, 16)


def test_formato_longo_com_serie_indicada_pelo_modelo_e_aceito():
    s = SugestaoGrafico(tipo="linha", x="mes", y=["reunioes"], serie="sdr")
    g = montar_grafico(s, REUNIOES_SDR)
    assert (g.origem, g.serie, len(g.series)) == ("modelo", "sdr", 3)


def test_barras_agrupadas_sem_tempo():
    r = _r(["segmento", "uf", "clientes"], ["VARCHAR", "VARCHAR", "BIGINT"],
           [["Saúde", "DF", 3], ["Saúde", "SP", 2], ["Varejo", "DF", 5], ["Varejo", "SP", 1], ["Indústria", "DF", 4]])
    g = montar_grafico(SugestaoGrafico(tipo="tabela"), r)
    assert g.tipo == "tabela"  # sugestão "tabela" do modelo é respeitada
    g = montar_grafico(SugestaoGrafico(tipo="barra", x="segmento", y=["clientes"]), r)
    assert (g.tipo, g.origem, g.x, g.serie) == ("barra", "regra", "segmento", "uf")  # 3 segmentos > 2 UFs
    assert _valores(g)["SP"] == [2.0, 1.0, None]


def test_mais_de_oito_grupos_vai_para_a_tabela_com_motivo():
    linhas = [["2026-01-01", f"v{i}", i] for i in range(9)]
    g = montar_grafico(SugestaoGrafico(tipo="linha", x="mes", y=["n"], serie="vendedor"),
                       _r(["mes", "vendedor", "n"], ["DATE", "VARCHAR", "BIGINT"], linhas))
    assert g.tipo == "tabela" and "9 grupos" in g.motivo


# ---------------------------------------------------------------- uma série

def test_linha_no_tempo_ordenada_por_data():
    g = montar_grafico(SugestaoGrafico(tipo="linha", x="mes", y=["vendas"]), POR_MES)
    assert (g.tipo, g.origem) == ("linha", "modelo")
    assert g.categorias == ["2026-01-01", "2026-02-01", "2026-03-01"]
    assert _valores(g) == {"vendas": [8.0, 10.0, 12.0]}


def test_mes_em_texto_conta_como_tempo():
    assert montar_grafico(SugestaoGrafico(tipo="linha", x="mes", y=["vendas"]), POR_MES_TEXTO).origem == "modelo"


def test_ranking_ordenado_do_maior_para_o_menor():
    g = montar_grafico(SugestaoGrafico(tipo="barra", x="closer", y=["vendas"]), POR_CLOSER)
    assert g.categorias == ["Bia", "Caio", "Ana"] and _valores(g) == {"vendas": [9.0, 7.0, 5.0]}
    assert g.orientacao == "vertical"


def test_ranking_com_muitas_categorias_ou_nomes_longos_fica_horizontal():
    muitas = _r(["closer", "vendas"], ["VARCHAR", "BIGINT"], [[f"c{i}", i] for i in range(9)])
    longos = _r(["closer", "vendas"], ["VARCHAR", "BIGINT"], [["Gabriela Queiroz", 37], ["Vinícius Lacerda", 37]])
    assert montar_grafico(SugestaoGrafico(tipo="barra", x="closer", y=["vendas"]), muitas).orientacao == "horizontal"
    assert montar_grafico(SugestaoGrafico(tipo="barra", x="closer", y=["vendas"]), longos).orientacao == "horizontal"


def test_ano_inteiro_e_dimensao_de_tempo_e_nao_medida():
    r = _r(["ano", "vendas"], ["INTEGER", "BIGINT"], [[2025, 100], [2026, 169]])
    g = montar_grafico(SugestaoGrafico(tipo="tabela"), r)
    g = montar_grafico(SugestaoGrafico(tipo="indicador", y=["ano"]), r)  # sugestão ruim
    assert (g.tipo, g.x, g.y) == ("linha", "ano", ["vendas"])


# ---------------------------------------------------------------- várias medidas

def test_medidas_de_escalas_parecidas_dividem_o_grafico():
    r = _r(["mes", "reunioes", "vendas"], ["DATE", "BIGINT", "BIGINT"], [["2026-01-01", 40, 14], ["2026-02-01", 35, 8]])
    g = montar_grafico(SugestaoGrafico(tipo="linha", x="mes", y=["reunioes", "vendas"]), r)
    assert len(g.series) == 2 and not g.escalas_separadas


def test_medidas_de_escalas_muito_diferentes_ganham_graficos_separados():
    r = _r(["mes", "vendas", "receita"], ["DATE", "BIGINT", "DOUBLE"], [["2026-01-01", 14, 91745.0], ["2026-02-01", 8, 57967.5]])
    g = montar_grafico(SugestaoGrafico(tipo="linha", x="mes", y=["vendas", "receita"]), r)
    assert g.escalas_separadas  # nunca dois eixos y


# ---------------------------------------------------------------- indicadores

def test_um_valor_vira_indicador():
    g = montar_grafico(SugestaoGrafico(tipo="indicador", y=["vendas"]), UM_VALOR)
    assert (g.tipo, g.origem) == ("indicador", "modelo")
    assert [(i.rotulo, i.valor) for i in g.indicadores] == [("vendas", 12)]


def test_varios_numeros_numa_linha_viram_indicadores():
    g = montar_grafico(SugestaoGrafico(tipo="barra", x="vendas", y=["receita"]), DOIS_NUMEROS)
    assert (g.tipo, g.origem) == ("indicador", "regra")
    assert [i.rotulo for i in g.indicadores] == ["vendas", "receita"]


# ---------------------------------------------------------------- sugestões inválidas e tabela

def test_coluna_inexistente_cai_na_regra():
    g = montar_grafico(SugestaoGrafico(tipo="barra", x="vendedor", y=["total"]), POR_CLOSER)
    assert (g.tipo, g.x, g.origem) == ("barra", "closer", "regra")


def test_linha_sem_tempo_vira_barra():
    g = montar_grafico(SugestaoGrafico(tipo="linha", x="closer", y=["vendas"]), POR_CLOSER)
    assert (g.tipo, g.origem) == ("barra", "regra")


def test_eixo_y_de_texto_e_invalido():
    assert montar_grafico(SugestaoGrafico(tipo="barra", x="vendas", y=["closer"]), POR_CLOSER).origem == "regra"


def test_sem_medida_vira_tabela():
    g = montar_grafico(SugestaoGrafico(tipo="barra", x="nome", y=["uf"]), SO_TEXTO)
    assert (g.tipo, g.origem) == ("tabela", "regra") and g.motivo


def test_resultado_vazio_vira_tabela():
    assert montar_grafico(SugestaoGrafico(tipo="indicador", y=["vendas"]), VAZIO).tipo == "tabela"


def test_id_numerico_nao_e_medida():
    r = _r(["cliente_id", "contratos"], ["BIGINT", "BIGINT"], [[1, 3], [2, 5]])
    g = montar_grafico(SugestaoGrafico(tipo="tabela"), r)
    g = montar_grafico(SugestaoGrafico(tipo="indicador", y=["cliente_id"]), r)
    assert (g.tipo, g.x, g.y) == ("barra", "cliente_id", ["contratos"])
