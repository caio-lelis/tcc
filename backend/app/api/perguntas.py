"""Rota de perguntas (RF04, RF05, RF06)."""
from fastapi import APIRouter, Depends, HTTPException

from app.models.resposta import Pergunta, RespostaFinal
from app.services import cliente_llm, fluxo

router = APIRouter(tags=["perguntas"])


def obter_cliente() -> cliente_llm.ClienteLLM:
    """Separado em função para os testes trocarem pelo ModeloFalso."""
    return cliente_llm.obter_cliente()


@router.post("/perguntas", response_model=RespostaFinal)
def perguntar(corpo: Pergunta, cliente: cliente_llm.ClienteLLM = Depends(obter_cliente)):
    """Responde em texto, gráfico e tabela. O SQL só vem com "avancado": true (RF05)."""
    try:
        return fluxo.responder(corpo.pergunta, cliente, corpo.configuracao, corpo.avancado)
    except ValueError as erro:
        raise HTTPException(409, str(erro)) from erro
