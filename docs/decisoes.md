# Decisões de projeto do Fala Dados

Registro das decisões tomadas durante a implementação que se ligam às ideias centrais do TCC. Cada uma traz a alternativa descartada, o porquê e onde ela aparece na monografia. Serve de base para a apresentação e para a escrita do TCC2.

**Tese em uma frase:** o modelo erra números de negócio não por falta de SQL, mas por falta de contexto; e o contexto que resolve isso pode ser escrito pelo próprio usuário.

**Exemplo-âncora** (modelo de partida, `dados/exemplo/`): "Quantas vendas houve em março de 2026?"

| Como o modelo entende | Resultado |
|---|---|
| contratos criados em março | 20 |
| `status = 'A'` e criados em março | 9 |
| **pela regra do negócio** (assinados em março, sem arrependimento em 7 dias) | **12** |

Três consultas válidas, três números plausíveis, só um certo, e o usuário não técnico não tem como saber qual.

---

## Índice

| # | Decisão | Tema |
|---|---|---|
| D-01 | Esquema no prompt em formato `CREATE TABLE` | validade do experimento |
| D-02 | Todas as regras sempre no C2, sem seleção | validade do experimento |
| D-03 | Instruções gerais idênticas nas três configurações | validade do experimento |
| D-04 | Hash do contexto e do prompt em cada execução | reprodutibilidade |
| D-05 | Versões fixas de tudo (Python, bibliotecas, modelo) | reprodutibilidade |
| D-06 | Terra no experimento, Luna no desenvolvimento | escolha do modelo |
| D-07 | Empresa e pessoas reais, com entrevista de levantamento | cenário da pesquisa |
| D-08 | Modelo de partida fictício com armadilhas | desenvolvimento |
| D-09 | Contexto fora do banco de dados | segurança |
| D-10 | Contexto preservado ao atualizar tabelas (RF10) | usabilidade |
| D-11 | Nomes de tabelas e colunas normalizados | usabilidade |
| D-12 | Testes automatizados sem chamar a API | custo e qualidade |

---

## Validade do experimento

### D-01 · Esquema no prompt em formato `CREATE TABLE`

- **Decisão:** o esquema é apresentado ao modelo como código SQL (`CREATE TABLE`), com as descrições do C1 como comentários `--` e as linhas de amostra num bloco `/* */`.
- **Alternativa descartada:** texto livre, como na Fig. 4 da proposta (`Tabela contratos(id INTEGER, ...)`).
- **Por quê:** Gao et al. (2024, DAIL-SQL) mostraram que a forma de representar o esquema muda a acurácia, e a representação em código está entre as melhores. Com ela, o C0 é uma **linha de base forte e justa**: o ganho medido no C1 e no C2 não pode ser atribuído a um C0 artificialmente fraco.
- **Na monografia:** Seção 3.5 e Fig. 4 (refazer no novo formato); ameaça à validade de construto.

### D-02 · Todas as regras sempre no C2, sem seleção

- **Decisão:** no C2, todas as regras cadastradas vão para o prompt, em toda pergunta. A marcação de tabelas numa regra serve só para organizar a tela.
- **Alternativa descartada:** escolher as regras "relevantes" para cada pergunta (por tabela ou por similaridade).
- **Por quê:** selecionar regras criaria uma **segunda variável** no experimento: um erro no C2 poderia ser do contexto ou da seleção. Mantendo todas, a única variável é o nível de contexto. O custo é pequeno: as regras de um domínio cabem com folga na janela do modelo.
- **Na monografia:** Seções 3.5 e 4.6.1 (variáveis); trabalho futuro: seleção de regras para domínios grandes.

### D-03 · Instruções gerais idênticas nas três configurações

- **Decisão:** as instruções (papel do assistente, dialeto DuckDB, "apenas SELECT", formato de saída) ficam num arquivo próprio em `backend/app/prompts/` e são as mesmas no C0, no C1 e no C2. Só o bloco de contexto muda.
- **Por quê:** é o que garante que a diferença de acurácia venha do contexto (Seção 3.5: "todos os demais elementos do prompt [...] serão idênticos"). Em arquivo separado, o texto pode ir para um apêndice e ser auditado.
- **Na monografia:** Seção 3.5; apêndice com as instruções.

---

## Reprodutibilidade

### D-04 · Hash do contexto e do prompt em cada execução

- **Decisão:** o contexto (descrições e regras) e o prompt final recebem uma "impressão digital" (SHA-256, 12 caracteres), gravada em cada execução.
- **Por quê:** prova que as 180 execuções usaram exatamente o mesmo contexto e que as 3 repetições de cada pergunta receberam exatamente o mesmo texto. Se alguém alterar uma regra no meio do experimento, o hash denuncia.
- **Na monografia:** RNF02; Seção 4.6.2; ameaça "não determinismo do modelo" (Tab. 10).

### D-05 · Versões fixas de tudo

