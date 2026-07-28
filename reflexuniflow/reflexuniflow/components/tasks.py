import reflex as rx
from reflexuniflow.states.task_state import TaskState
from reflexuniflow.states.onboarding_state import OnboardingState


def priority_badge(priority) -> rx.Component:
    return rx.el.span(
        priority,
        class_name=rx.match(
            priority,
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
    )


def task_row(task) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon(
                rx.cond(task["completed"], "check-circle-2", "circle"),
                class_name=rx.cond(
                    task["completed"],
                    "h-6 w-6 text-[#0d9488]",
                    "h-6 w-6 text-[#8b6f47]",
                ),
            ),
            on_click=lambda: TaskState.toggle_complete(task["id"]),
            class_name="shrink-0",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    task["title"],
                    class_name=rx.cond(
                        task["completed"],
                        "font-semibold text-[#8b6f47] line-through",
                        "font-semibold text-[#5c3a1e]",
                    ),
                ),
                priority_badge(task["priority"]),
                class_name="flex items-center gap-3 flex-wrap",
            ),
            rx.el.div(
                rx.cond(
                    task["subject"],
                    rx.el.span(
                        task["subject"],
                        class_name="text-xs px-2 py-0.5 rounded-full bg-[#fef3c7] text-[#92400e] font-medium w-fit",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    task["category"],
                    rx.el.span(
                        task["category"], class_name="text-xs text-[#8b6f47]"
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    task["due_date"],
                    rx.el.span(
                        f"📅 {task['due_date']} {task['due_time']}",
                        class_name="text-xs text-[#8b6f47] font-['IBM_Plex_Mono']",
                    ),
                    rx.fragment(),
                ),
                class_name="flex items-center gap-2 mt-1 flex-wrap",
            ),
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("pencil", class_name="h-4 w-4"),
                on_click=TaskState.open_edit(task["id"]).stop_propagation,
                class_name="p-2 rounded-lg text-[#8b6f47] hover:bg-[#f5e6c8]",
            ),
            rx.el.button(
                rx.icon("trash-2", class_name="h-4 w-4"),
                on_click=TaskState.delete_task(task["id"]).stop_propagation,
                class_name="p-2 rounded-lg text-[#8b6f47] hover:bg-red-50 hover:text-red-600",
            ),
            class_name="flex items-center gap-1 shrink-0",
        ),
        class_name="flex items-start gap-3 p-4 bg-[#fbf3e2] rounded-2xl border-2 border-[#e8d5a8]",
    )


