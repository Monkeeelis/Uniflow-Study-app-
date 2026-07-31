"""In-app notification feed shown in the navbar bell."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

MAX_NOTIFICATIONS = 50


def add(data: dict[str, Any], title: str, message: str, kind: str = "info") -> None:
    if not data["onboarding"]["notifications_enabled"]:
        return
    items = data["notifications"]["items"]
    items.insert(
        0,
        {
            "id": str(uuid.uuid4()),
            "title": title,
            "message": message,
            "kind": kind,
            "timestamp": datetime.datetime.now().strftime("%H:%M"),
            "read": False,
        },
    )
    del items[MAX_NOTIFICATIONS:]


def toggle_panel(data: dict[str, Any]) -> None:
    section = data["notifications"]
    section["show_panel"] = not section["show_panel"]


def mark_all_read(data: dict[str, Any]) -> None:
    for item in data["notifications"]["items"]:
        item["read"] = True


def clear_all(data: dict[str, Any]) -> None:
    data["notifications"]["items"] = []


def dismiss(data: dict[str, Any], notification_id: str) -> None:
    section = data["notifications"]
    section["items"] = [n for n in section["items"] if n["id"] != notification_id]


def view(data: dict[str, Any]) -> dict[str, Any]:
    section = data["notifications"]
    return {
        "items": section["items"],
        "show_panel": section["show_panel"],
        "unread_count": sum(1 for n in section["items"] if not n["read"]),
    }
