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
  /* fundo azul da barra lateral até o fim da página, mesmo em páginas longas */
  background: linear-gradient(to right, var(--azul-profundo) 264px, transparent 264px);
}

.lateral {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 30px;
  padding: 24px 16px;
  background: var(--degrade-lateral);
  color: #fff;
  overflow: hidden;
}
/* arco decorativo em menta, ao fundo */
.lateral::before {
  content: "";
  position: absolute;
  width: 360px;
  height: 360px;
  right: -230px;
  bottom: -120px;
  border-radius: 50%;
  border: 46px solid rgba(62, 233, 176, 0.13);
  pointer-events: none;
}
.lateral > * { position: relative; }

.marca { display: flex; align-items: center; gap: 12px; padding: 0 8px; }
.logo {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  background: var(--menta);
  color: var(--azul-noite);
  box-shadow: 0 8px 20px -6px rgba(62, 233, 176, 0.6);
}
.logo svg { width: 22px; height: 22px; }
.nome { font-weight: 800; font-size: 1.12rem; letter-spacing: -0.02em; color: #fff; }
.slogan { font-size: 0.8rem; color: var(--menta-clara); font-weight: 500; }

nav { display: flex; flex-direction: column; gap: 4px; }
.item {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 44px;
  padding: 0 14px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: rgba(255, 255, 255, 0.82);
  font: inherit;
  font-weight: 540;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s, color 0.15s;
}
.item svg { width: 19px; height: 19px; color: rgba(255, 255, 255, 0.6); transition: color 0.15s; }
.item:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
.item:focus-visible { outline: 2px solid var(--menta); outline-offset: 2px; }
.item.ativo { background: var(--menta); color: var(--azul-noite); font-weight: 680; box-shadow: 0 6px 16px -8px rgba(62, 233, 176, 0.8); }
.item.ativo svg { color: var(--azul-noite); }

.avancado {
  position: relative;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.07);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.avancado:hover { background: rgba(255, 255, 255, 0.11); }
.avancado.ligado { border-color: rgba(62, 233, 176, 0.5); background: rgba(62, 233, 176, 0.12); }
.avancado-texto { flex: 1; }
.linha-titulo { display: flex; align-items: center; gap: 7px; font-weight: 620; font-size: 0.88rem; color: #fff; }
.linha-titulo svg { width: 15px; height: 15px; color: var(--menta-clara); }
.descricao { font-size: 0.78rem; color: rgba(255, 255, 255, 0.72); margin-top: 4px; line-height: 1.4; }
.avancado input { position: absolute; opacity: 0; pointer-events: none; }
.chave {
  flex-shrink: 0;
  width: 36px;
  height: 20px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.28);
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
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s;
}
.avancado input:checked + .chave { background: var(--menta); }
.avancado input:checked + .chave::after { transform: translateX(16px); background: var(--azul-noite); }
.avancado input:focus-visible + .chave { box-shadow: 0 0 0 3px rgba(62, 233, 176, 0.45); }

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
