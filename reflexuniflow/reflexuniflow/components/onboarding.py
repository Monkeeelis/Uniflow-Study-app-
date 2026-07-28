import reflex as rx
from reflexuniflow.states.onboarding_state import OnboardingState


def step_indicator() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            [0, 1, 2, 3],
            lambda i: rx.el.div(
                class_name=rx.cond(
                    OnboardingState.step >= i,
                    "h-2 w-12 rounded-full bg-[#b45309] transition-colors",
                    "h-2 w-12 rounded-full bg-[#e8d5a8] transition-colors",
                )
            ),
        ),
        class_name="flex items-center justify-center gap-2 mb-8",
    )


def step_name() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Welcome!",
            class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces'] mb-2",
        ),
        rx.el.p("Let's get to know you.", class_name="text-[#8b6f47] mb-6"),
        rx.el.label(
            "Your name",
            class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
        ),
        rx.el.input(
            default_value=OnboardingState.name,
            on_change=OnboardingState.set_name.debounce(300),
            placeholder="e.g. Alex",
            class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#fbf3e2] text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
        ),
        rx.el.label(
            "Year level",
            class_name="block text-sm font-semibold text-[#5c3a1e] mt-4 mb-2",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    OnboardingState.year_options,
                    lambda o: rx.el.option(o, value=o),
                ),
                value=OnboardingState.year_level,
                on_change=OnboardingState.set_year_level,
                class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#fbf3e2] text-[#3d2914] appearance-none focus:outline-hidden focus:border-[#b45309]",
            ),
            rx.icon(
                "chevron-down",
                class_name="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#8b6f47] pointer-events-none",
            ),
            class_name="relative",
        ),
    )


def step_subjects() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Your subjects",
            class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces'] mb-2",
        ),
        rx.el.p(
            "Add subjects you're studying.", class_name="text-[#8b6f47] mb-6"
        ),
        rx.el.div(
            rx.el.input(
                default_value=OnboardingState.subject_input,
                on_change=OnboardingState.set_subject_input.debounce(200),
                placeholder="e.g. Mathematics",
                class_name="flex-1 px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#fbf3e2] text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-5 w-5"),
                type="button",
                on_click=OnboardingState.add_subject,
                class_name="px-4 py-3 rounded-xl bg-[#b45309] text-white hover:bg-[#92400e] transition-colors",
            ),
            class_name="flex gap-2 mb-4",
        ),
        rx.el.div(
            rx.foreach(
                OnboardingState.subjects,
                lambda s: rx.el.div(
                    rx.el.span(
                        s, class_name="text-sm font-medium text-[#5c3a1e]"
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-3 w-3"),
                        type="button",
                        on_click=lambda: OnboardingState.remove_subject(s),
                        class_name="text-[#8b6f47] hover:text-[#b45309]",
                    ),
                    class_name="flex items-center gap-2 px-3 py-1.5 bg-[#fef3c7] border border-[#e8d5a8] rounded-full",
                ),
            ),
            class_name="flex flex-wrap gap-2",
        ),
    )


def step_pomodoro() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Focus preferences",
            class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces'] mb-2",
        ),
        rx.el.p(
            "Customize your Pomodoro timer.", class_name="text-[#8b6f47] mb-6"
        ),
        rx.el.label(
            "Work duration (minutes)",
            class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
        ),
        rx.el.input(
            type="number",
            default_value=OnboardingState.pomodoro_work.to_string(),
            on_change=OnboardingState.set_pomodoro_work.debounce(300),
            class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#fbf3e2] text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
        ),
        rx.el.label(
            "Break duration (minutes)",
            class_name="block text-sm font-semibold text-[#5c3a1e] mt-4 mb-2",
        ),
        rx.el.input(
            type="number",
            default_value=OnboardingState.pomodoro_break.to_string(),
            on_change=OnboardingState.set_pomodoro_break.debounce(300),
            class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#fbf3e2] text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
        ),
    )


def step_notifications() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Notifications",
            class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces'] mb-2",
        ),
        rx.el.p(
            "Get reminders for tasks and study time.",
            class_name="text-[#8b6f47] mb-6",
        ),
        rx.el.button(
            rx.el.div(
                rx.icon(
                    rx.cond(
                        OnboardingState.notifications_enabled,
                        "bell",
                        "bell-off",
                    ),
                    class_name="h-6 w-6",
                ),
                rx.el.div(
                    rx.el.p(
                        rx.cond(
                            OnboardingState.notifications_enabled,
                            "Enabled",
                            "Disabled",
                        ),
                        class_name="font-semibold text-[#5c3a1e]",
                    ),
                    rx.el.p(
                        "Tap to toggle", class_name="text-sm text-[#8b6f47]"
                    ),
                ),
                class_name="flex items-center gap-4",
            ),
            type="button",
            on_click=OnboardingState.toggle_notifications,
            class_name=rx.cond(
                OnboardingState.notifications_enabled,
                "w-full p-6 rounded-2xl border-2 border-[#0d9488] bg-[#ccfbf1] text-[#134e4a] transition-all",
                "w-full p-6 rounded-2xl border-2 border-[#e8d5a8] bg-[#fbf3e2] text-[#5c3a1e] transition-all",
            ),
        ),
    )


def onboarding_page() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("book-open", class_name="h-8 w-8 text-[#b45309]"),
                rx.el.span(
                    "UniFlow",
                    class_name="text-3xl font-bold text-[#5c3a1e] font-['Fraunces']",
                ),
                class_name="flex items-center justify-center gap-2 mb-8",
            ),
            step_indicator(),
            rx.el.div(
                rx.match(
                    OnboardingState.step,
                    (0, step_name()),
                    (1, step_subjects()),
                    (2, step_pomodoro()),
                    (3, step_notifications()),
                    step_name(),
                ),
                class_name="mb-8",
            ),
            rx.el.div(
                rx.cond(
                    OnboardingState.step > 0,
                    rx.el.button(
                        rx.icon("arrow-left", class_name="h-4 w-4"),
                        "Back",
                        on_click=OnboardingState.prev_step,
                        class_name="flex items-center gap-2 px-5 py-2.5 rounded-xl border-2 border-[#e8d5a8] text-[#5c3a1e] hover:bg-[#fbf3e2] font-medium",
                    ),
                    rx.el.div(),
                ),
                rx.cond(
                    OnboardingState.step < 3,
                    rx.el.button(
                        "Next",
                        rx.icon("arrow-right", class_name="h-4 w-4"),
                        on_click=OnboardingState.next_step,
                        class_name="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#b45309] text-white hover:bg-[#92400e] font-medium",
                    ),
                    rx.el.button(
                        "Get Started",
                        rx.icon("check", class_name="h-4 w-4"),
                        on_click=OnboardingState.finish,
                        class_name="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#0d9488] text-white hover:bg-[#0f766e] font-medium",
                    ),
                ),
                class_name="flex items-center justify-between",
            ),
            class_name="w-full max-w-lg bg-[#fbf3e2] rounded-3xl p-8 sm:p-10 border-2 border-[#e8d5a8]",
        ),
        class_name="min-h-screen bg-[#faf1dd] flex items-center justify-center px-4 py-10 font-['Inter']",
    )
