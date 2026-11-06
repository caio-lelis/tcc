"""Ponto de entrada da API do Fala Dados.

Rodar (de dentro de backend/):  .venv/Scripts/uvicorn app.main:app --reload
Documentação interativa:        http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI

from app.api import contexto, tabelas

app = FastAPI(title="Fala Dados", description="Fala com seus dados.", version="0.1.0")
app.include_router(tabelas.router)
app.include_router(contexto.router)


@app.get("/saude", tags=["infra"])
def saude():
    return {"status": "ok"}
