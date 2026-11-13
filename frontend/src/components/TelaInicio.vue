<script setup>
// Início em bento: pergunta rápida, mascote, os dados anexados, o quanto do contexto já foi
// escrito, o último relatório e os primeiros passos. Todos os números vêm da API.
// Grade bento: React Bits Pro (blocos "Bento"); movimentos: transitions.dev (ver docs/interface-fontes.md).
import { computed, onMounted, ref, watch } from "vue";
import { ArrowRight, ArrowUp, Database, FileText } from "@lucide/vue";
import LogoDataTalk from "./LogoDataTalk.vue";
import NumeroTambor from "./NumeroTambor.vue";
import PrimeirosPassos from "./PrimeirosPassos.vue";
import { api } from "../api.js";
import { jornada } from "../jornada.js";
import { pedirPergunta } from "../pedido.js";
import { carregarLista, relatorios } from "../relatorios.js";
import { formatarNumero } from "../formatacao.js";

const props = defineProps({ versao: { type: Number, default: 0 } });
const emit = defineEmits(["ir-para"]);

const tabelas = ref(null);
const contexto = ref(null);
const pergunta = ref("");

const SUGESTOES = ["Qual closer vendeu mais este ano?", "Como evoluiu a receita mês a mês em 2026?", "Quantas vendas houve em março de 2026?"];

const hora = new Date().getHours();
const saudacao = hora < 12 ? "Bom dia!" : hora < 18 ? "Boa tarde!" : "Boa noite!";
const palavras = computed(() => `${saudacao} O que você quer saber hoje?`.split(" "));

async function carregar() {
  try {
    const [t, c] = await Promise.all([api.listarTabelas(), api.obterContexto()]);
    tabelas.value = t;
    contexto.value = c;
  } catch {
    tabelas.value = [];
  }
  carregarLista().catch(() => {});
}
onMounted(carregar);
watch(() => props.versao, carregar);

const totalLinhas = computed(() => (tabelas.value ?? []).reduce((s, t) => s + t.linhas, 0));

// quantos campos (descrição da tabela + cada coluna) já têm texto
const descricao = computed(() => {
  const salvo = contexto.value?.contexto?.tabelas ?? {};
  let feitos = 0;
  let total = 0;
  for (const t of tabelas.value ?? []) {
    const s = salvo[t.nome];
    total += 1 + t.colunas.length;
    if (s?.descricao?.trim()) feitos++;
    feitos += t.colunas.filter((c) => s?.colunas?.[c.nome]?.trim()).length;
  }
  return { feitos, total, pct: total ? feitos / total : 0 };
});
const regras = computed(() => contexto.value?.contexto?.regras?.length ?? 0);
const CIRCUNFERENCIA = 326.7;

const ultimo = computed(() => relatorios.lista[0] ?? null);
const dia = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" });

const passosVisiveis = computed(
  () => jornada.carregada && !(jornada.temTabelas && jornada.descritas === jornada.totalTabelas && jornada.perguntou),
);

function perguntar(texto) {
  const p = (texto ?? pergunta.value).trim();
  if (!p) return;
  pergunta.value = "";
  pedirPergunta(p);
  emit("ir-para", "conversa");
}
</script>

