"""Testes das rotas /contexto, /tabelas/{nome}/descricao e /regras."""
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def _anexar(csv_exemplo, nome):
    cliente.post("/tabelas", files={"arquivo": (f"{nome}.csv", csv_exemplo(nome))})


def test_fluxo_de_contexto(csv_exemplo):
    _anexar(csv_exemplo, "vendedores")

    resposta = cliente.put("/tabelas/vendedores/descricao", json={
        "descricao": "pessoas do time comercial",
        "colunas": {"equipe": "SDR agenda reuniões; CLOSER fecha contratos"},
    })
    assert resposta.status_code == 200

    regra = cliente.post("/regras", json={"texto": "Vendas são do closer.", "tabelas": ["vendedores"]})
    assert regra.status_code == 201 and regra.json()["id"] == 1

    completo = cliente.get("/contexto").json()
    assert completo["contexto"]["tabelas"]["vendedores"]["descricao"] == "pessoas do time comercial"
    assert completo["pendencias"]["colunas_sem_descricao"]["vendedores"] == ["id", "nome", "ativo"]
    assert len(completo["hash"]) == 12

    assert cliente.put("/regras/1", json={"texto": "Vendas e receita são do closer."}).status_code == 200
    assert cliente.delete("/regras/1").status_code == 204
    assert cliente.get("/regras").json() == []


def test_erros(csv_exemplo):
    _anexar(csv_exemplo, "vendedores")
    assert cliente.put("/tabelas/nada/descricao", json={"descricao": "x"}).status_code == 404
    assert cliente.put("/tabelas/vendedores/descricao", json={"colunas": {"cpf": "x"}}).status_code == 422
    assert cliente.post("/regras", json={"texto": ""}).status_code == 422
    assert cliente.post("/regras", json={"texto": "x", "tipo": "outro"}).status_code == 422
    assert cliente.delete("/regras/42").status_code == 404
