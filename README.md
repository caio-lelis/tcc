# Data Talk

*Fala com seus dados.*

Assistente text-to-SQL para usuários não técnicos: o usuário anexa tabelas em CSV, descreve cada uma, registra as regras de negócio e faz perguntas em linguagem natural. A resposta vem em texto, gráfico interativo e tabela.

Desenvolvido no Trabalho de Conclusão de Curso *"Contexto de negócio e confiabilidade de LLMs na análise de dados empresariais: avaliação de um assistente text-to-SQL para usuários não técnicos"* (Engenharia de Software, UnB/FCTE). Proposta em [`docs/proposta.pdf`](docs/proposta.pdf).

## Como rodar

### Com Docker (recomendado)

Requer Docker com Compose. Na raiz do repositório:

```bash
cp .env.example .env                 # e preencha OPENAI_API_KEY
docker compose up --build -d
```

| O quê | Onde |
|---|---|
| Interface | http://localhost:3030 |
| API (documentação interativa) | http://localhost:8000/docs |

Para testar, anexe os CSVs de [`dados/exemplo/`](dados/exemplo/) em **Meus dados** e copie as descrições e regras de [`dados/exemplo/README.md`](dados/exemplo/README.md) em **Sobre os dados**.

- **Portas:** só ficam acessíveis nesta máquina (`127.0.0.1`), porque a API usa a sua chave da OpenAI. Para trocar: `DATA_TALK_PORTA=4000 DATA_TALK_PORTA_API=8001 docker compose up -d`.
- **Dados fora do container:** o banco (`dados/data_talk.duckdb`), o contexto (`dados/contexto.json`) e os registros (`experimento/execucoes/`) ficam nas pastas do repositório, montadas como volumes. Recriar os containers não apaga nada.
- **Testes no container:** `docker compose run --rm --no-deps -e OPENAI_API_KEY=x backend python -m pytest`
- **Parar:** `docker compose down`

### Sem Docker (desenvolvimento do backend)

Requer Python 3.12:

```bash
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt

cd backend
.venv/Scripts/python -m pytest       # testes (não usam a chave nem gastam API)
.venv/Scripts/uvicorn app.main:app --reload
```

O frontend em modo de desenvolvimento (`npm run dev` em `frontend/`, com Node 22) repassa `/api` para o backend em `localhost:8000`.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `backend/` | API (FastAPI), DuckDB e cliente do modelo de linguagem |
| `experimento/` | banco de perguntas, harness e análise estatística |
| `dados/exemplo/` | tabelas fictícias para desenvolvimento |
| `dados/reais/` | tabelas da empresa (fora do git) |
| `frontend/` | interface (Vue + ECharts) |
| `docs/` | monografia e documentação; [`decisoes.md`](docs/decisoes.md) registra as decisões de projeto, [`rastreabilidade.md`](docs/rastreabilidade.md) liga cada requisito ao código e ao commit, e [`ajustes-monografia.md`](docs/ajustes-monografia.md) lista o que corrigir no texto |

## Experimento de acurácia (harness)

O harness (RF07) roda o banco de perguntas nas três configurações, com três repetições, pelo mesmo fluxo da interface, e compara cada resultado com o gabarito. Ele usa os dados e o contexto que estão anexados no Data Talk.

```bash
docker compose exec backend python -m scripts.harness verificar                       # gabaritos e alternativas (D-16)
docker compose exec backend python -m scripts.harness congelar                        # grava perguntas.congelado.json
docker compose exec backend python -m scripts.harness rodar --rodada piloto --ensaio  # sem API: responde com o gabarito
docker compose exec backend python -m scripts.harness rodar --rodada oficial          # 180 execuções (gasta API)
docker compose exec backend python -m scripts.harness resumir --rodada oficial        # acurácia, consistência e CSV
```

| Arquivo | O que é |
|---|---|
| `experimento/perguntas.yaml` | banco de perguntas, escrito à mão (ainda não existe: depende das tabelas da empresa) |
| `experimento/exemplo/perguntas.yaml` | exemplo de formato, sobre o modelo de partida fictício; use com `--banco` |
| `experimento/perguntas.congelado.json` | banco congelado: resultado esperado, cópia do contexto e impressões digitais |
| `experimento/execucoes/<rodada>.jsonl` | registro de cada execução |
| `experimento/execucoes/<rodada>.revisao.yaml` | decisões manuais: casos limítrofes e categoria de cada erro |
| `experimento/analise/<rodada>.csv` | uma linha por execução, com o veredito: entrada da análise estatística |

`rodar` pode ser interrompido e retomado. Ele recusa começar se o banco congelado foi alterado ou se o contexto ou os dados mudaram desde o congelamento. Formato do arquivo de revisão:

```yaml
- execucao: 3f9a1c2b7d10        # id mostrado pelo "resumir"
  acerto: true                  # opcional: só para casos limítrofes
  categoria: filtro_regra       # esquema | juncao | filtro_regra | agregacao | data_periodo | interpretacao
  justificativa: A coluna a mais só repete o nome do mês.
```

Decisões de projeto: D-16, D-20, D-21 e D-22 em [`docs/decisoes.md`](docs/decisoes.md).

## Custo estimado da API da OpenAI

Estimativa para o modelo `gpt-5.6-terra`, feita antes da implementação. O registro de execuções (RNF02) grava os tokens e o custo reais de cada chamada, e esta seção será atualizada com os valores medidos.

> **Medido em 06/11/2026** ([sonda](docs/evidencias/2026-11-06-sonda-modelos.md)): com esforço de raciocínio `low`, uma geração C2 no Terra usou ~1.400 tokens de entrada e ~100 de saída, **US$ 0,004**. É cerca de 6 a 9 vezes menos que a estimativa abaixo, que fica como teto conservador. Os valores definitivos virão do registro de execuções.

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

## Relatórios ao vivo

Funcionalidade além do escopo do TCC: nas respostas de "Perguntar", o botão **Adicionar ao relatório**
monta um documento editável ao lado da conversa. A aba **Relatórios** lista os documentos.

- **Postgres** guarda os relatórios editáveis, o SQL de cada resultado e o índice de versões.
- **MinIO** (API S3) guarda os PDFs: cada exportação é uma versão nova e imutável.
- **DuckDB** não guarda nada de relatórios: uma consulta gerada pelo modelo não pode lê-los.
- Os textos aceitam negrito, itálico, sublinhado, tachado, subtítulos, listas e citações. Ficam guardados
  como JSON do Tiptap, nunca como HTML; o PDF só converte uma lista fechada de elementos.
- **Atualizar números** roda de novo a consulta guardada no servidor. Não chama o modelo e não
  escreve no registro de execuções. O navegador nunca envia nem recebe esse SQL.

Postgres e MinIO sobem com o `docker compose up`, sem portas publicadas. Se caírem, só os relatórios
param: as perguntas continuam funcionando. Os dados ficam em volumes do Docker, fora do repositório,
porque os PDFs têm dados reais; `docker compose down -v` apaga tudo.

Em servidor, defina as senhas descritas no `.env.example`. Ainda não há login: quem acessa a
aplicação vê todos os relatórios (a coluna `dono_id` já existe para isso).

Testes de integração (precisam de Postgres e MinIO, com o compose no ar):

```
docker compose exec -e DATA_TALK_TESTE_INTEGRACAO=1 backend python -m pytest tests/test_relatorios.py
```
