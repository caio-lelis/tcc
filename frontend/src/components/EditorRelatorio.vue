<script setup>
// Editor do relatório: blocos de título, texto e resultados anexados da conversa.
import { computed, nextTick, ref } from "vue";
import {
  ArrowDown, ArrowUp, BarChart3, Check, CloudOff, Download, FileDown, GripVertical, Heading2, LoaderCircle,
  RefreshCw, Table2, Trash2, Type,
} from "@lucide/vue";
import Grafico from "./Grafico.vue";
import TextoRico from "./TextoRico.vue";
import TabelaResultado from "./TabelaResultado.vue";
import { formatarNumero, formatarValor, nomeLegivel } from "../formatacao.js";
import {
  adicionarBloco, atualizarBloco, atualizarTodos, exportarPdf, marcarAlterado, moverBloco, relatorios, removerBloco, urlDoPdf,
} from "../relatorios.js";

defineProps({ compacto: { type: Boolean, default: false } });

const atual = computed(() => relatorios.atual);
const temResultados = computed(() => atual.value.blocos.some((b) => b.tipo === "resultado"));
const arrastando = ref(null);
const destino = ref(null);
const editor = ref(null);
const blocoNovo = ref(null); // o bloco recém-criado recebe o cursor

const SITUACAO = {
  salvo: "Salvo",
  pendente: "Salvando…",
  salvando: "Salvando…",
  erro: "Não foi salvo",
};

