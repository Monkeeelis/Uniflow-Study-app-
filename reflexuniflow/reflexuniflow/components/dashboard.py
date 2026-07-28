import reflex as rx
from reflexuniflow.states.onboarding_state import OnboardingState
from reflexuniflow.states.task_state import TaskState
from reflexuniflow.states.stats_state import StatsState
from reflexuniflow.states.focus_state import FocusState
from reflexuniflow.states.dashboard_state import DashboardState


def stat_card(icon: str, label: str, value, accent: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name=f"h-6 w-6 {accent}"),
            class_name="w-12 h-12 rounded-xl bg-[#fef3c7] flex items-center justify-center mb-3",
        ),
        rx.el.p(label, class_name="text-sm text-[#8b6f47] font-medium"),
        rx.el.p(
            value,
            class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces']",
        ),
        class_name="bg-[#fbf3e2] p-6 rounded-2xl border-2 border-[#e8d5a8]",
    )


def quick_link(href: str, icon: str, title: str, desc: str) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon(icon, class_name="h-6 w-6 text-[#b45309]"),
            class_name="w-12 h-12 rounded-xl bg-[#fef3c7] flex items-center justify-center mb-3",
        ),
        rx.el.p(
            title,
            class_name="font-semibold text-[#5c3a1e] font-['Fraunces'] text-lg",
        ),
        rx.el.p(desc, class_name="text-sm text-[#8b6f47]"),
        href=href,
        class_name="block bg-[#fbf3e2] p-6 rounded-2xl border-2 border-[#e8d5a8] hover:border-[#b45309] transition-colors",
    )


def urgent_task_item(task) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(task["title"], class_name="font-medium text-[#5c3a1e]"),
            rx.el.p(
                f"{task['subject']} · {task['due_date']}",
                class_name="text-xs text-[#8b6f47]",
            ),
        ),
        rx.el.span(
            task["priority"],
            class_name=rx.match(
                task["priority"],
                (
                    "High",
                    "px-2 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700 w-fit",
                ),
                (
                    "Medium",
                    "px-2 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 w-fit",
                ),
                (
                    "Low",
                    "px-2 py-1 rounded-full text-xs font-semibold bg-teal-100 text-teal-700 w-fit",
                ),
                "px-2 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 w-fit",
            ),
        ),
        class_name="flex items-center justify-between p-3 rounded-xl bg-[#faf1dd] border border-[#e8d5a8]",
    )


def quote_card() -> rx.Component:
    return rx.el.div(
        rx.icon(
            "quote",
            class_name="h-5 w-5 text-[#b45309] shrink-0 mt-1",
        ),
        rx.el.div(
            rx.el.p(
                DashboardState.quote_text,
                class_name="text-[#5c3a1e] font-['Fraunces'] text-base sm:text-lg italic leading-snug",
            ),
            rx.el.p(
                f"— {DashboardState.quote_author}",
                class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono'] mt-1",
            ),
            class_name="flex-1",
        ),
        rx.el.button(
            rx.icon("refresh-cw", class_name="h-4 w-4"),
            on_click=DashboardState.next_quote,
            title="Show another quote",
            class_name="p-2 rounded-lg text-[#8b6f47] hover:bg-[#f5e6c8] hover:text-[#b45309] shrink-0 transition-colors",
        ),
        class_name="flex items-start gap-3 bg-[#fef3c7] p-4 sm:p-5 rounded-2xl border-2 border-[#e8d5a8] mb-8",
    )


