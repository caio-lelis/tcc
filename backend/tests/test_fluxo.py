"""Testes do fluxo de uma pergunta (Seção 3.4, Figura 3) e da rota /perguntas.
O modelo é o ModeloFalso: nenhum teste chama a API."""
import pytest
from fastapi.testclient import TestClient

from app import config
from app.api.perguntas import obter_cliente
from app.main import app
from app.models.resposta import ErroModelo, SugestaoGrafico
from app.services import registro
from app.services.cliente_llm import ModeloFalso
from app.services.fluxo import responder
from app.services.ingestao import ingerir_csv
from tests.conftest import PASTA_EXEMPLO

PERGUNTA = "Quantas vendas houve em março de 2026?"
SQL_REGRA = ("SELECT COUNT(*) AS vendas FROM contratos WHERE data_assinatura BETWEEN '2026-03-01' AND '2026-03-31' "
             "AND NOT (data_cancelamento IS NOT NULL AND date_diff('day', data_assinatura, data_cancelamento) <= 7)")


@pytest.fixture
def cenario(csv_exemplo):
    """Modelo de partida anexado e contexto de exemplo cadastrado."""
    for nome in ("vendedores", "clientes", "reunioes", "contratos"):
        ingerir_csv(csv_exemplo(nome), f"{nome}.csv")
    config.ARQUIVO_CONTEXTO.write_text((PASTA_EXEMPLO / "contexto_exemplo.json").read_text(encoding="utf-8"),
                                       encoding="utf-8")


def _registradas():
    return [e for arquivo in sorted(config.PASTA_EXECUCOES.rglob("*.jsonl")) for e in registro.ler(arquivo)]


# ---------------------------------------------------------------- caminho feliz

def test_responde_com_texto_grafico_e_tabela(cenario):
    modelo = ModeloFalso(sql=SQL_REGRA, grafico=SugestaoGrafico(tipo="indicador", y=["vendas"]),
                         texto="Foram 12 vendas em março de 2026.")
    r = responder(PERGUNTA, modelo, "C2")

    assert r.status == "sucesso" and r.mensagem is None
    assert r.linhas == [[12]] and r.colunas == ["vendas"]
    assert r.grafico.tipo == "indicador" and r.grafico.indicador["valor"] == 12
    assert r.texto == "Foram 12 vendas em março de 2026."
    assert r.sql is None  # RF05: fora do modo avançado


def test_interpretacao_recebe_o_resultado_obtido(cenario):
    modelo = ModeloFalso(sql=SQL_REGRA)
    responder(PERGUNTA, modelo, "C2")
    pergunta, resultado = modelo.interpretacoes[0]
    assert pergunta == PERGUNTA and resultado.linhas == [[12]]


def test_modo_avancado_mostra_o_sql(cenario):
    r = responder(PERGUNTA, ModeloFalso(sql=SQL_REGRA), "C2", avancado=True)
    assert r.sql == SQL_REGRA


def test_configuracao_chega_ao_prompt(cenario):
    modelo = ModeloFalso(sql=SQL_REGRA)
    responder(PERGUNTA, modelo, "C0")
    responder(PERGUNTA, modelo, "C2")
    c0, c2 = modelo.prompts
    assert (c0.configuracao, c2.configuracao) == ("C0", "C2")
    assert "Regras de negócio" not in c0.usuario and "Regras de negócio" in c2.usuario


def test_configuracao_padrao(cenario, monkeypatch):
    monkeypatch.setattr(config, "CONFIGURACAO_PADRAO", "C1")
    assert responder(PERGUNTA, ModeloFalso(sql=SQL_REGRA)).configuracao == "C1"


# ---------------------------------------------------------------- registro (passo 8)

