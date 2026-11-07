"""Relatórios ao vivo.

Os testes de API precisam de Postgres e MinIO de verdade e só rodam com
DATA_TALK_TESTE_INTEGRACAO=1 (ver README). Os demais rodam sempre.
"""
import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app
from app.models.registro import Execucao
from app.models.relatorio import Bloco, Relatorio
from app.models.resposta import SugestaoGrafico
from app.services import armazenamento, pdf_relatorio, registro, relatorios
from app.services.erros_relatorio import ErroEntrada, ErroIndisponivel

integracao = pytest.mark.skipif(
    not os.getenv("DATA_TALK_TESTE_INTEGRACAO"), reason="precisa de Postgres e MinIO",
)
SQL = "SELECT count(*) AS total FROM contratos"
SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"><rect width="100" height="50" fill="#1560e0"/></svg>'


@pytest.fixture
def cliente():
    return TestClient(app)


@pytest.fixture
def execucao():
    """Uma resposta bem-sucedida gravada no registro de uso, como faria o fluxo."""
    item = Execucao(
        id="exec-teste-1", quando=datetime.now(timezone.utc), origem="interface", pergunta="Quantos contratos?",
        configuracao="C2", modelo="falso", esforco=None, hash_contexto="a", hash_prompt="b", prompt_sistema="s",
        prompt_usuario="u", sql=SQL, grafico_sugerido=SugestaoGrafico(tipo="indicador", y=["total"]),
        status="sucesso", tempo_total_ms=1, versao_codigo="teste",
    )
    registro.registrar(item)
    return item


@pytest.fixture
def com_tabela(cliente, csv_exemplo):
    resposta = cliente.post("/tabelas", files={"arquivo": ("contratos.csv", csv_exemplo("contratos"), "text/csv")})
    assert resposta.status_code < 300


def novo(cliente, titulo="Teste"):
    return cliente.post("/relatorios", json={"titulo": titulo}).json()


def anexar(cliente, relatorio_id, execucao_id="exec-teste-1"):
    return cliente.post(f"/relatorios/{relatorio_id}/anexos", json={
        "execucao_id": execucao_id, "texto": "Texto do assistente", "colunas": ["total"], "linhas": [[1]],
    })


def editar(cliente, relatorio, **mudancas):
    corpo = {"titulo": relatorio["titulo"], "blocos": relatorio["blocos"], "revisao": relatorio["revisao"], **mudancas}
    return cliente.put(f"/relatorios/{relatorio['id']}", json=corpo)


# ---------------------------------------------------------------- sem serviços externos

@pytest.mark.parametrize("svg", [
    "<script>alert(1)</script>",
    '<svg><image href="file:///etc/passwd"/></svg>',
    '<svg><use xlink:href="http://exemplo.com/a.svg#b"/></svg>',
    '<!DOCTYPE svg [<!ENTITY a "b">]><svg></svg>',
    '<svg onload="alert(1)"></svg>',
    "<svg>" + "a" * pdf_relatorio.LIMITE_SVG,
])
def test_svg_perigoso_e_recusado(svg):
    with pytest.raises(ErroEntrada):
        pdf_relatorio.validar_svg(svg)


def test_html_do_pdf_escapa_o_texto_da_pessoa():
    agora = datetime.now(timezone.utc)
    relatorio = Relatorio(id="1", titulo="<b>t</b>", revisao=1, criado_em=agora, atualizado_em=agora, blocos=[
        Bloco(id="a", tipo="texto", texto='<img src="file:///etc/passwd">'),
    ])
    html = pdf_relatorio.montar_html(relatorio, {}, 1)
    assert "<b>t</b>" not in html and '<img src="file' not in html


def test_tabela_grande_avisa_o_corte_no_pdf():
    bloco = Bloco(id="a", tipo="resultado", visao="tabela", colunas=["n"], linhas=[[i] for i in range(100)])
    assert f"mostrando {config.LINHAS_TABELA_PDF} de 100 linhas" in pdf_relatorio._origem(bloco)


def test_sem_postgres_so_os_relatorios_param(cliente, monkeypatch):
    monkeypatch.setattr(config, "URL_POSTGRES", "postgresql://x:y@127.0.0.1:1/z")
    monkeypatch.setattr(relatorios, "_esquema_pronto", False)
    assert cliente.get("/relatorios").status_code == 503
    assert cliente.get("/saude").status_code == 200
    assert cliente.get("/tabelas").status_code == 200


# ---------------------------------------------------------------- com Postgres e MinIO

@integracao
def test_edita_e_guarda_os_blocos(cliente):
    relatorio = novo(cliente)
    blocos = [{"id": "a", "tipo": "titulo", "texto": "Vendas"}, {"id": "b", "tipo": "texto", "texto": "Olá"}]
    editado = editar(cliente, relatorio, titulo="Mensal", blocos=blocos).json()
    relido = cliente.get(f"/relatorios/{relatorio['id']}").json()
    assert relido["titulo"] == "Mensal"
    assert [b["texto"] for b in relido["blocos"]] == ["Vendas", "Olá"]
    assert editado["revisao"] == relatorio["revisao"] + 1


