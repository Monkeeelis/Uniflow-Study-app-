import reflex as rx
from reflexuniflow.components.onboarding import onboarding_page
from reflexuniflow.components.dashboard import dashboard_page
from reflexuniflow.components.tasks import tasks_page
from reflexuniflow.components.calendar import calendar_page
from reflexuniflow.components.focus import focus_page
from reflexuniflow.components.quiz import quiz_page
from reflexuniflow.components.profile import profile_page
from reflexuniflow.states.onboarding_state import OnboardingState


def index() -> rx.Component:
    return rx.cond(
        OnboardingState.completed,
        dashboard_page(),
        onboarding_page(),
    )


def dashboard_route() -> rx.Component:
    return rx.cond(
        OnboardingState.completed,
        dashboard_page(),
        onboarding_page(),
    )


def tasks_route() -> rx.Component:
    return rx.cond(
        OnboardingState.completed,
        tasks_page(),
        onboarding_page(),
    )


def calendar_route() -> rx.Component:
    return rx.cond(
        OnboardingState.completed,
        calendar_page(),
        onboarding_page(),
    )


def focus_route() -> rx.Component:
    return rx.cond(
        OnboardingState.completed,
        focus_page(),
        onboarding_page(),
    )


def quiz_route() -> rx.Component:
    return rx.cond(
        OnboardingState.completed,
        quiz_page(),
        onboarding_page(),
    )


def profile_route() -> rx.Component:
    return rx.cond(
        OnboardingState.completed,
        profile_page(),
        onboarding_page(),
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, route="/")
app.add_page(dashboard_route, route="/dashboard")
app.add_page(tasks_route, route="/tasks")
app.add_page(calendar_route, route="/calendar")
app.add_page(focus_route, route="/focus")
app.add_page(quiz_route, route="/quiz")
app.add_page(profile_route, route="/profile")
