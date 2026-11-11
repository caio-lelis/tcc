// Estado dos relatórios ao vivo, compartilhado pela conversa, pelo painel e pela aba Relatórios.
// Texto digitado é salvo sozinho. Gravações e operações no servidor passam por uma fila única:
// duas nunca correm juntas, e o que a pessoa digita durante uma delas não se perde.
import { reactive } from "vue";
import { api } from "./api.js";
import { avisar } from "./avisos.js";
import { svgsParaPdf } from "./graficoOpcoes.js";

const ESPERA_SALVAR = 700;
const ESPERA_NOVA_TENTATIVA = 5000;

export const relatorios = reactive({
  lista: [],
  atual: null,
  versoes: [],
  situacao: "salvo", // salvo | pendente | salvando | erro
  painelAberto: false,
  exportando: false,
  atualizando: new Set(), // blocos com consulta em andamento
  anexados: new Set(), // execuções já anexadas ao relatório atual
});

let temporizador = null;
let gravacao = null; // promessa da operação em andamento na fila
let sujo = false;

const novoId = () => crypto.randomUUID().replaceAll("-", "");

function trocarAtual(relatorio) {
  relatorios.atual = relatorio;
  sujo = false;
  relatorios.situacao = "salvo";
}

async function gravar() {
  const atual = relatorios.atual;
  sujo = false;
  relatorios.situacao = "salvando";
  try {
    const salvo = await api.editarRelatorio(atual.id, {
      titulo: atual.titulo.trim() || "Relatório sem título",
      blocos: atual.blocos,
      revisao: atual.revisao,
    });
    // só a revisão muda aqui: a pessoa pode ter continuado digitando durante a gravação
    atual.revisao = salvo.revisao;
    atual.atualizado_em = salvo.atualizado_em;
    relatorios.situacao = sujo ? "pendente" : "salvo";
  } catch (e) {
    relatorios.situacao = "erro";
    avisar(e.message, "erro");
    if (e.status === 409) {
      // outra aba gravou antes: vale a versão do servidor. Sem passar pela fila, que é esta gravação.
      trocarAtual(await api.obterRelatorio(atual.id));
    } else if (!e.status || e.status >= 500) {
      // rede ou serviço fora do ar: a edição continua pendente e tenta de novo sozinha
      sujo = true;
      temporizador = setTimeout(() => salvarAgora().catch(() => {}), ESPERA_NOVA_TENTATIVA);
    }
    throw e;
  }
}

/** Grava o que estiver pendente e só termina quando não sobrar nada. */
export async function salvarAgora() {
  clearTimeout(temporizador);
  while (relatorios.atual && (sujo || gravacao)) {
    if (!gravacao) gravacao = gravar().finally(() => (gravacao = null));
    await gravacao;
  }
}

/** Roda uma operação no servidor com a fila vazia; quem digitar enquanto isso espera ela acabar. */
async function naFila(acao) {
  do {
    await salvarAgora();
  } while (gravacao);
  const tarefa = acao();
  gravacao = tarefa.then(() => {}, () => {}).finally(() => (gravacao = null));
  return tarefa;
}

export function marcarAlterado() {
  sujo = true;
  relatorios.situacao = "pendente";
  clearTimeout(temporizador);
  temporizador = setTimeout(() => salvarAgora().catch(() => {}), ESPERA_SALVAR);
}

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") salvarAgora().catch(() => {});
});

export async function carregarLista() {
  relatorios.lista = await api.listarRelatorios();
}

export async function abrirRelatorio(id) {
  await salvarAgora().catch(() => {});
  trocarAtual(await api.obterRelatorio(id));
  relatorios.anexados = new Set();
  relatorios.versoes = await api.listarVersoes(id);
}

export async function criarRelatorio(titulo) {
  await salvarAgora().catch(() => {});
  trocarAtual(await api.criarRelatorio(titulo));
  relatorios.anexados = new Set();
  relatorios.versoes = [];
  await carregarLista();
}