@integracao
def test_aba_antiga_nao_apaga_trabalho_novo(cliente):
    relatorio = novo(cliente)
    assert editar(cliente, relatorio, titulo="Nova").status_code == 200
    assert editar(cliente, relatorio, titulo="Velha").status_code == 409
    assert cliente.get(f"/relatorios/{relatorio['id']}").json()["titulo"] == "Nova"


@integracao
def test_anexo_nao_expoe_o_sql(cliente, execucao):
    resposta = anexar(cliente, novo(cliente)["id"])
    assert resposta.status_code == 201
    assert SQL not in resposta.text
    assert resposta.json()["blocos"][0]["pergunta"] == "Quantos contratos?"


@integracao
def test_anexo_de_execucao_desconhecida(cliente):
    assert anexar(cliente, novo(cliente)["id"], "nao-existe").status_code == 404


@integracao
def test_resultado_nao_nasce_por_edicao(cliente):
    relatorio = novo(cliente)
    falso = [{"id": "x", "tipo": "resultado", "colunas": ["a"], "linhas": [[1]]}]
    assert editar(cliente, relatorio, blocos=falso).status_code == 422


@integracao
def test_atualizar_usa_o_sql_do_servidor_e_nao_registra_execucao(cliente, execucao, com_tabela):
    relatorio = anexar(cliente, novo(cliente)["id"]).json()
    bloco = relatorio["blocos"][0]
    # o navegador tenta trocar a consulta: o campo é ignorado
    bloco["sql"] = "SELECT 999 AS total"
    relatorio = editar(cliente, relatorio).json()

    antes = len(registro.ler(registro.caminho_registro("interface")))
    atualizado = cliente.post(f"/relatorios/{relatorio['id']}/blocos/{bloco['id']}/atualizar")
    assert atualizado.status_code == 200
    novo_bloco = atualizado.json()["blocos"][0]
    assert novo_bloco["linhas"][0][0] != 999
    assert novo_bloco["texto"] == "Texto do assistente"  # o texto da pessoa não muda
    assert novo_bloco["dados_em"] > bloco["dados_em"]
    assert len(registro.ler(registro.caminho_registro("interface"))) == antes


@integracao
def test_atualizar_informa_quando_a_tabela_sumiu(cliente, execucao):
    relatorio = anexar(cliente, novo(cliente)["id"]).json()
    bloco = relatorio["blocos"][0]
    resposta = cliente.post(f"/relatorios/{relatorio['id']}/blocos/{bloco['id']}/atualizar")
    assert resposta.status_code == 409
    assert "Não consegui atualizar" in resposta.json()["detail"]


@integracao
def test_remover_bloco_apaga_a_consulta(cliente, execucao):
    relatorio = anexar(cliente, novo(cliente)["id"]).json()
    bloco = relatorio["blocos"][0]
    relatorio = editar(cliente, relatorio, blocos=[]).json()
    resposta = cliente.post(f"/relatorios/{relatorio['id']}/blocos/{bloco['id']}/atualizar")
    assert resposta.status_code == 404


@integracao
def test_cada_exportacao_vira_uma_versao_no_s3(cliente, execucao):
    relatorio = anexar(cliente, novo(cliente, "Vendas de março")["id"]).json()
    bloco = relatorio["blocos"][0]["id"]
    rota = f"/relatorios/{relatorio['id']}/versoes"

    primeira = cliente.post(rota, json={"graficos": {bloco: [SVG]}})
    segunda = cliente.post(rota, json={"graficos": {bloco: [SVG]}})
    assert (primeira.status_code, segunda.status_code) == (201, 201)
    assert [v["numero"] for v in cliente.get(rota).json()] == [2, 1]

    pdf = cliente.get(f"{rota}/1/pdf")
    assert pdf.content.startswith(b"%PDF")
    assert "vendas-de-marco-v1.pdf" in pdf.headers["content-disposition"]


@integracao
def test_exportar_vazio_e_recusado(cliente):
    relatorio = novo(cliente)
    assert cliente.post(f"/relatorios/{relatorio['id']}/versoes", json={}).status_code == 422


@integracao
def test_svg_perigoso_nao_vira_versao(cliente, execucao):
    relatorio = anexar(cliente, novo(cliente)["id"]).json()
    bloco = relatorio["blocos"][0]["id"]
    rota = f"/relatorios/{relatorio['id']}/versoes"
    resposta = cliente.post(rota, json={"graficos": {bloco: ['<svg><image href="file:///etc/passwd"/></svg>']}})
    assert resposta.status_code == 422
    assert cliente.get(rota).json() == []


@integracao
def test_excluir_apaga_os_pdfs(cliente, execucao):
    relatorio = anexar(cliente, novo(cliente)["id"]).json()
    rota = f"/relatorios/{relatorio['id']}"
    cliente.post(f"{rota}/versoes", json={})
    assert cliente.delete(rota).status_code == 204
    assert cliente.get(rota).status_code == 404
    with pytest.raises(ErroIndisponivel):
        armazenamento.ler(f"relatorios/{relatorio['id']}/v1.pdf")
