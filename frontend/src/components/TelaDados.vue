<script setup>
// Tela de anexação (RF01) e atualização de tabelas (RF10).
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

async function excluir(tabela) {
  if (!confirm(`Remover a tabela "${tabela}"?\n\nO que você escreveu sobre ela fica guardado e volta se ela for anexada de novo.`)) return;
  try {
    await api.removerTabela(tabela);
    avisar(`Tabela "${tabela}" removida.`);
    emit("alterado");
  } catch (e) {
    avisar(e.message, "erro");
  }
}

function alternar(nomeTabela) {
  const s = new Set(abertas.value);
  s.has(nomeTabela) ? s.delete(nomeTabela) : s.add(nomeTabela);
  abertas.value = s;
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
      <article v-for="t in tabelas" :key="t.nome" class="cartao tabela-cartao">
        <header class="tabela-topo">
          <div class="tabela-icone"><FileSpreadsheet /></div>
          <div>
            <h3>{{ t.nome }}</h3>
            <div class="texto-suave pequeno">{{ formatarNumero(t.linhas) }} linhas · {{ t.colunas.length }} colunas</div>
          </div>
          <span class="espaco"></span>
          <button class="botao fantasma icone pequeno perigo" title="Remover tabela" @click="excluir(t.nome)"><Trash2 /></button>
        </header>

        <div class="colunas">
          <span v-for="c in t.colunas" :key="c.nome" class="coluna" :title="`${c.tipo} · original: ${c.nome_original}`">
            <component :is="iconeDoTipo(c.tipo)" />{{ c.nome }}
          </span>
        </div>

        <button class="ver-amostra" @click="alternar(t.nome)">
          <Rows3 /> {{ abertas.has(t.nome) ? "Esconder amostra" : "Ver amostra" }}
          <ChevronDown class="seta" :class="{ aberta: abertas.has(t.nome) }" />
        </button>
        <div v-if="abertas.has(t.nome)" class="amostra surgir">
          <TabelaResultado :colunas="t.colunas.map((c) => c.nome)" :linhas="amostraEmLinhas(t)" />
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.soltar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 36px 24px;
  border: 2px dashed var(--borda-forte);
  border-radius: var(--raio-lg);
  background: var(--superficie);
  cursor: pointer;
  text-align: center;
  transition: border-color 0.15s, background 0.15s;
}
.soltar:hover, .soltar.arrastando { border-color: #a5b4fc; background: #fafbff; }
.soltar.arrastando { transform: scale(1.005); }
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
.tabela-cartao { padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; min-width: 0; }
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
