"""Armazenamento de objetos pela API S3 (hoje um MinIO local).

Usa só a API S3 padrão: trocar de fornecedor é mudar endereço e credenciais em config.py.
O bucket é privado e o acesso aos PDFs sempre passa pelo backend.
"""
import threading

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app import config
from app.services.erros_relatorio import ErroIndisponivel

_trava = threading.Lock()
_bucket_pronto = False
MENSAGEM = "O armazenamento de PDFs está indisponível no momento. Tente de novo em instantes."


def _cliente():
    return boto3.client(
        "s3",
        endpoint_url=config.S3_ENDPOINT,
        aws_access_key_id=config.S3_CHAVE,
        aws_secret_access_key=config.S3_SEGREDO,
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=3,
            read_timeout=20,
            retries={"max_attempts": 2},
        ),
    )


def _garantir_bucket(cliente) -> None:
    global _bucket_pronto
    with _trava:
        if _bucket_pronto:
            return
        try:
            cliente.head_bucket(Bucket=config.S3_BUCKET)
        except ClientError as erro:
            if erro.response.get("Error", {}).get("Code") not in ("404", "NoSuchBucket"):
                raise
            cliente.create_bucket(Bucket=config.S3_BUCKET)
        _bucket_pronto = True


def guardar(chave: str, dados: bytes, tipo: str = "application/pdf") -> None:
    try:
        cliente = _cliente()
        _garantir_bucket(cliente)
        cliente.put_object(Bucket=config.S3_BUCKET, Key=chave, Body=dados, ContentType=tipo)
    except (BotoCoreError, ClientError) as erro:
        raise ErroIndisponivel(MENSAGEM) from erro


def ler(chave: str) -> bytes:
    try:
        return _cliente().get_object(Bucket=config.S3_BUCKET, Key=chave)["Body"].read()
    except (BotoCoreError, ClientError) as erro:
        raise ErroIndisponivel(MENSAGEM) from erro


def remover(chaves: list[str]) -> None:
    if not chaves:
        return
    try:
        _cliente().delete_objects(
            Bucket=config.S3_BUCKET, Delete={"Objects": [{"Key": c} for c in chaves], "Quiet": True},
        )
    except (BotoCoreError, ClientError) as erro:
        raise ErroIndisponivel(MENSAGEM) from erro
