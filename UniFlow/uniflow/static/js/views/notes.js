// Notes page: a small document editor, not another card grid. A VS Code-style
// explorer sidebar (subjects as expandable folders, notes as files) picks
// what you're studying; the main pane is a paper-styled document with a
// floating bold/italic/underline/highlight toolbar and adjustable font.
// Edits stay in the browser (like every other form in the app) until "Save"
// — nothing is sent per keystroke.

import { h } from "../dom.js";
import { icon } from "../icons.js";
import { act } from "../state.js";
import { banner, emptyState, selectField } from "../ui.js";

function fileItem(note, selectedId) {
  return h(
    "button",
    {
      class: ["notebook-file", note.id === selectedId && "is-active"],
      onClick: () => act("notes/select", { note_id: note.id }),
    },
    icon("file-text", "icon-xs"),
    h("span", { class: "notebook-file-title" }, note.title),
    note.pinned ? icon("pin", "icon-xs") : null,
  );
}

function folderGroup(group, selectedId) {
  return h(
    "div",
    {},
    h(
      "button",
      {
        class: "notebook-item",
        onClick: () => act("notes/folder/toggle", { subject: group.subject }),
      },
      icon(group.expanded ? "chevron-down" : "chevron-right", "icon-xs"),
      icon(group.expanded ? "folder-open" : "folder", "icon-sm"),
      h("span", { class: "grow" }, group.subject),
      h("span", { class: "notebook-count" }, String(group.notes.length)),
    ),
    group.expanded
      ? h("div", { class: "notebook-files" }, group.notes.map((n) => fileItem(n, selectedId)))
      : null,
  );
}

function searchResultsList(notes) {
  return h(
    "div",
    { class: "notebook-files notebook-files-flat" },
    notes.search_results.length
      ? notes.search_results.map((n) => fileItem(n, notes.selected_note_id))
      : h("p", { class: "p tiny notes-sidebar-muted" }, "No matches."),
  );
}

async function importNoteFile(file) {
  if (!file) return;
  const raw = await file.text();
  const title = file.name.replace(/\.(md|markdown|txt)$/i, "") || "Imported note";
  await act("notes/new");
  await act("notes/save", { title, subject: "", tags: "", content: markdownToHtml(raw) });
}

function sidebar(notes) {
  const searchInput = h("input", {
    class: "input input-sm mb-3",
    placeholder: "Search notes... (Enter)",
    value: notes.search,
    onKeyDown: (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        act("notes/view", { search: event.target.value });
      }
    },
    onBlur: (event) => act("notes/view", { search: event.target.value }),
  });

  const importInput = h("input", {
    type: "file",
    accept: ".md,.markdown,.txt",
    style: { display: "none" },
    onChange: (event) => {
      importNoteFile(event.target.files[0]);
      event.target.value = "";
    },
  });

  return h(
    "aside",
    { class: "notes-sidebar" },
    h(
      "div",
      { class: "row-between mb-3" },
      h("p", { class: "notes-sidebar-title" }, "My Notebooks"),
      h(
        "div",
        { class: "row", style: { gap: "4px" } },
        importInput,
        h(
          "button",
          {
            class: "notebook-add",
            "aria-label": "Import a Markdown or text note",
            title: "Import a Markdown or text note",
            onClick: () => importInput.click(),
          },
          icon("upload", "icon-sm"),
        ),
        h(
          "button",
          { class: "notebook-add", "aria-label": "New note", onClick: () => act("notes/new") },
          icon("plus", "icon-sm"),
        ),
      ),
    ),
    searchInput,
    h(
      "div",
      { class: "notebook-tree" },
      notes.search
        ? searchResultsList(notes)
        : notes.tree.length
          ? notes.tree.map((group) => folderGroup(group, notes.selected_note_id))
          : h("p", { class: "p tiny notes-sidebar-muted" }, "No notes yet — hit + to write one."),
    ),
  );
}

function breadcrumb(note) {
  return h(
    "div",
    { class: "notes-breadcrumb" },
    h("span", {}, "Notebooks"),
    icon("chevron-right", "icon-xs"),
    h("span", {}, note.subject || "Unfiled"),
    icon("chevron-right", "icon-xs"),
    h("span", { class: "is-current" }, note.title),
  );
}

function toolbarButton(iconName, label, command, value) {
  return h(
    "button",
    {
      class: "editor-tool",
      type: "button",
      "aria-label": label,
      title: label,
      // Keep the contenteditable's text selection alive through the click.
      onMouseDown: (event) => event.preventDefault(),
      onClick: () => document.execCommand(command, false, value),
    },
    icon(iconName, "icon-sm"),
  );
}

// document.execCommand("hiliteColor") is unreliable for reading back
// whether the selection is already highlighted (queryCommandValue support
// is inconsistent across browsers), so highlighting is done by hand with
// real <mark> elements instead: wrap the selection in one to highlight,
// or unwrap an ancestor <mark> to remove it. This makes "click again to
// un-highlight" work every time instead of only when the browser's query
// happens to agree the text is highlighted.
function unwrapMark(mark) {
  const parent = mark.parentNode;
  while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
  parent.removeChild(mark);
}

