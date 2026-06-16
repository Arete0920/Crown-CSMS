from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Sequence
from uuid import UUID


@dataclass(frozen=True)
class AssessmentBlueprint:
    """Canonical assessment design contract for Module 019 proof."""

    school_id: UUID
    assessment_id: str
    title: str
    term: str
    max_points: Decimal
    weight_percent: Decimal
    mastery_cutoff_percent: Decimal = Decimal("80.00")
    active: bool = True


@dataclass(frozen=True)
class AssessmentSubmission:
    """Student score submitted against an assessment blueprint."""

    school_id: UUID
    assessment_id: str
    student_id: str
    points_earned: Decimal | None
    submitted: bool = True
    excused: bool = False


PASSING_CUTOFF_PERCENT = Decimal("60.00")


def _decimal(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validate_assessment_blueprint(blueprint: AssessmentBlueprint) -> None:
    """Validate assessment design before scoring or reporting."""

    if not blueprint.assessment_id:
        raise ValueError("assessment_id is required")
    if not blueprint.title.strip():
        raise ValueError("title is required")
    if not blueprint.term.strip():
        raise ValueError("term is required")
    if _decimal(blueprint.max_points) <= Decimal("0.00"):
        raise ValueError("max_points must be greater than zero")
    if not Decimal("0.00") <= _decimal(blueprint.weight_percent) <= Decimal("100.00"):
        raise ValueError("weight_percent must be between 0 and 100")
    if not Decimal("0.00") <= _decimal(blueprint.mastery_cutoff_percent) <= Decimal("100.00"):
        raise ValueError("mastery_cutoff_percent must be between 0 and 100")


def assessment_design_violations(
    school_id: UUID,
    blueprints: Iterable[AssessmentBlueprint],
    *,
    term: str | None = None,
) -> list[dict]:
    """Return tenant-scoped assessment design issues without mutating records."""

    seen: set[str] = set()
    violations: list[dict] = []

    scoped = [item for item in blueprints if item.school_id == school_id]
    if term:
        scoped = [item for item in scoped if item.term == term]

    for blueprint in sorted(scoped, key=lambda item: (item.term, item.assessment_id)):
        try:
            validate_assessment_blueprint(blueprint)
        except ValueError as exc:
            violations.append(
                {
                    "assessment_id": blueprint.assessment_id,
                    "term": blueprint.term,
                    "violation_type": "INVALID_ASSESSMENT_DESIGN",
                    "message": str(exc),
                }
            )

        if blueprint.assessment_id in seen:
            violations.append(
                {
                    "assessment_id": blueprint.assessment_id,
                    "term": blueprint.term,
                    "violation_type": "DUPLICATE_ASSESSMENT_ID",
                    "message": "assessment_id must be unique within the scoped school assessment set",
                }
            )
        seen.add(blueprint.assessment_id)

    return violations


def score_submission(
    blueprint: AssessmentBlueprint,
    submission: AssessmentSubmission,
) -> dict:
    """Return a deterministic score verdict for one assessment submission."""

    validate_assessment_blueprint(blueprint)

    if blueprint.school_id != submission.school_id:
        raise ValueError("cross-school assessment scoring is not permitted")
    if blueprint.assessment_id != submission.assessment_id:
        raise ValueError("submission assessment_id does not match blueprint")
    if submission.excused:
        return {
            "student_id": submission.student_id,
            "assessment_id": blueprint.assessment_id,
            "status": "EXCUSED",
            "points_earned": None,
            "max_points": _decimal(blueprint.max_points),
            "percent": None,
            "mastery_met": False,
        }
    if not submission.submitted or submission.points_earned is None:
        return {
            "student_id": submission.student_id,
            "assessment_id": blueprint.assessment_id,
            "status": "MISSING",
            "points_earned": None,
            "max_points": _decimal(blueprint.max_points),
            "percent": None,
            "mastery_met": False,
        }

    points = _decimal(submission.points_earned)
    max_points = _decimal(blueprint.max_points)

    if points < Decimal("0.00"):
        raise ValueError("points_earned must be non-negative")
    if points > max_points:
        raise ValueError("points_earned cannot exceed max_points")

    percent = ((points / max_points) * Decimal("100.00")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    mastery_cutoff = _decimal(blueprint.mastery_cutoff_percent)

    if percent >= mastery_cutoff:
        status = "MASTERED"
    elif percent >= PASSING_CUTOFF_PERCENT:
        status = "PASSING"
    else:
        status = "BELOW_STANDARD"

    return {
        "student_id": submission.student_id,
        "assessment_id": blueprint.assessment_id,
        "status": status,
        "points_earned": points,
        "max_points": max_points,
        "percent": percent,
        "mastery_met": percent >= mastery_cutoff,
    }


def assessment_score_summary(
    school_id: UUID,
    blueprints: Sequence[AssessmentBlueprint],
    submissions: Iterable[AssessmentSubmission],
    *,
    term: str | None = None,
) -> dict:
    """Return tenant-scoped aggregate scoring counts for assessment reporting."""

    scoped_blueprints = [item for item in blueprints if item.school_id == school_id]
    if term:
        scoped_blueprints = [item for item in scoped_blueprints if item.term == term]
    blueprint_by_id = {item.assessment_id: item for item in scoped_blueprints}

    results = []
    for submission in submissions:
        if submission.school_id != school_id:
            continue
        blueprint = blueprint_by_id.get(submission.assessment_id)
        if blueprint is None:
            continue
        results.append(score_submission(blueprint, submission))

    scored = [row for row in results if row["percent"] is not None]
    if scored:
        average_percent = (
            sum(row["percent"] for row in scored) / Decimal(len(scored))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        average_percent = None

    return {
        "school_id": str(school_id),
        "term": term,
        "assessment_count": len(scoped_blueprints),
        "submission_count": len(results),
        "scored_count": len(scored),
        "missing_count": sum(1 for row in results if row["status"] == "MISSING"),
        "excused_count": sum(1 for row in results if row["status"] == "EXCUSED"),
        "mastery_count": sum(1 for row in results if row["status"] == "MASTERED"),
        "average_percent": average_percent,
    }
