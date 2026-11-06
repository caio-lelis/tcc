# Roteiro de entrevista de levantamento

Conversa com a empresa parceira para definir as tabelas do domínio comercial (etapa 3 da Tab. 8 da proposta). Duração sugerida: 60 a 90 minutos, com uma pessoa da gestão comercial e, se possível, quem hoje produz os relatórios.

**O que sai desta conversa:**

| Saída | Usada em |
|---|---|
| Lista de tabelas e campos a exportar em CSV | ingestão (RF01) |
| Significado de colunas, códigos e status | contexto **C1** (descrições) |
| Regras de cálculo das métricas | contexto **C2** (regras de negócio) |
| Perguntas que o time faz no dia a dia | banco de perguntas (estratos) |
| Restrições de privacidade | anonimização (Seção 3.8, LGPD) |

**Material para levar:** o modelo de partida em [`dados/exemplo/`](../dados/exemplo/) (4 tabelas fictícias) para mostrar "a estrutura de vocês é parecida com esta?".

> Grave ou anote as respostas com as palavras do entrevistado. A forma como a empresa *explica* uma regra é exatamente o tipo de texto que um usuário real escreveria no C1 e no C2.

---

## 1. Abertura (5 min)

- Apresentar o objetivo do TCC em uma frase: medir se um assistente que responde perguntas sobre os dados acerta mais quando conhece as regras do negócio.
- Explicar o que será pedido à empresa: exportações em CSV, anonimizadas, e de 1 a 2 horas de pessoas para validar perguntas e participar do estudo.
- Confirmar quem autoriza formalmente o uso dos dados (risco da Tab. 15).

## 2. Processo comercial (15 min)

1. Como uma venda acontece aqui, do primeiro contato até o contrato? Quais as etapas?
2. Quem participa de cada etapa (SDR, closer, gerente, pós-venda…)? Uma mesma pessoa pode estar em mais de uma?
3. Em que sistemas cada etapa fica registrada (CRM, planilha, assinatura eletrônica, financeiro)?
4. Quais desses sistemas permitem exportar CSV? Quem faz essa exportação?

## 3. Tabelas e campos (20 min)

Para cada sistema citado:

5. Quais tabelas ou relatórios existem? O que é **uma linha** em cada um (um contrato? uma reunião? um lead por dia?)
6. Quais campos vocês realmente usam? Quais estão lá mas ninguém confia?
7. Existem códigos ou siglas? O que significa cada valor? (status, etapa, origem, tipo…)
8. Que datas existem em cada registro (criação, agendamento, assinatura, pagamento, cancelamento)? Qual delas vocês usam para cada relatório?
9. Como as tabelas se ligam? Existe um identificador comum (id do cliente, telefone, e-mail)? Há casos em que a ligação falha?
10. Há registros duplicados, de teste ou que devem ser ignorados?

## 4. Métricas e regras de negócio (20 min) — a parte mais importante

11. Quais são os 5 a 10 números que a gestão olha toda semana?
12. Para cada um: **como ele é calculado?** O que entra e o que fica de fora?
    - O que conta como **venda**? Contrato assinado? Pago? E se for cancelado depois?
    - A venda pertence a qual mês: criação, assinatura ou pagamento?
    - **Receita** é o valor bruto, com desconto, com imposto?
    - O que conta como **reunião** (ou lead, ou oportunidade)? Remarcações e retornos contam?
    - O resultado de uma venda é atribuído a quem: quem marcou ou quem fechou?
13. **Já aconteceu de dois relatórios mostrarem números diferentes para a "mesma" métrica? Por quê?** (Esta resposta costuma revelar as regras mais valiosas para o C2.)
14. Existe algum documento, painel ou planilha que já define essas métricas oficialmente?

## 5. Perguntas do dia a dia (10 min)

15. Que perguntas o time comercial faz hoje para quem cuida dos dados? Peça exemplos reais, com as palavras deles.
16. Quais perguntas demoram mais para ser respondidas? Quais geram mais retrabalho?
17. Há perguntas que cada pessoa interpreta de um jeito ("como foi o mês?", "quem vendeu mais?")?

> Objetivo: sair com pelo menos 30 perguntas candidatas, para chegar às 20 do banco nos quatro estratos (simples, com junção, dependente de regra, ambígua).

## 6. Privacidade e próximos passos (10 min)

18. Quais campos têm dados pessoais (nome, CPF, telefone, e-mail, endereço)? Quais podem ser removidos ou substituídos por códigos sem perder o sentido?
19. Qual período de dados faz sentido exportar (sugestão: os últimos 6 a 12 meses)?
20. Quem pode atuar como **validador** das perguntas e gabaritos (2 a 3 pessoas com experiência comercial)?
21. Quem poderia participar do **estudo com usuários** (5 a 8 pessoas que não escrevem SQL)?
22. Combinar a data de entrega dos CSVs e o formato (separador, codificação, datas).

---

## Depois da entrevista

- [ ] Transcrever as regras do bloco 4 em frases curtas: são o rascunho do C2.
- [ ] Listar o significado de cada código do bloco 3: rascunho do C1.
- [ ] Separar as perguntas do bloco 5 por estrato.
- [ ] Enviar à empresa a lista final de tabelas e campos a exportar, já com o que deve ser anonimizado.
- [ ] Registrar a autorização formal de uso dos dados.
