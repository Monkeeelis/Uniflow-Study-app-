"""Small grab-bag of helpers used across the service modules."""

from __future__ import annotations

from typing import Any


# Shorthand for the {message, kind} shape the frontend expects for toasts.
def toast(message: str, kind: str = "info") -> dict[str, str]:
    return {"message": message, "kind": kind}


# Same idea as toast() but stored on the section for inline display rather than popped up.
def set_feedback(section: dict[str, Any], message: str, kind: str = "info") -> None:
    section["feedback"] = {"message": message, "kind": kind}


# Grabs a form field and trims it; missing/None just falls back to default.
def text(payload: dict[str, Any], key: str, default: str = "") -> str:
    value = payload.get(key, default)
    if value is None:
        return default
    return str(value).strip()


def flag(payload: dict[str, Any], key: str, default: bool = False) -> bool:
    """Coerce a checkbox value - HTML forms post these as strings like "on" or "true", not real booleans."""
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "on", "1", "yes")
    return bool(value)


def positive_int(value: Any, fallback: int) -> int:
    """Coax user input into an int >= 1; anything unparsable just returns fallback."""
    try:
        return max(1, int(float(value)))
    except (TypeError, ValueError):
        return fallback


def clamp_int(value: Any, low: int, high: int, fallback: int = 0) -> int:
    """Like positive_int, but clamps into an arbitrary [low, high] range instead of just >=1."""
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        number = fallback
    return max(low, min(high, number))
