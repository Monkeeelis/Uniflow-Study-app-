"""Flashcard decks and the review/quiz sessions that run over them."""

from __future__ import annotations

import datetime
import random
import uuid
from typing import Any

from uniflow.services import notes as notes_service
from uniflow.services.common import flag, set_feedback, text, toast

REVIEW_MODES = ("flashcards", "quiz")

# Lines like "Mitosis: cell division producing identical daughter cells" or
# "Mitosis - cell division..." become a card; anything without one of these
# separators is prose, not a term/definition pair, and gets skipped.
_PAIR_SEPARATORS = (":", " - ", " – ")
_MAX_GENERATED_CARDS = 30

EMPTY_CARD: dict[str, Any] = {
    "id": "",
    "front": "",
    "back": "",
    "times_reviewed": 0,
    "times_correct": 0,
    "interval_days": 0,
    "next_due": "",
}
EMPTY_DECK: dict[str, Any] = {"id": "", "name": "", "subject": "", "cards": []}


# Fresh card, review stats all zeroed out.
def _new_card(front: str, back: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "front": front,
        "back": back,
        "times_reviewed": 0,
        "times_correct": 0,
        "interval_days": 0,
        "next_due": "",
    }


# No due date means it's never been scheduled, so treat that as due too.
def _is_due(card: dict[str, Any], today: str) -> bool:
    due = card.get("next_due") or ""
    return due == "" or due <= today


def _reschedule(card: dict[str, Any], correct: bool) -> None:
    """Minimal spaced-repetition scheduler. Get it right and the gap before
    the card comes up again doubles (starting from 1 day); miss it and it's
    due again immediately - so cards you're shaky on keep showing up while
    the ones you know drift further and further apart."""
    today = datetime.date.today()
    if correct:
        card["interval_days"] = max(1, card.get("interval_days", 0) * 2)
        card["next_due"] = (today + datetime.timedelta(days=card["interval_days"])).isoformat()
    else:
        card["interval_days"] = 0
        card["next_due"] = today.isoformat()


# Resolves selected_deck_id to the actual deck, or None if nothing's selected.
def _deck(section: dict[str, Any]) -> dict[str, Any] | None:
    for deck in section["decks"]:
        if deck["id"] == section["selected_deck_id"]:
            return deck
    return None


# Finds a card by id inside a given deck.
def _card(deck: dict[str, Any] | None, card_id: str) -> dict[str, Any] | None:
    if deck is None:
        return None
    for card in deck["cards"]:
        if card["id"] == card_id:
            return card
    return None


# Whatever card the review cursor is sitting on right now; None once we're past the end.
def _current_card(section: dict[str, Any]) -> dict[str, Any] | None:
    review = section["review"]
    if review["index"] >= len(review["order"]):
        return None
    return _card(_deck(section), review["order"][review["index"]])


# Wipes the review dict back to its empty starting shape.
def _reset_review(section: dict[str, Any]) -> None:
    section["review"] = {
        "mode": "",
        "order": [],
        "index": 0,
        "flipped": False,
        "correct": 0,
        "incorrect": 0,
        "missed": [],
        "last_result": "",
        "finished": False,
    }


# Dismisses the feedback banner on this page.
def clear_feedback(data: dict[str, Any]) -> None:
    set_feedback(data["flashcards"], "", "")


# Show/hide the new-deck form.
def toggle_deck_form(data: dict[str, Any]) -> None:
    section = data["flashcards"]
    section["show_deck_form"] = not section["show_deck_form"]
    set_feedback(section, "", "")


# Makes an empty deck out of whatever the deck form submitted.
def create_deck(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str]:
    section = data["flashcards"]
    name = text(payload, "name")
    if not name:
        return toast("Please enter a deck name.", "warning")
    section["decks"].append(
        {
            "id": str(uuid.uuid4()),
            "name": name,
            "subject": text(payload, "subject"),
            "cards": [],
        }
    )
    section["show_deck_form"] = False
    set_feedback(section, f"Deck created: {name}", "success")
    return toast(f"Deck created: {name}", "success")


# Deletes by id. If it happened to be the selected deck, clears out the active review too.
def delete_deck(data: dict[str, Any], deck_id: str) -> dict[str, str] | None:
    section = data["flashcards"]
    removed = next((d for d in section["decks"] if d["id"] == deck_id), None)
    section["decks"] = [d for d in section["decks"] if d["id"] != deck_id]
    if section["selected_deck_id"] == deck_id:
        section["selected_deck_id"] = ""
        _reset_review(section)
    if removed is None:
        return None
    set_feedback(section, f"Deleted deck: {removed['name']}", "info")
    return toast(f"Deleted deck: {removed['name']}", "info")


