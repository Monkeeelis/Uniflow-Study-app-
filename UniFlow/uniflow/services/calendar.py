"""Calendar service - events, categories, month/week/day layouts.

The grid positioning math is done here on purpose, not in JS, so the
views stay a faithful port of the original Python.
"""

from __future__ import annotations

import calendar as pycal
import datetime
import logging
import uuid
from typing import Any

from uniflow.services.common import flag, set_feedback, text, toast

GRID_START_HOUR = 6
GRID_HOURS = 18  # 6am -> midnight
HOUR_HEIGHT_PX = 48
DEFAULT_TASK_DURATION_MIN = 60
DEFAULT_COLOR = "#b45309"
VIEW_MODES = ("month", "week", "day")

EMPTY_EVENT: dict[str, Any] = {
    "id": "",
    "title": "",
    "category": "",
    "date": "",
    "start_time": "",
    "end_time": "",
    "notes": "",
    "color": DEFAULT_COLOR,
}


# "HH:MM" -> (hour, minute); None if it's empty or malformed.
def _parse_hm(value: str) -> tuple[int, int] | None:
    if not value:
        return None
    try:
        parts = value.split(":")
        if len(parts) != 2:
            return None
        hour, minute = int(parts[0]), int(parts[1])
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            return None
        return hour, minute
    except (TypeError, ValueError) as e:
        logging.exception(f"Error parsing time value: {e}")
        return None


# Inverse of _parse_hm - minutes since midnight back to "HH:MM", clamped so it can't spill into the next day.
def _format_hm(total_min: int) -> str:
    total_min = max(0, min(24 * 60 - 1, total_min))
    hour, minute = divmod(total_min, 60)
    return f"{hour:02d}:{minute:02d}"


# "Xh Ym" for the duration chip on an event block.
def _format_duration_label(minutes: int) -> str:
    if minutes <= 0:
        return ""
    hours, mins = divmod(minutes, 60)
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    if hours > 0:
        return f"{hours}h"
    return f"{mins}m"


# Pulls the stored year/month/day out of section; if it's ever corrupt we just fall back to today rather than blow up.
def _current_date(section: dict[str, Any]) -> datetime.date:
    current = section["current"]
    try:
        return datetime.date(current["year"], current["month"], current["day"])
    except (TypeError, ValueError):
        today = datetime.date.today()
        section["current"] = {
            "year": today.year,
            "month": today.month,
            "day": today.day,
        }
        return today


# Counterpart to _current_date - splits a date object back into the section's fields.
def _store_date(section: dict[str, Any], value: datetime.date) -> None:
    section["current"] = {
        "year": value.year,
        "month": value.month,
        "day": value.day,
    }

# The title above the grid - "August 2026", a week range, or a full day name depending on view_mode.
def header_label(section: dict[str, Any]) -> str:
    current = _current_date(section)
    if section["view_mode"] == "month":
        return f"{pycal.month_name[current.month]} {current.year}"
    if section["view_mode"] == "week":
        start = current - datetime.timedelta(days=current.weekday())
        end = start + datetime.timedelta(days=6)
        return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
    return current.strftime("%A, %B %d, %Y")


# --- actions ---------------------------------------------------------------


# Wipes whatever feedback banner is currently showing.
def clear_feedback(data: dict[str, Any]) -> None:
    set_feedback(data["calendar"], "", "")


