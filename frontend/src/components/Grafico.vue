<script setup>
// Gráfico da resposta (RF09). O backend já conferiu a sugestão do modelo e
// mandou a configuração do ECharts pronta; aqui só desenhamos.
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import { formatar } from "../api.js";

const props = defineProps({ grafico: { type: Object, required: true } });

const area = ref(null);
let instancia = null;
let observador = null;

function desenhar() {
  if (!area.value || !props.grafico.echarts) return;
  instancia ??= echarts.init(area.value);
  instancia.setOption(
    {
      ...props.grafico.echarts,
      color: ["#2f5bea", "#1f8a4c", "#b45309", "#8e44ad", "#c0392b"],
      grid: { left: 64, right: 24, top: 40, bottom: 72 },
      yAxis: { ...props.grafico.echarts.yAxis, axisLabel: { formatter: (v) => formatar(v) } },
      tooltip: { ...props.grafico.echarts.tooltip, valueFormatter: (v) => formatar(v) },
    },
    true,
  );
}

onMounted(() => {
  desenhar();
  observador = new ResizeObserver(() => instancia?.resize());
  if (area.value) observador.observe(area.value);
});
watch(() => props.grafico, desenhar, { deep: true });
onBeforeUnmount(() => {
  observador?.disconnect();
  instancia?.dispose();
});
</script>

<template>
  <div v-if="grafico.tipo === 'indicador'" class="indicador">
    <div class="valor">{{ formatar(grafico.indicador?.valor) }}</div>
    <div class="suave">{{ grafico.indicador?.rotulo?.replaceAll("_", " ") }}</div>
  </div>
  <div v-else-if="grafico.echarts" ref="area" class="area"></div>
</template>

<style scoped>
.area { width: 100%; height: 340px; }
.indicador { padding: 12px 0; }
.valor { font-size: 2.6em; font-weight: 700; color: var(--primaria); line-height: 1.1; }
</style>
