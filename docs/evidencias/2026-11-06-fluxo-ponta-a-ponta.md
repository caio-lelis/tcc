# Primeiro teste de ponta a ponta: 06/11/2026

Primeira execução do fluxo completo (`services/fluxo.py`, os 9 passos da Figura 3) com um modelo real.

- **Modelo:** `gpt-5.6-luna` (modelo de desenvolvimento, D-06), esforço `low`
- **Configuração:** C2 (esquema + descrições + regras)
- **Dados:** modelo de partida (`dados/exemplo/`) e `contexto_exemplo.json`, em banco temporário
- **Custo das duas perguntas:** US$ 0,0076 (geração + interpretação)

> Teste exploratório, uma execução por pergunta. **Não é resultado do experimento**: ilustração e insumo para decisões.

## Pergunta 1: "Quantas vendas houve em março de 2026?" ✅

```sql
SELECT COUNT(*) AS vendas
FROM contratos
WHERE data_assinatura >= DATE '2026-03-01'
  AND data_assinatura < DATE '2026-04-01'
  AND (data_cancelamento IS NULL
       OR data_cancelamento > data_assinatura + INTERVAL '7 days');
```

- **Resultado:** 12 (correto)
- **Gráfico:** indicador (sugestão do modelo aceita)
- **Texto:** "Houve 12 vendas em março de 2026."

## Pergunta 2: "Como evoluiu a receita mês a mês em 2026?" ❌

```sql
WITH meses AS (
  SELECT (DATE '2026-01-01' + INTERVAL (mes - 1) MONTH)::DATE AS mes FROM range(1, 13) AS t(mes)
), receita_mensal AS (
  SELECT DATE_TRUNC('month', data_assinatura)::DATE AS mes, SUM(valor - desconto) AS receita
  FROM contratos
  WHERE data_assinatura >= DATE '2026-01-01' AND data_assinatura < DATE '2027-01-01'
    AND NOT (data_cancelamento >= data_assinatura
             AND data_cancelamento <= data_assinatura + INTERVAL 7 DAY)
  GROUP BY 1
)
SELECT m.mes AS mes, COALESCE(r.receita, 0) AS receita
FROM meses m LEFT JOIN receita_mensal r ON m.mes = r.mes ORDER BY m.mes
```

- **Gráfico:** linha no tempo (sugestão do modelo aceita)
- **Texto:** "A receita começou em 0 em janeiro, subiu para 11.240 em fevereiro e atingiu o maior valor do ano em abril, com 45.170. Depois, oscilou: caiu para 5.920 em agosto, voltou a 23.055 em setembro e terminou o ano em 0 em novembro e dezembro."

### O erro

Para contratos nunca cancelados, `data_cancelamento` é `NULL`; `NOT (NULL AND ...)` resulta em `NULL`, e a linha é descartada. **Todos os contratos não cancelados ficaram fora da soma.**

| Mês | Receita correta | Respondido | Contratos considerados (certo / respondido) |
|---|---|---|---|
| jan | 91.745,00 | 0 | 14 / 0 |
| fev | 57.967,50 | 11.240,00 | 8 / 1 |
| mar | 98.575,00 | 7.310,00 | 12 / 1 |
| abr | 115.787,50 | 45.170,00 | 13 / 4 |
| set | 213.585,00 | 23.055,00 | 28 / 2 |

Além disso, a consulta completou novembro e dezembro com zero, embora os dados terminem em outubro.

### O que o caso mostra

1. **O contexto não elimina todos os erros.** A regra estava no prompt (C2) e o modelo a entendeu; o erro foi na tradução para SQL (lógica de três valores com `NULL`). Categoria da Seção 4.6.4: **filtro**, por competência em SQL e não por falta de contexto. Material direto para a Q3 ("que erros o contexto elimina e quais persistem?").
2. **O texto interpretativo narra o número errado com total fluência.** Ele não alucinou: descreveu fielmente o resultado obtido, como a separação das duas chamadas garante (Seção 3.4). Mas o resultado estava errado, e nada no texto sinaliza isso. É o risco central da Seção 2.5 para o usuário não técnico.
3. **"Terminou o ano em 0":** a consulta inventou meses futuros e o texto os apresentou como fato. Observação qualitativa para o estudo com usuários (Seção 4.7: "se houve casos em que o texto [...] confundiu o participante").
