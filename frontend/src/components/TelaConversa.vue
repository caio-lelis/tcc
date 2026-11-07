<script setup>
// Tela de conversa (RF04): pergunta em linguagem natural; resposta em texto, gráfico e tabela.
import { nextTick, onMounted, ref, watch } from "vue";
import { ArrowUp, CalendarRange, Database, LineChart, Trophy, Users } from "@lucide/vue";
import LogoDataTalk from "./LogoDataTalk.vue";
import RespostaCard from "./RespostaCard.vue";
import { api } from "../api.js";

const props = defineProps({
  avancado: { type: Boolean, default: false },
  versao: { type: Number, default: 0 },
});
defineEmits(["ir-para"]);

const pergunta = ref("");
const configuracao = ref(""); // vazio = padrão do servidor (RF06, só no modo avançado)
const trocas = ref([]);
const tabelas = ref(null);
const enviando = ref(false);
const fim = ref(null);
const campo = ref(null);

const SUGESTOES = [
  { icone: CalendarRange, texto: "Quantas vendas houve em março de 2026?" },
  { icone: LineChart, texto: "Como evoluiu a receita mês a mês em 2026?" },
  { icone: Trophy, texto: "Qual closer vendeu mais este ano?" },
  { icone: Users, texto: "Quantas reuniões cada SDR marcou por mês?" },
];

async function carregarTabelas() {
  try {
    tabelas.value = await api.listarTabelas();
  } catch {
    tabelas.value = [];
  }
}
onMounted(carregarTabelas);
watch(() => props.versao, carregarTabelas);

function ajustarAltura() {
  const el = campo.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 180) + "px";
}
watch(pergunta, () => nextTick(ajustarAltura));

async function rolarParaFim() {
  await nextTick();
  fim.value?.scrollIntoView({ behavior: "smooth", block: "end" });
}

async function enviar(texto) {
  const p = (texto ?? pergunta.value).trim();
  if (!p || enviando.value) return;
  pergunta.value = "";
  trocas.value.push({ pergunta: p, resposta: null, erro: null, carregando: true });
  const atual = trocas.value[trocas.value.length - 1];
  enviando.value = true;
  rolarParaFim();
  try {
    atual.resposta = await api.perguntar({
      pergunta: p,
      avancado: props.avancado,
      ...(props.avancado && configuracao.value ? { configuracao: configuracao.value } : {}),
    });
  } catch (e) {
    atual.erro = e.message;
  } finally {
    atual.carregando = false;
    enviando.value = false;
    rolarParaFim();
  }
}

function aoTeclar(evento) {
  if (evento.key === "Enter" && !evento.shiftKey) {
    evento.preventDefault();
    enviar();
  }
}
</script>

<template>
  <section class="conversa">
    <div class="rolagem">
      <!-- sem dados ainda -->
      <div v-if="tabelas && tabelas.length === 0" class="vazio surgir">
        <LogoDataTalk class="logo-inicial" />
        <h1>Comece pelos seus dados</h1>
        <p>Anexe as tabelas da sua empresa em CSV para fazer a primeira pergunta.</p>
        <button class="botao primario" @click="$emit('ir-para', 'dados')"><Database /> Anexar dados</button>
      </div>

      <!-- boas-vindas -->
      <div v-else-if="trocas.length === 0" class="vazio surgir">
        <LogoDataTalk class="logo-inicial" />
        <h1>O que você quer saber?</h1>
        <p>Pergunte como perguntaria a um colega. O Data Talk consulta as suas tabelas e responde com texto, gráfico e tabela.</p>
        <div class="sugestoes">
          <button v-for="s in SUGESTOES" :key="s.texto" class="sugestao" @click="enviar(s.texto)">
            <component :is="s.icone" />
            <span>{{ s.texto }}</span>
          </button>
        </div>
      </div>

      <RespostaCard v-for="(t, i) in trocas" :key="i" v-bind="t" :avancado="avancado" />
      <div ref="fim"></div>
    </div>

    <form class="compositor" @submit.prevent="enviar()">
      <div class="caixa" :class="{ desativada: tabelas?.length === 0 }">
        <textarea
          ref="campo"
          v-model="pergunta"
          rows="1"
          placeholder="Pergunte algo sobre os seus dados…"
          :disabled="tabelas?.length === 0"
          @keydown="aoTeclar"
        ></textarea>
        <div class="acoes">
          <select v-if="avancado" v-model="configuracao" class="config" title="Nível de contexto enviado ao modelo (RF06)">
            <option value="">Contexto padrão</option>
            <option value="C0">C0 · só o esquema</option>
            <option value="C1">C1 · + descrições</option>
            <option value="C2">C2 · + regras</option>
          </select>
          <span class="dica">Enter envia · Shift+Enter quebra a linha</span>
          <span class="espaco"></span>
          <button class="enviar" type="submit" :disabled="!pergunta.trim() || enviando" title="Perguntar">
            <ArrowUp />
          </button>
        </div>
      </div>
    </form>
  </section>
