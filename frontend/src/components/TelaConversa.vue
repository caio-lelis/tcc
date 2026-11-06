<script setup>
// Tela de conversa (RF04): pergunta em linguagem natural, resposta em texto, gráfico e tabela.
import { nextTick, onMounted, ref, watch } from "vue";
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

const EXEMPLOS = [
  "Quantas vendas houve em março de 2026?",
  "Como evoluiu a receita mês a mês em 2026?",
  "Qual closer vendeu mais este ano?",
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

async function enviar(texto) {
  const p = (texto ?? pergunta.value).trim();
  if (!p || enviando.value) return;
  pergunta.value = "";
  const troca = { pergunta: p, resposta: null, erro: null, carregando: true };
  trocas.value.push(troca);
  enviando.value = true;
  await nextTick();
  fim.value?.scrollIntoView({ behavior: "smooth" });

  const atual = trocas.value[trocas.value.length - 1];
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
    await nextTick();
    fim.value?.scrollIntoView({ behavior: "smooth" });
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
  <section>
    <div v-if="tabelas && tabelas.length === 0" class="cartao">
      <h3>Comece pelos seus dados</h3>
      <p class="suave">Ainda não há nenhuma tabela. Anexe arquivos CSV para poder fazer perguntas.</p>
      <button class="primario" @click="$emit('ir-para', 'dados')">Anexar dados</button>
    </div>

    <div v-else-if="trocas.length === 0" class="cartao boas-vindas">
      <h3>O que você quer saber?</h3>
      <p class="suave">Pergunte como você perguntaria a um colega. Por exemplo:</p>
      <div class="linha">
        <button v-for="e in EXEMPLOS" :key="e" class="exemplo" @click="enviar(e)">{{ e }}</button>
      </div>
    </div>

    <RespostaCard v-for="(t, i) in trocas" :key="i" v-bind="t" :avancado="avancado" />
    <div ref="fim"></div>

    <form class="entrada cartao" @submit.prevent="enviar()">
      <textarea
        v-model="pergunta"
        rows="2"
        placeholder="Escreva sua pergunta… (Enter envia, Shift+Enter quebra a linha)"
        :disabled="tabelas?.length === 0"
        @keydown="aoTeclar"
      ></textarea>
      <div class="linha">
        <label v-if="avancado" class="linha suave">
          Contexto:
          <select v-model="configuracao" class="config">
            <option value="">padrão</option>
            <option value="C0">C0: só esquema</option>
            <option value="C1">C1: + descrições</option>
            <option value="C2">C2: + regras</option>
          </select>
        </label>
        <span class="espaco"></span>
        <button class="primario" type="submit" :disabled="!pergunta.trim() || enviando">
          {{ enviando ? "Respondendo…" : "Perguntar" }}
        </button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.entrada { position: sticky; bottom: 16px; box-shadow: 0 6px 24px rgba(29, 36, 51, 0.08); margin-top: 8px; }
.entrada textarea { margin-bottom: 10px; border: none; padding: 4px; }
.entrada textarea:focus { outline: none; }
.config { width: auto; }
.exemplo { background: var(--primaria-suave); border-color: transparent; color: var(--primaria); }
</style>