const dataHora = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });
const quando = (valor) => dataHora.format(new Date(valor));
const tamanho = (bytes) => (bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")} MB`);

const temGrafico = (b) => ["linha", "barra"].includes(b.grafico?.tipo) && b.grafico.series?.length > 0;
const indicadores = (b) => (b.grafico?.tipo === "indicador" ? b.grafico.indicadores : []);

function ajustar(evento) {
  const campo = evento.target;
  campo.style.height = "auto";
  campo.style.height = `${campo.scrollHeight}px`;
}
function aoDigitar(evento) {
  ajustar(evento);
  marcarAlterado();
}
// textareas já preenchidos nascem com a altura do conteúdo
const vAltura = {
  mounted: (el) => nextTick(() => ajustar({ target: el })),
  updated: (el) => ajustar({ target: el }),
};

async function novoBloco(tipo) {
  adicionarBloco(tipo);
  blocoNovo.value = atual.value.blocos[atual.value.blocos.length - 1].id;
  if (tipo !== "titulo") return; // o editor de texto pega o foco ao nascer
  await nextTick();
  const campos = editor.value.querySelectorAll(".bloco textarea");
  campos[campos.length - 1]?.focus();
}

function aplicarTexto(bloco, { doc, texto }) {
  bloco.doc = doc;
  bloco.texto = texto;
  marcarAlterado();
}

function trocarVisao(bloco, visao) {
  bloco.visao = visao;
  marcarAlterado();
}

async function exportar() {
  const versao = await exportarPdf();
  if (versao) location.assign(urlDoPdf(atual.value.id, versao.numero));
}

function soltar(indice) {
  if (arrastando.value !== null) moverBloco(arrastando.value, indice);
  arrastando.value = destino.value = null;
}
</script>

<template>
  <div v-if="atual" ref="editor" class="editor" :class="{ compacto }">
    <header class="topo">
      <input
        v-model="atual.titulo"
        class="titulo-relatorio"
        maxlength="200"
        placeholder="Título do relatório"
        aria-label="Título do relatório"
        @input="marcarAlterado"
      />
      <div class="acoes">
        <span class="situacao" :class="relatorios.situacao">
          <CloudOff v-if="relatorios.situacao === 'erro'" />
          <Check v-else-if="relatorios.situacao === 'salvo'" />
          <LoaderCircle v-else class="girando" />
          {{ SITUACAO[relatorios.situacao] }}
        </span>
        <span class="espaco"></span>
        <button v-if="temResultados" class="botao pequeno" :disabled="relatorios.atualizando.size > 0" title="Roda de novo as consultas de todos os resultados" @click="atualizarTodos">
          <RefreshCw :class="{ girando: relatorios.atualizando.size > 0 }" /> Atualizar números
        </button>
        <button class="botao primario pequeno" :disabled="relatorios.exportando || !atual.blocos.length" @click="exportar">
          <LoaderCircle v-if="relatorios.exportando" class="girando" /><FileDown v-else /> Exportar PDF
        </button>
      </div>
    </header>

    <div v-if="!atual.blocos.length" class="vazio">
      <p class="vazio-titulo">Seu relatório começa aqui</p>
      <p>Faça perguntas em "Perguntar" e use <b>Adicionar ao relatório</b> em cada resposta, ou escreva direto com os botões abaixo.</p>
    </div>

    <section
      v-for="(b, i) in atual.blocos"
      :key="b.id"
      class="bloco"
      :class="[b.tipo, { arrastando: arrastando === i, destino: destino === i && arrastando !== i }]"
      @dragover.prevent="destino = i"
      @drop.prevent="soltar(i)"
    >
      <div class="ferramentas">
        <button
          class="alca"
          draggable="true"
          title="Arraste para mover"
          aria-label="Arrastar bloco"
          @dragstart="arrastando = i"
          @dragend="arrastando = destino = null"
        ><GripVertical /></button>
        <button :disabled="i === 0" title="Mover para cima" aria-label="Mover para cima" @click="moverBloco(i, i - 1)"><ArrowUp /></button>
        <button :disabled="i === atual.blocos.length - 1" title="Mover para baixo" aria-label="Mover para baixo" @click="moverBloco(i, i + 1)"><ArrowDown /></button>
        <button class="perigo" title="Remover bloco" aria-label="Remover bloco" @click="removerBloco(b.id)"><Trash2 /></button>
      </div>

      <textarea v-if="b.tipo === 'titulo'" v-model="b.texto" v-altura class="campo-titulo" rows="1" placeholder="Título da seção" @input="aoDigitar"></textarea>
      <TextoRico v-else-if="b.tipo === 'texto'" :doc="b.doc" :texto="b.texto" :autofoco="blocoNovo === b.id" @alterado="aplicarTexto(b, $event)" />

      <template v-else>
        <p class="pergunta">{{ b.pergunta }}</p>
        <TextoRico class="comentario" :doc="b.doc" :texto="b.texto" dica="Comente este resultado…" @alterado="aplicarTexto(b, $event)" />

        <div v-if="indicadores(b).length" class="numeros">
          <div v-for="ind in indicadores(b)" :key="ind.rotulo" class="numero">
            <small>{{ nomeLegivel(ind.rotulo) }}</small>
            <b>{{ typeof ind.valor === "number" ? formatarNumero(ind.valor) : formatarValor(ind.valor) }}</b>
          </div>
        </div>
        <template v-else>
          <div v-if="temGrafico(b)" class="alternador">
            <button :class="{ ativo: b.visao === 'grafico' }" @click="trocarVisao(b, 'grafico')"><BarChart3 /> Gráfico</button>
            <button :class="{ ativo: b.visao === 'tabela' }" @click="trocarVisao(b, 'tabela')"><Table2 /> Tabela</button>
          </div>
          <Grafico v-if="temGrafico(b) && b.visao === 'grafico'" :grafico="b.grafico" />
          <TabelaResultado v-else :colunas="b.colunas" :linhas="b.linhas" />
        </template>

        <div class="rodape">
          <span>Dados de {{ quando(b.dados_em) }}</span>
          <span v-if="b.truncado" class="selo ambar">resultado cortado no limite de linhas</span>
          <span class="espaco"></span>
          <button class="botao fantasma pequeno" :disabled="relatorios.atualizando.has(b.id)" @click="atualizarBloco(b.id)">
            <RefreshCw :class="{ girando: relatorios.atualizando.has(b.id) }" /> Atualizar
          </button>
        </div>
      </template>
    </section>

    <div class="adicionar">
      <button class="botao pequeno" @click="novoBloco('titulo')"><Heading2 /> Título</button>
      <button class="botao pequeno" @click="novoBloco('texto')"><Type /> Texto</button>
    </div>

    <details v-if="relatorios.versoes.length" class="versoes">
      <summary>Versões em PDF ({{ relatorios.versoes.length }})</summary>
      <a v-for="v in relatorios.versoes" :key="v.numero" class="versao" :href="urlDoPdf(atual.id, v.numero)">
        <Download />
        <span>Versão {{ v.numero }}</span>
        <span class="texto-suave">{{ quando(v.criado_em) }} · {{ tamanho(v.tamanho) }}</span>
      </a>
    </details>
  </div>
</template>

<style scoped>
.editor { display: flex; flex-direction: column; gap: 12px; }
.topo { display: flex; flex-direction: column; gap: 10px; margin-bottom: 6px; }
.titulo-relatorio {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--texto);
  font: inherit;
  font-size: 1.6rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  padding: 2px 0;
  border-bottom: 2px solid transparent;
}
.compacto .titulo-relatorio { font-size: 1.25rem; }
.titulo-relatorio:focus { outline: none; border-bottom-color: var(--borda-foco); }
.acoes { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.situacao { display: inline-flex; align-items: center; gap: 5px; font-size: 0.8rem; color: var(--suave); }
.situacao svg { width: 14px; height: 14px; }
.situacao.salvo svg { color: var(--verde); }
.situacao.erro { color: var(--vermelho); }

.vazio { padding: 28px 22px; border: 1.5px dashed var(--borda-forte); border-radius: var(--raio); color: var(--suave); text-align: center; }
.vazio-titulo { font-weight: 650; color: var(--texto); margin-bottom: 4px; }

.bloco {
  position: relative;
  padding: 12px 14px;
  border: 1px solid transparent;
  border-radius: var(--raio);
  transition: border-color 0.15s, background 0.15s, opacity 0.15s;
}
.bloco:hover, .bloco:focus-within { border-color: var(--borda); }
.bloco.resultado { background: var(--superficie); border-color: var(--borda); box-shadow: var(--sombra-sm); }
.bloco.arrastando { opacity: 0.45; }
.bloco.destino { border-color: var(--primaria); box-shadow: 0 -2px 0 var(--primaria); }

.ferramentas {
  position: absolute;
  top: 6px;
  right: 6px;
  z-index: 2;
  display: flex;
  gap: 1px;
  padding: 2px;
  border-radius: 9px;
  background: var(--superficie);
  border: 1px solid var(--borda);
  box-shadow: var(--sombra-sm);
  opacity: 0;
  transition: opacity 0.12s;
}
.bloco:hover .ferramentas, .bloco:focus-within .ferramentas { opacity: 1; }
@media (hover: none) { .ferramentas { opacity: 1; } }
.ferramentas button {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--suave);
  cursor: pointer;
}
.ferramentas button:hover:not(:disabled) { background: var(--superficie-2); color: var(--texto); }
.ferramentas button:focus-visible { outline: 2px solid var(--borda-foco); }
.ferramentas button:disabled { opacity: 0.35; cursor: default; }
.ferramentas button.perigo:hover { color: var(--vermelho); background: var(--vermelho-50); }
.ferramentas .alca { cursor: grab; }
.ferramentas svg { width: 15px; height: 15px; }

