<script setup>
// Gráfico da resposta (RF09). A forma e os dados vêm prontos do backend (services/visualizacao.py);
// aqui só se decide o desenho: um gráfico, ou um por medida quando as escalas são muito diferentes.
import { computed } from "vue";
import GraficoPainel from "./GraficoPainel.vue";
import { CORES } from "../paleta.js";
import { nomeLegivel } from "../formatacao.js";

const props = defineProps({ grafico: { type: Object, required: true } });

// a cor acompanha a série (ordem fixa da paleta), mesmo quando cada série vai para o seu gráfico
const series = computed(() => props.grafico.series.map((s, i) => ({ ...s, cor: CORES[i % CORES.length] })));

const paineis = computed(() =>
  props.grafico.escalas_separadas
    ? series.value.map((s) => ({ titulo: nomeLegivel(s.nome), series: [s] }))
    : [{ titulo: null, series: series.value }],
);

// rótulo no fim da linha para até 4 séries: identificar a série não depende só da cor
const rotulosDiretos = computed(
  () => props.grafico.tipo === "linha" && !props.grafico.escalas_separadas && series.value.length >= 2 && series.value.length <= 4,
);
</script>

<template>
  <div class="graficos" :class="{ lado: paineis.length > 1 }">
    <div v-for="(p, i) in paineis" :key="i" class="painel">
      <div v-if="p.titulo" class="titulo">{{ p.titulo }}</div>
      <GraficoPainel
        :tipo="grafico.tipo"
        :orientacao="grafico.orientacao"
        :categorias="grafico.categorias"
        :series="p.series"
        :rotulos-diretos="rotulosDiretos"
      />
    </div>
  </div>
</template>

<style scoped>
.graficos.lado { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
.titulo { font-size: 0.82rem; font-weight: 600; color: var(--texto-2); margin-bottom: 6px; }
</style>
