"""Rotas dos relatórios ao vivo. O SQL dos resultados nunca passa por aqui."""
import re
import unicodedata
from urllib.parse import quote

from fastapi import APIRouter, Response

from app.models.relatorio import (
    EdicaoRelatorio, NovaVersao, NovoAnexo, NovoRelatorio, Relatorio, ResumoRelatorio, Versao,
)
from app.services import relatorios

router = APIRouter(prefix="/relatorios", tags=["relatorios"])


@router.get("", response_model=list[ResumoRelatorio])
def listar():
    return relatorios.listar()


@router.post("", response_model=Relatorio, status_code=201)
def criar(corpo: NovoRelatorio):
    return relatorios.criar(corpo.titulo)


@router.get("/{relatorio_id}", response_model=Relatorio)
def obter(relatorio_id: str):
    return relatorios.obter(relatorio_id)


@router.put("/{relatorio_id}", response_model=Relatorio)
def editar(relatorio_id: str, corpo: EdicaoRelatorio):
    return relatorios.editar(relatorio_id, corpo)


@router.delete("/{relatorio_id}", status_code=204)
def excluir(relatorio_id: str):
    relatorios.excluir(relatorio_id)


@router.post("/{relatorio_id}/anexos", response_model=Relatorio, status_code=201)
def anexar(relatorio_id: str, corpo: NovoAnexo):
    return relatorios.anexar(relatorio_id, corpo)


@router.post("/{relatorio_id}/blocos/{bloco_id}/atualizar", response_model=Relatorio)
def atualizar_bloco(relatorio_id: str, bloco_id: str):
    return relatorios.atualizar_bloco(relatorio_id, bloco_id)


@router.get("/{relatorio_id}/versoes", response_model=list[Versao])
def listar_versoes(relatorio_id: str):
    return relatorios.listar_versoes(relatorio_id)


@router.post("/{relatorio_id}/versoes", response_model=Versao, status_code=201)
def publicar_versao(relatorio_id: str, corpo: NovaVersao):
    return relatorios.publicar_versao(relatorio_id, corpo)


def _nome_ascii(titulo: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", sem_acento).strip("-").lower() or "relatorio"


@router.get("/{relatorio_id}/versoes/{numero}/pdf")
def baixar_versao(relatorio_id: str, numero: int):
    titulo, pdf = relatorios.ler_versao(relatorio_id, numero)
    nome = f"{_nome_ascii(titulo)}-v{numero}.pdf"
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=\"{nome}\"; filename*=UTF-8''{quote(nome)}",
    })
