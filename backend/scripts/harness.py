"""Harness do experimento de acurácia (RF07), pela linha de comando.

Rodar de dentro de backend/ (ou no container):

    python -m scripts.harness verificar                      # o banco de perguntas está são?
    python -m scripts.harness congelar                       # grava perguntas.congelado.json
    python -m scripts.harness rodar --rodada piloto --ensaio # ensaio sem custo (responde com o gabarito)
    python -m scripts.harness rodar --rodada oficial         # 20 x 3 x 3 = 180 execuções (gasta API)
    python -m scripts.harness resumir --rodada oficial       # vereditos, acurácia e CSV da análise

No container:  docker compose exec backend python -m scripts.harness verificar

Os dados e o contexto usados são os que estão anexados no Data Talk (dados/).
"rodar" pode ser interrompido e retomado: o que já foi respondido é pulado.
"""
import argparse
import sys
from pathlib import Path

from app import config
from app.models.experimento import CONFIGURACOES, ESTRATOS, Problema
from app.services import harness, registro
from app.services.cliente_llm import ClienteOpenAI

PASTA = config.RAIZ / "experimento"
BANCO = PASTA / "perguntas.yaml"
CONGELADO = PASTA / "perguntas.congelado.json"


def _mostrar(problemas: list[Problema]) -> int:
    """Imprime os problemas e devolve o número de erros."""
    for p in sorted(problemas, key=lambda p: (p.gravidade != "erro", p.pergunta_id or "")):
        print(f"  {p.gravidade.upper():5} {p.pergunta_id or '-':8} {p.mensagem}")
    return sum(p.gravidade == "erro" for p in problemas)


def _pct(valor: float | None) -> str:
    return "   -  " if valor is None else f"{valor * 100:5.1f}%"


def cmd_verificar(args) -> int:
    banco = harness.carregar_banco(args.banco)
    problemas = harness.verificar(banco)
    erros = _mostrar(problemas)
    print(f"{len(banco.perguntas)} pergunta(s): {erros} erro(s), {len(problemas) - erros} aviso(s).")
    return 1 if erros else 0


def cmd_congelar(args) -> int:
    banco = harness.carregar_banco(args.banco)
    try:
        congelado = harness.congelar(banco, args.congelado)
    except harness.BancoInvalido as invalido:
        _mostrar(invalido.problemas)
        print("Banco NÃO congelado: corrija os erros acima.")
        return 1
    except FileExistsError as erro:
        print(erro)
        return 1
    print(f"Congelado em {args.congelado}")
    print(f"  {len(congelado.perguntas)} perguntas | banco {congelado.hash_banco} | "
          f"contexto {congelado.hash_contexto} | código {congelado.versao_codigo}")
    if congelado.versao_codigo.endswith("-modificado"):
        print("  ATENÇÃO: há alterações de código sem commit.")
    return 0


def cmd_rodar(args) -> int:
    congelado = harness.carregar_congelado(args.congelado)
    rodada = args.rodada
    if args.ensaio:
        cliente = harness.ClienteGabarito(congelado)
        rodada = rodada if rodada.startswith("ensaio") else f"ensaio-{rodada}"
    else:
        cliente = ClienteOpenAI()
        print(f"Modelo: {cliente.modelo} | esforço: {cliente.esforco} | código: {registro.versao_codigo()}")
        if registro.versao_codigo().endswith("-modificado"):
            print("ATENÇÃO: há alterações de código sem commit; a rodada não será reproduzível pelo commit.")

    def avancar(feito, total, execucao):
        situacao = execucao.status if execucao else "FALHA DE INFRAESTRUTURA (refazer)"
        rotulo = f"{execucao.pergunta_id}/{execucao.configuracao}/r{execucao.repeticao}" if execucao else ""
        print(f"  [{feito:3}/{total}] {rotulo:16} {situacao}", flush=True)

    try:
        arquivo = harness.rodar(congelado, cliente, rodada, args.configuracoes, args.repeticoes,
                                interpretar=args.com_interpretacao, ao_avancar=avancar)
    except harness.BancoInvalido as invalido:
        _mostrar(invalido.problemas)
        print("Rodada NÃO iniciada: o ambiente não é o do congelamento.")
        return 1
    print(f"Registro: {arquivo}")
    print(f"Agora: python -m scripts.harness resumir --rodada {rodada}")
    return 0