<template>
  <section class="inicio">
    <div class="bento">
      <!-- pergunta rápida -->
      <section class="bloco heroi revela" style="--i: 1">
        <h1>
          <span v-for="(p, i) in palavras" :key="i" class="palavra" :class="{ destaque: i >= palavras.length - 2 }" :style="{ '--i': i }">{{ p }} </span>
        </h1>
        <div class="feixe">
          <form class="compositor" @submit.prevent="perguntar()">
            <label for="pergunta-inicio" class="sr">Pergunta</label>
            <input id="pergunta-inicio" v-model="pergunta" autocomplete="off" :disabled="tabelas?.length === 0" />
            <!-- exemplos que se revezam no lugar do placeholder -->
            <span v-if="!pergunta" class="trocas" aria-hidden="true">
              <span v-for="(s, i) in SUGESTOES" :key="s" class="troca" :style="{ animationDelay: `${i * 3}s` }">{{ s }}</span>
            </span>
            <button type="submit" class="enviar" aria-label="Perguntar" :disabled="!pergunta.trim()"><ArrowUp /></button>
          </form>
        </div>
        <div class="sugestoes">
          <button v-for="(s, i) in SUGESTOES" :key="s" class="sugestao" :style="{ '--i': i }" :disabled="tabelas?.length === 0" @click="perguntar(s)">
            {{ s }} <ArrowRight class="ir" />
          </button>
        </div>
      </section>

      <!-- mascote -->
      <section class="bloco mascote vivo revela" style="--i: 2">
        <div class="arco" aria-hidden="true"></div>
        <div class="recorte"><LogoDataTalk fundo="escuro" class="simbolo" /></div>
        <div class="legenda">
          <strong>Fala com seus dados.</strong>
          <span>Passe o mouse para ele pular</span>
        </div>
      </section>

      <!-- seus dados -->
      <section class="bloco dados vivo revela" style="--i: 3">
        <div class="linha-topo">
          <h2>Seus dados</h2>
          <button class="link" @click="$emit('ir-para', 'dados')">Gerenciar</button>
        </div>
        <template v-if="tabelas?.length">
          <div class="fichas">
            <div v-for="t in tabelas" :key="t.nome" class="ficha">
              <strong>{{ t.nome }}</strong>
              <span>{{ formatarNumero(t.linhas) }} linhas</span>
            </div>
          </div>
        </template>
        <div v-else-if="tabelas" class="vazio">
          <p>Nenhuma tabela ainda. Anexe os CSVs da empresa para começar.</p>
          <button class="botao primario" @click="$emit('ir-para', 'dados')"><Database /> Anexar dados</button>
        </div>
        <div v-else class="fichas" aria-hidden="true">
          <div v-for="i in 3" :key="i" class="ficha"><span class="esqueleto" style="height: 14px; width: 70%"></span><span class="esqueleto" style="height: 10px; width: 45%"></span></div>
        </div>
      </section>

      <!-- linhas -->
      <section class="bloco escuro vivo revela" style="--i: 4">
        <span class="rotulo">Linhas para analisar</span>
        <NumeroTambor v-if="tabelas" class="grande menta" :valor="totalLinhas" :atraso="500" />
        <span class="nota">em {{ tabelas?.length ?? 0 }} tabela{{ tabelas?.length === 1 ? "" : "s" }}</span>
      </section>

      <!-- contexto -->
      <section class="bloco contexto vivo revela" style="--i: 5">
        <span class="rotulo">Sobre os dados</span>
        <div class="anel-linha">
          <svg width="74" height="74" viewBox="0 0 120 120" role="img" :aria-label="`${Math.round(descricao.pct * 100)}% dos campos descritos`">
            <circle cx="60" cy="60" r="52" fill="none" stroke="var(--trilho)" stroke-width="12" />
            <circle class="anel" cx="60" cy="60" r="52" fill="none" stroke="var(--menta)" stroke-width="12" stroke-linecap="round"
              :stroke-dasharray="CIRCUNFERENCIA" :style="{ strokeDashoffset: CIRCUNFERENCIA * (1 - descricao.pct) }" transform="rotate(-90 60 60)" />
            <text x="60" y="69" text-anchor="middle" class="anel-texto">{{ Math.round(descricao.pct * 100) }}%</text>
          </svg>
          <div class="anel-legenda">
            <span>{{ descricao.feitos }} de {{ descricao.total }} campos</span>
            <span>{{ regras }} regra{{ regras === 1 ? "" : "s" }}</span>
          </div>
        </div>
        <button class="link" @click="$emit('ir-para', 'contexto')">Descrever →</button>
      </section>

      <!-- último relatório -->
      <section class="bloco relatorio vivo revela" :class="{ largo: !passosVisiveis }" style="--i: 6">
        <div class="folha" aria-hidden="true">
          <span class="f-titulo"></span><span class="f-linha"></span><span class="f-linha curta"></span>
          <span class="f-barras"><i style="height: 40%"></i><i style="height: 70%"></i><i class="pico" style="height: 100%"></i></span>
        </div>
        <div class="rel-texto">
          <span class="rotulo">Último relatório</span>
          <strong>{{ ultimo?.titulo ?? "Nenhum relatório ainda" }}</strong>
          <span class="nota">{{ ultimo ? `${dia.format(new Date(ultimo.atualizado_em))} · ${ultimo.quantidade_versoes} PDF${ultimo.quantidade_versoes === 1 ? "" : "s"}` : "Junte respostas num documento e exporte em PDF." }}</span>
        </div>
        <button class="botao" @click="$emit('ir-para', 'relatorios')"><FileText /> {{ ultimo ? "Abrir" : "Criar" }}</button>
      </section>

      <!-- primeiros passos -->
      <section v-if="passosVisiveis" class="bloco vivo revela passos-bloco" style="--i: 7">
        <PrimeirosPassos @ir-para="$emit('ir-para', $event)" />
      </section>
    </div>
  </section>
