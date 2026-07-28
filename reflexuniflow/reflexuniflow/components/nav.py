import reflex as rx
from reflexuniflow.states.notification_state import NotificationState


def nav_link(label: str, href: str, icon: str) -> rx.Component:
    return rx.el.a(
        rx.icon(icon, class_name="h-5 w-5"),
        rx.el.span(label, class_name="font-medium hidden lg:inline"),
        href=href,
        class_name="flex items-center gap-2 px-3 py-2 rounded-xl text-[#5c3a1e] hover:bg-[#f5e6c8] transition-colors",
    )


def notification_item(n) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                rx.match(
                    n["kind"],
                    ("success", "circle-check"),
                    ("warning", "triangle-alert"),
                    "info",
                ),
                class_name=rx.match(
                    n["kind"],
                    ("success", "h-4 w-4 text-[#0d9488]"),
                    ("warning", "h-4 w-4 text-amber-600"),
                    "h-4 w-4 text-[#b45309]",
                ),
            ),
            rx.el.div(
                rx.el.p(
                    n["title"],
                    class_name="font-semibold text-sm text-[#5c3a1e]",
                ),
                rx.el.p(
                    n["message"], class_name="text-xs text-[#8b6f47] mt-0.5"
                ),
                rx.el.p(
                    n["timestamp"],
                    class_name="text-[10px] text-[#8b6f47] font-['IBM_Plex_Mono'] mt-1",
                ),
                class_name="flex-1",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3 w-3"),
                on_click=lambda: NotificationState.dismiss(n["id"]),
                class_name="p-1 text-[#8b6f47] hover:text-[#5c3a1e]",
            ),
            class_name="flex items-start gap-2 p-3",
        ),
        class_name="border-b border-[#e8d5a8] last:border-0",
    )


def notification_panel() -> rx.Component:
    return rx.cond(
        NotificationState.show_panel,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        "Notifications",
                        class_name="font-bold text-[#5c3a1e] font-['Fraunces']",
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Mark read",
                            on_click=NotificationState.mark_all_read,
                            class_name="text-xs text-[#8b6f47] hover:text-[#5c3a1e]",
                        ),
                        rx.el.button(
                            "Clear",
                            on_click=NotificationState.clear_all,
                            class_name="text-xs text-[#8b6f47] hover:text-[#5c3a1e] ml-3",
                        ),
                        class_name="flex items-center",
                    ),
                    class_name="flex items-center justify-between p-3 border-b border-[#e8d5a8]",
                ),
                rx.cond(
                    NotificationState.notifications.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            NotificationState.notifications,
                            notification_item,
                        ),
                        class_name="max-h-96 overflow-y-auto",
                    ),
                    rx.el.div(
                        rx.icon(
                            "bell-off",
                            class_name="h-8 w-8 text-[#8b6f47] mx-auto mb-2",
                        ),
                        rx.el.p(
                            "No notifications yet.",
                            class_name="text-sm text-[#8b6f47] text-center",
                        ),
                        class_name="p-8",
                    ),
                ),
                class_name="absolute right-0 top-12 w-80 bg-[#fbf3e2] rounded-2xl border-2 border-[#e8d5a8] shadow-lg z-50",
                on_click=rx.stop_propagation,
            ),
            class_name="fixed inset-0 z-40",
            on_click=NotificationState.toggle_panel,
        ),
        rx.fragment(),
    )


def navbar() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.a(
                rx.el.div(
                    rx.icon("book-open", class_name="h-6 w-6 text-[#b45309]"),
                    rx.el.span(
                        "UniFlow",
                        class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
                    ),
                    class_name="flex items-center gap-2",
                ),
                href="/dashboard",
            ),
            rx.el.nav(
                nav_link("Dashboard", "/dashboard", "layout-dashboard"),
                nav_link("Tasks", "/tasks", "list-checks"),
                nav_link("Calendar", "/calendar", "calendar-days"),
                nav_link("Focus", "/focus", "timer"),
                nav_link("Cards", "/quiz", "layers"),
                nav_link("Profile", "/profile", "user"),
                class_name="flex items-center gap-1",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("bell", class_name="h-5 w-5 text-[#5c3a1e]"),
                    rx.cond(
                        NotificationState.unread_count > 0,
                        rx.el.span(
                            NotificationState.unread_count,
                            class_name="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-[#b45309] text-white text-[10px] font-bold flex items-center justify-center",
                        ),
                        rx.fragment(),
                    ),
                    on_click=NotificationState.toggle_panel,
                    class_name="relative p-2 rounded-xl hover:bg-[#f5e6c8]",
                ),
                notification_panel(),
                class_name="relative",
            ),
            class_name="max-w-7xl mx-auto flex items-center justify-between gap-2 px-4 sm:px-6 py-4",
        ),
        class_name="bg-[#fbf3e2] border-b-2 border-[#e8d5a8] sticky top-0 z-40",
    )


def page_shell(content: rx.Component) -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            content,
            class_name="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-10",
        ),
        class_name="min-h-screen bg-[#faf1dd] font-['Inter'] text-[#3d2914]",
    )
