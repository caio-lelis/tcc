# Exemplo de prompts: C0, C1 e C2

Gerado por `backend/scripts/exemplo_prompts.py` a partir do modelo de partida (`dados/exemplo/`). Não editar à mão.

Pergunta: **Quantas vendas houve em março de 2026?**

| Configuração | Caracteres da mensagem | Hash do prompt |
|---|---|---|
| C0 | 1.561 | `0a561cd19cb2` |
| C1 | 2.491 | `5f74189085eb` |
| C2 | 3.250 | `55c26f591b33` |

Hash do contexto (igual nas três): `90a994c5b80e`

## Instruções gerais (idênticas nas três configurações)

```text
Você é o assistente de dados do Fala Dados. Sua tarefa é transformar a pergunta de um usuário que não conhece SQL em uma única consulta SQL que responda a essa pergunta a partir das tabelas descritas.

Regras para a consulta:
- Use o dialeto SQL do DuckDB.
- Escreva uma única consulta de leitura: SELECT, opcionalmente precedido de WITH. Nunca escreva comandos que alterem dados ou estrutura.
- Use apenas as tabelas e colunas que aparecem no esquema. Não invente nomes.
- Dê às colunas do resultado nomes curtos e legíveis em português, em snake_case.
- Quando o resultado tiver muitas linhas, ordene-as de forma que faça sentido para a pergunta.

Sugestão de gráfico:
- Indique o tipo de gráfico mais adequado ao resultado: "linha" (evolução no tempo), "barra" (comparação entre categorias), "indicador" (um único número) ou "tabela" (quando nenhum gráfico ajuda).
- Indique a coluna do eixo x e as colunas do eixo y, usando os nomes das colunas do resultado da sua consulta.
- Se o resultado tiver uma coluna que separa grupos (por exemplo, uma linha por vendedor para cada mês), indique-a em "serie" e use uma única coluna no eixo y; caso contrário, deixe "serie" nulo.

Responda apenas no formato JSON solicitado.
```

## C0

```sql
Esquema do banco de dados:

CREATE TABLE clientes (
  id BIGINT,
  nome VARCHAR,
  uf VARCHAR,
  segmento VARCHAR,
  data_cadastro DATE
);
/* Amostra (3 de 80 linhas):
id | nome | uf | segmento | data_cadastro
1 | Rezende Logística | BA | Educação | 2026-01-12
2 | Hora Comércio | DF | Varejo | 2025-10-26
3 | Duarte Escola | DF | Saúde | 2026-05-14
*/

CREATE TABLE contratos (
  id BIGINT,
  cliente_id BIGINT,
  vendedor_id BIGINT,
  valor DOUBLE,
  desconto DOUBLE,
  status VARCHAR,
  data_criacao DATE,
  data_assinatura DATE,
  data_cancelamento DATE
);
/* Amostra (3 de 254 linhas):
id | cliente_id | vendedor_id | valor | desconto | status | data_criacao | data_assinatura | data_cancelamento
1 | 48 | 7 | 13450.0 | 0.0 | C | 2026-04-18 | 2026-04-23 | 2026-05-05
2 | 75 | 5 | 1750.0 | 0.0 | A | 2026-09-04 | 2026-09-21 | NULL
3 | 74 | 7 | 2250.0 | 0.0 | A | 2026-06-11 | 2026-06-24 | NULL
*/

CREATE TABLE reunioes (
  id BIGINT,
  cliente_id BIGINT,
  sdr_id BIGINT,
  closer_id BIGINT,
  data_reuniao DATE,
  situacao VARCHAR,
  tipo VARCHAR
);
/* Amostra (3 de 400 linhas):
id | cliente_id | sdr_id | closer_id | data_reuniao | situacao | tipo
1 | 48 | 2 | 7 | 2026-04-13 | R | 1A
2 | 75 | 2 | 5 | 2026-08-31 | R | 1A
3 | 1 | 2 | 7 | 2026-09-06 | N | 1A
*/

CREATE TABLE vendedores (
  id BIGINT,
  nome VARCHAR,
  equipe VARCHAR,
  ativo BOOLEAN
);
/* Amostra (3 de 8 linhas):
id | nome | equipe | ativo
1 | Diego Moraes | SDR | true
2 | João Nogueira | SDR | true
3 | Pedro Cardoso | SDR | true
*/

Pergunta: Quantas vendas houve em março de 2026?
```

