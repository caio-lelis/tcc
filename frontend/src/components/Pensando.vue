<script setup>
// Estado "pensando" da resposta: texto com brilho que passa e frases que se revezam.
// As frases descrevem o que o assistente faz em geral; não acompanham a etapa real do servidor.
import { onBeforeUnmount, onMounted, ref } from "vue";

const FRASES = ["Entendendo a pergunta…", "Consultando suas tabelas…", "Preparando a resposta…"];
const indice = ref(0);
let relogio;

onMounted(() => {
  relogio = setInterval(() => {
    // para na última frase em vez de voltar ao começo
    if (indice.value < FRASES.length - 1) indice.value++;
  }, 2200);
});
onBeforeUnmount(() => clearInterval(relogio));
</script>

<template>
  <div class="pensando" role="status">
    <span class="pontos" aria-hidden="true"><i></i><i></i><i></i></span>
    <Transition name="frase" mode="out-in">
      <span :key="indice" class="brilho">{{ FRASES[indice] }}</span>
    </Transition>
  </div>
</template>

<style scoped>
.pensando { display: flex; align-items: center; gap: 12px; padding-top: 2px; min-height: 24px; }

.brilho {
  font-weight: 520;
  color: transparent;
  background: linear-gradient(90deg, var(--suave) 0%, var(--suave) 35%, var(--primaria) 50%, var(--suave) 65%, var(--suave) 100%);
  background-size: 250% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  animation: varrer 2s linear infinite;
}
@keyframes varrer { from { background-position: 100% 0; } to { background-position: -150% 0; } }

.pontos { display: inline-flex; gap: 4px; }
.pontos i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--primaria);
  opacity: 0.3;
  animation: pulsar 1.2s infinite ease-in-out;
}
.pontos i:nth-child(2) { animation-delay: 0.15s; }
.pontos i:nth-child(3) { animation-delay: 0.3s; }
@keyframes pulsar { 0%, 80%, 100% { opacity: 0.25; transform: scale(0.85); } 40% { opacity: 1; transform: scale(1); } }

.frase-enter-active, .frase-leave-active { transition: opacity 0.25s, transform 0.25s, filter 0.25s; }
.frase-enter-from { opacity: 0; transform: translateY(5px); filter: blur(3px); }
.frase-leave-to { opacity: 0; transform: translateY(-5px); filter: blur(3px); }

@media (prefers-reduced-motion: reduce) {
  .brilho { animation: none; color: var(--suave); background: none; }
}
</style>
