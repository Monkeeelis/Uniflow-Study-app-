"""Focus page: pomodoro cycles, plain timer, and the study session log.

The countdown itself ticks in the browser — it would be wasteful to poll the
server ten times a second. The browser reports the elapsed time when something
meaningful happens (pause, skip, phase complete) and Python stays in charge of
logging sessions, advancing phases and totalling the stats.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from uniflow.services import notifications
from uniflow.services.common import clamp_int, positive_int, text

MODES = ("pomodoro", "timer")
STUDY_MODES = ("pomodoro-work", "timer")
MAX_ELAPSED_DS = 24 * 60 * 60 * 10  # a day, as a sanity bound on client input


def target_seconds(data: dict[str, Any]) -> int:
    section = data["focus"]
    onboarding = data["onboarding"]
    if section["mode"] == "pomodoro":
        minutes = (
            onboarding["pomodoro_work"]
            if section["pomodoro_phase"] == "work"
            else onboarding["pomodoro_break"]
        )
    else:
        minutes = section["timer_duration_minutes"]
    return max(1, minutes) * 60


def _accept_elapsed(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Trust the browser's clock, within the bounds of the current phase."""
    if "elapsed_ds" not in payload:
        return
    section = data["focus"]
    limit = min(MAX_ELAPSED_DS, target_seconds(data) * 10)
    section["elapsed_ds"] = clamp_int(payload["elapsed_ds"], 0, limit)


def set_mode(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["focus"]
    mode = text(payload, "mode")
    section["mode"] = mode if mode in MODES else "timer"
    section["running"] = False
    section["elapsed_ds"] = 0
    section["pomodoro_phase"] = "work"
    section["completed_cycles"] = 0
    section["session_started_at"] = ""


def set_settings(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["focus"]
    if "total_cycles" in payload:
        section["total_cycles"] = positive_int(payload["total_cycles"], 4)
    if "timer_duration_minutes" in payload:
        section["timer_duration_minutes"] = positive_int(
            payload["timer_duration_minutes"], 15
        )


def start(data: dict[str, Any]) -> None:
    section = data["focus"]
    if section["running"]:
        return
    section["running"] = True
    if not section["session_started_at"]:
        section["session_started_at"] = datetime.datetime.now().isoformat()


def pause(data: dict[str, Any], payload: dict[str, Any]) -> None:
    _accept_elapsed(data, payload)
    data["focus"]["running"] = False


def sync(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Periodic heartbeat so a closed tab doesn't lose the running phase."""
    _accept_elapsed(data, payload)


def reset(data: dict[str, Any]) -> None:
    section = data["focus"]
    section["running"] = False
    section["elapsed_ds"] = 0
    section["pomodoro_phase"] = "work"
    section["completed_cycles"] = 0
    section["session_started_at"] = ""


def skip(data: dict[str, Any], payload: dict[str, Any]) -> None:
    _accept_elapsed(data, payload)
    _advance(data, completed=False)


def complete(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Called by the browser when the countdown reaches the target."""
    section = data["focus"]
    section["elapsed_ds"] = target_seconds(data) * 10
    _accept_elapsed(data, payload)
    _advance(data, completed=True)


def _advance(data: dict[str, Any], completed: bool) -> None:
    """Log the phase that just ended and move to the next one.

    Pomodoro alternates work -> break -> work, ending the whole set once
    ``total_cycles`` work phases are done; plain timer mode just stops.
    """
    section = data["focus"]
    seconds = section["elapsed_ds"] // 10
    now = datetime.datetime.now().isoformat()

    if section["mode"] == "pomodoro":
        if section["pomodoro_phase"] == "work":
            _log_session(data, "pomodoro-work", seconds, completed)
            section["completed_cycles"] += 1
            section["pomodoro_phase"] = "break"
            section["elapsed_ds"] = 0
            section["session_started_at"] = now
            notifications.add(
                data,
                "Work session complete!",
                "Time for a break. You earned it.",
                "success",
            )
            if section["completed_cycles"] >= section["total_cycles"]:
                section["running"] = False
                notifications.add(
                    data,
                    "Pomodoro set complete!",
                    f"You finished {section['total_cycles']} cycles.",
                    "success",
                )
        else:
            _log_session(data, "pomodoro-break", seconds, completed)
            section["pomodoro_phase"] = "work"
            section["elapsed_ds"] = 0
            section["session_started_at"] = now
            notifications.add(data, "Break over", "Back to focus!", "info")
    else:
        _log_session(data, "timer", seconds, completed)
        section["running"] = False
        section["elapsed_ds"] = 0
        section["session_started_at"] = ""
        notifications.add(data, "Timer finished!", "Nice work.", "success")


def _log_session(
    data: dict[str, Any], mode: str, seconds: int, completed: bool
) -> None:
    if seconds <= 0:
        return
    section = data["focus"]
    now = datetime.datetime.now().isoformat()
    section["sessions"].append(
        {
            "id": str(uuid.uuid4()),
            "mode": mode,
            "duration_seconds": seconds,
            "date": datetime.date.today().isoformat(),
            "completed": completed,
            "started_at": section["session_started_at"] or now,
            "ended_at": now,
        }
    )


# --- computed values -------------------------------------------------------


def _study_seconds(sessions: list[dict[str, Any]], day: str | None = None) -> int:
    return sum(
        s["duration_seconds"]
        for s in sessions
        if s["mode"] in STUDY_MODES and (day is None or s["date"] == day)
    )


def _duration_label(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _recent_sessions(sessions: list[dict[str, Any]]) -> list[dict[str, str]]:
    labels = {"pomodoro-break": "Break", "timer": "Timer"}
    recent = []
    for session in list(reversed(sessions))[:8]:
        recent.append(
            {
                "id": session["id"],
                "mode": labels.get(session["mode"], "Pomodoro"),
                "date": session["date"],
                "duration": _duration_label(session["duration_seconds"]),
                "completed": "yes" if session["completed"] else "no",
            }
        )
    return recent


def view(data: dict[str, Any]) -> dict[str, Any]:
    section = data["focus"]
    sessions = section["sessions"]
    today = datetime.date.today().isoformat()
    total_minutes_all = _study_seconds(sessions) // 60
    hours, minutes = divmod(total_minutes_all, 60)

    return {
        "mode": section["mode"],
        "running": section["running"],
        "elapsed_ds": section["elapsed_ds"],
        "pomodoro_phase": section["pomodoro_phase"],
        "completed_cycles": section["completed_cycles"],
        "total_cycles": section["total_cycles"],
        "timer_duration_minutes": section["timer_duration_minutes"],
        "target_seconds": target_seconds(data),
        "cycle_dots": [
            {"index": i, "filled": i < section["completed_cycles"]}
            for i in range(section["total_cycles"])
        ],
        "study_minutes_today": _study_seconds(sessions, today) // 60,
        "study_hours_all": f"{hours}h {minutes}m",
        "sessions_today": len(
            [s for s in sessions if s["date"] == today and s["mode"] in STUDY_MODES]
        ),
        "pomodoros_completed_today": len(
            [
                s
                for s in sessions
                if s["mode"] == "pomodoro-work"
                and s["date"] == today
                and s["completed"]
            ]
        ),
        "timers_completed_today": len(
            [
                s
                for s in sessions
                if s["mode"] == "timer" and s["date"] == today and s["completed"]
            ]
        ),
        "recent_sessions": _recent_sessions(sessions),
    }
