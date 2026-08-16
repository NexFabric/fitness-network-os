#!/usr/bin/env python3
"""Fail when critical modules fall below their coverage floors.

Global --cov-fail-under remains 70. This script is the per-module floor
so a high average cannot hide a 0% worker or a 22% finance API.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Anti-regression floors from the 2026-08-16 full-suite measurement,
# plus the modules this campaign lifted (report worker, finance HTTP).
# Raising booking/import/DSAR to 70 is the next test-depth wave — do not
# pretend a 29% file is already at 70.
FLOORS: dict[str, float] = {
    "app/core/security.py": 70.0,
    "app/core/session_policy.py": 80.0,
    "app/services/finance.py": 75.0,
    "app/api/v1/endpoints/finance.py": 40.0,
    "app/services/access.py": 80.0,
    "app/services/booking.py": 35.0,
    "app/services/data_import.py": 30.0,
    "app/services/dsar.py": 48.0,
    "app/workers/report.py": 70.0,
    "app/workers/notification.py": 60.0,
    "app/workers/outbox.py": 60.0,
    "app/workers/retention.py": 60.0,
}


def _percent(file_data: dict) -> float:
    summary = file_data.get("summary") or {}
    if "percent_covered" in summary:
        return float(summary["percent_covered"])
    covered = float(summary.get("covered_lines", 0))
    num = float(summary.get("num_statements", 0))
    if num <= 0:
        return 100.0
    return (covered / num) * 100.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--coverage",
        default="coverage.json",
        help="coverage.py JSON report",
    )
    args = parser.parse_args()
    path = Path(args.coverage)
    if not path.is_file():
        print(f"critical coverage: missing report {path}", file=sys.stderr)
        return 1
    report = json.loads(path.read_text(encoding="utf-8"))
    files = report.get("files") or {}
    errors: list[str] = []
    for rel, floor in sorted(FLOORS.items()):
        data = files.get(rel)
        if data is None:
            # coverage.py sometimes prefixes with cwd
            matches = [k for k in files if k.endswith(rel)]
            data = files.get(matches[0]) if matches else None
        if data is None:
            errors.append(f"{rel}: missing from coverage report (floor {floor})")
            continue
        pct = _percent(data)
        if pct + 1e-9 < floor:
            errors.append(f"{rel}: {pct:.2f}% < floor {floor:.0f}%")
        else:
            print(f"OK {rel}: {pct:.2f}% (floor {floor:.0f}%)")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Critical-module coverage floors passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
