"""Testes da ingestão de CSV (RF01) e da atualização de tabelas (RF10)."""
import pytest

from app.services.ingestao import (
    ErroIngestao, descrever_tabela, ingerir_csv, listar_tabelas, normalizar_nome, remover_tabela,
)


# ---------------------------------------------------------------- nomes

@pytest.mark.parametrize("entrada, esperado", [
    ("Data Criação", "data_criacao"),
    ("  Valor (R$) ", "valor_r"),
    ("Situação/Etapa", "situacao_etapa"),
    ("2026_vendas", "t_2026_vendas"),
    ("contratos", "contratos"),
])
def test_normaliza_nomes(entrada, esperado):
    assert normalizar_nome(entrada) == esperado


def test_rejeita_nome_sem_caracteres_validos():
    with pytest.raises(ErroIngestao):
        normalizar_nome("###")


# ---------------------------------------------------------------- ingestão

def test_ingere_csv_do_modelo_de_partida(csv_exemplo):
    resultado = ingerir_csv(csv_exemplo("contratos"), "contratos.csv")

    tabela = resultado.tabela
    assert resultado.nova
    assert tabela.nome == "contratos"
    assert tabela.linhas == 254
    tipos = {c.nome: c.tipo for c in tabela.colunas}
    assert tipos["id"] == "BIGINT"
    assert tipos["data_assinatura"] == "DATE"
    assert tipos["status"] == "VARCHAR"
    assert tipos["valor"] == "DOUBLE"


def test_amostra_tem_tamanho_configurado_e_vira_json(csv_exemplo):
    tabela = ingerir_csv(csv_exemplo("contratos"), "contratos.csv").tabela
    assert len(tabela.amostra) == 3
    assert tabela.amostra[0]["data_criacao"] == "2026-04-18"  # data vira texto ISO
    assert tabela.amostra[1]["data_cancelamento"] is None


def test_normaliza_cabecalhos_e_guarda_o_original():
    conteudo = "Código,Data Criação,Valor Total\n1,2026-03-01,10.5\n".encode()
    tabela = ingerir_csv(conteudo, "Vendas do Mês.csv").tabela

    assert tabela.nome == "vendas_do_mes"
    assert [c.nome for c in tabela.colunas] == ["codigo", "data_criacao", "valor_total"]
    assert [c.nome_original for c in tabela.colunas] == ["Código", "Data Criação", "Valor Total"]


def test_cabecalhos_repetidos_ganham_sufixo():
    tabela = ingerir_csv(b"Valor,valor\n1,2\n", "t.csv").tabela
    assert [c.nome for c in tabela.colunas] == ["valor", "valor_2"]


def test_nome_da_tabela_pode_ser_informado():
    tabela = ingerir_csv(b"a\n1\n", "export_crm_20261106.csv", nome_tabela="Clientes").tabela
    assert tabela.nome == "clientes"


def test_csv_brasileiro_latin1_ponto_e_virgula_virgula_decimal():
    conteudo = "nome;valor;situação\nJosé;1234,56;ok\nAna;10,00;ok\n".encode("cp1252")
    tabela = ingerir_csv(conteudo, "br.csv").tabela

    tipos = {c.nome: c.tipo for c in tabela.colunas}
    assert tipos["valor"] == "DOUBLE"
    assert tabela.amostra[0] == {"nome": "José", "valor": 1234.56, "situacao": "ok"}


def test_data_com_fuso_horario_vira_texto_iso():
    # exportações de CRM costumam trazer o fuso; o DuckDB lê como TIMESTAMPTZ e precisa do pytz
    conteudo = b"id,criado_em\n1,2026-11-06 14:30:00-03:00\n"
    tabela = ingerir_csv(conteudo, "crm.csv").tabela

    tipos = {c.nome: c.tipo for c in tabela.colunas}
    assert tipos["criado_em"] == "TIMESTAMP WITH TIME ZONE"
    assert tabela.amostra[0]["criado_em"].startswith("2026-11-06")
    assert listar_tabelas()[0].amostra[0]["criado_em"] == tabela.amostra[0]["criado_em"]


def test_rejeita_arquivo_vazio():
    with pytest.raises(ErroIngestao):
        ingerir_csv(b"   \n", "vazio.csv")


# ---------------------------------------------------------------- atualização (RF10)

def test_reanexar_informa_colunas_novas_removidas_e_tipo_alterado():
    ingerir_csv(b"id,status,valor\n1,A,10\n", "contratos.csv")
    resultado = ingerir_csv(b"id,valor,desconto\n1,10.5,0\n2,20,1\n", "contratos.csv")

    assert not resultado.nova
    assert resultado.colunas_novas == ["desconto"]
    assert resultado.colunas_removidas == ["status"]
    assert resultado.colunas_tipo_alterado == ["valor"]  # BIGINT -> DOUBLE
    assert resultado.tabela.linhas == 2


def test_tabela_nova_nao_lista_colunas_novas():
    resultado = ingerir_csv(b"id\n1\n", "x.csv")
    assert resultado.nova and resultado.colunas_novas == []


# ---------------------------------------------------------------- consulta e remoção

def test_lista_descreve_e_remove(csv_exemplo):
    for nome in ("clientes", "vendedores"):
        ingerir_csv(csv_exemplo(nome), f"{nome}.csv")

    assert [t.nome for t in listar_tabelas()] == ["clientes", "vendedores"]
    assert descrever_tabela("vendedores").linhas == 8
    assert descrever_tabela("inexistente") is None

    assert remover_tabela("clientes")
    assert not remover_tabela("clientes")
    assert [t.nome for t in listar_tabelas()] == ["vendedores"]


def test_lista_vazia_sem_banco():
    assert listar_tabelas() == []
