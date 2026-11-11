"""Ponto de entrada da API do Data Talk.

Rodar (de dentro de backend/):  .venv/Scripts/uvicorn app.main:app --reload
Documentação interativa:        http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import contexto, perguntas, relatorios, tabelas
from app.services.erros_relatorio import ErroRelatorio

app = FastAPI(title="Data Talk", description="Fala com seus dados.", version="0.1.0")
app.include_router(tabelas.router)
app.include_router(contexto.router)
app.include_router(perguntas.router)
app.include_router(relatorios.router)


@app.exception_handler(ErroRelatorio)
def erro_relatorio(_: Request, erro: ErroRelatorio):
    return JSONResponse(status_code=erro.status, content={"detail": erro.mensagem})


@app.get("/saude", tags=["infra"])
def saude():
    return {"status": "ok"}
