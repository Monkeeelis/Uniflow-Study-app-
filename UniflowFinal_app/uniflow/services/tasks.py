"""Task list: create, edit, complete, filter and sort."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from uniflow.services.common import flag, set_feedback, text, toast

PRIORITY_OPTIONS = ["Low", "Medium", "High"]
PRIORITY_FILTERS = ["All", "Low", "Medium", "High"]
SORT_OPTIONS = ["due_date", "priority", "title"]
PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}

EMPTY_TASK: dict[str, Any] = {
    "id": "",
    "title": "",
    "category": "",
    "subject": "",
    "due_date": "",
    "due_time": "",
    "priority": "Medium",
    "completed": False,
    "notes": "",
    "show_on_calendar": False,
}


def clear_feedback(data: dict[str, Any]) -> None:
    set_feedback(data["tasks"], "", "")


def set_form(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["tasks"]
    section["show_form"] = flag(payload, "open", True)
    section["editing_id"] = text(payload, "task_id") if section["show_form"] else ""
    set_feedback(section, "", "")


def submit(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["tasks"]
    title = text(payload, "title")
    if not title:
        # Keep the form open so the user doesn't lose their input.
        section["show_form"] = True
        set_feedback(section, "Please enter a title for the task.", "warning")
        return toast("Please enter a title for the task.", "warning")

    priority = text(payload, "priority", "Medium")
    if priority not in PRIORITY_OPTIONS:
        priority = "Medium"
    fields = {
        "title": title,
        "category": text(payload, "category"),
        "subject": text(payload, "subject"),
        "due_date": text(payload, "due_date"),
        "due_time": text(payload, "due_time"),
        "priority": priority,
        "notes": text(payload, "notes"),
        "show_on_calendar": flag(payload, "show_on_calendar"),
    }

    editing_id = section["editing_id"]
    was_editing = False
    if editing_id:
        for task in section["items"]:
            if task["id"] == editing_id:
                task.update(fields)
                was_editing = True
                break
        if not was_editing:
            set_feedback(section, "That task no longer exists.", "warning")
            return toast("That task no longer exists.", "warning")
    else:
        new_task = dict(EMPTY_TASK)
        new_task.update(fields)
        new_task["id"] = str(uuid.uuid4())
        new_task["completed"] = False
        section["items"].append(new_task)

    section["show_form"] = False
    section["editing_id"] = ""
    action = "updated" if was_editing else "created"
    set_feedback(section, f"Task {action}: {title}", "success")
    return toast(f"Task {action}: {title}", "success")


def toggle_complete(data: dict[str, Any], task_id: str) -> None:
    for task in data["tasks"]["items"]:
        if task["id"] == task_id:
            task["completed"] = not task["completed"]
            return


def delete(data: dict[str, Any], task_id: str) -> dict[str, str] | None:
    section = data["tasks"]
    removed = next((t for t in section["items"] if t["id"] == task_id), None)
    section["items"] = [t for t in section["items"] if t["id"] != task_id]
    if section["editing_id"] == task_id:
        section["editing_id"] = ""
        section["show_form"] = False
    if removed is None:
        return None
    set_feedback(section, f"Task deleted: {removed['title']}", "info")
    return toast(f"Deleted task: {removed['title']}", "info")


def set_view(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["tasks"]
    if "filter_subject" in payload:
        section["filter_subject"] = text(payload, "filter_subject", "All") or "All"
    if "filter_priority" in payload:
        value = text(payload, "filter_priority", "All")
        section["filter_priority"] = value if value in PRIORITY_FILTERS else "All"
    if "sort_by" in payload:
        value = text(payload, "sort_by", "due_date")
        section["sort_by"] = value if value in SORT_OPTIONS else "due_date"
    if "show_completed" in payload:
        section["show_completed"] = flag(payload, "show_completed", True)


def toggle_show_completed(data: dict[str, Any]) -> None:
    section = data["tasks"]
    section["show_completed"] = not section["show_completed"]


# --- computed values -------------------------------------------------------


def _editing_task(section: dict[str, Any]) -> dict[str, Any]:
    for task in section["items"]:
        if task["id"] == section["editing_id"]:
            return task
    return dict(EMPTY_TASK)


def _all_subjects(section: dict[str, Any]) -> list[str]:
    found = {t["subject"] for t in section["items"] if t["subject"]}
    return ["All"] + sorted(found)


def _filtered(section: dict[str, Any]) -> list[dict[str, Any]]:
    result = list(section["items"])
    if section["filter_subject"] != "All":
        result = [t for t in result if t["subject"] == section["filter_subject"]]
    if section["filter_priority"] != "All":
        result = [t for t in result if t["priority"] == section["filter_priority"]]
    if not section["show_completed"]:
        result = [t for t in result if not t["completed"]]
    if section["sort_by"] == "due_date":
        result.sort(
            key=lambda t: (t["due_date"] or "9999-99-99", t["due_time"] or "99:99")
        )
    elif section["sort_by"] == "priority":
        result.sort(key=lambda t: PRIORITY_RANK.get(t["priority"], 3))
    elif section["sort_by"] == "title":
        result.sort(key=lambda t: t["title"].lower())
    return result


def urgent_tasks(data: dict[str, Any]) -> list[dict[str, Any]]:
    today = datetime.date.today().isoformat()
    upcoming = [
        t
        for t in data["tasks"]["items"]
        if not t["completed"] and t["due_date"] and t["due_date"] >= today
    ]
    upcoming.sort(key=lambda t: (t["due_date"], t["due_time"] or "99:99"))
    return upcoming[:5]


def view(data: dict[str, Any]) -> dict[str, Any]:
    section = data["tasks"]
    filtered = _filtered(section)
    items = section["items"]
    return {
        "items": items,
        "active": [t for t in filtered if not t["completed"]],
        "completed": [t for t in filtered if t["completed"]],
        "total_count": len(items),
        "completed_count": len([t for t in items if t["completed"]]),
        "urgent": urgent_tasks(data),
        "show_form": section["show_form"],
        "editing_id": section["editing_id"],
        "editing_task": _editing_task(section),
        "filter_subject": section["filter_subject"],
        "filter_priority": section["filter_priority"],
        "sort_by": section["sort_by"],
        "show_completed": section["show_completed"],
        "subject_options": _all_subjects(section),
        "priority_options": PRIORITY_OPTIONS,
        "priority_filters": PRIORITY_FILTERS,
        "feedback": section["feedback"],
    }
