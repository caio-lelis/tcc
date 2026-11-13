<script setup>
// Tela de anexação (RF01) e atualização de tabelas (RF10).
// Movimentos (borda que anda, esqueleto, remoção que se dissolve, sanfona) em docs/interface-fontes.md.
import { onMounted, ref, watch } from "vue";
import {
  Calendar, ChevronDown, CloudUpload, FileSpreadsheet, Hash, LoaderCircle, Rows3, ToggleLeft, Trash2, Type, X,
} from "@lucide/vue";
import TabelaResultado from "./TabelaResultado.vue";
import { api } from "../api.js";
import { avisar } from "../avisos.js";
import { formatarBytes, formatarNumero } from "../formatacao.js";

const props = defineProps({ versao: { type: Number, default: 0 } });
const emit = defineEmits(["alterado", "ir-para"]);

const tabelas = ref([]);
const arquivos = ref([]);
const nome = ref("");
const enviando = ref(false);
const resultados = ref([]);
const arrastando = ref(false);
const seletor = ref(null);
const abertas = ref(new Set());
const montadas = ref(new Set()); // amostras já abertas uma vez: continuam no DOM para a sanfona fechar suave
const confirmando = ref(null);
const saindo = ref(null);

async function carregar() {
  try {
    tabelas.value = await api.listarTabelas();
  } catch (e) {
    avisar(e.message, "erro");
  }
}
onMounted(carregar);
watch(() => props.versao, carregar);

function escolher(lista) {
  const csvs = [...lista].filter((a) => a.name.toLowerCase().endsWith(".csv"));
  if (csvs.length < lista.length) avisar("Só arquivos .csv são aceitos.", "erro");
  arquivos.value = csvs;
  if (csvs.length !== 1) nome.value = "";
}
function aoSoltar(evento) {
  arrastando.value = false;
  escolher(evento.dataTransfer.files);
}
function remover(i) {
  arquivos.value.splice(i, 1);
}

async function anexar() {
  enviando.value = true;
  resultados.value = [];
  try {
    for (const arquivo of arquivos.value) {
      const r = await api.anexarTabela(arquivo, arquivos.value.length === 1 ? nome.value : "");
      resultados.value.push({ arquivo: arquivo.name, ...r });
    }
    avisar(arquivos.value.length === 1 ? "Tabela anexada." : `${arquivos.value.length} tabelas anexadas.`);
    arquivos.value = [];
    nome.value = "";
    if (seletor.value) seletor.value.value = "";
    emit("alterado");
  } catch (e) {
    avisar(e.message, "erro");
  } finally {
    enviando.value = false;
  }
}

// remoção confirmada no próprio cartão, sem janela do navegador; o cartão se dissolve ao sair
async function excluir(tabela) {
  confirmando.value = null;
  saindo.value = tabela;
  try {
    await Promise.all([api.removerTabela(tabela), new Promise((r) => setTimeout(r, 500))]);
    avisar(`Tabela "${tabela}" removida. O que você escreveu sobre ela fica guardado e volta se ela for anexada de novo.`);
    emit("alterado");
  } catch (e) {
    avisar(e.message, "erro");
  } finally {
    saindo.value = null;
  }
}

function alternar(nomeTabela) {
  const s = new Set(abertas.value);
  s.has(nomeTabela) ? s.delete(nomeTabela) : s.add(nomeTabela);
  abertas.value = s;
  montadas.value = new Set([...montadas.value, nomeTabela]);
}

function classeDoTipo(tipo) {
  const t = tipo.toUpperCase();
  if (/INT|DOUBLE|FLOAT|DECIMAL|REAL/.test(t)) return "numero";
  if (/DATE|TIME/.test(t)) return "data";
  if (t === "BOOLEAN") return "logico";
  return "texto";
}

function iconeDoTipo(tipo) {
  const t = tipo.toUpperCase();
  if (/INT|DOUBLE|FLOAT|DECIMAL|REAL/.test(t)) return Hash;
  if (/DATE|TIME/.test(t)) return Calendar;
  if (t === "BOOLEAN") return ToggleLeft;
  return Type;
}
const amostraEmLinhas = (t) => t.amostra.map((l) => t.colunas.map((c) => l[c.nome]));
</script>