textarea {
  display: block;
  width: 100%;
  resize: none;
  overflow: hidden;
  border: none;
  background: transparent;
  color: var(--texto-2);
  font: inherit;
  line-height: 1.6;
  padding: 0;
}
textarea:focus { outline: none; }
textarea::placeholder { color: var(--muito-suave); }
.campo-titulo { font-size: 1.2rem; font-weight: 700; color: var(--texto); letter-spacing: -0.01em; }
.pergunta { font-weight: 650; color: var(--texto); margin-bottom: 4px; padding-right: 118px; }
.comentario { margin-bottom: 10px; }

.alternador {
  display: inline-flex;
  padding: 3px;
  margin-bottom: 10px;
  border-radius: 10px;
  background: var(--superficie-2);
  border: 1px solid var(--borda);
}
.alternador button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 11px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 550;
  color: var(--suave);
  cursor: pointer;
}
.alternador button svg { width: 14px; height: 14px; }
.alternador button.ativo { background: var(--superficie); color: var(--texto); box-shadow: var(--sombra-sm); }

.numeros { display: flex; flex-wrap: wrap; gap: 10px; }
.numero { padding: 10px 16px; border-left: 3px solid var(--primaria); background: var(--superficie-2); border-radius: 0 10px 10px 0; }
.numero small { display: block; color: var(--suave); font-size: 0.78rem; font-weight: 600; }
.numero b { font-size: 1.6rem; font-weight: 750; color: var(--texto); font-variant-numeric: tabular-nums; }

.rodape { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 8px; font-size: 0.8rem; color: var(--suave); }

.adicionar { display: flex; gap: 8px; margin-top: 2px; }

.versoes { margin-top: 10px; padding-top: 12px; border-top: 1px solid var(--borda); }
.versoes summary { cursor: pointer; font-weight: 600; font-size: 0.9rem; color: var(--texto-2); }
.versao { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 8px 6px; border-radius: 8px; color: var(--texto-2); font-size: 0.88rem; text-decoration: none; }
.versao:first-of-type { margin-top: 6px; }
.versao:hover { background: var(--superficie-2); }
.versao svg { width: 15px; height: 15px; color: var(--primaria); }
</style>
