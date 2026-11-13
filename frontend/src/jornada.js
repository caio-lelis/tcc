// Primeiros passos: quanto do caminho "anexar → descrever → perguntar" o usuário já fez.
// Alimenta o cartão de progresso da barra lateral.
import { reactive } from "vue";
import { api } from "./api.js";

const CHAVE = "data-talk:perguntou";

function jaPerguntou() {
  try {
    return localStorage.getItem(CHAVE) === "sim";
  } catch {
    return false;
  }
}

export const jornada = reactive({
  carregada: false,
  temTabelas: false,
  descritas: 0, // tabelas com descrição
  totalTabelas: 0,
  perguntou: jaPerguntou(),
});

export async function atualizarJornada() {
  try {
    const [tabelas, completo] = await Promise.all([api.listarTabelas(), api.obterContexto()]);
    const descricoes = completo?.contexto?.tabelas ?? {};
    jornada.totalTabelas = tabelas.length;
    jornada.temTabelas = tabelas.length > 0;
    jornada.descritas = tabelas.filter((t) => descricoes[t.nome]?.descricao?.trim()).length;
    jornada.carregada = true;
  } catch {
    /* API fora do ar: o cartão simplesmente não aparece */
  }
}

export function marcarPergunta() {
  jornada.perguntou = true;
  try {
    localStorage.setItem(CHAVE, "sim");
  } catch {
    /* sem armazenamento */
  }
}
