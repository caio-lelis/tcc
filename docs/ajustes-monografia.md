# Ajustes na monografia

Pontos levantados durante a implementação que precisam ser refletidos no texto. Referências de seção e página são da proposta (`docs/proposta.pdf`).

Marque `[x]` quando corrigir.

## Modelo de linguagem

- [ ] **Temperatura zero NÃO é aceita: confirmado em 06/11/2026 (RNF03, Seções 3.7, 4.6.1 e Tab. 10).** A API respondeu `400 - Unsupported parameter: 'temperature' is not supported with this model` para o `gpt-5.6-luna` e o `gpt-5.6-terra`. Ver `docs/decisoes.md`, D-15. Mudanças no texto:
  - **RNF03** passa a ser: "Manter fixos, durante o experimento, a versão datada do modelo e o nível de esforço de raciocínio."
  - **Seção 4.6.1:** trocar "a temperatura (zero)" por "o nível de esforço de raciocínio" entre os fatores mantidos constantes.
  - **Tab. 10, ameaça "não determinismo do modelo":** mitigação passa a ser "versão datada fixa, esforço de raciocínio fixo, três repetições, veredito por maioria e medida de consistência".
  - **Seção 2.5 (estabilidade):** registrar que modelos de raciocínio atuais não permitem fixar a temperatura, o que reforça a necessidade de medir a consistência (Q4).
  - **Confirmado em 06/11/2026:** o esforço de raciocínio é aceito pelos dois modelos e foi fixado em `low`. Evidência em `docs/evidencias/2026-11-06-sonda-modelos.md`.
- [ ] **Modelo de desenvolvimento x modelo do experimento (Seção 3.7).** Registrar que o desenvolvimento usa o `gpt-5.6-luna` (mais barato) e que o experimento e o estudo com usuários usam o `gpt-5.6-terra`. Os ajustes finais do prompt são feitos no Terra.
- [ ] **Piloto Luna x Terra (opcional, Seção 3.7).** Se for feito o piloto com 5 perguntas, citar o resultado como justificativa adicional da escolha do modelo.
- [ ] **Critério "Custo" sem número (Seção 3.7).** A estimativa inicial (US$ 0,035 por pergunta) ficou bem acima do medido: na sonda, uma geração C2 no Terra com esforço `low` custou US$ 0,004 (cerca de 1.400 tokens de entrada e 100 de saída). Usar os valores medidos pelo registro (RNF02) no TCC2.
- [ ] **Exemplo real de erro que o contexto não resolve (Seções 2.5, 4.6.4 e discussão da Q3).** No primeiro teste de ponta a ponta, o Luna no C2 entendeu a regra do arrependimento, mas escreveu `NOT (data_cancelamento >= ... AND ...)`, que descarta todos os contratos nunca cancelados (`NULL`); a receita de janeiro saiu 0 em vez de 91.745. O texto interpretativo narrou os números errados com fluência. Ver `docs/evidencias/2026-11-06-fluxo-ponta-a-ponta.md`. Bom candidato a pergunta do banco (estrato regra de negócio) e a exemplo na discussão.
- [ ] **Exemplo real para a Seção 2.4 / Fig. 1 (opcional).** A sonda produziu um caso real do erro da Fig. 1: o Terra respondeu 11 no C0 (`status = 'A'`) e 12 no C2. Pode ilustrar o problema ou a apresentação, deixando claro que é exploratório (uma execução, dados fictícios).
- [ ] **Referência de preços.** Citar a página oficial de preços da OpenAI (o valor ainda varia entre fontes: US$ 2/12 ou US$ 2,50/15 por milhão de tokens).
- [ ] **Versão datada (Seções 4.4.2 e 5.4).** Preencher o identificador do snapshot fixado quando for definido. Atenção: a API devolve só `gpt-5.6-terra`, sem data (sonda de 06/11/2026); o identificador datado precisa ser encontrado na documentação e configurado explicitamente em `OPENAI_MODEL`.
- [ ] **Batch API (Seção 4.6.2).** Se o harness usar a Batch API para reduzir custo, mencionar no procedimento (mesmo modelo e parâmetros, só muda a forma de envio).

