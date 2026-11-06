<script setup>
// Tela de descrições (RF02) e regras de negócio (RF03), com as pendências do RF10.
import { computed, onMounted, reactive, ref, watch } from "vue";
import { api } from "../api.js";

const props = defineProps({
  versao: { type: Number, default: 0 },
  avancado: { type: Boolean, default: false },
});

const tabelas = ref([]);
const completo = ref(null);
const rascunhos = reactive({}); // tabela -> { descricao, colunas: {} }
const regras = ref([]);
const novaRegra = reactive({ texto: "", tipo: "regra" });
const salvando = ref("");
const mensagem = ref("");
const erro = ref("");

async function carregar() {
  erro.value = "";
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
    }
    regras.value = c.contexto.regras.map((r) => ({ ...r }));
  } catch (e) {
    erro.value = e.message;
  }
}
onMounted(carregar);
watch(() => props.versao, carregar);

const pendencias = computed(() => completo.value?.pendencias);
const totalPendente = computed(() => {
  const p = pendencias.value;
  if (!p) return 0;
  return p.tabelas_sem_descricao.length + Object.values(p.colunas_sem_descricao).reduce((s, l) => s + l.length, 0);
});
const semDescricao = (tabela, coluna) => !rascunhos[tabela]?.colunas[coluna]?.trim();

// Atualiza só pendências e hash, sem apagar o que está sendo escrito nas outras tabelas.
async function atualizarPendencias() {
  completo.value = await api.obterContexto();
}

async function recarregarRegras() {
  completo.value = await api.obterContexto();
  regras.value = completo.value.contexto.regras.map((r) => ({ ...r }));
}

function avisar(texto) {
  mensagem.value = texto;
  setTimeout(() => (mensagem.value = ""), 2500);
}

async function salvarTabela(nome) {
  salvando.value = nome;
  erro.value = "";
  try {
    await api.salvarDescricao(nome, rascunhos[nome]);
    avisar(`Descrição de "${nome}" salva.`);
    await atualizarPendencias();
  } catch (e) {
    erro.value = e.message;
  } finally {
    salvando.value = "";
  }
}

async function adicionarRegra() {
  erro.value = "";
  try {
    await api.adicionarRegra({ texto: novaRegra.texto, tipo: novaRegra.tipo });
    novaRegra.texto = "";
    novaRegra.tipo = "regra";
    avisar("Regra adicionada.");
    await recarregarRegras();
  } catch (e) {
    erro.value = e.message;
  }
}

async function salvarRegra(regra) {
  erro.value = "";
  try {
    await api.atualizarRegra(regra.id, { texto: regra.texto, tipo: regra.tipo, tabelas: regra.tabelas });
    avisar("Regra salva.");
    await atualizarPendencias();
  } catch (e) {
    erro.value = e.message;
  }
}

async function removerRegra(regra) {
  if (!confirm("Remover esta regra?")) return;
  try {
    await api.removerRegra(regra.id);
    await recarregarRegras();
  } catch (e) {
    erro.value = e.message;
  }
}
</script>

