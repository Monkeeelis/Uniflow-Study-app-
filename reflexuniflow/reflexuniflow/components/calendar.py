import reflex as rx
from reflexuniflow.states.calendar_state import CalendarState


def event_pill(ev) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            style={"backgroundColor": ev["color"]},
            class_name="h-1.5 w-1.5 rounded-full shrink-0",
        ),
        rx.cond(
            ev["start_time"] != "",
            rx.el.span(
                ev["start_time"],
                class_name="font-['IBM_Plex_Mono'] text-[10px] text-[#8b6f47] shrink-0",
            ),
            rx.fragment(),
        ),
        rx.el.span(
            ev["title"],
            class_name="text-xs font-medium text-[#5c3a1e] truncate",
        ),
        on_click=lambda: CalendarState.open_event_detail(ev["id"]),
        class_name="w-full flex items-center gap-1 px-1.5 py-0.5 rounded-md hover:bg-[#f5e6c8] text-left",
    )


def month_cell(cell) -> rx.Component:
    return rx.el.div(
        rx.cond(
            cell["in_month"] == "true",
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        cell["day"],
                        class_name=rx.cond(
                            cell["is_today"] == "true",
                            "inline-flex items-center justify-center w-7 h-7 rounded-full bg-[#b45309] text-white text-sm font-bold",
                            "text-sm font-semibold text-[#5c3a1e]",
                        ),
                    ),
                    rx.el.button(
                        rx.icon("plus", class_name="h-3 w-3"),
                        on_click=lambda: CalendarState.open_new_event(
                            cell["date"]
                        ),
                        class_name="opacity-0 group-hover:opacity-100 p-1 rounded text-[#8b6f47] hover:bg-[#f5e6c8]",
                    ),
                    class_name="flex items-center justify-between mb-1",
                ),
                rx.el.div(
                    rx.foreach(
                        CalendarState.events_by_date.get(cell["date"], []),
                        event_pill,
                    ),
                    class_name="flex flex-col gap-0.5",
                ),
                class_name="h-full flex flex-col",
            ),
            rx.el.div(),
        ),
        class_name="group min-h-[100px] p-2 bg-[#fbf3e2] border border-[#e8d5a8] rounded-lg",
    )


def month_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.foreach(
                ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                lambda d: rx.el.div(
                    d,
                    class_name="text-xs font-bold text-[#8b6f47] uppercase font-['IBM_Plex_Mono'] text-center py-2",
                ),
            ),
            class_name="grid grid-cols-7 gap-2 mb-2",
        ),
        rx.el.div(
            rx.foreach(CalendarState.month_cells, month_cell),
            class_name="grid grid-cols-7 gap-2",
        ),
    )


# ---------------------------------------------------------------------------
# Time-grid rendering shared by day and week views.
# ---------------------------------------------------------------------------


def timed_block(b) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.span(
                b["start_time"],
                class_name="font-['IBM_Plex_Mono'] text-[10px] text-[#5c3a1e] font-semibold",
            ),
            rx.el.span("–", class_name="text-[10px] text-[#8b6f47]"),
            rx.el.span(
                b["end_time"],
                class_name="font-['IBM_Plex_Mono'] text-[10px] text-[#5c3a1e] font-semibold",
            ),
            rx.cond(
                b["duration_label"] != "",
                rx.el.span(
                    f"· {b['duration_label']}",
                    class_name="font-['IBM_Plex_Mono'] text-[10px] text-[#8b6f47] ml-1",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-1 mb-0.5",
        ),
        rx.el.p(
            b["title"],
            class_name="text-xs sm:text-sm font-semibold text-[#5c3a1e] font-['Fraunces'] leading-tight line-clamp-2",
        ),
        rx.cond(
            b["category"] != "",
            rx.el.p(
                b["category"],
                class_name="text-[10px] font-['IBM_Plex_Mono'] text-[#8b6f47] uppercase mt-0.5 truncate",
            ),
            rx.fragment(),
        ),
        on_click=lambda: CalendarState.open_event_detail(b["id"]),
        style={
            "top": f"{b['top']}px",
            "height": f"{b['height']}px",
            "borderLeftColor": b["color"],
        },
        class_name="absolute left-1 right-1 rounded-lg text-left bg-[#faf1dd] border-2 border-[#e8d5a8] border-l-4 hover:border-[#b45309] transition-colors overflow-hidden px-2 py-1.5",
    )