def cmd_resumir(args) -> int:
    congelado = harness.carregar_congelado(args.congelado)
    arquivo = registro.caminho_registro("experimento", args.rodada)
    execucoes = registro.ler(arquivo)
    if not execucoes:
        print(f"Nenhuma execução em {arquivo}")
        return 1
    revisao = args.revisao or arquivo.with_suffix(".revisao.yaml")
    resumo, avaliacoes = harness.resumir(congelado, execucoes, harness.carregar_revisao(revisao),
                                         args.repeticoes, args.rodada)
    configuracoes = list(resumo.acuracia)

    print(f"Rodada {args.rodada}: {resumo.execucoes} execuções válidas, {resumo.refeitas} refeita(s) por "
          f"falha de infraestrutura, {len(resumo.faltando)} faltando. Custo: US$ {resumo.custo_usd:.4f}")
    if resumo.faltando:
        print("  faltando: " + ", ".join(resumo.faltando[:12]) + (" ..." if len(resumo.faltando) > 12 else ""))

    print("\nAcurácia de execução, pela maioria das repetições (Q1, Q2)")
    print(f"  {'':10}" + "".join(f"{c:>8}" for c in configuracoes))
    print(f"  {'geral':10}" + "".join(f"{_pct(resumo.acuracia[c]):>8}" for c in configuracoes))
    for estrato in ESTRATOS:
        linha = resumo.acuracia_por_estrato[estrato]
        print(f"  {estrato:10}" + "".join(f"{_pct(linha[c]):>8}" for c in configuracoes))

    print("\nConsistência entre repetições (Q4)")
    print(f"  {'':10}" + "".join(f"{_pct(resumo.consistencia[c]):>8}" for c in configuracoes))

    print("\nRespostas erradas por categoria (Q3; 'sem_categoria' = classificar na revisão)")
    for configuracao in configuracoes:
        partes = ", ".join(f"{k}: {v}" for k, v in resumo.erros_por_categoria[configuracao].items()) or "nenhuma"
        print(f"  {configuracao}  {partes}")

    pendentes = [a for a in avaliacoes if a.limitrofe or (not a.acerto and not a.categoria)]
    if pendentes:
        print(f"\nPara a revisão manual ({revisao.name}): {len(pendentes)} execução(ões)")
        for a in pendentes:
            motivo = a.limitrofe or "sem categoria de erro"
            dica = f" | coincide com: {a.alternativa} ({a.categoria_sugerida or '?'})" if a.alternativa else ""
            print(f"  {a.execucao}  {a.pergunta_id}/{a.configuracao}/r{a.repeticao}  {motivo}{dica}")

    destino = PASTA / "analise" / f"{registro.normalizar_nome(args.rodada)}.csv"
    harness.gravar_csv(avaliacoes, destino)
    destino.with_suffix(".resumo.json").write_text(resumo.model_dump_json(indent=2), encoding="utf-8", newline="\n")
    print(f"\nGravado: {destino} e {destino.with_suffix('.resumo.json').name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(prog="python -m scripts.harness", description="Harness do experimento (RF07)")
    comandos = analisador.add_subparsers(dest="comando", required=True)

    def comum(nome, funcao, ajuda):
        sub = comandos.add_parser(nome, help=ajuda)
        sub.set_defaults(funcao=funcao)
        return sub

    for nome, funcao, ajuda in (("verificar", cmd_verificar, "confere gabaritos e alternativas (D-16)"),
                                ("congelar", cmd_congelar, "grava o banco congelado")):
        sub = comum(nome, funcao, ajuda)
        sub.add_argument("--banco", type=Path, default=BANCO)
        sub.add_argument("--congelado", type=Path, default=CONGELADO)

    sub = comum("rodar", cmd_rodar, "executa perguntas x configurações x repetições")
    sub.add_argument("--rodada", required=True, help="nome da rodada (ex.: piloto, oficial)")
    sub.add_argument("--congelado", type=Path, default=CONGELADO)
    sub.add_argument("--configuracoes", nargs="+", choices=CONFIGURACOES, default=list(CONFIGURACOES))
    sub.add_argument("--repeticoes", type=int, default=harness.REPETICOES)
    sub.add_argument("--ensaio", action="store_true", help="sem API: responde com o gabarito")
    sub.add_argument("--com-interpretacao", action="store_true", help="faz também a 2ª chamada (texto)")

    sub = comum("resumir", cmd_resumir, "vereditos, acurácia, consistência e CSV da análise")
    sub.add_argument("--rodada", required=True)
    sub.add_argument("--congelado", type=Path, default=CONGELADO)
    sub.add_argument("--revisao", type=Path, default=None, help="padrão: <rodada>.revisao.yaml ao lado do registro")
    sub.add_argument("--repeticoes", type=int, default=harness.REPETICOES)

    args = analisador.parse_args(argv)
    return args.funcao(args)


if __name__ == "__main__":
    sys.exit(main())
