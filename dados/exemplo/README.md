# Modelo de partida (dados fictícios)

Quatro tabelas inventadas de uma empresa comercial fictícia, usadas para **desenvolver e testar** o Fala Dados e para **mostrar na entrevista** com a empresa parceira ("a estrutura de vocês é parecida com esta?"). Nenhum dado é real.

Para regerar (sempre sai igual, semente fixa):

```bash
python gerar_exemplo.py
```

| Arquivo | Linhas | Uma linha é… |
|---|---|---|
| `vendedores.csv` | 8 | uma pessoa do time comercial |
| `clientes.csv` | 80 | uma empresa cliente |
| `reunioes.csv` | 400 | uma reunião agendada, jan–out/2026 |
| `contratos.csv` | 254 | um contrato enviado a um cliente |

Abaixo está o contexto que um usuário escreveria no Fala Dados. Ele serve de exemplo para os testes das configurações C1 e C2.

## Contexto C1: descrições

**vendedores**: pessoas do time comercial.
- `equipe`: `SDR` agenda reuniões; `CLOSER` conduz a reunião e fecha o contrato.
- `ativo`: `false` para quem já saiu da empresa.

**clientes**: empresas clientes ou potenciais clientes.
- `uf`: estado da sede. `segmento`: ramo de atuação.
- `data_cadastro`: dia em que o cliente entrou no CRM.

**reunioes**: reuniões comerciais agendadas.
- `sdr_id`: vendedor (SDR) que agendou. `closer_id`: vendedor (closer) que atendeu.
- `situacao`: `R` = realizada, `N` = cliente não compareceu, `M` = remarcada.
- `tipo`: `1A` = primeira reunião com o cliente, `RET` = reunião de retorno.

**contratos**: contratos enviados a clientes.
- `vendedor_id`: closer responsável pelo contrato.
- `valor`: valor bruto em reais. `desconto`: desconto concedido, em reais.
- `status`: `E` = enviado (aguardando assinatura), `A` = assinado, `C` = cancelado.
- `data_criacao`: dia em que o contrato foi gerado.
- `data_assinatura`: dia em que o cliente assinou (vazia se não assinou).
- `data_cancelamento`: dia do cancelamento (vazia se não foi cancelado). Um contrato pode ser cancelado antes ou depois de assinado.

## Contexto C2: regras de negócio

1. **Venda** é um contrato com `data_assinatura` preenchida, **exceto** se foi cancelado em até 7 dias após a assinatura (direito de arrependimento). Cancelamentos depois de 7 dias continuam contando como venda.
2. A venda pertence ao **mês da `data_assinatura`**, nunca ao da `data_criacao`.
3. **Receita** = `valor - desconto`, somada apenas sobre as vendas (regra 1).
4. **Reunião** só conta quando `situacao = 'R'` e `tipo = '1A'`. Retornos e remarcações não entram nas métricas.
5. Reuniões são atribuídas ao **SDR** que agendou (`sdr_id`); vendas e receita são atribuídas ao **closer** (`contratos.vendedor_id`).
6. **Taxa de conversão** de um período = vendas ÷ reuniões, ambas pelas regras acima.

## Armadilhas (por que C0, C1 e C2 dão respostas diferentes)

| Armadilha | Sem o contexto, o modelo tende a… | Resolvida em |
|---|---|---|
| Códigos `E/A/C`, `R/N/M`, `1A/RET` | adivinhar o significado | C1 |
| Mês da assinatura × mês da criação (60 contratos mudam de mês) | contar pela data de criação | C2 |
| Cancelamento em até 7 dias (6 casos) × depois de 7 dias (19 casos) | usar só `status = 'A'` | C2 |
| Receita líquida | somar `valor` bruto | C2 |
| Reunião válida | contar todas as linhas de `reunioes` | C2 |
| SDR × closer | misturar as equipes | C2 |

Exemplo, "quantas vendas houve em março de 2026?":

| Consulta | Resultado |
|---|---|
| contratos criados em março | 20 |
| `status = 'A'` e criados em março | 9 |
| **pela regra (assinatura em março, sem arrependimento)** | **12** |
