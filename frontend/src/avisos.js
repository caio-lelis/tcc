// Avisos flutuantes ("Descrição salva", "Erro ao enviar"...), usados por todas as telas.
import { reactive } from "vue";

export const avisos = reactive([]);
let proximo = 1;

export function avisar(texto, tipo = "sucesso") {
  const id = proximo++;
  avisos.push({ id, texto, tipo });
  setTimeout(() => {
    const i = avisos.findIndex((a) => a.id === id);
    if (i >= 0) avisos.splice(i, 1);
  }, tipo === "erro" ? 6000 : 2800);
}
