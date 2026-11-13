<script setup>
// Casca do Data Talk: barra superior com a logo, as abas em pílula, o modo avançado e o tema.
// Layout em "bento" (React Bits Pro, blocos de navegação e bento); movimentos em docs/interface-fontes.md.
import { computed, ref, watch } from "vue";
import { FileText, Moon, PanelRightClose, Sun } from "@lucide/vue";
import LogoDataTalk from "./components/LogoDataTalk.vue";
import TelaInicio from "./components/TelaInicio.vue";
import TelaConversa from "./components/TelaConversa.vue";
import TelaDados from "./components/TelaDados.vue";
import TelaContexto from "./components/TelaContexto.vue";
import TelaRelatorios from "./components/TelaRelatorios.vue";
import EditorRelatorio from "./components/EditorRelatorio.vue";
import Avisos from "./components/Avisos.vue";
import { alternarTema, tema } from "./tema.js";
import { avisar } from "./avisos.js";
import { abrirRelatorio, carregarLista, criarRelatorio, relatorios } from "./relatorios.js";
import { usarIndicador } from "./indicador.js";
import { atualizarJornada } from "./jornada.js";

const abas = [
  { id: "inicio", rotulo: "Início" },
  { id: "conversa", rotulo: "Perguntar" },
  { id: "dados", rotulo: "Meus dados" },
  { id: "contexto", rotulo: "Sobre os dados" },
  { id: "relatorios", rotulo: "Relatórios" },
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

const existe = (id) => abas.some((a) => a.id === id);
const parametro = new URLSearchParams(location.search).get("aba");
const salva = ler("data-talk:aba", "inicio");
const aba = ref(existe(parametro) ? parametro : existe(salva) ? salva : "inicio");
const avancado = ref(ler("data-talk:avancado", "nao") === "sim");
const versao = ref(0); // muda quando as tabelas mudam, para as telas recarregarem

// direção da troca de tela: indo para uma aba mais à direita, a tela entra pela direita
const direcao = ref(1);
watch(aba, (nova, antiga) => {
  gravar("data-talk:aba", nova);
  direcao.value = abas.findIndex((a) => a.id === nova) >= abas.findIndex((a) => a.id === antiga) ? 1 : -1;
  atualizarJornada();
});
watch(avancado, (v) => gravar("data-talk:avancado", v ? "sim" : "nao"));
atualizarJornada();
watch(versao, atualizarJornada);

// pílula sólida no item ativo + pílula-fantasma que segue o mouse
const menu = ref(null);
const sobre = ref(null);
const { estilo: estiloPilula } = usarIndicador(menu, aba);
const { estilo: estiloFantasma } = usarIndicador(menu, sobre, "[data-sobre='true']");

const painelVisivel = computed(() => aba.value === "conversa" && relatorios.painelAberto);

async function alternarPainel() {
  if (relatorios.painelAberto) {
    relatorios.painelAberto = false;
    return;
  }
  try {
    if (!relatorios.atual) {
      await carregarLista();
      if (relatorios.lista.length) await abrirRelatorio(relatorios.lista[0].id);
      else await criarRelatorio("Relatório sem título");
    }
    relatorios.painelAberto = true;
  } catch (e) {
    avisar(e.message, "erro");
  }
}
</script>

<template>
  <div class="app">
    <header class="topo revela">
      <button class="marca" aria-label="Data Talk, ir para o início" @click="aba = 'inicio'">
        <LogoDataTalk class="logo-topo" />
      </button>

      <nav ref="menu" class="abas" aria-label="Seções" @mouseleave="sobre = null">
        <span class="pilula-deslizante fantasma" :style="estiloFantasma" aria-hidden="true"></span>
        <span class="pilula-deslizante ativa" :style="estiloPilula" aria-hidden="true"></span>
        <button
          v-for="a in abas"
          :key="a.id"
          class="aba"
          :class="{ ativo: aba === a.id }"
          :data-ativo="aba === a.id"
          :data-sobre="sobre === a.id && aba !== a.id"
          :aria-current="aba === a.id ? 'page' : undefined"
          @mouseenter="sobre = a.id"
          @click="aba = a.id"
        >
          {{ a.rotulo }}
        </button>
      </nav>

      <div class="espaco"></div>

      <label class="avancado" title="Mostra a consulta SQL e permite escolher o nível de contexto">
        <input v-model="avancado" type="checkbox" />
        <span>Modo avançado</span>
        <span class="chave" aria-hidden="true"></span>
      </label>

      <button class="botao-tema" :aria-label="tema === 'escuro' ? 'Usar tema claro' : 'Usar tema escuro'" @click="alternarTema">
        <Moon class="icone-tema" :class="{ visivel: tema !== 'escuro' }" />
        <Sun class="icone-tema sol" :class="{ visivel: tema === 'escuro' }" />
      </button>
    </header>

    <main class="conteudo" :class="{ 'com-painel': painelVisivel }" :style="{ '--direcao': direcao }">
      <button v-if="aba === 'conversa' && !relatorios.painelAberto" class="botao abrir-painel" @click="alternarPainel">
        <FileText /> Relatório
      </button>
      <!-- cada tela entra deslizando de leve; a que sai some na hora, para não haver duas na tela -->
      <Transition name="tela"><TelaInicio v-show="aba === 'inicio'" :versao="versao" @ir-para="aba = $event" /></Transition>
      <Transition name="tela"><TelaConversa v-show="aba === 'conversa'" :avancado="avancado" :versao="versao" @ir-para="aba = $event" /></Transition>
      <Transition name="tela"><TelaDados v-show="aba === 'dados'" :versao="versao" @alterado="versao++" @ir-para="aba = $event" /></Transition>
      <Transition name="tela"><TelaContexto v-show="aba === 'contexto'" :versao="versao" :avancado="avancado" @ir-para="aba = $event" /></Transition>
      <Transition name="tela"><TelaRelatorios v-if="aba === 'relatorios'" /></Transition>

      <Transition name="painel">
        <aside v-if="painelVisivel" class="painel-relatorio">
          <button class="botao fantasma icone pequeno fechar-painel" title="Fechar painel" aria-label="Fechar painel" @click="alternarPainel"><PanelRightClose /></button>
          <EditorRelatorio compacto />
        </aside>
      </Transition>
    </main>

    <Avisos />
  </div>
</template>

<style scoped>
.app { min-height: 100vh; display: flex; flex-direction: column; background: var(--fundo); }

/* ---------- barra superior ---------- */
.topo {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 24px;
  padding: 14px 32px;
  background: color-mix(in srgb, var(--superficie) 88%, transparent);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--borda);
}
.marca { display: block; width: 150px; padding: 0; border: none; background: none; cursor: pointer; border-radius: 10px; }
.marca:focus-visible { outline: 2px solid var(--borda-foco); outline-offset: 4px; }
.logo-topo { width: 100%; }

