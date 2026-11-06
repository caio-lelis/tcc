"""Sonda dos modelos: temperatura zero e saída estruturada (antes de escrever o D5).

Para cada modelo (Luna e Terra):
  1. chamada mínima com temperature=0 + esquema JSON  -> aceita?
     (se recusar, repete sem temperatura, para saber o que funciona)
  2. chamada real com o prompt C2 de "quantas vendas em março?" do modelo de
     partida, executando o SQL devolvido num banco temporário -> deu 12?

Nunca imprime a chave. Custo estimado: < US$ 0,10 no total (4 a 6 chamadas).
Rodar de dentro de backend/:  .venv/Scripts/python -m scripts.sonda_modelos
"""
import json
import tempfile
import time
from pathlib import Path


from openai import OpenAI  # noqa: E402

from app import config  # noqa: E402
from app.models.contexto import Contexto  # noqa: E402
from app.models.resposta import FalhaConsulta  # noqa: E402
from app.services.construtor_contexto import montar_prompt  # noqa: E402
from app.services.executor import executar  # noqa: E402
from app.services.ingestao import ingerir_csv, listar_tabelas  # noqa: E402

MODELOS = ["gpt-5.6-luna", "gpt-5.6-terra"]


ESQUEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["sql", "grafico"],
    "properties": {
        "sql": {"type": "string"},
        "grafico": {
            "type": "object",
            "additionalProperties": False,
            "required": ["tipo", "x", "y"],
            "properties": {
                "tipo": {"type": "string", "enum": ["linha", "barra", "indicador", "tabela"]},
                "x": {"type": ["string", "null"]},
                "y": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}
FORMATO = {"format": {"type": "json_schema", "name": "consulta", "schema": ESQUEMA, "strict": True}}

cliente = OpenAI(api_key=config.OPENAI_API_KEY)
gasto_total = 0.0


def chamar(modelo, instrucoes, entrada, esforco):
    global gasto_total
    args = dict(model=modelo, instructions=instrucoes, input=entrada, text=FORMATO)
    if esforco is not None:
        args["reasoning"] = {"effort": esforco}
    inicio = time.perf_counter()
    r = cliente.responses.create(**args)
    segundos = time.perf_counter() - inicio
    u = r.usage
    raciocinio = getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", None)
    pe, ps = config.PRECOS[modelo]
    custo = u.input_tokens * pe / 1e6 + u.output_tokens * ps / 1e6
    gasto_total += custo
    print(f"    modelo resolvido: {r.model} | {segundos:.1f} s | tokens: entrada {u.input_tokens}, "
          f"saída {u.output_tokens} (raciocínio {raciocinio}) | ~US$ {custo:.4f}")
    return json.loads(r.output_text)


def preparar_banco():
    pasta = Path(tempfile.mkdtemp())
    config.BANCO_DUCKDB = pasta / "sonda.duckdb"
    exemplo = config.RAIZ / "dados" / "exemplo"
    for nome in ("vendedores", "clientes", "reunioes", "contratos"):
        ingerir_csv((exemplo / f"{nome}.csv").read_bytes(), f"{nome}.csv")
    contexto = Contexto.model_validate_json((exemplo / "contexto_exemplo.json").read_text(encoding="utf-8"))
    return listar_tabelas(), contexto


def main():
    """Rodada 2 (temperatura já confirmada como não suportada): testa reasoning.effort
    e roda C0 e C2 da pergunta de março para cada modelo."""
    tabelas, contexto = preparar_banco()
    pergunta = "Quantas vendas houve em março de 2026?"

    for modelo in MODELOS:
        print(f"\n=== {modelo} ===")
        print("  1) chamada mínima com reasoning.effort = 'low' (sem temperatura)")
        esforco = "low"
        try:
            saida = chamar(modelo, "Responda no formato pedido.", "Gere: SELECT 1 AS um", esforco)
            print(f"    ACEITOU esforço 'low'. Saída: {saida}")
        except Exception as erro:  # noqa: BLE001
            print(f"    RECUSOU esforço: {type(erro).__name__}: {str(erro)[:300]}")
            esforco = None
            try:
                saida = chamar(modelo, "Responda no formato pedido.", "Gere: SELECT 1 AS um", None)
                print(f"    sem esforço funcionou. Saída: {saida}")
            except Exception as erro2:  # noqa: BLE001
                print(f"    falhou também sem esforço: {type(erro2).__name__}: {str(erro2)[:300]}")
                continue

        for configuracao in ("C0", "C2"):
            prompt = montar_prompt(pergunta, configuracao, tabelas, contexto)
            print(f"  2) prompt real {configuracao} (esforço={esforco})")
            saida = chamar(modelo, prompt.sistema, prompt.usuario, esforco)
            print(f"    gráfico: {saida['grafico']}")
            print("    SQL:\n      " + saida["sql"].replace("\n", "\n      "))
            try:
                resultado = executar(saida["sql"])
                print(f"    resultado: {resultado.linhas}  (resposta certa: 12)")
            except FalhaConsulta as falha:
                print(f"    falha na execução [{falha.categoria}]: {falha.mensagem[:200]}")

    print(f"\nGasto estimado total: ~US$ {gasto_total:.4f}")


if __name__ == "__main__":
    main()
