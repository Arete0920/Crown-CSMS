"""Deterministic local seed for canonical Scheduling master data.

Safe-by-default:
- Refuses to run on Azure/production.
- Writes only canonical academics.Term/Course/Section records.
- Never writes crown_api legacy scheduling masters.
- Does not invent a core.Student <-> households.Student crosswalk for rosters.
- Replays without mutating canonical relationship authority.
- Reuses the current academic year's canonical active term when one exists.

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


def _term_for_year(Term, year):
    """Return a canonical active term inside ``year``, creating one only if absent."""
    school_id = year.school_id
    term = (
        Term.objects.filter(
            school_id=school_id,
            academic_year=year,
            active=True,
        )
        .order_by("ordering", "start_date", "code", "id")
        .first()
    )
    if term is not None:
        if term.start_date < year.start_date or term.end_date > year.end_date:
            raise SystemExit(
                f"Canonical term {term.code} falls outside academic_year={year.id}."
            )
        return term

    start_year = year.start_date.year
    term_code = f"{start_year}-FALL"
    term_name = f"Fall {start_year}"
    term_end = min(year.end_date, date(start_year, 12, 31))
    term, created = Term.objects.get_or_create(
        academic_year=year,
        code=term_code,
        defaults={
            "school_id": school_id,
            "name": term_name,
            "school_year": year.name,
            "active": True,
            "start_date": year.start_date,
            "end_date": term_end,
            "ordering": 1,
        },
    )
    if not created:
        if str(term.school_id) != str(school_id):
            raise SystemExit(
                f"Canonical term authority mismatch for academic_year={year.id} code={term.code}."
            )
        if term.start_date < year.start_date or term.end_date > year.end_date:
            raise SystemExit(
                f"Canonical term {term.code} falls outside academic_year={year.id}."
            )
        term_updates = {
            "name": term_name,
            "school_year": year.name,
            "active": True,
            "ordering": 1,
        }
        changed_fields = []
        for field, value in term_updates.items():
            if getattr(term, field) != value:
                setattr(term, field, value)
                changed_fields.append(field)
        if changed_fields:
            term.save(update_fields=[*changed_fields, "updated_at"])
    return term


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
        term = _term_for_year(Term, year)

        courses = {}
        for code, name in (
            ("MATH-101", "Mathematics"),
            ("ELA-101", "English Language Arts"),
        ):
            course, course_created = Course.objects.get_or_create(
                school_id=school_id,
                code=code,
                defaults={"name": name},
            )
            if not course_created and course.name != name:
                course.name = name
                course.save(update_fields=["name", "updated_at"])
            courses[code] = course

        for code, labels in (("MATH-101", ("A", "B")), ("ELA-101", ("A", "B"))):
            course = courses[code]
            for label in labels:
                section_id = _section_id(school_id, year.id, code, label)
                section, section_created = Section.objects.get_or_create(
                    id=section_id,
                    defaults={
                        "school_id": school_id,
                        "course": course,
                        "term_ref": term,
                        "term": term.code,
                        "teacher": None,
                        "teacher_name": "",
                    },
                )
                if not section_created:
                    if (
                        str(section.school_id) != str(school_id)
                        or section.course_id != course.id
                        or section.term_ref_id != term.id
                    ):
                        raise SystemExit(
                            f"Canonical section authority mismatch for section={section_id}."
                        )
                    if section.term != term.code:
                        section.term = term.code
                        section.save(update_fields=["term", "updated_at"])

        logger.info(
            "Seeded canonical Scheduling masters for school=%s year=%s term=%s",
            school_id,
            year.id,
            term.code,
        )

    logger.info("Roster seeding intentionally omitted: ADR-001 forbids guessed cross-domain student identity remapping.")


if __name__ == "__main__":
    run()
