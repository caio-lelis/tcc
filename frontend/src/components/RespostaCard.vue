<script setup>
// Uma resposta do assistente (Seção 3.6): texto + gráfico + tabela; SQL só no modo avançado (RF05).
import { computed, ref } from "vue";
import Grafico from "./Grafico.vue";
import { formatar } from "../api.js";

const props = defineProps({
  pergunta: { type: String, required: true },
  resposta: { type: Object, default: null },
  erro: { type: String, default: null },
  carregando: { type: Boolean, default: false },
  avancado: { type: Boolean, default: false },
});

const verTabela = ref(false);
const LIMITE_TELA = 200;

const sucesso = computed(() => props.resposta?.status === "sucesso");
const temGrafico = computed(() => sucesso.value && props.resposta.grafico && props.resposta.grafico.tipo !== "tabela");
const linhasTela = computed(() => (props.resposta?.linhas ?? []).slice(0, LIMITE_TELA));
const ehNumero = (v) => typeof v === "number";
</script>

<template>
  <div class="troca">
    <div class="pergunta">{{ pergunta }}</div>

    <div class="cartao resposta">
      <div v-if="carregando" class="suave">Analisando os dados…</div>
      <div v-else-if="erro" class="erro">{{ erro }}</div>

      <template v-else-if="resposta">
        <div v-if="!sucesso" class="aviso">{{ resposta.mensagem }}</div>

        <template v-else>
          <p v-if="resposta.texto" class="texto">{{ resposta.texto }}</p>
          <Grafico v-if="temGrafico" :grafico="resposta.grafico" />

          <div v-if="resposta.linhas.length === 0" class="suave">Nenhum dado encontrado.</div>
          <div v-else class="linha">
            <button class="discreto" @click="verTabela = !verTabela">
              {{ verTabela || !temGrafico ? "▾" : "▸" }} Tabela ({{ resposta.linhas.length }}{{ resposta.truncado ? "+" : "" }}
              linha{{ resposta.linhas.length === 1 ? "" : "s" }})
            </button>
            <span v-if="resposta.truncado" class="selo alerta">resultado cortado no limite de linhas</span>
          </div>
          <div v-if="resposta.linhas.length && (verTabela || !temGrafico)" class="rolagem">
            <table class="dados">
              <thead>
                <tr><th v-for="c in resposta.colunas" :key="c">{{ c.replaceAll("_", " ") }}</th></tr>
              </thead>
              <tbody>
                <tr v-for="(linha, i) in linhasTela" :key="i">
                  <td v-for="(v, j) in linha" :key="j" :class="{ num: ehNumero(v) }">{{ formatar(v) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="resposta.linhas.length > LIMITE_TELA" class="suave">
              Mostrando {{ LIMITE_TELA }} de {{ resposta.linhas.length }} linhas.
            </div>
          </div>
        </template>

        <div v-if="avancado" class="tecnico">
          <div class="linha">
            <span class="selo">{{ resposta.configuracao }}</span>
            <span class="selo" :class="sucesso ? 'ok' : 'alerta'">{{ resposta.status }}</span>
            <span v-if="resposta.grafico" class="selo">gráfico: {{ resposta.grafico.tipo }} ({{ resposta.grafico.origem }})</span>
            <span class="suave">execução {{ resposta.id }}</span>
          </div>
          <pre v-if="resposta.sql" class="sql">{{ resposta.sql }}</pre>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.troca { margin-bottom: 22px; }
.pergunta {
  margin-left: auto;
  width: fit-content;
  max-width: 80%;
  background: var(--primaria);
  color: #fff;
  padding: 10px 14px;
  border-radius: 14px 14px 4px 14px;
  margin-bottom: 8px;
}
.resposta { border-radius: 14px 14px 14px 4px; }
.texto { font-size: 1.05em; line-height: 1.5; margin-top: 0; }
.tecnico { margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--borda); }
</style>