# Switching decks kills whatever review was in progress, since it belonged to the old deck.
def select_deck(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["flashcards"]
    section["selected_deck_id"] = text(payload, "deck_id")
    section["show_card_form"] = False
    section["editing_card_id"] = ""
    _reset_review(section)


# Opens the card form, remembering which card (if any) is being edited; closing clears that.
def set_card_form(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["flashcards"]
    section["show_card_form"] = flag(payload, "open", True)
    section["editing_card_id"] = (
        text(payload, "card_id") if section["show_card_form"] else ""
    )


# Needs both sides filled in and an open deck; otherwise creates or overwrites the card being edited.
def submit_card(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str]:
    section = data["flashcards"]
    front = text(payload, "front")
    back = text(payload, "back")
    if not front or not back:
        section["show_card_form"] = True
        return toast("Please fill in both the question and the answer.", "warning")

    deck = _deck(section)
    if deck is None:
        return toast("Open a deck before adding cards.", "warning")

    editing_id = section["editing_card_id"]
    existing = _card(deck, editing_id) if editing_id else None
    if existing is not None:
        existing["front"] = front
        existing["back"] = back
    else:
        deck["cards"].append(_new_card(front, back))

    section["show_card_form"] = False
    section["editing_card_id"] = ""
    action = "updated" if existing is not None else "added"
    set_feedback(section, f"Card {action}.", "success")
    return toast(f"Card {action}.", "success")


# Deletes a card and patches up the active review session so it doesn't reference a dead card.
def delete_card(data: dict[str, Any], card_id: str) -> dict[str, str] | None:
    section = data["flashcards"]
    deck = _deck(section)
    if deck is None:
        return None
    removed = _card(deck, card_id)
    if removed is None:
        return None
    deck["cards"] = [c for c in deck["cards"] if c["id"] != card_id]

    review = section["review"]
    if card_id in review["order"]:
        review["order"] = [cid for cid in review["order"] if cid != card_id]
        if review["order"]:
            review["index"] = min(review["index"], len(review["order"]) - 1)
        else:
            _reset_review(section)

    label = removed["front"][:40] + ("…" if len(removed["front"]) > 40 else "")
    set_feedback(section, f"Deleted card: {label}", "info")
    return toast(f"Deleted card: {label}", "info")


# Scans lines for one of the _PAIR_SEPARATORS and splits into (term, definition) when found.
def _extract_pairs(lines: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in lines:
        for sep in _PAIR_SEPARATORS:
            if sep not in line:
                continue
            front, _, back = line.partition(sep)
            front, back = front.strip(" -–:"), back.strip(" -–:")
            if front and back and len(front) <= 200:
                pairs.append((front, back))
            break
    return pairs


def generate_from_note(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str]:
    """Scrape a note for "Term: Definition" lines and turn them into cards,
    filing them into a deck named after the note (creating it if needed)."""
    section = data["flashcards"]
    note_id = text(payload, "note_id")
    note = next((n for n in data["notes"]["items"] if n["id"] == note_id), None)
    if note is None:
        return toast("Note not found.", "warning")

    pairs = _extract_pairs(notes_service.plain_lines(note["content"]))
    if not pairs:
        return toast(
            'No "Term: Definition" style lines found to turn into flashcards.',
            "warning",
        )

    deck_name = note["title"] or note["subject"] or "General"
    deck = next((d for d in section["decks"] if d["name"] == deck_name), None)
    if deck is None:
        deck = {"id": str(uuid.uuid4()), "name": deck_name, "subject": note["subject"], "cards": []}
        section["decks"].append(deck)

    existing_fronts = {c["front"].lower() for c in deck["cards"]}
    created = 0
    for front, back in pairs[:_MAX_GENERATED_CARDS]:
        if front.lower() in existing_fronts:
            continue
        deck["cards"].append(_new_card(front, back))
        existing_fronts.add(front.lower())
        created += 1

    section["selected_deck_id"] = deck["id"]
    if created == 0:
        return toast("Those flashcards were already in the deck.", "info")
    set_feedback(section, f"Generated {created} flashcard(s) from \"{note['title']}\".", "success")
    return toast(f"Generated {created} flashcard(s) into \"{deck_name}\".", "success")


# --- review / quiz ---------------------------------------------------------


# Builds the shuffled queue for a session - due-only by default, but the
# caller can ask for just the missed cards or the whole deck instead.
def start_review(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["flashcards"]
    deck = _deck(section)
    if deck is None:
        return toast("Open a deck first.", "warning")
    if not deck["cards"]:
        return toast("Add a card to this deck first.", "warning")

    mode = text(payload, "mode")
    if mode not in REVIEW_MODES:
        mode = "flashcards"

    if flag(payload, "only_missed"):
        deck_card_ids = {c["id"] for c in deck["cards"]}
        missed = [cid for cid in section["review"]["missed"] if cid in deck_card_ids]
        if not missed:
            return toast("No missed cards to review.", "warning")
        order = missed
    elif flag(payload, "due_only"):
        today = datetime.date.today().isoformat()
        order = [c["id"] for c in deck["cards"] if _is_due(c, today)]
        if not order:
            return toast("No cards due for review right now — try Review all.", "info")
    else:
        order = [c["id"] for c in deck["cards"]]
    random.shuffle(order)

    _reset_review(section)
    section["review"].update({"mode": mode, "order": order})
    return None


# Just flips the flipped flag on the current card.
def flip_card(data: dict[str, Any]) -> None:
    review = data["flashcards"]["review"]
    review["flipped"] = not review["flipped"]


def mark_result(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Flashcards mode - just takes the user's own word for whether they knew it."""
    section = data["flashcards"]
    card = _current_card(section)
    if card is None:
        return
    correct = flag(payload, "correct")
    card["times_reviewed"] += 1
    _reschedule(card, correct)
    if correct:
        card["times_correct"] += 1
        section["review"]["correct"] += 1
    else:
        section["review"]["incorrect"] += 1
        section["review"]["missed"].append(card["id"])
    _advance(section)


def submit_answer(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Quiz mode - compares the typed answer to the card's back, ignoring case."""
    section = data["flashcards"]
    review = section["review"]
    card = _current_card(section)
    if card is None or review["last_result"]:
        # Already graded this card — ignore a duplicate/late submit.
        return
    correct = text(payload, "answer").lower() == card["back"].strip().lower()
    card["times_reviewed"] += 1
    _reschedule(card, correct)
    if correct:
        card["times_correct"] += 1
        review["correct"] += 1
        review["last_result"] = "correct"
    else:
        review["incorrect"] += 1
        review["last_result"] = "incorrect"
        review["missed"].append(card["id"])


# Resets last_result and advances the cursor.
def next_card(data: dict[str, Any]) -> None:
    section = data["flashcards"]
    section["review"]["last_result"] = ""
    _advance(section)


# Bails out of whatever session is running.
def exit_review(data: dict[str, Any]) -> None:
    _reset_review(data["flashcards"])


# Steps the cursor forward one card; flags the session finished once we run out.
def _advance(section: dict[str, Any]) -> None:
    review = section["review"]
    review["flipped"] = False
    if review["index"] + 1 >= len(review["order"]):
        review["finished"] = True
    else:
        review["index"] += 1


# --- computed values -------------------------------------------------------


# Flashcards page view-model - decks, whichever one's selected, and the state of any active review.
def view(data: dict[str, Any]) -> dict[str, Any]:
    section = data["flashcards"]
    review = section["review"]
    deck = _deck(section)
    answered = review["correct"] + review["incorrect"]
    current = _current_card(section)
    today = datetime.date.today().isoformat()

    return {
        "decks": section["decks"],
        "deck_summaries": [
            {
                "id": d["id"],
                "name": d["name"],
                "subject": d["subject"],
                "count": len(d["cards"]),
                "due_count": sum(1 for c in d["cards"] if _is_due(c, today)),
            }
            for d in section["decks"]
        ],
        "selected_deck_id": section["selected_deck_id"],
        "selected_deck": deck if deck is not None else dict(EMPTY_DECK),
        "due_count": sum(1 for c in deck["cards"] if _is_due(c, today)) if deck else 0,
        "show_deck_form": section["show_deck_form"],
        "show_card_form": section["show_card_form"],
        "editing_card_id": section["editing_card_id"],
        "editing_card": _card(deck, section["editing_card_id"]) or dict(EMPTY_CARD),
        "review": {
            "mode": review["mode"],
            "index": review["index"],
            "total": len(review["order"]),
            "flipped": review["flipped"],
            "correct": review["correct"],
            "incorrect": review["incorrect"],
            "missed_count": len(review["missed"]),
            "last_result": review["last_result"],
            "finished": review["finished"],
            "score_percent": (
                int(review["correct"] / answered * 100) if answered else 0
            ),
            "current_card": current if current is not None else dict(EMPTY_CARD),
        },
        "feedback": section["feedback"],
    }
