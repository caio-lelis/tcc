// Tema claro/escuro. Segue o sistema até a pessoa escolher; a escolha fica guardada no navegador.
// O index.html aplica o tema antes do primeiro desenho, para a tela não piscar.
import { ref } from "vue";

const CHAVE = "data-talk:tema";
const sistema = window.matchMedia("(prefers-color-scheme: dark)");

function lerEscolha() {
  try {
    return localStorage.getItem(CHAVE);
  } catch {
    return null;
  }
}

const doSistema = () => (sistema.matches ? "escuro" : "claro");

export const tema = ref(lerEscolha() ?? doSistema());

function aplicar(valor) {
  // o atributo muda antes do ref: quem observa o tema já lê as cores novas
  document.documentElement.dataset.tema = valor;
  tema.value = valor;
}

export function alternarTema() {
  const novo = tema.value === "escuro" ? "claro" : "escuro";
  aplicar(novo);
  try {
    localStorage.setItem(CHAVE, novo);
  } catch {
    /* sem armazenamento: vale só nesta visita */
  }
}

sistema.addEventListener("change", () => {
  if (!lerEscolha()) aplicar(doSistema());
});

aplicar(tema.value);
