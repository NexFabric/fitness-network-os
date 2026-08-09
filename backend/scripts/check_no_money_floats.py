#!/usr/bin/env python3
"""Architecture fitness: No ORM Float columns in app models.

Phase 11 gate: ban SQLAlchemy Float mapped columns entirely (money uses
amount_minor int; rates use integer basis points). This does NOT prove
schemas/services/API coercion are float-free — pair with MoneyMinor/StrictInt
and assert_amount_minor at service boundaries.

Exit code 1 if any Float ORM column is found.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
MODELS_DIR = BACKEND / "app" / "models"

# Column / attribute names treated as money (or former money) when typed float.
MONEY_NAME_RE = re.compile(
    r"(^|_)(amount|price|fee|cost|balance|total|tax|discount|credit|refund|"
    r"payment|money|value|charge|fare|premium|salary|wage|revenue|payout|"
    r"subtotal|grand_total|unit_price|line_total)(_|$)",
    re.IGNORECASE,
)

# Explicit allowlist: non-money floats if any remain (should be empty after Phase 11).
ALLOWED_FLOAT_COLUMNS: set[tuple[str, str]] = set()


def _is_money_name(name: str) -> bool:
    return bool(MONEY_NAME_RE.search(name))


def scan_models() -> list[str]:
    """Load ORM models and find Float columns."""
    sys.path.insert(0, str(BACKEND))
    # Import all models into Base.metadata
    from sqlalchemy import Float

    import app.models  # noqa: F401
    from app.db.base import Base

    errors: list[str] = []
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        table = getattr(cls, "__tablename__", cls.__name__)
        for col in mapper.columns:
            if isinstance(col.type, Float):
                key = (str(table), col.name)
                if key in ALLOWED_FLOAT_COLUMNS:
                    continue
                if _is_money_name(col.name) or True:
                    # Phase 11: ban ALL Float ORM columns in app models.
                    # Analytics should use integer bps / scores.
                    errors.append(
                        f"Float column forbidden: {cls.__module__}.{cls.__name__}."
                        f"{col.name} (table={table})"
                    )
    return errors


def scan_source_ast() -> list[str]:
    """Static scan of model sources for Float / Mapped[float] money fields."""
    errors: list[str] = []
    for path in sorted(MODELS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.AnnAssign) or not isinstance(
                node.target, ast.Name
            ):
                continue
            name = node.target.id
            ann = node.annotation
            ann_src = ast.unparse(ann) if ann is not None else ""
            if "float" in ann_src.lower() and _is_money_name(name):
                errors.append(
                    f"{path.relative_to(BACKEND)}: money field '{name}' annotated "
                    f"as float-like: {ann_src}"
                )
            # mapped_column(Float, ...)
            if node.value and isinstance(node.value, ast.Call):
                for arg in list(node.value.args) + [
                    kw.value for kw in node.value.keywords
                ]:
                    if isinstance(arg, ast.Name) and arg.id == "Float":
                        if _is_money_name(name) or True:
                            errors.append(
                                f"{path.relative_to(BACKEND)}: mapped_column(Float) "
                                f"on '{name}' — use Integer amount_minor / bps"
                            )
    return errors


def main() -> int:
    errors = scan_source_ast()
    try:
        errors.extend(scan_models())
    except Exception as e:  # pragma: no cover
        errors.append(f"Failed to import models for float scan: {e}")

    # de-dupe preserve order
    seen: set[str] = set()
    unique: list[str] = []
    for e in errors:
        if e not in seen:
            seen.add(e)
            unique.append(e)

    if unique:
        print("Money float fitness check FAILED:")
        for e in unique:
            print(f"  - {e}")
        print(
            "\nRule: No payment/money using float. Use amount_minor (int) + currency "
            "or integer basis points for rates."
        )
        return 1

    print("ORM Float fitness check passed: no Float columns in app models.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
