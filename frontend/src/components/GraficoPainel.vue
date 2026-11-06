<script setup>
// Um gráfico (linha ou barras) desenhado com ECharts a partir da especificação do backend.
import { onBeforeUnmount, onMounted, ref, watch, computed } from "vue";
import * as echarts from "echarts";
import { formatarCompacto, formatarNumero, nomeLegivel, rotulosDeEixo } from "../formatacao.js";


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

const horizontal = computed(() => props.tipo === "barra" && props.orientacao === "horizontal");
const altura = computed(() => (horizontal.value ? Math.max(200, props.categorias.length * 34 + 56) : 300));

const TEXTO = { color: "#64748b", fontSize: 12, fontFamily: "Inter Variable, Segoe UI, sans-serif" };

function opcao() {
  const linha = props.tipo === "linha";
  const variasSeries = props.series.length > 1;
  const rotulos = rotulosDeEixo(props.categorias);
  const muitosPontos = props.categorias.length > 24;

  const series = props.series.map((s) => {
    const base = { name: nomeLegivel(s.nome), data: s.valores, emphasis: { focus: "series" } };
    if (linha) {
      return {
        ...base,
        type: "line",
        // várias séries: linhas retas; uma série: suavização monotônica, que nunca passa
        // acima ou abaixo dos pontos (curvas livres "inventam" valores entre eles)
        smooth: variasSeries ? false : 0.3,
        smoothMonotone: "x",
        labelLayout: { moveOverlap: "shiftY" }, // rótulos do fim da linha não se sobrepõem
        connectNulls: false, // mês sem registro não vira um traço inventado
        symbol: "circle",
        symbolSize: 8,
        showSymbol: !muitosPontos,
        lineStyle: { width: 2, color: s.cor },
        itemStyle: { color: s.cor, borderColor: "#fff", borderWidth: 2 },
        areaStyle: variasSeries
          ? undefined
          : {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: s.cor + "33" },
                { offset: 1, color: s.cor + "00" },
              ]),
            },
        endLabel: props.rotulosDiretos
          ? { show: true, formatter: "{a}", color: "#334155", fontSize: 12, fontWeight: 600, distance: 8 }
          : undefined,
      };
    }
    return {
      ...base,
      type: "bar",
      barMaxWidth: horizontal.value ? 22 : 40,
      barGap: "12%",
      barCategoryGap: variasSeries ? "28%" : "36%",
      itemStyle: { color: s.cor, borderRadius: horizontal.value ? [0, 4, 4, 0] : [4, 4, 0, 0] },
    };
  });

  const eixoCategoria = {
    type: "category",
    data: rotulos,
    boundaryGap: !linha,
    inverse: horizontal.value, // ranking: o maior em cima
    axisLine: { lineStyle: { color: "#e2e8f0" } },
    axisTick: { show: false },
    axisLabel: { ...TEXTO, margin: 12, hideOverlap: true, color: horizontal.value ? "#334155" : TEXTO.color },
  };
  const eixoValor = {
    type: "value",
    splitLine: { lineStyle: { color: "#eef1f6", type: "dashed" } },
    axisLabel: { ...TEXTO, formatter: (v) => formatarCompacto(v) },
  };

  return {
    textStyle: { fontFamily: TEXTO.fontFamily },
    grid: {
      left: 4,
      right: props.rotulosDiretos ? 110 : 20,
      top: variasSeries ? 40 : 16,
      bottom: muitosPontos && !horizontal.value ? 44 : 4,
      containLabel: true,
    },
    legend: variasSeries
      ? { top: 0, left: 0, icon: "roundRect", itemWidth: 12, itemHeight: 12, itemGap: 16, textStyle: { color: "#334155", fontSize: 13 } }
      : { show: false },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#0f172a",
      borderWidth: 0,
      padding: [10, 14],
      textStyle: { color: "#f1f5f9", fontSize: 13 },
      axisPointer: linha
        ? { type: "line", lineStyle: { color: "#94a3b8", width: 1, type: "dashed" } }
        : { type: "shadow", shadowStyle: { color: "rgba(15,23,42,0.04)" } },
      valueFormatter: (v) => (v === null || v === undefined || Number.isNaN(v) ? "sem dado" : formatarNumero(v)),
    },
    xAxis: horizontal.value ? eixoValor : eixoCategoria,
    yAxis: horizontal.value ? eixoCategoria : eixoValor,
    dataZoom: muitosPontos && !horizontal.value
      ? [{ type: "inside" }, { type: "slider", height: 16, bottom: 4, borderColor: "transparent", fillerColor: "rgba(21,96,224,0.12)", showDetail: false }]
      : [],
    series,
    animationDuration: 500,
    animationEasing: "cubicOut",
  };
}

function desenhar() {
  if (!area.value) return;
  instancia ??= echarts.init(area.value, null, { renderer: "svg" });
  instancia.resize();
  instancia.setOption(opcao(), true);
}

onMounted(() => {
  desenhar();
  observador = new ResizeObserver(() => instancia?.resize());
  observador.observe(area.value);
});
watch(() => [props.series, props.categorias, props.tipo, props.orientacao], desenhar, { deep: true });
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