<template>
  <section class="pagina">
    <header class="cabecalho">
      <h1>Meus dados</h1>
      <p>
        Anexe as tabelas exportadas dos sistemas da empresa, em CSV. Cada arquivo vira uma tabela. Enviar de novo um
        arquivo com o mesmo nome atualiza a tabela e mantém tudo o que você já escreveu sobre ela.
      </p>
    </header>

    <!-- área de envio -->
    <div
      class="soltar"
      :class="{ arrastando }"
      @dragover.prevent="arrastando = true"
      @dragleave.prevent="arrastando = false"
      @drop.prevent="aoSoltar"
      @click="seletor?.click()"
    >
      <input ref="seletor" type="file" accept=".csv,text/csv" multiple hidden @change="escolher($event.target.files)" />
      <div class="soltar-icone"><CloudUpload /></div>
      <div class="soltar-titulo">Arraste arquivos CSV para cá</div>
      <div class="texto-suave pequeno">ou <span class="link">clique para escolher</span> · até 50 MB por arquivo</div>
    </div>

    <div v-if="arquivos.length" class="escolhidos cartao preenchido surgir">
      <div v-for="(a, i) in arquivos" :key="a.name" class="escolhido">
        <FileSpreadsheet class="icone-arquivo" />
        <span class="nome-arquivo">{{ a.name }}</span>
        <span class="texto-suave pequeno">{{ formatarBytes(a.size) }}</span>
        <span class="espaco"></span>
        <button class="botao fantasma icone pequeno" title="Tirar da lista" @click="remover(i)"><X /></button>
      </div>
      <div class="linha envio">
        <input
          v-if="arquivos.length === 1"
          v-model="nome"
          class="campo nome-tabela"
          placeholder="Nome da tabela (opcional; padrão: nome do arquivo)"
        />
        <span class="espaco"></span>
        <button class="botao primario" :disabled="enviando" @click="anexar">
          <LoaderCircle v-if="enviando" class="girando" /><CloudUpload v-else />
          {{ enviando ? "Enviando…" : arquivos.length === 1 ? "Anexar tabela" : `Anexar ${arquivos.length} tabelas` }}
        </button>
      </div>
      <div v-if="enviando" class="progresso" role="progressbar" aria-label="Enviando"><span></span></div>
    </div>

    <!-- o que mudou no último envio (RF10) -->
    <div v-if="resultados.length" class="resultados surgir">
      <div v-for="r in resultados" :key="r.arquivo" class="resultado">
        <strong>{{ r.tabela.nome }}</strong>
        <span v-if="r.nova" class="selo verde">nova tabela</span>
        <span v-else class="selo primario">atualizada</span>
        <span class="texto-suave pequeno">{{ formatarNumero(r.tabela.linhas) }} linhas</span>
        <span v-if="r.colunas_novas.length" class="selo ambar">colunas novas: {{ r.colunas_novas.join(", ") }}</span>
        <span v-if="r.colunas_removidas.length" class="selo ambar">removidas: {{ r.colunas_removidas.join(", ") }}</span>
        <span v-if="r.colunas_tipo_alterado.length" class="selo ambar">tipo mudou: {{ r.colunas_tipo_alterado.join(", ") }}</span>
        <button v-if="r.colunas_novas.length || r.nova" class="botao fantasma pequeno" @click="$emit('ir-para', 'contexto')">
          Descrever →
        </button>
      </div>
    </div>

    <!-- tabelas anexadas -->
    <div class="secao-titulo">
      <h2>Tabelas anexadas</h2>
      <span class="contagem">{{ tabelas.length }}</span>
    </div>

    <div v-if="!tabelas.length" class="cartao preenchido vazio texto-suave">Nenhuma tabela anexada ainda.</div>

    <div class="grade">
      <article
        v-for="(t, i) in tabelas"
        :key="t.nome"
        class="cartao tabela-cartao vivo revela"
        :class="{ saindo: saindo === t.nome, confirmando: confirmando === t.nome }"
        :style="{ '--i': i + 2 }"
      >
        <header class="tabela-topo">
          <div class="tabela-icone"><FileSpreadsheet /></div>
          <div>
            <h3>{{ t.nome }}</h3>
            <div class="texto-suave pequeno">{{ formatarNumero(t.linhas) }} linhas · {{ t.colunas.length }} colunas</div>
          </div>
          <span class="espaco"></span>
          <Transition name="troca" mode="out-in">
            <div v-if="confirmando === t.nome" key="c" class="confirmar">
              <span>Remover?</span>
              <button class="botao pequeno sim" @click="excluir(t.nome)">Sim</button>
              <button class="botao pequeno" @click="confirmando = null">Não</button>
            </div>
            <button v-else key="b" class="botao fantasma icone pequeno perigo" :aria-label="`Remover a tabela ${t.nome}`" @click="confirmando = t.nome"><Trash2 /></button>
          </Transition>
        </header>

        <div class="colunas">
          <span v-for="c in t.colunas" :key="c.nome" class="coluna" :class="classeDoTipo(c.tipo)" :title="`${c.tipo} · original: ${c.nome_original}`">
            <component :is="iconeDoTipo(c.tipo)" />{{ c.nome }}
          </span>
        </div>

        <button class="ver-amostra" :aria-expanded="abertas.has(t.nome)" @click="alternar(t.nome)">
          <Rows3 /> {{ abertas.has(t.nome) ? "Esconder amostra" : "Ver amostra" }}
          <ChevronDown class="seta" :class="{ aberta: abertas.has(t.nome) }" />
        </button>
        <div class="sanfona-corpo-anim" :class="{ aberta: abertas.has(t.nome) }">
          <div>
            <TabelaResultado v-if="montadas.has(t.nome)" class="amostra" :colunas="t.colunas.map((c) => c.nome)" :linhas="amostraEmLinhas(t)" />
          </div>
        </div>
      </article>

      <!-- esqueleto da tabela que está chegando -->
      <article v-if="enviando" class="cartao tabela-cartao esqueleto-cartao" aria-label="Lendo a tabela nova">
        <div class="tabela-topo"><span class="esqueleto" style="width: 40px; height: 40px; border-radius: 12px"></span><div style="flex: 1; display: flex; flex-direction: column; gap: 7px"><span class="esqueleto" style="width: 55%; height: 14px"></span><span class="esqueleto" style="width: 35%; height: 11px"></span></div></div>
        <div class="colunas"><span class="esqueleto" style="width: 70px; height: 24px"></span><span class="esqueleto" style="width: 96px; height: 24px"></span><span class="esqueleto" style="width: 62px; height: 24px"></span></div>
      </article>
    </div>
  </section>
