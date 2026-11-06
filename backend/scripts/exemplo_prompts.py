"""Gera docs/exemplo-prompts.md: os prompts C0, C1 e C2 do modelo de partida.

Usa um banco temporário (não mexe no banco de trabalho) e não chama a API.
Rodar de dentro de backend/:  .venv/Scripts/python -m scripts.exemplo_prompts
"""
import os
import tempfile
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "nao-usada")

from app import config  # noqa: E402
from app.models.contexto import Contexto  # noqa: E402
from app.services.construtor_contexto import montar_prompt  # noqa: E402
from app.services.ingestao import ingerir_csv, listar_tabelas  # noqa: E402

PERGUNTA = "Quantas vendas houve em março de 2026?"
EXEMPLO = config.RAIZ / "dados" / "exemplo"
SAIDA = config.RAIZ / "docs" / "exemplo-prompts.md"


def main() -> None:
    with tempfile.TemporaryDirectory() as pasta:
        config.BANCO_DUCKDB = Path(pasta) / "exemplo.duckdb"
        for nome in ("vendedores", "clientes", "reunioes", "contratos"):
            ingerir_csv((EXEMPLO / f"{nome}.csv").read_bytes(), f"{nome}.csv")
        tabelas = listar_tabelas()

    contexto = Contexto.model_validate_json((EXEMPLO / "contexto_exemplo.json").read_text(encoding="utf-8"))
    prompts = [montar_prompt(PERGUNTA, c, tabelas, contexto) for c in ("C0", "C1", "C2")]

    partes = [
        "# Exemplo de prompts: C0, C1 e C2\n",
        "Gerado por `backend/scripts/exemplo_prompts.py` a partir do modelo de partida "
        "(`dados/exemplo/`). Não editar à mão.\n",
        f"Pergunta: **{PERGUNTA}**\n",
        "| Configuração | Caracteres da mensagem | Hash do prompt |",
        "|---|---|---|",
        *[f"| {p.configuracao} | {len(p.usuario):,} | `{p.hash_prompt}` |".replace(",", ".") for p in prompts],
        f"\nHash do contexto (igual nas três): `{prompts[0].hash_contexto}`\n",
        "## Instruções gerais (idênticas nas três configurações)\n",
        "```text", prompts[0].sistema, "```\n",
    ]
    for p in prompts:
        partes += [f"## {p.configuracao}\n", "```sql", p.usuario, "```\n"]

    SAIDA.write_text("\n".join(partes), encoding="utf-8")
    print(f"Gerado: {SAIDA}")


if __name__ == "__main__":
    main()
