"""Focus page: pomodoro cycles, plain timer, and the study session log.

The countdown itself runs client-side — polling the server ten times a
second for a ticking clock would be silly. The browser just tells us the
elapsed time when something worth recording happens (pause, skip, phase
done), and Python handles logging sessions, advancing phases, and the
running totals.
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


# How long the current phase should run, in seconds.
def target_seconds(data: dict[str, Any]) -> int:
    section = data["focus"]
    onboarding = data["onboarding"]
    if section["mode"] == "pomodoro":
        minutes = (
            onboarding["pomodoro_work"]
            if section["pomodoro_phase"] == "work"
            else onboarding["pomodoro_break"]
        )
        return max(1, minutes) * 60
    total = section["timer_duration_minutes"] * 60 + section["timer_duration_seconds"]
    return max(1, total)


def _accept_elapsed(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Client reports elapsed time; we just clamp it to the phase's bounds."""
    if "elapsed_ds" not in payload:
        return
    section = data["focus"]
    limit = min(MAX_ELAPSED_DS, target_seconds(data) * 10)
    section["elapsed_ds"] = clamp_int(payload["elapsed_ds"], 0, limit)


# Swaps modes and wipes progress back to a clean slate.
def set_mode(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["focus"]
    mode = text(payload, "mode")
    section["mode"] = mode if mode in MODES else "timer"
    section["running"] = False
    section["elapsed_ds"] = 0
    section["pomodoro_phase"] = "work"
    section["completed_cycles"] = 0
    section["session_started_at"] = ""


# Cycle count and/or timer length, whichever fields the user actually sent.
def set_settings(data: dict[str, Any], payload: dict[str, Any]) -> None:
    section = data["focus"]
    if "total_cycles" in payload:
        section["total_cycles"] = positive_int(payload["total_cycles"], 4)
    if "timer_duration_minutes" in payload:
        section["timer_duration_minutes"] = clamp_int(
            payload["timer_duration_minutes"], 0, 999, section["timer_duration_minutes"]
        )
    if "timer_duration_seconds" in payload:
        section["timer_duration_seconds"] = clamp_int(
            payload["timer_duration_seconds"], 0, 59, section["timer_duration_seconds"]
        )


# Kick off the countdown, or resume it if it was already going.
def start(data: dict[str, Any]) -> None:
    section = data["focus"]
    if section["running"]:
        return
    section["running"] = True
    if not section["session_started_at"]:
        section["session_started_at"] = datetime.datetime.now().isoformat()


# Stop running but keep whatever elapsed time the client last reported.
def pause(data: dict[str, Any], payload: dict[str, Any]) -> None:
    _accept_elapsed(data, payload)
    data["focus"]["running"] = False


def sync(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Called on an interval from the client so a dropped connection doesn't lose progress."""
    _accept_elapsed(data, payload)


# Hard reset — same end state as a fresh set_mode, without changing mode.
def reset(data: dict[str, Any]) -> None:
    section = data["focus"]
    section["running"] = False
    section["elapsed_ds"] = 0
    section["pomodoro_phase"] = "work"
    section["completed_cycles"] = 0
    section["session_started_at"] = ""


# User bailed early — jump to the next phase without the timer hitting zero.
def skip(data: dict[str, Any], payload: dict[str, Any]) -> None:
    _accept_elapsed(data, payload)
    _advance(data, completed=False)


def complete(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Countdown hit zero client-side — snap elapsed to the target and advance."""
    section = data["focus"]
    section["elapsed_ds"] = target_seconds(data) * 10
    _accept_elapsed(data, payload)
    _advance(data, completed=True)


def _advance(data: dict[str, Any], completed: bool) -> None:
    """Log whatever phase just ended, then figure out what comes next.

    Pomodoro just cycles work -> break -> work until ``total_cycles`` work
    phases are done, then stops; timer mode has nowhere to go but stop.
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


# Records the finished phase; zero-length ones aren't worth logging.
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


# Total study-mode seconds, across everything or just one day if given.
def _study_seconds(sessions: list[dict[str, Any]], day: str | None = None) -> int:
    return sum(
        s["duration_seconds"]
        for s in sessions
        if s["mode"] in STUDY_MODES and (day is None or s["date"] == day)
    )


# Seconds -> "Xh Ym" / "Xm Ys" / "Xs", whichever units are relevant.
def _duration_label(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


# Last 8 sessions, newest first, formatted for the log table.
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


# Everything the focus page template needs: timer state, cycle dots, study totals.
def view(data: dict[str, Any]) -> dict[str, Any]:
    section = data["focus"]
    sessions = section["sessions"]
    today = datetime.date.today().isoformat()
    # Study time is one pool whether it was logged here or from the
    # dashboard's free-running stopwatch, so the totals shown here include
    # both.
    dashboard_sessions = data["dashboard"]["sessions"]
    dashboard_seconds_today = sum(
        s["duration_seconds"] for s in dashboard_sessions if s["date"] == today
    )
    dashboard_seconds_all = sum(s["duration_seconds"] for s in dashboard_sessions)
    total_minutes_all = (_study_seconds(sessions) + dashboard_seconds_all) // 60
    hours, minutes = divmod(total_minutes_all, 60)

    return {
        "mode": section["mode"],
        "running": section["running"],
        "elapsed_ds": section["elapsed_ds"],
        "pomodoro_phase": section["pomodoro_phase"],
        "completed_cycles": section["completed_cycles"],
        "total_cycles": section["total_cycles"],
        "timer_duration_minutes": section["timer_duration_minutes"],
        "timer_duration_seconds": section["timer_duration_seconds"],
        "target_seconds": target_seconds(data),
        "cycle_dots": [
            {"index": i, "filled": i < section["completed_cycles"]}
            for i in range(section["total_cycles"])
        ],
        "study_minutes_today": (_study_seconds(sessions, today) + dashboard_seconds_today)
        // 60,
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
