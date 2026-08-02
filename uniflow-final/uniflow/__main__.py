"""Run the development server: ``python -m uniflow``."""

from __future__ import annotations

import os

from uniflow.app import app

if __name__ == "__main__":
    app.run(
        host=os.environ.get("UNIFLOW_HOST", "127.0.0.1"),
        port=int(os.environ.get("UNIFLOW_PORT", "5000")),
        debug=os.environ.get("UNIFLOW_DEBUG", "1") == "1",
    )
