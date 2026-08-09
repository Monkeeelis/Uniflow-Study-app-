"""Study-time heatmap and the summary metrics beside it."""

from __future__ import annotations

import datetime
from typing import Any

from uniflow.services.common import text
from uniflow.services.focus import STUDY_MODES

RANGE_MODES = ("week", "month", "year")
YEAR_WEEKS = 53
RANGE_LABELS = {
    "week": "Past 7 days",
    "month": "Past 30 days",
    "year": "Past year",
}


def set_range(data: dict[str, Any], payload: dict[str, Any]) -> None:
    mode = text(payload, "mode")
    if mode in RANGE_MODES:
        data["insights"]["range_mode"] = mode


def _minutes_by_date(data: dict[str, Any]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for session in data["dashboard"]["sessions"]:
        totals[session["date"]] = (
            totals.get(session["date"], 0) + session["duration_seconds"]
        )
    for session in data["focus"]["sessions"]:
        if session["mode"] in STUDY_MODES:
            totals[session["date"]] = (
                totals.get(session["date"], 0) + session["duration_seconds"]
            )
    return {day: seconds // 60 for day, seconds in totals.items()}


def _level(minutes: int, max_minutes: int) -> int:
    if minutes <= 0:
        return 0
    if max_minutes <= 0:
        return 1
    ratio = minutes / max_minutes
    if ratio < 0.25:
        return 1
    if ratio < 0.5:
        return 2
    if ratio < 0.8:
        return 3
    return 4


def _dates_in_range(range_mode: str, today: datetime.date) -> list[datetime.date]:
    if range_mode == "week":
        days = 7
    elif range_mode == "month":
        days = 30
    else:
        # 53 weeks ending with the current week, so the grid aligns by weekday.
        end_of_week = today + datetime.timedelta(days=6 - today.weekday())
        start = end_of_week - datetime.timedelta(days=YEAR_WEEKS * 7 - 1)
        return [
            start + datetime.timedelta(days=i) for i in range(YEAR_WEEKS * 7)
        ]
    start = today - datetime.timedelta(days=days - 1)
    return [start + datetime.timedelta(days=i) for i in range(days)]


def heatmap_cells(data: dict[str, Any]) -> list[dict[str, Any]]:
    range_mode = data["insights"]["range_mode"]
    minutes_map = _minutes_by_date(data)
    today = datetime.date.today()
    dates = _dates_in_range(range_mode, today)
    max_minutes = max(
        (minutes_map.get(d.isoformat(), 0) for d in dates), default=0
    )

    cells = []
    for day in dates:
        iso = day.isoformat()
        minutes = minutes_map.get(iso, 0)
        in_range = not (range_mode == "year" and day > today)
        cells.append(
            {
                "date": iso,
                "label": day.strftime("%a, %b %d"),
                "minutes": minutes,
                "level": _level(minutes, max_minutes) if in_range else 0,
                "weekday": day.weekday(),
                "is_today": day == today,
                "in_range": in_range,
            }
        )
    return cells


def _hm_display(minutes: int) -> str:
    hours, mins = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def view(data: dict[str, Any]) -> dict[str, Any]:
    range_mode = data["insights"]["range_mode"]
    cells = heatmap_cells(data)
    in_range = [c for c in cells if c["in_range"]]
    total_minutes = sum(c["minutes"] for c in in_range)
    active_days = len([c for c in in_range if c["minutes"] > 0])
    best = max(in_range, key=lambda c: c["minutes"], default=None)
    average = total_minutes // active_days if active_days else 0

    return {
        "range_mode": range_mode,
        "range_label": RANGE_LABELS[range_mode],
        "cells": cells,
        "total_display": _hm_display(total_minutes),
        "active_days": active_days,
        "average_display": _hm_display(average),
        "best_display": _hm_display(best["minutes"]) if best else "0m",
        "best_day_label": (
            best["label"] if best is not None and best["minutes"] > 0 else "—"
        ),
    }
