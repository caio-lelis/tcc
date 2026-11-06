"""Testes do repositório de contexto (RF02, RF03) e das pendências (RF10)."""
import pytest

from app import config
from app.models.contexto import DescricaoTabela, RegraEntrada
from app.services import repositorio
from app.services.ingestao import ingerir_csv, remover_tabela


@pytest.fixture
def contratos():
    ingerir_csv(b"id,status,data_assinatura\n1,A,2026-03-10\n", "contratos.csv")


# ---------------------------------------------------------------- descrições

def test_contexto_vazio_sem_arquivo():
    assert repositorio.carregar().tabelas == {}
    assert repositorio.listar_regras() == []


def test_define_descricao_e_persiste_em_arquivo(contratos):
    repositorio.definir_descricao("contratos", DescricaoTabela(
        descricao="um registro por contrato", colunas={"status": "E, A ou C"}))

    assert config.ARQUIVO_CONTEXTO.exists()
    salvo = repositorio.carregar().tabelas["contratos"]
    assert salvo.descricao == "um registro por contrato"
    assert salvo.colunas == {"status": "E, A ou C"}


def test_colunas_sao_mescladas_e_vazio_apaga(contratos):
    repositorio.definir_descricao("contratos", DescricaoTabela(colunas={"status": "s", "id": "i"}))
    repositorio.definir_descricao("contratos", DescricaoTabela(colunas={"status": "novo", "id": "  "}))

    assert repositorio.carregar().tabelas["contratos"].colunas == {"status": "novo"}


def test_rejeita_tabela_ou_coluna_inexistente(contratos):
    with pytest.raises(repositorio.ErroContexto, match="não existe"):
        repositorio.definir_descricao("vendas", DescricaoTabela(descricao="x"))
    with pytest.raises(repositorio.ErroContexto, match="valor"):
        repositorio.definir_descricao("contratos", DescricaoTabela(colunas={"valor": "x"}))


# ---------------------------------------------------------------- regras

def test_crud_de_regras(contratos):
    r1 = repositorio.adicionar_regra(RegraEntrada(texto="  Venda = contrato assinado. ", tabelas=["contratos"]))
    r2 = repositorio.adicionar_regra(RegraEntrada(texto="Receita = valor - desconto", tipo="metrica"))
    assert (r1.id, r2.id) == (1, 2)
    assert r1.texto == "Venda = contrato assinado."

    repositorio.atualizar_regra(1, RegraEntrada(texto="Venda pela data de assinatura"))
    repositorio.remover_regra(2)
    assert [(r.id, r.texto) for r in repositorio.listar_regras()] == [(1, "Venda pela data de assinatura")]

    r3 = repositorio.adicionar_regra(RegraEntrada(texto="outra"))
    assert r3.id == 2  # id = maior existente + 1


def test_regra_inexistente_ou_tabela_inexistente(contratos):
    with pytest.raises(repositorio.ErroContexto):
        repositorio.atualizar_regra(99, RegraEntrada(texto="x"))
    with pytest.raises(repositorio.ErroContexto):
        repositorio.remover_regra(99)
    with pytest.raises(repositorio.ErroContexto, match="vendas"):
        repositorio.adicionar_regra(RegraEntrada(texto="x", tabelas=["vendas"]))


# ---------------------------------------------------------------- pendências (RF10)

def test_pendencias_de_tabela_nova(contratos):
    p = repositorio.obter_completo().pendencias
    assert p.tabelas_sem_descricao == ["contratos"]
    assert p.colunas_sem_descricao == {"contratos": ["id", "status", "data_assinatura"]}


def test_reanexar_csv_preserva_descricoes_e_aponta_novas_e_orfas(contratos):
    repositorio.definir_descricao("contratos", DescricaoTabela(
        descricao="contratos", colunas={"id": "i", "status": "s", "data_assinatura": "d"}))

    # nova versão do CSV: sai "status", entra "desconto"
    ingerir_csv(b"id,data_assinatura,desconto\n1,2026-03-10,0\n", "contratos.csv")

    completo = repositorio.obter_completo()
    assert completo.contexto.tabelas["contratos"].colunas["status"] == "s"  # preservada
    assert completo.pendencias.colunas_sem_descricao == {"contratos": ["desconto"]}
    assert completo.pendencias.colunas_orfas == {"contratos": ["status"]}


def test_tabela_removida_vira_orfa(contratos):
    repositorio.definir_descricao("contratos", DescricaoTabela(descricao="x"))
    remover_tabela("contratos")
    assert repositorio.obter_completo().pendencias.tabelas_orfas == ["contratos"]


# ---------------------------------------------------------------- hash (RNF02)

def test_hash_muda_com_o_conteudo_e_e_estavel(contratos):
    h_vazio = repositorio.obter_completo().hash
    repositorio.adicionar_regra(RegraEntrada(texto="regra"))
    h1 = repositorio.obter_completo().hash
    h2 = repositorio.obter_completo().hash

    assert h1 != h_vazio
    assert h1 == h2 and len(h1) == 12
