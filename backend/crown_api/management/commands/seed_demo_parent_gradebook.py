"""
Seed deterministic parent-gradebook demo data.

Produces:
  - Demo Student "Alex Demo" in Demo Household
  - Course MATH-101 + Section (term=2026-FALL)
  - Enrollment
  - 2 GradeEntries with known scores (Quiz 1: 18/20, Homework 1: 9/10)

Idempotent (get_or_create everywhere).
Depends on: seed_demo_school (seed_demo_ledger_min optional — household is
created here if absent).

Usage:
  python manage.py seed_demo_parent_gradebook [--verbose]
"""
from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from academics.models import Course, Enrollment, Section
from core.models import School
from gradebook.models import GradeEntry
from households.models import Household, Student

DEMO_SCHOOL_NAME = "Heritage Christian Academy"
DEMO_HOUSEHOLD_NAME = "Demo Household (proof)"
DEMO_STUDENT_FIRST = "Alex"
DEMO_STUDENT_LAST = "Demo"


class Command(BaseCommand):
    help = "Seed deterministic parent-gradebook demo data (Alex Demo, idempotent)"

    def add_arguments(self, parser):
        parser.add_argument("--verbose", action="store_true", default=False)

    @transaction.atomic
    def handle(self, *args, **options):
        verbose = options["verbose"]

        def log(msg):
            if verbose:
                self.stdout.write(msg)

        # 1) Demo school
        school = School.objects.filter(name=DEMO_SCHOOL_NAME).first()
        if not school:
            raise CommandError(
                f"School '{DEMO_SCHOOL_NAME}' not found. Run seed_demo_school first."
            )
        log(f"seed_demo_parent_gradebook: school_id={school.id}")

        # 2) Demo household (idempotent — created here if absent)
        household, _ = Household.objects.get_or_create(
            school_id=school.id,
            name=DEMO_HOUSEHOLD_NAME,
        )
        log(f"seed_demo_parent_gradebook: household_id={household.pk}")

        # 3) Demo student — filter+create pattern avoids constraint collisions
        student = Student.objects.filter(
            school_id=school.id,
            household=household,
            first_name=DEMO_STUDENT_FIRST,
            last_name=DEMO_STUDENT_LAST,
        ).first()
        if not student:
            student = Student.objects.create(
                school_id=school.id,
                household=household,
                first_name=DEMO_STUDENT_FIRST,
                last_name=DEMO_STUDENT_LAST,
                grade_level="10",
                is_active=True,
            )
        log(f"seed_demo_parent_gradebook: student_id={student.pk}")

        # 4) Course
        course, _ = Course.objects.get_or_create(
            school_id=school.id,
            code="MATH-101",
            defaults={"name": "Math 101"},
        )
        log(f"seed_demo_parent_gradebook: course_id={course.pk}")

        # 5) Section — Section has no 'name' field; keyed on course + term
        section, _ = Section.objects.get_or_create(
            school_id=school.id,
            course=course,
            term="2026-FALL",
        )
        log(f"seed_demo_parent_gradebook: section_id={section.pk}")

        # 6) Enrollment
        enrollment, _ = Enrollment.objects.get_or_create(
            school_id=school.id,
            section=section,
            student=student,
        )
        log(f"seed_demo_parent_gradebook: enrollment_id={enrollment.pk}")

        # 7) Grade entries (assignment FK is nullable — use assignment_name)
        entries = [
            ("Quiz 1",     Decimal("18.0"), Decimal("20.0")),
            ("Homework 1", Decimal("9.0"),  Decimal("10.0")),
        ]
        for name, earned, possible in entries:
            _, created = GradeEntry.objects.get_or_create(
                school_id=school.id,
                section=section,
                student=student,
                assignment_name=name,
                defaults={"points_earned": earned, "points_possible": possible},
            )
            log(f"seed_demo_parent_gradebook: grade_entry '{name}' {'created' if created else 'exists'}")

        self.stdout.write(
            f"seed_demo_parent_gradebook: OK  student_id={student.pk}"
        )
