# Backend do Data Talk: FastAPI + DuckDB.
# A estrutura dentro do container imita a do repositório (/app = raiz), para que
# config.RAIZ, dados/ e experimento/ funcionem do mesmo jeito que fora dele.
FROM python:3.12-slim

# git: para registrar em cada execução o commit do código que rodou (versao_codigo)
# pango e fontes: para o WeasyPrint gerar os PDFs dos relatórios
RUN apt-get update \
    && apt-get install -y --no-install-recommends git libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-inter fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY tests ./tests

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/saude')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
