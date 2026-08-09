"""Streak counting and the matching encouragement line."""

from __future__ import annotations

import datetime
from typing import Any


def _active_dates(data: dict[str, Any]) -> set[str]:
    dates = {s["date"] for s in data["focus"]["sessions"]}
    for task in data["tasks"]["items"]:
        if task["completed"] and task["due_date"]:
            dates.add(task["due_date"])
    return dates


def streak_days(data: dict[str, Any]) -> int:
    active = _active_dates(data)
    if not active:
        return 0

    today = datetime.date.today()
    # A streak that hasn't been extended yet today still counts from yesterday.
    start = today if today.isoformat() in active else today - datetime.timedelta(days=1)
    streak = 0
    day = start
    while day.isoformat() in active:
        streak += 1
        day -= datetime.timedelta(days=1)
    return streak


def motivation_message(streak: int) -> str:
    if streak == 0:
        return "Start a session today to begin your streak!"
    if streak < 3:
        return f"Great start — {streak} day streak. Keep it going!"
    if streak < 7:
        return f"🔥 {streak} days in a row! You're building momentum."
    return f"🔥🔥 {streak} day streak! You're on fire."


def view(data: dict[str, Any]) -> dict[str, Any]:
    streak = streak_days(data)
    return {
        "streak_days": streak,
        "motivation_message": motivation_message(streak),
    }
