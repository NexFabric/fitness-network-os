"""Phase 11 — money must not use binary float."""

from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from app.core.money import (
    assert_amount_minor,
    legacy_major_string_to_minor,
    legacy_probability_to_bps,
    major_to_minor,
    minor_to_major,
)
from app.models.growth import Opportunity, RetentionCockpit
from app.schemas.finance import MoneyMinorPos


def test_major_to_minor_decimal():
    assert major_to_minor(Decimal("150.00")) == 15000
    assert major_to_minor(Decimal("1000.50")) == 100050
    assert major_to_minor("19.99") == 1999
    assert major_to_minor(10) == 1000


def test_major_to_minor_rejects_float():
    with pytest.raises(TypeError, match="float is not allowed"):
        major_to_minor(10.5)  # type: ignore[arg-type]


def test_minor_to_major_roundtrip():
    assert minor_to_major(15000) == Decimal(150)
    assert minor_to_major(50025) == Decimal("500.25")


def test_assert_amount_minor():
    assert assert_amount_minor(0) == 0
    assert assert_amount_minor(100) == 100
    with pytest.raises(TypeError):
        assert_amount_minor(1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        assert_amount_minor(True)  # type: ignore[arg-type]


def test_opportunity_uses_integer_money_fields():
    cols = {c.name: c.type.__class__.__name__ for c in Opportunity.__table__.columns}
    assert "value" not in cols
    assert cols["value_amount_minor"] in ("INTEGER", "Integer")
    assert cols["currency"] in ("VARCHAR", "String")


def test_retention_uses_integer_bps_not_float():
    cols = {
        c.name: c.type.__class__.__name__ for c in RetentionCockpit.__table__.columns
    }
    assert "churn_probability" not in cols
    assert cols["churn_probability_bps"] in ("INTEGER", "Integer")


def test_fitness_script_passes():
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "scripts" / "check_no_money_floats.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "major_str,expected",
    [
        ("19.99", 1999),
        ("19.995", 2000),  # ROUND_HALF_UP
        ("0", 0),
        ("999999.99", 99999999),
        ("1000.50", 100050),
    ],
)
def test_legacy_major_string_conversion(major_str, expected):
    assert legacy_major_string_to_minor(major_str) == expected


def test_legacy_major_null():
    assert legacy_major_string_to_minor(None) is None


@pytest.mark.parametrize(
    "prob_str,expected",
    [
        ("0", 0),
        ("0.125", 1250),
        ("1", 10000),
        ("1.5", 10000),  # clamp
        ("-0.1", 0),  # clamp
    ],
)
def test_legacy_probability_bps(prob_str, expected):
    assert legacy_probability_to_bps(prob_str) == expected


def test_strict_money_minor_rejects_float_coercion():
    ta = TypeAdapter(MoneyMinorPos)
    assert ta.validate_python(100) == 100
    with pytest.raises(ValidationError):
        ta.validate_python(100.0)
    with pytest.raises(ValidationError):
        ta.validate_python(100.5)
    with pytest.raises(ValidationError):
        ta.validate_python(True)
    with pytest.raises(ValidationError):
        ta.validate_python("100")
