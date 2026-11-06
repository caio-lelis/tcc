# Rastreabilidade dos requisitos

Onde cada requisito da Tab. 5 da proposta (mais o RF10, criado na implementação) está implementado e testado, e em qual commit entrou. Serve de base para a tabela de rastreabilidade do TCC2 (Seção 3.2) e para os cartões do Kanban (Seção 4.9).

Repositório: https://github.com/caio-lelis/tcc. Caminhos relativos à raiz; código em `backend/app/`, testes em `backend/tests/`.

**Legenda:** ✅ implementado e testado · 🟡 parcial · ⬜ pendente

## Visão geral

| ID | Requisito | Status | Parte (Tab. 11) | Commit(s) |
|---|---|---|---|---|
| RF01 | Anexar tabelas em CSV | ✅ backend · ⬜ tela | D2 | [`415808c`][c-415808c] |
| RF02 | Descrição de tabelas e colunas | ✅ backend · ⬜ tela | D3 | [`ad5a249`][c-ad5a249] |
| RF03 | Regras de negócio e métricas | ✅ backend · ⬜ tela | D3 | [`ad5a249`][c-ad5a249] |
| RF04 | Perguntar e responder em linguagem natural | 🟡 cliente do modelo pronto, falta o fluxo e a rota | D5, D8 | [`3467d6f`][c-3467d6f] |
| RF05 | SQL visível só no modo avançado | ⬜ | D8 | |
| RF06 | Selecionar configuração C0, C1 ou C2 | 🟡 montagem pronta, falta seleção na API | D4 | [`701ff37`][c-701ff37] |
| RF07 | Executar banco de perguntas em lote | ⬜ | D10 | |
| RF08 | Texto interpretativo do resultado | 🟡 chamada de interpretação pronta, falta o fluxo | D5 | [`3467d6f`][c-3467d6f] |
| RF09 | Gráfico interativo | ⬜ | D7 | |
| RF10 | Atualizar tabela preservando o contexto *(novo)* | ✅ backend · ⬜ tela | D2, D3 | [`415808c`][c-415808c], [`ad5a249`][c-ad5a249] |
| RNF01 | Somente consultas de leitura | ✅ | D6 | [`b494158`][c-b494158] |
| RNF02 | Registrar prompt, SQL, resultado, tempo e custo | 🟡 hashes, tempo e custo prontos, falta o registro | D3, D4, D5, D9 | [`ad5a249`][c-ad5a249], [`701ff37`][c-701ff37], [`3467d6f`][c-3467d6f] |
| RNF03 | Modelo e esforço de raciocínio fixos *(era: temperatura)* | 🟡 esforço fixado, falta a versão datada | D1, D5 | [`e800176`][c-e800176], [`3467d6f`][c-3467d6f] |
| RNF04 | Limite de tempo e de linhas | ✅ | D1, D6 | [`e800176`][c-e800176], [`b494158`][c-b494158] |
| RNF05 | Interface em português, para quem não sabe SQL | 🟡 API e mensagens em português, falta a tela | D8 | |

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
- **Notas:** saída JSON estrita `{sql, grafico}`; sem temperatura (D-15). Falta o fluxo dos 9 passos (`services/fluxo.py`) e a rota de perguntas.

### RF06 · Selecionar a configuração de contexto (C0, C1 ou C2)

- **Código:** `services/construtor_contexto.py` (`montar_contexto`, `montar_prompt`), `prompts/instrucoes_geracao.md`
- **Testes:** `test_construtor_contexto.py`
- **Commit:** [`701ff37`][c-701ff37]
- **Notas:** esquema em `CREATE TABLE` (D-01); instruções idênticas nas três configurações (D-03); exemplo real em `docs/exemplo-prompts.md`. Falta a escolha da configuração na rota de perguntas.

### RF08 · Texto em linguagem natural que interpreta o resultado

- **Código:** `services/cliente_llm.py` (`ClienteOpenAI.interpretar`, `montar_entrada_interpretacao`), `prompts/instrucoes_interpretacao.md`
- **Testes:** `test_cliente_llm.py`
- **Commit:** [`3467d6f`][c-3467d6f]
- **Notas:** a 2ª chamada recebe só o resultado obtido (até 50 linhas, com aviso de corte) e é instruída a não inventar valores (Seção 3.4).

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
- **Pendente:** o componente de registro (D9).

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

[c-50d196a]: https://github.com/caio-lelis/tcc/commit/50d196aca353915b0dc2410e24405c44ecb94595
[c-e800176]: https://github.com/caio-lelis/tcc/commit/e80017663e01e875ba312405e70335b80de062a3
[c-415808c]: https://github.com/caio-lelis/tcc/commit/415808c4dd234a0ef60bcc6b4dda2dae4d1498af
[c-ad5a249]: https://github.com/caio-lelis/tcc/commit/ad5a24913a4d43068fb035cedc1af5d639c26319
[c-701ff37]: https://github.com/caio-lelis/tcc/commit/701ff3759e378f0bef449b021ddcfa9d9c0f622f
[c-b494158]: https://github.com/caio-lelis/tcc/commit/b494158c58aa7215695fe6f89288d470a654c6c0
[c-3467d6f]: https://github.com/caio-lelis/tcc/commit/3467d6f095b60bec896be5d70a996504511dd30c
[pr-1]: https://github.com/caio-lelis/tcc/pull/1
[pr-2]: https://github.com/caio-lelis/tcc/pull/2
