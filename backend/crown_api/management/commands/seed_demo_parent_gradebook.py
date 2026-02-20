"""
Seed minimal parent-gradebook demo data.

Idempotent. Creates:
  - Demo Student in Demo Household
  - Course + Section (term=2026-FALL)
  - Enrollment
  - 2 GradeEntries with scores

Usage:
  python manage.py seed_demo_parent_gradebook [--verbose]
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from core.models import School
from households.models import Household, Student
from academics.models import Course, Section
from academics.models import Enrollment
from gradebook.models import GradeEntry


class Command(BaseCommand):
    help = "Seed demo parent gradebook data (idempotent)"

    def add_arguments(self, parser):
        parser.add_argument("--verbose", action="store_true", default=False)

    def handle(self, *args, **options):
        verbose = options["verbose"]

        def log(msg):
            if verbose:
                self.stdout.write(msg)

        # 1) Demo school
        try:
            school = School.objects.get(name="Crown Demo Christian Academy")
        except School.DoesNotExist:
            raise CommandError(
                "Demo school not found. Run seed_demo_school first."
            )
        school_id = school.id
        log(f"seed_demo_parent_gradebook: school_id={school_id}")

        # 2) Demo household (from ledger seed)
        household = Household.objects.filter(
            school_id=school_id, name="Demo Household (proof)"
        ).first()
        if household is None:
            raise CommandError(
                "Demo household not found. Run seed_demo_ledger_min first."
            )
        log(f"seed_demo_parent_gradebook: household_id={household.pk}")

        # 3) Demo student
        student, created = Student.objects.get_or_create(
            school_id=school_id,
            household=household,
            first_name="Alex",
            last_name="Demo",
            defaults={"grade_level": "10", "is_active": True},
        )
        log(
            f"seed_demo_parent_gradebook: student {'created' if created else 'exists'} pk={student.pk}"
        )

        # 4) Course
        course, created = Course.objects.get_or_create(
            school_id=school_id,
            code="DEMO-MATH",
            defaults={"name": "Demo Mathematics", "credits": 1},
        )
        log(
            f"seed_demo_parent_gradebook: course {'created' if created else 'exists'} pk={course.pk}"
        )

        # 5) Section
        section, created = Section.objects.get_or_create(
            school_id=school_id,
            course=course,
            term="2026-FALL",
        )
        log(
            f"seed_demo_parent_gradebook: section {'created' if created else 'exists'} pk={section.pk}"
        )

        # 6) Enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            school_id=school_id,
            section=section,
            student=student,
        )
        log(
            f"seed_demo_parent_gradebook: enrollment {'created' if created else 'exists'} pk={enrollment.pk}"
        )

        # 7) Grade entries (uses legacy assignment_name — FK is nullable)
        entries = [
            ("Homework 1", "90.00", "100.00"),
            ("Quiz 1", "78.00", "100.00"),
        ]
        for name, earned, possible in entries:
            entry, created = GradeEntry.objects.get_or_create(
                school_id=school_id,
                section=section,
                student=student,
                assignment_name=name,
                defaults={
                    "points_earned": earned,
                    "points_possible": possible,
                },
            )
            log(
                f"seed_demo_parent_gradebook: grade entry '{name}' {'created' if created else 'exists'}"
            )

        self.stdout.write(
            f"seed_demo_parent_gradebook: OK  student_id={student.pk}"
        )
