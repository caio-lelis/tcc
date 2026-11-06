<script setup>
// Tela de anexação (RF01) e atualização de tabelas (RF10).
import { onMounted, ref, watch } from "vue";
import { api, formatar } from "../api.js";

const props = defineProps({ versao: { type: Number, default: 0 } });
const emit = defineEmits(["alterado"]);

const tabelas = ref([]);
const arquivos = ref([]);
const nome = ref("");
const enviando = ref(false);
const resultados = ref([]);
const erro = ref("");
const seletor = ref(null);

async function carregar() {
  try {
    tabelas.value = await api.listarTabelas();
  } catch (e) {
    erro.value = e.message;
  }
}
onMounted(carregar);
watch(() => props.versao, carregar);

function aoEscolher(evento) {
  arquivos.value = [...evento.target.files];
  if (arquivos.value.length !== 1) nome.value = "";
}

async function anexar() {
  enviando.value = true;
  erro.value = "";
  resultados.value = [];
  try {
    for (const arquivo of arquivos.value) {
      const r = await api.anexarTabela(arquivo, arquivos.value.length === 1 ? nome.value : "");
      resultados.value.push({ arquivo: arquivo.name, ...r });
    }
    arquivos.value = [];
    nome.value = "";
    if (seletor.value) seletor.value.value = "";
    emit("alterado");
  } catch (e) {
    erro.value = e.message;
  } finally {
    enviando.value = false;
  }
}

async function remover(tabela) {
  if (!confirm(`Remover a tabela "${tabela}"? As descrições escritas sobre ela ficam guardadas.`)) return;
  try {
    await api.removerTabela(tabela);
    emit("alterado");
  } catch (e) {
    erro.value = e.message;
  }
}
</script>

<template>
  <section>
    <div class="cartao">
      <h3>Anexar tabelas</h3>
      <p class="suave">
        Envie arquivos CSV exportados dos seus sistemas. Cada arquivo vira uma tabela. Enviar de novo um arquivo
        com o mesmo nome atualiza a tabela e mantém o que você já escreveu sobre ela.
      </p>
      <div class="linha">
        <input ref="seletor" type="file" accept=".csv,text/csv" multiple @change="aoEscolher" class="arquivo" />
        <input
          v-if="arquivos.length === 1"
          v-model="nome"
          placeholder="Nome da tabela (opcional)"
          class="nome"
        />
        <button class="primario" :disabled="!arquivos.length || enviando" @click="anexar">
          {{ enviando ? "Enviando…" : "Anexar" }}
        </button>
      </div>
      <p v-if="erro" class="erro">{{ erro }}</p>

      <ul v-if="resultados.length" class="resultados">
        <li v-for="r in resultados" :key="r.arquivo">
          <strong>{{ r.tabela.nome }}</strong>
          <span class="suave"> ({{ r.arquivo }}): </span>
          <span v-if="r.nova" class="selo ok">nova tabela, {{ formatar(r.tabela.linhas) }} linhas</span>
          <template v-else>
            <span class="selo">atualizada, {{ formatar(r.tabela.linhas) }} linhas</span>
            <span v-if="r.colunas_novas.length" class="selo alerta">novas: {{ r.colunas_novas.join(", ") }}</span>
            <span v-if="r.colunas_removidas.length" class="selo alerta">removidas: {{ r.colunas_removidas.join(", ") }}</span>
            <span v-if="r.colunas_tipo_alterado.length" class="selo alerta">tipo mudou: {{ r.colunas_tipo_alterado.join(", ") }}</span>
          </template>
        </li>
      </ul>
    </div>

    <p v-if="!tabelas.length" class="suave">Nenhuma tabela anexada ainda.</p>

    <div v-for="t in tabelas" :key="t.nome" class="cartao">
      <div class="linha">
        <h3>{{ t.nome }}</h3>
        <span class="selo">{{ formatar(t.linhas) }} linhas</span>
        <span class="espaco"></span>
        <button class="discreto perigo" @click="remover(t.nome)">Remover</button>
      </div>
      <div class="rolagem">
        <table class="dados">
          <thead>
            <tr><th v-for="c in t.colunas" :key="c.nome" :title="`original: ${c.nome_original}`">
              {{ c.nome }}<div class="tipo">{{ c.tipo }}</div>
            </th></tr>
          </thead>
          <tbody>
            <tr v-for="(linha, i) in t.amostra" :key="i">
              <td v-for="c in t.colunas" :key="c.nome">{{ formatar(linha[c.nome]) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="suave">Amostra das primeiras linhas.</p>
    </div>
  </section>
</template>

<style scoped>
.arquivo { flex: 2; min-width: 220px; }
.nome { flex: 1; min-width: 180px; }
.resultados { padding-left: 18px; line-height: 2; }
.resultados .selo { margin-left: 4px; }
.tipo { font-weight: 400; font-size: 0.8em; color: var(--texto-suave); }
</style>
