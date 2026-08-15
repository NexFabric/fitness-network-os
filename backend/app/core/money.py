"""Money helpers — integer minor units only. Never use binary float for money."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# ISO 4217 currencies with non-2 decimal exponents are rare for this product;
# default minor factor is 100 (cents/kuruş).
DEFAULT_MINOR_FACTOR = 100


def major_to_minor(
    major: Decimal | str | int,
    *,
    minor_factor: int = DEFAULT_MINOR_FACTOR,
) -> int:
    """Convert major currency units to integer minor units via Decimal."""
    if isinstance(major, bool):
        raise TypeError("major amount cannot be bool")
    if isinstance(major, float):
        raise TypeError(
            "float is not allowed for money conversion; use Decimal, str, or int"
        )
    if minor_factor <= 0:
        raise ValueError("minor_factor must be > 0")

    try:
        d = Decimal(major) if not isinstance(major, Decimal) else major
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"invalid money amount: {major!r}") from e

    quantized = (d * Decimal(minor_factor)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return int(quantized)


def minor_to_major(
    minor: int,
    *,
    minor_factor: int = DEFAULT_MINOR_FACTOR,
) -> Decimal:
    """Convert integer minor units to Decimal major units."""
    if isinstance(minor, bool) or not isinstance(minor, int):
        raise TypeError("minor must be int")
    if minor_factor <= 0:
        raise ValueError("minor_factor must be > 0")
    return Decimal(minor) / Decimal(minor_factor)


def assert_amount_minor(value: object) -> int:
    """Validate a money amount is a non-bool int (allows 0 and negative where needed)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("amount_minor must be int (float not allowed)")
    return value


def assert_quantity(value: object) -> int:
    """Strict positive quantity (entitlements, line items)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("quantity must be int (float not allowed)")
    if value <= 0:
        raise ValueError("quantity must be > 0")
    return value


def legacy_major_string_to_minor(
    major_str: str | None,
    *,
    minor_factor: int = DEFAULT_MINOR_FACTOR,
) -> int | None:
    """
    Convert a decimal *string* representation of a legacy major amount to minor.

    Used for Phase 11 backfill tests (never pass binary float).
    ROUND_HALF_UP matches PostgreSQL ROUND(value * 100) for half cases on numeric.
    """
    if major_str is None:
        return None
    return major_to_minor(major_str, minor_factor=minor_factor)


def legacy_probability_to_bps(prob_str: str | None) -> int | None:
    """Convert probability decimal string in [0,1] to basis points 0..10000."""
    if prob_str is None:
        return None
    d = Decimal(prob_str)
    bps = int((d * Decimal(10000)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return max(0, min(10000, bps))
