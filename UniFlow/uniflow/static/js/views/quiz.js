// Quiz & Cards page. One route, four states picked by quizPage() at the
// bottom: deck list -> deck detail -> (flashcard review | quiz) -> finished.
// Which state is active lives entirely in `state.flashcards` (selected deck,
// review mode, finished flag) — this file has no local view state of its own.

import { h } from "../dom.js";
import { icon } from "../icons.js";
import { act } from "../state.js";
import { banner, emptyState, modal } from "../ui.js";

function deckForm() {
  const nameInput = h("input", { class: "input mb-2", placeholder: "Deck name", autofocus: true });
  const subjectInput = h("input", { class: "input mb-3", placeholder: "Subject (optional)" });
  const create = () =>
    act("flashcards/decks/create", { name: nameInput.value, subject: subjectInput.value });

  nameInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      create();
    }
  });

  return h(
    "div",
    { class: "card card-lg mb-6" },
    h("h2", { class: "h3 mb-3" }, "Create a deck"),
    nameInput,
    subjectInput,
    h(
      "div",
      { class: "row", style: { gap: "12px" } },
      h("button", { class: "btn btn-outline btn-flex", onClick: () => act("flashcards/deck-form") }, "Cancel"),
      h("button", { class: "btn btn-primary btn-flex", onClick: create }, "Create"),
    ),
  );
}

function deckCard(deck) {
  return h(
    "div",
    { class: "deck-card" },
    h(
      "button",
      { class: "deck-open", onClick: () => act("flashcards/decks/select", { deck_id: deck.id }) },
      h(
        "div",
        { class: "row-between deck-head mb-3", style: { gap: "8px" } },
        icon("layers", "icon-lg"),
        h("span", { class: "tiny muted mono", style: { fontWeight: "700" } }, `${deck.count} cards`),
      ),
      h("p", { class: "p deck-name" }, deck.name),
      deck.subject ? h("p", { class: "p badge badge-subject mt-2" }, deck.subject) : null,
    ),
    h(
      "button",
      {
        class: "icon-btn icon-btn-danger deck-delete",
        "aria-label": `Delete ${deck.name}`,
        onClick: () => act("flashcards/decks/delete", { deck_id: deck.id }),
      },
      icon("trash-2", "icon-sm"),
    ),
  );
}

function deckListView(flashcards) {
  return h(
    "div",
    {},
    h(
      "div",
      { class: "row-between mb-6" },
      h(
        "div",
        {},
        h("h1", { class: "h1" }, "Quiz & Cards"),
        h("p", { class: "p muted mt-2" }, "Create flashcards and quiz yourself."),
      ),
      h(
        "button",
        { class: "btn btn-primary", onClick: () => act("flashcards/deck-form") },
        icon("plus"),
        "New Deck",
      ),
    ),
    flashcards.show_deck_form ? deckForm() : null,
    flashcards.deck_summaries.length
      ? h("div", { class: "grid grid-1-2 grid-lg-3" }, flashcards.deck_summaries.map(deckCard))
      : emptyState("layers", "No decks yet. Create one to start studying!"),
  );
}

function cardRow(card) {
  return h(
    "div",
    { class: "task-row" },
    h(
      "div",
      { class: "grow" },
      h("p", { class: "p", style: { fontWeight: "600", color: "var(--heading)" } }, card.front),
      h("p", { class: "p small muted mt-2" }, card.back),
      h(
        "p",
        { class: "p tiny muted mono mt-2" },
        `Reviewed ${card.times_reviewed} × · ${card.times_correct} correct`,
      ),
    ),
    h(
      "div",
      { class: "row", style: { gap: "4px", flex: "none" } },
      h(
        "button",
        {
          class: "icon-btn",
          "aria-label": "Edit card",
          onClick: () => act("flashcards/card-form", { open: true, card_id: card.id }),
        },
        icon("pencil", "icon-sm"),
      ),
      h(
        "button",
        {
          class: "icon-btn icon-btn-danger",
          "aria-label": "Delete card",
          onClick: () => act("flashcards/cards/delete", { card_id: card.id }),
        },
        icon("trash-2", "icon-sm"),
      ),
    ),
  );
}

