# Fala Dados

*Fala com seus dados.*

Assistente text-to-SQL para usuários não técnicos: o usuário anexa tabelas em CSV, descreve cada uma, registra as regras de negócio e faz perguntas em linguagem natural. A resposta vem em texto, gráfico interativo e tabela.

Desenvolvido no Trabalho de Conclusão de Curso *"Contexto de negócio e confiabilidade de LLMs na análise de dados empresariais: avaliação de um assistente text-to-SQL para usuários não técnicos"* (Engenharia de Software, UnB/FCTE). Proposta em [`docs/proposta.pdf`](docs/proposta.pdf).

## Como rodar

Requer Python 3.12. Na raiz do repositório:

```bash
cp .env.example .env                 # e preencha OPENAI_API_KEY
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt

cd backend
.venv/Scripts/python -m pytest       # testes (não usam a chave nem gastam API)
.venv/Scripts/uvicorn app.main:app --reload
```

Com o servidor no ar, a documentação interativa da API fica em http://127.0.0.1:8000/docs. Para testar, anexe os CSVs de [`dados/exemplo/`](dados/exemplo/).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `backend/` | API (FastAPI), DuckDB e cliente do modelo de linguagem |
| `experimento/` | banco de perguntas, harness e análise estatística |
| `dados/exemplo/` | tabelas fictícias para desenvolvimento |
| `dados/reais/` | tabelas da empresa (fora do git) |
| `frontend/` | interface (Vue + ECharts) |
| `docs/` | monografia e documentação; [`decisoes.md`](docs/decisoes.md) registra as decisões de projeto e [`ajustes-monografia.md`](docs/ajustes-monografia.md) lista o que corrigir no texto |

## Custo estimado da API da OpenAI

Estimativa para o modelo `gpt-5.6-terra`, feita antes da implementação. O registro de execuções (RNF02) grava os tokens e o custo reais de cada chamada, e esta seção será atualizada com os valores medidos.

**Preço usado:** US$ 2,00 por milhão de tokens de entrada e US$ 12,00 por milhão de tokens de saída (valores de agregadores em nov/2026; **confirmar na [página oficial de preços](https://developers.openai.com/api/docs/pricing)** antes do experimento).

**Tokens por pergunta** (duas chamadas, Seção 3.4 da proposta):

| Chamada | Entrada | Saída | Observação |
|---|---|---|---|
| Geração | ~4.000 | ~1.500 | instruções + contexto C0/C1/C2 + pergunta; saída inclui tokens de raciocínio do modelo |
| Interpretação | ~1.500 | ~500 | pergunta + resultado da consulta |
| **Total** | **~5.500** | **~2.000** | **≈ US$ 0,035 por pergunta** |

O contexto C2 é o mais longo, mas mesmo ele fica muito abaixo da janela do modelo. Quem domina o custo é a saída, sobretudo os tokens de raciocínio.

**Por fase:**

| Fase | Perguntas | Custo estimado |
|---|---|---|
| Desenvolvimento e testes manuais | ~1.000 | ~US$ 35 |
| Experimento de acurácia: 20 perguntas × 3 configurações × 3 repetições = 180, rodado ~3 vezes (piloto + oficial + reserva) | ~540 | ~US$ 19 |
| Estudo com usuários: 8 participantes × 6 tarefas × ~3 perguntas | ~150 | ~US$ 5 |
| **Total** | **~1.700** | **~US$ 60** |

Com margem para raciocínio mais longo que o previsto, a faixa realista é **US$ 50 a 120**.

**Modelo por fase:** o desenvolvimento usa o `gpt-5.6-luna` (US$ 1/6 por milhão de tokens, metade do preço), e o experimento e o estudo com usuários usam o `gpt-5.6-terra`. Os ajustes finais do prompt são feitos no Terra. Para trocar, basta mudar `OPENAI_MODEL` no `.env`. Com isso, o total estimado cai para cerca de **US$ 45**.

**Como reduzir, se necessário:**
- os testes automatizados usam um modelo falso e não gastam nada;
- a Batch API da OpenAI cobra metade do preço e serve para o harness do experimento, que não precisa de resposta imediata;
- as instruções gerais são iguais em todas as chamadas, então o cache de prompt reduz o custo da entrada repetida;
- defina um limite mensal de gasto no painel da OpenAI (Settings → Limits).
