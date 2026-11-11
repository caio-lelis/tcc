"""Testes do harness do experimento (RF07). Nenhum teste chama a API (D-12)."""
import csv

import pytest

from app import config
from app.models.experimento import BancoPerguntas, Revisao
from app.models.resposta import ErroModelo
from app.services import harness, registro
from app.services.cliente_llm import ModeloFalso
from app.services.ingestao import ingerir_csv
from scripts import harness as cli
from tests.conftest import PASTA_EXEMPLO

BANCO_EXEMPLO = config.RAIZ / "experimento" / "exemplo" / "perguntas.yaml"

VENDAS_ABRIL = ("SELECT COUNT(*) FROM contratos WHERE data_assinatura BETWEEN '2026-04-01' AND '2026-04-30' "
                "AND NOT (data_cancelamento IS NOT NULL AND date_diff('day', data_assinatura, data_cancelamento) <= 7)")
CRIADOS_ABRIL = "SELECT COUNT(*) FROM contratos WHERE data_criacao BETWEEN '2026-04-01' AND '2026-04-30'"


@pytest.fixture
def cenario(csv_exemplo):
    for nome in ("vendedores", "clientes", "reunioes", "contratos"):
        ingerir_csv(csv_exemplo(nome), f"{nome}.csv")
    config.ARQUIVO_CONTEXTO.write_text((PASTA_EXEMPLO / "contexto_exemplo.json").read_text(encoding="utf-8"),
                                       encoding="utf-8")


def _banco(*itens) -> BancoPerguntas:
    return BancoPerguntas.model_validate({"perguntas": list(itens)})


def _item(**campos):
    base = {"id": "P01", "pergunta": "Quantas vendas houve em abril de 2026?", "estrato": "regra",
            "sql_gabarito": VENDAS_ABRIL, "regra_envolvida": "regras 1 e 2",
            "consultas_alternativas": [{"descricao": "criados em abril", "sql": CRIADOS_ABRIL,
                                        "categoria": "data_periodo"}]}
    return {**base, **campos}


@pytest.fixture
def congelado(cenario, tmp_path):
    return harness.congelar(_banco(_item()), tmp_path / "congelado.json")


def _erros(problemas):
    return [p.mensagem for p in problemas if p.gravidade == "erro"]


# ---------------------------------------------------------------- verificar

def test_banco_de_exemplo_passa_na_verificacao(cenario):
    banco = harness.carregar_banco(BANCO_EXEMPLO)
    assert len(banco.perguntas) == 8
    assert _erros(harness.verificar(banco)) == []


def test_alternativa_que_coincide_com_o_gabarito_e_erro(cenario):
    # D-16: em março nenhum contrato caiu no arrependimento; ignorar a regra dá o mesmo número
    marco = VENDAS_ABRIL.replace("04-01", "03-01").replace("04-30", "03-31")
    sem_regra = "SELECT COUNT(*) FROM contratos WHERE data_assinatura BETWEEN '2026-03-01' AND '2026-03-31'"
    banco = _banco(_item(sql_gabarito=marco, consultas_alternativas=[{"descricao": "sem a regra", "sql": sem_regra}]))
    [erro] = _erros(harness.verificar(banco))
    assert "MESMO resultado" in erro and "sem a regra" in erro


def test_gabarito_ou_alternativa_que_nao_executa_e_erro(cenario):
    banco = _banco(
        _item(id="P01", sql_gabarito="SELECT COUNT(*) FROM tabela_que_nao_existe"),
        _item(id="P02", consultas_alternativas=[{"descricao": "apaga", "sql": "DELETE FROM contratos"}]),
    )
    erros = _erros(harness.verificar(banco))
    assert any("gabarito não executa" in e for e in erros) and any("'apaga' não executa" in e for e in erros)


def test_avisos_nao_impedem(cenario):
    problemas = harness.verificar(_banco(_item(consultas_alternativas=[], regra_envolvida=None)))
    assert _erros(problemas) == []
    avisos = " ".join(p.mensagem for p in problemas)
    assert "sem consultas alternativas" in avisos and "regra_envolvida" in avisos and "prevê 5" in avisos


def test_ids_repetidos_sao_recusados():
    with pytest.raises(ValueError, match="ids repetidos"):
        _banco(_item(), _item())


# ---------------------------------------------------------------- congelar

def test_congelar_grava_resultado_esperado_e_hashes(congelado, tmp_path):
    [item] = congelado.perguntas
    assert item.resultado_esperado.linhas == [[13]]
    assert item.consultas_alternativas[0].resultado.linhas == [[24]]
    assert congelado.contexto.regras and len(congelado.hash_contexto) == 12

    relido = harness.carregar_congelado(tmp_path / "congelado.json")
    assert relido.hash_banco == congelado.hash_banco


