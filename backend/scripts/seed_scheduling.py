"""Deterministic local seed for Scheduling module (terms + sections + schedules).

Safe-by-default:
- Refuses to run on Azure (WEBSITE_HOSTNAME/WEBSITE_INSTANCE_ID present)
- Uses get_or_create so it can be re-run without duplicating

Usage (PowerShell):
  cd backend
    .\\venv\\Scripts\\python.exe ..\\backend\\scripts\\seed_scheduling.py

Note: This seed expects students from scripts/seed_households.py.
"""

import os
import logging
from datetime import date


logger = logging.getLogger(__name__)


def _refuse_if_azure() -> None:
    if os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"):
        raise SystemExit("Refusing to run seed_scheduling on Azure/production.")


def run() -> None:
    _refuse_if_azure()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django

    django.setup()

    from core.models import Student
    from crown_api.models import Course, Person, Section, SectionEnrollment, Term

    term, _ = Term.objects.get_or_create(
        code="2026-SPR",
        defaults={"name": "Spring 2026", "active": True, "start_date": date(2026, 1, 10), "end_date": date(2026, 5, 20)},
    )

    # Courses (reuse if they already exist)
    math, _ = Course.objects.get_or_create(course_code="MATH-101", defaults={"name": "Mathematics", "term": "2026", "active": True})
    ela, _ = Course.objects.get_or_create(course_code="ELA-101", defaults={"name": "English Language Arts", "term": "2026", "active": True})

    teacher, _ = Person.objects.get_or_create(
        email="teacher.one@example.com",
        defaults={"first_name": "Teacher", "last_name": "One", "phone": None},
    )

    # Two sections per course
    m1, _ = Section.objects.get_or_create(
        term=term,
        course=math,
        section_code="A",
        defaults={"teacher": teacher, "room": "101", "meeting_days": "MWF", "meeting_time": "09:00", "name_override": ""},
    )
    m2, _ = Section.objects.get_or_create(
        term=term,
        course=math,
        section_code="B",
        defaults={"teacher": None, "room": "102", "meeting_days": "TR", "meeting_time": "10:00", "name_override": ""},
    )
    e1, _ = Section.objects.get_or_create(
        term=term,
        course=ela,
        section_code="A",
        defaults={"teacher": teacher, "room": "201", "meeting_days": "MWF", "meeting_time": "11:00", "name_override": ""},
    )
    e2, _ = Section.objects.get_or_create(
        term=term,
        course=ela,
        section_code="B",
        defaults={"teacher": None, "room": "202", "meeting_days": "TR", "meeting_time": "13:00", "name_override": ""},
    )

    students = list(Student.objects.order_by("last_name", "first_name"))
    if not students:
        raise SystemExit("No students found. Run seed_demo_school or seed_heritage_realism_pack first.")

    # Enroll first two students into two sections each.
    for student in students[:2]:
        SectionEnrollment.objects.get_or_create(section=m1, student=student, defaults={"active": True})
        SectionEnrollment.objects.get_or_create(section=e1, student=student, defaults={"active": True})

    logger.info("Seeded scheduling:")
    logger.info("- Terms: %s", Term.objects.count())
    logger.info("- Sections: %s", Section.objects.count())
    logger.info("- Section enrollments: %s", SectionEnrollment.objects.count())


if __name__ == "__main__":
    run()
