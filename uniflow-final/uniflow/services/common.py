"""Helpers shared by the service modules."""

from __future__ import annotations

from typing import Any


def toast(message: str, kind: str = "info") -> dict[str, str]:
    return {"message": message, "kind": kind}


def set_feedback(section: dict[str, Any], message: str, kind: str = "info") -> None:
    section["feedback"] = {"message": message, "kind": kind}


def text(payload: dict[str, Any], key: str, default: str = "") -> str:
    value = payload.get(key, default)
    if value is None:
        return default
    return str(value).strip()


def flag(payload: dict[str, Any], key: str, default: bool = False) -> bool:
    """Read a checkbox-style value, accepting the string forms an HTML form posts."""
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "on", "1", "yes")
    return bool(value)


def positive_int(value: Any, fallback: int) -> int:
    """Parse a >=1 integer from user input, falling back on anything invalid."""
    try:
        return max(1, int(float(value)))
    except (TypeError, ValueError):
        return fallback


def clamp_int(value: Any, low: int, high: int, fallback: int = 0) -> int:
    """Parse an integer from user input and clamp it into [low, high]."""
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        number = fallback
    return max(low, min(high, number))
