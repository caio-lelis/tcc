# Rastreabilidade dos requisitos

Onde cada requisito da Tab. 5 da proposta (mais o RF10, criado na implementação) está implementado e testado, e em qual commit entrou. Serve de base para a tabela de rastreabilidade do TCC2 (Seção 3.2) e para os cartões do Kanban (Seção 4.9).

Repositório: https://github.com/caio-lelis/tcc. Caminhos relativos à raiz; código em `backend/app/`, testes em `backend/tests/`.

**Legenda:** ✅ implementado e testado · 🟡 parcial · ⬜ pendente

## Visão geral

| ID | Requisito | Status | Parte (Tab. 11) | Commit(s) |
|---|---|---|---|---|
| RF01 | Anexar tabelas em CSV | ✅ | D2 | [`415808c`][c-415808c], [`2668ed8`][c-2668ed8] |
| RF02 | Descrição de tabelas e colunas | ✅ | D3 | [`ad5a249`][c-ad5a249], [`2668ed8`][c-2668ed8] |
| RF03 | Regras de negócio e métricas | ✅ | D3 | [`ad5a249`][c-ad5a249], [`2668ed8`][c-2668ed8] |
| RF04 | Perguntar e responder em linguagem natural | ✅ | D5, D8 | [`3467d6f`][c-3467d6f], [`5b928e8`][c-5b928e8], [`2668ed8`][c-2668ed8] |
| RF05 | SQL visível só no modo avançado | ✅ | D8 | [`5b928e8`][c-5b928e8], [`2668ed8`][c-2668ed8] |
| RF06 | Selecionar configuração C0, C1 ou C2 | ✅ | D4 | [`701ff37`][c-701ff37], [`5b928e8`][c-5b928e8], [`2668ed8`][c-2668ed8] |
| RF07 | Executar banco de perguntas em lote | ⬜ | D10 | |
| RF08 | Texto interpretativo do resultado | ✅ | D5 | [`3467d6f`][c-3467d6f], [`5b928e8`][c-5b928e8], [`2668ed8`][c-2668ed8] |
| RF09 | Gráfico interativo | ✅ | D7 | [`5b928e8`][c-5b928e8], [`2668ed8`][c-2668ed8] |
| RF10 | Atualizar tabela preservando o contexto *(novo)* | ✅ | D2, D3 | [`415808c`][c-415808c], [`ad5a249`][c-ad5a249], [`2668ed8`][c-2668ed8] |
| RNF01 | Somente consultas de leitura | ✅ | D6 | [`b494158`][c-b494158] |
| RNF02 | Registrar prompt, SQL, resultado, tempo e custo | ✅ | D3, D4, D5, D9 | [`ad5a249`][c-ad5a249], [`701ff37`][c-701ff37], [`3467d6f`][c-3467d6f], [`395fff6`][c-395fff6] |
| RNF03 | Modelo e esforço de raciocínio fixos *(era: temperatura)* | 🟡 esforço fixado, falta a versão datada | D1, D5 | [`e800176`][c-e800176], [`3467d6f`][c-3467d6f] |
| RNF04 | Limite de tempo e de linhas | ✅ | D1, D6 | [`e800176`][c-e800176], [`b494158`][c-b494158] |
| RNF05 | Interface em português, para quem não sabe SQL | ✅ | D8 | [`2668ed8`][c-2668ed8] |

## Detalhe por requisito

### RF01 · Anexar uma ou mais tabelas em formato CSV

