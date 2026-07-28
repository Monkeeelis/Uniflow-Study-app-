import reflex as rx
from reflexuniflow.states.flashcard_state import FlashcardState


def deck_card(d) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.el.div(
                rx.icon("layers", class_name="h-6 w-6 text-[#b45309]"),
                rx.el.span(
                    f"{d['count']} cards",
                    class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono']",
                ),
                class_name="flex items-center justify-between mb-3",
            ),
            rx.el.p(
                d["name"],
                class_name="text-lg font-bold text-[#5c3a1e] font-['Fraunces']",
            ),
            rx.cond(
                d["subject"] != "",
                rx.el.p(
                    d["subject"],
                    class_name="text-xs text-[#92400e] mt-1 px-2 py-0.5 rounded-full bg-[#fef3c7] w-fit",
                ),
                rx.fragment(),
            ),
            on_click=lambda: FlashcardState.select_deck(d["id"]),
            class_name="w-full text-left",
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="h-4 w-4"),
            on_click=FlashcardState.delete_deck(d["id"]).stop_propagation,
            class_name="absolute top-3 right-3 p-1.5 rounded-lg text-[#8b6f47] hover:bg-red-50 hover:text-red-600",
        ),
        class_name="relative bg-[#fbf3e2] p-5 rounded-2xl border-2 border-[#e8d5a8] hover:border-[#b45309] transition-colors",
    )


def deck_list_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Quiz & Cards",
                    class_name="text-4xl font-bold text-[#5c3a1e] font-['Fraunces']",
                ),
                rx.el.p(
                    "Create flashcards and quiz yourself.",
                    class_name="text-[#8b6f47] mt-1",
                ),
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-5 w-5"),
                "New Deck",
                on_click=FlashcardState.toggle_deck_form,
                class_name="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#b45309] text-white font-medium",
            ),
            class_name="flex flex-wrap items-center justify-between gap-4 mb-6",
        ),
        rx.cond(
            FlashcardState.show_deck_form,
            rx.el.div(
                rx.el.h2(
                    "Create a deck",
                    class_name="text-lg font-bold text-[#5c3a1e] font-['Fraunces'] mb-3",
                ),
                rx.el.input(
                    placeholder="Deck name",
                    default_value=FlashcardState.new_deck_name,
                    on_change=FlashcardState.set_new_deck_name.debounce(200),
                    class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] mb-2",
                ),
                rx.el.input(
                    placeholder="Subject (optional)",
                    default_value=FlashcardState.new_deck_subject,
                    on_change=FlashcardState.set_new_deck_subject.debounce(200),
                    class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] mb-3",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=FlashcardState.toggle_deck_form,
                        class_name="flex-1 px-4 py-2.5 rounded-xl border-2 border-[#e8d5a8] text-[#5c3a1e] font-medium",
                    ),
                    rx.el.button(
                        "Create",
                        on_click=FlashcardState.create_deck,
                        class_name="flex-1 px-4 py-2.5 rounded-xl bg-[#b45309] text-white font-medium",
                    ),
                    class_name="flex gap-3",
                ),
                class_name="bg-[#fbf3e2] p-5 rounded-2xl border-2 border-[#e8d5a8] mb-6",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FlashcardState.deck_summaries.length() > 0,
            rx.el.div(
                rx.foreach(FlashcardState.deck_summaries, deck_card),
                class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4",
            ),
            rx.el.div(
                rx.icon(
                    "layers",
                    class_name="h-12 w-12 text-[#8b6f47] mx-auto mb-3",
                ),
                rx.el.p(
                    "No decks yet. Create one to start studying!",
                    class_name="text-[#8b6f47] text-center",
                ),
                class_name="p-12 bg-[#fbf3e2] rounded-2xl border-2 border-dashed border-[#e8d5a8]",
            ),
        ),
    )


def card_row(c) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                c["front"],
                class_name="font-semibold text-[#5c3a1e]",
            ),
            rx.el.p(
                c["back"],
                class_name="text-sm text-[#8b6f47] mt-1",
            ),
            rx.el.p(
                f"Reviewed {c['times_reviewed']} × · {c['times_correct']} correct",
                class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono'] mt-2",
            ),
            class_name="flex-1",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("pencil", class_name="h-4 w-4"),
                on_click=FlashcardState.open_edit_card(
                    c["id"]
                ).stop_propagation,
                class_name="p-2 rounded-lg text-[#8b6f47] hover:bg-[#f5e6c8]",
            ),
            rx.el.button(
                rx.icon("trash-2", class_name="h-4 w-4"),
                on_click=FlashcardState.delete_card(c["id"]).stop_propagation,
                class_name="p-2 rounded-lg text-[#8b6f47] hover:bg-red-50 hover:text-red-600",
            ),
            class_name="flex items-center gap-1 shrink-0",
        ),
        class_name="flex items-start gap-3 p-4 bg-[#fbf3e2] rounded-2xl border-2 border-[#e8d5a8]",
    )


