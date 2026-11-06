"""Configuração central do Data Talk.

Tudo o que precisa ficar FIXO durante o experimento (RNF03) e os limites
de segurança (RNF04) vivem aqui, num lugar só.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]  # .../tcc (raiz do repositório)
load_dotenv(RAIZ / ".env")

# Modelo de linguagem (RNF03): fixos durante o experimento.
# Temperatura NÃO é configurável: os modelos GPT-5.6 recusam o parâmetro (D-15).
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]  # falha logo se não estiver no .env
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
# Esforço de raciocínio ("low", "medium", "high"); "low" fixado em 06/11/2026 (D-15). Vazio = padrão do modelo.
ESFORCO_RACIOCINIO = os.getenv("OPENAI_ESFORCO", "low") or None

# Preço por milhão de tokens em US$ (entrada, saída), para o custo do registro (RNF02).
# Fonte: agregadores em nov/2026; CONFIRMAR na página oficial antes do experimento.
PRECOS = {
    "gpt-5.6-luna": (1.00, 6.00),
    "gpt-5.6-terra": (2.00, 12.00),
}

# Chamada de interpretação: no máximo estas linhas do resultado vão para o modelo
LINHAS_INTERPRETACAO = 50

# Configuração de contexto usada pela interface quando a pergunta não informa (RF06).
# No estudo com usuários, será a de melhor desempenho no experimento (Seção 4.7).
CONFIGURACAO_PADRAO = "C2"

# Limites das consultas (RNF04)
LIMITE_LINHAS = 1000  # linhas devolvidas ao usuário
LIMITE_SEGUNDOS = 10  # tempo máximo de uma consulta
LINHAS_AMOSTRA = 3  # linhas de amostra por tabela no contexto C0 (vão para a OpenAI)

# Onde ficam os arquivos gerados
PASTA_DADOS = RAIZ / "dados"
BANCO_DUCKDB = PASTA_DADOS / "data_talk.duckdb"
ARQUIVO_CONTEXTO = PASTA_DADOS / "contexto.json"  # descrições e regras (RF02, RF03)
PASTA_EXECUCOES = RAIZ / "experimento" / "execucoes"  # log (RNF02)
