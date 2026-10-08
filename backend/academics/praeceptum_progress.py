"""Praeceptum curriculum progression and coverage calculations.

Praeceptum does not duplicate classroom records. It derives curriculum state
from the existing governed academics data:

Intended -> Planned -> Delivered -> Assessed -> Mastered

The pure calculator is intentionally separate from the ORM adapter so coverage
semantics can be regression-tested deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AbstractSet, Iterable
from uuid import UUID


DELIVERED_STATUSES = frozenset({"taught", "partial"})


@dataclass(frozen=True)
class CurriculumProgress:
    intended: frozenset[str]
    planned: frozenset[str]
    delivered: frozenset[str]
    assessed: frozenset[str]
    mastered: frozenset[str]

    @staticmethod
    def _pct(numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 1)

    @property
    def intended_count(self) -> int:
        return len(self.intended)

    @property
    def planned_count(self) -> int:
        return len(self.planned)

    @property
    def delivered_count(self) -> int:
        return len(self.delivered)

    @property
    def assessed_count(self) -> int:
        return len(self.assessed)

    @property
    def mastered_count(self) -> int:
        return len(self.mastered)

    @property
    def planning_coverage_percent(self) -> float:
        return self._pct(len(self.planned & self.intended), len(self.intended))

    @property
    def delivery_coverage_percent(self) -> float:
        return self._pct(len(self.delivered & self.intended), len(self.intended))

    @property
    def assessment_coverage_percent(self) -> float:
        return self._pct(len(self.assessed & self.intended), len(self.intended))

    @property
    def mastery_coverage_percent(self) -> float:
        return self._pct(len(self.mastered & self.intended), len(self.intended))

    @property
    def intended_not_planned(self) -> frozenset[str]:
        return self.intended - self.planned

    @property
    def planned_not_delivered(self) -> frozenset[str]:
        return (self.planned & self.intended) - self.delivered

    @property
    def delivered_not_assessed(self) -> frozenset[str]:
        return (self.delivered & self.intended) - self.assessed

    @property
    def assessed_not_mastered(self) -> frozenset[str]:
        return (self.assessed & self.intended) - self.mastered

    def as_dict(self) -> dict:
        return {
            "counts": {
                "intended": self.intended_count,
                "planned": self.planned_count,
                "delivered": self.delivered_count,
                "assessed": self.assessed_count,
                "mastered": self.mastered_count,
            },
            "coverage_percent": {
                "planned": self.planning_coverage_percent,
                "delivered": self.delivery_coverage_percent,
                "assessed": self.assessment_coverage_percent,
                "mastered": self.mastery_coverage_percent,
            },
            "gaps": {
                "intended_not_planned": sorted(self.intended_not_planned),
                "planned_not_delivered": sorted(self.planned_not_delivered),
                "delivered_not_assessed": sorted(self.delivered_not_assessed),
                "assessed_not_mastered": sorted(self.assessed_not_mastered),
            },
        }


def calculate_curriculum_progress(
    *,
    intended: Iterable[str],
    planned: Iterable[str],
    delivered: Iterable[str],
    assessed: Iterable[str],
    mastered: Iterable[str],
) -> CurriculumProgress:
    """Normalize objective identifiers and calculate Praeceptum coverage."""

    def normalized(values: Iterable[str]) -> frozenset[str]:
        return frozenset(str(value) for value in values if value is not None and str(value))

    return CurriculumProgress(
        intended=normalized(intended),
        planned=normalized(planned),
        delivered=normalized(delivered),
        assessed=normalized(assessed),
        mastered=normalized(mastered),
    )


def section_curriculum_progress(
    *,
    school_id: UUID | str,
    section_id: UUID | str,
    mastery_threshold: int = 3,
) -> CurriculumProgress:
    """Derive Praeceptum coverage from existing tenant-scoped academics records.

    Mastered means an intended objective has mastery evidence at or above the
    threshold for at least one enrolled student. Cohort mastery rates remain a
    separate reporting concern; this function answers objective-coverage state.
    """

    if mastery_threshold < 1 or mastery_threshold > 4:
        raise ValueError("mastery_threshold must be between 1 and 4")

    from .lesson_execution_models import LessonPlanLesson
    from .models import Assignment, MasteryRecord, PublisherObjective, Section

    section = Section.objects.filter(id=section_id, school_id=school_id).only("id", "course_id").first()
    if section is None:
        raise ValueError("section not found in school scope")

    intended_qs = PublisherObjective.objects.filter(
        school_id=school_id,
        lesson__unit__course_id=section.course_id,
    )
    intended_ids = set(intended_qs.values_list("id", flat=True))

    planned_lesson_ids = LessonPlanLesson.objects.filter(
        school_id=school_id,
        lesson_plan__section_id=section.id,
    ).values_list("lesson_id", flat=True)
    planned_ids = set(
        intended_qs.filter(lesson_id__in=planned_lesson_ids).values_list("id", flat=True)
    )

    delivered_lesson_ids = LessonPlanLesson.objects.filter(
        school_id=school_id,
        lesson_plan__section_id=section.id,
        delivery_status__in=DELIVERED_STATUSES,
    ).values_list("lesson_id", flat=True)
    delivered_ids = set(
        intended_qs.filter(lesson_id__in=delivered_lesson_ids).values_list("id", flat=True)
    )

    assessed_ids = set(
        Assignment.objects.filter(
            school_id=school_id,
            section_id=section.id,
            objective_id__isnull=False,
        ).values_list("objective_id", flat=True)
    ) & intended_ids

    enrolled_student_ids = section.enrollments.values_list("student_id", flat=True)
    mastered_ids = set(
        MasteryRecord.objects.filter(
            school_id=school_id,
            student_id__in=enrolled_student_ids,
            objective_id__in=intended_ids,
            mastery_level__gte=mastery_threshold,
        ).values_list("objective_id", flat=True)
    )

    return calculate_curriculum_progress(
        intended=intended_ids,
        planned=planned_ids,
        delivered=delivered_ids,
        assessed=assessed_ids,
        mastered=mastered_ids,
    )
