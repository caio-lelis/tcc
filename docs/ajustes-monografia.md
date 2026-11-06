# Ajustes na monografia

Pontos levantados durante a implementação que precisam ser refletidos no texto. Referências de seção e página são da proposta (`docs/proposta.pdf`).

Marque `[x]` quando corrigir.

## Modelo de linguagem

- [ ] **Temperatura zero pode não ser aceita (RNF03, Seções 3.7, 4.6.1 e Tab. 10).** Modelos de raciocínio da OpenAI costumam não aceitar `temperature=0`. Testar com o `gpt-5.6-terra` assim que o cliente do modelo existir. Se não for aceita: reescrever o RNF03, trocar "temperatura zero" na Seção 4.6.1 e na ameaça "Não determinismo do modelo" (Tab. 10) pelo que for possível fixar (versão datada, esforço de raciocínio, seed), e reforçar que as 3 repetições e a medida de consistência (Q4) são a mitigação principal.
- [ ] **Modelo de desenvolvimento x modelo do experimento (Seção 3.7).** Registrar que o desenvolvimento usa o `gpt-5.6-luna` (mais barato) e que o experimento e o estudo com usuários usam o `gpt-5.6-terra`. Os ajustes finais do prompt são feitos no Terra.
- [ ] **Piloto Luna x Terra (opcional, Seção 3.7).** Se for feito o piloto com 5 perguntas, citar o resultado como justificativa adicional da escolha do modelo.
- [ ] **Critério "Custo" sem número (Seção 3.7).** Incluir a estimativa: cerca de US$ 0,035 por pergunta e US$ 50 a 120 no total (detalhe no README). Substituir pelos valores medidos pelo registro (RNF02) no TCC2.
- [ ] **Referência de preços.** Citar a página oficial de preços da OpenAI (o valor ainda varia entre fontes: US$ 2/12 ou US$ 2,50/15 por milhão de tokens).
- [ ] **Versão datada (Seções 4.4.2 e 5.4).** Preencher o identificador do snapshot fixado quando for definido.
- [ ] **Batch API (Seção 4.6.2).** Se o harness usar a Batch API para reduzir custo, mencionar no procedimento (mesmo modelo e parâmetros, só muda a forma de envio).

## Proposta e arquitetura

- [ ] **Nome do produto (Seção 3.1).** Apresentar o assistente como **Fala Dados** e usar o nome no restante do texto e nas figuras.
- [ ] **Formato do esquema no prompt (Seção 3.5 e Fig. 4).** Refazer a Fig. 4 no formato `CREATE TABLE` com descrições em comentários `--` e amostra em bloco `/* */` (ver `docs/decisoes.md`, D-01), e citar Gao et al. (2024) como justificativa do formato.
- [ ] **Novo requisito RF10 (Tab. 5 e Fig. 2).** "Atualizar uma tabela anexada preservando o contexto já cadastrado": ao reanexar um CSV, as descrições e regras existentes são mantidas, colunas novas aparecem como "sem descrição" e colunas removidas têm a descrição marcada como órfã. Ligar o RF10 ao componente de Ingestão e ao Repositório de contexto.
- [ ] **Normalização de nomes (Seção 3.3, Ingestão).** Registrar que nomes de tabelas e colunas são convertidos para minúsculas, sem acento e com `_` (ex.: "Data Criação" → `data_criacao`), e que o C0 mostra os nomes normalizados.
- [ ] **Entrevista de levantamento (Tab. 8, etapa 3; Seção 4.4.3).** Descrever a entrevista com a empresa como procedimento de coleta para definir tabelas, descrições (C1), regras (C2) e perguntas candidatas. Incluir o roteiro (`docs/roteiro-entrevista.md`) como apêndice.
- [ ] **Empresa parceira ainda não definida (Tab. 15 e Seção 5.4).** O risco "tabelas não definidas" passa a incluir "empresa parceira ainda não definida". Mitigação: desenvolvimento com o modelo de partida fictício (`dados/exemplo/`) e entrevista de levantamento assim que houver parceira.
- [ ] **Limites concretos (RNF04, Seção 3.8).** Informar os valores adotados: até 1.000 linhas por consulta, 10 segundos de tempo máximo, 3 linhas de amostra por tabela no contexto.
- [ ] **Amostra enviada à OpenAI (Seção 3.8).** Deixar explícito que as 3 linhas de amostra de cada tabela fazem parte do prompt em todas as configurações e, portanto, saem da empresa (reforça a anonimização).
- [ ] **Tecnologias (Seção 3.10).** Citar que as versões das bibliotecas são fixadas no `requirements.txt`. Na descrição do DuckDB, mencionar que o próprio parser dele é usado para validar o SQL gerado (D-14), sem biblioteca extra.
- [ ] **Validador em duas camadas (Seções 3.3 e 3.8).** Descrever as duas camadas: (1) o validador aceita um único comando de leitura, analisado pelo parser do DuckDB; (2) o executor abre o banco somente leitura, sem acesso a arquivos e com a configuração travada. Ver `docs/decisoes.md`, D-14.
- [ ] **Nova categoria de erro (Seção 4.6.4).** Acrescentar "consulta recusada": consulta barrada pelas camadas de segurança (comando que não é leitura, mais de um comando, acesso a arquivos). Fica separada de "consulta inválida", que passa a significar apenas consultas que o banco não conseguiu executar. Ver D-13.
- [ ] **Tempo esgotado (Seção 4.6.4).** Decidir como classificar consultas interrompidas pelo limite de 10 s: categoria própria ou dentro de "consulta inválida". O sistema já registra separado (`tempo_esgotado`).
- [ ] **Rastreabilidade (Seção 3.2 e apêndice).** Usar `docs/rastreabilidade.md` para a tabela que liga cada requisito ao código, aos testes e ao commit.
- [ ] **Repositório (Seção 4.9).** Citar o endereço do repositório: https://github.com/caio-lelis/tcc

## Elementos pré-textuais (sobras do modelo LaTeX)

- [ ] **Folha de aprovação:** a data está "01 de junho de 2013" e os membros da banca ainda são "Convidado 1 / Convidado 2".
- [ ] **Dedicatória, agradecimentos e epígrafe:** ainda trazem o texto de instrução do modelo ("A dedicatória é opcional. Caso não deseje uma..."). Escrever o texto final ou deixar em branco.
- [ ] **Ficha catalográfica:** conferir o número de páginas ("61 p.") na versão final e se o código CDU "02:141:005.6" é o correto ou veio do modelo.