- **Decisão:** Python 3.12, bibliotecas com versão exata em `backend/requirements.txt`, modelo configurado num único lugar (`.env`), e versão datada (snapshot) no experimento.
- **Por quê:** o experimento precisa poder ser refeito com o mesmo ambiente. Atualizações silenciosas de bibliotecas ou do modelo mudariam os resultados.
- **Na monografia:** RNF03; Seções 3.10 e 4.9.

---

## Escolha do modelo

### D-06 · Terra no experimento, Luna no desenvolvimento

- **Decisão:** `gpt-5.6-terra` no experimento e no estudo com usuários; `gpt-5.6-luna` (metade do preço) no desenvolvimento. Ajustes finais do prompt são feitos no Terra.
- **Alternativa descartada:** usar um modelo mais barato também no experimento.
- **Por quê:** um modelo mais fraco erra mais por conta própria (SQL inválido, coluna errada), o que **mistura ruído no sinal que o trabalho quer medir**: os erros de regra de negócio. Com 20 perguntas, o sinal precisa ser limpo. O custo total estimado é baixo (~US$ 45) e o Terra é o tipo de modelo que uma empresa adotaria.
- **Pendência:** confirmar se o Terra aceita temperatura zero (RNF03).
- **Na monografia:** Seção 3.7 (critérios de escolha e custo).

---

## Cenário da pesquisa

### D-07 · Empresa e pessoas reais, com entrevista de levantamento

- **Decisão:** o experimento usará dados de uma empresa real; os validadores das perguntas serão pessoas com experiência comercial real. As tabelas, descrições, regras e perguntas candidatas saem de uma entrevista de levantamento (`docs/roteiro-entrevista.md`).
- **Alternativa descartada:** cenário fictício, com pessoas quaisquer apresentadas como "analistas de negócio".
- **Por quê:** o diferencial do trabalho frente a Spider e BIRD (Tab. 3) é a avaliação em um banco empresarial real com usuários do domínio. Validadores sem experiência real comprometeriam a validação do gabarito.
- **Na monografia:** Tab. 3, Tab. 8 (etapa 3), Seção 4.4, Tab. 15 (riscos).

### D-08 · Modelo de partida fictício com armadilhas

- **Decisão:** enquanto não há empresa parceira, o desenvolvimento usa 4 tabelas fictícias (`dados/exemplo/`) construídas com as mesmas armadilhas de dados reais: códigos internos (resolvidos pelo C1) e regras de negócio (resolvidas pelo C2).
- **Por quê:** permite desenvolver e testar sem esperar a empresa, ver o C0, o C1 e o C2 se comportando diferente desde o início, e serve de material na entrevista ("a estrutura de vocês é parecida com esta?").
- **Importante:** o modelo de partida **não** é usado no experimento.
- **Na monografia:** Seção 4.9 (processo de desenvolvimento); exemplo ilustrativo na Seção 2.4.

---

## Segurança e usabilidade

### D-09 · Contexto fora do banco de dados

- **Decisão:** descrições e regras ficam em `dados/contexto.json`, separado do DuckDB e fora do git. A versão congelada para o experimento é copiada de propósito para `experimento/`.
- **Alternativa descartada:** guardar o contexto em tabelas do próprio DuckDB.
- **Por quê:** (1) uma consulta gerada pelo modelo nunca consegue ler as regras como se fossem dados; (2) as regras de uma empresa real não vão parar num repositório público; (3) o arquivo pode ser congelado e versionado para o experimento.
- **Na monografia:** Seções 3.3 (Repositório de contexto) e 3.8.

### D-10 · Contexto preservado ao atualizar tabelas (RF10)

- **Decisão:** ao reanexar um CSV, descrições existentes são mantidas; colunas novas aparecem como "sem descrição"; descrições de colunas que sumiram ficam guardadas como órfãs.
- **Por quê:** dados reais mudam (a empresa exporta de novo, acrescenta um campo). Se o usuário perdesse o que escreveu a cada atualização, o contexto, que é justamente o que o trabalho defende, seria abandonado na prática.
- **Na monografia:** novo requisito RF10 (Tab. 5).

### D-11 · Nomes de tabelas e colunas normalizados

- **Decisão:** "Data Criação" vira `data_criacao`; o nome original é guardado.
- **Por quê:** CSVs reais têm espaços, acentos e maiúsculas, que geram erros de SQL que não têm nada a ver com contexto de negócio. Normalizar remove essa fonte de ruído. CSVs no padrão brasileiro (Latin-1, `;`, vírgula decimal) também são aceitos.
- **Na monografia:** Seção 3.3 (Ingestão).

### D-12 · Testes automatizados sem chamar a API

- **Decisão:** todos os testes usam banco temporário e chave falsa; nenhum chama a OpenAI.
- **Por quê:** testes rodam a cada mudança, de graça, e não dependem de rede. Só o experimento e o uso real gastam API.
- **Na monografia:** Seção 4.9; parte D11 (Tab. 11).
