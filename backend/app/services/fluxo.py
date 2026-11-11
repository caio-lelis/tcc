"""Fluxo de uma pergunta (Seção 3.4, Figura 3): os 9 passos, de ponta a ponta.

  1. usuário envia a pergunta
  2. construtor monta o prompt na configuração ativa (C0, C1 ou C2)
  3. 1ª chamada ao modelo: SQL + sugestão de gráfico
  4. validador: consulta de leitura e dentro dos limites?
  5. executor roda no DuckDB (somente leitura)
  6. gerador de visualização confere a sugestão contra o resultado
  7. 2ª chamada ao modelo: texto que descreve o resultado OBTIDO
  8. registro grava tudo (RNF02)
  9. resposta: texto + gráfico + tabela (SQL só no modo avançado)

Se a consulta for recusada ou falhar, o assistente informa que não conseguiu
responder, SEM nova tentativa (sem autocorreção, Seção 3.4), e o registro
guarda a falha com a categoria (D-13).
"""
import time
import uuid
from datetime import datetime, timezone

from app import config
from app.models.contexto import Configuracao
from app.models.registro import Execucao, Origem, ResultadoRegistrado, UsoRegistrado
from app.models.resposta import ErroModelo, FalhaConsulta, RespostaFinal
from app.services import registro, repositorio
from app.services.cliente_llm import ClienteLLM
from app.services.construtor_contexto import montar_prompt
from app.services.executor import executar
from app.services.ingestao import listar_tabelas
from app.services.visualizacao import montar_grafico

MENSAGENS = {
    "recusada": "Não consegui responder a essa pergunta com segurança. Tente perguntar de outra forma.",
    "invalida": "Não consegui montar uma consulta válida para essa pergunta. Tente reformulá-la.",
    "tempo_esgotado": "A consulta demorou demais e foi interrompida. Tente uma pergunta mais específica.",
    "erro_modelo": "O serviço de inteligência artificial está indisponível no momento. Tente de novo em instantes.",
}


def responder(pergunta: str, cliente: ClienteLLM, configuracao: Configuracao | None = None,
              avancado: bool = False, origem: Origem = "interface", rodada: str | None = None,
              pergunta_id: str | None = None, repeticao: int | None = None,
              interpretar: bool = True) -> RespostaFinal:
    inicio = time.perf_counter()
    configuracao = configuracao or config.CONFIGURACAO_PADRAO

    # passo 2: montagem do contexto
    tabelas = listar_tabelas()
    if not tabelas:
        raise ValueError("Nenhuma tabela foi anexada ainda.")
    contexto = repositorio.carregar()
    prompt = montar_prompt(pergunta, configuracao, tabelas, contexto)

    execucao = Execucao(
        id=uuid.uuid4().hex[:12], quando=datetime.now(timezone.utc), origem=origem,
        rodada=rodada, pergunta_id=pergunta_id, repeticao=repeticao,
        pergunta=pergunta.strip(), configuracao=configuracao,
        modelo=getattr(cliente, "modelo", "desconhecido"), esforco=getattr(cliente, "esforco", None),
        hash_contexto=prompt.hash_contexto, hash_prompt=prompt.hash_prompt,
        prompt_sistema=prompt.sistema, prompt_usuario=prompt.usuario,
        status="sucesso", tempo_total_ms=0, versao_codigo=registro.versao_codigo(),
    )
    uso = UsoRegistrado()
    resposta = RespostaFinal(id=execucao.id, status="sucesso", configuracao=configuracao)

    try:
        # passo 3: geração
        geracao = cliente.gerar(prompt)
        uso.geracao = geracao.uso
        execucao.sql, execucao.grafico_sugerido = geracao.sql, geracao.grafico

        # passos 4 e 5: validação e execução
        resultado = executar(geracao.sql)
        execucao.resultado = ResultadoRegistrado(colunas=resultado.colunas, linhas=resultado.linhas,
                                                 truncado=resultado.truncado)
        execucao.tempo_consulta_ms = resultado.tempo_ms

        # passo 6: gráfico
        resposta.grafico = montar_grafico(geracao.grafico, resultado)
        resposta.colunas, resposta.linhas, resposta.truncado = resultado.colunas, resultado.linhas, resultado.truncado

        # passo 7: interpretação (se falhar, a resposta ainda tem gráfico e tabela).
        # O harness a dispensa: a acurácia avalia só o resultado da consulta (Seção 3.6).
        if interpretar:
            try:
                interpretacao = cliente.interpretar(pergunta, resultado)
                uso.interpretacao = interpretacao.uso
                resposta.texto = execucao.texto = interpretacao.texto
            except ErroModelo as erro:
                execucao.erro = f"interpretação indisponível: {erro}"

    except FalhaConsulta as falha:
        execucao.status, execucao.erro = falha.categoria, falha.mensagem
    except ErroModelo as erro:
        execucao.status, execucao.erro = "erro_modelo", str(erro)

    # passo 8: registro
    custos = [u.custo_usd for u in (uso.geracao, uso.interpretacao) if u and u.custo_usd is not None]
    execucao.uso = uso
    execucao.custo_total_usd = round(sum(custos), 6) if custos else None
    execucao.tempo_total_ms = round((time.perf_counter() - inicio) * 1000, 1)
    registro.registrar(execucao)

    # passo 9: resposta
    resposta.status = execucao.status
    resposta.mensagem = MENSAGENS.get(execucao.status)
    if avancado:
        resposta.sql = execucao.sql
    return resposta
