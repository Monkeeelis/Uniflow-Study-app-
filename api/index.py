"""Vercel serverless entrypoint.

Vercel imports this module and serves the WSGI callable named ``app``. The
Flask app itself lives one level down in ``UniFlow/uniflow``, so the package
directory goes on sys.path before the import.

Persistence comes from the key-value store when KV_REST_API_URL and
KV_REST_API_TOKEN are set, which is what keeps each visitor's data separate and
alive between requests. The /tmp default below is only a last resort for when
those are missing: Vercel's filesystem is read-only everywhere else, so without
it the app would fail outright rather than merely forget everything.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "UniFlow"))

os.environ.setdefault("UNIFLOW_DATA_DIR", "/tmp/uniflow-data")

from uniflow.app import app  # noqa: E402  (path setup has to run first)
