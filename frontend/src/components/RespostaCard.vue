<script setup>
// Uma pergunta e a resposta do assistente (Seção 3.6): texto + gráfico + tabela.
// SQL, configuração e status só no modo avançado (RF05).
import { computed, ref } from "vue";
import { BarChart3, Check, Code2, Copy, Sparkles, Table2, TriangleAlert } from "@lucide/vue";
import Grafico from "./Grafico.vue";
import TabelaResultado from "./TabelaResultado.vue";
import { formatarNumero, nomeLegivel } from "../formatacao.js";

const props = defineProps({
  pergunta: { type: String, required: true },
  resposta: { type: Object, default: null },
  erro: { type: String, default: null },
  carregando: { type: Boolean, default: false },
  avancado: { type: Boolean, default: false },
});

const visao = ref("grafico");
const copiado = ref(false);

const sucesso = computed(() => props.resposta?.status === "sucesso");
const grafico = computed(() => props.resposta?.grafico);
const temGrafico = computed(() => sucesso.value && ["linha", "barra"].includes(grafico.value?.tipo) && grafico.value.echarts);
const indicador = computed(() => (sucesso.value && grafico.value?.tipo === "indicador" ? grafico.value.indicador : null));
const temLinhas = computed(() => sucesso.value && props.resposta.linhas.length > 0);
const ROTULO_STATUS = {
  sucesso: "consulta executada",
  recusada: "recusada por segurança",
  invalida: "consulta inválida",
  tempo_esgotado: "tempo esgotado",
  erro_modelo: "falha no serviço de IA",
};

async function copiarSql() {
  try {
    await navigator.clipboard.writeText(props.resposta.sql);
    copiado.value = true;
    setTimeout(() => (copiado.value = false), 1600);
  } catch {
    /* sem área de transferência */
  }
}
</script>

<template>
  <div class="troca surgir">
    <div class="pergunta">{{ pergunta }}</div>

    <div class="assistente">
      <div class="avatar"><Sparkles /></div>

      <div class="corpo">
        <!-- carregando -->
        <div v-if="carregando" class="pensando">
          <span class="pontos"><i></i><i></i><i></i></span>
          Analisando seus dados…
        </div>

        <!-- erro de comunicação -->
        <div v-else-if="erro" class="alerta erro"><TriangleAlert /><span>{{ erro }}</span></div>

        <template v-else-if="resposta">
          <!-- o assistente não conseguiu responder -->
          <div v-if="!sucesso" class="alerta"><TriangleAlert /><span>{{ resposta.mensagem }}</span></div>

          <template v-else>
            <p v-if="resposta.texto" class="texto">{{ resposta.texto }}</p>

            <!-- número em destaque -->
            <div v-if="indicador" class="indicador cartao">
              <div class="indicador-rotulo">{{ nomeLegivel(indicador.rotulo) }}</div>
              <div class="indicador-valor">{{ formatarNumero(indicador.valor) }}</div>
            </div>

            <!-- gráfico e tabela -->
            <div v-else-if="temLinhas" class="painel cartao">
              <div v-if="temGrafico" class="alternador">
                <button :class="{ ativo: visao === 'grafico' }" @click="visao = 'grafico'"><BarChart3 /> Gráfico</button>
                <button :class="{ ativo: visao === 'tabela' }" @click="visao = 'tabela'"><Table2 /> Tabela</button>
              </div>
              <Grafico v-if="temGrafico && visao === 'grafico'" :grafico="grafico" />
              <TabelaResultado v-else :colunas="resposta.colunas" :linhas="resposta.linhas" />
              <div class="rodape">
                <span>{{ resposta.linhas.length }}{{ resposta.truncado ? "+" : "" }} linha{{ resposta.linhas.length === 1 ? "" : "s" }}</span>
                <span v-if="resposta.truncado" class="selo ambar">resultado cortado no limite de linhas</span>
              </div>
            </div>

            <p v-else class="texto-suave">Nenhum dado encontrado para essa pergunta.</p>
          </template>

          <!-- detalhes técnicos -->
          <details v-if="avancado" class="tecnico">
            <summary><Code2 /> Detalhes técnicos</summary>
            <div class="linha selos">
              <span class="selo primario">{{ resposta.configuracao }}</span>
              <span class="selo" :class="sucesso ? 'verde' : 'ambar'">{{ ROTULO_STATUS[resposta.status] ?? resposta.status }}</span>
              <span v-if="grafico" class="selo">gráfico: {{ grafico.tipo }} · {{ grafico.origem === "modelo" ? "sugerido pelo modelo" : "por regra" }}</span>
              <span class="selo">execução {{ resposta.id }}</span>
            </div>
            <div v-if="resposta.sql" class="sql">
              <button class="botao fantasma pequeno copiar" @click="copiarSql">
                <Check v-if="copiado" /><Copy v-else /> {{ copiado ? "Copiado" : "Copiar" }}
              </button>
              <pre class="codigo">{{ resposta.sql }}</pre>
            </div>
          </details>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.troca { display: flex; flex-direction: column; gap: 14px; margin-bottom: 30px; }