## C1

```sql
Esquema do banco de dados:

CREATE TABLE clientes (  -- Empresas clientes ou potenciais clientes.
  id BIGINT,
  nome VARCHAR,
  uf VARCHAR,  -- Estado da sede.
  segmento VARCHAR,  -- Ramo de atuação.
  data_cadastro DATE  -- Dia em que o cliente entrou no CRM.
);
/* Amostra (3 de 80 linhas):
id | nome | uf | segmento | data_cadastro
1 | Rezende Logística | BA | Educação | 2026-01-12
2 | Hora Comércio | DF | Varejo | 2025-10-26
3 | Duarte Escola | DF | Saúde | 2026-05-14
*/

CREATE TABLE contratos (  -- Contratos enviados a clientes.
  id BIGINT,
  cliente_id BIGINT,
  vendedor_id BIGINT,  -- Closer responsável pelo contrato.
  valor DOUBLE,  -- Valor bruto em reais.
  desconto DOUBLE,  -- Desconto concedido, em reais.
  status VARCHAR,  -- E = enviado (aguardando assinatura), A = assinado, C = cancelado.
  data_criacao DATE,  -- Dia em que o contrato foi gerado.
  data_assinatura DATE,  -- Dia em que o cliente assinou (vazia se não assinou).
  data_cancelamento DATE  -- Dia do cancelamento (vazia se não foi cancelado). Um contrato pode ser cancelado antes ou depois de assinado.
);
/* Amostra (3 de 254 linhas):
id | cliente_id | vendedor_id | valor | desconto | status | data_criacao | data_assinatura | data_cancelamento
1 | 48 | 7 | 13450.0 | 0.0 | C | 2026-04-18 | 2026-04-23 | 2026-05-05
2 | 75 | 5 | 1750.0 | 0.0 | A | 2026-09-04 | 2026-09-21 | NULL
3 | 74 | 7 | 2250.0 | 0.0 | A | 2026-06-11 | 2026-06-24 | NULL
*/

CREATE TABLE reunioes (  -- Reuniões comerciais agendadas.
  id BIGINT,
  cliente_id BIGINT,
  sdr_id BIGINT,  -- Vendedor (SDR) que agendou a reunião.
  closer_id BIGINT,  -- Vendedor (closer) que atendeu a reunião.
  data_reuniao DATE,
  situacao VARCHAR,  -- R = realizada, N = cliente não compareceu, M = remarcada.
  tipo VARCHAR  -- 1A = primeira reunião com o cliente, RET = reunião de retorno.
);
/* Amostra (3 de 400 linhas):
id | cliente_id | sdr_id | closer_id | data_reuniao | situacao | tipo
1 | 48 | 2 | 7 | 2026-04-13 | R | 1A
2 | 75 | 2 | 5 | 2026-08-31 | R | 1A
3 | 1 | 2 | 7 | 2026-09-06 | N | 1A
*/

CREATE TABLE vendedores (  -- Pessoas do time comercial.
  id BIGINT,
  nome VARCHAR,
  equipe VARCHAR,  -- SDR agenda reuniões; CLOSER conduz a reunião e fecha o contrato.
  ativo BOOLEAN  -- false para quem já saiu da empresa.
);
/* Amostra (3 de 8 linhas):
id | nome | equipe | ativo
1 | Diego Moraes | SDR | true
2 | João Nogueira | SDR | true
3 | Pedro Cardoso | SDR | true
*/

Pergunta: Quantas vendas houve em março de 2026?
```

## C2

