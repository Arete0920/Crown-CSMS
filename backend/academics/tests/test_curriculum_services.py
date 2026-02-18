"""
Tests for academics vertical slice: grade calculation, mastery tracking.
"""
from decimal import Decimal
import pytest

from academics.services import (
    percentage_to_letter,
    compute_percentage,
    mastery_from_percentage,
)


@pytest.mark.parametrize("pct,expected", [
    (Decimal("95.00"), "A"),
    (Decimal("90.00"), "A"),
    (Decimal("89.99"), "B"),
    (Decimal("85.00"), "B"),
    (Decimal("80.00"), "B"),
    (Decimal("79.99"), "C"),
    (Decimal("75.00"), "C"),
    (Decimal("70.00"), "C"),
    (Decimal("69.99"), "D"),
    (Decimal("65.00"), "D"),
    (Decimal("60.00"), "D"),
    (Decimal("59.99"), "F"),
    (Decimal("25.00"), "F"),
    (Decimal("0.00"), "F"),
])
def test_percentage_to_letter(pct, expected):
    """Test 10-point grading scale."""
    assert percentage_to_letter(pct) == expected


@pytest.mark.parametrize("score,possible,expected", [
    (Decimal("85"), Decimal("100"), Decimal("85.00")),
    (Decimal("50"), Decimal("50"), Decimal("100.00")),
    (Decimal("0"), Decimal("100"), Decimal("0.00")),
    (Decimal("100"), Decimal("100"), Decimal("100.00")),
    (Decimal("45.5"), Decimal("50"), Decimal("91.00")),
])
def test_compute_percentage(score, possible, expected):
    """Test percentage calculation."""
    result = compute_percentage(score, possible).quantize(Decimal("0.01"))
    assert result == expected


def test_compute_percentage_zero_possible():
    """Test percentage when points_possible is 0."""
    assert compute_percentage(Decimal("10"), Decimal("0")) == Decimal("0.00")


@pytest.mark.parametrize("pct,expected_level", [
    (Decimal("95"), 4),
    (Decimal("90"), 4),
    (Decimal("89"), 3),
    (Decimal("85"), 3),
    (Decimal("80"), 3),
    (Decimal("79"), 2),
    (Decimal("75"), 2),
    (Decimal("70"), 2),
    (Decimal("69"), 1),
    (Decimal("65"), 1),
    (Decimal("25"), 1),
])
def test_mastery_from_percentage(pct, expected_level):
    """Test mastery level mapping (1-4)."""
    assert mastery_from_percentage(pct) == expected_level