def dashboard_timer_widget() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("timer", class_name="h-5 w-5 text-[#b45309]"),
                    rx.el.h2(
                        "Study timer",
                        class_name="text-xl sm:text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    "Track any study session and save it to your history.",
                    class_name="text-sm text-[#8b6f47] mt-1",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.cond(
                        DashboardState.timer_running,
                        rx.el.span(
                            class_name="h-2 w-2 rounded-full bg-[#0d9488] animate-pulse"
                        ),
                        rx.el.span(
                            class_name="h-2 w-2 rounded-full bg-[#e8d5a8]"
                        ),
                    ),
                    rx.el.span(
                        rx.cond(
                            DashboardState.timer_running,
                            "Running",
                            "Idle",
                        ),
                        class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase tracking-widest",
                    ),
                    class_name="flex items-center gap-2",
                ),
                class_name="shrink-0",
            ),
            class_name="flex flex-wrap items-start justify-between gap-4 mb-6",
        ),
        rx.el.div(
            rx.el.p(
                DashboardState.display_time,
                class_name="text-6xl sm:text-7xl md:text-8xl font-bold text-[#5c3a1e] font-['IBM_Plex_Mono'] tracking-wider text-center",
            ),
            rx.el.p(
                rx.cond(
                    DashboardState.timer_seconds > 0,
                    f"{DashboardState.timer_minutes_pending} min pending — press stop to save",
                    "Press start when you begin studying",
                ),
                class_name="text-xs sm:text-sm text-[#8b6f47] font-['IBM_Plex_Mono'] text-center mt-2 uppercase tracking-widest",
            ),
            class_name="py-6",
        ),
        rx.el.div(
            rx.cond(
                DashboardState.timer_running,
                rx.el.button(
                    rx.icon("pause", class_name="h-5 w-5"),
                    rx.el.span("Pause"),
                    on_click=DashboardState.pause_timer,
                    class_name="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-[#b45309] text-white font-semibold hover:bg-[#92400e] transition-colors",
                ),
                rx.el.button(
                    rx.icon("play", class_name="h-5 w-5"),
                    rx.el.span(
                        rx.cond(
                            DashboardState.timer_seconds > 0,
                            "Resume",
                            "Start",
                        )
                    ),
                    on_click=DashboardState.start_timer,
                    class_name="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-[#b45309] text-white font-semibold hover:bg-[#92400e] transition-colors",
                ),
            ),
            rx.el.button(
                rx.icon("square", class_name="h-5 w-5"),
                rx.el.span("Stop & save"),
                on_click=DashboardState.stop_and_save,
                disabled=DashboardState.timer_seconds == 0,
                class_name="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-[#0d9488] text-white font-semibold hover:bg-[#0f766e] disabled:opacity-40 disabled:cursor-not-allowed transition-colors",
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-5 w-5"),
                rx.el.span("Reset", class_name="hidden sm:inline"),
                on_click=DashboardState.reset_timer,
                title="Reset without saving",
                class_name="flex items-center justify-center gap-2 px-4 py-3 rounded-2xl border-2 border-[#e8d5a8] text-[#5c3a1e] font-semibold hover:bg-[#f5e6c8] transition-colors",
            ),
            class_name="flex flex-wrap items-stretch gap-2 sm:gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("clock", class_name="h-4 w-4 text-[#b45309]"),
                    rx.el.span(
                        "Today's dashboard total",
                        class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase tracking-widest",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    DashboardState.dashboard_today_display,
                    class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces']",
                ),
                rx.el.p(
                    f"{DashboardState.dashboard_sessions_today_count} sessions saved today",
                    class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
                ),
                class_name="flex-1 p-4 bg-[#faf1dd] rounded-2xl border-2 border-[#e8d5a8]",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("infinity", class_name="h-4 w-4 text-[#b45309]"),
                    rx.el.span(
                        "All-time dashboard total",
                        class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase tracking-widest",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    DashboardState.dashboard_all_display,
                    class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces']",
                ),
                rx.el.p(
                    f"{DashboardState.dashboard_sessions.length()} sessions saved overall",
                    class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
                ),
                class_name="flex-1 p-4 bg-[#faf1dd] rounded-2xl border-2 border-[#e8d5a8]",
            ),
            class_name="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3",
        ),
        rx.cond(
            DashboardState.recent_dashboard_sessions.length() > 0,
            rx.el.div(
                rx.el.div(
                    rx.icon("history", class_name="h-4 w-4 text-[#b45309]"),
                    rx.el.span(
                        "Recent saved sessions",
                        class_name="text-xs font-bold text-[#8b6f47] font-['IBM_Plex_Mono'] uppercase tracking-widest",
                    ),
                    class_name="flex items-center gap-2 mb-3",
                ),
                rx.el.div(
                    rx.foreach(
                        DashboardState.recent_dashboard_sessions,
                        lambda s: rx.el.div(
                            rx.el.div(
                                rx.el.p(
                                    s["duration"],
                                    class_name="font-bold text-[#5c3a1e] font-['IBM_Plex_Mono']",
                                ),
                                rx.el.p(
                                    s["date"],
                                    class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
                                ),
                                class_name="flex-1",
                            ),
                            rx.el.button(
                                rx.icon("trash-2", class_name="h-3.5 w-3.5"),
                                on_click=lambda: (
                                    DashboardState.delete_dashboard_session(
                                        s["id"]
                                    )
                                ),
                                class_name="p-1.5 rounded-lg text-[#8b6f47] hover:bg-red-50 hover:text-red-600",
                            ),
                            class_name="flex items-center gap-2 px-3 py-2 bg-[#faf1dd] rounded-xl border border-[#e8d5a8]",
                        ),
                    ),
                    class_name="flex flex-col gap-2",
                ),
                class_name="mt-4 p-4 bg-[#faf1dd] rounded-2xl border-2 border-[#e8d5a8]",
            ),
            rx.fragment(),
        ),
        class_name="bg-[#fbf3e2] p-5 sm:p-6 rounded-3xl border-2 border-[#e8d5a8] mb-8",
    )