def task_form_modal() -> rx.Component:
    return rx.cond(
        TaskState.show_form,
        rx.el.div(
            rx.el.div(
                rx.el.form(
                    rx.el.div(
                        rx.el.h2(
                            rx.cond(
                                TaskState.editing_id, "Edit Task", "New Task"
                            ),
                            class_name="text-2xl font-bold text-[#5c3a1e] font-['Fraunces']",
                        ),
                        rx.el.button(
                            rx.icon("x", class_name="h-5 w-5"),
                            type="button",
                            on_click=TaskState.close_form,
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
                        default_value=TaskState.editing_task["title"],
                        key=TaskState.editing_id,
                        placeholder="What do you need to do?",
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309] mb-4",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.label(
                                "Subject",
                                class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                            ),
                            rx.el.div(
                                rx.el.select(
                                    rx.el.option("", value=""),
                                    rx.foreach(
                                        OnboardingState.subjects,
                                        lambda s: rx.el.option(s, value=s),
                                    ),
                                    name="subject",
                                    default_value=TaskState.editing_task[
                                        "subject"
                                    ],
                                    class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] appearance-none focus:outline-hidden focus:border-[#b45309]",
                                ),
                                rx.icon(
                                    "chevron-down",
                                    class_name="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#8b6f47] pointer-events-none",
                                ),
                                class_name="relative",
                            ),
                        ),
                        rx.el.div(
                            rx.el.label(
                                "Category",
                                class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                            ),
                            rx.el.input(
                                name="category",
                                default_value=TaskState.editing_task[
                                    "category"
                                ],
                                placeholder="e.g. Assignment",
                                class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
                            ),
                        ),
                        class_name="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.label(
                                "Due date",
                                class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                            ),
                            rx.el.input(
                                type="date",
                                name="due_date",
                                default_value=TaskState.editing_task[
                                    "due_date"
                                ],
                                class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
                            ),
                        ),
                        rx.el.div(
                            rx.el.label(
                                "Due time",
                                class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                            ),
                            rx.el.input(
                                type="time",
                                name="due_time",
                                default_value=TaskState.editing_task[
                                    "due_time"
                                ],
                                class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309]",
                            ),
                        ),
                        class_name="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4",
                    ),
                    rx.el.label(
                        "Priority",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.div(
                        rx.foreach(
                            TaskState.priority_options,
                            lambda p: rx.el.label(
                                rx.el.input(
                                    type="radio",
                                    name="priority",
                                    value=p,
                                    default_checked=TaskState.editing_task[
                                        "priority"
                                    ]
                                    == p,
                                    class_name="sr-only peer",
                                ),
                                rx.el.span(p),
                                class_name="flex-1 text-center py-2.5 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#5c3a1e] font-medium cursor-pointer peer-checked:bg-[#b45309] peer-checked:text-white peer-checked:border-[#b45309]",
                            ),
                        ),
                        class_name="flex gap-2 mb-4",
                    ),
                    rx.el.label(
                        "Notes",
                        class_name="block text-sm font-semibold text-[#5c3a1e] mb-2",
                    ),
                    rx.el.textarea(
                        name="notes",
                        default_value=TaskState.editing_task["notes"],
                        placeholder="Optional notes...",
                        rows="3",
                        class_name="w-full px-4 py-3 rounded-xl border-2 border-[#e8d5a8] bg-[#faf1dd] text-[#3d2914] focus:outline-hidden focus:border-[#b45309] mb-4",
                    ),
                    rx.el.label(
                        rx.el.input(
                            type="checkbox",
                            name="show_on_calendar",
                            default_checked=TaskState.editing_task[
                                "show_on_calendar"
                            ],
                            class_name="h-4 w-4 accent-[#b45309]",
                            default_value="true",
                            key=f"cal_{TaskState.editing_id}",
                        ),
                        rx.el.span(
                            "Show on calendar",
                            class_name="text-sm font-medium text-[#5c3a1e]",
                        ),
                        class_name="flex items-center gap-2 mb-6",
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            type="button",
                            on_click=TaskState.close_form,
                            class_name="flex-1 px-5 py-2.5 rounded-xl border-2 border-[#e8d5a8] text-[#5c3a1e] hover:bg-[#faf1dd] font-medium",
                        ),
                        rx.el.button(
                            "Save",
                            type="submit",
                            class_name="flex-1 px-5 py-2.5 rounded-xl bg-[#b45309] text-white hover:bg-[#92400e] font-medium",
                        ),
                        class_name="flex gap-3",
                    ),
                    on_submit=TaskState.submit_task,
                    reset_on_submit=True,
                    on_click=rx.stop_propagation,
                    class_name="bg-[#fbf3e2] p-6 sm:p-8 rounded-3xl border-2 border-[#e8d5a8] w-full max-w-lg max-h-[90vh] overflow-y-auto",
                ),
                class_name="fixed inset-0 flex items-center justify-center p-4 z-50 bg-black/40",
                on_click=TaskState.close_form,
            ),
            class_name="",
        ),
        rx.fragment(),
    )


