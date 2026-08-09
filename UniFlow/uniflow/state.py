"""Assembles the single view model the browser renders from."""

from __future__ import annotations

from typing import Any

from uniflow.services import (
    calendar,
    dashboard,
    flashcards,
    focus,
    insights,
    notes,
    notifications,
    onboarding,
    stats,
    tasks,
)

def build_state(data: dict[str, Any], device_id: str = "") -> dict[str, Any]:
    return {
        "onboarding": onboarding.view(data, device_id),
        "tasks": tasks.view(data),
        "calendar": calendar.view(data),
        "focus": focus.view(data),
        "dashboard": dashboard.view(data),
        "flashcards": flashcards.view(data),
        "notes": notes.view(data),
        "notifications": notifications.view(data),
        "insights": insights.view(data),
        "stats": stats.view(data),
    }
