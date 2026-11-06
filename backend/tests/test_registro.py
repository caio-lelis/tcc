"""Testes do registro de execuções (RNF02)."""
import json
from datetime import date, datetime, timezone

import pytest

from app import config
from app.models.registro import Execucao, ResultadoRegistrado, UsoRegistrado
from app.models.resposta import SugestaoGrafico, UsoModelo
from app.services import registro


def _execucao(**mudancas) -> Execucao:
    base = dict(
        id="e1", quando=datetime(2026, 11, 6, 18, 30, tzinfo=timezone.utc), origem="interface",
        pergunta="Quantas vendas houve em março?", configuracao="C2",
        modelo="gpt-5.6-terra", esforco="low", hash_contexto="ctx", hash_prompt="prm",
        prompt_sistema="instruções", prompt_usuario="esquema + pergunta",
        sql="SELECT 12 AS vendas", grafico_sugerido=SugestaoGrafico(tipo="indicador", y=["vendas"]),
        status="sucesso", resultado=ResultadoRegistrado(colunas=["vendas"], linhas=[[12]], truncado=False),
        tempo_consulta_ms=1.5, texto="Foram 12 vendas em março.",
        uso=UsoRegistrado(geracao=UsoModelo(modelo="gpt-5.6-terra", tokens_entrada=1361, tokens_saida=103,
                                            custo_usd=0.004, tempo_ms=1800)),
        custo_total_usd=0.004, tempo_total_ms=4120, versao_codigo="abc1234",
    )
    return Execucao(**{**base, **mudancas})


def test_registra_e_le_de_volta_sem_perder_nada():
    arquivo = registro.registrar(_execucao())
    lidas = registro.ler(arquivo)
    assert lidas == [_execucao()]


def test_acrescenta_uma_linha_por_execucao_com_acentos_legiveis():
    arquivo = registro.registrar(_execucao(id="e1"))
    registro.registrar(_execucao(id="e2"))

    linhas = arquivo.read_text(encoding="utf-8").splitlines()
    assert [json.loads(l)["id"] for l in linhas] == ["e1", "e2"]
    assert "março" in linhas[0]  # sem ç no arquivo


def test_caminho_da_interface_e_por_dia():
    caminho = registro.caminho_registro("interface", dia=date(2026, 11, 20))
    assert caminho == config.PASTA_EXECUCOES / "uso" / "2026-11-20.jsonl"


def test_caminho_do_experimento_e_por_rodada():
    assert registro.caminho_registro("experimento", "Piloto 01").name == "piloto_01.jsonl"
    with pytest.raises(ValueError):
        registro.caminho_registro("experimento")


def test_execucao_do_experimento_vai_para_o_arquivo_da_rodada():
    execucao = _execucao(origem="experimento", rodada="oficial-01", pergunta_id="P07", repeticao=2)
    arquivo = registro.registrar(execucao)
    assert arquivo.name == "oficial_01.jsonl"
    assert registro.ler(arquivo)[0].repeticao == 2


def test_falha_registrada_sem_resultado():
    falha = _execucao(status="recusada", erro="Apenas consultas de leitura", resultado=None, texto=None)
    lida = registro.ler(registro.registrar(falha))[0]
    assert lida.status == "recusada" and lida.resultado is None


def test_ler_arquivo_inexistente():
    assert registro.ler(config.PASTA_EXECUCOES / "nada.jsonl") == []


def test_versao_do_codigo():
    versao = registro.versao_codigo()
    assert versao == "desconhecida" or len(versao.split("-")[0]) >= 7