def test_registra_a_execucao_completa(cenario):
    r = responder(PERGUNTA, ModeloFalso(sql=SQL_REGRA), "C2")
    [e] = _registradas()

    assert e.id == r.id and e.origem == "interface" and e.status == "sucesso"
    assert e.configuracao == "C2" and e.sql == SQL_REGRA
    assert e.resultado.linhas == [[12]]
    assert len(e.hash_prompt) == len(e.hash_contexto) == 12
    assert "Pergunta: Quantas vendas" in e.prompt_usuario
    assert e.uso.geracao.modelo == "falso" and e.custo_total_usd == 0.0
    assert e.tempo_total_ms > 0 and e.versao_codigo


def test_execucao_do_experimento_vai_para_a_rodada(cenario):
    responder(PERGUNTA, ModeloFalso(sql=SQL_REGRA), "C1", origem="experimento",
              rodada="piloto", pergunta_id="P01", repeticao=3)
    e = registro.ler(config.PASTA_EXECUCOES / "piloto.jsonl")[0]
    assert (e.pergunta_id, e.repeticao, e.configuracao) == ("P01", 3, "C1")


# ---------------------------------------------------------------- falhas (sem nova tentativa)

def test_consulta_recusada_nao_e_executada_nem_interpretada(cenario):
    modelo = ModeloFalso(sql="DELETE FROM contratos")
    r = responder(PERGUNTA, modelo, "C2", avancado=True)

    assert r.status == "recusada" and "segurança" in r.mensagem
    assert r.linhas == [] and r.grafico is None and r.texto is None
    assert r.sql == "DELETE FROM contratos"  # no modo avançado, mostra o que foi recusado
    assert modelo.interpretacoes == [] and len(modelo.prompts) == 1  # uma tentativa só
    assert _registradas()[0].status == "recusada"


def test_consulta_invalida(cenario):
    r = responder(PERGUNTA, ModeloFalso(sql="SELECT receita FROM contratos"), "C0")
    assert r.status == "invalida"
    assert "coluna" in _registradas()[0].erro.lower() or "receita" in _registradas()[0].erro


class ModeloForaDoAr(ModeloFalso):
    def gerar(self, prompt):
        raise ErroModelo("RateLimitError: sem créditos")


class InterpretacaoForaDoAr(ModeloFalso):
    def interpretar(self, pergunta, resultado):
        raise ErroModelo("timeout")


def test_erro_do_modelo_e_registrado_como_infraestrutura(cenario):
    r = responder(PERGUNTA, ModeloForaDoAr(), "C2")
    assert r.status == "erro_modelo" and "indisponível" in r.mensagem
    assert _registradas()[0].status == "erro_modelo"


def test_falha_so_na_interpretacao_ainda_entrega_grafico_e_tabela(cenario):
    r = responder(PERGUNTA, InterpretacaoForaDoAr(sql=SQL_REGRA), "C2")
    assert r.status == "sucesso" and r.linhas == [[12]] and r.texto is None
    assert "interpretação indisponível" in _registradas()[0].erro


def test_sem_tabelas_e_erro():
    with pytest.raises(ValueError):
        responder(PERGUNTA, ModeloFalso(), "C2")


# ---------------------------------------------------------------- rota

@pytest.fixture
def cliente_api():
    modelo = ModeloFalso(sql=SQL_REGRA, texto="Foram 12 vendas.")
    app.dependency_overrides[obter_cliente] = lambda: modelo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_rota_perguntas(cenario, cliente_api):
    resposta = cliente_api.post("/perguntas", json={"pergunta": PERGUNTA, "configuracao": "C2"})
    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["linhas"] == [[12]] and corpo["texto"] == "Foram 12 vendas." and corpo["sql"] is None

    avancado = cliente_api.post("/perguntas", json={"pergunta": PERGUNTA, "avancado": True}).json()
    assert avancado["sql"] == SQL_REGRA


def test_rota_sem_tabelas_e_409(cliente_api):
    assert cliente_api.post("/perguntas", json={"pergunta": PERGUNTA}).status_code == 409


def test_rota_valida_entrada(cenario, cliente_api):
    assert cliente_api.post("/perguntas", json={"pergunta": ""}).status_code == 422
    assert cliente_api.post("/perguntas", json={"pergunta": "x", "configuracao": "C9"}).status_code == 422
