"""Pure, teacher-editable Praeceptum lesson planning scaffolds.

Only school-authored text and permitted source references belong in a plan.
No publisher lesson content is copied from public reference indexes.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import date, timedelta


@dataclass(frozen=True)
class DailyLessonDraft:
    day: str
    course: str
    unit: str
    lesson: str
    objectives: tuple[str, ...]
    source_reference: str
    biblical_worldview: str = ""
    portrait_of_graduate: str = ""
    opening_review: str = ""
    direct_instruction: str = ""
    guided_practice: str = ""
    independent_practice: str = ""
    differentiation: str = ""
    resources: str = ""
    assessment: str = ""
    homework: str = ""
    teacher_notes: str = ""
    planned_minutes: int = 45

    def to_dict(self) -> dict:
        return asdict(self)


def draft_weekly_lessons(
    *, course: str, unit: str, lesson_titles: list[str],
    objectives_by_lesson: dict[str, list[str]], start_date: date,
    source_reference: str = "", planned_minutes: int = 45,
) -> list[DailyLessonDraft]:
    """Create editable planning shells; never generate copyrighted lesson text."""
    if not course.strip() or not unit.strip():
        raise ValueError("course and unit are required")
    if not 1 <= planned_minutes <= 480:
        raise ValueError("planned_minutes must be between 1 and 480")
    if len(lesson_titles) > 7:
        raise ValueError("a weekly draft supports at most seven lessons")
    if len(set(lesson_titles)) != len(lesson_titles) or any(not x.strip() for x in lesson_titles):
        raise ValueError("lesson titles must be unique and nonempty")
    result = []
    for offset, lesson in enumerate(lesson_titles):
        result.append(DailyLessonDraft(
            day=(start_date + timedelta(days=offset)).isoformat(),
            course=course, unit=unit, lesson=lesson,
            objectives=tuple(objectives_by_lesson.get(lesson, [])),
            source_reference=source_reference,
            planned_minutes=planned_minutes,
        ))
    return result
