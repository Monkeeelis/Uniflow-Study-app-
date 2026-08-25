"""Dashboard - the rotating motivational quote plus the free-running study timer."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from uniflow.services import focus, notifications
from uniflow.services.common import clamp_int, toast

MAX_TIMER_SECONDS = 24 * 60 * 60

QUOTES: list[dict[str, str]] = [
    {
        "text": "The secret of getting ahead is getting started.",
        "author": "Mark Twain",
    },
    {
        "text": "Success is the sum of small efforts, repeated day in and day out.",
        "author": "Robert Collier",
    },
    {
        "text": "Don't watch the clock; do what it does. Keep going.",
        "author": "Sam Levenson",
    },
    {
        "text": "The expert in anything was once a beginner.",
        "author": "Helen Hayes",
    },
    {
        "text": "Small daily improvements are the key to staggering long-term results.",
        "author": "Robin Sharma",
    },
    {
        "text": "You don't have to be great to start, but you have to start to be great.",
        "author": "Zig Ziglar",
    },
    {
        "text": "Focus on being productive instead of busy.",
        "author": "Tim Ferriss",
    },
    {
        "text": "Learning never exhausts the mind.",
        "author": "Leonardo da Vinci",
    },
    {
        "text": "The beautiful thing about learning is that no one can take it away from you.",
        "author": "B.B. King",
    },
    {
        "text": "Discipline is the bridge between goals and accomplishment.",
        "author": "Jim Rohn",
    },
    {
        "text": "Study while others are sleeping; work while others are loafing.",
        "author": "William A. Ward",
    },
    {
        "text": "Every accomplishment starts with the decision to try.",
        "author": "John F. Kennedy",
    },
    {
        "text": "It always seems impossible until it's done.",
        "author": "Nelson Mandela",
    },
    {
        "text": "The future depends on what you do today.",
        "author": "Mahatma Gandhi",
    },
    {
        "text": "Push yourself, because no one else is going to do it for you.",
        "author": "Anonymous",
    },
]


# Bumps quote_index, wrapping back to 0 once we hit the end of QUOTES.
def next_quote(data: dict[str, Any]) -> None:
    section = data["dashboard"]
    section["quote_index"] = (section["quote_index"] + 1) % len(QUOTES)


# If the client bothered to send a "seconds" value, trust it and store it (clamped).
def _accept_seconds(data: dict[str, Any], payload: dict[str, Any]) -> None:
    if "seconds" not in payload:
        return
    data["dashboard"]["timer_seconds"] = clamp_int(
        payload["seconds"], 0, MAX_TIMER_SECONDS
    )


# Starts the timer, or resumes it if it's already got a start time. No-op if it's already running.
def start_timer(data: dict[str, Any]) -> None:
    section = data["dashboard"]
    if section["timer_running"]:
        return
    section["timer_running"] = True
    if not section["timer_started_at"] or section["timer_seconds"] == 0:
        section["timer_started_at"] = datetime.datetime.now().isoformat()


# Stops running but keeps the elapsed seconds the client last reported.
def pause_timer(data: dict[str, Any], payload: dict[str, Any]) -> None:
    _accept_seconds(data, payload)
    data["dashboard"]["timer_running"] = False


def sync_timer(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Called periodically from the client so we don't lose progress if the tab gets closed mid-session."""
    _accept_seconds(data, payload)


# Hard reset - stops the timer and zeroes everything, nothing gets saved.
def reset_timer(data: dict[str, Any]) -> None:
    section = data["dashboard"]
    section["timer_running"] = False
    section["timer_seconds"] = 0
    section["timer_started_at"] = ""


# Stops the timer and, assuming there's actually time on the clock, logs it as a completed study session.
def stop_and_save(data: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
    section = data["dashboard"]
    _accept_seconds(data, payload)
    seconds = section["timer_seconds"]
    section["timer_running"] = False
    if seconds <= 0:
        section["timer_seconds"] = 0
        section["timer_started_at"] = ""
        return None

    now = datetime.datetime.now().isoformat()
    section["sessions"].append(
        {
            "id": str(uuid.uuid4()),
            "duration_seconds": seconds,
            "date": datetime.date.today().isoformat(),
            "started_at": section["timer_started_at"] or now,
            "ended_at": now,
        }
    )
    minutes, secs = divmod(seconds, 60)
    notifications.add(
        data,
        "Study session saved!",
        f"You studied for {minutes}m {secs}s. Nice work.",
        "success",
    )
    section["timer_seconds"] = 0
    section["timer_started_at"] = ""
    return toast(f"Saved {minutes}m {secs}s of study time.", "success")


# Drops a session from history by id.
def delete_session(data: dict[str, Any], session_id: str) -> None:
    section = data["dashboard"]
    section["sessions"] = [s for s in section["sessions"] if s["id"] != session_id]


# --- computed values -------------------------------------------------------


# Seconds -> "Xh Ym" for the totals shown on the dashboard.
def _hm_display(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


# Last 5 sessions, newest first, with duration already formatted for display.
def _recent_sessions(sessions: list[dict[str, Any]]) -> list[dict[str, str]]:
    recent = []
    for session in list(reversed(sessions))[:5]:
        hours, remainder = divmod(session["duration_seconds"], 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            duration = f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            duration = f"{minutes}m {secs}s"
        else:
            duration = f"{secs}s"
        recent.append(
            {
                "id": session["id"],
                "date": session["date"],
                "duration": duration,
            }
        )
    return recent


# Dashboard view-model - today/all-time totals plus the recent session list.
def view(data: dict[str, Any]) -> dict[str, Any]:
    section = data["dashboard"]
    sessions = section["sessions"]
    today = datetime.date.today().isoformat()
    seconds_today = sum(
        s["duration_seconds"] for s in sessions if s["date"] == today
    )
    # Study time is one pool whether it was logged from the dashboard's
    # free-running stopwatch or a Focus pomodoro/timer session, so the totals
    # shown here include both.
    focus_sessions = data["focus"]["sessions"]
    seconds_today += focus._study_seconds(focus_sessions, today)
    seconds_all = sum(s["duration_seconds"] for s in sessions) + focus._study_seconds(
        focus_sessions
    )
    return {
        "quote": QUOTES[section["quote_index"] % len(QUOTES)],
        "quote_index": section["quote_index"],
        "timer_running": section["timer_running"],
        "timer_seconds": section["timer_seconds"],
        "today_display": _hm_display(seconds_today),
        "all_display": _hm_display(seconds_all),
        "sessions_today_count": len([s for s in sessions if s["date"] == today]),
        "sessions_total": len(sessions),
        "recent_sessions": _recent_sessions(sessions),
    }
