#!/usr/bin/env python3
"""Fail CI when release authority documents regress to disproven claims."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

AUTHORITY = (
    "docs/HANDOFF.md",
    "docs/PROGRESS_CHECKLIST.md",
    "backend/docs/plans/REMAINING_WORK_BOARD.md",
    "AGENTS.md",
)

# String match only — no GitHub API, no live HEAD SHA (those go stale).
# #89 is closed; a file may not claim both an OPEN story and a merged-main story,
# and may not pin last code at the pre-#89 SHA once it also says #89 MERGED.
PR89_OPEN = (
    "PR #89 OPEN",
    "PR **#89 OPEN",
)
PR89_MERGED_STORY = (
    "PR #89 MERGED",
    "PR **#89 MERGED",
    "#89→`e05e29f`",
    "`#89`→`e05e29f`",
)
STALE_PRE89_SHA = "ee6597e"

AUTHORITY_FORBIDDEN = (
    "PR #62 OPEN",
    "| **Production-ready?** | **YES** |",
    "**Production-ready?** **YES**",
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> list[str]:
    text = _read(path)
    return [f"{path}: missing {needle!r}" for needle in needles if needle not in text]


def forbid(path: str, *needles: str) -> list[str]:
    text = _read(path)
    return [
        f"{path}: forbidden stale claim {needle!r}"
        for needle in needles
        if needle in text
    ]


def exclusive_pair_errors(path: str, text: str, left: str, right: str) -> list[str]:
    if left in text and right in text:
        return [f"{path}: mutually exclusive claims {left!r} and {right!r}"]
    return []


def forbid_both(path: str, left: str, right: str) -> list[str]:
    return exclusive_pair_errors(path, _read(path), left, right)


def authority_exclusive_errors(path: str, text: str) -> list[str]:
    errors: list[str] = []
    for open_needle in PR89_OPEN:
        for merged_needle in PR89_MERGED_STORY:
            errors.extend(exclusive_pair_errors(path, text, open_needle, merged_needle))
    for merged_needle in PR89_MERGED_STORY:
        errors.extend(exclusive_pair_errors(path, text, STALE_PRE89_SHA, merged_needle))
    errors.extend(exclusive_pair_errors(path, text, "PR #62 OPEN", "MERGED to `main`"))
    return errors


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
        *require("docs/HANDOFF.md", "Production-ready?", "**NO**", "NOT VERIFIED"),
        *require(
            "docs/PROGRESS_CHECKLIST.md",
            "PRODUCTION **NO-GO**",
        ),
        *require(
            "backend/docs/plans/REMAINING_WORK_BOARD.md",
            "**Production-ready?** **NO**",
            "Phase 26 PASS?",
        ),
        *forbid(
            "AGENTS.md",
            "PR **#62 OPEN**",
            "feat/public-site-modernization-and-seo",
        ),
    ]

    for path in AUTHORITY:
        errors.extend(forbid(path, *AUTHORITY_FORBIDDEN))
        errors.extend(authority_exclusive_errors(path, _read(path)))

    if errors:
        for error in errors:
            print(error)
        return 1
    print("Release truth documents are internally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
