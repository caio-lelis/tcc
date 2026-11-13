<script setup>
import { CircleAlert, CircleCheck } from "@lucide/vue";
import { avisos } from "../avisos.js";
</script>

<template>
  <div class="avisos" aria-live="polite">
    <TransitionGroup name="aviso">
      <div v-for="a in avisos" :key="a.id" class="aviso" :class="a.tipo">
        <CircleAlert v-if="a.tipo === 'erro'" />
        <CircleCheck v-else class="check-desenho" />
        <span>{{ a.texto }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.avisos {
  position: fixed;
  right: 24px;
  bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 100;
  pointer-events: none;
}
.aviso {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 260px;
  max-width: 420px;
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--aviso-fundo);
  color: #f1f5f9;
  box-shadow: var(--sombra-lg);
  font-size: 0.9rem;
  font-weight: 500;
}
.aviso svg { width: 18px; height: 18px; flex-shrink: 0; color: #34d399; }
.aviso.erro svg { color: #f87171; }
/* sobe com desfoque; ao sair, os de baixo escorregam para o lugar */
.aviso-enter-active { transition: opacity 0.3s, transform 0.4s cubic-bezier(0.34, 1.4, 0.64, 1), filter 0.3s; }
.aviso-leave-active { transition: opacity 0.2s, transform 0.2s, filter 0.2s; position: absolute; right: 0; }
.aviso-move { transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1); }
.aviso-enter-from { opacity: 0; transform: translateY(14px) scale(0.94); filter: blur(4px); }
.aviso-leave-to { opacity: 0; transform: scale(0.96); filter: blur(3px); }
</style>