<template>
  <section>
    <div class="cartao">
      <h3>Sobre os dados</h3>
      <p class="suave">
        Explique os seus dados como explicaria a alguém que acabou de chegar na empresa: o que cada tabela
        guarda, o que significam os códigos e como vocês calculam cada número. Quanto mais claro, melhores as
        respostas.
      </p>
      <div class="linha">
        <span v-if="totalPendente" class="selo alerta">{{ totalPendente }} item(ns) sem descrição</span>
        <span v-else-if="tabelas.length" class="selo ok">tudo descrito</span>
        <span v-if="avancado && completo" class="suave">hash do contexto: {{ completo.hash }}</span>
      </div>
      <p v-if="mensagem" class="ok-msg">{{ mensagem }}</p>
      <p v-if="erro" class="erro">{{ erro }}</p>
    </div>

    <!-- Regras de negócio (C2) -->
    <div class="cartao">
      <h3>Regras do negócio</h3>
      <p class="suave">
        Como vocês contam as coisas. Ex.: "Venda é um contrato assinado; ela pertence ao mês da assinatura."
      </p>
      <div v-for="r in regras" :key="r.id" class="regra">
        <select v-model="r.tipo" class="tipo-regra">
          <option value="regra">Regra</option>
          <option value="metrica">Métrica</option>
        </select>
        <textarea v-model="r.texto" rows="2"></textarea>
        <div class="acoes">
          <button @click="salvarRegra(r)">Salvar</button>
          <button class="discreto perigo" @click="removerRegra(r)">Remover</button>
        </div>
      </div>
      <div class="regra nova">
        <select v-model="novaRegra.tipo" class="tipo-regra">
          <option value="regra">Regra</option>
          <option value="metrica">Métrica</option>
        </select>
        <textarea v-model="novaRegra.texto" rows="2" placeholder="Escreva uma nova regra ou definição de métrica…"></textarea>
        <div class="acoes">
          <button class="primario" :disabled="!novaRegra.texto.trim()" @click="adicionarRegra">Adicionar</button>
        </div>
      </div>
    </div>

    <!-- Descrições de tabelas e colunas (C1) -->
    <p v-if="!tabelas.length" class="suave">Anexe tabelas em "Meus dados" para descrevê-las.</p>

    <div v-for="t in tabelas" :key="t.nome" class="cartao">
      <div class="linha">
        <h3>{{ t.nome }}</h3>
        <span v-if="pendencias?.colunas_sem_descricao[t.nome]" class="selo alerta">
          {{ pendencias.colunas_sem_descricao[t.nome].length }} coluna(s) sem descrição
        </span>
        <span v-if="pendencias?.colunas_orfas[t.nome]" class="selo" title="Descrições guardadas de colunas que não existem mais no arquivo">
          descrições guardadas: {{ pendencias.colunas_orfas[t.nome].join(", ") }}
        </span>
      </div>
      <template v-if="rascunhos[t.nome]">
        <label class="rotulo">O que esta tabela guarda?</label>
        <textarea v-model="rascunhos[t.nome].descricao" rows="2" placeholder="Ex.: um registro por contrato enviado a um cliente."></textarea>

        <table class="dados colunas">
          <thead><tr><th>Coluna</th><th>Exemplo</th><th>O que significa</th></tr></thead>
          <tbody>
            <tr v-for="c in t.colunas" :key="c.nome" :class="{ pendente: semDescricao(t.nome, c.nome) }">
              <td><strong>{{ c.nome }}</strong><div class="suave">{{ c.tipo }}</div></td>
              <td class="exemplo">{{ t.amostra[0]?.[c.nome] ?? "—" }}</td>
              <td><input v-model="rascunhos[t.nome].colunas[c.nome]" placeholder="sem descrição" /></td>
            </tr>
          </tbody>
        </table>
        <div class="linha fim">
          <span class="espaco"></span>
          <button class="primario" :disabled="salvando === t.nome" @click="salvarTabela(t.nome)">
            {{ salvando === t.nome ? "Salvando…" : "Salvar descrições" }}
          </button>
        </div>
      </template>
    </div>

    <div v-if="pendencias?.tabelas_orfas.length" class="cartao suave">
      Descrições guardadas de tabelas removidas: {{ pendencias.tabelas_orfas.join(", ") }}.
      Elas voltam a valer se a tabela for anexada de novo.
    </div>
  </section>
</template>

<style scoped>
.rotulo { display: block; font-weight: 600; margin: 8px 0 4px; }
.colunas { margin-top: 14px; }
.colunas td { vertical-align: middle; }
.colunas tr.pendente input { border-color: #f3c98b; background: #fffaf2; }
.exemplo { color: var(--texto-suave); max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fim { margin-top: 12px; }
.regra { display: grid; grid-template-columns: 120px 1fr auto; gap: 10px; align-items: start; margin-bottom: 10px; }
.regra.nova { padding-top: 10px; border-top: 1px dashed var(--borda); }
.acoes { display: flex; flex-direction: column; gap: 6px; }
.ok-msg { color: var(--sucesso); }
@media (max-width: 640px) {
  .regra { grid-template-columns: 1fr; }
}
</style>
