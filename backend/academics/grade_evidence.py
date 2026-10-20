"""Resolve the authoritative grade evidence shown to classroom readers.

Conflicting stored scores are withheld until a teacher can review them.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from academics.models import Assignment, Grade
    from gradebook.models import GradeEntry


class GradeEvidence(TypedDict):
    """Stable grade-evidence fields consumed by classroom and family views."""

    earned: Decimal | None
    possible: Decimal | None
    source: str | None
    conflict: bool


def resolve_grade(
    assignment: Assignment,
    entry: GradeEntry | None = None,
    academic: Grade | None = None,
) -> GradeEvidence:
    """Choose recorded grade evidence without masking conflicting values.

    A scored gradebook entry takes precedence over an academic grade only
    when its denominator matches the assignment and any academic score
    agrees. Otherwise, withhold earned points for teacher review. An
    unscored gradebook entry does not override the academic grade.
    """
    assignment_points = assignment.points_possible

    if entry is not None and entry.points_earned is not None:
        denominator_conflict = entry.points_possible != assignment_points
        score_conflict = (
            academic is not None
            and entry.points_earned != academic.numeric_score
        )
        if denominator_conflict or score_conflict:
            return {
                "earned": None,
                "possible": assignment_points,
                "source": "conflict_requires_teacher_review",
                "conflict": True,
            }

        return {
            "earned": entry.points_earned,
            "possible": entry.points_possible,
            "source": "gradebook.GradeEntry",
            "conflict": False,
        }

    return {
        "earned": academic.numeric_score if academic else None,
        "possible": assignment_points,
        "source": "academics.Grade" if academic else None,
        "conflict": False,
    }
