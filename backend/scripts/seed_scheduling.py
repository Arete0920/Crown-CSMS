"""Deterministic local seed for canonical Scheduling master data.

Safe-by-default:
- Refuses to run on Azure/production.
- Writes only canonical academics.Term/Course/Section records.
- Never writes crown_api legacy scheduling masters.
- Does not invent a core.Student <-> households.Student crosswalk for rosters.

Usage (PowerShell):
  cd backend
  .\\venv\\Scripts\\python.exe ..\\backend\\scripts\\seed_scheduling.py
"""

import logging
import os
import uuid
from datetime import date


logger = logging.getLogger(__name__)
SEED_NAMESPACE = uuid.UUID("4c0e4577-36a8-4cc6-a3cc-cf24d128672c")


def _refuse_if_azure() -> None:
    if os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"):
        raise SystemExit("Refusing to run seed_scheduling on Azure/production.")


def _section_id(school_id, academic_year_id, course_code: str, section_label: str) -> uuid.UUID:
    return uuid.uuid5(
        SEED_NAMESPACE,
        f"{school_id}:{academic_year_id}:{course_code}:{section_label}",
    )


def run() -> None:
    _refuse_if_azure()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django

    django.setup()

    from academics.models import Course, Section, Term
    from core.models import AcademicYear

    years = list(
        AcademicYear.objects.filter(is_current=True)
        .select_related("school")
        .order_by("school_id", "start_date")
    )
    if not years:
        raise SystemExit("No current AcademicYear found. Seed school/year data first.")

    for year in years:
        school_id = year.school_id
        term, _ = Term.objects.update_or_create(
            academic_year=year,
            code="2026-SPR",
            defaults={
                "school_id": school_id,
                "name": "Spring 2026",
                "school_year": year.name,
                "active": True,
                "start_date": date(2026, 1, 10),
                "end_date": date(2026, 5, 20),
                "ordering": 1,
            },
        )

        courses = {}
        for code, name in (
            ("MATH-101", "Mathematics"),
            ("ELA-101", "English Language Arts"),
        ):
            course, _ = Course.objects.update_or_create(
                school_id=school_id,
                code=code,
                defaults={"name": name},
            )
            courses[code] = course

        for code, labels in (("MATH-101", ("A", "B")), ("ELA-101", ("A", "B"))):
            course = courses[code]
            for label in labels:
                Section.objects.update_or_create(
                    id=_section_id(school_id, year.id, code, label),
                    defaults={
                        "school_id": school_id,
                        "course": course,
                        "term_ref": term,
                        "term": term.code,
                        "teacher": None,
                        "teacher_name": "",
                    },
                )

        logger.info(
            "Seeded canonical Scheduling masters for school=%s year=%s term=%s",
            school_id,
            year.id,
            term.code,
        )

    logger.info("Roster seeding intentionally omitted: ADR-001 forbids guessed cross-domain student identity remapping.")


if __name__ == "__main__":
    run()