.pergunta {
  align-self: flex-end;
  max-width: 78%;
  padding: 12px 16px;
  border-radius: 18px 18px 6px 18px;
  background: var(--degrade);
  color: #fff;
  font-weight: 500;
  box-shadow: 0 6px 18px -8px rgba(99, 102, 241, 0.7);
}

.assistente { display: flex; gap: 14px; align-items: flex-start; }
.avatar {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: var(--primaria-50);
  color: var(--primaria);
  border: 1px solid var(--primaria-100);
}
.avatar svg { width: 17px; height: 17px; }
.corpo { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 14px; padding-top: 5px; }

.texto { font-size: 1.02rem; line-height: 1.65; color: var(--texto-2); }

.pensando { display: flex; align-items: center; gap: 12px; color: var(--suave); padding-top: 2px; }
.pontos { display: inline-flex; gap: 4px; }
.pontos i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--primaria);
  opacity: 0.3;
  animation: pulsar 1.2s infinite ease-in-out;
}
.pontos i:nth-child(2) { animation-delay: 0.15s; }
.pontos i:nth-child(3) { animation-delay: 0.3s; }
@keyframes pulsar { 0%, 80%, 100% { opacity: 0.25; transform: scale(0.85); } 40% { opacity: 1; transform: scale(1); } }

.indicador { padding: 20px 24px; width: fit-content; min-width: 240px; position: relative; overflow: hidden; }
.indicador::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: var(--degrade); }
.indicador-rotulo { font-size: 0.82rem; font-weight: 600; color: var(--suave); text-transform: uppercase; letter-spacing: 0.05em; }
.indicador-valor {
  font-size: 2.6rem;
  font-weight: 750;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin-top: 4px;
  background: var(--degrade);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  font-variant-numeric: tabular-nums;
}

.painel { padding: 16px 18px 12px; }
.alternador {
  display: inline-flex;
  padding: 3px;
  margin-bottom: 14px;
  border-radius: 10px;
  background: var(--superficie-2);
  border: 1px solid var(--borda);
}
.alternador button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 550;
  color: var(--suave);
  cursor: pointer;
}
.alternador button svg { width: 15px; height: 15px; }
.alternador button.ativo { background: var(--superficie); color: var(--texto); box-shadow: var(--sombra-sm); }
.rodape { display: flex; gap: 10px; align-items: center; margin-top: 10px; font-size: 0.82rem; color: var(--muito-suave); }

.tecnico { border-top: 1px dashed var(--borda); padding-top: 12px; }
.tecnico summary {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  cursor: pointer;
  font-size: 0.86rem;
  font-weight: 550;
  color: var(--suave);
  list-style: none;
}
.tecnico summary::-webkit-details-marker { display: none; }
.tecnico summary svg { width: 15px; height: 15px; }
.tecnico[open] summary { color: var(--texto); margin-bottom: 12px; }
.selos { margin-bottom: 12px; }
.sql { position: relative; }
.copiar { position: absolute; top: 8px; right: 8px; color: #cbd5e1; }
.copiar:hover:not(:disabled) { background: rgba(255, 255, 255, 0.08) !important; color: #fff !important; }
</style>
