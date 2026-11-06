<script setup>
import { ref, watch } from "vue";
import { BookOpenText, Database, MessageSquareText, MessagesSquare, Wrench } from "@lucide/vue";
import TelaConversa from "./components/TelaConversa.vue";
import TelaDados from "./components/TelaDados.vue";
import TelaContexto from "./components/TelaContexto.vue";
import Avisos from "./components/Avisos.vue";

const abas = [
  { id: "conversa", rotulo: "Perguntar", icone: MessageSquareText },
  { id: "dados", rotulo: "Meus dados", icone: Database },
  { id: "contexto", rotulo: "Sobre os dados", icone: BookOpenText },
];

function ler(chave, padrao) {
  try {
    return localStorage.getItem(chave) ?? padrao;
  } catch {
    return padrao;
  }
}
function gravar(chave, valor) {
  try {
    localStorage.setItem(chave, valor);
  } catch {
    /* sem armazenamento: segue sem lembrar */
  }
}

const parametro = new URLSearchParams(location.search).get("aba");
const aba = ref(abas.some((a) => a.id === parametro) ? parametro : ler("fala-dados:aba", "conversa"));
const avancado = ref(ler("fala-dados:avancado", "nao") === "sim");
const versao = ref(0); // muda quando as tabelas mudam, para as telas recarregarem

watch(aba, (v) => gravar("fala-dados:aba", v));
watch(avancado, (v) => gravar("fala-dados:avancado", v ? "sim" : "nao"));
</script>

<template>
  <div class="app">
    <aside class="lateral">
      <div class="marca">
        <div class="logo"><MessagesSquare /></div>
        <div>
          <div class="nome">Fala Dados</div>
          <div class="slogan">Fala com seus dados.</div>
        </div>
      </div>

      <nav>
        <button
          v-for="a in abas"
          :key="a.id"
          class="item"
          :class="{ ativo: aba === a.id }"
          @click="aba = a.id"
        >
          <component :is="a.icone" />
          <span>{{ a.rotulo }}</span>
        </button>
      </nav>

      <div class="espaco"></div>

      <label class="avancado" :class="{ ligado: avancado }">
        <div class="avancado-texto">
          <div class="linha-titulo"><Wrench /> Modo avançado</div>
          <div class="descricao">Mostra a consulta SQL e permite escolher o nível de contexto.</div>
        </div>
        <input type="checkbox" v-model="avancado" />
        <span class="chave" aria-hidden="true"></span>
      </label>
    </aside>

    <main class="conteudo">
      <TelaConversa v-show="aba === 'conversa'" :avancado="avancado" :versao="versao" @ir-para="aba = $event" />
      <TelaDados v-show="aba === 'dados'" :versao="versao" @alterado="versao++" @ir-para="aba = $event" />
      <TelaContexto v-show="aba === 'contexto'" :versao="versao" :avancado="avancado" @ir-para="aba = $event" />
    </main>

    <Avisos />
  </div>
</template>

<style scoped>
.app {
  display: grid;
  grid-template-columns: 264px 1fr;
  min-height: 100vh;
  /* fundo branco da barra lateral até o fim da página, mesmo em páginas longas */
  background: linear-gradient(to right, var(--superficie) 263px, var(--borda) 263px, var(--borda) 264px, transparent 264px);
}

.lateral {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 22px 16px;
  background: var(--superficie);
  border-right: 1px solid var(--borda);
}
.marca { display: flex; align-items: center; gap: 12px; padding: 0 8px; }
.logo {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--degrade);
  color: #fff;
  box-shadow: 0 6px 16px -4px rgba(99, 102, 241, 0.55);
}
.logo svg { width: 22px; height: 22px; }
.nome { font-weight: 750; font-size: 1.08rem; letter-spacing: -0.02em; }
.slogan { font-size: 0.8rem; color: var(--suave); }

nav { display: flex; flex-direction: column; gap: 4px; }
.item {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 42px;
  padding: 0 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--texto-2);
  font: inherit;
  font-weight: 520;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s, color 0.15s;
}
.item svg { width: 19px; height: 19px; color: var(--muito-suave); transition: color 0.15s; }
.item:hover { background: var(--superficie-2); }
.item.ativo { background: var(--primaria-50); color: var(--primaria); font-weight: 620; }
.item.ativo svg { color: var(--primaria); }

.avancado {
  position: relative;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid var(--borda);
  background: var(--superficie-2);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.avancado.ligado { border-color: var(--primaria-100); background: var(--primaria-50); }
.avancado-texto { flex: 1; }
.linha-titulo { display: flex; align-items: center; gap: 7px; font-weight: 600; font-size: 0.88rem; }
.linha-titulo svg { width: 15px; height: 15px; color: var(--suave); }
.descricao { font-size: 0.78rem; color: var(--suave); margin-top: 4px; line-height: 1.4; }
.avancado input { position: absolute; opacity: 0; pointer-events: none; }
.chave {
  flex-shrink: 0;
  width: 36px;
  height: 20px;
  border-radius: 999px;
  background: var(--borda-forte);
  position: relative;
  transition: background 0.2s;
  margin-top: 1px;
}
.chave::after {
  content: "";
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s;
}
.avancado input:checked + .chave { background: var(--primaria); }
.avancado input:checked + .chave::after { transform: translateX(16px); }
.avancado input:focus-visible + .chave { box-shadow: var(--foco); }

.conteudo { min-width: 0; }

@media (max-width: 860px) {
  .app { grid-template-columns: 1fr; }
  .lateral {
    position: sticky;
    height: auto;
    flex-direction: row;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    padding: 12px 16px;
    border-right: none;
    border-bottom: 1px solid var(--borda);
    z-index: 20;
  }
  nav { flex-direction: row; }
  .item span { display: none; }
  .slogan, .descricao, .espaco { display: none; }
  .avancado { padding: 8px 10px; }
}
</style>