function cardFormModal(flashcards) {
  if (!flashcards.show_card_form) return null;
  const editing = flashcards.editing_card;

  return modal({
    title: flashcards.editing_card_id ? "Edit Card" : "New Card",
    onClose: () => act("flashcards/card-form", { open: false }),
    onSubmit: (form) => act("flashcards/cards/save", form),
    children: h(
      "div",
      {},
      h("label", { class: "label", for: "card-front" }, "Front (question)"),
      h("textarea", { class: "textarea mb-4", id: "card-front", name: "front", rows: "2", autofocus: true }, editing.front),
      h("label", { class: "label", for: "card-back" }, "Back (answer)"),
      h("textarea", { class: "textarea mb-6", id: "card-back", name: "back", rows: "2" }, editing.back),
    ),
    footer: h(
      "div",
      { class: "row", style: { gap: "12px" } },
      h(
        "button",
        { class: "btn btn-outline btn-flex", type: "button", onClick: () => act("flashcards/card-form", { open: false }) },
        "Cancel",
      ),
      h("button", { class: "btn btn-primary btn-flex", type: "submit" }, "Save"),
    ),
  });
}

function deckDetailView(flashcards) {
  const deck = flashcards.selected_deck;
  return h(
    "div",
    {},
    h(
      "button",
      { class: "ghost-link mb-4", onClick: () => act("flashcards/decks/select", { deck_id: "" }) },
      icon("arrow-left", "icon-sm"),
      "Back to decks",
    ),
    h(
      "div",
      { class: "row-between mb-6" },
      h(
        "div",
        {},
        h("h1", { class: "h1 display-lg" }, deck.name),
        deck.subject ? h("p", { class: "p small muted" }, deck.subject) : null,
      ),
      h(
        "div",
        { class: "row row-wrap" },
        h(
          "button",
          {
            class: "btn btn-teal-outline",
            onClick: () => act("flashcards/review/start", { mode: "flashcards" }),
          },
          icon("book-open", "icon-sm"),
          "Review",
        ),
        h(
          "button",
          { class: "btn btn-primary", onClick: () => act("flashcards/review/start", { mode: "quiz" }) },
          icon("check-check", "icon-sm"),
          "Quiz",
        ),
        h(
          "button",
          { class: "btn btn-outline", onClick: () => act("flashcards/card-form", { open: true }) },
          icon("plus", "icon-sm"),
          "Add",
        ),
      ),
    ),
    deck.cards.length
      ? h("div", { class: "stack" }, deck.cards.map(cardRow))
      : emptyState("square-stack", "No cards in this deck. Add one to get started!"),
    cardFormModal(flashcards),
  );
}

function reviewHeader(review, { label, exitLabel }) {
  return h(
    "div",
    {},
    h(
      "button",
      { class: "ghost-link mb-4", onClick: () => act("flashcards/review/exit") },
      icon("x", "icon-sm"),
      exitLabel,
    ),
    h("p", { class: "p small muted mono center mb-1" }, `${label} ${review.index + 1} of ${review.total}`),
    h(
      "div",
      { class: "row mb-4", style: { justifyContent: "center" } },
      h("span", { class: "badge badge-score-good" }, `✓ ${review.correct}`),
      h("span", { class: "badge badge-score-bad" }, `✗ ${review.incorrect}`),
    ),
  );
}

function reviewFlashcardView(flashcards) {
  const review = flashcards.review;
  const card = review.current_card;
  const progress = review.total ? ((review.index + 1) * 100) / review.total : 0;

  return h(
    "div",
    {},
    reviewHeader(review, { label: "Card", exitLabel: "End review" }),
    h("div", { class: "progress" }, h("div", { class: "progress-bar", style: { width: `${progress}%` } })),
    h(
      "button",
      { class: ["flashcard", review.flipped && "is-flipped"], onClick: () => act("flashcards/review/flip") },
      h(
        "div",
        {},
        h(
          "div",
          { class: "flashcard-kind" },
          icon(review.flipped ? "lightbulb" : "circle-help", "icon-sm"),
          h("span", {}, review.flipped ? "Answer" : "Question"),
        ),
        h("p", { class: "p flashcard-face" }, review.flipped ? card.back : card.front),
        h(
          "div",
          { class: "row mt-6", style: { justifyContent: "center", gap: "4px" } },
          icon("refresh-cw", "icon-xs"),
          h("span", { class: "tiny muted mono" }, "Tap to flip"),
        ),
      ),
    ),
    h(
      "div",
      { class: "row mt-6", style: { gap: "12px" } },
      h(
        "button",
        {
          class: "btn btn-lg btn-danger-outline btn-flex",
          onClick: () => act("flashcards/review/mark", { correct: false }),
        },
        icon("x"),
        "Didn't know",
      ),
      h(
        "button",
        { class: "btn btn-lg btn-teal btn-flex", onClick: () => act("flashcards/review/mark", { correct: true }) },
        icon("check"),
        "Knew it",
      ),
    ),
  );
}

