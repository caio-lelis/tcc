<script setup>
// Tela de descrições (RF02) e regras de negócio (RF03), com as pendências do RF10.
// É o instrumento que produz o contexto C1 (descrições) e C2 (regras) do experimento.
import { computed, onMounted, reactive, ref, watch } from "vue";
import {
  Archive, BookOpenText, Calculator, ChevronDown, CircleCheck, FileSpreadsheet, LoaderCircle, Plus, Save, Scale, Trash2,
} from "@lucide/vue";
import { api } from "../api.js";
import { avisar } from "../avisos.js";
import { formatarValor } from "../formatacao.js";

const props = defineProps({
  versao: { type: Number, default: 0 },
  avancado: { type: Boolean, default: false },
});
defineEmits(["ir-para"]);

const tabelas = ref([]);
const completo = ref(null);
const rascunhos = reactive({}); // tabela -> { descricao, colunas }
const salvos = reactive({}); // tabela -> JSON do que está salvo (para saber o que mudou)
const regras = ref([]);
const regrasSalvas = reactive({}); // id -> JSON salvo
const novaRegra = reactive({ texto: "", tipo: "regra" });
const salvando = ref("");
const abertas = ref(new Set());

function copiarRegras(lista) {
  regras.value = lista.map((r) => ({ ...r }));
  for (const k of Object.keys(regrasSalvas)) delete regrasSalvas[k];
  for (const r of lista) regrasSalvas[r.id] = JSON.stringify([r.texto, r.tipo]);
}

async function carregar() {
  try {
    const [t, c] = await Promise.all([api.listarTabelas(), api.obterContexto()]);
    tabelas.value = t;
    completo.value = c;
    for (const tabela of t) {
      const salvo = c.contexto.tabelas[tabela.nome] ?? { descricao: "", colunas: {} };
      rascunhos[tabela.nome] = {
        descricao: salvo.descricao,
        colunas: Object.fromEntries(tabela.colunas.map((col) => [col.nome, salvo.colunas[col.nome] ?? ""])),
      };
      salvos[tabela.nome] = JSON.stringify(rascunhos[tabela.nome]);
    }
    copiarRegras(c.contexto.regras);
    if (abertas.value.size === 0 && t.length) abertas.value = new Set([t[0].nome]);
  } catch (e) {
    avisar(e.message, "erro");
  }
}
onMounted(carregar);
watch(() => props.versao, carregar);

// ---------------------------------------------------------------- progresso
function contagem(nome) {
  const r = rascunhos[nome];
  if (!r) return { feitas: 0, total: 0 };
  const colunas = Object.values(r.colunas);
  return {
    feitas: colunas.filter((v) => v.trim()).length + (r.descricao.trim() ? 1 : 0),
    total: colunas.length + 1,
  };
}
const progresso = computed(() => {
  let feitas = 0;
  let total = 0;
  for (const t of tabelas.value) {
    const c = contagem(t.nome);
    feitas += c.feitas;
    total += c.total;
  }
  return total ? Math.round((feitas / total) * 100) : 0;
});
const alterada = (nome) => rascunhos[nome] && JSON.stringify(rascunhos[nome]) !== salvos[nome];
const regraAlterada = (r) => JSON.stringify([r.texto, r.tipo]) !== regrasSalvas[r.id];
const orfas = computed(() => completo.value?.pendencias ?? { colunas_orfas: {}, tabelas_orfas: [] });

function alternar(nome) {
  const s = new Set(abertas.value);
  s.has(nome) ? s.delete(nome) : s.add(nome);
  abertas.value = s;
}

// ---------------------------------------------------------------- ações
async function salvarTabela(nome) {
  salvando.value = nome;
  try {
    await api.salvarDescricao(nome, rascunhos[nome]);
    salvos[nome] = JSON.stringify(rascunhos[nome]);
    completo.value = await api.obterContexto(); // atualiza pendências sem apagar outros rascunhos
    avisar(`Descrições de "${nome}" salvas.`);
  } catch (e) {
    avisar(e.message, "erro");
  } finally {
    salvando.value = "";
  }
}

async function recarregarRegras() {
  completo.value = await api.obterContexto();
  copiarRegras(completo.value.contexto.regras);
}

