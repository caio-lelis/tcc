<script setup>
import { ref, watch } from "vue";
import TelaConversa from "./components/TelaConversa.vue";
import TelaDados from "./components/TelaDados.vue";
import TelaContexto from "./components/TelaContexto.vue";

const abas = [
  { id: "conversa", rotulo: "Perguntar" },
  { id: "dados", rotulo: "Meus dados" },
  { id: "contexto", rotulo: "Sobre os dados" },
];

function lerPreferencia(chave, padrao) {
  try {
    return localStorage.getItem(chave) ?? padrao;
  } catch {
    return padrao;
  }
}
function gravarPreferencia(chave, valor) {
  try {
    localStorage.setItem(chave, valor);
  } catch {
    /* sem armazenamento: segue sem lembrar */
  }
}

const aba = ref(lerPreferencia("fala-dados:aba", "conversa"));
const avancado = ref(lerPreferencia("fala-dados:avancado", "nao") === "sim");
const versao = ref(0); // muda quando tabelas ou contexto mudam, para as telas recarregarem

watch(aba, (valor) => gravarPreferencia("fala-dados:aba", valor));
watch(avancado, (valor) => gravarPreferencia("fala-dados:avancado", valor ? "sim" : "nao"));
</script>

<template>
  <header class="topo">
    <div class="marca">
      <span class="logo">💬</span>
      <div>
        <strong>Fala Dados</strong>
        <div class="suave">Fala com seus dados.</div>
      </div>
    </div>
    <nav>
      <button v-for="a in abas" :key="a.id" :class="{ ativa: aba === a.id }" @click="aba = a.id">
        {{ a.rotulo }}
      </button>
    </nav>
    <label class="avancado" title="Mostra a consulta SQL e permite escolher a configuração de contexto">
      <input type="checkbox" v-model="avancado" />
      Modo avançado
    </label>
  </header>

  <main>
    <TelaConversa v-show="aba === 'conversa'" :avancado="avancado" :versao="versao" @ir-para="aba = $event" />
    <TelaDados v-show="aba === 'dados'" :versao="versao" @alterado="versao++" />
    <TelaContexto v-show="aba === 'contexto'" :versao="versao" :avancado="avancado" />
  </main>
</template>

<style scoped>
.topo {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
  padding: 14px 24px;
  background: var(--superficie);
  border-bottom: 1px solid var(--borda);
  position: sticky;
  top: 0;
  z-index: 10;
}
.marca { display: flex; align-items: center; gap: 10px; }
.logo { font-size: 1.8em; }
nav { display: flex; gap: 6px; flex: 1; }
nav button { border: none; background: none; color: var(--texto-suave); }
nav button.ativa { background: var(--primaria-suave); color: var(--primaria); font-weight: 600; }
.avancado { display: flex; align-items: center; gap: 6px; font-size: 0.9em; color: var(--texto-suave); cursor: pointer; }
.avancado input { width: auto; }
main { max-width: 980px; margin: 0 auto; padding: 24px 16px 64px; }
</style>
