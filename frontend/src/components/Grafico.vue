<script setup>
// Gráfico da resposta (RF09). O backend já conferiu a sugestão do modelo e mandou
// a configuração base do ECharts; aqui aplicamos o visual do Fala Dados.
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import { formatarCompacto, formatarNumero, nomeLegivel, rotulosDeEixo } from "../formatacao.js";

const props = defineProps({ grafico: { type: Object, required: true } });

const CORES = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#0ea5e9", "#8b5cf6"];
const area = ref(null);
let instancia = null;
let observador = null;

function opcao() {
  const base = props.grafico.echarts;
  const linha = props.grafico.tipo === "linha";
  const series = base.series.map((s, i) => {
    const cor = CORES[i % CORES.length];
    const estilo = linha
      ? {
          type: "line",
          smooth: 0.35,
          symbol: "circle",
          symbolSize: 7,
          showSymbol: base.xAxis.data.length <= 24,
          lineStyle: { width: 3, color: cor },
          itemStyle: { color: cor, borderColor: "#fff", borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: cor + "40" },
              { offset: 1, color: cor + "00" },
            ]),
          },
        }
      : {
          type: "bar",
          barMaxWidth: 44,
          itemStyle: { color: cor, borderRadius: [7, 7, 0, 0] },
          emphasis: { itemStyle: { color: cor, opacity: 0.85 } },
        };
    return { ...s, ...estilo, name: nomeLegivel(s.name) };
  });

  const eixo = { color: "#94a3b8", fontSize: 12, fontFamily: "Inter Variable, sans-serif" };
  const variasSeries = series.length > 1;
  return {
    textStyle: { fontFamily: "Inter Variable, Segoe UI, sans-serif" },
    color: CORES,
    grid: { left: 8, right: 16, top: variasSeries ? 44 : 20, bottom: base.xAxis.data.length > 12 ? 56 : 8, containLabel: true },
    legend: variasSeries
      ? { top: 0, left: 0, icon: "roundRect", itemWidth: 12, itemHeight: 12, textStyle: { color: "#475569" } }
      : { show: false },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#0f172a",
      borderWidth: 0,
      padding: [10, 14],
      textStyle: { color: "#f1f5f9", fontSize: 13 },
      axisPointer: linha ? { type: "line", lineStyle: { color: "#c7d2fe", width: 1.5 } } : { type: "shadow", shadowStyle: { color: "rgba(99,102,241,0.06)" } },
      valueFormatter: (v) => formatarNumero(v),
    },
    xAxis: {
      type: "category",
      data: rotulosDeEixo(base.xAxis.data),
      boundaryGap: !linha,
      axisLine: { lineStyle: { color: "#e2e8f0" } },
      axisTick: { show: false },
      axisLabel: { ...eixo, margin: 12, hideOverlap: true },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#eef1f6", type: "dashed" } },
      axisLabel: { ...eixo, formatter: (v) => formatarCompacto(v) },
    },
    dataZoom: base.xAxis.data.length > 12
      ? [{ type: "inside" }, { type: "slider", height: 18, bottom: 6, borderColor: "transparent", fillerColor: "rgba(99,102,241,0.12)", handleSize: "80%", showDetail: false }]
      : [{ type: "inside" }],
    series,
    animationDuration: 600,
    animationEasing: "cubicOut",
  };
}

function desenhar() {
  if (!area.value || !props.grafico.echarts) return;
  instancia ??= echarts.init(area.value, null, { renderer: "svg" });
  instancia.setOption(opcao(), true);
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
  <div ref="area" class="area"></div>
</template>

<style scoped>
.area { width: 100%; height: 320px; }
</style>