export async function excluirRelatorio(id) {
  await api.excluirRelatorio(id);
  if (relatorios.atual?.id === id) {
    clearTimeout(temporizador);
    sujo = false;
    relatorios.atual = null;
    relatorios.versoes = [];
  }
  await carregarLista();
}

/** Anexa uma resposta do assistente; sem relatório aberto, abre o mais recente ou cria um. */
export async function anexarResposta(resposta) {
  if (!relatorios.atual) {
    await carregarLista();
    if (relatorios.lista.length) await abrirRelatorio(relatorios.lista[0].id);
    else await criarRelatorio("Relatório sem título");
  }
  await naFila(async () => {
    const atual = relatorios.atual;
    const novo = await api.anexarAoRelatorio(atual.id, {
      execucao_id: resposta.id,
      texto: resposta.texto ?? "",
      grafico: resposta.grafico,
      colunas: resposta.colunas,
      linhas: resposta.linhas,
      truncado: resposta.truncado,
    });
    // só o bloco novo entra: o resto da tela continua como a pessoa deixou
    atual.blocos.push(novo.blocos[novo.blocos.length - 1]);
    atual.revisao = novo.revisao;
  });
  relatorios.anexados.add(resposta.id);
  relatorios.painelAberto = true;
}

export function adicionarBloco(tipo, posicao = relatorios.atual.blocos.length) {
  relatorios.atual.blocos.splice(posicao, 0, { id: novoId(), tipo, texto: "" });
  marcarAlterado();
}

export function removerBloco(id) {
  const blocos = relatorios.atual.blocos;
  blocos.splice(blocos.findIndex((b) => b.id === id), 1);
  marcarAlterado();
}

export function moverBloco(de, para) {
  const blocos = relatorios.atual.blocos;
  if (para < 0 || para >= blocos.length || de === para) return;
  blocos.splice(para, 0, blocos.splice(de, 1)[0]);
  marcarAlterado();
}

async function atualizarUm(id) {
  relatorios.atualizando.add(id);
  try {
    await naFila(async () => {
      const atual = relatorios.atual;
      const novo = await api.atualizarBloco(atual.id, id);
      atual.revisao = novo.revisao;
      // só os dados mudam: texto e visão são da pessoa, que pode ter editado durante a consulta
      const bloco = atual.blocos.find((b) => b.id === id);
      const { grafico, colunas, linhas, truncado, dados_em } = novo.blocos.find((b) => b.id === id);
      if (bloco) Object.assign(bloco, { grafico, colunas, linhas, truncado, dados_em });
    });
  } finally {
    relatorios.atualizando.delete(id);
  }
}

export async function atualizarBloco(id) {
  try {
    await atualizarUm(id);
    avisar("Números atualizados.");
  } catch (e) {
    avisar(e.message, "erro");
  }
}

export async function atualizarTodos() {
  const ids = relatorios.atual.blocos.filter((b) => b.tipo === "resultado").map((b) => b.id);
  let falhas = 0;
  for (const id of ids) {
    try {
      await atualizarUm(id);
    } catch (e) {
      falhas++;
      avisar(e.message, "erro");
    }
  }
  if (!falhas && ids.length) avisar("Todos os números foram atualizados.");
}

export async function exportarPdf() {
  relatorios.exportando = true;
  try {
    const versao = await naFila(() => {
      const graficos = {};
      for (const b of relatorios.atual.blocos) {
        const desenhavel = b.tipo === "resultado" && b.visao === "grafico" && ["linha", "barra"].includes(b.grafico?.tipo);
        if (desenhavel && b.grafico.series?.length) graficos[b.id] = svgsParaPdf(b.grafico);
      }
      return api.publicarVersao(relatorios.atual.id, { graficos });
    });
    relatorios.versoes.unshift(versao);
    await carregarLista();
    avisar(`Versão ${versao.numero} gerada.`);
    return versao;
  } catch (e) {
    avisar(e.message, "erro");
    return null;
  } finally {
    relatorios.exportando = false;
  }
}

export const urlDoPdf = (id, numero) => `/api/relatorios/${id}/versoes/${numero}/pdf`;
