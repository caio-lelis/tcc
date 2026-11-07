<script setup>
// Um gráfico (linha ou barras) desenhado com ECharts a partir da especificação do backend.
import { onBeforeUnmount, onMounted, ref, watch, computed } from "vue";
import * as echarts from "echarts";
import { alturaDoGrafico, coresDoTema, montarOpcao } from "../graficoOpcoes.js";
import { tema } from "../tema.js";

const props = defineProps({
  tipo: { type: String, required: true }, // linha | barra
  orientacao: { type: String, default: "vertical" },
  categorias: { type: Array, required: true },
  series: { type: Array, required: true }, // [{ nome, valores, cor }]
  rotulosDiretos: { type: Boolean, default: false },
});

const area = ref(null);
let instancia = null;
let observador = null;

const altura = computed(() => alturaDoGrafico(props));

function desenhar() {
  if (!area.value) return;
  instancia ??= echarts.init(area.value, null, { renderer: "svg" });
  instancia.resize();
  instancia.setOption(montarOpcao(props, coresDoTema()), true);
}

onMounted(() => {
  desenhar();
  observador = new ResizeObserver(() => instancia?.resize());
  observador.observe(area.value);
});
watch(() => [props.series, props.categorias, props.tipo, props.orientacao, tema.value], desenhar, { deep: true });
onBeforeUnmount(() => {
  observador?.disconnect();
  instancia?.dispose();
});
</script>

<template>
  <div ref="area" class="area" :style="{ height: altura + 'px' }"></div>
</template>

<style scoped>
.area { width: 100%; }
</style>
