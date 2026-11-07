// Monta os gráficos do ECharts a partir da especificação do backend.
import * as echarts from "echarts";
import { CORES } from "./paleta.js";
import { formatarCompacto, formatarNumero, nomeLegivel, rotulosDeEixo } from "./formatacao.js";

const FONTE = "Inter Variable, Inter, Segoe UI, sans-serif";

// O ECharts desenha fora do CSS: as cores vêm dos tokens do tema atual.
export function coresDoTema() {
  const estilo = getComputedStyle(document.documentElement);
  const token = (nome) => estilo.getPropertyValue(nome).trim();
  return {
    suave: token("--suave"),
    textoForte: token("--texto-2"),
    superficie: token("--superficie"),
    eixo: token("--grafico-eixo"),
    grade: token("--grafico-grade"),
    aviso: token("--aviso-fundo"),
    muitoSuave: token("--muito-suave"),
    destaque: token("--grafico-destaque"),
  };
}

export const ehHorizontal = (g) => g.tipo === "barra" && g.orientacao === "horizontal";
export const alturaDoGrafico = (g) => (ehHorizontal(g) ? Math.max(200, g.categorias.length * 34 + 56) : 300);

/** Um painel por gráfico. Escalas muito diferentes: um painel por medida. */
export function paineisDoGrafico(grafico) {
  // a cor acompanha a série (ordem fixa da paleta), mesmo quando cada série vai para o seu gráfico
  const series = grafico.series.map((s, i) => ({ ...s, cor: CORES[i % CORES.length] }));
  return grafico.escalas_separadas
    ? series.map((s) => ({ titulo: nomeLegivel(s.nome), series: [s] }))
    : [{ titulo: null, series }];
}

// rótulo no fim da linha para até 4 séries: identificar a série não depende só da cor
export const usaRotulosDiretos = (g) =>
  g.tipo === "linha" && !g.escalas_separadas && g.series.length >= 2 && g.series.length <= 4;

export function montarOpcao(g, cores) {
  const linha = g.tipo === "linha";
  const horizontal = ehHorizontal(g);
  const variasSeries = g.series.length > 1;
  const rotulos = rotulosDeEixo(g.categorias);
  const muitosPontos = g.categorias.length > 24;
  const texto = { color: cores.suave, fontSize: 12, fontFamily: FONTE };

  const series = g.series.map((s) => {
    const base = { name: nomeLegivel(s.nome), data: s.valores, emphasis: { focus: "series" } };
    if (linha) {
      return {
        ...base,
        type: "line",
        // várias séries: linhas retas; uma série: suavização monotônica, que nunca passa
        // acima ou abaixo dos pontos (curvas livres "inventam" valores entre eles)
        smooth: variasSeries ? false : 0.3,
        smoothMonotone: "x",
        labelLayout: { moveOverlap: "shiftY" }, // rótulos do fim da linha não se sobrepõem
        connectNulls: false, // mês sem registro não vira um traço inventado
        symbol: "circle",
        symbolSize: 8,
        showSymbol: !muitosPontos,
        lineStyle: { width: 2, color: s.cor },
        itemStyle: { color: s.cor, borderColor: cores.superficie, borderWidth: 2 },
        areaStyle: variasSeries
          ? undefined
          : {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: s.cor + "33" },
                { offset: 1, color: s.cor + "00" },
              ]),
            },
        endLabel: g.rotulosDiretos
          ? { show: true, formatter: "{a}", color: cores.textoForte, fontSize: 12, fontWeight: 600, distance: 8 }
          : undefined,
      };
    }
    return {
      ...base,
      type: "bar",
      barMaxWidth: horizontal ? 22 : 40,
      barGap: "12%",
      barCategoryGap: variasSeries ? "28%" : "36%",
      itemStyle: { color: s.cor, borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] },
    };
  });

  const eixoCategoria = {
    type: "category",
    data: rotulos,
    boundaryGap: !linha,
    inverse: horizontal, // ranking: o maior em cima
    axisLine: { lineStyle: { color: cores.eixo } },
    axisTick: { show: false },
    axisLabel: { ...texto, margin: 12, hideOverlap: true, color: horizontal ? cores.textoForte : texto.color },
  };
  const eixoValor = {
    type: "value",
    splitLine: { lineStyle: { color: cores.grade, type: "dashed" } },
    axisLabel: { ...texto, formatter: (v) => formatarCompacto(v) },
  };

  return {
    textStyle: { fontFamily: FONTE },
    grid: {
      left: 4,
      // em linhas, o último rótulo do eixo fica centrado na borda do gráfico e precisa de folga
      right: g.rotulosDiretos ? 110 : linha ? 34 : 20,
      top: variasSeries ? 40 : 16,
      bottom: muitosPontos && !horizontal ? 44 : 4,
      containLabel: true,
    },
    legend: variasSeries
      ? { top: 0, left: 0, icon: "roundRect", itemWidth: 12, itemHeight: 12, itemGap: 16, textStyle: { color: cores.textoForte, fontSize: 13 } }
      : { show: false },
    tooltip: {
      trigger: "axis",
      backgroundColor: cores.aviso,
      borderWidth: 0,
      padding: [10, 14],
      textStyle: { color: "#f1f5f9", fontSize: 13 },
      axisPointer: linha
        ? { type: "line", lineStyle: { color: cores.muitoSuave, width: 1, type: "dashed" } }
        : { type: "shadow", shadowStyle: { color: cores.destaque } },
      valueFormatter: (v) => (v === null || v === undefined || Number.isNaN(v) ? "sem dado" : formatarNumero(v)),
    },
    xAxis: horizontal ? eixoValor : eixoCategoria,
    yAxis: horizontal ? eixoCategoria : eixoValor,
    dataZoom: muitosPontos && !horizontal
      ? [{ type: "inside" }, { type: "slider", height: 16, bottom: 4, borderColor: "transparent", fillerColor: "rgba(21,96,224,0.12)", showDetail: false }]
      : [],
    series,
    animationDuration: 500,
    animationEasing: "cubicOut",
  };
}
