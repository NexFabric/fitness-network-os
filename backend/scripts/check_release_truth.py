#!/usr/bin/env python3
"""Fail CI when release authority documents regress to disproven claims."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require(path: str, *needles: str) -> list[str]:
    text = (ROOT / path).read_text(encoding="utf-8")
    return [f"{path}: missing {needle!r}" for needle in needles if needle not in text]


def forbid(path: str, *needles: str) -> list[str]:
    text = (ROOT / path).read_text(encoding="utf-8")
    return [
        f"{path}: forbidden stale claim {needle!r}"
        for needle in needles
        if needle in text
    ]


def main() -> int:
    errors = [
        *require(
            "backend/docs/plans/phase26_core_mvp_exit_gate.md",
            "SUPERSEDED — NOT PASSED",
            "| **Production-ready?** | **NO** |",
        ),
        *forbid(
            "backend/docs/plans/phase26_core_mvp_exit_gate.md",
            "PASS — production-ready",
            "| **Production-ready?** | **YES** |",
            "Automatic PASS for Exit Gate",
        ),
        *require(
            "docs/ops/ASVS_L2_COMPLIANCE_REPORT.md",
            "ASVS 5.0 Level 2",
            "NOT INDEPENDENTLY VERIFIED",
        ),
        *forbid(
            "docs/ops/ASVS_L2_COMPLIANCE_REPORT.md",
            "ASVS 4.0.3",
        ),
    ]
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Release truth documents are internally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
