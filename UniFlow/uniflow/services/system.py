"""App-wide actions that don't belong to any one page."""

from __future__ import annotations

from typing import Any

from uniflow import store
from uniflow.services.common import toast


def reset(data: dict[str, Any]) -> dict[str, str]:
    """Nukes everything and restores the fresh-install defaults."""
    fresh = store.default_data()
    data.clear()
    data.update(fresh)
    return toast("All data has been reset.", "info")
