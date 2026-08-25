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

THEME_OPTIONS = [
    {"value": "light", "label": "Cream (default)"},
    {"value": "high-contrast", "label": "High Contrast"},
    {"value": "ocean", "label": "Ocean"},
    {"value": "purple", "label": "Purple & Yellow"},
    {"value": "pink", "label": "Pink"},
]

COLORBLIND_OPTIONS = [
    {"value": "none", "label": "Off"},
    {"value": "protanopia", "label": "Protanopia (red-weak)"},
    {"value": "deuteranopia", "label": "Deuteranopia (green-weak)"},
    {"value": "tritanopia", "label": "Tritanopia (blue-weak)"},
    {"value": "deuteranomaly", "label": "Deuteranomaly (green-shifted)"},
    {"value": "achromatopsia", "label": "Achromatopsia (no colour)"},
]

LAST_STEP = 3


# Only touches the onboarding/profile fields that showed up in the payload.
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
    if "weekly_goal_minutes" in payload:
        ob["weekly_goal_minutes"] = positive_int(payload["weekly_goal_minutes"], 300)
    if "notifications_enabled" in payload:
        ob["notifications_enabled"] = flag(payload, "notifications_enabled")


# Jump to a specific wizard step, or nudge it by a delta if no step was given; either way we clamp to [0, LAST_STEP].
def set_step(data: dict[str, Any], payload: dict[str, Any]) -> None:
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


# Bail out with a toast if the name is blank or already in the list.
def add_subject(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    name = text(payload, "name")
    if not name:
        return toast("Enter a subject name first.", "warning")
    subjects = data["onboarding"]["subjects"]
    if name in subjects:
        return toast(f"{name} is already on your list.", "warning")
    subjects.append(name)
    return None


# Drop a subject by name, nothing fancy.
def remove_subject(data: dict[str, Any], name: str) -> None:
    ob = data["onboarding"]
    ob["subjects"] = [s for s in ob["subjects"] if s != name]


# Just a toggle for the notifications pref.
def toggle_notifications(data: dict[str, Any]) -> None:
    ob = data["onboarding"]
    ob["notifications_enabled"] = not ob["notifications_enabled"]


# Same idea, but for dark mode.
def toggle_theme(data: dict[str, Any]) -> None:
    ob = data["onboarding"]
    ob["dark_mode"] = not ob["dark_mode"]


# Ignores the request silently if the theme value isn't one we recognise.
def set_theme(data: dict[str, Any], payload: dict[str, Any]) -> None:
    value = text(payload, "theme")
    if value in {option["value"] for option in THEME_OPTIONS}:
        data["onboarding"]["theme"] = value


# Same pattern as set_theme, but for the colourblind filter.
def set_colorblind_mode(data: dict[str, Any], payload: dict[str, Any]) -> None:
    value = text(payload, "mode")
    if value in {option["value"] for option in COLORBLIND_OPTIONS}:
        data["onboarding"]["colorblind_mode"] = value


# Marks this device as done with onboarding and sends back a greeting toast.
def finish(data: dict[str, Any], device_id: str) -> dict[str, str]:
    ob = data["onboarding"]
    ob["completed"] = True
    if device_id and device_id not in ob["completed_devices"]:
        ob["completed_devices"].append(device_id)
    greeting = f"Welcome, {ob['name']}!" if ob["name"] else "Welcome to UniFlow!"
    return toast(greeting, "success")


# Everything the onboarding/profile screen needs, bundled up for this device.
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
        "weekly_goal_minutes": ob["weekly_goal_minutes"],
        "notifications_enabled": ob["notifications_enabled"],
        "theme": ob["theme"],
        "theme_options": THEME_OPTIONS,
        "dark_mode": ob["dark_mode"],
        "colorblind_mode": ob["colorblind_mode"],
        "colorblind_options": COLORBLIND_OPTIONS,
    }
