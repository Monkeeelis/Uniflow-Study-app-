"""JSON-file persistence for UniFlow.

The Reflex build kept everything in per-session server memory, so closing the
tab lost the lot. Now that the browser owns the UI, one JSON document on disk
holds the whole app and survives restarts.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(
    os.environ.get("UNIFLOW_DATA_DIR", PACKAGE_DIR.parent / "data")
)
DATA_FILE = DATA_DIR / "uniflow.json"  # legacy single-shared-file location

# Each browser gets its own file here, keyed by the device-id cookie app.py
# already sets — so hosting the app publicly (e.g. on PythonAnywhere) no
# longer means every visitor reads and writes the same document.
DEVICES_DIR = DATA_DIR / "devices"
_migration_lock = threading.Lock()

DEFAULT_CATEGORIES: list[dict[str, str]] = [
    {"name": "Class", "color": "#b45309"},
    {"name": "Study", "color": "#0d9488"},
    {"name": "Exam", "color": "#dc2626"},
    {"name": "Personal", "color": "#7c3aed"},
]


def default_data() -> dict[str, Any]:
    today = datetime.date.today()
    return {
        "onboarding": {
            "completed": False,
            "completed_devices": [],
            "step": 0,
            "name": "",
            "year_level": "",
            "subjects": [],
            "pomodoro_work": 25,
            "pomodoro_break": 5,
            "weekly_goal_minutes": 300,
            "notifications_enabled": True,
            "theme": "light",
            "dark_mode": False,
            "colorblind_mode": "none",
        },
        "tasks": {
            "items": [],
            "show_form": False,
            "editing_id": "",
            "filter_subject": "All",
            "filter_priority": "All",
            "sort_by": "due_date",
            "show_completed": True,
            "feedback": {"message": "", "kind": ""},
        },
        "calendar": {
            "events": [],
            "categories": [dict(c) for c in DEFAULT_CATEGORIES],
            "view_mode": "month",
            "current": {
                "year": today.year,
                "month": today.month,
                "day": today.day,
            },
            "show_event_form": False,
            "editing_event_id": "",
            "selected_date": "",
            "show_event_detail": False,
            "detail_event_id": "",
            "show_category_form": False,
            "feedback": {"message": "", "kind": ""},
        },
        "focus": {
            "mode": "pomodoro",
            "running": False,
            "elapsed_ds": 0,
            "pomodoro_phase": "work",
            "completed_cycles": 0,
            "total_cycles": 4,
            "timer_duration_minutes": 15,
            "timer_duration_seconds": 0,
            "session_started_at": "",
            "sessions": [],
        },
        "dashboard": {
            "quote_index": 0,
            "timer_running": False,
            "timer_seconds": 0,
            "timer_started_at": "",
            "sessions": [],
        },
        "flashcards": {
            "decks": [],
            "selected_deck_id": "",
            "show_deck_form": False,
            "show_card_form": False,
            "editing_card_id": "",
            "review": {
                "mode": "",
                "order": [],
                "index": 0,
                "flipped": False,
                "correct": 0,
                "incorrect": 0,
                "missed": [],
                "last_result": "",
                "finished": False,
            },
            "feedback": {"message": "", "kind": ""},
        },
        "notes": {
            "items": [],
            "folders": [],
            "selected_note_id": "",
            "expanded_subjects": [],
            "search": "",
            "font_family": "serif",
            "font_size": "md",
            "feedback": {"message": "", "kind": ""},
        },
        "notifications": {
            "items": [],
            "show_panel": False,
        },
        "insights": {
            "range_mode": "month",
        },
    }


_NUMERIC = (int, float)  # bool counts too; that's fine, it's a 0/1 int


def _same_shape(defaults: Any, saved: Any) -> bool:
    """True if a saved value is safe to keep instead of its default."""
    if isinstance(defaults, _NUMERIC) and isinstance(saved, _NUMERIC):
        return True
    return type(defaults) is type(saved)


def _merge(defaults: Any, saved: Any) -> Any:
    """Fill gaps in a saved document with defaults so older files keep loading."""
    if isinstance(defaults, dict) and isinstance(saved, dict):
        merged = {
            key: _merge(fallback, saved[key]) if key in saved else fallback
            for key, fallback in defaults.items()
        }
        # Keep any extra keys the saved file has that defaults doesn't (e.g. a
        # field from a newer version of the app being loaded by an older one).
        merged.update({k: v for k, v in saved.items() if k not in merged})
        return merged
    # A corrupted or renamed field falls back to its default rather than
    # breaking a page that expects a particular type.
    return saved if _same_shape(defaults, saved) else defaults


def _device_file(device_id: str) -> Path:
    return DEVICES_DIR / f"{device_id}.json"


def _migrate_legacy_file(device_file: Path) -> None:
    """One-time upgrade path: the first device to load after switching to
    per-device files inherits whatever was in the old shared uniflow.json,
    so nobody's existing data disappears. Every device after that just
    starts fresh, since the whole point is no longer sharing one file."""
    with _migration_lock:
        if DEVICES_DIR.exists() or not DATA_FILE.exists():
            return
        DEVICES_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FILE.replace(device_file)


def load(device_id: str) -> dict[str, Any]:
    defaults = default_data()
    device_file = _device_file(device_id)
    if not device_file.exists():
        _migrate_legacy_file(device_file)
    if not device_file.exists():
        return defaults
    try:
        saved = json.loads(device_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        logging.exception(f"Could not read {device_file}, starting fresh: {e}")
        return defaults
    if not isinstance(saved, dict):
        return defaults
    return _merge(defaults, saved)


def save(data: dict[str, Any], device_id: str) -> None:
    DEVICES_DIR.mkdir(parents=True, exist_ok=True)
    device_file = _device_file(device_id)
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    # Write beside the target then swap, so a crash never truncates the file.
    handle, tmp_path = tempfile.mkstemp(dir=DEVICES_DIR, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp_path, device_file)
    except OSError as e:
        logging.exception(f"Could not save {device_file}: {e}")
        Path(tmp_path).unlink(missing_ok=True)
