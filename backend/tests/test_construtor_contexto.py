"""Testes do construtor de contexto (RF06): C0, C1 e C2."""
import pytest

from app.models.contexto import Contexto, DescricaoTabela, Regra
from app.services.construtor_contexto import instrucoes_gerais, montar_contexto, montar_prompt
from app.services.ingestao import ingerir_csv, listar_tabelas
from tests.conftest import PASTA_EXEMPLO

PERGUNTA = "Quantas vendas houve em março de 2026?"


@pytest.fixture
def tabelas_exemplo(csv_exemplo):
    for nome in ("vendedores", "clientes", "reunioes", "contratos"):
        ingerir_csv(csv_exemplo(nome), f"{nome}.csv")
    return listar_tabelas()


@pytest.fixture
def contexto_exemplo():
    return Contexto.model_validate_json((PASTA_EXEMPLO / "contexto_exemplo.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- diferença entre configurações

def test_c0_tem_esquema_e_amostra_mas_nenhum_contexto(tabelas_exemplo, contexto_exemplo):
    c0 = montar_contexto("C0", tabelas_exemplo, contexto_exemplo)
    assert "CREATE TABLE contratos (" in c0
    assert "  status VARCHAR," in c0
    assert "/* Amostra (3 de 254 linhas):" in c0
    assert "--" not in c0  # nem descrição, nem regra


def test_c1_acrescenta_descricoes_mas_nao_regras(tabelas_exemplo, contexto_exemplo):
    c1 = montar_contexto("C1", tabelas_exemplo, contexto_exemplo)
    assert "CREATE TABLE contratos (  -- Contratos enviados a clientes." in c1
    assert "  status VARCHAR,  -- E = enviado (aguardando assinatura), A = assinado, C = cancelado." in c1
    assert "Regras de negócio" not in c1


def test_c2_acrescenta_todas_as_regras_numeradas(tabelas_exemplo, contexto_exemplo):
    c2 = montar_contexto("C2", tabelas_exemplo, contexto_exemplo)
    assert "-- Regras de negócio e definições de métricas:" in c2
    assert "-- 1. Regra: Venda é um contrato" in c2
    assert "-- 3. Métrica: Receita = valor - desconto" in c2
    assert c2.count("-- ") - montar_contexto("C1", tabelas_exemplo, contexto_exemplo).count("-- ") == 7  # cabeçalho + 6


def test_configuracoes_sao_cumulativas(tabelas_exemplo, contexto_exemplo):
    c0, c1, c2 = (montar_contexto(c, tabelas_exemplo, contexto_exemplo) for c in ("C0", "C1", "C2"))
    assert len(c0) < len(c1) < len(c2)
    assert c2.startswith(c1)  # C2 = C1 + regras


def test_amostra_usa_null_e_booleano_do_sql(tabelas_exemplo, contexto_exemplo):
    c0 = montar_contexto("C0", tabelas_exemplo, contexto_exemplo)
    assert "1 | Diego Moraes | SDR | true" in c0
    assert "| 2026-09-21 | NULL" in c0


def test_coluna_sem_descricao_fica_sem_comentario(tabelas_exemplo, contexto_exemplo):
    c1 = montar_contexto("C1", tabelas_exemplo, contexto_exemplo)
    assert "  id BIGINT,\n" in c1  # "id" não tem descrição no contexto de exemplo


def test_c2_sem_regras_e_igual_ao_c1(tabelas_exemplo, contexto_exemplo):
    sem_regras = contexto_exemplo.model_copy(update={"regras": []})
    assert montar_contexto("C2", tabelas_exemplo, sem_regras) == montar_contexto("C1", tabelas_exemplo, sem_regras)


# ---------------------------------------------------------------- prompt completo

def test_instrucoes_sao_identicas_nas_tres_configuracoes(tabelas_exemplo, contexto_exemplo):
    prompts = [montar_prompt(PERGUNTA, c, tabelas_exemplo, contexto_exemplo) for c in ("C0", "C1", "C2")]
    assert {p.sistema for p in prompts} == {instrucoes_gerais()}
    assert len({p.hash_prompt for p in prompts}) == 3
    assert len({p.hash_contexto for p in prompts}) == 1


def test_pergunta_vem_no_fim(tabelas_exemplo, contexto_exemplo):
    prompt = montar_prompt(f"  {PERGUNTA}\n", "C2", tabelas_exemplo, contexto_exemplo)
    assert prompt.usuario.startswith("Esquema do banco de dados:")
    assert prompt.usuario.endswith(f"Pergunta: {PERGUNTA}")


def test_prompt_e_deterministico(tabelas_exemplo, contexto_exemplo):
    a = montar_prompt(PERGUNTA, "C1", tabelas_exemplo, contexto_exemplo)
    b = montar_prompt(PERGUNTA, "C1", list(reversed(tabelas_exemplo)), contexto_exemplo)
    assert a == b  # a ordem das tabelas não importa


def test_sem_tabelas_e_erro(contexto_exemplo):
    with pytest.raises(ValueError):
        montar_prompt(PERGUNTA, "C0", [], contexto_exemplo)


# ---------------------------------------------------------------- textos que poderiam quebrar o SQL

def test_textos_problematicos_sao_neutralizados():
    ingerir_csv(b"obs\n\"fecha */ comentario\"\n", "t.csv")
    contexto = Contexto(
        tabelas={"t": DescricaoTabela(descricao="linha 1\nlinha 2", colunas={"obs": "a\n  b"})},
        regras=[Regra(id=1, texto="regra\ncom quebra")],
    )
    c2 = montar_contexto("C2", listar_tabelas(), contexto)
    assert "*/ comentario" not in c2
    assert "-- linha 1 linha 2" in c2
    assert "-- a b" in c2
    assert "-- 1. Regra: regra com quebra" in c2
