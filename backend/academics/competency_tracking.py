from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Sequence
from uuid import UUID


@dataclass(frozen=True)
class CompetencyRubric:
    """Canonical competency definition and mastery rule for Module 021 proof."""

    school_id: UUID
    competency_id: str
    code: str
    title: str
    domain: str
    mastery_threshold: Decimal = Decimal("3.00")
    required_evidence_count: int = 2
    active: bool = True


@dataclass(frozen=True)
class CompetencyEvidence:
    """Evidence item submitted against a competency for one student."""

    school_id: UUID
    evidence_id: str
    competency_id: str
    student_id: str
    score: Decimal
    source_type: str
    submitted: bool = True


VALID_SOURCE_TYPES = {"assessment", "project", "portfolio", "observation", "service"}


def _decimal(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validate_competency_rubric(rubric: CompetencyRubric) -> None:
    """Validate the mastery rubric before evidence is credited."""

    if not rubric.competency_id:
        raise ValueError("competency_id is required")
    if not rubric.code.strip():
        raise ValueError("code is required")
    if not rubric.title.strip():
        raise ValueError("title is required")
    if not rubric.domain.strip():
        raise ValueError("domain is required")
    if rubric.required_evidence_count <= 0:
        raise ValueError("required_evidence_count must be greater than zero")
    threshold = _decimal(rubric.mastery_threshold)
    if threshold < Decimal("0.00") or threshold > Decimal("4.00"):
        raise ValueError("mastery_threshold must be between 0 and 4")


def validate_competency_evidence(evidence: CompetencyEvidence) -> None:
    """Validate one evidence item before it can contribute to mastery."""

    if not evidence.evidence_id:
        raise ValueError("evidence_id is required")
    if not evidence.competency_id:
        raise ValueError("competency_id is required")
    if not evidence.student_id:
        raise ValueError("student_id is required")
    score = _decimal(evidence.score)
    if score < Decimal("0.00") or score > Decimal("4.00"):
        raise ValueError("score must be between 0 and 4")
    if evidence.source_type not in VALID_SOURCE_TYPES:
        raise ValueError("source_type is not recognized")


def competency_rubric_violations(
    school_id: UUID,
    rubrics: Iterable[CompetencyRubric],
) -> list[dict]:
    """Return tenant-scoped rubric-definition issues."""

    seen: set[str] = set()
    violations: list[dict] = []

    scoped = [rubric for rubric in rubrics if rubric.school_id == school_id]
    for rubric in sorted(scoped, key=lambda item: item.competency_id):
        try:
            validate_competency_rubric(rubric)
        except ValueError as exc:
            violations.append(
                {
                    "competency_id": rubric.competency_id,
                    "violation_type": "INVALID_RUBRIC",
                    "message": str(exc),
                }
            )

        if rubric.competency_id in seen:
            violations.append(
                {
                    "competency_id": rubric.competency_id,
                    "violation_type": "DUPLICATE_COMPETENCY_ID",
                    "message": "competency_id must be unique within the scoped school rubric set",
                }
            )
        seen.add(rubric.competency_id)

    return violations


def competency_evidence_summary(
    school_id: UUID,
    rubric: CompetencyRubric,
    evidence_items: Sequence[CompetencyEvidence],
    *,
    student_id: str,
) -> dict:
    """Return tenant-scoped evidence counts and average score for one student competency."""

    validate_competency_rubric(rubric)
    if rubric.school_id != school_id:
        raise ValueError("rubric school_id does not match requested school")

    credited: list[CompetencyEvidence] = []
    rejected: list[dict] = []

    for evidence in evidence_items:
        if evidence.school_id != school_id:
            continue
        if evidence.competency_id != rubric.competency_id:
            continue
        if evidence.student_id != student_id:
            continue
        if not evidence.submitted:
            rejected.append(
                {
                    "evidence_id": evidence.evidence_id,
                    "reason": "NOT_SUBMITTED",
                }
            )
            continue
        try:
            validate_competency_evidence(evidence)
        except ValueError as exc:
            rejected.append(
                {
                    "evidence_id": evidence.evidence_id,
                    "reason": str(exc),
                }
            )
            continue
        credited.append(evidence)

    if credited:
        average_score = (
            sum(_decimal(item.score) for item in credited) / Decimal(len(credited))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        average_score = None

    return {
        "school_id": str(school_id),
        "student_id": student_id,
        "competency_id": rubric.competency_id,
        "evidence_count": len(credited),
        "required_evidence_count": rubric.required_evidence_count,
        "average_score": average_score,
        "rejected_count": len(rejected),
        "rejected": rejected,
    }


def competency_mastery_status(
    school_id: UUID,
    rubric: CompetencyRubric,
    evidence_items: Sequence[CompetencyEvidence],
    *,
    student_id: str,
) -> dict:
    """Return the student's mastery status for one competency."""

    summary = competency_evidence_summary(
        school_id,
        rubric,
        evidence_items,
        student_id=student_id,
    )

    average_score = summary["average_score"]
    if summary["evidence_count"] < rubric.required_evidence_count:
        status = "INSUFFICIENT_EVIDENCE"
        mastered = False
    elif average_score is not None and average_score >= _decimal(rubric.mastery_threshold):
        status = "MASTERED"
        mastered = True
    else:
        status = "DEVELOPING"
        mastered = False

    return {
        **summary,
        "mastery_threshold": _decimal(rubric.mastery_threshold),
        "status": status,
        "mastered": mastered,
    }


def competency_portfolio_gaps(
    school_id: UUID,
    rubrics: Sequence[CompetencyRubric],
    evidence_items: Sequence[CompetencyEvidence],
    *,
    student_id: str,
) -> list[dict]:
    """Return active competencies where a student has not yet reached mastery."""

    gaps: list[dict] = []
    for rubric in sorted(
        [item for item in rubrics if item.school_id == school_id and item.active],
        key=lambda item: item.code,
    ):
        status = competency_mastery_status(
            school_id,
            rubric,
            evidence_items,
            student_id=student_id,
        )
        if not status["mastered"]:
            gaps.append(
                {
                    "competency_id": rubric.competency_id,
                    "code": rubric.code,
                    "title": rubric.title,
                    "status": status["status"],
                    "evidence_count": status["evidence_count"],
                    "required_evidence_count": status["required_evidence_count"],
                    "average_score": status["average_score"],
                }
            )
    return gaps
