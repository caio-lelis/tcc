<script setup>
// Logo do Data Talk em vetor, com as peças separadas para animar ao passar o mouse.
// fundo="auto" acompanha o tema; fundo="escuro" é para superfícies sempre azuis (barra lateral).
import { ref } from "vue";
import marca from "../assets/logo-data-talk.svg?raw";

defineProps({ fundo: { type: String, default: "auto" } });

const animando = ref(false);
let sobre = false;

function entrar() {
  sobre = true;
  animando.value = true;
}
function sair() {
  sobre = false;
}
// A animação só para no fim do ciclo, com todas as peças de volta ao lugar.
// A cauda é a referência porque anima sempre, mesmo com movimento reduzido.
function fimDoCiclo(evento) {
  if (!sobre && evento.target.classList.contains("cauda")) animando.value = false;
}
</script>

<template>
  <div
    class="logo-dt"
    :class="[fundo, { animando }]"
    @mouseenter="entrar"
    @mouseleave="sair"
    @animationiteration="fimDoCiclo"
    v-html="marca"
  ></div>
</template>

<style>
/* Sem scoped: o SVG entra por v-html. Origens em unidades do viewBox do desenho. */
.logo-dt { line-height: 0; }
.logo-dt svg { display: block; width: 100%; height: auto; overflow: visible; }

.logo-dt .contorno { display: none; }
.logo-dt.escuro .contorno { display: inline; }
.logo-dt.escuro .sombra { display: none; }
.logo-dt.escuro .t-data { fill: #fff; }
:root[data-tema="escuro"] .logo-dt.auto .contorno { display: inline; }
:root[data-tema="escuro"] .logo-dt.auto .sombra { display: none; }
:root[data-tema="escuro"] .logo-dt.auto .t-data { fill: #fff; }

.logo-dt .cauda { transform-origin: 368px 920px; }
.logo-dt .cabeca { transform-origin: 900px 800px; }
.logo-dt .sombra { transform-origin: 660px 1240px; }
.logo-dt .balao { transform-origin: 1220px 472px; }
.logo-dt .barra { transform-origin: 1220px 360px; }
.logo-dt .raios { transform-origin: 1400px 190px; }

.logo-dt.animando .cachorro { animation: logo-pulo 1.6s ease-in-out infinite; }
.logo-dt.animando .sombra { animation: logo-sombra 1.6s ease-in-out infinite; }
.logo-dt.animando .cauda { animation: logo-cauda 1.6s ease-in-out infinite; }
.logo-dt.animando .cabeca { animation: logo-cabeca 1.6s ease-in-out infinite; }
.logo-dt.animando .balao { animation: logo-balao 1.6s ease-in-out infinite; }
.logo-dt.animando .barra-1 { animation: logo-barra-1 1.6s ease-out infinite; }
.logo-dt.animando .barra-2 { animation: logo-barra-2 1.6s ease-out infinite; }
.logo-dt.animando .barra-3 { animation: logo-barra-3 1.6s ease-out infinite; }
.logo-dt.animando .raios { animation: logo-raios 1.6s ease-out infinite; }

@keyframes logo-pulo {
  0%, 46%, 100% { transform: none; }
  12% { transform: translateY(-34px); }
  24% { transform: none; }
  34% { transform: translateY(-16px); }
}
@keyframes logo-sombra {
  0%, 46%, 100% { transform: none; }
  12% { transform: scale(0.86); }
  24% { transform: none; }
  34% { transform: scale(0.93); }
}
@keyframes logo-cauda {
  0%, 100% { transform: none; }
  10%, 30%, 50%, 70% { transform: rotate(13deg); }
  20%, 40%, 60%, 80% { transform: rotate(-11deg); }
  90% { transform: rotate(6deg); }
}
@keyframes logo-cabeca {
  0%, 85%, 100% { transform: none; }
  18%, 42% { transform: rotate(-6deg); }
  62% { transform: rotate(3deg); }
}
@keyframes logo-balao {
  0%, 44%, 100% { transform: none; }
  10% { transform: scale(0.9); }
  26% { transform: scale(1.09); }
}
@keyframes logo-barra-1 {
  0%, 46%, 100% { transform: none; }
  12% { transform: scaleY(0.25); }
  26% { transform: scaleY(1.2); }
}
@keyframes logo-barra-2 {
  0%, 52%, 100% { transform: none; }
  12% { transform: scaleY(0.25); }
  32% { transform: scaleY(1.2); }
}
@keyframes logo-barra-3 {
  0%, 58%, 100% { transform: none; }
  12% { transform: scaleY(0.25); }
  38% { transform: scaleY(1.15); }
}
@keyframes logo-raios {
  0%, 62%, 100% { transform: none; opacity: 1; }
  14% { transform: scale(0.7); opacity: 0; }
  40% { transform: scale(1.16); opacity: 1; }
}

/* Quem pediu menos movimento ao sistema vê só a cauda e as barras: nada de pulo nem balanço. */
@media (prefers-reduced-motion: reduce) {
  .logo-dt.animando .cachorro,
  .logo-dt.animando .sombra,
  .logo-dt.animando .cabeca,
  .logo-dt.animando .balao,
  .logo-dt.animando .raios { animation: none; }
}
</style>
