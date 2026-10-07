"""Money helpers. Amounts are Decimal so that comparisons are exact."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def to_decimal(value: float | int | str) -> Decimal:
    """Convert a JSON number or a text amount to Decimal without floating-point noise."""
    try:
        return Decimal(str(value).strip())
    except InvalidOperation as error:
        raise ValueError(f"Not a number: {value!r}") from error


def calculate_payout(stake: Decimal, odds: Decimal) -> Decimal:
    """Potential payout of a single bet: stake × odds."""
    return stake * odds
