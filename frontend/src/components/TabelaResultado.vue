<script setup>
import { computed } from "vue";
import { formatarValor, nomeLegivel } from "../formatacao.js";

const props = defineProps({
  colunas: { type: Array, required: true },
  linhas: { type: Array, required: true },
  limite: { type: Number, default: 200 },
});
const visiveis = computed(() => props.linhas.slice(0, props.limite));
const numerica = computed(() =>
  props.colunas.map((_, j) => props.linhas.some((l) => typeof l[j] === "number")),
);
</script>

<template>
  <div class="tabela-envoltorio">
    <table class="tabela">
      <thead>
        <tr>
          <th v-for="(c, j) in colunas" :key="c" :class="{ num: numerica[j] }">{{ nomeLegivel(c) }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(linha, i) in visiveis" :key="i">
          <td v-for="(v, j) in linha" :key="j" :class="{ num: numerica[j], nulo: v === null }">{{ formatarValor(v) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <p v-if="linhas.length > limite" class="texto-suave pequeno rodape">
    Mostrando {{ limite }} de {{ linhas.length }} linhas.
  </p>
</template>

<style scoped>
.rodape { margin-top: 8px; }
</style>
