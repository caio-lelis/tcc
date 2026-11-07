"""Gera o PDF de um relatório.

Os gráficos chegam em SVG, desenhados pelo navegador com o mesmo código da tela e sempre
em cores claras. Como esse SVG vem de fora, ele entra como imagem isolada e o gerador só
pode ler URLs "data:": não abre arquivos do servidor nem faz requisições de rede.
"""
import base64
import re
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Any

from app import config
from app.models.relatorio import Bloco, Relatorio
from app.services.erros_relatorio import ErroEntrada

FUSO = timezone(timedelta(hours=-3))  # horário de Brasília
LIMITE_SVG = 2_000_000
PROIBIDO_SVG = re.compile(r"<!|<\?|<script|<foreignobject|<image|<use\b|\bon\w+\s*=|href\s*=", re.IGNORECASE)
PROFUNDIDADE_DOC = 12  # listas dentro de listas: além disso, o conteúdo fica de fora

# Lista fechada do que vira HTML no PDF. Qualquer outro elemento mantém só o texto.
MARCAS = {"bold": "strong", "italic": "em", "underline": "u", "strike": "s"}
ELEMENTOS = {"paragraph": "p", "bulletList": "ul", "orderedList": "ol", "listItem": "li", "blockquote": "blockquote"}
SUBTITULOS = {2: "h3", 3: "h4"}  # o título de seção do relatório já é h2

DATA = re.compile(r"^(\d{4})-(\d{2})(?:-(\d{2}))?(?:[T ].*)?$")
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

ESTILO = """
@page {
  size: A4;
  margin: 22mm 18mm 20mm;
  @bottom-left { content: "Data Talk"; font: 8pt Inter, sans-serif; color: #67655f; }
  @bottom-right { content: counter(page) " / " counter(pages); font: 8pt Inter, sans-serif; color: #67655f; }
}
body { font: 10.5pt/1.55 Inter, "DejaVu Sans", sans-serif; color: #1f2937; }
h1 { font-size: 23pt; line-height: 1.15; color: #0d3072; margin: 0 0 4pt; }
.capa { border-bottom: 2.5pt solid #3ee9b0; padding-bottom: 10pt; margin-bottom: 18pt; }
.capa p { margin: 0; color: #67655f; font-size: 9pt; }
h2 { font-size: 14pt; color: #0d3072; margin: 18pt 0 6pt; break-after: avoid; }
h3 { font-size: 11.5pt; color: #0d3072; margin: 10pt 0 4pt; break-after: avoid; }
h4 { font-size: 10.5pt; color: #0d3072; margin: 8pt 0 3pt; break-after: avoid; }
ul, ol { margin: 0 0 7pt; padding-left: 16pt; }
li > p { margin: 0 0 2pt; }
blockquote { margin: 0 0 7pt; padding: 1pt 0 1pt 9pt; border-left: 2.5pt solid #d3ccbf; color: #475569; }
p { margin: 0 0 7pt; }
.resultado { margin: 12pt 0 16pt; break-inside: avoid; }
.pergunta { font-weight: 600; color: #0d3072; break-after: avoid; }
.grafico { width: 100%; margin: 4pt 0; break-inside: avoid; }
.origem { font-size: 8pt; color: #67655f; margin-top: 3pt; }
table { width: 100%; border-collapse: collapse; font-size: 8.5pt; margin: 4pt 0; }
th { text-align: left; color: #475569; border-bottom: 1pt solid #94a3b8; padding: 4pt 6pt; }
td { border-bottom: .5pt solid #e4dfd5; padding: 3.5pt 6pt; }
td.num, th.num { text-align: right; }
.indicadores { margin: 4pt 0; }
.indicador { display: inline-block; min-width: 130pt; margin: 0 8pt 8pt 0; padding: 8pt 12pt; border-left: 3pt solid #1560e0; background: #f3f0ea; }
.indicador small { display: block; color: #475569; font-size: 8pt; }
.indicador b { font-size: 19pt; color: #0d3072; }
"""


def validar_svg(svg: str) -> str:
    texto = svg.strip()
    if len(texto) > LIMITE_SVG or not texto.startswith("<svg") or PROIBIDO_SVG.search(texto):
        raise ErroEntrada("Um dos gráficos não pôde ser usado no PDF.")
    return texto


def _numero(valor: float) -> str:
    texto = f"{valor:,.2f}".rstrip("0").rstrip(".") if isinstance(valor, float) else f"{valor:,}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def _valor(valor: Any) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, bool):
        return "sim" if valor else "não"
    if isinstance(valor, (int, float)):
        return _numero(valor)
    texto = str(valor)
    data = DATA.match(texto)
    if data:
        ano, mes, dia = data.groups()
        return f"{dia}/{mes}/{ano}" if dia else f"{MESES[int(mes) - 1]} {ano}"
    return texto


def _legivel(coluna: str) -> str:
    texto = coluna.replace("_", " ").strip()
    return texto[:1].upper() + texto[1:]


def _quando(momento: datetime) -> str:
    return momento.astimezone(FUSO).strftime("%d/%m/%Y às %H:%M")


def _paragrafos(texto: str) -> str:
    partes = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    return "".join("<p>" + escape(p).replace("\n", "<br>") + "</p>" for p in partes)