async function adicionarRegra() {
  try {
    await api.adicionarRegra({ texto: novaRegra.texto, tipo: novaRegra.tipo });
    novaRegra.texto = "";
    novaRegra.tipo = "regra";
    await recarregarRegras();
    avisar("Regra adicionada.");
  } catch (e) {
    avisar(e.message, "erro");
  }
}

async function salvarRegra(regra) {
  try {
    await api.atualizarRegra(regra.id, { texto: regra.texto, tipo: regra.tipo, tabelas: regra.tabelas });
    regrasSalvas[regra.id] = JSON.stringify([regra.texto, regra.tipo]);
    completo.value = await api.obterContexto();
    avisar("Regra salva.");
  } catch (e) {
    avisar(e.message, "erro");
  }
}

async function removerRegra(regra) {
  if (!confirm("Remover esta regra?")) return;
  try {
    await api.removerRegra(regra.id);
    await recarregarRegras();
    avisar("Regra removida.");
  } catch (e) {
    avisar(e.message, "erro");
  }
}
</script>

<template>
  <section class="pagina">
    <header class="cabecalho">
      <h1>Sobre os dados</h1>
      <p>
        Explique os seus dados como explicaria a alguém que acabou de chegar na empresa: o que cada tabela guarda, o que
        significam os códigos e como vocês calculam cada número. Quanto mais claro, melhores as respostas.
      </p>
    </header>

    <!-- progresso -->
    <div v-if="tabelas.length" class="cartao preenchido progresso">
      <div class="progresso-topo">
        <div>
          <div class="progresso-titulo">
            <CircleCheck v-if="progresso === 100" class="ok" />
            {{ progresso === 100 ? "Tudo descrito" : "Descrição dos dados" }}
          </div>
          <div class="texto-suave pequeno">{{ regras.length }} regra{{ regras.length === 1 ? "" : "s" }} cadastrada{{ regras.length === 1 ? "" : "s" }}</div>
        </div>
        <span class="espaco"></span>
        <div class="porcentagem">{{ progresso }}%</div>
      </div>
      <div class="barra"><div class="preenchimento" :style="{ width: progresso + '%' }"></div></div>
      <div v-if="avancado && completo" class="texto-suave pequeno hash">hash do contexto: <code>{{ completo.hash }}</code></div>
    </div>

    <!-- regras de negócio (C2) -->
    <div class="secao-titulo">
      <Scale class="icone-secao" />
      <h2>Regras do negócio</h2>
      <span class="contagem">{{ regras.length }}</span>
    </div>
    <p class="texto-suave pequeno explicacao">
      Como vocês contam as coisas. Ex.: <em>"Venda é um contrato assinado; ela pertence ao mês da assinatura."</em>
    </p>

    <div class="regras">
      <div v-for="(r, i) in regras" :key="r.id" class="regra cartao">
        <div class="numero">{{ i + 1 }}</div>
        <div class="regra-corpo">
          <div class="tipo-alternador">
            <button :class="{ ativo: r.tipo === 'regra' }" @click="r.tipo = 'regra'"><Scale /> Regra</button>
            <button :class="{ ativo: r.tipo === 'metrica' }" @click="r.tipo = 'metrica'"><Calculator /> Métrica</button>
          </div>
          <textarea v-model="r.texto" class="campo" rows="2"></textarea>
        </div>
        <div class="regra-acoes">
          <button v-if="regraAlterada(r)" class="botao primario pequeno" @click="salvarRegra(r)"><Save /> Salvar</button>
          <button class="botao fantasma icone pequeno perigo" title="Remover regra" @click="removerRegra(r)"><Trash2 /></button>
        </div>
      </div>

      <div class="regra cartao nova">
        <div class="numero mais"><Plus /></div>
        <div class="regra-corpo">
          <div class="tipo-alternador">
            <button :class="{ ativo: novaRegra.tipo === 'regra' }" @click="novaRegra.tipo = 'regra'"><Scale /> Regra</button>
            <button :class="{ ativo: novaRegra.tipo === 'metrica' }" @click="novaRegra.tipo = 'metrica'"><Calculator /> Métrica</button>
          </div>
          <textarea v-model="novaRegra.texto" class="campo" rows="2" placeholder="Escreva uma nova regra ou definição de métrica…"></textarea>
        </div>
        <div class="regra-acoes">
          <button class="botao primario pequeno" :disabled="!novaRegra.texto.trim()" @click="adicionarRegra"><Plus /> Adicionar</button>
        </div>
      </div>
    </div>

    <!-- descrições (C1) -->
    <div class="secao-titulo">
      <BookOpenText class="icone-secao" />
      <h2>Tabelas e colunas</h2>
      <span class="contagem">{{ tabelas.length }}</span>
    </div>

    <div v-if="!tabelas.length" class="cartao preenchido vazio">
      <p class="texto-suave">Anexe tabelas para poder descrevê-las.</p>
      <button class="botao primario" @click="$emit('ir-para', 'dados')">Ir para Meus dados</button>
    </div>

    <article v-for="t in tabelas" :key="t.nome" class="cartao sanfona" :class="{ aberta: abertas.has(t.nome) }">
      <button class="sanfona-topo" @click="alternar(t.nome)">
        <div class="tabela-icone"><FileSpreadsheet /></div>
        <div class="sanfona-titulo">
          <h3>{{ t.nome }}</h3>
          <div class="texto-suave pequeno">{{ rascunhos[t.nome]?.descricao || "Sem descrição" }}</div>
        </div>
        <span class="espaco"></span>
        <span v-if="alterada(t.nome)" class="selo ambar">não salvo</span>
        <span
          class="selo"
          :class="contagem(t.nome).feitas === contagem(t.nome).total ? 'verde' : ''"
        >{{ contagem(t.nome).feitas }}/{{ contagem(t.nome).total }} descritos</span>
        <ChevronDown class="seta" />
      </button>

      <div v-if="abertas.has(t.nome) && rascunhos[t.nome]" class="sanfona-corpo">
        <label class="rotulo">O que esta tabela guarda?</label>
        <textarea
          v-model="rascunhos[t.nome].descricao"
          class="campo"
          rows="2"
          placeholder="Ex.: um registro por contrato enviado a um cliente."
        ></textarea>

        <label class="rotulo">O que significa cada coluna?</label>
        <div class="colunas">
          <div v-for="c in t.colunas" :key="c.nome" class="coluna" :class="{ pendente: !rascunhos[t.nome].colunas[c.nome].trim() }">
            <div class="coluna-nome">
              <code>{{ c.nome }}</code>
              <span class="tipo">{{ c.tipo.toLowerCase() }}</span>
            </div>
            <div class="exemplo" :title="String(t.amostra[0]?.[c.nome] ?? '')">ex.: {{ formatarValor(t.amostra[0]?.[c.nome]) }}</div>
            <input v-model="rascunhos[t.nome].colunas[c.nome]" class="campo" placeholder="O que significa?" />
          </div>
        </div>

        <div v-if="orfas.colunas_orfas[t.nome]" class="guardadas texto-suave pequeno">
          <Archive /> Descrições guardadas de colunas que não estão mais no arquivo:
          {{ orfas.colunas_orfas[t.nome].join(", ") }}
        </div>

        <div class="sanfona-rodape">
          <span v-if="alterada(t.nome)" class="texto-suave pequeno">Você tem alterações não salvas.</span>
          <span class="espaco"></span>
          <button class="botao primario" :disabled="!alterada(t.nome) || salvando === t.nome" @click="salvarTabela(t.nome)">
            <LoaderCircle v-if="salvando === t.nome" class="girando" /><Save v-else />
            Salvar descrições
          </button>
        </div>
      </div>
    </article>

    <div v-if="orfas.tabelas_orfas.length" class="guardadas texto-suave pequeno">
      <Archive /> Descrições guardadas de tabelas removidas: {{ orfas.tabelas_orfas.join(", ") }}. Elas voltam a valer
      se a tabela for anexada de novo.
    </div>
  </section>
