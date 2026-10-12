import { Editor } from "@tiptap/core";
import StarterKit from "@tiptap/starter-kit";
import { Table, TableCell, TableHeader, TableRow } from "@tiptap/extension-table";
import UniqueID from "@tiptap/extension-unique-id";

// Avoid inline widths/styles under the portal CSP. Row/column editing is retained.
const SimpleTable = Table.extend({
  renderHTML() { return ["div", { class: "table-scroll" }, ["table", {}, ["tbody", 0]]]; },
});
const SimpleCell = TableCell.extend({ content: "paragraph+" });
const SimpleHeader = TableHeader.extend({ content: "paragraph+" });

export function mountEditor() {
  const root = document.querySelector<HTMLElement>("[data-editor]");
  const surface = root?.querySelector<HTMLElement>("[data-editor-surface]");
  const input = document.querySelector<HTMLInputElement>('input[name="body"]');
  const form = root?.closest<HTMLFormElement>("form");
  const error = root?.querySelector<HTMLElement>("[data-editor-error]");
  if (!root || !surface || !input || !form || !error) return;
  const submitButtons = form.querySelectorAll<HTMLButtonElement>("[data-editor-submit]");
  const fail = (message: string) => { error.textContent = message; error.hidden = false; };
  try {
    const content = JSON.parse(input.value);
    const editor = new Editor({
      element: surface,
      content,
      injectCSS: false,
      enableContentCheck: true,
      extensions: [
        StarterKit.configure({ heading: { levels: [2, 3, 4] }, blockquote: false, horizontalRule: false, strike: false, underline: false, code: false, dropcursor: false, trailingNode: false, link: { openOnClick: false, autolink: false, linkOnPaste: false, HTMLAttributes: { target: null, rel: "noopener noreferrer" } } }),
        UniqueID.configure({ types: ["heading"], attributeName: "id", generateID: () => crypto.randomUUID() }),
        SimpleTable.configure({ resizable: false }), TableRow, SimpleCell, SimpleHeader,
      ],
      editorProps: { attributes: { role: "textbox", "aria-multiline": "true", "aria-label": "Texte de la spécification", spellcheck: "true" } },
      onUpdate: () => { input.value = JSON.stringify(editor.getJSON()); form.dispatchEvent(new Event("input", { bubbles: true })); },
      onContentError: () => { fail("Le document enregistré contient une structure non prise en charge. Vos données restent dans le formulaire ; revenez à une version valide depuis l’historique."); submitButtons.forEach(button => { button.disabled = true; }); },
    });
    input.value = JSON.stringify(editor.getJSON());
    if (error.hidden) submitButtons.forEach(button => { button.disabled = false; });
    const linkInput = root.querySelector<HTMLInputElement>("#editor-link");
    const actions: Record<string, () => boolean | undefined> = {
      paragraph: () => editor.chain().focus().setParagraph().run(),
      h2: () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
      h3: () => editor.chain().focus().toggleHeading({ level: 3 }).run(),
      h4: () => editor.chain().focus().toggleHeading({ level: 4 }).run(),
      bold: () => editor.chain().focus().toggleBold().run(),
      italic: () => editor.chain().focus().toggleItalic().run(),
      bullet: () => editor.chain().focus().toggleBulletList().run(),
      ordered: () => editor.chain().focus().toggleOrderedList().run(),
      code: () => editor.chain().focus().toggleCodeBlock().run(),
      table: () => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
      addRow: () => editor.chain().focus().addRowAfter().run(),
      deleteRow: () => editor.chain().focus().deleteRow().run(),
      addColumn: () => editor.chain().focus().addColumnAfter().run(),
      deleteColumn: () => editor.chain().focus().deleteColumn().run(),
      deleteTable: () => editor.chain().focus().deleteTable().run(),
      undo: () => editor.chain().focus().undo().run(), redo: () => editor.chain().focus().redo().run(),
      unlink: () => editor.chain().focus().extendMarkRange("link").unsetLink().run(),
      link: () => {
        const href = linkInput?.value.trim() ?? "";
        if (!/^(https?:\/\/|mailto:|\/(?!\/)|#)/i.test(href) || /[\s\\\u0000-\u001f]/.test(href)) { fail("Utilisez un lien HTTP(S), mailto ou un chemin local sans espace."); return false; }
        error.hidden = true;
        return editor.chain().focus().extendMarkRange("link").setLink({ href }).run();
      },
    };
    root.querySelectorAll<HTMLButtonElement>("[data-command]").forEach(button => {
      button.addEventListener("click", () => { actions[button.dataset.command ?? ""]?.(); updateToolbar(); });
    });
    const updateToolbar = () => {
      const active: Record<string, boolean> = { bold: editor.isActive("bold"), italic: editor.isActive("italic"), bullet: editor.isActive("bulletList"), ordered: editor.isActive("orderedList"), code: editor.isActive("codeBlock"), h2: editor.isActive("heading", { level: 2 }), h3: editor.isActive("heading", { level: 3 }), h4: editor.isActive("heading", { level: 4 }), paragraph: editor.isActive("paragraph") };
      root.querySelectorAll<HTMLButtonElement>("[data-command]").forEach(button => {
        const command = button.dataset.command ?? "";
        if (command in active) button.setAttribute("aria-pressed", String(active[command]));
        if (["addRow", "deleteRow", "addColumn", "deleteColumn", "deleteTable"].includes(command)) button.disabled = !editor.isActive("table");
        if (command === "undo") button.disabled = !editor.can().undo();
        if (command === "redo") button.disabled = !editor.can().redo();
      });
    };
    editor.on("selectionUpdate", updateToolbar);
    editor.on("transaction", updateToolbar);
    updateToolbar();
    form.addEventListener("submit", () => { input.value = JSON.stringify(editor.getJSON()); });
  } catch {
    fail("L’éditeur n’a pas pu être chargé. Rechargez la page ; le contenu enregistré reste conservé.");
    submitButtons.forEach(button => { button.disabled = true; });
  }
}