</template>

<style scoped>
/* área de soltar com "formigas": o tracejado anda em volta da borda */
.soltar {
  --traco: var(--borda-forte);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 36px 24px;
  border-radius: 26px;
  background-color: var(--superficie);
  background-image:
    repeating-linear-gradient(90deg, var(--traco) 0 10px, transparent 10px 18px),
    repeating-linear-gradient(90deg, var(--traco) 0 10px, transparent 10px 18px),
    repeating-linear-gradient(0deg, var(--traco) 0 10px, transparent 10px 18px),
    repeating-linear-gradient(0deg, var(--traco) 0 10px, transparent 10px 18px);
  background-size: 100% 2px, 100% 2px, 2px 100%, 2px 100%;
  background-position: 0 0, 0 100%, 0 0, 100% 0;
  background-repeat: no-repeat;
  animation: formigas 1.2s linear infinite, revela 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.2s backwards;
  cursor: pointer;
  text-align: center;
  transition: background-color 0.3s, transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes formigas { to { background-position: 18px 0, -18px 100%, 0 -18px, 100% 18px; } }
.soltar:hover, .soltar.arrastando { --traco: var(--primaria); background-color: var(--menta-50); }
.soltar.arrastando { transform: scale(1.01); }
.soltar-icone { transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1); }
.soltar:hover .soltar-icone, .soltar.arrastando .soltar-icone { transform: translateY(-6px) scale(1.08); }