</template>

<style scoped>
.progresso-topo { display: flex; align-items: center; gap: 12px; }
.progresso-titulo { display: flex; align-items: center; gap: 7px; font-weight: 650; }
.progresso-titulo .ok { width: 18px; height: 18px; color: var(--verde); }
.porcentagem { font-size: 1.6rem; font-weight: 750; letter-spacing: -0.02em; color: var(--primaria); font-variant-numeric: tabular-nums; }
.barra { margin-top: 12px; height: 8px; border-radius: 999px; background: var(--superficie-2); border: 1px solid var(--borda); overflow: hidden; }
.preenchimento { height: 100%; border-radius: 999px; background: var(--degrade-progresso); transition: width 0.4s ease; }
.hash { margin-top: 10px; }
.hash code { font-size: 0.85em; background: var(--superficie-2); padding: 2px 6px; border-radius: 5px; }

.icone-secao { width: 19px; height: 19px; color: var(--primaria); }
.explicacao { margin: -6px 0 14px; }

.regras { display: flex; flex-direction: column; gap: 10px; }
.regra { display: flex; gap: 14px; align-items: flex-start; padding: 14px 16px; }
.regra.nova { border-style: dashed; box-shadow: none; background: var(--superficie-2); }
.numero {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--primaria-50);
  color: var(--primaria);
  font-weight: 700;
  font-size: 0.85rem;
  margin-top: 2px;
}
.numero.mais { background: var(--superficie); border: 1px solid var(--borda); color: var(--suave); }
.numero.mais svg { width: 15px; height: 15px; }
.regra-corpo { flex: 1; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.regra-acoes { display: flex; flex-direction: column; gap: 6px; align-items: flex-end; min-width: 92px; }

.tipo-alternador { display: inline-flex; gap: 4px; }
.tipo-alternador button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--borda);
  background: var(--superficie);
  font: inherit;
  font-size: 0.78rem;
  font-weight: 550;
  color: var(--suave);
  cursor: pointer;
}
.tipo-alternador button svg { width: 13px; height: 13px; }
.tipo-alternador button.ativo { background: var(--primaria-50); border-color: var(--primaria-100); color: var(--primaria); }

