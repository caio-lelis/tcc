<script setup>
// Gráfico da resposta (RF09). A forma e os dados vêm prontos do backend (services/visualizacao.py);
// aqui só se decide o desenho: um gráfico, ou um por medida quando as escalas são muito diferentes.
import { computed } from "vue";
import GraficoPainel from "./GraficoPainel.vue";
import { paineisDoGrafico, usaRotulosDiretos } from "../graficoOpcoes.js";

const props = defineProps({ grafico: { type: Object, required: true } });

const paineis = computed(() => paineisDoGrafico(props.grafico));
const rotulosDiretos = computed(() => usaRotulosDiretos(props.grafico));
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
