"""Onboarding wizard plus the profile settings that reuse the same fields."""

from __future__ import annotations

from typing import Any

from uniflow.services.common import flag, positive_int, text, toast

YEAR_OPTIONS = [
    "High School",
    "Year 11",
    "Year 12",
    "Undergraduate",
    "Postgraduate",
    "Other",
]

LAST_STEP = 3


def update(data: dict[str, Any], payload: dict[str, Any]) -> None:
    ob = data["onboarding"]
    if "name" in payload:
        ob["name"] = text(payload, "name")
    if "year_level" in payload:
        value = text(payload, "year_level")
        if value in YEAR_OPTIONS or value == "":
            ob["year_level"] = value
    if "pomodoro_work" in payload:
        ob["pomodoro_work"] = positive_int(payload["pomodoro_work"], 25)
    if "pomodoro_break" in payload:
        ob["pomodoro_break"] = positive_int(payload["pomodoro_break"], 5)
    if "notifications_enabled" in payload:
        ob["notifications_enabled"] = flag(payload, "notifications_enabled")


def set_step(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Move to an explicit step, or by a relative delta (default +1), clamped
    to the wizard's bounds. Lets Back/Next buttons and step-dot clicks share
    one handler."""
    ob = data["onboarding"]
    if "step" in payload:
        target = payload["step"]
    else:
        try:
            delta = int(payload.get("delta", 1))
        except (TypeError, ValueError):
            delta = 1
        target = ob["step"] + delta
    try:
        target = int(target)
    except (TypeError, ValueError):
        target = ob["step"]
    ob["step"] = max(0, min(LAST_STEP, target))


def add_subject(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    name = text(payload, "name")
    if not name:
        return toast("Enter a subject name first.", "warning")
    subjects = data["onboarding"]["subjects"]
    if name in subjects:
        return toast(f"{name} is already on your list.", "warning")
    subjects.append(name)
    return None


def remove_subject(data: dict[str, Any], name: str) -> None:
    ob = data["onboarding"]
    ob["subjects"] = [s for s in ob["subjects"] if s != name]


def toggle_notifications(data: dict[str, Any]) -> None:
    ob = data["onboarding"]
    ob["notifications_enabled"] = not ob["notifications_enabled"]


def finish(data: dict[str, Any], device_id: str) -> dict[str, str]:
    ob = data["onboarding"]
    ob["completed"] = True
    if device_id and device_id not in ob["completed_devices"]:
        ob["completed_devices"].append(device_id)
    greeting = f"Welcome, {ob['name']}!" if ob["name"] else "Welcome to UniFlow!"
    return toast(greeting, "success")


def view(data: dict[str, Any], device_id: str) -> dict[str, Any]:
    ob = data["onboarding"]
    return {
        "completed": device_id in ob["completed_devices"],
        "step": ob["step"],
        "last_step": LAST_STEP,
        "name": ob["name"],
        "year_level": ob["year_level"],
        "year_options": YEAR_OPTIONS,
        "subjects": ob["subjects"],
        "pomodoro_work": ob["pomodoro_work"],
        "pomodoro_break": ob["pomodoro_break"],
        "notifications_enabled": ob["notifications_enabled"],
    }
