import reflex as rx
from reflexuniflow.states.onboarding_state import OnboardingState
from reflexuniflow.states.task_state import TaskState
from reflexuniflow.states.focus_state import FocusState
from reflexuniflow.states.stats_state import StatsState
from reflexuniflow.states.flashcard_state import FlashcardState
from reflexuniflow.states.insights_state import InsightsState


def section(title: str, children: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            title,
            class_name="text-xl font-bold text-[#5c3a1e] font-['Fraunces'] mb-4",
        ),
        children,
        class_name="bg-[#fbf3e2] p-6 rounded-2xl border-2 border-[#e8d5a8] mb-6",
    )


def stat_box(label: str, value) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase",
        ),
        rx.el.p(
            value,
            class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
        ),
        class_name="p-4 bg-[#faf1dd] rounded-xl border border-[#e8d5a8] text-center",
    )


def range_button(label: str, mode: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=lambda: InsightsState.set_range(mode),
        class_name=rx.cond(
            InsightsState.range_mode == mode,
            "px-4 py-1.5 rounded-full bg-[#b45309] text-white text-sm font-medium",
            "px-4 py-1.5 rounded-full text-[#5c3a1e] text-sm font-medium hover:bg-[#f5e6c8]",
        ),
    )


def heatmap_cell(c) -> rx.Component:
    return rx.el.div(
        title=f"{c['label']} — {c['minutes']} min",
        class_name=rx.cond(
            c["in_range"] == "false",
            "w-full aspect-square rounded-[3px] bg-transparent",
            rx.cond(
                c["is_today"] == "true",
                rx.match(
                    c["level"],
                    (
                        0,
                        "w-full aspect-square rounded-[3px] bg-[#f5e6c8] ring-2 ring-[#0d9488]",
                    ),
                    (
                        1,
                        "w-full aspect-square rounded-[3px] bg-[#fde9b3] ring-2 ring-[#0d9488]",
                    ),
                    (
                        2,
                        "w-full aspect-square rounded-[3px] bg-[#fbbf24] ring-2 ring-[#0d9488]",
                    ),
                    (
                        3,
                        "w-full aspect-square rounded-[3px] bg-[#d97706] ring-2 ring-[#0d9488]",
                    ),
                    (
                        4,
                        "w-full aspect-square rounded-[3px] bg-[#92400e] ring-2 ring-[#0d9488]",
                    ),
                    "w-full aspect-square rounded-[3px] bg-[#f5e6c8] ring-2 ring-[#0d9488]",
                ),
                rx.match(
                    c["level"],
                    (
                        0,
                        "w-full aspect-square rounded-[3px] bg-[#f5e6c8] border border-[#e8d5a8]",
                    ),
                    (
                        1,
                        "w-full aspect-square rounded-[3px] bg-[#fde9b3] border border-[#e8d5a8]",
                    ),
                    (
                        2,
                        "w-full aspect-square rounded-[3px] bg-[#fbbf24] border border-[#f59e0b]",
                    ),
                    (
                        3,
                        "w-full aspect-square rounded-[3px] bg-[#d97706] border border-[#b45309]",
                    ),
                    (
                        4,
                        "w-full aspect-square rounded-[3px] bg-[#92400e] border border-[#78350f]",
                    ),
                    "w-full aspect-square rounded-[3px] bg-[#f5e6c8] border border-[#e8d5a8]",
                ),
            ),
        ),
    )


def insights_metric(label: str, value, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-[#b45309]"),
            rx.el.p(
                label,
                class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase tracking-widest",
            ),
            class_name="flex items-center gap-2 mb-1",
        ),
        rx.el.p(
            value,
            class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
        ),
        class_name="flex-1 p-4 bg-[#faf1dd] rounded-2xl border-2 border-[#e8d5a8]",
    )


def heatmap_legend() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            "Less",
            class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
        ),
        rx.el.div(
            class_name="h-3 w-3 rounded-[3px] bg-[#f5e6c8] border border-[#e8d5a8]"
        ),
        rx.el.div(
            class_name="h-3 w-3 rounded-[3px] bg-[#fde9b3] border border-[#e8d5a8]"
        ),
        rx.el.div(
            class_name="h-3 w-3 rounded-[3px] bg-[#fbbf24] border border-[#f59e0b]"
        ),
        rx.el.div(
            class_name="h-3 w-3 rounded-[3px] bg-[#d97706] border border-[#b45309]"
        ),
        rx.el.div(
            class_name="h-3 w-3 rounded-[3px] bg-[#92400e] border border-[#78350f]"
        ),
        rx.el.span(
            "More",
            class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
        ),
        class_name="flex items-center gap-1.5",
    )


def insights_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Study Insights",
                    class_name="text-xl font-bold text-[#5c3a1e] font-['Fraunces']",
                ),
                rx.el.p(
                    InsightsState.range_label,
                    class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
                ),
            ),
            rx.el.div(
                range_button("Week", "week"),
                range_button("Month", "month"),
                range_button("Year", "year"),
                class_name="flex items-center gap-1 bg-[#faf1dd] p-1 rounded-full border-2 border-[#e8d5a8]",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3 mb-4",
        ),
        rx.el.div(
            insights_metric(
                "Total time", InsightsState.total_display_str, "clock"
            ),
            insights_metric(
                "Active days", InsightsState.active_days, "calendar-check"
            ),
            insights_metric(
                "Avg / active day",
                InsightsState.average_display_str,
                "chart-line",
            ),
            insights_metric(
                "Best day", InsightsState.best_display_str, "trophy"
            ),
            class_name="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.foreach(InsightsState.heatmap_cells, heatmap_cell),
                class_name=rx.match(
                    InsightsState.range_mode,
                    (
                        "week",
                        "grid grid-cols-7 gap-2",
                    ),
                    (
                        "month",
                        "grid grid-cols-10 sm:grid-cols-10 gap-1.5",
                    ),
                    (
                        "year",
                        "grid grid-flow-col grid-rows-7 gap-[3px] overflow-x-auto pb-2",
                    ),
                    "grid grid-cols-10 gap-1.5",
                ),
                style=rx.match(
                    InsightsState.range_mode,
                    ("year", {"gridAutoColumns": "12px"}),
                    {},
                ),
            ),
            class_name="p-4 bg-[#faf1dd] rounded-2xl border-2 border-[#e8d5a8] mb-3 overflow-hidden",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Best day",
                    class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase",
                ),
                rx.el.p(
                    InsightsState.best_day_label,
                    class_name="text-sm text-[#5c3a1e] font-semibold",
                ),
            ),
            heatmap_legend(),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        class_name="bg-[#fbf3e2] p-6 rounded-2xl border-2 border-[#e8d5a8] mb-6",
    )