function toggleHighlight() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return;
  const range = selection.getRangeAt(0);

  const startMark = range.startContainer.nodeType === 3
    ? range.startContainer.parentElement?.closest("mark")
    : range.startContainer.closest?.("mark");
  if (startMark) {
    unwrapMark(startMark);
    return;
  }

  // No inline colour here — .notes-doc mark in styles.css derives the
  // highlight from the current theme's own --accent/--panel/--ink, so it
  // stays readable (and on-theme) in both light and dark mode instead of
  // painting a fixed light-yellow that goes illegible on a dark background.
  const mark = document.createElement("mark");
  try {
    range.surroundContents(mark);
  } catch {
    // Selection crosses element boundaries (e.g. spans two paragraphs),
    // so a single surroundContents() would fail — extract then rewrap.
    const content = range.extractContents();
    mark.appendChild(content);
    range.insertNode(mark);
  }
  selection.removeAllRanges();
  const after = document.createRange();
  after.selectNodeContents(mark);
  selection.addRange(after);
}

function highlightButton() {
  return h(
    "button",
    {
      class: "editor-tool",
      type: "button",
      "aria-label": "Highlight",
      title: "Highlight",
      onMouseDown: (event) => event.preventDefault(),
      onClick: toggleHighlight,
    },
    icon("highlighter", "icon-sm"),
  );
}

function fontControls(notes) {
  return h(
    "div",
    { class: "row", style: { gap: "8px" } },
    selectField({
      value: notes.font_family,
      options: notes.font_family_options,
      small: true,
      onChange: (value) => act("notes/font", { font_family: value }),
    }),
    selectField({
      value: notes.font_size,
      options: notes.font_size_options,
      small: true,
      onChange: (value) => act("notes/font", { font_size: value }),
    }),
  );
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function downloadNote(note) {
  const plain = note.title + "\n\n" + note.content.replace(/<[^>]+>/g, "");
  downloadFile(`${note.title || "note"}.txt`, plain, "text/plain");
}

// Only handles the tags sanitize_body already lets through (bold/italic/
// underline/highlight/paragraphs), which is all a note can ever contain.
function htmlToMarkdown(bodyHtml) {
  const withMarkup = bodyHtml
    .replace(/<(strong|b)>(.*?)<\/\1>/gis, "**$2**")
    .replace(/<(em|i)>(.*?)<\/\1>/gis, "*$2*")
    .replace(/<u>(.*?)<\/u>/gis, "_$1_")
    .replace(/<mark[^>]*>(.*?)<\/mark>/gis, "==$1==")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(p|div|li)>/gi, "\n")
    .replace(/<[^>]+>/g, "");
  const unescaper = document.createElement("textarea");
  unescaper.innerHTML = withMarkup;
  return unescaper.value.replace(/\n{3,}/g, "\n\n").trim();
}

function downloadMarkdown(note) {
  const md = `# ${note.title || "Untitled note"}\n\n${htmlToMarkdown(note.content)}`;
  downloadFile(`${note.title || "note"}.md`, md, "text/markdown");
}

// The reverse of htmlToMarkdown, for files brought in via Import. Escapes
// first so any stray HTML in the source file can't sneak through.
function markdownToHtml(md) {
  const escaped = md.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const withMarkup = escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+?)\*(?!\*)/g, "$1<em>$2</em>")
    .replace(/__(.+?)__/g, "<u>$1</u>");
  return withMarkup
    .split("\n")
    .map((line) => line || "<br>")
    .join("<br>");
}

const NEW_SUBJECT_VALUE = "__new_subject__";

async function saveSelectionAsFlashcard(note, flashcards) {
  const selection = window.getSelection().toString().trim();
  const front = selection || window.prompt("Flashcard question (front):", "");
  if (!front) return;
  const back = window.prompt(`Answer for:\n"${front}"`, "");
  if (!back) return;

  const deckName = note.subject || "General";
  let deck = flashcards.deck_summaries.find((d) => d.name === deckName);
  if (!deck) {
    const res = await act("flashcards/decks/create", { name: deckName, subject: note.subject });
    deck = res?.state?.flashcards?.deck_summaries.find((d) => d.name === deckName);
    if (!deck) return;
  }

  const previousDeckId = flashcards.selected_deck_id;
  await act("flashcards/decks/select", { deck_id: deck.id });
  await act("flashcards/cards/save", { front, back });
  if (previousDeckId) await act("flashcards/decks/select", { deck_id: previousDeckId });
}