.vazio { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 14px; }

.sanfona { margin-bottom: 12px; overflow: hidden; transition: box-shadow 0.2s; }
.sanfona.aberta { box-shadow: var(--sombra); }
.sanfona-topo {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border: none;
  background: none;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.sanfona-topo:hover { background: var(--linha-hover); }
.sanfona-titulo { min-width: 0; }
.sanfona-titulo h3 { font-size: 1rem; }
.sanfona-titulo .pequeno { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 460px; }
.tabela-icone {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: var(--verde-50);
  color: var(--verde);
}
.tabela-icone svg { width: 19px; height: 19px; }
.seta { width: 18px; height: 18px; color: var(--muito-suave); transition: transform 0.2s; }
.aberta .seta { transform: rotate(180deg); }

.sanfona-corpo { padding: 4px 20px 18px; border-top: 1px solid var(--borda); }
.rotulo { display: block; font-weight: 600; font-size: 0.88rem; margin: 16px 0 8px; color: var(--texto-2); }

.colunas { display: flex; flex-direction: column; border: 1px solid var(--borda); border-radius: var(--raio); overflow: hidden; }
.coluna {
  display: grid;
  grid-template-columns: 200px 150px 1fr;
  gap: 14px;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--linha-fina);
}
.coluna:last-child { border-bottom: none; }
.coluna.pendente { background: var(--ambar-suave); }
.coluna.pendente .campo { border-color: var(--ambar-borda); }
.coluna-nome { display: flex; flex-direction: column; min-width: 0; }
.coluna-nome code { font-size: 0.85rem; font-weight: 600; color: var(--texto); overflow: hidden; text-overflow: ellipsis; }
.tipo { font-size: 0.74rem; color: var(--muito-suave); }
.exemplo { font-size: 0.82rem; color: var(--suave); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.coluna .campo { padding: 7px 10px; font-size: 0.9rem; }

.sanfona-rodape { display: flex; align-items: center; gap: 10px; margin-top: 16px; }
.guardadas { display: flex; align-items: center; gap: 7px; margin-top: 12px; }
.guardadas svg { width: 15px; height: 15px; flex-shrink: 0; }

@media (max-width: 760px) {
  .coluna { grid-template-columns: 1fr; gap: 6px; }
  .regra { flex-wrap: wrap; }
}
</style>
