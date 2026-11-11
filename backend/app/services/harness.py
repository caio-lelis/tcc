"""Harness do experimento (RF07): executa o banco de perguntas em todas as
configurações e repetições e compara cada resultado com o gabarito.

Quatro passos, na ordem:

  1. verificar  o banco escrito à mão está são? Cada gabarito executa, e cada
                interpretação errada plausível dá resultado DIFERENTE do gabarito (D-16).
  2. congelar   grava o banco com o resultado esperado e as impressões digitais.
                Daqui em diante, perguntas e gabaritos não mudam (Seção 4.5).
  3. rodar      perguntas x configurações x repetições, pelo MESMO fluxo da
                interface (services/fluxo.py), sem intervenção manual (Seção 4.6.2).
  4. avaliar    veredito de cada execução pela regra de acerto (Seção 4.6.3),
                maioria das repetições, consistência e contagens (Q1 a Q4).

O harness não tem lógica própria de geração nem de execução: tudo passa por
fluxo.responder, para que o experimento meça o assistente que o usuário usa.
"""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

import yaml

from app import config
from app.models.contexto import Configuracao, PromptMontado
from app.models.experimento import (
    CONFIGURACOES, ESTRATOS, AlternativaCongelada, Avaliacao, BancoCongelado, BancoPerguntas, ItemCongelado,
    Problema, Resumo, Revisao, Tabela, VereditoPergunta,
)
from app.models.registro import Execucao
from app.models.resposta import FalhaConsulta, RespostaGeracao, RespostaInterpretacao, ResultadoConsulta
from app.models.resposta import SugestaoGrafico, UsoModelo
from app.services import fluxo, registro, repositorio
from app.services.cliente_llm import ClienteLLM
from app.services.comparacao import comparar
from app.services.executor import executar

REPETICOES = 3  # Seção 4.6.2
PERGUNTAS_POR_ESTRATO = 5  # Seção 4.5
TENTATIVAS_INFRA = 3  # falha de rede ou de saldo: refaz, não conta como erro do modelo
_FALHAS_DA_CONSULTA = ("invalida", "recusada", "tempo_esgotado")


class BancoInvalido(Exception):
    """O banco de perguntas (ou o ambiente) não está em condições de seguir."""

    def __init__(self, problemas: list[Problema]):
        super().__init__("; ".join(p.mensagem for p in problemas))
        self.problemas = problemas


# ---------------------------------------------------------------- 1. verificar

def carregar_banco(arquivo: Path) -> BancoPerguntas:
    dados = yaml.safe_load(Path(arquivo).read_text(encoding="utf-8"))
    if isinstance(dados, list):  # aceita a lista direta, sem a chave "perguntas"
        dados = {"perguntas": dados}
    return BancoPerguntas.model_validate(dados)


def _executar_referencia(sql: str) -> tuple[Tabela | None, str | None]:
    """Roda uma consulta do banco de perguntas. Devolve (resultado, motivo da falha)."""
    try:
        resultado = executar(sql)
    except FalhaConsulta as falha:
        return None, f"[{falha.categoria}] {falha.mensagem}"
    if resultado.truncado:
        return None, f"passa de {config.LIMITE_LINHAS} linhas, o limite do assistente (RNF04)"
    return Tabela(colunas=resultado.colunas, linhas=resultado.linhas), None


def _resolver(banco: BancoPerguntas) -> tuple[list[ItemCongelado], list[Problema]]:
    """Executa gabaritos e alternativas. Só devolve itens se não houver erro."""
    problemas: list[Problema] = []
    itens: list[ItemCongelado] = []

    for item in banco.perguntas:
        def erro(mensagem: str, item=item):
            problemas.append(Problema(gravidade="erro", pergunta_id=item.id, mensagem=mensagem))

        def aviso(mensagem: str, item=item):
            problemas.append(Problema(gravidade="aviso", pergunta_id=item.id, mensagem=mensagem))

        esperado, falha = _executar_referencia(item.sql_gabarito)
        if esperado is None:
            erro(f"o gabarito não executa: {falha}")
            continue
        if not esperado.linhas:
            aviso("o gabarito não devolve nenhuma linha")
        if item.estrato == "regra" and not item.regra_envolvida:
            aviso("estrato 'regra' sem o campo regra_envolvida")
        if not item.consultas_alternativas:
            aviso("sem consultas alternativas: não há como garantir que a pergunta discrimina (D-16)")

        alternativas = []
        for alternativa in item.consultas_alternativas:
            resultado, falha = _executar_referencia(alternativa.sql)
            if resultado is None:
                erro(f"a alternativa '{alternativa.descricao}' não executa: {falha}")
            elif comparar(esperado.linhas, resultado.linhas, item.ordenada).igual:
                erro(f"a alternativa '{alternativa.descricao}' dá o MESMO resultado do gabarito: "
                     "a pergunta não distingue essa interpretação errada (D-16)")
            else:
                alternativas.append(AlternativaCongelada(**alternativa.model_dump(), resultado=resultado))

        itens.append(ItemCongelado(
            **item.model_dump(exclude={"consultas_alternativas"}),
            resultado_esperado=esperado, consultas_alternativas=alternativas,
        ))

    por_estrato = Counter(item.estrato for item in banco.perguntas)
    for estrato in ESTRATOS:
        if por_estrato[estrato] != PERGUNTAS_POR_ESTRATO:
            problemas.append(Problema(
                gravidade="aviso",
                mensagem=f"estrato '{estrato}' tem {por_estrato[estrato]} pergunta(s); a Seção 4.5 prevê {PERGUNTAS_POR_ESTRATO}",
            ))
    return itens, problemas


