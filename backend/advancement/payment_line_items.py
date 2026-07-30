"""
Stage 3.4 – provider-neutral post-payment line-item helpers.

compute_totals_from_line_items: parse a provider-neutral line-items response and
return subtotal / donation / total as Decimal values.

Usage:
    line_items = provider.fetch_checkout_line_items(session_id, limit=20)
    totals = compute_totals_from_line_items(line_items)
    # totals = {"subtotal": Decimal("25.00"), "donation": Decimal("10.00"), "total": Decimal("35.00")}
"""
from __future__ import annotations

from decimal import Decimal


def cents_to_decimal(cents: int) -> Decimal:
    """Convert integer cents to 2-decimal Decimal."""
    return (Decimal(int(cents)) / Decimal(100)).quantize(Decimal("0.01"))


def compute_totals_from_line_items(line_items: dict) -> dict:
    """
    Parse a provider-neutral checkout line-items response.

    Assumption (matches our checkout sessions):
    - First line item  → tickets bundle (subtotal)
    - Additional items → optional donation items

    Returns:
        {
            "subtotal": Decimal,
            "donation": Decimal,
            "total":    Decimal,
        }
    """
    data = []
    if isinstance(line_items, dict):
        data = line_items.get("data", []) or []
    elif hasattr(line_items, "data"):
        # SDK-style response objects may expose a data attribute
        try:
            data = list(line_items.data)
        except Exception:
            data = []

    subtotal_cents = 0
    donation_cents = 0
    total_cents = 0

    for i, li in enumerate(data):
        if isinstance(li, dict):
            amt = int(li.get("amount_total") or li.get("amount_subtotal") or 0)
        else:
            # Provider SDK object
            amt = int(getattr(li, "amount_total", None) or getattr(li, "amount_subtotal", None) or 0)

        total_cents += amt
        if i == 0:
            subtotal_cents += amt
        else:
            donation_cents += amt

    return {
        "subtotal": cents_to_decimal(subtotal_cents),
        "donation": cents_to_decimal(donation_cents),
        "total": cents_to_decimal(total_cents),
    }
