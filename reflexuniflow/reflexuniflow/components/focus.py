import reflex as rx
from reflexuniflow.states.focus_state import FocusState


def mode_pill(label: str, value: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-4 w-4"),
        rx.el.span(label),
        on_click=lambda: FocusState.set_mode(value),
        class_name=rx.cond(
            FocusState.mode == value,
            "flex items-center gap-2 px-5 py-2 rounded-full bg-[#b45309] text-white font-medium text-sm shadow-sm",
            "flex items-center gap-2 px-5 py-2 rounded-full text-[#5c3a1e] font-medium text-sm hover:bg-[#f5e6c8]",
        ),
    )


def circular_progress() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                class_name="absolute inset-0 rounded-full",
                style={
                    "background": f"conic-gradient(#b45309 {FocusState.progress_percent}%, #f5e6c8 0)"
                },
            ),
            rx.el.div(
                rx.el.p(
                    FocusState.display_time,
                    class_name="text-5xl sm:text-6xl font-bold text-[#5c3a1e] font-['IBM_Plex_Mono'] tabular-nums",
                ),
                rx.cond(
                    FocusState.mode == "pomodoro",
                    rx.el.p(
                        rx.cond(
                            FocusState.pomodoro_phase == "work",
                            "FOCUS TIME",
                            "BREAK TIME",
                        ),
                        class_name=rx.cond(
                            FocusState.pomodoro_phase == "work",
                            "text-xs font-bold text-[#b45309] font-['IBM_Plex_Mono'] tracking-widest mt-2",
                            "text-xs font-bold text-[#0d9488] font-['IBM_Plex_Mono'] tracking-widest mt-2",
                        ),
                    ),
                    rx.el.p(
                        "TIMER",
                        class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] tracking-widest mt-2",
                    ),
                ),
                class_name="absolute inset-4 rounded-full bg-[#fbf3e2] flex flex-col items-center justify-center",
            ),
            class_name="relative w-72 h-72 sm:w-80 sm:h-80 rounded-full",
        ),
        class_name="flex items-center justify-center",
    )


def cycle_dot(dot) -> rx.Component:
    return rx.el.div(
        class_name=rx.cond(
            dot["filled"] == "true",
            "h-3 w-3 rounded-full bg-[#b45309]",
            "h-3 w-3 rounded-full bg-[#e8d5a8]",
        )
    )


def controls() -> rx.Component:
    return rx.el.div(
        rx.cond(
            FocusState.running,
            rx.el.button(
                rx.icon("pause", class_name="h-5 w-5"),
                rx.el.span("Pause"),
                on_click=FocusState.pause,
                class_name="flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#b45309] text-white font-semibold hover:bg-[#92400e]",
            ),
            rx.el.button(
                rx.icon("play", class_name="h-5 w-5"),
                rx.el.span("Start"),
                on_click=FocusState.start,
                class_name="flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#b45309] text-white font-semibold hover:bg-[#92400e]",
            ),
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-5 w-5"),
            "Reset",
            on_click=FocusState.reset_timer,
            class_name="flex items-center gap-2 px-6 py-3 rounded-2xl border-2 border-[#e8d5a8] text-[#5c3a1e] font-semibold hover:bg-[#f5e6c8]",
        ),
        rx.cond(
            FocusState.mode == "pomodoro",
            rx.el.button(
                rx.icon("skip-forward", class_name="h-5 w-5"),
                "Skip",
                on_click=FocusState.skip_phase,
                class_name="flex items-center gap-2 px-6 py-3 rounded-2xl border-2 border-[#e8d5a8] text-[#5c3a1e] font-semibold hover:bg-[#f5e6c8]",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-wrap items-center justify-center gap-3",
    )


def pomodoro_settings() -> rx.Component:
    return rx.cond(
        FocusState.mode == "pomodoro",
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Cycles",
                    class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase mb-2",
                ),
                rx.el.div(
                    rx.foreach(FocusState.cycle_dots, cycle_dot),
                    class_name="flex items-center gap-2",
                ),
                class_name="text-center",
            ),
            rx.el.div(
                rx.el.label(
                    "Total cycles",
                    class_name="text-xs text-[#8b6f47] font-semibold block mb-1",
                ),
                rx.el.input(
                    type="number",
                    default_value=FocusState.total_cycles.to_string(),
                    on_change=FocusState.set_total_cycles.debounce(300),
                    class_name="w-24 px-3 py-2 rounded-lg border-2 border-[#e8d5a8] bg-[#faf1dd] text-sm text-[#3d2914]",
                ),
            ),
            class_name="flex items-center gap-6 flex-wrap justify-center",
        ),
        rx.el.div(
            rx.el.label(
                "Duration (minutes)",
                class_name="text-xs text-[#8b6f47] font-semibold block mb-1",
            ),
            rx.el.input(
                type="number",
                default_value=FocusState.timer_duration_minutes.to_string(),
                on_change=FocusState.set_timer_duration.debounce(300),
                class_name="w-32 px-3 py-2 rounded-lg border-2 border-[#e8d5a8] bg-[#faf1dd] text-sm text-[#3d2914]",
            ),
            class_name="text-center",
        ),
    )