def _no(no: Any, nivel: int = 0) -> str:
    """Converte um nó do Tiptap em HTML. O texto é sempre escapado e nenhum atributo é copiado."""
    if not isinstance(no, dict) or nivel > PROFUNDIDADE_DOC:
        return ""
    tipo = no.get("type")
    if tipo == "text":
        html = escape(str(no.get("text", "")))
        marcas = no.get("marks")
        for marca in marcas if isinstance(marcas, list) else []:
            tag = MARCAS.get(marca.get("type")) if isinstance(marca, dict) else None
            if tag:
                html = f"<{tag}>{html}</{tag}>"
        return html
    if tipo == "hardBreak":
        return "<br>"

    filhos = no.get("content")
    html = "".join(_no(f, nivel + 1) for f in filhos) if isinstance(filhos, list) else ""
    atributos = no.get("attrs")
    tag = ELEMENTOS.get(tipo)
    if tipo == "heading" and isinstance(atributos, dict):
        tag = SUBTITULOS.get(atributos.get("level"))
    return f"<{tag}>{html}</{tag}>" if tag else html


def _texto(bloco: Bloco) -> str:
    return _no(bloco.doc) if bloco.doc else _paragrafos(bloco.texto)


def _tabela(bloco: Bloco) -> str:
    linhas = bloco.linhas[: config.LINHAS_TABELA_PDF]
    numerica = [any(isinstance(l[j], (int, float)) and not isinstance(l[j], bool) for l in bloco.linhas if j < len(l))
                for j in range(len(bloco.colunas))]
    classe = lambda j: ' class="num"' if j < len(numerica) and numerica[j] else ""  # noqa: E731
    cabecalho = "".join(f"<th{classe(j)}>{escape(_legivel(c))}</th>" for j, c in enumerate(bloco.colunas))
    corpo = "".join(
        "<tr>" + "".join(f"<td{classe(j)}>{escape(_valor(v))}</td>" for j, v in enumerate(l)) + "</tr>"
        for l in linhas
    )
    return f"<table><thead><tr>{cabecalho}</tr></thead><tbody>{corpo}</tbody></table>"


def _dados(bloco: Bloco, svgs: list[str]) -> str:
    grafico = bloco.grafico
    if grafico and grafico.tipo == "indicador" and grafico.indicadores:
        itens = "".join(
            f'<div class="indicador"><small>{escape(_legivel(i.rotulo))}</small><b>{escape(_valor(i.valor))}</b></div>'
            for i in grafico.indicadores
        )
        return f'<div class="indicadores">{itens}</div>'
    if bloco.visao == "grafico" and svgs:
        return "".join(
            '<img class="grafico" alt="" src="data:image/svg+xml;base64,'
            + base64.b64encode(validar_svg(s).encode()).decode() + '">'
            for s in svgs
        )
    return _tabela(bloco) if bloco.colunas else ""


def _origem(bloco: Bloco) -> str:
    partes = []
    if bloco.dados_em:
        partes.append(f"Dados de {_quando(bloco.dados_em)}")
    mostrando_tabela = not (bloco.grafico and bloco.grafico.tipo == "indicador") and bloco.visao == "tabela"
    if mostrando_tabela and len(bloco.linhas) > config.LINHAS_TABELA_PDF:
        partes.append(f"mostrando {config.LINHAS_TABELA_PDF} de {len(bloco.linhas)} linhas")
    if bloco.truncado:
        partes.append("resultado cortado no limite de linhas")
    return f'<p class="origem">{escape(" · ".join(partes))}</p>' if partes else ""


def _bloco(bloco: Bloco, svgs: list[str]) -> str:
    if bloco.tipo == "titulo":
        return f"<h2>{escape(bloco.texto)}</h2>" if bloco.texto.strip() else ""
    if bloco.tipo == "texto":
        return _texto(bloco)
    pergunta = f'<p class="pergunta">{escape(bloco.pergunta)}</p>' if bloco.pergunta else ""
    return f'<section class="resultado">{pergunta}{_texto(bloco)}{_dados(bloco, svgs)}{_origem(bloco)}</section>'


def montar_html(relatorio: Relatorio, graficos: dict[str, list[str]], numero: int) -> str:
    agora = _quando(datetime.now(timezone.utc))
    corpo = "".join(_bloco(b, graficos.get(b.id, [])) for b in relatorio.blocos)
    return (
        f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{escape(relatorio.titulo)}</title>'
        f"<style>{ESTILO}</style></head><body>"
        f'<div class="capa"><h1>{escape(relatorio.titulo)}</h1><p>Versão {numero} · gerado em {agora}</p></div>'
        f"{corpo}</body></html>"
    )


def gerar(relatorio: Relatorio, graficos: dict[str, list[str]], numero: int) -> bytes:
    # importado aqui: o WeasyPrint precisa de bibliotecas do sistema que só os relatórios usam
    from weasyprint import HTML
    from weasyprint.urls import URLFetcher

    return HTML(
        string=montar_html(relatorio, graficos, numero),
        url_fetcher=URLFetcher(allowed_protocols={"data"}),
    ).write_pdf()