def card_form_modal() -> rx.Component:
    return rx.cond(
        FlashcardState.show_card_form,
        rx.el.div(
            rx.el.div(
                rx.el.form(
                    rx.el.div(
                        rx.el.h2(
                            rx.cond(
                                FlashcardState.editing_card_id,
                                "Edit Card",
                                "New Card",
                            ),
                            class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
                        ),
                        rx.el.button(
                            rx.icon("x", class_name="h-5 w-5"),
                            type="button",
                            on_click=FlashcardState.close_card_form,
                            class_name="p-2 rounded-lg text-[#8b6f47] hover:bg-[#f5e6c8]",
                        ),
                        class_name="flex items-center justify-between mb-6",
                    ),
                    rx.el.label(
                        "Front (question)",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.textarea(
                        name="front",
                        default_value=FlashcardState.editing_card["front"],
                        key=FlashcardState.editing_card_id,
                        rows="2",
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] mb-4",
                    ),
                    rx.el.label(
                        "Back (answer)",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.textarea(
                        name="back",
                        default_value=FlashcardState.editing_card["back"],
                        rows="2",
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] mb-6",
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            type="button",
                            on_click=FlashcardState.close_card_form,
                            class_name="flex-1 px-5 py-2.5 rounded-xl border-2 border-[#e8d5a8] text-[#5c3a1e] font-medium",
                        ),
                        rx.el.button(
                            "Save",
                            type="submit",
                            class_name="flex-1 px-5 py-2.5 rounded-xl bg-[#b45309] text-white font-medium",
                        ),
                        class_name="flex gap-3",
                    ),
                    on_submit=FlashcardState.submit_card,
                    reset_on_submit=True,
                    on_click=rx.stop_propagation,
                    class_name="bg-[#fbf3e2] p-6 sm:p-8 rounded-3xl border-2 border-[#e8d5a8] w-full max-w-lg",
                ),
                class_name="fixed inset-0 flex items-center justify-center p-4 z-50 bg-black/40",
                on_click=FlashcardState.close_card_form,
            ),
        ),
        rx.fragment(),
    )


def deck_detail_view() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("arrow-left", class_name="h-4 w-4"),
            "Back to decks",
            on_click=FlashcardState.back_to_decks,
            class_name="flex items-center gap-2 text-[#8b6f47] hover:text-[#5c3a1e] mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    FlashcardState.selected_deck["name"],
                    class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces']",
                ),
                rx.cond(
                    FlashcardState.selected_deck["subject"] != "",
                    rx.el.p(
                        FlashcardState.selected_deck["subject"],
                        class_name="text-sm text-[#8b6f47]",
                    ),
                    rx.fragment(),
                ),
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("book-open", class_name="h-4 w-4"),
                    "Review",
                    on_click=lambda: FlashcardState.start_review("flashcards"),
                    class_name="flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 border-[#0d9488] text-[#0d9488] font-medium hover:bg-[#ccfbf1]",
                ),
                rx.el.button(
                    rx.icon("check-check", class_name="h-4 w-4"),
                    "Quiz",
                    on_click=lambda: FlashcardState.start_review("quiz"),
                    class_name="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#b45309] text-white font-medium",
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4"),
                    "Add",
                    on_click=FlashcardState.toggle_card_form,
                    class_name="flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 border-[#e8d5a8] text-[#5c3a1e] font-medium hover:bg-[#f5e6c8]",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-center justify-between gap-4 mb-6",
        ),
        rx.cond(
            FlashcardState.selected_deck["cards"].length() > 0,
            rx.el.div(
                rx.foreach(FlashcardState.selected_deck["cards"], card_row),
                class_name="flex flex-col gap-3",
            ),
            rx.el.div(
                rx.icon(
                    "square-stack",
                    class_name="h-12 w-12 text-[#8b6f47] mx-auto mb-3",
                ),
                rx.el.p(
                    "No cards in this deck. Add one to get started!",
                    class_name="text-[#8b6f47] text-center",
                ),
                class_name="p-12 bg-[#fbf3e2] rounded-2xl border-2 border-dashed border-[#e8d5a8]",
            ),
        ),
        card_form_modal(),
    )


