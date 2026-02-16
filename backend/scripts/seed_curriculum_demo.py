from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction

from core.models import School
from curriculum.models import CurriculumCourse, CurriculumUnit, CurriculumLesson


def _mk_resources(*pairs):
    return [{"label": p[0], "url": p[1]} for p in pairs]


@transaction.atomic
def seed_curriculum_demo(*, school_id: str) -> dict:
    school = School.objects.get(id=school_id)

    # Idempotent: clear existing curriculum for this school
    CurriculumCourse.objects.filter(school=school).delete()

    courses = [
        {
            "code": "BIB-09",
            "name": "Bible 9: Foundations",
            "subject": "Bible",
            "grade_level": "9",
            "worldview_theme": "Biblical worldview basics; identity in Christ",
            "anchor_scripture_ref": "Colossians 3:23",
            "anchor_scripture_text": "Whatever you do, work heartily, as for the Lord and not for men.",
        },
        {
            "code": "ENG-07",
            "name": "English 7: Reading & Composition",
            "subject": "English",
            "grade_level": "7",
            "worldview_theme": "Truth, beauty, and discernment in stories",
            "anchor_scripture_ref": "Philippians 4:8",
            "anchor_scripture_text": "Whatever is true... think about these things.",
        },
        {
            "code": "HIS-08",
            "name": "History 8: American Heritage",
            "subject": "History",
            "grade_level": "8",
            "worldview_theme": "Providence, civic virtue, and responsibility",
            "anchor_scripture_ref": "Micah 6:8",
            "anchor_scripture_text": "Do justice, love kindness, walk humbly with your God.",
        },
        {
            "code": "MTH-05",
            "name": "Math 5: Number Sense",
            "subject": "Math",
            "grade_level": "5",
            "worldview_theme": "Order and design in creation",
            "anchor_scripture_ref": "1 Corinthians 14:40",
            "anchor_scripture_text": "All things should be done decently and in order.",
        },
    ]

    created_courses = []
    for c in courses:
        created_courses.append(CurriculumCourse.objects.create(school=school, **c))

    # Units + lessons (4 units each, 5 lessons each)
    for course in created_courses:
        for u_idx in range(1, 5):
            unit = CurriculumUnit.objects.create(
                course=course,
                order=u_idx,
                title=f"Unit {u_idx}: Core Concepts",
                essential_question="What does it mean to learn with purpose?",
                big_idea="We learn to know truth, build skill, and serve others well.",
                worldview_focus=course.worldview_theme,
                scripture_ref=course.anchor_scripture_ref,
                scripture_text=course.anchor_scripture_text,
            )
            for l_idx in range(1, 6):
                base = date.today() - timedelta(days=14)  # 2 weeks back, ensures lessons are "due"
                planned = base + timedelta(days=(u_idx - 1) * 7 + (l_idx - 1))
                
                CurriculumLesson.objects.create(
                    unit=unit,
                    order=l_idx,
                    title=f"Lesson {l_idx}: Practice + Reflection",
                    planned_date=planned,
                    objective="Students can explain the key idea and apply it with integrity.",
                    activities="Warmup, guided practice, discussion, exit ticket.",
                    assessment="Exit ticket + short reflection.",
                    worldview_focus=course.worldview_theme,
                    scripture_ref=course.anchor_scripture_ref,
                    scripture_text=course.anchor_scripture_text,
                    resources=_mk_resources(
                        ("Teacher Guide", "https://example.org/teacher-guide"),
                        ("Student Notes", "https://example.org/student-notes"),
                    ),
                )

    return {
        "school_id": str(school.id),
        "courses": CurriculumCourse.objects.filter(school=school).count(),
        "units": CurriculumUnit.objects.filter(course__school=school).count(),
        "lessons": CurriculumLesson.objects.filter(unit__course__school=school).count(),
    }