def hour_row(h) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            h["label"],
            class_name="text-[10px] font-['IBM_Plex_Mono'] text-[#8b6f47] pr-2",
        ),
        style={"height": f"{CalendarState.hour_height_px}px"},
        class_name="flex items-start justify-end",
    )


def grid_hour_line(h) -> rx.Component:
    return rx.el.div(
        style={"height": f"{CalendarState.hour_height_px}px"},
        class_name="border-t border-[#e8d5a8] first:border-t-0",
    )


def all_day_pill(ev) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            style={"backgroundColor": ev["color"]},
            class_name="h-2 w-2 rounded-full shrink-0",
        ),
        rx.el.span(
            ev["title"],
            class_name="text-xs font-medium text-[#5c3a1e] truncate",
        ),
        on_click=lambda: CalendarState.open_event_detail(ev["id"]),
        class_name="flex items-center gap-1.5 px-2 py-1 rounded-md bg-[#faf1dd] border border-[#e8d5a8] hover:border-[#b45309] w-full text-left",
    )


def day_column(date_str: str) -> rx.Component:
    return rx.el.div(
        rx.foreach(CalendarState.hour_labels, grid_hour_line),
        rx.el.div(
            rx.foreach(
                CalendarState.positioned_events_by_date.get(date_str, []),
                timed_block,
            ),
            class_name="absolute inset-0",
        ),
        style={"height": f"{CalendarState.grid_height_px}px"},
        class_name="relative flex-1 min-w-0 bg-[#fbf3e2]",
    )


def week_day_column(day) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    day["label"],
                    class_name=rx.cond(
                        day["is_today"] == "true",
                        "font-bold text-[#b45309] text-sm",
                        "font-semibold text-[#5c3a1e] text-sm",
                    ),
                ),
                rx.el.button(
                    rx.icon("plus", class_name="h-3 w-3"),
                    on_click=lambda: CalendarState.open_new_event(day["date"]),
                    class_name="p-1 rounded text-[#8b6f47] hover:bg-[#f5e6c8]",
                ),
                class_name="flex items-center justify-between px-2 py-2 border-b-2 border-[#e8d5a8] bg-[#fbf3e2] sticky top-0 z-10",
            ),
            rx.cond(
                CalendarState.all_day_events_by_date.get(
                    day["date"], []
                ).length()
                > 0,
                rx.el.div(
                    rx.foreach(
                        CalendarState.all_day_events_by_date.get(
                            day["date"], []
                        ),
                        all_day_pill,
                    ),
                    class_name="flex flex-col gap-1 px-1 py-1 border-b border-[#e8d5a8] bg-[#faf1dd]",
                ),
                rx.fragment(),
            ),
            day_column(day["date"]),
            class_name="flex flex-col flex-1 min-w-[110px] border-r border-[#e8d5a8] last:border-r-0",
        ),
        class_name="flex flex-col flex-1 min-w-[110px]",
    )


def hour_labels_column() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-[41px] border-b-2 border-[#e8d5a8] bg-[#fbf3e2] sticky top-0 z-10",
        ),
        rx.foreach(CalendarState.hour_labels, hour_row),
        class_name="w-14 shrink-0 flex flex-col",
    )


def week_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            hour_labels_column(),
            rx.el.div(
                rx.foreach(CalendarState.week_days, week_day_column),
                class_name="flex flex-1 min-w-0",
            ),
            class_name="flex bg-[#fbf3e2] rounded-2xl border-2 border-[#e8d5a8] overflow-x-auto",
        ),
    )


def day_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                "Schedule",
                class_name="text-lg font-bold text-[#5c3a1e] font-['Fraunces']",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-4 w-4"),
                "Add event",
                on_click=lambda: CalendarState.open_new_event(
                    CalendarState.day_date_str
                ),
                class_name="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#b45309] text-white text-sm font-medium",
            ),
            class_name="flex items-center justify-between mb-3",
        ),
        rx.cond(
            CalendarState.all_day_events_by_date.get(
                CalendarState.day_date_str, []
            ).length()
            > 0,
            rx.el.div(
                rx.el.p(
                    "All day",
                    class_name="text-[10px] font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase tracking-widest mb-2",
                ),
                rx.el.div(
                    rx.foreach(
                        CalendarState.all_day_events_by_date.get(
                            CalendarState.day_date_str, []
                        ),
                        all_day_pill,
                    ),
                    class_name="flex flex-col gap-1",
                ),
                class_name="mb-3 p-3 bg-[#fbf3e2] rounded-2xl border-2 border-[#e8d5a8]",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            hour_labels_column(),
            day_column(CalendarState.day_date_str),
            class_name="flex bg-[#fbf3e2] rounded-2xl border-2 border-[#e8d5a8] overflow-hidden",
        ),
    )


