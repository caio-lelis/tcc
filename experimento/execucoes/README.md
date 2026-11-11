# Registros de execução

Uma linha JSON por pergunta respondida pelo Data Talk (RNF02), gravada pelo
`backend/app/services/registro.py`.

| Arquivo | O que é |
|---|---|
| `<rodada>.jsonl` | rodadas do harness do experimento (piloto, oficial…) |
| `<rodada>.revisao.yaml` | decisões manuais da rodada: casos limítrofes e categoria de cada erro (D-22) |
| `uso/AAAA-MM-DD.jsonl` | perguntas feitas pela interface, por dia |

**Os registros de `uso/` de 06/11/2026 são exploratórios**: perguntas de
desenvolvimento sobre o modelo de partida fictício (`dados/exemplo/`), com o
`gpt-5.6-luna`. Não fazem parte do experimento de acurácia.

Cada linha traz a pergunta, a configuração (C0/C1/C2), o prompt completo, os
hashes do contexto e do prompt, o SQL, o status, o resultado, o texto, os
tokens, o custo, os tempos e o commit do código que rodou. Para analisar:

```python
import pandas as pd
df = pd.read_json("experimento/execucoes/uso/2026-11-06.jsonl", lines=True)
```

> Dados de uma empresa real só entram aqui com o repositório privado.
