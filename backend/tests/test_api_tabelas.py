"""Testes das rotas /tabelas."""
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_saude():
    assert cliente.get("/saude").json() == {"status": "ok"}


def test_anexa_lista_detalha_e_remove(csv_exemplo):
    resposta = cliente.post("/tabelas", files={"arquivo": ("vendedores.csv", csv_exemplo("vendedores"), "text/csv")})
    assert resposta.status_code == 200
    assert resposta.json()["tabela"]["linhas"] == 8

    assert [t["nome"] for t in cliente.get("/tabelas").json()] == ["vendedores"]
    assert cliente.get("/tabelas/vendedores").json()["colunas"][2]["nome"] == "equipe"

    assert cliente.delete("/tabelas/vendedores").status_code == 204
    assert cliente.get("/tabelas/vendedores").status_code == 404


def test_nome_informado_no_formulario():
    resposta = cliente.post("/tabelas", files={"arquivo": ("export.csv", b"a\n1\n")}, data={"nome": "Metas"})
    assert resposta.json()["tabela"]["nome"] == "metas"


def test_csv_invalido_devolve_422():
    resposta = cliente.post("/tabelas", files={"arquivo": ("vazio.csv", b"")})
    assert resposta.status_code == 422