function reviewQuizView(flashcards) {
  const review = flashcards.review;
  const card = review.current_card;

  const answerInput = h("input", {
    class: "input mb-3",
    placeholder: "Your answer...",
    autofocus: true,
    onKeyDown: (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        submit();
      }
    },
  });
  const submit = () => act("flashcards/review/answer", { answer: answerInput.value });

  return h(
    "div",
    {},
    reviewHeader(review, { label: "Question", exitLabel: "End quiz" }),
    h(
      "div",
      { class: "question-card mb-4" },
      h(
        "div",
        { class: "flashcard-kind", style: { justifyContent: "flex-start" } },
        icon("circle-help", "icon-sm"),
        h("span", {}, "Question"),
      ),
      h("p", { class: "p flashcard-face", style: { fontSize: "1.5rem" } }, card.front),
    ),
    review.last_result === ""
      ? h(
          "div",
          {},
          answerInput,
          h("button", { class: "btn btn-lg btn-primary btn-block", onClick: submit }, "Submit"),
        )
      : h(
          "div",
          {},
          review.last_result === "correct"
            ? h(
                "div",
                { class: "result-good" },
                icon("circle-check", "icon-lg"),
                h("p", { class: "p", style: { fontWeight: "700" } }, "Correct!"),
              )
            : h(
                "div",
                { class: "result-bad" },
                icon("circle-x", "icon-lg"),
                h(
                  "div",
                  {},
                  h("p", { class: "p", style: { fontWeight: "700" } }, "Not quite."),
                  h("p", { class: "p small", style: { color: "var(--heading)" } }, `Correct answer: ${card.back}`),
                ),
              ),
          h(
            "button",
            { class: "btn btn-lg btn-primary btn-block mt-4", onClick: () => act("flashcards/review/next") },
            "Next",
            icon("arrow-right", "icon-sm"),
          ),
        ),
  );
}

function reviewFinishedView(flashcards) {
  const review = flashcards.review;
  return h(
    "div",
    { class: "card", style: { maxWidth: "448px", margin: "0 auto", borderRadius: "var(--r-xl)", padding: "32px" } },
    h("div", { class: "row", style: { justifyContent: "center", marginBottom: "16px", color: "var(--accent)" } },
      icon("trophy", "icon-hero")),
    h("h2", { class: "h1 center mb-2" }, "All done!"),
    h(
      "p",
      { class: "p muted center mb-6" },
      `You got ${review.correct} out of ${review.total} correct.`,
    ),
    h(
      "div",
      { class: "mb-8" },
      h("p", { class: "p score-big" }, `${review.score_percent}%`),
      h("p", { class: "p eyebrow center" }, "Score"),
    ),
    h(
      "div",
      { class: "row", style: { gap: "12px" } },
      h(
        "button",
        {
          class: "btn btn-primary btn-flex",
          onClick: () => act("flashcards/review/start", { mode: review.mode }),
        },
        "Review again",
      ),
      h("button", { class: "btn btn-outline btn-flex", onClick: () => act("flashcards/review/exit") }, "Back to deck"),
    ),
    review.missed_count
      ? h(
          "button",
          {
            class: "btn btn-teal-outline btn-block mt-3",
            onClick: () => act("flashcards/review/start", { mode: review.mode, only_missed: true }),
          },
          icon("rotate-ccw", "icon-sm"),
          `Review ${review.missed_count} missed card${review.missed_count === 1 ? "" : "s"}`,
        )
      : null,
  );
}

export function quizPage(state) {
  const { flashcards } = state;
  const feedback = banner(flashcards.feedback);
  const review = flashcards.review;

  let body;
  if (!flashcards.selected_deck_id) body = deckListView(flashcards);
  else if (review.finished) body = reviewFinishedView(flashcards);
  else if (review.mode === "flashcards") body = reviewFlashcardView(flashcards);
  else if (review.mode === "quiz") body = reviewQuizView(flashcards);
  else body = deckDetailView(flashcards);

  return h("div", {}, feedback && h("div", { class: "mb-4" }, feedback), body);
}
