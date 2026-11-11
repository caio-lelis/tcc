"""Testes da regra de acerto (Seção 4.6.3)."""
from app.services.comparacao import comparar


def test_mesmas_linhas_em_outra_ordem_sao_iguais():
    assert comparar([["DF", 24], ["SP", 14]], [["SP", 14], ["DF", 24]]).igual


def test_nomes_e_ordem_das_colunas_nao_importam():
    assert comparar([["DF", 24], ["SP", 14]], [[14, "SP"], [24, "DF"]]).igual


def test_tolerancia_numerica_de_um_centavo():
    assert comparar([[115787.5]], [[115787.504]]).igual
    assert comparar([[0.30]], [[0.29]]).igual  # 0.01 exato, apesar do ponto flutuante
    assert not comparar([[115787.5]], [[115787.52]]).igual


def test_tolerancia_nao_atrapalha_a_ordenacao_das_linhas():
    esperado = [[1.004, "a"], [1.006, "b"]]
    obtido = [[1.007, "b"], [1.003, "a"]]
    assert comparar(esperado, obtido).igual


def test_valor_diferente_reprova():
    assert not comparar([[13]], [[15]]).igual
    assert not comparar([["DF", 24]], [["DF", 23]]).igual


def test_numero_de_linhas_diferente_reprova():
    assert not comparar([[1], [2]], [[1]]).igual
    assert not comparar([[1]], []).igual


def test_linhas_repetidas_contam():
    assert not comparar([[1], [1], [2]], [[1], [2], [2]]).igual
    assert comparar([[1], [1], [2]], [[2], [1], [1]]).igual


def test_dois_resultados_vazios_sao_iguais():
    assert comparar([], []).igual


def test_nulos_textos_e_booleanos():
    assert comparar([[None, "a"]], [["a", None]]).igual
    assert not comparar([[None]], [[0]]).igual
    assert not comparar([["12"]], [[12]]).igual
    assert not comparar([[True]], [[1]]).igual
    assert comparar([[True]], [[True]]).igual


def test_pergunta_ordenada_exige_a_ordem():
    esperado = [["Diego", 300.0], ["Pedro", 200.0]]
    assert comparar(esperado, [[300.0, "Diego"], [200.0, "Pedro"]], ordenada=True).igual

    invertido = comparar(esperado, [["Pedro", 200.0], ["Diego", 300.0]], ordenada=True)
    assert not invertido.igual and "outra ordem" in invertido.limitrofe


def test_colunas_a_mais_reprovam_mas_pedem_revisao():
    r = comparar([["Diego", 300.0]], [[6, "Diego", 300.0]])
    assert not r.igual and "mais 1" in r.limitrofe


def test_colunas_a_mais_com_valores_errados_reprovam_sem_revisao():
    r = comparar([["Diego", 300.0]], [[6, "Diego", 999.0]])
    assert not r.igual and r.limitrofe is None


def test_colunas_a_menos_reprovam():
    r = comparar([["Diego", 300.0]], [["Diego"]])
    assert not r.igual and r.limitrofe is None


def test_resultado_cortado_reprova_e_pede_revisao():
    r = comparar([[1]], [[1]], truncado=True)
    assert not r.igual and "cortado" in r.limitrofe


def test_colunas_com_os_mesmos_valores_sao_casadas_pela_linha():
    # as duas colunas têm os valores {1, 2}: só o casamento por linha decide
    assert comparar([[1, 2], [2, 1]], [[2, 1], [1, 2]]).igual
    assert not comparar([[1, 2], [2, 1]], [[1, 1], [2, 2]]).igual
