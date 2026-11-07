// Cliente da API do Data Talk. Todas as rotas passam por /api (nginx ou Vite repassam ao backend).
const BASE = "/api";

async function pedir(metodo, caminho, corpo) {
  const opcoes = { method: metodo, headers: {} };
  if (corpo instanceof FormData) {
    opcoes.body = corpo;
  } else if (corpo !== undefined) {
    opcoes.headers["Content-Type"] = "application/json";
    opcoes.body = JSON.stringify(corpo);
  }
  const resposta = await fetch(BASE + caminho, opcoes);
  if (resposta.status === 204) return null;
  const dados = await resposta.json().catch(() => null);
  if (!resposta.ok) {
    const detalhe = dados?.detail;
    const mensagem = Array.isArray(detalhe)
      ? detalhe.map((d) => d.msg).join("; ")
      : detalhe || `Erro ${resposta.status}`;
    const erro = new Error(mensagem);
    erro.status = resposta.status;
    throw erro;
  }
  return dados;
}

export const api = {
  // tabelas (RF01, RF10)
  listarTabelas: () => pedir("GET", "/tabelas"),
  anexarTabela(arquivo, nome) {
    const formulario = new FormData();
    formulario.append("arquivo", arquivo);
    if (nome) formulario.append("nome", nome);
    return pedir("POST", "/tabelas", formulario);
  },
  removerTabela: (nome) => pedir("DELETE", `/tabelas/${encodeURIComponent(nome)}`),

  // contexto (RF02, RF03)
  obterContexto: () => pedir("GET", "/contexto"),
  salvarDescricao: (nome, descricao) =>
    pedir("PUT", `/tabelas/${encodeURIComponent(nome)}/descricao`, descricao),
  adicionarRegra: (regra) => pedir("POST", "/regras", regra),
  atualizarRegra: (id, regra) => pedir("PUT", `/regras/${id}`, regra),
  removerRegra: (id) => pedir("DELETE", `/regras/${id}`),

  // perguntas (RF04, RF05, RF06)
  perguntar: (corpo) => pedir("POST", "/perguntas", corpo),

  // relatórios ao vivo
  listarRelatorios: () => pedir("GET", "/relatorios"),
  criarRelatorio: (titulo) => pedir("POST", "/relatorios", { titulo }),
  obterRelatorio: (id) => pedir("GET", `/relatorios/${id}`),
  editarRelatorio: (id, corpo) => pedir("PUT", `/relatorios/${id}`, corpo),
  excluirRelatorio: (id) => pedir("DELETE", `/relatorios/${id}`),
  anexarAoRelatorio: (id, corpo) => pedir("POST", `/relatorios/${id}/anexos`, corpo),
  atualizarBloco: (id, bloco) => pedir("POST", `/relatorios/${id}/blocos/${bloco}/atualizar`),
  listarVersoes: (id) => pedir("GET", `/relatorios/${id}/versoes`),
  publicarVersao: (id, corpo) => pedir("POST", `/relatorios/${id}/versoes`, corpo),
};