def stats_row() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                "Study today",
                class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase",
            ),
            rx.el.p(
                f"{FocusState.study_minutes_today}m",
                class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
            ),
            class_name="flex-1 bg-[#fbf3e2] p-4 rounded-2xl border-2 border-[#e8d5a8] text-center",
        ),
        rx.el.div(
            rx.el.p(
                "Pomodoros",
                class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase",
            ),
            rx.el.p(
                FocusState.pomodoros_completed_today,
                class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
            ),
            class_name="flex-1 bg-[#fbf3e2] p-4 rounded-2xl border-2 border-[#e8d5a8] text-center",
        ),
        rx.el.div(
            rx.el.p(
                "Timers done",
                class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase",
            ),
            rx.el.p(
                FocusState.timers_completed_today,
                class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
            ),
            class_name="flex-1 bg-[#fbf3e2] p-4 rounded-2xl border-2 border-[#e8d5a8] text-center",
        ),
        rx.el.div(
            rx.el.p(
                "All time",
                class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase",
            ),
            rx.el.p(
                FocusState.study_hours_all,
                class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
            ),
            class_name="flex-1 bg-[#fbf3e2] p-4 rounded-2xl border-2 border-[#e8d5a8] text-center",
        ),
        class_name="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6",
    )


def session_row(s) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.cond(
                s["completed"] == "yes",
                rx.icon("circle-check", class_name="h-4 w-4 text-[#0d9488]"),
                rx.icon("circle-dashed", class_name="h-4 w-4 text-[#8b6f47]"),
            ),
            rx.el.span(
                s["mode"],
                class_name="text-sm font-semibold text-[#5c3a1e]",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.el.span(
                s["duration"],
                class_name="text-sm font-bold text-[#b45309] font-['IBM_Plex_Mono']",
            ),
            rx.el.span(
                s["date"],
                class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
            ),
            class_name="flex items-center gap-3",
        ),
        class_name="flex items-center justify-between px-3 py-2 bg-[#faf1dd] rounded-xl border border-[#e8d5a8]",
    )


def recent_sessions_section() -> rx.Component:
    return rx.cond(
        FocusState.recent_sessions.length() > 0,
        rx.el.div(
            rx.el.div(
                rx.icon("history", class_name="h-4 w-4 text-[#b45309]"),
                rx.el.span(
                    "Recent sessions",
                    class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase tracking-widest",
                ),
                class_name="flex items-center gap-2 mb-3",
            ),
            rx.el.div(
                rx.foreach(FocusState.recent_sessions, session_row),
                class_name="flex flex-col gap-2",
            ),
            class_name="bg-[#fbf3e2] p-5 rounded-2xl border-2 border-[#e8d5a8] mt-6",
        ),
        rx.fragment(),
    )


def focus_content() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Focus",
                class_name="text-4xl font-bold text-[#5c3a1e] font-['Fraunces']",
            ),
            rx.el.p(
                "Deep work, one session at a time.",
                class_name="text-[#8b6f47] mt-1",
            ),
            class_name="mb-6 text-center",
        ),
        rx.el.div(
            mode_pill("Pomodoro", "pomodoro", "brain"),
            mode_pill("Timer", "timer", "hourglass"),
            class_name="flex items-center justify-center gap-2 mb-8 bg-[#fbf3e2] p-1.5 rounded-full w-fit mx-auto border-2 border-[#e8d5a8]",
        ),
        circular_progress(),
        rx.el.div(controls(), class_name="mt-8"),
        rx.el.div(pomodoro_settings(), class_name="mt-6"),
        stats_row(),
        recent_sessions_section(),
    )


def focus_page() -> rx.Component:
    from reflexuniflow.components.nav import page_shell

    return page_shell(focus_content())