def view_toggle_btn(label: str, mode: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=lambda: CalendarState.set_view(mode),
        class_name=rx.cond(
            CalendarState.view_mode == mode,
            "px-4 py-2 rounded-lg bg-[#b45309] text-white text-sm font-medium",
            "px-4 py-2 rounded-lg bg-[#fbf3e2] text-[#5c3a1e] text-sm font-medium border-2 border-[#e8d5a8] hover:bg-[#f5e6c8]",
        ),
    )


def category_manager() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                "Categories",
                class_name="text-lg font-bold text-[#5c3a1e] font-['Fraunces']",
            ),
            rx.el.button(
                rx.icon(
                    rx.cond(CalendarState.show_category_form, "x", "plus"),
                    class_name="h-4 w-4",
                ),
                on_click=CalendarState.toggle_category_form,
                class_name="p-1.5 rounded-lg text-[#8b6f47] hover:bg-[#f5e6c8]",
            ),
            class_name="flex items-center justify-between mb-3",
        ),
        rx.cond(
            CalendarState.show_category_form,
            rx.el.div(
                rx.el.input(
                    placeholder="Category name",
                    default_value=CalendarState.new_category_name,
                    on_change=CalendarState.set_new_category_name.debounce(200),
                    class_name="flex-1 px-3 py-2 rounded-lg border-2 border-[#e8d5a8] bg-[#faf1dd] text-sm text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
                ),
                rx.el.input(
                    type="color",
                    default_value=CalendarState.new_category_color,
                    on_change=CalendarState.set_new_category_color.debounce(
                        200
                    ),
                    class_name="w-10 h-10 rounded-lg border-2 border-[#e8d5a8] cursor-pointer",
                ),
                rx.el.button(
                    rx.icon("check", class_name="h-4 w-4"),
                    on_click=CalendarState.add_category,
                    class_name="p-2 rounded-lg bg-[#0d9488] text-white hover:bg-[#0f766e]",
                ),
                class_name="flex items-center gap-2 mb-3",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.foreach(
                CalendarState.categories,
                lambda c: rx.el.div(
                    rx.el.div(
                        style={"backgroundColor": c["color"]},
                        class_name="h-3 w-3 rounded-full",
                    ),
                    rx.el.span(
                        c["name"], class_name="text-sm text-[#5c3a1e] flex-1"
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-3 w-3"),
                        on_click=lambda: CalendarState.remove_category(
                            c["name"]
                        ),
                        class_name="text-[#8b6f47] hover:text-red-600",
                    ),
                    class_name="flex items-center gap-2 px-3 py-1.5 bg-[#faf1dd] rounded-lg border border-[#e8d5a8]",
                ),
            ),
            class_name="flex flex-wrap gap-2",
        ),
        class_name="bg-[#fbf3e2] p-4 rounded-2xl border-2 border-[#e8d5a8] mb-6",
    )