## Proposta e arquitetura

- [ ] **Nome do produto (Seção 3.1).** Apresentar o assistente como **Data Talk** e usar o nome no restante do texto e nas figuras.
- [ ] **Formato do esquema no prompt (Seção 3.5 e Fig. 4).** Refazer a Fig. 4 no formato `CREATE TABLE` com descrições em comentários `--` e amostra em bloco `/* */` (ver `docs/decisoes.md`, D-01), e citar Gao et al. (2024) como justificativa do formato.
- [ ] **Novo requisito RF10 (Tab. 5 e Fig. 2).** "Atualizar uma tabela anexada preservando o contexto já cadastrado": ao reanexar um CSV, as descrições e regras existentes são mantidas, colunas novas aparecem como "sem descrição" e colunas removidas têm a descrição marcada como órfã. Ligar o RF10 ao componente de Ingestão e ao Repositório de contexto.
- [ ] **Normalização de nomes (Seção 3.3, Ingestão).** Registrar que nomes de tabelas e colunas são convertidos para minúsculas, sem acento e com `_` (ex.: "Data Criação" → `data_criacao`), e que o C0 mostra os nomes normalizados.
- [ ] **Entrevista de levantamento (Tab. 8, etapa 3; Seção 4.4.3).** Descrever a entrevista com a empresa como procedimento de coleta para definir tabelas, descrições (C1), regras (C2) e perguntas candidatas. Incluir o roteiro (`docs/roteiro-entrevista.md`) como apêndice.
- [ ] **Empresa parceira ainda não definida (Tab. 15 e Seção 5.4).** O risco "tabelas não definidas" passa a incluir "empresa parceira ainda não definida". Mitigação: desenvolvimento com o modelo de partida fictício (`dados/exemplo/`) e entrevista de levantamento assim que houver parceira.
- [ ] **Limites concretos (RNF04, Seção 3.8).** Informar os valores adotados: até 1.000 linhas por consulta, 10 segundos de tempo máximo, 3 linhas de amostra por tabela no contexto.
- [ ] **Amostra enviada à OpenAI (Seção 3.8).** Deixar explícito que as 3 linhas de amostra de cada tabela fazem parte do prompt em todas as configurações e, portanto, saem da empresa (reforça a anonimização).
- [ ] **Tecnologias (Seção 3.10).** Citar que as versões das bibliotecas são fixadas no `requirements.txt`. Na descrição do DuckDB, mencionar que o próprio parser dele é usado para validar o SQL gerado (D-14), sem biblioteca extra.
- [ ] **Validador em duas camadas (Seções 3.3 e 3.8).** Descrever as duas camadas: (1) o validador aceita um único comando de leitura, analisado pelo parser do DuckDB; (2) o executor abre o banco somente leitura, sem acesso a arquivos e com a configuração travada. Ver `docs/decisoes.md`, D-14.
- [ ] **Perguntas discriminantes (Tab. 7, Seções 3.9, 4.5 e Tab. 10).** Acrescentar à Tab. 7 o campo `consultas_alternativas` (interpretações erradas plausíveis) e descrever a verificação antes do congelamento: cada alternativa precisa dar resultado diferente do gabarito. Na Tab. 10, a mitigação de "consulta incorreta que coincide com o resultado esperado" passa a ser essa verificação, mais a revisão manual de uma amostra. Ver D-16.
- [ ] **Nova categoria de erro (Seção 4.6.4).** Acrescentar "consulta recusada": consulta barrada pelas camadas de segurança (comando que não é leitura, mais de um comando, acesso a arquivos). Fica separada de "consulta inválida", que passa a significar apenas consultas que o banco não conseguiu executar. Ver D-13.
- [ ] **Tempo esgotado (Seção 4.6.4).** Decidir como classificar consultas interrompidas pelo limite de 10 s: categoria própria ou dentro de "consulta inválida". O sistema já registra separado (`tempo_esgotado`).
- [ ] **Rastreabilidade (Seção 3.2 e apêndice).** Usar `docs/rastreabilidade.md` para a tabela que liga cada requisito ao código, aos testes e ao commit.
- [ ] **Regras de escolha do gráfico (Seção 3.6, RF09).** As três regras da proposta (data + número → linha; categoria + número → barra; valor único → indicador) viraram um conjunto maior: formato longo com uma série por grupo, barras agrupadas, ranking ordenado e horizontal, vários indicadores, gráficos separados para escalas diferentes, limite de 8 séries. Reescrever a Seção 3.6 com base em D-19 e incluir as capturas `docs/capturas/grafico-*.png`. O esquema de saída da chamada de geração ganhou o campo `serie` (Seção 3.4).
- [ ] **Docker e nginx (Seções 3.3, 3.10 e 4.4.2; Fig. 2).** Acrescentar Docker/Docker Compose e nginx às tecnologias; na Fig. 2, o frontend é servido pelo nginx, que repassa `/api` ao backend. Em 4.4.2, "um computador com o assistente instalado" passa a ser "com o assistente em containers (`docker compose up`)". Ver D-17.
- [ ] **Nomes das telas (Seções 3.3 e 3.6; Fig. 2).** As telas da Fig. 2 ("anexação", "descrições e regras", "conversa") se chamam na interface "Meus dados", "Sobre os dados" e "Perguntar". Ver D-18. Incluir capturas de tela no TCC2.
- [ ] **Repositório (Seção 4.9).** Citar o endereço do repositório: https://github.com/caio-lelis/tcc

