<script setup>
import { CircleAlert, CircleCheck } from "@lucide/vue";
import { avisos } from "../avisos.js";
</script>

<template>
  <div class="avisos" aria-live="polite">
    <TransitionGroup name="aviso">
      <div v-for="a in avisos" :key="a.id" class="aviso" :class="a.tipo">
        <CircleAlert v-if="a.tipo === 'erro'" />
        <CircleCheck v-else />
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
.aviso-enter-active, .aviso-leave-active { transition: all 0.25s ease; }
.aviso-enter-from, .aviso-leave-to { opacity: 0; transform: translateY(10px) scale(0.98); }
</style>