# Handles the month/week/day toggle.
def set_view(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["calendar"]
    view_mode = text(payload, "view")
    if view_mode not in VIEW_MODES:
        return toast("Unknown calendar view.", "warning")
    section["view_mode"] = view_mode
    set_feedback(section, "", "")
    return toast(f"Showing {view_mode} view.", "info")


# Handles the today/prev/next buttons - steps by a month, week, or day depending on which view is active.
def navigate(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["calendar"]
    direction = text(payload, "direction")
    if direction == "today":
        _store_date(section, datetime.date.today())
        set_feedback(section, "", "")
        return toast("Showing today.", "info")
    if direction not in ("prev", "next"):
        return toast("Unknown calendar move.", "warning")

    step = 1 if direction == "next" else -1
    current = _current_date(section)
    if section["view_mode"] == "month":
        month = current.month + step
        year = current.year
        if month < 1:
            month, year = 12, year - 1
        elif month > 12:
            month, year = 1, year + 1
        day = min(current.day, pycal.monthrange(year, month)[1])
        _store_date(section, datetime.date(year, month, day))
    else:
        days = 7 if section["view_mode"] == "week" else 1
        _store_date(section, current + datetime.timedelta(days=days * step))
    set_feedback(section, "", "")
    return toast(f"Moved to {header_label(section)}.", "info")


# Opens the create/edit event form (or closes it). Task-backed events get redirected to the Tasks page instead.
def set_event_form(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["calendar"]
    if not flag(payload, "open", True):
        section["show_event_form"] = False
        section["editing_event_id"] = ""
        return None

    event_id = text(payload, "event_id")
    if event_id:
        if event_id.startswith("task_"):
            set_feedback(
                section,
                "Task events are managed from Tasks and cannot be edited here.",
                "warning",
            )
            return toast("Edit the original task from the Tasks page.", "warning")
        for event in section["events"]:
            if event["id"] == event_id:
                section["selected_date"] = event["date"]
                section["editing_event_id"] = event_id
                section["show_event_form"] = True
                section["show_event_detail"] = False
                set_feedback(section, f"Editing event: {event['title']}", "info")
                return None
        set_feedback(section, "That event is no longer available.", "warning")
        return toast("That event could not be found.", "warning")

    chosen_date = text(payload, "date") or datetime.date.today().isoformat()
    section["selected_date"] = chosen_date
    section["editing_event_id"] = ""
    section["show_event_detail"] = False
    section["show_event_form"] = True
    set_feedback(section, f"Ready to add an event on {chosen_date}.", "info")
    return None


# Everything the event form needs before it can be saved - title, date, times all get checked, then we either create a new event or overwrite the one being edited.
def submit_event(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["calendar"]
    title = text(payload, "title")
    date_value = text(payload, "date") or section["selected_date"]
    if not title:
        set_feedback(section, "Please enter an event title.", "warning")
        return toast("Please enter an event title.", "warning")
    if not date_value:
        set_feedback(section, "Please choose a date for the event.", "warning")
        return toast("Please choose a date.", "warning")
    try:
        datetime.date.fromisoformat(date_value)
    except (TypeError, ValueError) as e:
        logging.exception(f"Error validating event date: {e}")
        set_feedback(section, "Please choose a valid date.", "warning")
        return toast("Please choose a valid date.", "warning")

    start_time = text(payload, "start_time")
    end_time = text(payload, "end_time")
    if start_time and _parse_hm(start_time) is None:
        set_feedback(section, "Please choose a valid start time.", "warning")
        return toast("Please choose a valid start time.", "warning")
    if end_time and _parse_hm(end_time) is None:
        set_feedback(section, "Please choose a valid end time.", "warning")
        return toast("Please choose a valid end time.", "warning")

    category = text(payload, "category")
    color = DEFAULT_COLOR
    for entry in section["categories"]:
        if entry["name"] == category:
            color = entry["color"]
            break

    editing_id = section["editing_event_id"]
    saved = {
        "id": editing_id or str(uuid.uuid4()),
        "title": title,
        "category": category,
        "date": date_value,
        "start_time": start_time,
        "end_time": end_time,
        "notes": text(payload, "notes"),
        "color": color,
    }
    if editing_id:
        updated = False
        for index, event in enumerate(section["events"]):
            if event["id"] == editing_id:
                section["events"][index] = saved
                updated = True
                break
        if not updated:
            set_feedback(section, "That event could not be updated.", "warning")
            return toast("That event no longer exists.", "warning")
    else:
        section["events"].append(saved)

    section["show_event_form"] = False
    section["editing_event_id"] = ""
    section["selected_date"] = date_value
    action = "updated" if editing_id else "created"
    set_feedback(section, f"Event {action}: {title}", "success")
    return toast(f"Event {action}: {title}", "success")


# Deletes by id - refuses task_ prefixed ids since those aren't real events, just projections of a task.
def delete_event(data: dict[str, Any], event_id: str) -> dict[str, str] | None:
    section = data["calendar"]
    section["show_event_detail"] = False
    section["show_event_form"] = False
    if event_id.startswith("task_"):
        set_feedback(section, "Task events cannot be deleted from Calendar.", "warning")
        return toast("Delete the original task from the Tasks page.", "warning")

    removed = None
    remaining = []
    for event in section["events"]:
        if event["id"] == event_id:
            removed = event
        else:
            remaining.append(event)
    section["events"] = remaining
    if removed is None:
        set_feedback(section, "That event was already removed.", "warning")
        return toast("That event could not be found.", "warning")
    set_feedback(section, f"Deleted event: {removed['title']}", "success")
    return toast(f"Deleted event: {removed['title']}", "success")


# Toggles the read-only detail popup.
def set_event_detail(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["calendar"]
    if flag(payload, "open", True):
        section["detail_event_id"] = text(payload, "event_id")
        section["show_event_detail"] = True
    else:
        section["show_event_detail"] = False
        section["detail_event_id"] = ""


# Just flips show_category_form.
def toggle_category_form(data: dict[str, Any]) -> None:
    section = data["calendar"]
    section["show_category_form"] = not section["show_category_form"]


# Adds a category - name comparison is case-insensitive so "Study" and "study" can't both exist.
def add_category(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["calendar"]
    name = text(payload, "name")
    color = text(payload, "color") or DEFAULT_COLOR
    if not name:
        set_feedback(section, "Enter a category name first.", "warning")
        return toast("Enter a category name first.", "warning")
    for entry in section["categories"]:
        if entry["name"].casefold() == name.casefold():
            set_feedback(section, "That category already exists.", "warning")
            return toast("That category already exists.", "warning")
    section["categories"].append({"name": name, "color": color})
    section["show_category_form"] = False
    set_feedback(section, f"Category added: {name}", "success")
    return toast(f"Category added: {name}", "success")


# Removing a category doesn't touch events already using it - they just keep their color as-is.
def remove_category(data: dict[str, Any], name: str) -> dict[str, str]:
    section = data["calendar"]
    remaining = [c for c in section["categories"] if c["name"] != name]
    found = len(remaining) != len(section["categories"])
    section["categories"] = remaining
    if not found:
        set_feedback(section, "That category was already removed.", "warning")
        return toast("That category was not found.", "warning")
    set_feedback(
        section,
        f"Category removed: {name}. Existing events keep their colors.",
        "success",
    )
    return toast(f"Removed category: {name}", "success")


# --- computed values -------------------------------------------------------


def _task_events(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Reshape calendar-enabled tasks so they look like events.

    Give a task with a due time a default duration so it takes up a real
    block on the day/week grids - tasks with no time just show up unpositioned.
    """
    result = []
    for task in data["tasks"]["items"]:
        if not task["show_on_calendar"] or not task["due_date"]:
            continue
        start = task["due_time"] or ""
        end = ""
        if start:
            parsed = _parse_hm(start)
            if parsed is not None:
                hour, minute = parsed
                end = _format_hm(hour * 60 + minute + DEFAULT_TASK_DURATION_MIN)
        result.append(
            {
                "id": f"task_{task['id']}",
                "title": f"📝 {task['title']}",
                "category": task["subject"] or task["category"] or "Task",
                "date": task["due_date"],
                "start_time": start,
                "end_time": end,
                "notes": task["notes"],
                "color": "#8b6f47" if task["completed"] else "#0d9488",
            }
        )
    return result


# Real events plus the synthetic ones generated from tasks, merged into one list.
def all_events(data: dict[str, Any]) -> list[dict[str, Any]]:
    return data["calendar"]["events"] + _task_events(data)


# Month view grid: 7 columns, padded with blank cells at the start/end so weeks line up.
def _month_cells(section: dict[str, Any]) -> list[dict[str, str]]:
    current = _current_date(section)
    first_day = datetime.date(current.year, current.month, 1)
    days_in_month = pycal.monthrange(current.year, current.month)[1]
    today = datetime.date.today()

    blank = {"date": "", "day": "", "in_month": "false", "is_today": "false"}
    cells: list[dict[str, str]] = [dict(blank) for _ in range(first_day.weekday())]
    for day in range(1, days_in_month + 1):
        date_obj = datetime.date(current.year, current.month, day)
        cells.append(
            {
                "date": date_obj.isoformat(),
                "day": str(day),
                "in_month": "true",
                "is_today": "true" if date_obj == today else "false",
            }
        )
    while len(cells) % 7 != 0:
        cells.append(dict(blank))
    return cells


# Buckets events by date; within a day, sorted by start time with all-day events pushed to the end.
def _events_by_date(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        grouped.setdefault(event["date"], []).append(event)
    for day in grouped:
        grouped[day].sort(key=lambda e: e["start_time"] or "99:99")
    return grouped


def _to_timed_block(event: dict[str, Any]) -> dict[str, Any] | None:
    """Turn a timed event into a pixel-positioned block for the day/week grid.

    All-day events (no start time) return None here. Anything that starts
    before the grid's visible window or runs past midnight gets clipped so
    it stays inside the grid instead of overflowing.
    """
    parsed = _parse_hm(event["start_time"])
    if parsed is None:
        return None
    start_hour, start_minute = parsed
    start_min = start_hour * 60 + start_minute

    end_parsed = _parse_hm(event["end_time"])
    if end_parsed is not None:
        end_hour, end_minute = end_parsed
        end_min = end_hour * 60 + end_minute
        if end_min <= start_min:
            end_min = start_min + 30
    else:
        end_min = start_min + DEFAULT_TASK_DURATION_MIN

    # Keep blocks inside the single-day grid, including events that begin
    # before 06:00 or run past midnight.
    end_min = min(24 * 60, end_min)
    grid_start_min = GRID_START_HOUR * 60
    visible_start_min = max(0, start_min)
    visible_end_min = max(visible_start_min + 30, end_min)
    duration = max(30, visible_end_min - visible_start_min)
    top_px = max(0.0, (visible_start_min - grid_start_min) * (HOUR_HEIGHT_PX / 60))
    if visible_start_min < grid_start_min:
        duration = max(30, visible_end_min - grid_start_min)
    height_px = max(28.0, duration * (HOUR_HEIGHT_PX / 60))
    return {
        "id": event["id"],
        "title": event["title"],
        "category": event["category"],
        "color": event["color"],
        "start_time": event["start_time"],
        "end_time": _format_hm(end_min),
        "duration_label": _format_duration_label(visible_end_min - visible_start_min),
        "notes": event["notes"],
        "top": round(top_px, 1),
        "height": round(height_px, 1),
    }


def _assign_lanes(blocks: list[dict[str, Any]]) -> None:
    """Spread overlapping blocks into side-by-side columns instead of letting
    them stack on top of each other.

    Basically greedy interval-graph colouring - walk blocks in start order
    and drop each into the first lane whose previous occupant has already
    finished. Then group blocks into clusters of things that transitively
    overlap, and stretch every block in a cluster to divide that cluster's
    width evenly across however many lanes it actually needed (not some
    fixed max), so a pair of overlapping events get 50% each and a three-way
    overlap gets a third each.
    """
    blocks.sort(key=lambda b: b["top"])
    lane_ends: list[float] = []
    for block in blocks:
        start = block["top"]
        end = start + block["height"]
        lane = next((i for i, e in enumerate(lane_ends) if start >= e), None)
        if lane is None:
            lane = len(lane_ends)
            lane_ends.append(end)
        else:
            lane_ends[lane] = end
        block["_lane"] = lane

    cluster: list[dict[str, Any]] = []
    cluster_end = float("-inf")
    clusters: list[list[dict[str, Any]]] = []
    for block in blocks:
        start = block["top"]
        end = start + block["height"]
        if cluster and start < cluster_end:
            cluster.append(block)
            cluster_end = max(cluster_end, end)
        else:
            if cluster:
                clusters.append(cluster)
            cluster = [block]
            cluster_end = end
    if cluster:
        clusters.append(cluster)

    for group in clusters:
        lane_count = max(b["_lane"] for b in group) + 1
        for block in group:
            block["left_pct"] = round(100 * block["_lane"] / lane_count, 2)
            block["width_pct"] = round(100 / lane_count, 2)
            del block["_lane"]


# Runs every timed event through _to_timed_block + _assign_lanes and groups the result by date.
def _positioned_by_date(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        block = _to_timed_block(event)
        if block is None:
            continue
        grouped.setdefault(event["date"], []).append(block)
    for day in grouped:
        _assign_lanes(grouped[day])
    return grouped


# Same grouping idea as above, but for events with no start time.
def _all_day_by_date(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if not event["start_time"]:
            grouped.setdefault(event["date"], []).append(event)
    return grouped


# The 6am-midnight labels running down the left edge of the day/week grid.
def _hour_labels() -> list[dict[str, str]]:
    labels = []
    for index in range(GRID_HOURS):
        hour = GRID_START_HOUR + index
        display_hour = hour % 12 or 12
        labels.append(
            {
                "hour": str(hour),
                "label": f"{display_hour} {'AM' if hour < 12 else 'PM'}",
                "military": f"{hour:02d}:00",
            }
        )
    return labels


# Mon-Sun header strip for the week view, with today flagged.
def _week_days(section: dict[str, Any]) -> list[dict[str, str]]:
    current = _current_date(section)
    start = current - datetime.timedelta(days=current.weekday())
    today = datetime.date.today()
    days = []
    for offset in range(7):
        day = start + datetime.timedelta(days=offset)
        days.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a %d"),
                "is_today": "true" if day == today else "false",
            }
        )
    return days


# Everything the template needs to render whichever view is active, in one dict.
def view(data: dict[str, Any]) -> dict[str, Any]:
    section = data["calendar"]
    events = all_events(data)
    current = _current_date(section)

    detail_event = dict(EMPTY_EVENT)
    for event in events:
        if event["id"] == section["detail_event_id"]:
            detail_event = event
            break

    editing_event = dict(EMPTY_EVENT)
    editing_event["date"] = section["selected_date"]
    for event in section["events"]:
        if event["id"] == section["editing_event_id"]:
            editing_event = event
            break

    return {
        "events": section["events"],
        "categories": section["categories"],
        "category_names": [c["name"] for c in section["categories"]],
        "view_mode": section["view_mode"],
        "header_label": header_label(section),
        "month_name": pycal.month_name[current.month],
        "current": section["current"],
        "day_date_str": current.isoformat(),
        "month_cells": _month_cells(section),
        "week_days": _week_days(section),
        "events_by_date": _events_by_date(events),
        "positioned_events_by_date": _positioned_by_date(events),
        "all_day_events_by_date": _all_day_by_date(events),
        "hour_labels": _hour_labels(),
        "grid_height_px": GRID_HOURS * HOUR_HEIGHT_PX,
        "hour_height_px": HOUR_HEIGHT_PX,
        "show_event_form": section["show_event_form"],
        "editing_event_id": section["editing_event_id"],
        "editing_event": editing_event,
        "selected_date": section["selected_date"],
        "show_event_detail": section["show_event_detail"],
        "detail_event_id": section["detail_event_id"],
        "detail_event": detail_event,
        "show_category_form": section["show_category_form"],
        "default_category_color": DEFAULT_COLOR,
        "feedback": section["feedback"],
    }