function editorPane(notes, onboarding, flashcards) {
  const note = notes.selected_note;

  if (!note.id) {
    return h(
      "div",
      { class: "notes-editor" },
      emptyState("file-text", "Select a note on the left, or start a new one."),
    );
  }

  const titleInput = h("input", {
    class: "notes-title-input",
    value: note.title,
    placeholder: "Untitled note",
    onInput: () => scheduleSave(),
    onBlur: () => flushSave(),
  });
  let currentSubject = note.subject;
  const subjectSelect = selectField({
    value: currentSubject,
    small: true,
    options: [
      { value: "", label: "No subject" },
      ...onboarding.subjects.map((s) => ({ value: s, label: s })),
      { value: NEW_SUBJECT_VALUE, label: "+ Add new subject..." },
    ],
    onChange: async (value) => {
      if (value !== NEW_SUBJECT_VALUE) {
        currentSubject = value;
        save();
        return;
      }
      const name = window.prompt("New subject name")?.trim();
      if (!name) {
        subjectSelect.querySelector("select").value = currentSubject;
        return;
      }
      currentSubject = name;
      await act("onboarding/subjects/add", { name });
      save();
    },
  });
  const tagsInput = h("input", {
    class: "input input-sm notes-tags-input",
    value: (note.tags || []).join(", "),
    placeholder: "Tags (comma separated)",
    onInput: () => scheduleSave(),
    onBlur: () => flushSave(),
  });
  const body = h("div", {
    class: "notes-doc",
    style: { "--notes-font-family": notes.font_family_css, "--notes-font-size": notes.font_size_css },
    contentEditable: "true",
    "data-placeholder": "Start writing...",
    onKeyDown: (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        flushSave();
      }
    },
    onInput: () => scheduleSave(),
    onBlur: () => flushSave(),
  });
  body.innerHTML = note.content || "";

  const save = () =>
    act("notes/save", {
      title: titleInput.value,
      subject: currentSubject,
      tags: tagsInput.value,
      content: body.innerHTML,
    });

  // Autosave shortly after the user stops typing, so switching pages or
  // toggling the theme — both of which re-render the whole app from the
  // server's saved copy — never silently discards in-progress edits.
  let saveTimer = null;
  const scheduleSave = () => {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(save, 800);
  };
  const flushSave = () => {
    clearTimeout(saveTimer);
    saveTimer = null;
    save();
  };

  return h(
    "div",
    { class: "notes-editor" },
    breadcrumb(note),
    h(
      "div",
      { class: "row-between mt-3", style: { gap: "12px", flexWrap: "wrap" } },
      titleInput,
      h(
        "div",
        { class: "row", style: { gap: "8px", flex: "none" } },
        h(
          "button",
          {
            class: "icon-btn",
            "aria-label": "Download as .txt",
            onClick: () => downloadNote(note),
          },
          icon("download", "icon-sm"),
        ),
        h(
          "button",
          {
            class: "icon-btn",
            "aria-label": "Export as Markdown",
            title: "Export as Markdown (.md)",
            onClick: () => downloadMarkdown(note),
          },
          icon("file-text", "icon-sm"),
        ),
        h(
          "button",
          {
            class: "icon-btn",
            "aria-label": "Save selected text as a flashcard",
            title: "Save selected text as a flashcard",
            onClick: () => saveSelectionAsFlashcard(note, flashcards),
          },
          icon("layers", "icon-sm"),
        ),
        h(
          "button",
          {
            class: "icon-btn",
            "aria-label": "Auto-generate flashcards from this note",
            title: 'Auto-generate flashcards from "Term: Definition" lines',
            onClick: async () => {
              await save();
              await act("flashcards/generate-from-note", { note_id: note.id });
            },
          },
          icon("sparkles", "icon-sm"),
        ),
        h(
          "button",
          {
            class: "icon-btn",
            "aria-label": note.pinned ? "Unpin note" : "Pin note",
            onClick: () => act("notes/pin", { note_id: note.id }),
          },
          icon("pin", "icon-sm"),
        ),
        h(
          "button",
          {
            class: "icon-btn icon-btn-danger",
            "aria-label": "Delete note",
            onClick: () => act("notes/delete", { note_id: note.id }),
          },
          icon("trash-2", "icon-sm"),
        ),
      ),
    ),
    h(
      "div",
      { class: "row mt-1 mb-4", style: { gap: "12px", flexWrap: "wrap", alignItems: "center" } },
      subjectSelect,
      tagsInput,
      h("p", { class: "p tiny muted mono" }, `${notes.word_count} words · updated ${note.updated_at}`),
    ),
    body,
    h(
      "div",
      { class: "notes-toolbar-wrap" },
      h(
        "div",
        { class: "editor-toolbar" },
        toolbarButton("bold", "Bold", "bold"),
        toolbarButton("italic", "Italic", "italic"),
        toolbarButton("underline", "Underline", "underline"),
        h("span", { class: "editor-tool-divider" }),
        highlightButton(),
      ),
      fontControls(notes),
      h(
        "button",
        { class: "btn btn-primary btn-sm", onClick: save, title: "Save (Ctrl+S)" },
        icon("check", "icon-sm"),
        "Save",
      ),
    ),
  );
}

export function notesPage(state) {
  const { notes, onboarding, flashcards } = state;
  const feedback = banner(notes.feedback);

  return h(
    "div",
    {},
    feedback && h("div", { class: "mb-4" }, feedback),
    h("div", { class: "notes-layout" }, sidebar(notes), editorPane(notes, onboarding, flashcards)),
  );
}