.progresso { height: 6px; margin-top: 12px; border-radius: 99px; background: var(--trilho); overflow: hidden; }
.progresso span { display: block; height: 100%; width: 40%; border-radius: 99px; background: var(--primaria); animation: vai-e-vem 1.2s ease-in-out infinite; }
@keyframes vai-e-vem { from { transform: translateX(-100%); } to { transform: translateX(250%); } }
.soltar-icone {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: var(--primaria-50);
  color: var(--primaria);
  margin-bottom: 8px;
}
.soltar-icone svg { width: 26px; height: 26px; }
.soltar-titulo { font-weight: 620; font-size: 1.02rem; }
.link { color: var(--primaria); font-weight: 600; }

.escolhidos { margin-top: 14px; display: flex; flex-direction: column; gap: 8px; }
.escolhido { display: flex; align-items: center; gap: 10px; }
.icone-arquivo { width: 20px; height: 20px; color: var(--verde); }
.nome-arquivo { font-weight: 550; }
.envio { margin-top: 10px; padding-top: 14px; border-top: 1px solid var(--borda); }
.nome-tabela { max-width: 380px; }

.resultados { margin-top: 14px; display: flex; flex-direction: column; gap: 8px; }
.resultado {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  border-radius: var(--raio);
  background: var(--superficie);
  border: 1px solid var(--borda);
}

.vazio { text-align: center; }
.grade { display: grid; grid-template-columns: repeat(auto-fill, minmax(440px, 1fr)); gap: 16px; }
.tabela-cartao { padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; min-width: 0; border-radius: 24px; }
.tabela-cartao.confirmando { border-color: var(--vermelho); }
.tabela-cartao.saindo { animation: dissolve 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards; pointer-events: none; }
@keyframes dissolve { to { opacity: 0; transform: scale(0.92); filter: blur(10px); } }
.confirmar { display: flex; align-items: center; gap: 6px; font-size: 0.86rem; font-weight: 600; color: var(--vermelho); }
.confirmar .sim { background: var(--vermelho); border-color: var(--vermelho); color: #fff; }
.troca-enter-active, .troca-leave-active { transition: opacity 0.2s, transform 0.3s cubic-bezier(0.34, 1.4, 0.64, 1), filter 0.2s; }
.troca-enter-from, .troca-leave-to { opacity: 0; transform: scale(0.9); filter: blur(3px); }
.esqueleto-cartao { animation: revela 0.5s cubic-bezier(0.22, 1, 0.36, 1) backwards; }
.amostra { margin-top: 4px; }
.tabela-topo { display: flex; align-items: center; gap: 12px; }
.tabela-topo h3 { font-size: 1.02rem; }
.tabela-icone {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--verde-50);
  color: var(--verde);
}
.tabela-icone svg { width: 20px; height: 20px; }

.colunas { display: flex; flex-wrap: wrap; gap: 6px; }
.coluna {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 9px;
  border-radius: 7px;
  background: var(--superficie-2);
  border: 1px solid var(--borda);
  font-size: 0.8rem;
  font-family: "JetBrains Mono", "Cascadia Code", Consolas, monospace;
  color: var(--texto-2);
}
.coluna svg { width: 12px; height: 12px; color: var(--muito-suave); }
/* cor por tipo: número, data, sim/não; texto fica neutro */
.coluna.numero { background: var(--primaria-50); border-color: var(--primaria-100); color: var(--primaria); }
.coluna.numero svg { color: var(--primaria); }
.coluna.data { background: var(--ambar-50); border-color: var(--ambar-borda); color: var(--ambar-texto); }
.coluna.data svg { color: var(--ambar); }
.coluna.logico { background: var(--menta-50); border-color: var(--menta-borda); color: var(--menta-texto); }
.coluna.logico svg { color: var(--menta-texto); }

.ver-amostra {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: none;
  padding: 0;
  font: inherit;
  font-size: 0.86rem;
  font-weight: 550;
  color: var(--primaria);
  cursor: pointer;
}
.ver-amostra svg { width: 15px; height: 15px; }
.seta { transition: transform 0.2s; }
.seta.aberta { transform: rotate(180deg); }

@media (max-width: 720px) {
  .grade { grid-template-columns: 1fr; }
}
</style>