def verificar(banco: BancoPerguntas) -> list[Problema]:
    """Erros impedem o congelamento; avisos não."""
    return _resolver(banco)[1]


# ---------------------------------------------------------------- 2. congelar

def _hash_banco(itens: list[ItemCongelado]) -> str:
    texto = json.dumps([i.model_dump(mode="json") for i in itens], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def congelar(banco: BancoPerguntas, destino: Path) -> BancoCongelado:
    """Grava o banco congelado. Recusa se houver erro na verificação ou se o arquivo já existir."""
    destino = Path(destino)
    if destino.exists():
        raise FileExistsError(f"{destino} já existe: um banco congelado não é regravado (Seção 4.5).")
    itens, problemas = _resolver(banco)
    erros = [p for p in problemas if p.gravidade == "erro"]
    if erros:
        raise BancoInvalido(erros)

    contexto = repositorio.carregar()
    congelado = BancoCongelado(
        congelado_em=datetime.now(timezone.utc), versao_codigo=registro.versao_codigo(),
        hash_banco=_hash_banco(itens), hash_contexto=repositorio.calcular_hash(contexto),
        contexto=contexto, perguntas=itens,
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(congelado.model_dump_json(indent=2), encoding="utf-8", newline="\n")
    return congelado


def carregar_congelado(arquivo: Path) -> BancoCongelado:
    congelado = BancoCongelado.model_validate_json(Path(arquivo).read_text(encoding="utf-8"))
    if _hash_banco(congelado.perguntas) != congelado.hash_banco:
        raise BancoInvalido([Problema(gravidade="erro", mensagem=(
            f"{arquivo} foi alterado depois do congelamento (a impressão digital não confere)."))])
    return congelado


def conferir_ambiente(congelado: BancoCongelado) -> list[Problema]:
    """Antes de rodar: os dados e o contexto ainda são os do congelamento?"""
    problemas = []
    atual = repositorio.calcular_hash(repositorio.carregar())
    if atual != congelado.hash_contexto:
        problemas.append(Problema(gravidade="erro", mensagem=(
            f"o contexto cadastrado ({atual}) não é o do congelamento ({congelado.hash_contexto}): "
            "descrições ou regras mudaram.")))
    for item in congelado.perguntas:
        resultado, falha = _executar_referencia(item.sql_gabarito)
        if resultado is None:
            problemas.append(Problema(gravidade="erro", pergunta_id=item.id,
                                      mensagem=f"o gabarito não executa mais: {falha}"))
        elif not comparar(item.resultado_esperado.linhas, resultado.linhas, item.ordenada).igual:
            problemas.append(Problema(gravidade="erro", pergunta_id=item.id, mensagem=(
                "o gabarito dá hoje um resultado diferente do congelado: os dados mudaram.")))
    return problemas


# ---------------------------------------------------------------- 3. rodar

def _chave(execucao: Execucao) -> tuple[str, str, int]:
    return (execucao.pergunta_id or "", execucao.configuracao, execucao.repeticao or 0)


def _validas(execucoes: Iterable[Execucao]) -> dict[tuple[str, str, int], Execucao]:
    """Uma execução por (pergunta, configuração, repetição): a primeira que não foi
    falha de infraestrutura. Repetir uma combinação já respondida não troca o veredito."""
    validas: dict[tuple[str, str, int], Execucao] = {}
    for execucao in execucoes:
        if execucao.status != "erro_modelo":
            validas.setdefault(_chave(execucao), execucao)
    return validas


def rodar(congelado: BancoCongelado, cliente: ClienteLLM, rodada: str,
          configuracoes: Iterable[Configuracao] = CONFIGURACOES, repeticoes: int = REPETICOES,
          interpretar: bool = False, ao_avancar: Callable[[int, int, Execucao | None], None] | None = None) -> Path:
    """Executa o que falta da rodada e devolve o arquivo de registro.

    Pode ser interrompida e retomada: combinações já respondidas são puladas.
    Falhas de infraestrutura (erro_modelo) são refeitas até TENTATIVAS_INFRA vezes.
    A interpretação fica desligada por padrão: a métrica avalia só a consulta.
    """
    problemas = conferir_ambiente(congelado)
    if problemas:
        raise BancoInvalido(problemas)

    arquivo = registro.caminho_registro("experimento", rodada)
    feitas = _validas(registro.ler(arquivo))
    configuracoes = list(configuracoes)
    total = len(congelado.perguntas) * len(configuracoes) * repeticoes
    feito = 0

    for repeticao in range(1, repeticoes + 1):
        for item in congelado.perguntas:
            for configuracao in configuracoes:
                feito += 1
                if (item.id, configuracao, repeticao) in feitas:
                    continue
                execucao = None
                for _ in range(TENTATIVAS_INFRA):
                    resposta = fluxo.responder(
                        item.pergunta, cliente, configuracao, origem="experimento", rodada=rodada,
                        pergunta_id=item.id, repeticao=repeticao, interpretar=interpretar,
                    )
                    if resposta.status != "erro_modelo":
                        execucao = registro.ler(arquivo)[-1]
                        break
                if ao_avancar:
                    ao_avancar(feito, total, execucao)
    return arquivo


class ClienteGabarito:
    """Ensaio sem custo: responde cada pergunta com o próprio gabarito.

    Serve para testar o caminho inteiro (rodar, registrar, avaliar) antes de
    gastar API. Uma rodada de ensaio tem de dar 100% em tudo.
    """

    modelo = "ensaio-gabarito"
    esforco = None

    def __init__(self, congelado: BancoCongelado):
        self._sql = {item.pergunta.strip(): item.sql_gabarito for item in congelado.perguntas}

    def gerar(self, prompt: PromptMontado) -> RespostaGeracao:
        pergunta = prompt.usuario.rsplit("Pergunta: ", 1)[-1].strip()
        return RespostaGeracao(sql=self._sql[pergunta], grafico=SugestaoGrafico(tipo="tabela"), uso=self._uso())

    def interpretar(self, pergunta: str, resultado: ResultadoConsulta) -> RespostaInterpretacao:
        return RespostaInterpretacao(texto="Ensaio.", uso=self._uso())

    @staticmethod
    def _uso() -> UsoModelo:
        return UsoModelo(modelo="ensaio-gabarito", tokens_entrada=0, tokens_saida=0, custo_usd=0.0, tempo_ms=0.0)


# ---------------------------------------------------------------- 4. avaliar

def carregar_revisao(arquivo: Path | None) -> dict[str, Revisao]:
    if not arquivo or not Path(arquivo).exists():
        return {}
    dados = yaml.safe_load(Path(arquivo).read_text(encoding="utf-8")) or []
    return {r.execucao: r for r in (Revisao.model_validate(d) for d in dados)}


def avaliar(congelado: BancoCongelado, execucoes: Iterable[Execucao],
            revisao: dict[str, Revisao] | None = None) -> list[Avaliacao]:
    """Veredito de cada execução válida, pela regra de acerto (Seção 4.6.3)."""
    revisao = revisao or {}
    itens = {item.id: item for item in congelado.perguntas}
    avaliacoes = []

    for execucao in _validas(execucoes).values():
        item = itens.get(execucao.pergunta_id or "")
        if item is None:
            continue  # execução de outro banco de perguntas
        avaliacao = Avaliacao(
            rodada=execucao.rodada or "", execucao=execucao.id, pergunta_id=item.id, estrato=item.estrato,
            configuracao=execucao.configuracao, repeticao=execucao.repeticao or 0, status=execucao.status,
            acerto=False, acerto_automatico=False,
            custo_usd=execucao.custo_total_usd, tempo_total_ms=execucao.tempo_total_ms,
        )

        if execucao.status in _FALHAS_DA_CONSULTA:
            avaliacao.categoria = execucao.status  # a consulta não produziu resultado
        elif execucao.resultado is not None:
            obtido = execucao.resultado
            comparacao = comparar(item.resultado_esperado.linhas, obtido.linhas, item.ordenada, obtido.truncado)
            avaliacao.acerto = avaliacao.acerto_automatico = comparacao.igual
            avaliacao.limitrofe = comparacao.limitrofe
            if not comparacao.igual:
                for alternativa in item.consultas_alternativas:
                    if comparar(alternativa.resultado.linhas, obtido.linhas, item.ordenada).igual:
                        avaliacao.alternativa = alternativa.descricao
                        avaliacao.categoria_sugerida = alternativa.categoria
                        break

        decisao = revisao.get(execucao.id)
        if decisao:
            if decisao.acerto is not None:
                avaliacao.acerto = decisao.acerto
            if decisao.categoria:
                avaliacao.categoria = decisao.categoria
            avaliacao.justificativa = decisao.justificativa
            avaliacao.limitrofe = None  # já decidido
        if avaliacao.acerto:
            avaliacao.categoria = avaliacao.categoria_sugerida = avaliacao.alternativa = None
        avaliacoes.append(avaliacao)

    ordem = {item.id: n for n, item in enumerate(congelado.perguntas)}
    return sorted(avaliacoes, key=lambda a: (ordem[a.pergunta_id], a.configuracao, a.repeticao))


def _proporcao(valores: list[bool]) -> float | None:
    return round(sum(valores) / len(valores), 4) if valores else None


def resumir(congelado: BancoCongelado, execucoes: list[Execucao], revisao: dict[str, Revisao] | None = None,
            repeticoes: int = REPETICOES, rodada: str = "") -> tuple[Resumo, list[Avaliacao]]:
    """Maioria das repetições, acurácia (Q1, Q2), erros (Q3) e consistência (Q4)."""
    avaliacoes = avaliar(congelado, execucoes, revisao)
    grupos: dict[tuple[str, str], list[Avaliacao]] = defaultdict(list)
    for a in avaliacoes:
        grupos[(a.pergunta_id, a.configuracao)].append(a)

    configuracoes = [c for c in CONFIGURACOES if any(a.configuracao == c for a in avaliacoes)]
    vereditos, faltando = [], []
    for item in congelado.perguntas:
        for configuracao in configuracoes:
            grupo = grupos.get((item.id, configuracao), [])
            feitas = {a.repeticao for a in grupo}
            faltando += [f"{item.id}/{configuracao}/r{r}" for r in range(1, repeticoes + 1) if r not in feitas]
            if not grupo:
                continue
            acertos = sum(a.acerto for a in grupo)
            vereditos.append(VereditoPergunta(
                pergunta_id=item.id, estrato=item.estrato, configuracao=configuracao,
                repeticoes=len(grupo), acertos=acertos, acerto=acertos * 2 > len(grupo),
                consistente=acertos in (0, len(grupo)), completo=len(grupo) >= repeticoes,
            ))

    def de(configuracao: str, estrato: str | None = None) -> list[VereditoPergunta]:
        return [v for v in vereditos if v.configuracao == configuracao and estrato in (None, v.estrato)]

    erros: dict[str, dict[str, int]] = {}
    for configuracao in configuracoes:
        contagem = Counter(a.categoria or "sem_categoria" for a in avaliacoes
                           if a.configuracao == configuracao and not a.acerto)
        erros[configuracao] = dict(sorted(contagem.items()))

    resumo = Resumo(
        rodada=rodada, repeticoes_previstas=repeticoes, execucoes=len(avaliacoes),
        refeitas=sum(e.status == "erro_modelo" for e in execucoes), faltando=faltando, vereditos=vereditos,
        acuracia={c: _proporcao([v.acerto for v in de(c)]) for c in configuracoes},
        acuracia_por_estrato={e: {c: _proporcao([v.acerto for v in de(c, e)]) for c in configuracoes}
                              for e in ESTRATOS},
        erros_por_categoria=erros,
        consistencia={c: _proporcao([v.consistente for v in de(c)]) for c in configuracoes},
        limitrofes=sum(a.limitrofe is not None for a in avaliacoes),
        custo_usd=round(sum(e.custo_total_usd or 0 for e in execucoes), 4),
    )
    return resumo, avaliacoes


def gravar_csv(avaliacoes: list[Avaliacao], destino: Path) -> Path:
    """Uma linha por execução: entrada da análise estatística (Seção 4.8)."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    campos = list(Avaliacao.model_fields)
    with destino.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(a.model_dump(mode="json") for a in avaliacoes)
    return destino
