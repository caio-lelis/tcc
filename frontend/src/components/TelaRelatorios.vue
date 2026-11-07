<script setup>
// Aba Relatórios: a lista dos documentos e o editor do que estiver aberto.
import { onMounted, ref } from "vue";
import { FilePlus2, FileText, Trash2 } from "@lucide/vue";
import EditorRelatorio from "./EditorRelatorio.vue";
import { avisar } from "../avisos.js";
import { abrirRelatorio, carregarLista, criarRelatorio, excluirRelatorio, relatorios } from "../relatorios.js";

const carregando = ref(true);
const confirmando = ref(null);
const indisponivel = ref(null);
const dia = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" });

async function tentar(acao) {
  try {
    await acao();
  } catch (e) {
    avisar(e.message, "erro");
  }
}

async function carregar() {
  try {
    await carregarLista();
    indisponivel.value = null;
    if (!relatorios.atual && relatorios.lista.length) await abrirRelatorio(relatorios.lista[0].id);
  } catch (e) {
    indisponivel.value = e.message;
  } finally {
    carregando.value = false;
  }
}

async function excluir(id) {
  if (confirmando.value !== id) {
    confirmando.value = id;
    return;
  }
  confirmando.value = null;
  await tentar(() => excluirRelatorio(id));
}

onMounted(carregar);
</script>

<template>
  <section class="pagina">
    <div class="cabecalho">
      <h1>Relatórios</h1>
      <p>Junte as respostas do assistente num documento seu, edite como quiser e exporte em PDF.</p>
    </div>

    <div v-if="indisponivel" class="alerta erro"><span>{{ indisponivel }}</span></div>

    <div v-else-if="!carregando" class="grade">
      <aside class="lista">
        <button class="botao primario" @click="tentar(() => criarRelatorio('Relatório sem título'))"><FilePlus2 /> Novo relatório</button>
        <div
          v-for="r in relatorios.lista"
          :key="r.id"
          class="item-relatorio"
          :class="{ ativo: relatorios.atual?.id === r.id }"
        >
          <button class="abrir" @click="tentar(() => abrirRelatorio(r.id))">
            <FileText />
            <span>
              <b>{{ relatorios.atual?.id === r.id ? relatorios.atual.titulo || "Sem título" : r.titulo }}</b>
              <small>{{ dia.format(new Date(r.atualizado_em)) }} · {{ r.quantidade_versoes }} PDF{{ r.quantidade_versoes === 1 ? "" : "s" }}</small>
            </span>
          </button>
          <button
            class="excluir"
            :class="{ confirmar: confirmando === r.id }"
            :title="confirmando === r.id ? 'Clique de novo para excluir, com todos os PDFs' : 'Excluir relatório'"
            @click="excluir(r.id)"
            @blur="confirmando = null"
          >
            <Trash2 /><span v-if="confirmando === r.id">Excluir?</span>
          </button>
        </div>
      </aside>

      <EditorRelatorio v-if="relatorios.atual" class="area-editor" />
      <div v-else class="area-editor nada">
        <p>Crie um relatório, ou vá em "Perguntar" e use <b>Adicionar ao relatório</b> numa resposta.</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.pagina { max-width: 1180px; }
.grade { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 28px; align-items: start; }
.lista { display: flex; flex-direction: column; gap: 6px; position: sticky; top: 24px; }
.lista > .botao { margin-bottom: 8px; }
.item-relatorio { display: flex; align-items: center; border-radius: 10px; border: 1px solid transparent; }
.item-relatorio:hover { background: var(--superficie-2); }
.item-relatorio.ativo { background: var(--superficie); border-color: var(--borda); box-shadow: var(--sombra-sm); }
.abrir {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border: none;
  background: transparent;
  color: var(--texto-2);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.abrir > svg { width: 18px; height: 18px; flex-shrink: 0; color: var(--primaria); }
.abrir span { min-width: 0; display: flex; flex-direction: column; }
.abrir b { font-weight: 600; font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.abrir small { color: var(--suave); font-size: 0.76rem; }
.abrir:focus-visible, .excluir:focus-visible { outline: 2px solid var(--borda-foco); border-radius: 8px; }
.excluir {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 30px;
  min-width: 30px;
  justify-content: center;
  margin-right: 4px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--muito-suave);
  font: inherit;
  font-size: 0.78rem;
  cursor: pointer;
}
.excluir svg { width: 15px; height: 15px; }
.excluir:hover { color: var(--vermelho); background: var(--vermelho-50); }
.excluir.confirmar { color: var(--vermelho); background: var(--vermelho-50); padding: 0 8px; font-weight: 600; }
.area-editor { min-width: 0; }
.nada { padding: 48px 24px; border: 1.5px dashed var(--borda-forte); border-radius: var(--raio); color: var(--suave); text-align: center; }

@media (max-width: 860px) {
  .grade { grid-template-columns: minmax(0, 1fr); }
  .lista { position: static; }
}
</style>