def dashboard_content() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Welcome back,",
                    class_name="text-[#8b6f47] font-['IBM_Plex_Mono'] text-sm",
                ),
                rx.el.h1(
                    f"Hi, {OnboardingState.name}!",
                    class_name="text-4xl sm:text-5xl font-bold text-[#5c3a1e] font-['Fraunces']",
                ),
                rx.el.p(
                    StatsState.motivation_message,
                    class_name="text-[#8b6f47] mt-2",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("flame", class_name="h-5 w-5 text-[#b45309]"),
                    rx.el.span(
                        f"{StatsState.streak_days}",
                        class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
                    ),
                    rx.el.span(
                        "day streak",
                        class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
                    ),
                    class_name="flex items-center gap-2",
                ),
                class_name="bg-[#fef3c7] px-4 py-3 rounded-2xl border-2 border-[#e8d5a8]",
            ),
            class_name="flex flex-wrap items-start justify-between gap-4 mb-6",
        ),
        quote_card(),
        dashboard_timer_widget(),
        rx.el.div(
            stat_card(
                "list-checks",
                "Active Tasks",
                TaskState.total_count - TaskState.completed_count,
                "text-[#b45309]",
            ),
            stat_card(
                "circle-check",
                "Completed",
                TaskState.completed_count,
                "text-[#0d9488]",
            ),
            stat_card(
                "timer",
                "Study Today",
                DashboardState.dashboard_today_display,
                "text-[#b45309]",
            ),
            stat_card(
                "book",
                "Subjects",
                OnboardingState.subjects.length(),
                "text-[#b45309]",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Quick access",
                    class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces'] mb-4",
                ),
                rx.el.div(
                    rx.el.div(
                        quick_link(
                            "/tasks",
                            "list-checks",
                            "Tasks",
                            "Manage your to-dos",
                        ),
                        quick_link(
                            "/calendar",
                            "calendar-days",
                            "Calendar",
                            "Plan your schedule",
                        ),
                        quick_link(
                            "/focus",
                            "timer",
                            "Focus",
                            "Pomodoro & timer",
                        ),
                        quick_link(
                            "/quiz",
                            "layers",
                            "Cards",
                            "Study with flashcards",
                        ),
                        class_name="grid grid-cols-1 sm:grid-cols-2 gap-4",
                    ),
                ),
            ),
            rx.el.div(
                rx.el.h2(
                    "Coming up",
                    class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces'] mb-4",
                ),
                rx.el.div(
                    rx.cond(
                        TaskState.urgent_tasks.length() > 0,
                        rx.el.div(
                            rx.foreach(
                                TaskState.urgent_tasks, urgent_task_item
                            ),
                            class_name="flex flex-col gap-2",
                        ),
                        rx.el.div(
                            rx.icon(
                                "coffee",
                                class_name="h-8 w-8 text-[#8b6f47] mx-auto mb-2",
                            ),
                            rx.el.p(
                                "No upcoming tasks. Enjoy your break!",
                                class_name="text-[#8b6f47] text-center",
                            ),
                            class_name="p-8",
                        ),
                    ),
                    class_name="bg-[#fbf3e2] p-6 rounded-2xl border-2 border-[#e8d5a8]",
                ),
                class_name="mt-8",
            ),
        ),
    )


def dashboard_page() -> rx.Component:
    from reflexuniflow.components.nav import page_shell

    return page_shell(dashboard_content())
