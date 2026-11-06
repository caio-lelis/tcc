# Fala Dados

*Fala com seus dados.*

Assistente text-to-SQL para usuários não técnicos: o usuário anexa tabelas em CSV, descreve cada uma, registra as regras de negócio e faz perguntas em linguagem natural. A resposta vem em texto, gráfico interativo e tabela.

Desenvolvido no Trabalho de Conclusão de Curso *"Contexto de negócio e confiabilidade de LLMs na análise de dados empresariais: avaliação de um assistente text-to-SQL para usuários não técnicos"* (Engenharia de Software, UnB/FCTE). Proposta em [`docs/proposta.pdf`](docs/proposta.pdf).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `backend/` | API (FastAPI), DuckDB e cliente do modelo de linguagem |
| `experimento/` | banco de perguntas, harness e análise estatística |
| `dados/exemplo/` | tabelas fictícias para desenvolvimento |
| `dados/reais/` | tabelas da empresa (fora do git) |
| `frontend/` | interface (Vue + ECharts) |
| `docs/` | monografia e documentação |
