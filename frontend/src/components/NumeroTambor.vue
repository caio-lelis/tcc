<script setup>
// Número em tambor: cada dígito gira até o valor (padrão "Spinning counter" do transitions.dev,
// reescrito aqui). O valor exato fica no aria-label; a animação é só a chegada.
import { computed } from "vue";
import { formatarNumero } from "../formatacao.js";

const props = defineProps({
  valor: { type: Number, required: true },
  atraso: { type: Number, default: 0 }, // ms antes de começar
});

const DIGITOS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
const texto = computed(() => formatarNumero(props.valor));
const partes = computed(() =>
  texto.value.split("").map((c, i) => ({
    c,
    digito: /\d/.test(c),
    // para no segundo ciclo, para o tambor dar uma volta inteira antes
    y: `-${10 + Number(c)}em`,
    atraso: `${props.atraso + i * 110}ms`,
  })),
);
</script>

<template>
  <span class="tambor" :aria-label="texto" role="img">
    <template v-for="(p, i) in partes" :key="`${texto}-${i}`">
      <span v-if="p.digito" class="roda" aria-hidden="true">
        <span class="faixa" :style="{ '--y': p.y, animationDelay: p.atraso }">
          <span v-for="(d, j) in DIGITOS" :key="j">{{ d }}</span>
        </span>
      </span>
      <span v-else aria-hidden="true">{{ p.c }}</span>
    </template>
  </span>
</template>

<style scoped>
.tambor { display: inline-flex; font-variant-numeric: tabular-nums; }
.roda { display: inline-block; height: 1em; line-height: 1; overflow: hidden; vertical-align: top; }
.faixa {
  display: flex;
  flex-direction: column;
  transform: translateY(var(--y));
  animation: roda 1.9s cubic-bezier(0.16, 1, 0.3, 1) backwards;
}
.faixa span { height: 1em; }
@keyframes roda { from { transform: translateY(0); } to { transform: translateY(var(--y)); } }
</style>
