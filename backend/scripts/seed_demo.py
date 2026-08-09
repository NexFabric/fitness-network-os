#!/usr/bin/env python3
"""Alias entrypoint for ``scripts/seed_demo_tenant.py``.

Preferred command (from ``backend/``)::

    set -a && source .env && set +a
    uv run python scripts/seed_demo.py

Prints tenant_id + bearer_token for Admin Web login at
http://localhost:5173/login. See ``seed_demo_tenant.py`` for flags.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from scripts.seed_demo_tenant import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