</template>

<style scoped>
.inicio { max-width: 1280px; margin: 0 auto; padding: 28px 32px 64px; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.bento { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.bloco { border-radius: 26px; background: var(--superficie); border: 1px solid var(--borda); padding: 22px 24px; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
h2 { font-size: 0.95rem; font-weight: 650; color: var(--texto-2); }
.rotulo { font-size: 0.86rem; color: var(--suave); }
.nota { font-size: 0.8rem; color: var(--suave); }
.link { align-self: flex-start; padding: 0; border: none; background: none; color: var(--primaria); font: inherit; font-size: 0.88rem; font-weight: 600; cursor: pointer; }
.linha-topo { display: flex; align-items: center; justify-content: space-between; }

/* ---------- herói ---------- */
.heroi { grid-column: span 3; padding: 30px 32px 26px; gap: 18px; }
h1 { font-size: 2.6rem; line-height: 1.1; letter-spacing: -0.035em; font-weight: 750; }
.palavra { display: inline-block; white-space: pre; animation: palavra 0.75s cubic-bezier(0.22, 1, 0.36, 1) backwards; animation-delay: calc(var(--i) * 70ms + 300ms); }
.palavra.destaque { color: var(--primaria); }
@keyframes palavra { from { opacity: 0; transform: translateY(45%); filter: blur(8px); } }

.compositor { position: relative; display: flex; align-items: center; gap: 12px; padding: 9px 9px 9px 22px; border-radius: 20.5px; background: var(--superficie); }
.compositor input { flex: 1; min-width: 0; height: 46px; border: none; outline: none; background: transparent; font: inherit; font-size: 1.05rem; color: var(--texto); }
.trocas { position: absolute; left: 22px; top: 0; bottom: 0; right: 70px; pointer-events: none; overflow: hidden; }
.troca { position: absolute; left: 0; top: 50%; margin-top: -12px; line-height: 24px; font-size: 1.05rem; color: var(--muito-suave); white-space: nowrap; opacity: 0; animation: troca 9s infinite; }
@keyframes troca {
  0% { opacity: 0; transform: translateY(10px); filter: blur(5px); }
  5%, 30% { opacity: 1; transform: none; filter: none; }
  35%, 100% { opacity: 0; transform: translateY(-10px); filter: blur(5px); }
}
.enviar { width: 50px; height: 50px; flex-shrink: 0; border-radius: 15px; border: none; background: var(--menta); color: var(--azul-noite); display: grid; place-items: center; cursor: pointer; box-shadow: var(--sombra-menta); transition: transform 0.2s, opacity 0.2s; }
.enviar svg { width: 20px; height: 20px; transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1); }
.enviar:hover:not(:disabled) { transform: translateY(-1px) scale(1.04); }
.enviar:hover:not(:disabled) svg { transform: translateY(-3px); }
.enviar:disabled { opacity: 0.45; cursor: not-allowed; box-shadow: none; }

.sugestoes { display: flex; flex-wrap: wrap; gap: 10px; }
.sugestao {
  display: flex; align-items: center; gap: 8px; height: 40px; padding: 0 14px; border-radius: 999px;
  border: 1px solid var(--borda); background: var(--chip); color: var(--texto-2); font: inherit; font-size: 0.9rem; cursor: pointer;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.3s;
  animation: revela 0.6s cubic-bezier(0.22, 1, 0.36, 1) backwards; animation-delay: calc(var(--i) * 70ms + 700ms);
}
.sugestao:hover:not(:disabled) { transform: translateY(-2px); border-color: var(--primaria); }
.sugestao:disabled { opacity: 0.5; cursor: not-allowed; }
.sugestao .ir { width: 14px; height: 14px; opacity: 0; transform: translateX(-6px); transition: opacity 0.25s, transform 0.35s cubic-bezier(0.22, 1, 0.36, 1); }
.sugestao:hover .ir { opacity: 1; transform: none; }

/* ---------- mascote ---------- */
.mascote { background: var(--marca); border-color: transparent; color: #fff; justify-content: space-between; min-height: 250px; }
.arco { position: absolute; width: 300px; height: 300px; right: -150px; bottom: -150px; border-radius: 50%; border: 40px solid rgba(62, 233, 176, 0.14); }
.recorte { position: relative; width: 100%; max-width: 240px; aspect-ratio: 1.02; overflow: hidden; }
.simbolo { width: 205%; margin-top: 4%; }
/* só o cachorro e o balão: o texto já está na barra do topo */
.simbolo :deep(.texto), .simbolo :deep(.t-brilho) { display: none; }
.legenda { position: relative; display: flex; flex-direction: column; gap: 2px; }
.legenda strong { font-size: 1.15rem; }
.legenda span { font-size: 0.82rem; color: var(--caramelo); }

/* ---------- seus dados ---------- */
.dados { grid-column: span 2; background: var(--menta-50); border-color: var(--menta-borda); }
.fichas { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; }
.ficha { display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; border-radius: 16px; background: var(--chip); border: 1px solid var(--borda); transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1); }
.ficha strong { font-size: 0.92rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ficha span { font-size: 0.78rem; color: var(--suave); }
/* as fichas se afastam da que está sob o mouse */
.fichas:hover .ficha { transform: translateY(2px) scale(0.98); }
.fichas .ficha:hover { transform: translateY(-6px) scale(1.03); }
.vazio { display: flex; flex-direction: column; align-items: flex-start; gap: 12px; color: var(--texto-2); }

/* ---------- números ---------- */
.escuro { background: var(--bloco); border-color: transparent; }
.escuro .rotulo { color: #c5d0e5; }
.escuro .nota { color: #9aabc8; }
.grande { font-size: 3.2rem; font-weight: 750; letter-spacing: -0.03em; }
.menta { color: var(--menta); }

.anel-linha { display: flex; align-items: center; gap: 14px; }
.anel { transition: stroke-dashoffset 0.9s cubic-bezier(0.22, 1, 0.36, 1); animation: anel 1.4s cubic-bezier(0.22, 1, 0.36, 1) 0.4s backwards; }
@keyframes anel { from { stroke-dashoffset: 326.7; } }
.anel-texto { font-size: 28px; font-weight: 750; fill: var(--texto); }
.anel-legenda { display: flex; flex-direction: column; gap: 2px; font-size: 0.85rem; color: var(--texto-2); }

/* ---------- relatório ---------- */
.relatorio { grid-column: span 2; flex-direction: row; align-items: center; gap: 18px; }
.relatorio.largo { grid-column: span 4; }
.rel-texto { flex: 1; display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.rel-texto strong { font-size: 1.05rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.folha {
  flex-shrink: 0; width: 70px; height: 88px; padding: 10px; box-sizing: border-box; border-radius: 10px;
  background: var(--chip); border: 1px solid var(--borda); display: flex; flex-direction: column; gap: 5px;
  transition: transform 0.6s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.6s;
}
/* inclinação 3D ao passar o mouse */
.relatorio:hover .folha { transform: perspective(700px) rotateY(-16deg) rotateX(7deg) translateZ(14px); box-shadow: 14px 18px 30px -16px rgba(15, 23, 42, 0.45); }
.f-titulo { height: 6px; width: 70%; border-radius: 3px; background: var(--texto); }
.f-linha { height: 4px; border-radius: 2px; background: var(--borda-forte); }
.f-linha.curta { width: 80%; }
.f-barras { flex: 1; display: flex; align-items: flex-end; gap: 3px; }
.f-barras i { flex: 1; border-radius: 2px; background: var(--barra-grafico); }
.f-barras i.pico { background: var(--primaria); }

.passos-bloco { grid-column: span 2; }

@media (max-width: 960px) {
  .bento { grid-template-columns: repeat(1, minmax(0, 1fr)); }
  .bento > * { grid-column: auto !important; }
  h1 { font-size: 2rem; }
}
@media (max-width: 720px) { .inicio { padding: 20px 16px 56px; } }
</style>
