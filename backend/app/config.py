"""Configuração central do Fala Dados.

Tudo o que precisa ficar FIXO durante o experimento (RNF03) e os limites
de segurança (RNF04) vivem aqui, num lugar só.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]  # .../tcc (raiz do repositório)
load_dotenv(RAIZ / ".env")

# Modelo de linguagem (RNF03): fixos durante o experimento
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]  # falha logo se não estiver no .env
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
TEMPERATURA = 0.0

# Limites das consultas (RNF04)
LIMITE_LINHAS = 1000  # linhas devolvidas ao usuário
LIMITE_SEGUNDOS = 10  # tempo máximo de uma consulta
LINHAS_AMOSTRA = 3  # linhas de amostra por tabela no contexto C0 (vão para a OpenAI)

# Onde ficam os arquivos gerados
PASTA_DADOS = RAIZ / "dados"
BANCO_DUCKDB = PASTA_DADOS / "fala_dados.duckdb"
ARQUIVO_CONTEXTO = PASTA_DADOS / "contexto.json"  # descrições e regras (RF02, RF03)
PASTA_EXECUCOES = RAIZ / "experimento" / "execucoes"  # log (RNF02)