def event_form_modal() -> rx.Component:
    return rx.cond(
        CalendarState.show_event_form,
        rx.el.div(
            rx.el.div(
                rx.el.form(
                    rx.el.div(
                        rx.el.h2(
                            rx.cond(
                                CalendarState.editing_event_id,
                                "Edit Event",
                                "New Event",
                            ),
                            class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
                        ),
                        rx.el.button(
                            rx.icon("x", class_name="h-5 w-5"),
                            type="button",
                            on_click=CalendarState.close_event_form,
                            class_name="p-2 rounded-lg text-[#8b6f47] hover:bg-[#f5e6c8]",
                        ),
                        class_name="flex items-center justify-between mb-6",
                    ),
                    rx.el.label(
                        "Title",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.input(
                        name="title",
                        default_value=CalendarState.editing_event["title"],
                        key=CalendarState.editing_event_id,
                        placeholder="Event title",
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309] mb-4",
                    ),
                    rx.el.label(
                        "Category",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.div(
                        rx.el.select(
                            rx.foreach(
                                CalendarState.category_names,
                                lambda n: rx.el.option(n, value=n),
                            ),
                            name="category",
                            default_value=CalendarState.editing_event[
                                "category"
                            ],
                            class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] appearance-none focus:outline-hidden focus:border-[#b45309]",
                        ),
                        rx.icon(
                            "chevron-down",
                            class_name="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#8b6f47] pointer-events-none",
                        ),
                        class_name="relative mb-4",
                    ),
                    rx.el.label(
                        "Date",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.input(
                        type="date",
                        name="date",
                        default_value=CalendarState.editing_event["date"],
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309] mb-4",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.label(
                                "Start",
                                class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                            ),
                            rx.el.input(
                                type="time",
                                name="start_time",
                                default_value=CalendarState.editing_event[
                                    "start_time"
                                ],
                                class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
                            ),
                        ),
                        rx.el.div(
                            rx.el.label(
                                "End",
                                class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                            ),
                            rx.el.input(
                                type="time",
                                name="end_time",
                                default_value=CalendarState.editing_event[
                                    "end_time"
                                ],
                                class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
                            ),
                        ),
                        class_name="grid grid-cols-2 gap-3 mb-4",
                    ),
                    rx.el.label(
                        "Notes",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.textarea(
                        name="notes",
                        default_value=CalendarState.editing_event["notes"],
                        rows="3",
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309] mb-6",
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            type="button",
                            on_click=CalendarState.close_event_form,
                            class_name="flex-1 px-5 py-2.5 rounded-xl border-2 border-[#e8d5a8] text-[#5c3a1e] hover:bg-[#faf1dd] font-medium",
                        ),
                        rx.el.button(
                            "Save",
                            type="submit",
                            class_name="flex-1 px-5 py-2.5 rounded-xl bg-[#b45309] text-white hover:bg-[#92400e] font-medium",
                        ),
                        class_name="flex gap-3",
                    ),
                    on_submit=CalendarState.submit_event,
                    reset_on_submit=True,
                    class_name="bg-[#fbf3e2] p-6 sm:p-8 rounded-3xl border-2 border-[#e8d5a8] w-full max-w-lg max-h-[90vh] overflow-y-auto",
                    on_click=rx.stop_propagation,
                ),
                class_name="fixed inset-0 flex items-center justify-center p-4 z-50 bg-black/40",
                on_click=CalendarState.close_event_form,
            ),
        ),
        rx.fragment(),
    )


def event_detail_modal() -> rx.Component:
    return rx.cond(
        CalendarState.show_event_detail,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            style={
                                "backgroundColor": CalendarState.detail_event[
                                    "color"
                                ]
                            },
                            class_name="w-3 h-3 rounded-full",
                        ),
                        rx.el.span(
                            CalendarState.detail_event["category"],
                            class_name="text-xs font-semibold text-[#8b6f47] uppercase font-['IBM_Plex_Mono']",
                        ),
                        class_name="flex items-center gap-2 mb-2",
                    ),
                    rx.el.h2(
                        CalendarState.detail_event["title"],
                        class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces'] mb-4",
                    ),
                    rx.el.div(
                        rx.icon(
                            "calendar", class_name="h-4 w-4 text-[#8b6f47]"
                        ),
                        rx.el.span(
                            CalendarState.detail_event["date"],
                            class_name="text-sm text-[#5c3a1e] font-['IBM_Plex_Mono']",
                        ),
                        class_name="flex items-center gap-2 mb-2",
                    ),
                    rx.cond(
                        CalendarState.detail_event["start_time"] != "",
                        rx.el.div(
                            rx.icon(
                                "clock", class_name="h-4 w-4 text-[#8b6f47]"
                            ),
                            rx.el.span(
                                f"{CalendarState.detail_event['start_time']} — {CalendarState.detail_event['end_time']}",
                                class_name="text-sm text-[#5c3a1e] font-['IBM_Plex_Mono']",
                            ),
                            class_name="flex items-center gap-2 mb-2",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        CalendarState.detail_event["notes"] != "",
                        rx.el.p(
                            CalendarState.detail_event["notes"],
                            class_name="text-sm text-[#5c3a1e] mt-3 p-3 bg-[#faf1dd] rounded-lg",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.div(
                        rx.cond(
                            CalendarState.detail_event_id.startswith("task_"),
                            rx.el.div(
                                "Task event",
                                class_name="flex-1 flex items-center justify-center px-4 py-2.5 rounded-xl bg-[#fef3c7] text-[#92400e] font-medium text-sm",
                            ),
                            rx.el.button(
                                rx.icon("pencil", class_name="h-4 w-4"),
                                "Edit",
                                on_click=CalendarState.open_edit_event(
                                    CalendarState.detail_event_id
                                ).stop_propagation,
                                class_name="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#b45309] text-white font-medium",
                            ),
                        ),
                        rx.el.button(
                            rx.icon("trash-2", class_name="h-4 w-4"),
                            on_click=CalendarState.delete_event(
                                CalendarState.detail_event_id
                            ).stop_propagation,
                            class_name=rx.cond(
                                CalendarState.detail_event_id.startswith(
                                    "task_"
                                ),
                                "px-4 py-2.5 rounded-xl border-2 border-[#e8d5a8] text-[#8b6f47] hover:bg-[#faf1dd]",
                                "px-4 py-2.5 rounded-xl border-2 border-red-200 text-red-600 hover:bg-red-50",
                            ),
                        ),
                        rx.el.button(
                            "Close",
                            on_click=CalendarState.close_event_detail,
                            class_name="px-4 py-2.5 rounded-xl border-2 border-[#e8d5a8] text-[#5c3a1e] hover:bg-[#faf1dd] font-medium",
                        ),
                        class_name="flex items-center gap-2 mt-6",
                    ),
                    on_click=rx.stop_propagation,
                    class_name="bg-[#fbf3e2] p-6 sm:p-8 rounded-3xl border-2 border-[#e8d5a8] w-full max-w-md",
                ),
                on_click=CalendarState.close_event_detail,
                class_name="fixed inset-0 flex items-center justify-center p-4 z-50 bg-black/40",
            ),
        ),
        rx.fragment(),
    )