def test_congelar_recusa_banco_com_erro_e_arquivo_existente(cenario, congelado, tmp_path):
    with pytest.raises(FileExistsError):
        harness.congelar(_banco(_item()), tmp_path / "congelado.json")
    with pytest.raises(harness.BancoInvalido):
        harness.congelar(_banco(_item(sql_gabarito="SELECT nada")), tmp_path / "outro.json")
    assert not (tmp_path / "outro.json").exists()


def test_banco_congelado_alterado_e_denunciado(congelado, tmp_path):
    arquivo = tmp_path / "congelado.json"
    arquivo.write_text(arquivo.read_text(encoding="utf-8").replace("abril de 2026", "maio de 2026"), encoding="utf-8")
    with pytest.raises(harness.BancoInvalido, match="alterado depois do congelamento"):
        harness.carregar_congelado(arquivo)


# ---------------------------------------------------------------- rodar

def test_rodar_executa_tudo_e_registra(congelado):
    modelo = ModeloFalso(sql=VENDAS_ABRIL)
    arquivo = harness.rodar(congelado, modelo, "piloto")
    execucoes = registro.ler(arquivo)

    assert len(execucoes) == 9  # 1 pergunta x 3 configurações x 3 repetições
    assert {(e.configuracao, e.repeticao) for e in execucoes} == {(c, r) for c in ("C0", "C1", "C2") for r in (1, 2, 3)}
    assert all(e.origem == "experimento" and e.rodada == "piloto" and e.pergunta_id == "P01" for e in execucoes)
    assert modelo.interpretacoes == []  # sem a 2ª chamada: a métrica avalia só a consulta
    assert len({e.hash_prompt for e in execucoes if e.configuracao == "C2"}) == 1  # mesmo texto nas repetições


def test_rodar_retoma_de_onde_parou(congelado):
    harness.rodar(congelado, ModeloFalso(sql=VENDAS_ABRIL), "piloto", configuracoes=["C0"], repeticoes=2)
    modelo = ModeloFalso(sql=VENDAS_ABRIL)
    arquivo = harness.rodar(congelado, modelo, "piloto")
    assert len(modelo.prompts) == 7 and len(registro.ler(arquivo)) == 9


def test_falha_de_infraestrutura_e_refeita_e_nao_conta(congelado):
    chamadas = []

    def instavel(prompt):
        chamadas.append(prompt)
        if len(chamadas) == 1:
            raise ErroModelo("sem rede")
        return VENDAS_ABRIL

    arquivo = harness.rodar(congelado, ModeloFalso(sql=instavel), "piloto", configuracoes=["C2"], repeticoes=1)
    execucoes = registro.ler(arquivo)
    assert [e.status for e in execucoes] == ["erro_modelo", "sucesso"]

    resumo, avaliacoes = harness.resumir(congelado, execucoes, repeticoes=1)
    assert resumo.refeitas == 1 and len(avaliacoes) == 1 and resumo.acuracia == {"C2": 1.0}


def test_rodar_recusa_se_o_contexto_ou_os_dados_mudaram(congelado, csv_exemplo):
    from app.models.contexto import RegraEntrada
    from app.services import repositorio

    repositorio.adicionar_regra(RegraEntrada(texto="Regra nova, depois do congelamento."))
    with pytest.raises(harness.BancoInvalido, match="contexto cadastrado"):
        harness.rodar(congelado, ModeloFalso(), "piloto")


def test_rodar_recusa_se_os_dados_mudaram(congelado):
    linhas = (PASTA_EXEMPLO / "contratos.csv").read_text(encoding="utf-8").splitlines()
    ingerir_csv("\n".join(linhas[:100]).encode("utf-8"), "contratos.csv")
    with pytest.raises(harness.BancoInvalido, match="os dados mudaram"):
        harness.rodar(congelado, ModeloFalso(), "piloto")


# ---------------------------------------------------------------- avaliar

def _rodar_por_configuracao(congelado, sql_por_configuracao, rodada="piloto"):
    modelo = ModeloFalso(sql=lambda prompt: sql_por_configuracao[prompt.configuracao])
    return registro.ler(harness.rodar(congelado, modelo, rodada))


