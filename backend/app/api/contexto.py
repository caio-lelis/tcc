"""Rotas do contexto de negócio: descrições (RF02) e regras (RF03)."""
from fastapi import APIRouter, HTTPException

from app.models.contexto import ContextoCompleto, DescricaoTabela, Regra, RegraEntrada
from app.services import repositorio

router = APIRouter(tags=["contexto"])


def _erro(erro: repositorio.ErroContexto) -> HTTPException:
    codigo = 404 if "não existe" in str(erro) else 422
    return HTTPException(codigo, str(erro))


@router.get("/contexto", response_model=ContextoCompleto)
def obter_contexto():
    """Todo o contexto, as pendências (colunas sem descrição, órfãs) e o hash."""
    return repositorio.obter_completo()


@router.put("/tabelas/{nome}/descricao", response_model=DescricaoTabela)
def definir_descricao(nome: str, descricao: DescricaoTabela):
    """Descrição da tabela e das colunas. Colunas enviadas vazias têm a descrição apagada."""
    try:
        return repositorio.definir_descricao(nome, descricao)
    except repositorio.ErroContexto as erro:
        raise _erro(erro) from erro


@router.get("/regras", response_model=list[Regra])
def listar_regras():
    return repositorio.listar_regras()


@router.post("/regras", response_model=Regra, status_code=201)
def adicionar_regra(entrada: RegraEntrada):
    try:
        return repositorio.adicionar_regra(entrada)
    except repositorio.ErroContexto as erro:
        raise _erro(erro) from erro


@router.put("/regras/{regra_id}", response_model=Regra)
def atualizar_regra(regra_id: int, entrada: RegraEntrada):
    try:
        return repositorio.atualizar_regra(regra_id, entrada)
    except repositorio.ErroContexto as erro:
        raise _erro(erro) from erro


@router.delete("/regras/{regra_id}", status_code=204)
def remover_regra(regra_id: int):
    try:
        repositorio.remover_regra(regra_id)
    except repositorio.ErroContexto as erro:
        raise _erro(erro) from erro
