<script setup>
// Cartão "Primeiros passos" do Início: mostra em que etapa o usuário está e leva direto para a
// tela da próxima. Some sozinho quando tudo estiver feito. Inspirado nos blocos "How it works".
import { computed } from "vue";
import { Check } from "@lucide/vue";
import { jornada } from "../jornada.js";

defineEmits(["ir-para"]);

const passos = computed(() => [
  { id: "dados", rotulo: "Anexe suas tabelas", feito: jornada.temTabelas },
  {
    id: "contexto",
    rotulo: "Conte o que cada tabela guarda",
    detalhe: jornada.totalTabelas ? `${jornada.descritas} de ${jornada.totalTabelas} descritas` : "",
    feito: jornada.totalTabelas > 0 && jornada.descritas === jornada.totalTabelas,
  },
  { id: "conversa", rotulo: "Faça sua primeira pergunta", feito: jornada.perguntou },
]);
const feitos = computed(() => passos.value.filter((p) => p.feito).length);
const proximo = computed(() => passos.value.find((p) => !p.feito)?.id);
const visivel = computed(() => jornada.carregada && feitos.value < passos.value.length);
defineExpose({ visivel });
</script>

<template>
  <section v-if="visivel" class="passos" aria-label="Primeiros passos">
    <div class="topo">
      <h2>Primeiros passos</h2>
      <span class="contagem">{{ feitos }}/{{ passos.length }}</span>
    </div>
    <div class="barra" role="progressbar" :aria-valuenow="feitos" aria-valuemin="0" :aria-valuemax="passos.length">
      <div class="enchimento" :style="{ transform: `scaleX(${feitos / passos.length})` }"></div>
    </div>
    <ol>
      <li v-for="(p, i) in passos" :key="p.id">
        <button class="passo" :class="{ feito: p.feito, proximo: p.id === proximo }" @click="$emit('ir-para', p.id)">
          <span class="marca-passo">
            <Transition name="check" mode="out-in">
              <Check v-if="p.feito" key="ok" />
              <span v-else key="n">{{ i + 1 }}</span>
            </Transition>
          </span>
          <span class="textos">
            <span class="rotulo">{{ p.rotulo }}</span>
            <span v-if="p.detalhe && !p.feito" class="detalhe">{{ p.detalhe }}</span>
          </span>
          <span class="ir" aria-hidden="true">→</span>
        </button>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.passos { display: flex; flex-direction: column; gap: 4px; }
.topo { display: flex; align-items: baseline; justify-content: space-between; }
h2 { font-size: 0.95rem; font-weight: 650; color: var(--texto-2); }
.contagem { font-size: 0.85rem; font-weight: 650; color: var(--menta-texto); font-variant-numeric: tabular-nums; }

.barra { height: 6px; margin: 8px 0 6px; border-radius: 999px; background: var(--trilho); overflow: hidden; }
.enchimento { height: 100%; background: var(--menta); transform-origin: left; transition: transform 0.7s cubic-bezier(0.22, 1, 0.36, 1); }

ol { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 2px; }
.passo {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 8px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--texto-2);
  font: inherit;
  font-size: 0.92rem;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.passo:hover { background: var(--superficie-2); color: var(--texto); }
.passo:focus-visible { outline: 2px solid var(--borda-foco); outline-offset: 1px; }
.passo.proximo { color: var(--texto); font-weight: 600; }
.passo.feito .rotulo { text-decoration: line-through; text-decoration-color: var(--borda-forte); color: var(--suave); }

.marca-passo {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 0.76rem;
  font-weight: 700;
  border: 1.5px solid var(--borda-forte);
  transition: background 0.25s, border-color 0.25s;
}
.marca-passo svg { width: 14px; height: 14px; stroke-width: 3; }
.passo.feito .marca-passo { background: var(--menta); border-color: var(--menta); color: var(--azul-noite); }
/* a próxima etapa "respira" para chamar atenção, sem piscar */
.passo.proximo .marca-passo { border-color: var(--primaria); color: var(--primaria); animation: respirar 2.4s ease-in-out infinite; }
@keyframes respirar { 0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--primaria) 40%, transparent); } 50% { box-shadow: 0 0 0 6px transparent; } }

.textos { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.detalhe { font-size: 0.78rem; font-weight: 500; color: var(--ambar); }
.ir { opacity: 0; transform: translateX(-6px); transition: opacity 0.25s, transform 0.35s cubic-bezier(0.22, 1, 0.36, 1); color: var(--primaria); }
.passo:hover .ir { opacity: 1; transform: none; }

.check-enter-active { transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s, filter 0.2s; }
.check-leave-active { transition: transform 0.15s, opacity 0.15s, filter 0.15s; }
.check-enter-from { transform: scale(0.4) rotate(-30deg); opacity: 0; filter: blur(2px); }
.check-leave-to { transform: scale(0.6); opacity: 0; filter: blur(2px); }
</style>
