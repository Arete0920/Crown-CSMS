"""Regression tests for defensive grading arithmetic and API input validation."""

from decimal import Decimal

import pytest

from academics.serializers import GradeCreateSerializer
from academics.services import compute_percentage


@pytest.mark.parametrize("score,possible", [
    (Decimal("-1"), Decimal("100")),
    (Decimal("NaN"), Decimal("100")),
    (Decimal("Infinity"), Decimal("100")),
    (Decimal("50"), Decimal("0")),
    (Decimal("50"), Decimal("-10")),
    (Decimal("50"), Decimal("NaN")),
    (Decimal("1000"), Decimal("1")),
])
def test_compute_percentage_rejects_unsafe_values(score, possible):
    with pytest.raises(ValueError):
        compute_percentage(score, possible)


@pytest.mark.parametrize("score,possible,expected", [
    (Decimal("90"), Decimal("100"), Decimal("90.00")),
    (Decimal("110"), Decimal("100"), Decimal("110.00")),
    (Decimal("0"), Decimal("100"), Decimal("0")),
])
def test_compute_percentage_keeps_valid_and_extra_credit(score, possible, expected):
    assert compute_percentage(score, possible) == expected


def test_grade_create_serializer_rejects_negative_scores():
    data = GradeCreateSerializer(data={
        "submission_id": "41ed035b-c67e-4d58-b2de-d2943e21d511",
        "numeric_score": "-0.01",
    })
    assert not data.is_valid()
    assert "numeric_score" in data.errors


def test_grade_create_serializer_allows_positive_extra_credit():
    data = GradeCreateSerializer(data={
        "submission_id": "41ed035b-c67e-4d58-b2de-d2943e21d511",
        "numeric_score": "105.00",
    })
    assert data.is_valid(), data.errors
