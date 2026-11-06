# Sonda dos modelos: 06/11/2026

Teste exploratório feito antes de implementar o cliente do modelo (D5), para responder: (1) os modelos aceitam temperatura zero (RNF03)? (2) a saída estruturada em JSON funciona? (3) como C0 e C2 se comportam na pergunta-âncora?

- **Script:** `backend/scripts/sonda_modelos.py`
- **Dados:** modelo de partida (`dados/exemplo/`), contexto de `contexto_exemplo.json`
- **Pergunta:** "Quantas vendas houve em março de 2026?" (resposta certa pela regra: **12**)
- **Modelos:** `gpt-5.6-luna` e `gpt-5.6-terra`, via Responses API, SDK `openai` 3.46.0
- **Custo total das duas rodadas:** ~US$ 0,012

> Teste exploratório, uma execução por caso. **Não é resultado do experimento**: serve para decisões de projeto e como ilustração.

## Rodada 1: temperatura zero

As duas chamadas foram recusadas antes de qualquer processamento:

```
gpt-5.6-luna   400 - Unsupported parameter: 'temperature' is not supported with this model.
gpt-5.6-terra  400 - Unsupported parameter: 'temperature' is not supported with this model.
```

(A rodada parou em seguida por falta de créditos na conta; nada foi cobrado.)

**Consequência:** decisão D-15, com a nova redação do RNF03.

## Rodada 2: esforço de raciocínio e C0 × C2

`reasoning.effort = "low"`, saída estruturada com o esquema `{sql, grafico}`.

| Modelo | Chamada | Tokens entrada / saída (raciocínio) | Tempo | Custo | Resultado |
|---|---|---|---|---|---|
| Luna | mínima | 97 / 33 (0) | 2,2 s | US$ 0,0003 | esforço aceito |
| Luna | C0 | 898 / 124 (52) | 2,7 s | US$ 0,0016 | 12 ⚠️ certo por coincidência |
| Luna | C2 | 1.361 / 185 (81) | 3,0 s | US$ 0,0025 | **12 ✅** |
| Terra | mínima | 97 / 61 (26) | 2,0 s | US$ 0,0009 | esforço aceito |
| Terra | C0 | 898 / 82 (0) | 3,7 s | US$ 0,0028 | **11 ❌** |
| Terra | C2 | 1.361 / 103 (0) | 1,8 s | US$ 0,0040 | **12 ✅** |

O nome do modelo devolvido pela API foi `gpt-5.6-luna` / `gpt-5.6-terra`, sem data de versão.

### Terra, C0: caiu na armadilha da regra de negócio

```sql
SELECT COUNT(*) AS quantidade_vendas
FROM contratos
WHERE status = 'A'
  AND data_assinatura >= DATE '2026-03-01'
  AND data_assinatura < DATE '2026-04-01';
-- 11
```

Sem a regra, o modelo tratou `status = 'A'` como "venda" e descartou um contrato assinado em março e cancelado mais de 7 dias depois, que pela regra 1 **conta como venda**. Consulta válida, número plausível, resposta errada: o caso da Fig. 1 da proposta.

### Terra, C2: aplicou a regra

```sql
SELECT COUNT(*) AS vendas
FROM contratos
WHERE data_assinatura >= DATE '2026-03-01'
  AND data_assinatura < DATE '2026-04-01'
  AND (data_cancelamento IS NULL
       OR data_cancelamento > data_assinatura + INTERVAL 7 DAY);
-- 12
```

### Luna, C0: certo por coincidência

```sql
SELECT COUNT(*) AS vendas
FROM contratos
WHERE data_assinatura >= DATE '2026-03-01'
  AND data_assinatura < DATE '2026-04-01';
-- 12
```

A consulta ignora a regra do arrependimento (cancelamento em até 7 dias) e só coincide com o gabarito porque, em março, nenhum contrato assinado foi cancelado em até 7 dias. Em outro mês, erraria. É a ameaça de construto "consulta incorreta que coincide com o resultado esperado" (Tab. 10), que motivou a decisão D-16.

## Conclusões para o projeto

1. Temperatura zero não é suportada; o esforço de raciocínio é aceito e foi fixado em `low` (D-15).
2. A saída estruturada funciona nos dois modelos.
3. O custo real é cerca de 6 a 9 vezes menor que a estimativa inicial: com esforço `low`, o modelo usa poucos tokens de raciocínio.
4. A API não devolve a versão datada; ela precisa ser configurada explicitamente.
5. Uma única pergunta já mostrou o efeito do contexto (Terra: 11 → 12) e o risco de acerto por coincidência (Luna, C0), o que motivou a verificação de perguntas discriminantes (D-16).
