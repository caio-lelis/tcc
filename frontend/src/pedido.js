// Pergunta feita fora da tela de conversa (o campo do Início): a conversa observa e envia.
import { ref } from "vue";

export const perguntaPendente = ref(null);

export function pedirPergunta(texto) {
  perguntaPendente.value = { texto, quando: Date.now() };
}
