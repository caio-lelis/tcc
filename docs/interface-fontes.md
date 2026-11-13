# Interface: elementos e fontes

A interface do Data Talk usa padrões visuais observados em dois catálogos, [transitions.dev](https://transitions.dev/library.html) e os blocos do [React Bits Pro](https://pro.reactbits.dev/docs/blocks). **Nenhuma linha de código desses sites foi copiada:** cada padrão foi reescrito do zero em Vue 3 e CSS, com os tokens de cor do Data Talk (ver [Licenças](#licenças)). Os números mostrados nas telas vêm sempre da API.

Caminhos relativos a `frontend/src/`.

## Inspirados no transitions.dev

| Elemento no Data Talk | Padrão de origem | Arquivo |
| --- | --- | --- |
| Pílula das abas do topo e pílula-fantasma que segue o mouse | [Tabs sliding](https://transitions.dev/detail.html?t=tabs-sliding) | `App.vue`, `indicador.js` |
| Alternador Gráfico/Tabela da resposta | [Tabs sliding](https://transitions.dev/detail.html?t=tabs-sliding) | `components/RespostaCard.vue` |
| Troca de tela que entra pelo lado da aba escolhida | [Page side-by-side](https://transitions.dev/detail.html?t=page-side-by-side) | `App.vue` |
| Painel do relatório que entra deslizando | [Panel reveal](https://transitions.dev/detail.html?t=panel-reveal) | `App.vue` |
| Avisos que sobem com desfoque e se reorganizam | [Toast open/close](https://transitions.dev/detail.html?t=toast-open-close), [Banner stacking](https://transitions.dev/detail.html?t=banner-stacking) | `components/Avisos.vue` |
| Check que se desenha | [Success check](https://transitions.dev/detail.html?t=success-check), [Checkbox check](https://transitions.dev/detail.html?t=checkbox-check) | `estilo.css`, `components/Avisos.vue`, `components/RespostaCard.vue` |
| Frases de "pensando" que se revezam | [Thinking states](https://transitions.dev/detail.html?t=thinking-states) | `components/Pensando.vue` |
| Brilho que varre o texto de "pensando" | [Shimmer text](https://transitions.dev/detail.html?t=shimmer-text) | `estilo.css` (`.brilho-texto`), `components/Pensando.vue` |
| Resposta que chega palavra por palavra | [Streaming text](https://transitions.dev/detail.html?t=streaming-text) | `components/RespostaCard.vue` |
| Título do Início que surge palavra por palavra | [Texts reveal](https://transitions.dev/detail.html?t=texts-reveal) | `components/TelaInicio.vue` |
| Exemplos de pergunta que se revezam no campo | [Text states swap](https://transitions.dev/detail.html?t=text-states-swap) | `components/TelaInicio.vue` |
| Números em tambor | [Spinning counter](https://transitions.dev/detail.html?t=spinning-counter) | `components/NumeroTambor.vue` |
| Ícone do tema que gira; botão de remover que vira "Sim / Não" | [Icon swap](https://transitions.dev/detail.html?t=icon-swap) | `App.vue`, `components/TelaDados.vue`, `components/TelaContexto.vue` |
| Interruptor do modo avançado com quique duplo | [Toggle](https://transitions.dev/detail.html?t=toggle) | `App.vue` |
| Seta que aparece no hover das sugestões e passos | [Learn more hover](https://transitions.dev/detail.html?t=learn-more-hover) | `components/TelaInicio.vue`, `components/PrimeirosPassos.vue` |
| Esqueleto enquanto a tabela chega | [Skeleton loader and reveal](https://transitions.dev/detail.html?t=skeleton-loader-and-reveal) | `estilo.css`, `components/TelaDados.vue`, `components/TelaInicio.vue` |
| Amostra e tabelas que abrem pela altura real | [Accordion](https://transitions.dev/detail.html?t=accordion) | `estilo.css` (`.sanfona-corpo-anim`), `components/TelaDados.vue`, `components/TelaContexto.vue` |
| Fichas das tabelas que se afastam no hover | [Avatar group hover](https://transitions.dev/detail.html?t=avatar-group-hover) | `components/TelaInicio.vue` |
| Miniatura do último relatório que inclina em 3D | [3D tilt](https://transitions.dev/detail.html?t=3d-tilt) | `components/TelaInicio.vue` |

Tudo respeita a opção "reduzir movimento" do sistema (`estilo.css`, fim do arquivo).

## Inspirados no React Bits Pro

Só ideias de layout, vistas nas páginas públicas de cada categoria (não há página por bloco).

| Elemento no Data Talk | Categoria de origem | Arquivo |
| --- | --- | --- |
| Grade em bento do Início | [Bento](https://pro.reactbits.dev/docs/blocks/bento) | `components/TelaInicio.vue` |
| Barra superior com logo, abas em pílula e ações à direita | [Navigation](https://pro.reactbits.dev/docs/blocks/navigation) | `App.vue` |
| Abertura com saudação, campo central e sugestões | [Hero Section](https://pro.reactbits.dev/docs/blocks/hero-section) | `components/TelaInicio.vue` |
| Cartões de número em destaque | [Stats](https://pro.reactbits.dev/docs/blocks/stats) | `components/TelaInicio.vue` |
| Primeiros passos em etapas numeradas | [How It Works](https://pro.reactbits.dev/docs/blocks/how-it-works) | `components/PrimeirosPassos.vue` |

## Elementos próprios

| Elemento | O que faz | Arquivo |
| --- | --- | --- |
| Logo animada | Entra em sequência, fica viva em repouso (rabo, barras, raios, brilho no "Talk") e pula no hover (o pulo já existia) | `components/LogoDataTalk.vue` |
| Mascote do Início | Recorte do cachorro e do balão sobre o azul da marca | `components/TelaInicio.vue` |
| Feixe no campo de pergunta | Brilho menta e azul girando em volta da borda | `estilo.css` (`.feixe`) |
| Cartão vivo | Sobe no hover e um reflexo atravessa | `estilo.css` (`.vivo`) |
| Entrada em cascata | Cada bloco chega desfocado, um depois do outro | `estilo.css` (`.revela`) |
| Área de soltar com tracejado que anda | Borda em movimento; muda de cor ao arrastar | `components/TelaDados.vue` |
| Remoção que se dissolve | Cartão some com desfoque | `components/TelaDados.vue` |
| Cores por tipo de coluna | Número azul, data âmbar, sim/não menta | `components/TelaDados.vue` |
| Anel de progresso | Quanto do contexto já foi descrito | `components/TelaContexto.vue`, `components/TelaInicio.vue` |
| Regras que entram e saem | Nova entra com mola; removida se dissolve | `components/TelaContexto.vue` |

## Licenças

| Site | Permite | Proíbe | Como o Data Talk usou |
| --- | --- | --- | --- |
| [transitions.dev](https://transitions.dev/terms.html) (termos de 10/10/2026) | Usar e modificar as transições em qualquer projeto, inclusive comercial | Republicar a coleção, ou boa parte dela, como biblioteca | Só o padrão visual; CSS e Vue reescritos |
| [React Bits Pro](https://pro.reactbits.dev/license) (licença v2.2, 11/09/2026) | Uso por um desenvolvedor licenciado | Redistribuir o código, inclusive em repositório aberto, e extraí-lo das prévias | Só ideias de layout das páginas públicas; nenhum código baixado |

Versão editável deste documento: [Data Talk — elementos de interface e fontes](https://claude.ai/artifact/XwKRb7poCoW3GGHdHjJAFM).
