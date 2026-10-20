"""Regression contracts for shared classroom and family grade evidence."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from academics.grade_evidence import resolve_grade


def _assignment(points: str = "10") -> SimpleNamespace:
    """Construct an assignment-shaped value without database access."""
    return SimpleNamespace(points_possible=Decimal(points))


def _entry(earned: str | None, possible: str | None) -> SimpleNamespace:
    """Construct gradebook evidence with optional recorded points."""
    return SimpleNamespace(
        points_earned=Decimal(earned) if earned is not None else None,
        points_possible=Decimal(possible) if possible is not None else None,
    )


def _academic(earned: str) -> SimpleNamespace:
    """Construct an academic grade with a decimal score."""
    return SimpleNamespace(numeric_score=Decimal(earned))


@pytest.mark.parametrize(
    ("entry", "academic", "earned", "source"),
    [
        (None, None, None, None),
        (_entry(None, "10"), None, None, None),
        (None, _academic("7"), Decimal("7"), "academics.Grade"),
        (_entry(None, "10"), _academic("8"), Decimal("8"), "academics.Grade"),
        (_entry("0", "10"), None, Decimal("0"), "gradebook.GradeEntry"),
        (_entry("7", "10"), None, Decimal("7"), "gradebook.GradeEntry"),
        (
            _entry("7", "10"),
            _academic("7"),
            Decimal("7"),
            "gradebook.GradeEntry",
        ),
    ],
)
def test_resolve_grade_selects_existing_evidence(
    entry: SimpleNamespace | None,
    academic: SimpleNamespace | None,
    earned: Decimal | None,
    source: str | None,
) -> None:
    """Keep the original precedence, zero-score, and empty-evidence rules."""
    assert resolve_grade(_assignment(), entry, academic) == {
        "earned": earned,
        "possible": Decimal("10"),
        "source": source,
        "conflict": False,
    }


@pytest.mark.parametrize(
    ("entry", "academic"),
    [
        (_entry("7", "5"), None),
        (_entry("7", None), None),
        (_entry("7", "10"), _academic("8")),
        (_entry("7", "5"), _academic("8")),
    ],
)
def test_resolve_grade_withholds_conflicting_evidence(
    entry: SimpleNamespace,
    academic: SimpleNamespace | None,
) -> None:
    """Do not publish scored evidence with mismatched grading records."""
    assert resolve_grade(_assignment(), entry, academic) == {
        "earned": None,
        "possible": Decimal("10"),
        "source": "conflict_requires_teacher_review",
        "conflict": True,
    }


def test_resolve_grade_preserves_assignment_denominator() -> None:
    """Return the actual assignment denominator for unscored work."""
    evidence = resolve_grade(_assignment("12.50"), _entry(None, None))
    assert evidence["earned"] is None
    assert evidence["possible"] == Decimal("12.50")
    assert evidence["conflict"] is False