```sql
Esquema do banco de dados:

CREATE TABLE clientes (  -- Empresas clientes ou potenciais clientes.
  id BIGINT,
  nome VARCHAR,
  uf VARCHAR,  -- Estado da sede.
  segmento VARCHAR,  -- Ramo de atuação.
  data_cadastro DATE  -- Dia em que o cliente entrou no CRM.
);
/* Amostra (3 de 80 linhas):
id | nome | uf | segmento | data_cadastro
1 | Rezende Logística | BA | Educação | 2026-01-12
2 | Hora Comércio | DF | Varejo | 2025-10-26
3 | Duarte Escola | DF | Saúde | 2026-05-14
*/

CREATE TABLE contratos (  -- Contratos enviados a clientes.
  id BIGINT,
  cliente_id BIGINT,
  vendedor_id BIGINT,  -- Closer responsável pelo contrato.
  valor DOUBLE,  -- Valor bruto em reais.
  desconto DOUBLE,  -- Desconto concedido, em reais.
  status VARCHAR,  -- E = enviado (aguardando assinatura), A = assinado, C = cancelado.
  data_criacao DATE,  -- Dia em que o contrato foi gerado.
  data_assinatura DATE,  -- Dia em que o cliente assinou (vazia se não assinou).
  data_cancelamento DATE  -- Dia do cancelamento (vazia se não foi cancelado). Um contrato pode ser cancelado antes ou depois de assinado.
);
/* Amostra (3 de 254 linhas):
id | cliente_id | vendedor_id | valor | desconto | status | data_criacao | data_assinatura | data_cancelamento
1 | 48 | 7 | 13450.0 | 0.0 | C | 2026-04-18 | 2026-04-23 | 2026-05-05
2 | 75 | 5 | 1750.0 | 0.0 | A | 2026-09-04 | 2026-09-21 | NULL
3 | 74 | 7 | 2250.0 | 0.0 | A | 2026-06-11 | 2026-06-24 | NULL
*/

CREATE TABLE reunioes (  -- Reuniões comerciais agendadas.
  id BIGINT,
  cliente_id BIGINT,
  sdr_id BIGINT,  -- Vendedor (SDR) que agendou a reunião.
  closer_id BIGINT,  -- Vendedor (closer) que atendeu a reunião.
  data_reuniao DATE,
  situacao VARCHAR,  -- R = realizada, N = cliente não compareceu, M = remarcada.
  tipo VARCHAR  -- 1A = primeira reunião com o cliente, RET = reunião de retorno.
);
/* Amostra (3 de 400 linhas):
id | cliente_id | sdr_id | closer_id | data_reuniao | situacao | tipo
1 | 48 | 2 | 7 | 2026-04-13 | R | 1A
2 | 75 | 2 | 5 | 2026-08-31 | R | 1A
3 | 1 | 2 | 7 | 2026-09-06 | N | 1A
*/

CREATE TABLE vendedores (  -- Pessoas do time comercial.
  id BIGINT,
  nome VARCHAR,
  equipe VARCHAR,  -- SDR agenda reuniões; CLOSER conduz a reunião e fecha o contrato.
  ativo BOOLEAN  -- false para quem já saiu da empresa.
);
/* Amostra (3 de 8 linhas):
id | nome | equipe | ativo
1 | Diego Moraes | SDR | true
2 | João Nogueira | SDR | true
3 | Pedro Cardoso | SDR | true
*/

-- Regras de negócio e definições de métricas:
-- 1. Regra: Venda é um contrato com data_assinatura preenchida, exceto se foi cancelado em até 7 dias após a assinatura (direito de arrependimento). Cancelamentos depois de 7 dias continuam contando como venda.
-- 2. Regra: A venda pertence ao mês da data_assinatura, nunca ao da data_criacao.
-- 3. Métrica: Receita = valor - desconto, somada apenas sobre as vendas.
-- 4. Regra: Reunião só conta quando situacao = 'R' e tipo = '1A'. Retornos e remarcações não entram nas métricas.
-- 5. Regra: Reuniões são atribuídas ao SDR que agendou (sdr_id); vendas e receita são atribuídas ao closer (contratos.vendedor_id).
-- 6. Métrica: Taxa de conversão de um período = vendas ÷ reuniões, ambas pelas regras acima.

Pergunta: Quantas vendas houve em março de 2026?
```
