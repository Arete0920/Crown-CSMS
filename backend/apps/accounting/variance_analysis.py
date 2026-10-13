"""Deterministic descriptions of posted-ledger budget variances.

This module performs arithmetic only. It does not forecast cash, alter accounting
records, or decide whether a budget variance warrants an operational action.
"""

from decimal import Decimal, ROUND_HALF_UP


PERCENT_PRECISION = Decimal("0.01")


def explain_variance(*, account_type: str, budget: Decimal, actual: Decimal) -> dict:
    """Describe actual-versus-budget movement with explicit sign conventions.

    ``deviation_amount`` is actual minus budget (positive means above plan).
    ``deviation_percent`` uses absolute budget as its denominator and is null
    for zero-budget rows. Favorability applies only to revenue and expense
    accounts; it is not a risk score or an autonomous recommendation.
    """
    deviation = actual - budget
    percent = (
        (deviation * Decimal("100") / abs(budget)).quantize(
            PERCENT_PRECISION, rounding=ROUND_HALF_UP
        )
        if budget != 0
        else None
    )
    if account_type not in {"REVENUE", "EXPENSE"}:
        favorability = "NOT_ASSESSED"
    elif deviation == 0:
        favorability = "ON_TARGET"
    elif account_type == "REVENUE":
        favorability = "FAVORABLE" if deviation > 0 else "UNFAVORABLE"
    else:
        favorability = "UNFAVORABLE" if deviation > 0 else "FAVORABLE"

    return {
        "deviation_amount": deviation,
        "deviation_percent": percent,
        "favorability": favorability,
    }