.abas {
  position: relative;
  display: flex;
  padding: 4px;
  border-radius: 999px;
  background: var(--superficie-2);
  border: 1px solid var(--borda);
  max-width: 100%;
  overflow-x: auto;
  scrollbar-width: none;
}
.pilula-deslizante { top: 0; left: 0; border-radius: 999px; }
.pilula-deslizante.ativa { background: var(--texto); }
.pilula-deslizante.fantasma { background: var(--borda); }
.aba {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  height: 38px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--texto-2);
  font: inherit;
  font-size: 0.93rem;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: color 0.3s ease;
}
.aba:hover { color: var(--texto); }
.aba.ativo { color: var(--fundo); font-weight: 650; }
.aba:focus-visible { outline: 2px solid var(--borda-foco); outline-offset: 2px; }

/* interruptor com quique duplo */
.avancado { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 0.86rem; font-weight: 600; color: var(--texto-2); }
.avancado input { position: absolute; opacity: 0; pointer-events: none; }
.chave { position: relative; width: 40px; height: 22px; border-radius: 999px; background: var(--borda-forte); transition: background 0.35s; }
.chave::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
  transition: transform 0.55s cubic-bezier(0.68, -0.6, 0.32, 1.6), background 0.35s;
}
.avancado input:checked + span + .chave { background: var(--menta); }
.avancado input:checked + span + .chave::after { transform: translateX(18px); background: var(--azul-noite); }
.avancado input:focus-visible + span + .chave { box-shadow: var(--foco); }

/* troca de ícone do tema: gira, encolhe e desfoca */
.botao-tema {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 13px;
  border: 1px solid var(--borda);
  background: var(--superficie);
  color: var(--texto);
  cursor: pointer;
}
.botao-tema:focus-visible { outline: none; box-shadow: var(--foco); }
.icone-tema {
  grid-area: 1 / 1;
  width: 19px;
  height: 19px;
  opacity: 0;
  transform: rotate(-90deg) scale(0.4);
  filter: blur(4px);
  transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.25s, filter 0.25s;
}
.icone-tema.visivel { opacity: 1; transform: none; filter: none; }
.icone-tema.sol { color: var(--caramelo); }

/* ---------- conteúdo ---------- */
.conteudo { flex: 1; min-width: 0; position: relative; }
.conteudo.com-painel { display: grid; grid-template-columns: minmax(0, 1fr) minmax(420px, 46%); }
.conteudo.com-painel :deep(.conversa) { width: 100%; margin: 0; padding: 0 24px; }

.tela-enter-active { transition: opacity 0.35s ease-out, transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), filter 0.35s; }
.tela-enter-from { opacity: 0; transform: translateX(calc(var(--direcao, 1) * 18px)); filter: blur(4px); }

.painel-enter-active { transition: opacity 0.25s, transform 0.35s cubic-bezier(0.22, 1, 0.36, 1); }
.painel-enter-from { opacity: 0; transform: translateX(24px); }

.abrir-painel { position: absolute; top: 18px; right: 22px; z-index: 5; box-shadow: var(--sombra-sm); }
.painel-relatorio {
  position: sticky;
  top: 71px;
  height: calc(100vh - 71px);
  overflow-y: auto;
  padding: 18px 20px 40px;
  background: var(--superficie-2);
  border-left: 1px solid var(--borda);
}
.fechar-painel { position: absolute; top: 12px; right: 12px; z-index: 3; }
.painel-relatorio :deep(.titulo-relatorio) { padding-right: 36px; }

@media (max-width: 1180px) {
  .conteudo.com-painel { display: block; }
  .conteudo.com-painel :deep(.conversa) { margin: 0 auto; padding: 0 32px; }
  .painel-relatorio { position: fixed; inset: 0 0 0 auto; z-index: 30; width: min(560px, 100vw); height: 100vh; box-shadow: var(--sombra-lg); }
}

@media (max-width: 760px) {
  .topo { padding: 12px 16px; gap: 10px 12px; }
  .marca { width: 118px; }
  .abas { order: 3; width: 100%; }
  .avancado span:first-of-type { display: none; }
}
</style>