def review_flashcard_view() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("x", class_name="h-4 w-4"),
            "End review",
            on_click=FlashcardState.exit_review,
            class_name="flex items-center gap-2 text-[#8b6f47] hover:text-[#5c3a1e] mb-4",
        ),
        rx.el.div(
            rx.el.p(
                f"Card {FlashcardState.review_index + 1} of {FlashcardState.review_total}",
                class_name="text-sm text-[#8b6f47] font-['IBM_Plex_Mono'] text-center mb-1",
            ),
            rx.el.div(
                rx.el.span(
                    f"✓ {FlashcardState.review_correct}",
                    class_name="px-2 py-0.5 rounded-full text-xs font-bold bg-[#ccfbf1] text-[#0f766e] font-['IBM_Plex_Mono']",
                ),
                rx.el.span(
                    f"✗ {FlashcardState.review_incorrect}",
                    class_name="px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700 font-['IBM_Plex_Mono']",
                ),
                class_name="flex items-center justify-center gap-2 mb-4",
            ),
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-1.5 rounded-full bg-[#b45309] transition-all duration-300",
                style={
                    "width": f"{(FlashcardState.review_index + 1) * 100 / FlashcardState.review_total}%"
                },
            ),
            class_name="w-full h-1.5 bg-[#e8d5a8] rounded-full mb-4 overflow-hidden",
        ),
        rx.el.button(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        rx.cond(
                            FlashcardState.review_flipped,
                            "lightbulb",
                            "help-circle",
                        ),
                        class_name=rx.cond(
                            FlashcardState.review_flipped,
                            "h-4 w-4 text-[#0d9488]",
                            "h-4 w-4 text-[#b45309]",
                        ),
                    ),
                    rx.el.p(
                        rx.cond(
                            FlashcardState.review_flipped,
                            "Answer",
                            "Question",
                        ),
                        class_name=rx.cond(
                            FlashcardState.review_flipped,
                            "text-xs font-bold text-[#0d9488] font-['IBM_Plex_Mono'] uppercase tracking-widest",
                            "text-xs font-bold text-[#b45309] font-['IBM_Plex_Mono'] uppercase tracking-widest",
                        ),
                    ),
                    class_name="flex items-center gap-2 mb-4",
                ),
                rx.el.p(
                    rx.cond(
                        FlashcardState.review_flipped,
                        FlashcardState.current_card["back"],
                        FlashcardState.current_card["front"],
                    ),
                    class_name="text-2xl sm:text-3xl font-bold text-[#5c3a1e] font-['Fraunces'] leading-snug",
                ),
                rx.el.div(
                    rx.icon(
                        "refresh-cw",
                        class_name="h-3 w-3 text-[#8b6f47]",
                    ),
                    rx.el.p(
                        "Tap to flip",
                        class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
                    ),
                    class_name="flex items-center justify-center gap-1 mt-6",
                ),
                class_name="text-center flex flex-col items-center justify-center",
            ),
            on_click=FlashcardState.flip_card,
            class_name=rx.cond(
                FlashcardState.review_flipped,
                "w-full min-h-[280px] bg-linear-to-br from-[#ccfbf1] to-[#faf1dd] p-8 rounded-3xl border-2 border-[#0d9488] flex items-center justify-center hover:shadow-lg transition-all",
                "w-full min-h-[280px] bg-linear-to-br from-[#fef3c7] to-[#faf1dd] p-8 rounded-3xl border-2 border-[#b45309] flex items-center justify-center hover:shadow-lg transition-all",
            ),
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("x", class_name="h-5 w-5"),
                "Didn't know",
                on_click=lambda: FlashcardState.mark_result(False),
                class_name="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl border-2 border-red-200 text-red-600 font-medium hover:bg-red-50",
            ),
            rx.el.button(
                rx.icon("check", class_name="h-5 w-5"),
                "Knew it",
                on_click=lambda: FlashcardState.mark_result(True),
                class_name="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-[#0d9488] text-white font-medium hover:bg-[#0f766e]",
            ),
            class_name="flex items-center gap-3 mt-6",
        ),
    )