- **Código:** `services/ingestao.py` (`ingerir_csv`), `api/tabelas.py` (`POST /tabelas`), `models/tabela.py`
- **Testes:** `test_ingestao.py`, `test_api_tabelas.py`
- **Commit:** [`415808c`][c-415808c] · [PR #1][pr-1]
- **Notas:** normaliza nomes de tabelas e colunas (D-11); aceita CSV brasileiro (Latin-1, `;`, vírgula decimal); guarda o nome original das colunas.

### RF02 · Cadastrar e editar descrição de tabelas e colunas

- **Código:** `services/repositorio.py` (`definir_descricao`), `api/contexto.py` (`PUT /tabelas/{nome}/descricao`), `models/contexto.py`
- **Testes:** `test_repositorio.py`, `test_api_contexto.py`
- **Commit:** [`ad5a249`][c-ad5a249] · [PR #2][pr-2]
- **Notas:** contexto em `dados/contexto.json`, fora do banco e do git (D-09).

### RF03 · Cadastrar regras de negócio e definições de métricas

- **Código:** `services/repositorio.py` (`adicionar_regra`, `atualizar_regra`, `remover_regra`), `api/contexto.py` (`/regras`)
- **Testes:** `test_repositorio.py`, `test_api_contexto.py`
- **Commit:** [`ad5a249`][c-ad5a249] · [PR #2][pr-2]
- **Notas:** cada regra tem `tipo` (regra ou métrica); no C2 vão todas (D-02).

### RF04 · Receber perguntas em linguagem natural e responder

- **Código:** `services/cliente_llm.py` (`ClienteOpenAI.gerar`), `models/resposta.py` (`RespostaGeracao`, `SugestaoGrafico`)
- **Testes:** `test_cliente_llm.py`
- **Commit:** [`3467d6f`][c-3467d6f]
- **Fluxo e rota:** `services/fluxo.py` (os 9 passos da Figura 3), `api/perguntas.py` (`POST /perguntas`); testes em `test_fluxo.py`; commit [`5b928e8`][c-5b928e8].
- **Notas:** saída JSON estrita `{sql, grafico}`; sem temperatura (D-15); sem nova tentativa em caso de falha (Seção 3.4). Evidência: `docs/evidencias/2026-11-06-fluxo-ponta-a-ponta.md`.

### RF05 · Exibir a consulta SQL gerada apenas em modo avançado

- **Código:** `api/perguntas.py` e `services/fluxo.py` (campo `avancado`; sem ele, a resposta não traz o SQL)
- **Testes:** `test_fluxo.py::test_modo_avancado_mostra_o_sql`, `::test_rota_perguntas`
- **Commit:** [`5b928e8`][c-5b928e8]

### RF06 · Selecionar a configuração de contexto (C0, C1 ou C2)

- **Código:** `services/construtor_contexto.py` (`montar_contexto`, `montar_prompt`), `prompts/instrucoes_geracao.md`
- **Testes:** `test_construtor_contexto.py`
- **Commit:** [`701ff37`][c-701ff37]
- **Notas:** esquema em `CREATE TABLE` (D-01); instruções idênticas nas três configurações (D-03); exemplo real em `docs/exemplo-prompts.md`. A configuração é escolhida no corpo de `POST /perguntas` (padrão: `config.CONFIGURACAO_PADRAO`), commit [`5b928e8`][c-5b928e8].

### RF08 · Texto em linguagem natural que interpreta o resultado

- **Código:** `services/cliente_llm.py` (`ClienteOpenAI.interpretar`, `montar_entrada_interpretacao`), `prompts/instrucoes_interpretacao.md`
- **Testes:** `test_cliente_llm.py`
- **Commit:** [`3467d6f`][c-3467d6f]
- **Notas:** a 2ª chamada recebe só o resultado obtido (até 50 linhas, com aviso de corte) e é instruída a não inventar valores (Seção 3.4).

### RF09 · Gráfico interativo adequado ao resultado

- **Código:** `services/visualizacao.py` (`montar_grafico`), `models/resposta.py` (`GraficoFinal`)
- **Testes:** `test_visualizacao.py`
- **Commit:** [`5b928e8`][c-5b928e8]
- **Notas:** a sugestão do modelo é conferida contra as colunas do resultado; se inválida, valem as regras da Seção 3.6 (indicador, linha, barra, tabela). A saída traz a configuração do ECharts com zoom (`dataZoom`), valores no cursor (`tooltip`) e legenda para ocultar séries.
- **Tela:** `frontend/src/components/Grafico.vue` (ECharts; indicador como número grande), commit [`2668ed8`][c-2668ed8].

### RF10 · Atualizar uma tabela anexada preservando o contexto *(novo)*

- **Código:** `services/ingestao.py` (comparação entre versões: colunas novas, removidas, com tipo alterado), `services/repositorio.py` (`calcular_pendencias`)
- **Testes:** `test_ingestao.py::test_reanexar_informa_colunas_novas_removidas_e_tipo_alterado`, `test_repositorio.py::test_reanexar_csv_preserva_descricoes_e_aponta_novas_e_orfas`
- **Commits:** [`415808c`][c-415808c], [`ad5a249`][c-ad5a249]
- **Notas:** decisão D-10.

### RNF01 · Executar apenas consultas de leitura

- **Código:** `services/validador_sql.py` (camada 1), `services/executor.py` (camada 2)
- **Testes:** `test_validador_executor.py`
- **Commit:** [`b494158`][c-b494158]
- **Notas:** parser do próprio DuckDB (D-14); falhas de segurança classificadas como "recusada" (D-13).

### RNF02 · Registrar prompt, consulta, resultado, tempo e custo

- **Pronto:** hash do contexto (`services/repositorio.py`, `calcular_hash`, commit [`ad5a249`][c-ad5a249]) e hash do prompt (`services/construtor_contexto.py`, commit [`701ff37`][c-701ff37]); tempo de execução da consulta (`services/executor.py`, commit [`b494158`][c-b494158]).
- **Pronto também:** tokens, custo e nome do modelo de cada chamada (`UsoModelo`, `services/cliente_llm.py`, commit [`3467d6f`][c-3467d6f]).
- **Registro:** `services/registro.py`, `models/registro.py`: uma linha JSON por execução em `experimento/execucoes/`, com prompt completo, hashes, SQL, status, resultado, texto, tokens, custo, tempos e commit do código; testes em `test_registro.py`; commit [`395fff6`][c-395fff6].

### RNF03 · Versão do modelo e esforço de raciocínio fixos *(era: temperatura)*

- **Código:** `config.py` (`OPENAI_MODEL`, `ESFORCO_RACIOCINIO`), `.env.example`, `services/cliente_llm.py` (nunca envia temperatura)
- **Testes:** `test_cliente_llm.py::test_geracao_envia_prompt_e_esquema_estrito_sem_temperatura`
- **Commits:** [`e800176`][c-e800176], [`3467d6f`][c-3467d6f]
- **Evidência:** `docs/evidencias/2026-11-06-sonda-modelos.md`: temperatura zero recusada pela API; esforço aceito e fixado em `low` (D-15).
- **Pendente:** identificador da versão datada do modelo.

### RNF04 · Limitar tempo de execução e número de linhas

- **Código:** `config.py` (`LIMITE_LINHAS = 1000`, `LIMITE_SEGUNDOS = 10`), `services/executor.py`
- **Testes:** `test_validador_executor.py::test_corta_no_limite_de_linhas_e_avisa`, `::test_interrompe_consulta_demorada`
- **Commits:** [`e800176`][c-e800176], [`b494158`][c-b494158]

## Interface web e containers

Commit [`2668ed8`][c-2668ed8]. A interface fecha a parte "tela" dos requisitos abaixo.

| Requisito | Tela / arquivo |
|---|---|
| RF01, RF10 | **Meus dados**: `frontend/src/components/TelaDados.vue` (anexar, atualizar, ver o que mudou, remover) |
| RF02, RF03, RF10 | **Sobre os dados**: `frontend/src/components/TelaContexto.vue` (descrições, regras, pendências e descrições guardadas) |
| RF04, RF08 | **Perguntar**: `frontend/src/components/TelaConversa.vue`, `RespostaCard.vue` |
| RF05, RF06 | modo avançado: SQL, configuração C0/C1/C2, status e hash (`App.vue`, `TelaConversa.vue`, `RespostaCard.vue`) |
| RF09 | `frontend/src/components/Grafico.vue` |
| RNF05 | todas as telas em português e com vocabulário do negócio (D-18) |
| — | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf` (D-17) |

Verificado em 06/11/2026: 122 testes passando dentro do container; teste de ponta a ponta pelo nginx (anexar os 4 CSVs do modelo de partida, cadastrar contexto, perguntar "Quantas vendas cada closer fez em 2026?" com o `gpt-5.6-luna`), com resposta correta (169 vendas no total) e registro gravado com `versao_codigo`.

## Histórico de commits

| Commit | Data | Entrega |
|---|---|---|
| [`50d196a`][c-50d196a] | 2026-11-06 | estrutura de pastas (D1) |
| [`e800176`][c-e800176] | 2026-11-06 | `config.py` e estimativa de custo (D1) |
| [`415808c`][c-415808c] | 2026-11-06 | ingestão de CSV e modelo de partida (D2) · [PR #1][pr-1] |
| [`ad5a249`][c-ad5a249] | 2026-11-06 | repositório de contexto (D3) · [PR #2][pr-2] |
| [`701ff37`][c-701ff37] | 2026-11-06 | construtor de contexto (D4) |
| [`b494158`][c-b494158] | 2026-11-06 | validador de SQL e executor (D6) |
| [`3467d6f`][c-3467d6f] | 2026-11-06 | cliente do modelo de linguagem (D5) |
| [`395fff6`][c-395fff6] | 2026-11-06 | registro de execuções (D9) |
| [`5b928e8`][c-5b928e8] | 2026-11-06 | fluxo de uma pergunta e conferência do gráfico (D7 backend) |
| [`2668ed8`][c-2668ed8] | 2026-11-06 | containers e interface web (D3 telas, D7, D8) |

[c-50d196a]: https://github.com/caio-lelis/tcc/commit/50d196aca353915b0dc2410e24405c44ecb94595
[c-e800176]: https://github.com/caio-lelis/tcc/commit/e80017663e01e875ba312405e70335b80de062a3
[c-415808c]: https://github.com/caio-lelis/tcc/commit/415808c4dd234a0ef60bcc6b4dda2dae4d1498af
[c-ad5a249]: https://github.com/caio-lelis/tcc/commit/ad5a24913a4d43068fb035cedc1af5d639c26319
[c-701ff37]: https://github.com/caio-lelis/tcc/commit/701ff3759e378f0bef449b021ddcfa9d9c0f622f
[c-b494158]: https://github.com/caio-lelis/tcc/commit/b494158c58aa7215695fe6f89288d470a654c6c0
[c-3467d6f]: https://github.com/caio-lelis/tcc/commit/3467d6f095b60bec896be5d70a996504511dd30c
[c-395fff6]: https://github.com/caio-lelis/tcc/commit/395fff6d756ccca72dbb2ea7cf32e623d134b5f2
[c-5b928e8]: https://github.com/caio-lelis/tcc/commit/5b928e87a3c9355dc085cba6ae80d4f49b084d62
[c-2668ed8]: https://github.com/caio-lelis/tcc/commit/2668ed84a9b45ed18773c7379c4329248153efb3
[pr-1]: https://github.com/caio-lelis/tcc/pull/1
[pr-2]: https://github.com/caio-lelis/tcc/pull/2
