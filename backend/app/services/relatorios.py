"""Relatórios ao vivo: a pessoa anexa respostas do assistente e edita o documento.

Onde cada coisa fica:
- Postgres: o relatório editável (blocos), o SQL de cada resultado e o índice de versões;
- S3 (MinIO): os PDFs, imutáveis, um por versão exportada;
- DuckDB: nada. Uma consulta gerada pelo modelo não pode conseguir ler os relatórios.

Este módulo não participa do fluxo de perguntas: sem Postgres ou sem MinIO só os
relatórios param, e nada aqui escreve no registro de execuções do experimento.
"""
import json
import threading
import uuid
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app import config
from app.models.registro import Execucao
from app.models.relatorio import (
    Bloco, EdicaoRelatorio, NovaVersao, NovoAnexo, Relatorio, ResumoRelatorio, Versao,
)
from app.models.resposta import FalhaConsulta, SugestaoGrafico
from app.services import armazenamento, pdf_relatorio
from app.services.erros_relatorio import (
    ErroConflito, ErroEntrada, ErroIndisponivel, ErroNaoEncontrado,
)
from app.services.executor import executar
from app.services.visualizacao import montar_grafico

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS relatorios (
    id            TEXT PRIMARY KEY,
    dono_id       TEXT,                 -- preenchido quando houver login
    titulo        TEXT NOT NULL,
    blocos        JSONB NOT NULL DEFAULT '[]',
    revisao       INTEGER NOT NULL DEFAULT 1,
    criado_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS relatorio_consultas (
    bloco_id     TEXT PRIMARY KEY,
    relatorio_id TEXT NOT NULL REFERENCES relatorios(id) ON DELETE CASCADE,
    execucao_id  TEXT NOT NULL,
    sql          TEXT NOT NULL,
    sugestao     JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS relatorio_versoes (
    relatorio_id TEXT NOT NULL REFERENCES relatorios(id) ON DELETE CASCADE,
    numero       INTEGER NOT NULL,
    chave        TEXT NOT NULL,
    tamanho      BIGINT NOT NULL,
    criado_em    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (relatorio_id, numero)
);
"""

_trava = threading.Lock()
_esquema_pronto = False


def _conectar() -> psycopg.Connection:
    """Conecta sob demanda: a API sobe mesmo com o Postgres fora do ar."""
    global _esquema_pronto
    try:
        conexao = psycopg.connect(config.URL_POSTGRES, connect_timeout=3, row_factory=dict_row)
        with _trava:
            if not _esquema_pronto:
                conexao.execute(_ESQUEMA)
                conexao.commit()
                _esquema_pronto = True
        return conexao
    except psycopg.OperationalError as erro:
        raise ErroIndisponivel("Os relatórios estão indisponíveis no momento. Tente de novo em instantes.") from erro


def _montar(linha: dict) -> Relatorio:
    return Relatorio(
        id=linha["id"], titulo=linha["titulo"], blocos=linha["blocos"], revisao=linha["revisao"],
        criado_em=linha["criado_em"], atualizado_em=linha["atualizado_em"],
    )


def _buscar(conexao: psycopg.Connection, relatorio_id: str, travar: bool = False) -> dict:
    sql = "SELECT * FROM relatorios WHERE id = %s" + (" FOR UPDATE" if travar else "")
    linha = conexao.execute(sql, (relatorio_id,)).fetchone()
    if not linha:
        raise ErroNaoEncontrado("Relatório não encontrado.")
    return linha


def _gravar_blocos(conexao: psycopg.Connection, relatorio_id: str, titulo: str, blocos: list[Bloco]) -> Relatorio:
    linha = conexao.execute(
        """UPDATE relatorios SET titulo = %s, blocos = %s, revisao = revisao + 1, atualizado_em = now()
           WHERE id = %s RETURNING *""",
        (titulo, Jsonb([b.model_dump(mode="json") for b in blocos]), relatorio_id),
    ).fetchone()
    return _montar(linha)


# ---------------------------------------------------------------- relatórios

def listar() -> list[ResumoRelatorio]:
    with _conectar() as conexao:
        linhas = conexao.execute(
            """SELECT r.id, r.titulo, r.atualizado_em, jsonb_array_length(r.blocos) AS quantidade_blocos,
                      (SELECT count(*) FROM relatorio_versoes v WHERE v.relatorio_id = r.id) AS quantidade_versoes
               FROM relatorios r ORDER BY r.atualizado_em DESC""",
        ).fetchall()
    return [ResumoRelatorio(**linha) for linha in linhas]


def criar(titulo: str) -> Relatorio:
    with _conectar() as conexao:
        linha = conexao.execute(
            "INSERT INTO relatorios (id, titulo) VALUES (%s, %s) RETURNING *", (uuid.uuid4().hex, titulo),
        ).fetchone()
    return _montar(linha)


def obter(relatorio_id: str) -> Relatorio:
    with _conectar() as conexao:
        return _montar(_buscar(conexao, relatorio_id))


def editar(relatorio_id: str, edicao: EdicaoRelatorio) -> Relatorio:
    ids = [b.id for b in edicao.blocos]
    if len(ids) != len(set(ids)):
        raise ErroEntrada("O relatório tem blocos repetidos.")

    with _conectar() as conexao:
        atual = _buscar(conexao, relatorio_id, travar=True)
        if atual["revisao"] != edicao.revisao:
            raise ErroConflito("Este relatório foi alterado em outra aba. Recarregue para ver a versão mais nova.")

        # resultados só nascem por anexo: assim todo número do relatório tem uma consulta de origem
        conhecidos = {
            l["bloco_id"] for l in conexao.execute(
                "SELECT bloco_id FROM relatorio_consultas WHERE relatorio_id = %s", (relatorio_id,),
            ).fetchall()
        }
        if any(b.tipo == "resultado" and b.id not in conhecidos for b in edicao.blocos):
            raise ErroEntrada("Resultados só podem entrar no relatório pelo botão de anexar.")

        conexao.execute(
            "DELETE FROM relatorio_consultas WHERE relatorio_id = %s AND NOT (bloco_id = ANY(%s))",
            (relatorio_id, ids),
        )
        return _gravar_blocos(conexao, relatorio_id, edicao.titulo, edicao.blocos)


def excluir(relatorio_id: str) -> None:
    with _conectar() as conexao:
        _buscar(conexao, relatorio_id, travar=True)
        chaves = [
            l["chave"] for l in conexao.execute(
                "SELECT chave FROM relatorio_versoes WHERE relatorio_id = %s", (relatorio_id,),
            ).fetchall()
        ]
        armazenamento.remover(chaves)  # falhou? o relatório fica, e nenhum PDF vira órfão
        conexao.execute("DELETE FROM relatorios WHERE id = %s", (relatorio_id,))


# ---------------------------------------------------------------- resultados

def buscar_execucao(execucao_id: str) -> Execucao:
    """Procura a execução nos registros de uso da interface, do dia mais recente ao mais antigo."""
    marca = json.dumps(execucao_id)
    pasta = config.PASTA_EXECUCOES / "uso"
    for arquivo in sorted(pasta.glob("*.jsonl"), reverse=True) if pasta.exists() else []:
        with arquivo.open(encoding="utf-8") as f:
            for linha in f:
                if marca in linha:
                    execucao = Execucao.model_validate_json(linha)
                    if execucao.id == execucao_id:
                        return execucao
    raise ErroNaoEncontrado("Não encontrei essa resposta no registro para anexá-la.")


def anexar(relatorio_id: str, anexo: NovoAnexo) -> Relatorio:
    execucao = buscar_execucao(anexo.execucao_id)
    if execucao.status != "sucesso" or not execucao.sql or not execucao.grafico_sugerido:
        raise ErroEntrada("Só respostas com resultado podem entrar no relatório.")

    bloco = Bloco(
        id=uuid.uuid4().hex, tipo="resultado", texto=anexo.texto, pergunta=execucao.pergunta,
        grafico=anexo.grafico, colunas=anexo.colunas, linhas=anexo.linhas, truncado=anexo.truncado,
        dados_em=execucao.quando,
    )
    with _conectar() as conexao:
        atual = _montar(_buscar(conexao, relatorio_id, travar=True))
        conexao.execute(
            "INSERT INTO relatorio_consultas (bloco_id, relatorio_id, execucao_id, sql, sugestao) VALUES (%s, %s, %s, %s, %s)",
            (bloco.id, relatorio_id, execucao.id, execucao.sql, Jsonb(execucao.grafico_sugerido.model_dump())),
        )
        return _gravar_blocos(conexao, relatorio_id, atual.titulo, [*atual.blocos, bloco])


def atualizar_bloco(relatorio_id: str, bloco_id: str) -> Relatorio:
    """Roda de novo a consulta guardada. Não chama o modelo: o texto do bloco continua o da pessoa."""
    with _conectar() as conexao:
        atual = _montar(_buscar(conexao, relatorio_id, travar=True))
        bloco = next((b for b in atual.blocos if b.id == bloco_id), None)
        consulta = conexao.execute(
            "SELECT sql, sugestao FROM relatorio_consultas WHERE bloco_id = %s AND relatorio_id = %s",
            (bloco_id, relatorio_id),
        ).fetchone()
        if not bloco or not consulta:
            raise ErroNaoEncontrado("Esse resultado não está mais no relatório.")

        try:
            resultado = executar(consulta["sql"])  # passa pelo validador e pelos limites de sempre
        except FalhaConsulta as falha:
            raise ErroConflito(f"Não consegui atualizar esses números: {falha.mensagem}") from falha

        bloco.grafico = montar_grafico(SugestaoGrafico(**consulta["sugestao"]), resultado)
        bloco.colunas, bloco.linhas, bloco.truncado = resultado.colunas, resultado.linhas, resultado.truncado
        bloco.dados_em = datetime.now(timezone.utc)
        return _gravar_blocos(conexao, relatorio_id, atual.titulo, atual.blocos)


# ---------------------------------------------------------------- versões em PDF

def listar_versoes(relatorio_id: str) -> list[Versao]:
    with _conectar() as conexao:
        _buscar(conexao, relatorio_id)
        linhas = conexao.execute(
            "SELECT numero, tamanho, criado_em FROM relatorio_versoes WHERE relatorio_id = %s ORDER BY numero DESC",
            (relatorio_id,),
        ).fetchall()
    return [Versao(**linha) for linha in linhas]


def publicar_versao(relatorio_id: str, pedido: NovaVersao) -> Versao:
    with _conectar() as conexao:
        relatorio = _montar(_buscar(conexao, relatorio_id, travar=True))
        if not relatorio.blocos:
            raise ErroEntrada("O relatório está vazio: anexe ou escreva algo antes de exportar.")
        numero = conexao.execute(
            "SELECT coalesce(max(numero), 0) + 1 AS numero FROM relatorio_versoes WHERE relatorio_id = %s",
            (relatorio_id,),
        ).fetchone()["numero"]

        pdf = pdf_relatorio.gerar(relatorio, pedido.graficos, numero)
        chave = f"relatorios/{relatorio_id}/v{numero}.pdf"
        armazenamento.guardar(chave, pdf)
        linha = conexao.execute(
            """INSERT INTO relatorio_versoes (relatorio_id, numero, chave, tamanho) VALUES (%s, %s, %s, %s)
               RETURNING numero, tamanho, criado_em""",
            (relatorio_id, numero, chave, len(pdf)),
        ).fetchone()
    return Versao(**linha)


def ler_versao(relatorio_id: str, numero: int) -> tuple[str, bytes]:
    """Devolve o título do relatório e o PDF da versão."""
    with _conectar() as conexao:
        relatorio = _buscar(conexao, relatorio_id)
        versao = conexao.execute(
            "SELECT chave FROM relatorio_versoes WHERE relatorio_id = %s AND numero = %s", (relatorio_id, numero),
        ).fetchone()
    if not versao:
        raise ErroNaoEncontrado("Essa versão do relatório não existe.")
    return relatorio["titulo"], armazenamento.ler(versao["chave"])