def profile_content() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.image(
                    src=f"https://api.dicebear.com/9.x/notionists/svg?seed={OnboardingState.name}",
                    class_name="h-20 w-20 rounded-full bg-[#fef3c7]",
                ),
                rx.el.div(
                    rx.el.h1(
                        OnboardingState.name,
                        class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces']",
                    ),
                    rx.el.p(
                        OnboardingState.year_level,
                        class_name="text-[#8b6f47]",
                    ),
                ),
                class_name="flex items-center gap-4",
            ),
            class_name="mb-6",
        ),
        section(
            "Productivity",
            rx.el.div(
                stat_box("Streak", f"{StatsState.streak_days}d"),
                stat_box("Tasks done", TaskState.completed_count),
                stat_box("Sessions", FocusState.sessions_today),
                stat_box("Total time", FocusState.study_hours_all),
                class_name="grid grid-cols-2 sm:grid-cols-4 gap-3",
            ),
        ),
        insights_section(),
        section(
            "Profile",
            rx.el.div(
                rx.el.label(
                    "Name",
                    class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                ),
                rx.el.input(
                    default_value=OnboardingState.name,
                    on_change=OnboardingState.set_name.debounce(400),
                    class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] mb-4",
                ),
                rx.el.label(
                    "Year level",
                    class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            OnboardingState.year_options,
                            lambda o: rx.el.option(o, value=o),
                        ),
                        value=OnboardingState.year_level,
                        on_change=OnboardingState.set_year_level,
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] appearance-none",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#8b6f47] pointer-events-none",
                    ),
                    class_name="relative",
                ),
            ),
        ),
        section(
            "Subjects",
            rx.el.div(
                rx.el.div(
                    rx.el.input(
                        placeholder="Add a subject",
                        default_value=OnboardingState.subject_input,
                        on_change=OnboardingState.set_subject_input.debounce(
                            200
                        ),
                        class_name="flex-1 px-4 py-2.5 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914]",
                    ),
                    rx.el.button(
                        rx.icon("plus", class_name="h-4 w-4"),
                        on_click=OnboardingState.add_subject,
                        class_name="px-4 py-2.5 rounded-xl bg-[#b45309] text-white",
                    ),
                    class_name="flex gap-2 mb-3",
                ),
                rx.el.div(
                    rx.foreach(
                        OnboardingState.subjects,
                        lambda s: rx.el.div(
                            rx.el.span(
                                s,
                                class_name="text-sm font-medium text-[#5c3a1e]",
                            ),
                            rx.el.button(
                                rx.icon("x", class_name="h-3 w-3"),
                                on_click=lambda: OnboardingState.remove_subject(
                                    s
                                ),
                                class_name="text-[#8b6f47] hover:text-[#b45309]",
                            ),
                            class_name="flex items-center gap-2 px-3 py-1.5 bg-[#fef3c7] border border-[#e8d5a8] rounded-full",
                        ),
                    ),
                    class_name="flex flex-wrap gap-2",
                ),
            ),
        ),
        section(
            "Focus preferences",
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Work duration (minutes)",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.input(
                        type="number",
                        default_value=OnboardingState.pomodoro_work.to_string(),
                        on_change=OnboardingState.set_pomodoro_work.debounce(
                            400
                        ),
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914]",
                    ),
                ),
                rx.el.div(
                    rx.el.label(
                        "Break duration (minutes)",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.input(
                        type="number",
                        default_value=OnboardingState.pomodoro_break.to_string(),
                        on_change=OnboardingState.set_pomodoro_break.debounce(
                            400
                        ),
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914]",
                    ),
                ),
                class_name="grid grid-cols-1 sm:grid-cols-2 gap-4",
            ),
        ),
        section(
            "Notifications",
            rx.el.button(
                rx.el.div(
                    rx.icon(
                        rx.cond(
                            OnboardingState.notifications_enabled,
                            "bell",
                            "bell-off",
                        ),
                        class_name="h-5 w-5",
                    ),
                    rx.el.span(
                        rx.cond(
                            OnboardingState.notifications_enabled,
                            "Notifications enabled",
                            "Notifications disabled",
                        ),
                        class_name="font-medium",
                    ),
                    class_name="flex items-center gap-3",
                ),
                on_click=OnboardingState.toggle_notifications,
                class_name=rx.cond(
                    OnboardingState.notifications_enabled,
                    "w-full p-4 rounded-xl border-2 border-[#0d9488] bg-[#ccfbf1] text-[#134e4a]",
                    "w-full p-4 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#5c3a1e]",
                ),
            ),
        ),
    )


def profile_page() -> rx.Component:
    from reflexuniflow.components.nav import page_shell

    return page_shell(profile_content())