def test_resumo_acuracia_erros_e_alternativa_que_coincidiu(congelado):
    execucoes = _rodar_por_configuracao(congelado, {
        "C0": CRIADOS_ABRIL,  # cai na interpretação errada prevista
        "C1": "SELECT COUNT(*) FROM contratoz",  # consulta inválida
        "C2": VENDAS_ABRIL,
    })
    resumo, avaliacoes = harness.resumir(congelado, execucoes, rodada="piloto")

    assert resumo.acuracia == {"C0": 0.0, "C1": 0.0, "C2": 1.0}
    assert resumo.acuracia_por_estrato["regra"] == {"C0": 0.0, "C1": 0.0, "C2": 1.0}
    assert resumo.acuracia_por_estrato["simples"]["C2"] is None
    assert resumo.consistencia == {"C0": 1.0, "C1": 1.0, "C2": 1.0}
    assert resumo.erros_por_categoria == {"C0": {"sem_categoria": 3}, "C1": {"invalida": 3}, "C2": {}}
    assert resumo.faltando == []

    c0 = next(a for a in avaliacoes if a.configuracao == "C0")
    assert c0.alternativa == "criados em abril" and c0.categoria_sugerida == "data_periodo" and c0.categoria is None


def test_maioria_e_consistencia(congelado):
    respostas = iter([VENDAS_ABRIL, CRIADOS_ABRIL, VENDAS_ABRIL])  # 2 de 3 certas
    modelo = ModeloFalso(sql=lambda prompt: next(respostas))
    execucoes = registro.ler(harness.rodar(congelado, modelo, "piloto", configuracoes=["C2"]))
    resumo, _ = harness.resumir(congelado, execucoes)

    [veredito] = resumo.vereditos
    assert (veredito.acertos, veredito.acerto, veredito.consistente, veredito.completo) == (2, True, False, True)
    assert resumo.acuracia == {"C2": 1.0} and resumo.consistencia == {"C2": 0.0}


def test_repeticoes_faltando_aparecem_no_resumo(congelado):
    execucoes = registro.ler(harness.rodar(congelado, ModeloFalso(sql=VENDAS_ABRIL), "piloto",
                                           configuracoes=["C2"], repeticoes=2))
    resumo, _ = harness.resumir(congelado, execucoes)
    assert resumo.faltando == ["P01/C2/r3"] and not resumo.vereditos[0].completo


def test_revisao_manual_decide_limitrofe_e_categoria(congelado):
    com_coluna_extra = VENDAS_ABRIL.replace("COUNT(*)", "COUNT(*), 'abril' AS mes")
    execucoes = _rodar_por_configuracao(congelado, {"C0": CRIADOS_ABRIL, "C1": com_coluna_extra, "C2": VENDAS_ABRIL})
    _, antes = harness.resumir(congelado, execucoes)
    extra = next(a for a in antes if a.configuracao == "C1")
    errada = next(a for a in antes if a.configuracao == "C0")
    assert not extra.acerto and "mais 1" in extra.limitrofe

    revisao = {
        extra.execucao: Revisao(execucao=extra.execucao, acerto=True, justificativa="coluna a mais só rotula o mês"),
        errada.execucao: Revisao(execucao=errada.execucao, categoria="data_periodo", justificativa="usou a criação"),
    }
    resumo, depois = harness.resumir(congelado, execucoes, revisao)
    revista = next(a for a in depois if a.execucao == extra.execucao)
    assert revista.acerto and not revista.acerto_automatico and revista.limitrofe is None
    assert resumo.erros_por_categoria["C0"] == {"data_periodo": 1, "sem_categoria": 2}
    assert resumo.limitrofes == 2  # as outras duas repetições do C1 seguem pendentes


# ---------------------------------------------------------------- ponta a ponta (linha de comando)

def test_ensaio_pela_linha_de_comando_da_cem_por_cento(cenario, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "PASTA", tmp_path / "experimento")
    congelado = tmp_path / "experimento" / "perguntas.congelado.json"
    comum = ["--congelado", str(congelado)]

    assert cli.main(["verificar", "--banco", str(BANCO_EXEMPLO)]) == 0
    assert cli.main(["congelar", "--banco", str(BANCO_EXEMPLO), *comum]) == 0
    assert cli.main(["rodar", "--rodada", "piloto", "--ensaio", *comum]) == 0
    assert cli.main(["resumir", "--rodada", "ensaio-piloto", *comum]) == 0

    saida = capsys.readouterr().out
    assert "72 execuções válidas" in saida and "0 faltando" in saida  # 8 x 3 x 3

    with (tmp_path / "experimento" / "analise" / "ensaio_piloto.csv").open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == 72 and all(linha["acerto"] == "True" for linha in linhas)
