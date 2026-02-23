"""
Stage 2 – Financial Invariant Lock
====================================
Installment Proration Unit Tests – _split_amount_evenly()

Invariants proved:
  1. Sum invariant     – parts always sum to total exactly (no penny lost or gained)
  2. Remainder rule    – last part absorbs rounding remainder
  3. Single part       – [total] returned unchanged
  4. No negative parts – all returned values >= Decimal("0.00")
  5. Zero parts        – ValueError raised
  6. Penny edge case   – $0.01 split N ways always sums to $0.01
"""

from decimal import Decimal

import pytest

from billing.services import _split_amount_evenly


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sum(parts):
    return sum(parts, Decimal("0.00"))


# ---------------------------------------------------------------------------
# 1: Sum invariant
# ---------------------------------------------------------------------------

class TestSumInvariant:
    """split always sums to the original total regardless of divisor."""

    def test_three_way_split_100(self):
        parts = _split_amount_evenly(Decimal("100.00"), 3)
        assert _sum(parts) == Decimal("100.00"), f"Sum must be 100.00; got {_sum(parts)}"

    def test_four_way_split_100(self):
        parts = _split_amount_evenly(Decimal("100.00"), 4)
        assert _sum(parts) == Decimal("100.00")

    def test_seven_way_split_1000(self):
        parts = _split_amount_evenly(Decimal("1000.00"), 7)
        assert _sum(parts) == Decimal("1000.00"), f"7-way split of $1000 must sum to $1000; got {_sum(parts)}"

    def test_twelve_way_split(self):
        """12 monthly installments of $1,234.56 must sum exactly."""
        parts = _split_amount_evenly(Decimal("1234.56"), 12)
        assert _sum(parts) == Decimal("1234.56")

    def test_prime_split_irregular_amount(self):
        """11-way split of $999.99 must sum exactly (stress test)."""
        parts = _split_amount_evenly(Decimal("999.99"), 11)
        assert _sum(parts) == Decimal("999.99"), f"Got {_sum(parts)}"


# ---------------------------------------------------------------------------
# 2: Remainder rule – last part absorbs rounding
# ---------------------------------------------------------------------------

class TestRemainderRule:
    """Base parts (all but last) are ROUND_DOWN; last part gets the remainder."""

    def test_three_way_100_remainder_in_last(self):
        parts = _split_amount_evenly(Decimal("100.00"), 3)
        # 100/3 = 33.33… → base=33.33, last=100.00 - 33.33*2 = 33.34
        assert len(parts) == 3
        assert parts[0] == Decimal("33.33")
        assert parts[1] == Decimal("33.33")
        assert parts[2] == Decimal("33.34")

    def test_three_way_1_penny_remainder_in_last(self):
        parts = _split_amount_evenly(Decimal("1.00"), 3)
        # 1/3 = 0.33… → base=0.33, last=1.00 - 0.33*2 = 0.34
        assert parts[0] == Decimal("0.33")
        assert parts[1] == Decimal("0.33")
        assert parts[2] == Decimal("0.34")
        assert _sum(parts) == Decimal("1.00")

    def test_even_division_all_parts_equal(self):
        # $10.00 / 4 = $2.50 exactly – no remainder
        parts = _split_amount_evenly(Decimal("10.00"), 4)
        assert all(p == Decimal("2.50") for p in parts)


# ---------------------------------------------------------------------------
# 3: Single part
# ---------------------------------------------------------------------------

class TestSinglePart:
    def test_single_part_returns_total(self):
        parts = _split_amount_evenly(Decimal("500.00"), 1)
        assert parts == [Decimal("500.00")]

    def test_single_part_length_is_one(self):
        parts = _split_amount_evenly(Decimal("1.23"), 1)
        assert len(parts) == 1
        assert parts[0] == Decimal("1.23")


# ---------------------------------------------------------------------------
# 4: No negative parts
# ---------------------------------------------------------------------------

class TestNoNegativeParts:
    def test_penny_split_three_ways_no_negative(self):
        # $0.01 / 3 → [0.00, 0.00, 0.01] – all non-negative
        parts = _split_amount_evenly(Decimal("0.01"), 3)
        assert all(p >= Decimal("0.00") for p in parts), f"All parts must be >= 0; got {parts}"
        assert _sum(parts) == Decimal("0.01")

    def test_zero_total_split_all_zeros(self):
        parts = _split_amount_evenly(Decimal("0.00"), 3)
        assert all(p == Decimal("0.00") for p in parts)
        assert _sum(parts) == Decimal("0.00")


# ---------------------------------------------------------------------------
# 5: Zero parts raises ValueError
# ---------------------------------------------------------------------------

class TestInvalidParts:
    def test_zero_parts_raises_value_error(self):
        with pytest.raises(ValueError, match="parts must be > 0"):
            _split_amount_evenly(Decimal("100.00"), 0)

    def test_negative_parts_raises_value_error(self):
        with pytest.raises(ValueError, match="parts must be > 0"):
            _split_amount_evenly(Decimal("100.00"), -1)


# ---------------------------------------------------------------------------
# 6: Penny edge case – sum always exact
# ---------------------------------------------------------------------------

class TestPennyEdgeCase:
    def test_one_penny_split_two_ways(self):
        # 0.01 / 2 = 0.005 → base=0.00, last=0.01 → [0.00, 0.01]
        parts = _split_amount_evenly(Decimal("0.01"), 2)
        assert _sum(parts) == Decimal("0.01")
        assert len(parts) == 2

    def test_one_penny_split_ten_ways(self):
        # Nine zeros + 0.01
        parts = _split_amount_evenly(Decimal("0.01"), 10)
        assert _sum(parts) == Decimal("0.01")
        assert len(parts) == 10