## Experimento (harness)

- [ ] **Campos do banco de perguntas (Tab. 7, Seção 3.9).** Além de `consultas_alternativas` (D-16), o item ganhou `ordenada` (verdadeiro quando a pergunta pede uma ordem, usado pela regra de acerto) e cada alternativa pode trazer a `categoria` de erro que representa. O banco é escrito em YAML e congelado em JSON.
- [ ] **Congelamento verificável (Seções 3.9 e 4.5).** Descrever que o banco congelado guarda o resultado esperado, a cópia do contexto e as impressões digitais, e que o harness recusa rodar se pergunta, gabarito, contexto ou dados mudaram. Ver D-21.
- [ ] **Chamada de interpretação fora do experimento (Seção 4.6.2).** Deixar explícito que as 180 execuções fazem só a chamada de geração, pelo mesmo fluxo da interface. Ver D-20.
- [ ] **Falhas de infraestrutura (Seção 4.6.2).** Registrar que falhas de rede ou de saldo são refeitas e não contam como erro do modelo.
- [ ] **Regra de acerto e casos limítrofes (Seção 4.6.3).** Detalhar os critérios implementados: número de colunas igual ao do gabarito; tolerância de 0,01; e os três casos marcados para revisão manual (colunas a mais, ordem diferente em pergunta ordenada, resultado cortado). Ver D-22.
- [ ] **Classificação dos erros (Seção 4.6.4).** Descrever o procedimento: categorias automáticas pelo status; para as demais, a coincidência com uma consulta alternativa sugere a categoria e a decisão manual fica registrada com justificativa.
- [ ] **Maioria com repetições faltando (Seção 4.6.3).** O resumo calcula a maioria sobre as repetições válidas e lista o que falta; a rodada oficial só deve ser analisada com "0 faltando".

## Elementos pré-textuais (sobras do modelo LaTeX)

- [ ] **Folha de aprovação:** a data está "01 de junho de 2013" e os membros da banca ainda são "Convidado 1 / Convidado 2".
- [ ] **Dedicatória, agradecimentos e epígrafe:** ainda trazem o texto de instrução do modelo ("A dedicatória é opcional. Caso não deseje uma..."). Escrever o texto final ou deixar em branco.
- [ ] **Ficha catalográfica:** conferir o número de páginas ("61 p.") na versão final e se o código CDU "02:141:005.6" é o correto ou veio do modelo.