def tasks_content() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Tasks",
                    class_name="text-4xl font-bold text-[#5c3a1e] font-['Fraunces']",
                ),
                rx.el.p(
                    f"{TaskState.total_count} total · {TaskState.completed_count} done",
                    class_name="text-[#8b6f47] font-['IBM_Plex_Mono'] text-sm mt-1",
                ),
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-5 w-5"),
                rx.el.span("New Task"),
                on_click=TaskState.toggle_form,
                class_name="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#b45309] text-white hover:bg-[#92400e] font-medium",
            ),
            class_name="flex flex-wrap items-center justify-between gap-4 mb-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Subject",
                    class_name="block text-xs font-semibold text-[#5c3a1e] mb-1",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            TaskState.all_subjects,
                            lambda s: rx.el.option(s, value=s),
                        ),
                        value=TaskState.filter_subject,
                        on_change=TaskState.set_filter_subject,
                        class_name="w-full px-3 py-2 rounded-lg border-2 border-[#e8d5a8] bg-[#fbf3e2] text-sm text-[#3d2914] appearance-none pr-8",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#8b6f47] pointer-events-none",
                    ),
                    class_name="relative",
                ),
            ),
            rx.el.div(
                rx.el.label(
                    "Priority",
                    class_name="block text-xs font-semibold text-[#5c3a1e] mb-1",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            TaskState.priority_filters,
                            lambda p: rx.el.option(p, value=p),
                        ),
                        value=TaskState.filter_priority,
                        on_change=TaskState.set_filter_priority,
                        class_name="w-full px-3 py-2 rounded-lg border-2 border-[#e8d5a8] bg-[#fbf3e2] text-sm text-[#3d2914] appearance-none pr-8",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#8b6f47] pointer-events-none",
                    ),
                    class_name="relative",
                ),
            ),
            rx.el.div(
                rx.el.label(
                    "Sort by",
                    class_name="block text-xs font-semibold text-[#5c3a1e] mb-1",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.el.option("Due date", value="due_date"),
                        rx.el.option("Priority", value="priority"),
                        rx.el.option("Title", value="title"),
                        value=TaskState.sort_by,
                        on_change=TaskState.set_sort_by,
                        class_name="w-full px-3 py-2 rounded-lg border-2 border-[#e8d5a8] bg-[#fbf3e2] text-sm text-[#3d2914] appearance-none pr-8",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="absolute right-3 top-1/2 -translate-y-1/2 h-3 w-3 text-[#8b6f47] pointer-events-none",
                    ),
                    class_name="relative",
                ),
            ),
            class_name="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6",
        ),
        rx.el.div(
            rx.cond(
                TaskState.active_tasks.length() > 0,
                rx.el.div(
                    rx.foreach(TaskState.active_tasks, task_row),
                    class_name="flex flex-col gap-3",
                ),
                rx.el.div(
                    rx.icon(
                        "clipboard-list",
                        class_name="h-12 w-12 text-[#8b6f47] mx-auto mb-3",
                    ),
                    rx.el.p(
                        "No active tasks. Add one to get started!",
                        class_name="text-[#8b6f47] text-center",
                    ),
                    class_name="p-12 bg-[#fbf3e2] rounded-2xl border-2 border-dashed border-[#e8d5a8]",
                ),
            ),
        ),
        rx.cond(
            TaskState.completed_tasks.length() > 0,
            rx.el.div(
                rx.el.button(
                    rx.el.span(
                        rx.cond(
                            TaskState.show_completed,
                            "Hide completed",
                            "Show completed",
                        ),
                    ),
                    rx.icon(
                        rx.cond(
                            TaskState.show_completed,
                            "chevron-up",
                            "chevron-down",
                        ),
                        class_name="h-4 w-4",
                    ),
                    on_click=TaskState.toggle_show_completed,
                    class_name="flex items-center gap-2 mt-6 mb-3 text-[#8b6f47] hover:text-[#5c3a1e] text-sm font-medium",
                ),
                rx.cond(
                    TaskState.show_completed,
                    rx.el.div(
                        rx.foreach(TaskState.completed_tasks, task_row),
                        class_name="flex flex-col gap-3",
                    ),
                    rx.fragment(),
                ),
            ),
            rx.fragment(),
        ),
        task_form_modal(),
    )


def tasks_page() -> rx.Component:
    from reflexuniflow.components.nav import page_shell

    return page_shell(tasks_content())
