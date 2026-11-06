"""Rotas de tabelas: anexar, atualizar, listar e remover (RF01, RF10)."""
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.tabela import ResultadoIngestao, TabelaInfo
from app.services import ingestao

router = APIRouter(prefix="/tabelas", tags=["tabelas"])

TAMANHO_MAXIMO = 50 * 1024 * 1024  # 50 MB por arquivo


@router.post("", response_model=ResultadoIngestao)
async def anexar_tabela(arquivo: UploadFile = File(...), nome: str | None = Form(None)):
    """Anexa um CSV. Se já existir tabela com o mesmo nome, ela é atualizada (RF10)."""
    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAXIMO:
        raise HTTPException(413, "Arquivo maior que 50 MB.")
    try:
        return ingestao.ingerir_csv(conteudo, arquivo.filename or "tabela.csv", nome)
    except ingestao.ErroIngestao as erro:
        raise HTTPException(422, str(erro)) from erro


@router.get("", response_model=list[TabelaInfo])
def listar():
    return ingestao.listar_tabelas()


@router.get("/{nome}", response_model=TabelaInfo)
def detalhar(nome: str):
    tabela = ingestao.descrever_tabela(nome)
    if tabela is None:
        raise HTTPException(404, f"Tabela {nome!r} não encontrada.")
    return tabela


@router.delete("/{nome}", status_code=204)
def remover(nome: str):
    if not ingestao.remover_tabela(nome):
        raise HTTPException(404, f"Tabela {nome!r} não encontrada.")