def calendar_content() -> rx.Component:
    return rx.el.div(
        rx.cond(
            CalendarState.feedback_message != "",
            rx.el.div(
                rx.icon(
                    rx.match(
                        CalendarState.feedback_kind,
                        ("success", "circle-check"),
                        ("warning", "triangle-alert"),
                        "info",
                    ),
                    class_name=rx.match(
                        CalendarState.feedback_kind,
                        ("success", "h-4 w-4 text-[#0d9488]"),
                        ("warning", "h-4 w-4 text-amber-600"),
                        "h-4 w-4 text-[#b45309]",
                    ),
                ),
                rx.el.span(
                    CalendarState.feedback_message,
                    class_name="text-sm font-medium text-[#5c3a1e]",
                ),
                class_name="flex items-center gap-2 mb-4 px-4 py-3 rounded-xl bg-[#fef3c7] border-2 border-[#e8d5a8]",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Calendar",
                    class_name="text-4xl font-bold text-[#5c3a1e] font-['Fraunces']",
                ),
                rx.el.p(
                    CalendarState.header_label,
                    class_name="text-[#8b6f47] font-['IBM_Plex_Mono'] text-sm mt-1",
                ),
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("chevron-left", class_name="h-4 w-4"),
                    on_click=CalendarState.prev_period,
                    class_name="p-2 rounded-lg bg-[#fbf3e2] border-2 border-[#e8d5a8] text-[#5c3a1e] hover:bg-[#f5e6c8]",
                ),
                rx.el.button(
                    "Today",
                    on_click=CalendarState.go_today,
                    class_name="px-3 py-2 rounded-lg bg-[#fbf3e2] border-2 border-[#e8d5a8] text-[#5c3a1e] text-sm font-medium hover:bg-[#f5e6c8]",
                ),
                rx.el.button(
                    rx.icon("chevron-right", class_name="h-4 w-4"),
                    on_click=CalendarState.next_period,
                    class_name="p-2 rounded-lg bg-[#fbf3e2] border-2 border-[#e8d5a8] text-[#5c3a1e] hover:bg-[#f5e6c8]",
                ),
                class_name="flex items-center gap-2",
            ),
            class_name="flex flex-wrap items-center justify-between gap-4 mb-4",
        ),
        rx.el.div(
            view_toggle_btn("Month", "month"),
            view_toggle_btn("Week", "week"),
            view_toggle_btn("Day", "day"),
            class_name="flex items-center gap-2 mb-6",
        ),
        category_manager(),
        rx.el.div(
            rx.cond(
                CalendarState.view_mode == "month",
                month_view(),
                rx.cond(
                    CalendarState.view_mode == "week",
                    week_view(),
                    rx.cond(
                        CalendarState.view_mode == "day",
                        day_view(),
                        month_view(),
                    ),
                ),
            ),
        ),
        event_form_modal(),
        event_detail_modal(),
    )


def calendar_page() -> rx.Component:
    from reflexuniflow.components.nav import page_shell

    return page_shell(calendar_content())