</template>

<style scoped>
.conversa { max-width: 860px; margin: 0 auto; padding: 0 32px; min-height: 100vh; display: flex; flex-direction: column; }
.rolagem { flex: 1; padding: 40px 0 24px; }

.vazio { text-align: center; padding: 8vh 0 24px; display: flex; flex-direction: column; align-items: center; }
.vazio h1 { font-size: 2rem; font-weight: 750; letter-spacing: -0.03em; margin-top: 18px; }
.vazio p { color: var(--suave); margin: 10px 0 26px; max-width: 520px; font-size: 1.02rem; }
.logo-inicial { width: min(320px, 80%); }

.sugestoes { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; width: 100%; max-width: 680px; }
.sugestao {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  text-align: left;
  font: inherit;
  font-size: 0.93rem;
  color: var(--texto-2);
  background: var(--superficie);
  border: 1px solid var(--borda);
  border-radius: 14px;
  box-shadow: var(--sombra-sm);
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}
.sugestao:hover { border-color: var(--borda-foco); box-shadow: var(--sombra); transform: translateY(-1px); }
.sugestao svg { width: 20px; height: 20px; color: var(--primaria); flex-shrink: 0; }

.compositor {
  position: sticky;
  bottom: 0;
  padding: 12px 0 24px;
  background: linear-gradient(to bottom, transparent 0%, var(--fundo) 30%);
}
.caixa {
  background: var(--superficie);
  border: 1px solid var(--borda);
  border-radius: 20px;
  padding: 14px 14px 10px 18px;
  box-shadow: var(--sombra-lg);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.caixa:focus-within { border-color: var(--borda-foco); box-shadow: var(--sombra-lg), var(--foco); }
.caixa.desativada { opacity: 0.6; }
.caixa textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font: inherit;
  font-size: 1rem;
  line-height: 1.5;
  color: var(--texto);
  background: transparent;
  max-height: 180px;
}
.caixa textarea::placeholder { color: var(--muito-suave); }
.acoes { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
.dica { font-size: 0.78rem; color: var(--muito-suave); }
.config {
  font: inherit;
  font-size: 0.82rem;
  font-weight: 550;
  color: var(--primaria);
  background: var(--primaria-50);
  border: 1px solid var(--primaria-100);
  border-radius: 999px;
  padding: 4px 10px;
  cursor: pointer;
}
.enviar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  border: none;
  display: grid;
  place-items: center;
  color: var(--azul-noite);
  background: var(--menta);
  cursor: pointer;
  box-shadow: var(--sombra-menta);
  transition: opacity 0.15s, transform 0.1s;
}
.enviar:disabled { opacity: 0.35; cursor: not-allowed; box-shadow: none; }
.enviar:active:not(:disabled) { transform: scale(0.95); }
.enviar svg { width: 19px; height: 19px; }

@media (max-width: 720px) {
  .conversa { padding: 0 16px; }
  .sugestoes { grid-template-columns: 1fr; }
  .dica { display: none; }
}
</style>
