import reflex as rx
from typing import TypedDict
import uuid
import random


class Flashcard(TypedDict):
    id: str
    front: str
    back: str
    times_reviewed: int
    times_correct: int


class Deck(TypedDict):
    id: str
    name: str
    subject: str
    cards: list[Flashcard]


class FlashcardState(rx.State):
    decks: list[Deck] = []
    selected_deck_id: str = ""
    show_deck_form: bool = False
    show_card_form: bool = False
    editing_card_id: str = ""

    new_deck_name: str = ""
    new_deck_subject: str = ""

    review_mode: str = ""
    review_index: int = 0
    review_flipped: bool = False
    review_order: list[str] = []
    review_correct: int = 0
    review_incorrect: int = 0
    review_answer_input: str = ""
    review_last_result: str = ""
    review_finished: bool = False

    feedback_message: str = ""
    feedback_kind: str = ""

    def _set_feedback(self, message: str, kind: str = "info"):
        self.feedback_message = message
        self.feedback_kind = kind

    @rx.event
    def clear_feedback(self):
        self.feedback_message = ""
        self.feedback_kind = ""

    @rx.event
    def toggle_deck_form(self):
        self.show_deck_form = not self.show_deck_form
        self.new_deck_name = ""
        self.new_deck_subject = ""
        self.feedback_message = ""
        self.feedback_kind = ""

    @rx.event
    def set_new_deck_name(self, v: str):
        self.new_deck_name = v

    @rx.event
    def set_new_deck_subject(self, v: str):
        self.new_deck_subject = v

    @rx.event
    def create_deck(self):
        name = self.new_deck_name.strip()
        if not name:
            return rx.toast(
                "Please enter a deck name.",
                duration=2500,
                close_button=True,
            )
        self.decks.append(
            Deck(
                id=str(uuid.uuid4()),
                name=name,
                subject=self.new_deck_subject.strip(),
                cards=[],
            )
        )
        self.new_deck_name = ""
        self.new_deck_subject = ""
        self.show_deck_form = False
        self._set_feedback(f"Deck created: {name}", "success")
        return rx.toast(
            f"Deck created: {name}",
            duration=2500,
            close_button=True,
        )

    @rx.event
    def delete_deck(self, deck_id: str):
        removed = next((d for d in self.decks if d["id"] == deck_id), None)
        self.decks = [d for d in self.decks if d["id"] != deck_id]
        if self.selected_deck_id == deck_id:
            self.selected_deck_id = ""
        if removed is not None:
            self._set_feedback(f"Deleted deck: {removed['name']}", "info")
            return rx.toast(
                f"Deleted deck: {removed['name']}",
                duration=2500,
                close_button=True,
            )

    @rx.event
    def select_deck(self, deck_id: str):
        self.selected_deck_id = deck_id
        self.review_mode = ""
        self.review_finished = False

    @rx.event
    def back_to_decks(self):
        self.selected_deck_id = ""
        self.review_mode = ""

    @rx.event
    def toggle_card_form(self):
        self.show_card_form = not self.show_card_form
        self.editing_card_id = ""

    @rx.event
    def open_edit_card(self, card_id: str):
        self.editing_card_id = card_id
        self.show_card_form = True

    @rx.event
    def close_card_form(self):
        self.show_card_form = False
        self.editing_card_id = ""

    @rx.event
    def submit_card(self, form_data: dict):
        front = form_data.get("front", "").strip()
        back = form_data.get("back", "").strip()
        if not front or not back:
            return rx.toast(
                "Please fill in both the question and the answer.",
                duration=2500,
                close_button=True,
            )
        was_editing = bool(self.editing_card_id)
        for i, d in enumerate(self.decks):
            if d["id"] == self.selected_deck_id:
                if self.editing_card_id:
                    for j, c in enumerate(d["cards"]):
                        if c["id"] == self.editing_card_id:
                            self.decks[i]["cards"][j]["front"] = front
                            self.decks[i]["cards"][j]["back"] = back
                            break
                else:
                    self.decks[i]["cards"].append(
                        Flashcard(
                            id=str(uuid.uuid4()),
                            front=front,
                            back=back,
                            times_reviewed=0,
                            times_correct=0,
                        )
                    )
                break
        self.show_card_form = False
        self.editing_card_id = ""
        self._set_feedback(
            f"Card {'updated' if was_editing else 'added'}.", "success"
        )
        return rx.toast(
            f"Card {'updated' if was_editing else 'added'}.",
            duration=2500,
            close_button=True,
        )

    @rx.event
    def delete_card(self, card_id: str):
        removed_front = ""
        for i, d in enumerate(self.decks):
            if d["id"] == self.selected_deck_id:
                for c in d["cards"]:
                    if c["id"] == card_id:
                        removed_front = c["front"]
                        break
                self.decks[i]["cards"] = [
                    c for c in d["cards"] if c["id"] != card_id
                ]
                break
        if removed_front:
            short = removed_front[:40] + (
                "…" if len(removed_front) > 40 else ""
            )
            self._set_feedback(f"Deleted card: {short}", "info")
            return rx.toast(
                f"Deleted card: {short}",
                duration=2500,
                close_button=True,
            )

    @rx.event
    async def start_review(self, mode: str):
        for d in self.decks:
            if d["id"] == self.selected_deck_id:
                if not d["cards"]:
                    return
                ids = [c["id"] for c in d["cards"]]
                random.shuffle(ids)
                self.review_order = ids
                self.review_mode = mode
                self.review_index = 0
                self.review_flipped = False
                self.review_correct = 0
                self.review_incorrect = 0
                self.review_answer_input = ""
                self.review_last_result = ""
                self.review_finished = False
                break

    @rx.event
    def flip_card(self):
        self.review_flipped = not self.review_flipped

    @rx.event
    async def mark_result(self, correct: bool):
        current_id = self.review_order[self.review_index]
        for i, d in enumerate(self.decks):
            if d["id"] == self.selected_deck_id:
                for j, c in enumerate(d["cards"]):
                    if c["id"] == current_id:
                        self.decks[i]["cards"][j]["times_reviewed"] += 1
                        if correct:
                            self.decks[i]["cards"][j]["times_correct"] += 1
                        break
                break
        if correct:
            self.review_correct += 1
        else:
            self.review_incorrect += 1
        self._advance_review()

    @rx.event
    def set_review_answer(self, v: str):
        self.review_answer_input = v

    @rx.event
    async def submit_quiz_answer(self):
        current_card = self._get_current_card()
        if not current_card:
            return
        ans = self.review_answer_input.strip().lower()
        correct = ans == current_card["back"].strip().lower()
        from reflexuniflow.states.notification_state import NotificationState

        notif = await self.get_state(NotificationState)
        for i, d in enumerate(self.decks):
            if d["id"] == self.selected_deck_id:
                for j, c in enumerate(d["cards"]):
                    if c["id"] == current_card["id"]:
                        self.decks[i]["cards"][j]["times_reviewed"] += 1
                        if correct:
                            self.decks[i]["cards"][j]["times_correct"] += 1
                        break
                break
        if correct:
            self.review_correct += 1
            self.review_last_result = "correct"
        else:
            self.review_incorrect += 1
            self.review_last_result = f"incorrect|{current_card['back']}"

    @rx.event
    def next_quiz_card(self):
        self.review_answer_input = ""
        self.review_last_result = ""
        self._advance_review()

    def _advance_review(self):
        self.review_flipped = False
        if self.review_index + 1 >= len(self.review_order):
            self.review_finished = True
        else:
            self.review_index += 1

    def _get_current_card(self) -> Flashcard | None:
        if self.review_index >= len(self.review_order):
            return None
        current_id = self.review_order[self.review_index]
        for d in self.decks:
            if d["id"] == self.selected_deck_id:
                for c in d["cards"]:
                    if c["id"] == current_id:
                        return c
        return None

    @rx.event
    def exit_review(self):
        self.review_mode = ""
        self.review_finished = False

    @rx.var
    def selected_deck(self) -> Deck:
        for d in self.decks:
            if d["id"] == self.selected_deck_id:
                return d
        return Deck(id="", name="", subject="", cards=[])

    @rx.var
    def current_card(self) -> Flashcard:
        c = self._get_current_card()
        if c:
            return c
        return Flashcard(
            id="", front="", back="", times_reviewed=0, times_correct=0
        )

    @rx.var
    def review_total(self) -> int:
        return len(self.review_order)

    @rx.var
    def review_score_percent(self) -> int:
        total = self.review_correct + self.review_incorrect
        if total == 0:
            return 0
        return int((self.review_correct / total) * 100)

    @rx.var
    def deck_summaries(self) -> list[dict[str, str]]:
        return [
            {
                "id": d["id"],
                "name": d["name"],
                "subject": d["subject"],
                "count": str(len(d["cards"])),
            }
            for d in self.decks
        ]

    @rx.var
    def editing_card(self) -> Flashcard:
        for d in self.decks:
            if d["id"] == self.selected_deck_id:
                for c in d["cards"]:
                    if c["id"] == self.editing_card_id:
                        return c
        return Flashcard(
            id="", front="", back="", times_reviewed=0, times_correct=0
        )
