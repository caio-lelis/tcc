"""Testes do cliente do modelo (RF04, RF08). Nenhum teste chama a API:
o SDK da OpenAI é substituído por um objeto falso que registra o pedido."""
import json
from types import SimpleNamespace

import openai
import pytest

from app import config
from app.models.contexto import PromptMontado
from app.models.resposta import ErroModelo, ResultadoConsulta
from app.services.cliente_llm import (
    ClienteOpenAI, ModeloFalso, calcular_custo, instrucoes_interpretacao, montar_entrada_interpretacao,
)

PROMPT = PromptMontado(configuracao="C2", sistema="instrucoes", usuario="esquema + pergunta",
                       hash_prompt="abc", hash_contexto="def")
RESULTADO = ResultadoConsulta(sql="SELECT 1", colunas=["mes", "vendas"], tipos=["VARCHAR", "BIGINT"],
                              linhas=[["2026-03", 12], ["2026-04", None]], truncado=False, tempo_ms=1.0)


class SdkFalso:
    """Imita openai.OpenAI(): sdk.responses.create(**kwargs)."""

    def __init__(self, saida: dict | str, modelo="gpt-5.6-terra-2026-10-01", erro: Exception | None = None):
        self.saida, self.modelo, self.erro = saida, modelo, erro
        self.pedidos: list[dict] = []
        self.responses = self

    def create(self, **kwargs):
        self.pedidos.append(kwargs)
        if self.erro:
            raise self.erro
        texto = self.saida if isinstance(self.saida, str) else json.dumps(self.saida)
        uso = SimpleNamespace(input_tokens=1000, output_tokens=500,
                              output_tokens_details=SimpleNamespace(reasoning_tokens=300))
        return SimpleNamespace(output_text=texto, model=self.modelo, usage=uso)


GERACAO = {"sql": "SELECT COUNT(*) AS vendas FROM contratos", "grafico": {"tipo": "indicador", "x": None, "y": ["vendas"]}}


# ---------------------------------------------------------------- pedido enviado à API

def test_geracao_envia_prompt_e_esquema_estrito_sem_temperatura():
    sdk = SdkFalso(GERACAO)
    ClienteOpenAI(modelo="gpt-5.6-terra", esforco="low", sdk=sdk).gerar(PROMPT)

    pedido = sdk.pedidos[0]
    assert pedido["model"] == "gpt-5.6-terra"
    assert pedido["instructions"] == "instrucoes"
    assert pedido["input"] == "esquema + pergunta"
    assert pedido["reasoning"] == {"effort": "low"}
    assert "temperature" not in pedido  # D-15
    formato = pedido["text"]["format"]
    assert formato["type"] == "json_schema" and formato["strict"] is True
    assert formato["schema"]["required"] == ["sql", "grafico"]


def test_sem_esforco_configurado_nao_envia_reasoning(monkeypatch):
    monkeypatch.setattr(config, "ESFORCO_RACIOCINIO", None)
    sdk = SdkFalso(GERACAO)
    ClienteOpenAI(modelo="gpt-5.6-luna", sdk=sdk).gerar(PROMPT)
    assert "reasoning" not in sdk.pedidos[0]


# ---------------------------------------------------------------- resposta

def test_geracao_devolve_sql_grafico_e_uso():
    resposta = ClienteOpenAI(modelo="gpt-5.6-terra", sdk=SdkFalso(GERACAO)).gerar(PROMPT)

    assert resposta.sql == "SELECT COUNT(*) AS vendas FROM contratos"
    assert resposta.grafico.tipo == "indicador" and resposta.grafico.y == ["vendas"]
    uso = resposta.uso
    assert uso.modelo == "gpt-5.6-terra-2026-10-01"  # nome devolvido pela API, com a versão datada
    assert (uso.tokens_entrada, uso.tokens_saida, uso.tokens_raciocinio) == (1000, 500, 300)
    assert uso.custo_usd == pytest.approx(1000 * 2 / 1e6 + 500 * 12 / 1e6)


def test_interpretacao_usa_instrucoes_proprias_e_devolve_texto():
    sdk = SdkFalso({"texto": "Foram 12 vendas em março."})
    resposta = ClienteOpenAI(modelo="gpt-5.6-terra", sdk=sdk).interpretar("Vendas por mês?", RESULTADO)

    assert resposta.texto == "Foram 12 vendas em março."
    assert sdk.pedidos[0]["instructions"] == instrucoes_interpretacao()
    assert sdk.pedidos[0]["text"]["format"]["name"] == "interpretacao"
    assert "2026-03 | 12" in sdk.pedidos[0]["input"]


# ---------------------------------------------------------------- falhas de infraestrutura

def test_erro_da_api_vira_erro_modelo():
    sdk = SdkFalso(GERACAO, erro=openai.OpenAIError("sem créditos"))
    with pytest.raises(ErroModelo, match="sem créditos"):
        ClienteOpenAI(sdk=sdk).gerar(PROMPT)


def test_resposta_que_nao_e_json_vira_erro_modelo():
    with pytest.raises(ErroModelo, match="formato JSON"):
        ClienteOpenAI(sdk=SdkFalso("isto não é json")).gerar(PROMPT)


# ---------------------------------------------------------------- custo

def test_custo_por_modelo():
    assert calcular_custo("gpt-5.6-luna", 1_000_000, 1_000_000) == 7.0
    assert calcular_custo("gpt-5.6-terra-2026-10-01", 1_000_000, 0) == 2.0
    assert calcular_custo("gpt-5.6-terrazzo", 10, 10) is None  # prefixo sem o hífen não conta
    assert calcular_custo("outro-modelo", 10, 10) is None


# ---------------------------------------------------------------- entrada da interpretação

def test_entrada_da_interpretacao_mostra_tabela_e_null():
    entrada = montar_entrada_interpretacao("  Vendas por mês? ", RESULTADO)
    assert entrada.splitlines() == [
        "Pergunta: Vendas por mês?", "", "Resultado (2 linha(s)):", "mes | vendas", "2026-03 | 12", "2026-04 | NULL",
    ]


def test_entrada_da_interpretacao_avisa_corte(monkeypatch):
    monkeypatch.setattr(config, "LINHAS_INTERPRETACAO", 1)
    entrada = montar_entrada_interpretacao("x", RESULTADO)
    assert "resultado cortado" in entrada
    assert "2026-04" not in entrada


def test_entrada_da_interpretacao_com_resultado_vazio():
    vazio = RESULTADO.model_copy(update={"linhas": []})
    assert "nenhuma linha" in montar_entrada_interpretacao("x", vazio)


# ---------------------------------------------------------------- modelo falso

def test_modelo_falso_registra_chamadas_e_aceita_funcao():
    falso = ModeloFalso(sql=lambda p: f"SELECT '{p.configuracao}' AS config")
    assert falso.gerar(PROMPT).sql == "SELECT 'C2' AS config"
    assert falso.interpretar("x", RESULTADO).texto == "Resultado de teste."
    assert falso.prompts == [PROMPT] and len(falso.interpretacoes) == 1
    assert falso.gerar(PROMPT).uso.custo_usd == 0.0
