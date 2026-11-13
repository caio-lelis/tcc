// Indicador deslizante: uma "pílula" que acompanha o item ativo de uma lista de botões
// (menu lateral, alternador Gráfico/Tabela). Mede o botão ativo e devolve o estilo da pílula.
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

export function usarIndicador(container, ativo, seletor = "[data-ativo='true']") {
  const estilo = ref({ opacity: 0 });
  let observador;

  function medir() {
    const el = container.value?.querySelector(seletor);
    if (!el || !el.offsetWidth) {
      // some no lugar em que estava, em vez de voltar para o canto
      estilo.value = { ...estilo.value, opacity: 0 };
      return;
    }
    estilo.value = {
      opacity: 1,
      width: `${el.offsetWidth}px`,
      height: `${el.offsetHeight}px`,
      transform: `translate(${el.offsetLeft}px, ${el.offsetTop}px)`,
    };
  }

  onMounted(() => {
    nextTick(medir);
    if (typeof ResizeObserver !== "undefined" && container.value) {
      observador = new ResizeObserver(medir);
      observador.observe(container.value);
    }
  });
  onBeforeUnmount(() => observador?.disconnect());
  watch(ativo, () => nextTick(medir));

  return { estilo, medir };
}
