<script setup>
// Logo do Data Talk em vetor, com as peças separadas para animar.
// Entra em sequência ao aparecer, fica viva em repouso (rabo, barras, raios, brilho no "Talk")
// e pula ao passar o mouse. fundo="auto" acompanha o tema; fundo="escuro" é para superfícies sempre azuis.
import { onBeforeUnmount, onMounted, ref } from "vue";
import marca from "../assets/logo-data-talk.svg?raw";

const props = defineProps({
  fundo: { type: String, default: "auto" },
  entrada: { type: Boolean, default: true },
});

const raiz = ref(null);
const entrando = ref(props.entrada);
const animando = ref(false);
let relogio;
let contador = 0;

function semMovimento() {
  return typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// Brilho que atravessa o "Talk": uma cópia da palavra pintada com um degradê que anda.
function adicionarBrilho(svg) {
  const talk = svg.querySelector(".t-talk");
  if (!talk || semMovimento()) return;
  const NS = "http://www.w3.org/2000/svg";
  const id = `dt-brilho-${++contador}-${Math.random().toString(36).slice(2, 7)}`;
  const defs = document.createElementNS(NS, "defs");
  defs.innerHTML = `<linearGradient id="${id}" x1="0" y1="0" x2="1" y2="0.25">
      <stop offset="0.42" stop-color="#fff" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#fff" stop-opacity="0.9"/>
      <stop offset="0.58" stop-color="#fff" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0;1 0" keyTimes="0;0.4;1" dur="5s" begin="1.8s" repeatCount="indefinite"/>
    </linearGradient>`;
  svg.prepend(defs);
  const copia = talk.cloneNode(true);
  copia.setAttribute("class", "t-brilho");
  copia.setAttribute("fill", `url(#${id})`);
  talk.after(copia);
}

onMounted(() => {
  const svg = raiz.value?.querySelector("svg");
  if (svg) adicionarBrilho(svg);
  if (entrando.value) relogio = setTimeout(() => (entrando.value = false), 1700);
});
onBeforeUnmount(() => clearTimeout(relogio));
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
    ref="raiz"
    class="logo-dt"
    :class="[fundo, { animando, entrando }]"
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

/* ---- entrada em sequência: cai com amortecimento, balão estoura, barras sobem, raios acendem ---- */
.logo-dt.entrando .cachorro { transform-origin: 660px 1240px; animation: logo-cai 0.95s cubic-bezier(0.3, 1.35, 0.5, 1) 0.1s both; }
.logo-dt.entrando .sombra { animation: logo-sombra-entra 0.95s ease-out 0.1s both; }
.logo-dt.entrando .balao { animation: logo-estoura 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.55s both; }
.logo-dt.entrando .barra-1 { animation: logo-cresce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.8s both; }
.logo-dt.entrando .barra-2 { animation: logo-cresce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.9s both; }
.logo-dt.entrando .barra-3 { animation: logo-cresce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 1s both; }
.logo-dt.entrando .raios { animation: logo-estoura 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 1.15s both; }
.logo-dt.entrando .texto { animation: logo-sobe 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.45s both; }
.logo-dt.entrando .t-brilho { opacity: 0; }

/* ---- em repouso: rabo abana de vez em quando, barras respiram como um gráfico ao vivo, raios piscam ---- */
.logo-dt:not(.animando):not(.entrando) .cauda { animation: logo-abana 3.4s ease-in-out infinite; }
.logo-dt:not(.animando):not(.entrando) .barra-1 { animation: logo-respira 2.6s ease-in-out infinite; }
.logo-dt:not(.animando):not(.entrando) .barra-2 { animation: logo-respira 2.6s ease-in-out 0.2s infinite; }
.logo-dt:not(.animando):not(.entrando) .barra-3 { animation: logo-respira 2.6s ease-in-out 0.4s infinite; }
.logo-dt:not(.animando):not(.entrando) .raio { transform-origin: 1400px 190px; animation: logo-pisca 2.4s ease-in-out infinite; }
.logo-dt:not(.animando):not(.entrando) .raio-2 { animation-delay: 0.2s; }
.logo-dt:not(.animando):not(.entrando) .raio-3 { animation-delay: 0.4s; }

@keyframes logo-cai {
  0% { transform: translateY(-260px); opacity: 0; }
  35% { opacity: 1; }
  58% { transform: translateY(0) scale(1.04, 0.94); }
  76% { transform: translateY(-36px) scale(0.99, 1.01); }
  100% { transform: none; }
}
@keyframes logo-sombra-entra { 0% { transform: scale(0.3); opacity: 0; } 58% { transform: scale(1.06); opacity: 1; } 100% { transform: none; } }
@keyframes logo-estoura { 0% { transform: scale(0); opacity: 0; } 100% { transform: none; opacity: 1; } }
@keyframes logo-cresce { 0% { transform: scaleY(0); } 100% { transform: none; } }
@keyframes logo-sobe { 0% { transform: translateY(80px); opacity: 0; filter: blur(8px); } 100% { transform: none; opacity: 1; filter: none; } }
@keyframes logo-abana {
  0%, 42%, 100% { transform: none; }
  6%, 16%, 26% { transform: rotate(12deg); }
  11%, 21%, 31% { transform: rotate(-10deg); }
  36% { transform: rotate(4deg); }
}
@keyframes logo-respira { 0%, 100% { transform: none; } 50% { transform: scaleY(0.7); } }
@keyframes logo-pisca { 0%, 100% { opacity: 1; transform: none; } 50% { opacity: 0.3; transform: scale(0.88); } }

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
  .logo-dt.entrando * { animation: none !important; }
  .logo-dt.animando .cachorro,
  .logo-dt.animando .sombra,
  .logo-dt.animando .cabeca,
  .logo-dt.animando .balao,
  .logo-dt.animando .raios { animation: none; }
}
</style>
