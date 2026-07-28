import reflex as rx
from typing import TypedDict
import uuid


class Task(TypedDict):
    id: str
    title: str
    category: str
    subject: str
    due_date: str
    due_time: str
    priority: str
    completed: bool
    notes: str
    show_on_calendar: bool


class TaskState(rx.State):
    tasks: list[Task] = []
    show_form: bool = False
    editing_id: str = ""
    filter_subject: str = "All"
    filter_priority: str = "All"
    sort_by: str = "due_date"
    show_completed: bool = True

    priority_options: list[str] = ["Low", "Medium", "High"]
    sort_options: list[str] = ["due_date", "priority", "title"]

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
    def toggle_form(self):
        self.show_form = not self.show_form
        self.editing_id = ""
        self.feedback_message = ""
        self.feedback_kind = ""

    @rx.event
    def open_edit(self, task_id: str):
        self.editing_id = task_id
        self.show_form = True

    @rx.event
    def close_form(self):
        self.show_form = False
        self.editing_id = ""

    @rx.event
    def submit_task(self, form_data: dict):
        title = form_data.get("title", "").strip()
        if not title:
            # Keep the form open so the user doesn't lose their input.
            self.show_form = True
            self._set_feedback("Please enter a title for the task.", "warning")
            return rx.toast(
                "Please enter a title for the task.",
                duration=3000,
                close_button=True,
            )
        raw_cal = form_data.get("show_on_calendar", False)
        show_cal = raw_cal is True or (
            isinstance(raw_cal, str)
            and raw_cal.lower() in ("true", "on", "1", "yes")
        )
        was_editing = bool(self.editing_id)
        if self.editing_id:
            for i, t in enumerate(self.tasks):
                if t["id"] == self.editing_id:
                    self.tasks[i] = Task(
                        id=t["id"],
                        title=title,
                        category=form_data.get("category", "").strip(),
                        subject=form_data.get("subject", "").strip(),
                        due_date=form_data.get("due_date", ""),
                        due_time=form_data.get("due_time", ""),
                        priority=form_data.get("priority", "Medium"),
                        completed=t["completed"],
                        notes=form_data.get("notes", ""),
                        show_on_calendar=show_cal,
                    )
                    break
        else:
            new_task: Task = {
                "id": str(uuid.uuid4()),
                "title": title,
                "category": form_data.get("category", "").strip(),
                "subject": form_data.get("subject", "").strip(),
                "due_date": form_data.get("due_date", ""),
                "due_time": form_data.get("due_time", ""),
                "priority": form_data.get("priority", "Medium"),
                "completed": False,
                "notes": form_data.get("notes", ""),
                "show_on_calendar": show_cal,
            }
            self.tasks.append(new_task)
        self.show_form = False
        self.editing_id = ""
        self._set_feedback(
            f"Task {'updated' if was_editing else 'created'}: {title}",
            "success",
        )
        return rx.toast(
            f"Task {'updated' if was_editing else 'created'}: {title}",
            duration=3000,
            close_button=True,
        )

    @rx.event
    def toggle_complete(self, task_id: str):
        for i, t in enumerate(self.tasks):
            if t["id"] == task_id:
                self.tasks[i]["completed"] = not t["completed"]
                break

    @rx.event
    def delete_task(self, task_id: str):
        removed = next((t for t in self.tasks if t["id"] == task_id), None)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        if removed is not None:
            self._set_feedback(f"Task deleted: {removed['title']}", "info")
            return rx.toast(
                f"Deleted task: {removed['title']}",
                duration=2500,
                close_button=True,
            )

    @rx.event
    def set_filter_subject(self, val: str):
        self.filter_subject = val

    @rx.event
    def set_filter_priority(self, val: str):
        self.filter_priority = val

    @rx.event
    def set_sort_by(self, val: str):
        self.sort_by = val

    @rx.event
    def toggle_show_completed(self):
        self.show_completed = not self.show_completed

    @rx.var
    def editing_task(self) -> Task:
        for t in self.tasks:
            if t["id"] == self.editing_id:
                return t
        return Task(
            id="",
            title="",
            category="",
            subject="",
            due_date="",
            due_time="",
            priority="Medium",
            completed=False,
            notes="",
            show_on_calendar=False,
        )

    @rx.var
    def all_subjects(self) -> list[str]:
        s = set()
        for t in self.tasks:
            if t["subject"]:
                s.add(t["subject"])
        return ["All"] + sorted(list(s))

    @rx.var
    def priority_filters(self) -> list[str]:
        return ["All", "Low", "Medium", "High"]

    def _priority_rank(self, p: str) -> int:
        return {"High": 0, "Medium": 1, "Low": 2}.get(p, 3)

    @rx.var
    def filtered_tasks(self) -> list[Task]:
        result = list(self.tasks)
        if self.filter_subject != "All":
            result = [t for t in result if t["subject"] == self.filter_subject]
        if self.filter_priority != "All":
            result = [
                t for t in result if t["priority"] == self.filter_priority
            ]
        if not self.show_completed:
            result = [t for t in result if not t["completed"]]
        if self.sort_by == "due_date":
            result.sort(
                key=lambda t: (
                    t["due_date"] or "9999-99-99",
                    t["due_time"] or "99:99",
                )
            )
        elif self.sort_by == "priority":
            result.sort(key=lambda t: self._priority_rank(t["priority"]))
        elif self.sort_by == "title":
            result.sort(key=lambda t: t["title"].lower())
        return result

    @rx.var
    def active_tasks(self) -> list[Task]:
        return [t for t in self.filtered_tasks if not t["completed"]]

    @rx.var
    def completed_tasks(self) -> list[Task]:
        return [t for t in self.filtered_tasks if t["completed"]]

    @rx.var
    def total_count(self) -> int:
        return len(self.tasks)

    @rx.var
    def completed_count(self) -> int:
        return len([t for t in self.tasks if t["completed"]])

    @rx.var
    def urgent_tasks(self) -> list[Task]:
        import datetime

        today = datetime.date.today().isoformat()
        upcoming = [
            t
            for t in self.tasks
            if not t["completed"] and t["due_date"] and t["due_date"] >= today
        ]
        upcoming.sort(key=lambda t: (t["due_date"], t["due_time"] or "99:99"))
        return upcoming[:5]
