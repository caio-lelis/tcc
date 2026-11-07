<script setup>
// Texto formatado de um bloco do relatório. O conteúdo é JSON do Tiptap, nunca HTML:
// o que é colado de fora só entra se couber nos elementos habilitados aqui.
import { watch } from "vue";
import { EditorContent, useEditor } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import { Placeholder } from "@tiptap/extensions";
import { Bold, Heading2, Heading3, Italic, List, ListOrdered, Quote, Strikethrough, Underline } from "@lucide/vue";

const props = defineProps({
  doc: { type: Object, default: null },
  texto: { type: String, default: "" }, // blocos antigos e respostas recém-anexadas só têm texto simples
  dica: { type: String, default: "Escreva aqui…" },
  autofoco: { type: Boolean, default: false }, // bloco recém-criado: o cursor já começa nele
});
const emit = defineEmits(["alterado"]);

function docDoTexto(texto) {
  const paragrafos = texto.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  return {
    type: "doc",
    content: paragrafos.map((p) => ({
      type: "paragraph",
      content: p.split("\n").flatMap((linha, i) => [
        ...(i ? [{ type: "hardBreak" }] : []),
        ...(linha ? [{ type: "text", text: linha }] : []),
      ]),
    })),
  };
}

const conteudo = () => props.doc ?? docDoTexto(props.texto);

const editor = useEditor({
  content: conteudo(),
  autofocus: props.autofoco ? "end" : false,
  extensions: [
    StarterKit.configure({
      heading: { levels: [2, 3] },
      code: false,
      codeBlock: false,
      horizontalRule: false,
      link: false,
    }),
    Placeholder.configure({ placeholder: () => props.dica }),
  ],
  onUpdate: ({ editor: e }) => emit("alterado", { doc: e.getJSON(), texto: e.getText({ blockSeparator: "\n\n" }) }),
});

// o conteúdo só muda por fora quando outra aba gravou antes e o relatório foi recarregado
watch(() => [props.doc, props.texto], () => {
  const novo = conteudo();
  if (editor.value && JSON.stringify(novo) !== JSON.stringify(editor.value.getJSON()) && props.doc) {
    editor.value.commands.setContent(novo, { emitUpdate: false });
  }
});

const BOTOES = [
  { nome: "bold", rotulo: "Negrito (Ctrl+B)", icone: Bold, acao: (c) => c.toggleBold() },
  { nome: "italic", rotulo: "Itálico (Ctrl+I)", icone: Italic, acao: (c) => c.toggleItalic() },
  { nome: "underline", rotulo: "Sublinhado (Ctrl+U)", icone: Underline, acao: (c) => c.toggleUnderline() },
  { nome: "strike", rotulo: "Tachado", icone: Strikethrough, acao: (c) => c.toggleStrike() },
  { separador: true },
  { nome: "heading", atributos: { level: 2 }, rotulo: "Subtítulo", icone: Heading2, acao: (c) => c.toggleHeading({ level: 2 }) },
  { nome: "heading", atributos: { level: 3 }, rotulo: "Subtítulo menor", icone: Heading3, acao: (c) => c.toggleHeading({ level: 3 }) },
  { separador: true },
  { nome: "bulletList", rotulo: "Lista", icone: List, acao: (c) => c.toggleBulletList() },
  { nome: "orderedList", rotulo: "Lista numerada", icone: ListOrdered, acao: (c) => c.toggleOrderedList() },
  { nome: "blockquote", rotulo: "Citação", icone: Quote, acao: (c) => c.toggleBlockquote() },
];
</script>

<template>
  <div class="texto-rico">
    <div v-if="editor" class="barra" role="toolbar" aria-label="Formatação do texto">
      <template v-for="(b, i) in BOTOES" :key="i">
        <span v-if="b.separador" class="divisor"></span>
        <button
          v-else
          type="button"
          :class="{ ativo: editor.isActive(b.nome, b.atributos) }"
          :aria-pressed="editor.isActive(b.nome, b.atributos)"
          :aria-label="b.rotulo"
          :title="b.rotulo"
          @mousedown.prevent
          @click="b.acao(editor.chain().focus()).run()"
        ><component :is="b.icone" /></button>
      </template>
    </div>
    <EditorContent :editor="editor" />
  </div>
</template>

<style scoped>
.texto-rico { position: relative; }

/* a barra aparece só no bloco em edição, sem empurrar o texto */
.barra {
  position: absolute;
  left: 0;
  bottom: 100%;
  z-index: 3;
  display: none;
  align-items: center;
  gap: 1px;
  margin-bottom: 4px;
  padding: 2px;
  border-radius: 9px;
  background: var(--superficie);
  border: 1px solid var(--borda);
  box-shadow: var(--sombra);
}
.texto-rico:focus-within .barra { display: flex; }
.barra button {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--suave);
  cursor: pointer;
}
.barra button:hover { background: var(--superficie-2); color: var(--texto); }
.barra button:focus-visible { outline: 2px solid var(--borda-foco); }
.barra button.ativo { background: var(--primaria-50); color: var(--primaria); }
.barra svg { width: 15px; height: 15px; }
.divisor { width: 1px; height: 16px; margin: 0 3px; background: var(--borda); }

.texto-rico :deep(.ProseMirror) { outline: none; color: var(--texto-2); line-height: 1.6; min-height: 1.6em; overflow-wrap: anywhere; }
.texto-rico :deep(.ProseMirror > * + *) { margin-top: 0.55em; }
.texto-rico :deep(p) { margin: 0; }
.texto-rico :deep(h2), .texto-rico :deep(h3) { margin: 0.5em 0 0; color: var(--texto); font-weight: 700; letter-spacing: -0.01em; }
.texto-rico :deep(h2) { font-size: 1.12rem; }
.texto-rico :deep(h3) { font-size: 1rem; }
.texto-rico :deep(ul), .texto-rico :deep(ol) { margin: 0; padding-left: 1.4em; }
.texto-rico :deep(blockquote) { margin: 0; padding: 2px 0 2px 12px; border-left: 3px solid var(--borda-forte); color: var(--suave); }
.texto-rico :deep(p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  height: 0;
  color: var(--muito-suave);
  pointer-events: none;
}
</style>
