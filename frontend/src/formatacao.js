// Formatação de números, datas e nomes de coluna para leitura por quem não é técnico.
const numero = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
const compacto = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const DATA = /^(\d{4})-(\d{2})(?:-(\d{2}))?(?:[T ].*)?$/;

export function formatarNumero(valor) {
  return numero.format(valor);
}

export function formatarCompacto(valor) {
  return Math.abs(valor) >= 10000 ? compacto.format(valor) : numero.format(valor);
}

/** 2026-03-01 -> "01/03/2026"; 2026-03 -> "mar 2026" */
export function formatarData(texto) {
  const m = DATA.exec(texto);
  if (!m) return texto;
  const [, ano, mes, dia] = m;
  return dia ? `${dia}/${mes}/${ano}` : `${MESES[Number(mes) - 1]} ${ano}`;
}

/** Rótulo de eixo: meses agregados (dia 01 em todos) viram "mar 2026". */
export function rotulosDeEixo(valores) {
  const textos = valores.map((v) => (v === null || v === undefined ? "—" : String(v)));
  const todosMeses = textos.length > 0 && textos.every((t) => {
    const m = DATA.exec(t);
    return m && (!m[3] || m[3] === "01");
  });
  if (todosMeses) {
    return textos.map((t) => {
      const [, ano, mes] = DATA.exec(t);
      return `${MESES[Number(mes) - 1]} ${ano}`;
    });
  }
  return textos.map((t) => (DATA.test(t) ? formatarData(t) : t));
}

export function formatarValor(valor) {
  if (valor === null || valor === undefined) return "—";
  if (typeof valor === "number") return numero.format(valor);
  if (typeof valor === "boolean") return valor ? "sim" : "não";
  if (typeof valor === "string" && DATA.test(valor)) return formatarData(valor);
  return String(valor);
}

/** "quantidade_vendas" -> "Quantidade vendas" */
export function nomeLegivel(coluna) {
  if (!coluna) return "";
  const texto = coluna.replaceAll("_", " ").trim();
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

export function formatarBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