def review_quiz_view() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("x", class_name="h-4 w-4"),
            "End quiz",
            on_click=FlashcardState.exit_review,
            class_name="flex items-center gap-2 text-[#8b6f47] hover:text-[#5c3a1e] mb-4",
        ),
        rx.el.p(
            f"Question {FlashcardState.review_index + 1} of {FlashcardState.review_total}",
            class_name="text-sm text-[#8b6f47] font-['IBM_Plex_Mono'] text-center mb-1",
        ),
        rx.el.div(
            rx.el.span(
                f"✓ {FlashcardState.review_correct}",
                class_name="px-2 py-0.5 rounded-full text-xs font-bold bg-[#ccfbf1] text-[#0f766e] font-['IBM_Plex_Mono']",
            ),
            rx.el.span(
                f"✗ {FlashcardState.review_incorrect}",
                class_name="px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700 font-['IBM_Plex_Mono']",
            ),
            class_name="flex items-center justify-center gap-2 mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("circle_help", class_name="h-4 w-4 text-[#b45309]"),
                rx.el.p(
                    "QUESTION",
                    class_name="text-xs font-bold text-[#b45309] font-['IBM_Plex_Mono'] uppercase tracking-widest",
                ),
                class_name="flex items-center gap-2 mb-3",
            ),
            rx.el.p(
                FlashcardState.current_card["front"],
                class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
            ),
            class_name="bg-linear-to-br from-[#fef3c7] to-[#faf1dd] p-6 rounded-3xl border-2 border-[#b45309] mb-4",
        ),
        rx.cond(
            FlashcardState.review_last_result == "",
            rx.el.div(
                rx.el.input(
                    placeholder="Your answer...",
                    default_value=FlashcardState.review_answer_input,
                    on_change=FlashcardState.set_review_answer.debounce(200),
                    class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#fbf3e2] text-[#3d2914] mb-3",
                ),
                rx.el.button(
                    "Submit",
                    on_click=FlashcardState.submit_quiz_answer,
                    class_name="w-full px-5 py-3 rounded-xl bg-[#b45309] text-white font-semibold",
                ),
            ),
            rx.el.div(
                rx.cond(
                    FlashcardState.review_last_result == "correct",
                    rx.el.div(
                        rx.icon(
                            "circle-check",
                            class_name="h-6 w-6 text-[#0d9488]",
                        ),
                        rx.el.p(
                            "Correct!",
                            class_name="text-lg font-bold text-[#0d9488]",
                        ),
                        class_name="flex items-center gap-2 p-4 bg-[#ccfbf1] rounded-2xl border-2 border-[#0d9488]",
                    ),
                    rx.el.div(
                        rx.icon(
                            "circle-x",
                            class_name="h-6 w-6 text-red-600",
                        ),
                        rx.el.div(
                            rx.el.p(
                                "Not quite.",
                                class_name="text-lg font-bold text-red-600",
                            ),
                            rx.el.p(
                                f"Correct answer: {FlashcardState.current_card['back']}",
                                class_name="text-sm text-[#5c3a1e]",
                            ),
                        ),
                        class_name="flex items-start gap-2 p-4 bg-red-50 rounded-2xl border-2 border-red-200",
                    ),
                ),
                rx.el.button(
                    "Next",
                    rx.icon("arrow-right", class_name="h-4 w-4"),
                    on_click=FlashcardState.next_quiz_card,
                    class_name="w-full mt-4 flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-[#b45309] text-white font-semibold",
                ),
            ),
        ),
    )


def review_finished_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "trophy",
                class_name="h-16 w-16 text-[#b45309] mx-auto mb-4",
            ),
            rx.el.h2(
                "All done!",
                class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces'] text-center mb-2",
            ),
            rx.el.p(
                f"You got {FlashcardState.review_correct} out of {FlashcardState.review_total} correct.",
                class_name="text-[#8b6f47] text-center mb-6",
            ),
            rx.el.div(
                rx.el.p(
                    f"{FlashcardState.review_score_percent}%",
                    class_name="text-6xl font-bold text-[#b45309] font-['Fraunces'] text-center",
                ),
                rx.el.p(
                    "Score",
                    class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase text-center tracking-widest",
                ),
                class_name="mb-8",
            ),
            rx.el.div(
                rx.el.button(
                    "Review again",
                    on_click=lambda: FlashcardState.start_review(
                        FlashcardState.review_mode
                    ),
                    class_name="flex-1 px-5 py-2.5 rounded-xl bg-[#b45309] text-white font-medium",
                ),
                rx.el.button(
                    "Back to deck",
                    on_click=FlashcardState.exit_review,
                    class_name="flex-1 px-5 py-2.5 rounded-xl border-2 border-[#e8d5a8] text-[#5c3a1e] font-medium",
                ),
                class_name="flex gap-3",
            ),
            class_name="max-w-md mx-auto bg-[#fbf3e2] p-8 rounded-3xl border-2 border-[#e8d5a8]",
        ),
    )


def quiz_content() -> rx.Component:
    return rx.cond(
        FlashcardState.selected_deck_id == "",
        deck_list_view(),
        rx.cond(
            FlashcardState.review_finished,
            review_finished_view(),
            rx.cond(
                FlashcardState.review_mode == "flashcards",
                review_flashcard_view(),
                rx.cond(
                    FlashcardState.review_mode == "quiz",
                    review_quiz_view(),
                    deck_detail_view(),
                ),
            ),
        ),
    )


def quiz_page() -> rx.Component:
    from reflexuniflow.components.nav import page_shell

    return page_shell(quiz_content())
