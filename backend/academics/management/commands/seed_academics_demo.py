"""
Seed deterministic academics data (courses, sections, enrollments) for DEV demos.

Designed for Azure DEV OPS reset workflow:
- Idempotent: get_or_create for all models with unique constraints
- Deterministic: fixed codes (MATH-101, ENG-101), no random collisions
- Multi-run safe: can be called multiple times without duplication

Creates:
- 2 Courses (MATH-101, ENG-101)
- 2 Sections per course (one per term)
- Enrollments: first 25 active students per section (or fewer if < 25 exist)

Usage:
    python manage.py seed_academics_demo --school-id <uuid>
"""
from __future__ import annotations

import uuid
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from academics.models import Course, Section, Enrollment, Term
from core.models import School, AcademicYear
from households.models import Student, Household


class Command(BaseCommand):
    help = "Seed demo academics (courses, sections, enrollments) for OPS reset workflow."

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            type=str,
            required=True,
            help="UUID of school to seed academics for",
        )
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete existing academics data before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        school_id_str = options["school_id"]
        try:
            school_uuid = uuid.UUID(school_id_str)
        except ValueError:
            self.stderr.write(self.style.ERROR(f"Invalid UUID: {school_id_str}"))
            return

        # Verify school exists (get_or_create for idempotency)
        school, created = School.objects.get_or_create(
            id=school_uuid,
            defaults={
                "name": "Demo School",
                "timezone": "America/Chicago",
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(self.style.WARNING(f"Created school: {school.id}"))
        
        # Wipe if requested
        if options.get("wipe"):
            self._wipe_academics(school)
            self.stdout.write(self.style.SUCCESS(f"Wiped academics for school {school.id}"))

        # Get or create academic year
        academic_year, _ = AcademicYear.objects.get_or_create(
            school=school,
            name="2025-2026",
            defaults={
                "start_date": date(2025, 8, 15),
                "end_date": date(2026, 6, 10),
                "is_current": True,
            }
        )

        # Get or create term
        term, _ = Term.objects.get_or_create(
            school_id=school.id,
            academic_year=academic_year,
            code="2026-SPRING",
            defaults={
                "name": "Spring 2026",
                "start_date": date(2026, 1, 15),
                "end_date": date(2026, 6, 10),
                "active": True,
            }
        )

        # Create courses (idempotent)
        course_specs = [
            ("MATH-101", "Mathematics 101"),
            ("ENG-101", "English 101"),
        ]

        courses = []
        for code, name in course_specs:
            course, created = Course.objects.get_or_create(
                school_id=school.id,
                code=code,
                defaults={"name": name}
            )
            courses.append(course)
            status = "created" if created else "exists"
            self.stdout.write(f"  Course {code}: {status}")

        # Create sections (idempotent)
        sections = []
        for course in courses:
            section, created = Section.objects.get_or_create(
                school_id=school.id,
                course=course,
                term=term.code,
                defaults={
                    "term_ref": term,
                    "teacher_name": "Demo Teacher",
                    "grade_band": "9-12",
                }
            )
            sections.append(section)
            status = "created" if created else "exists"
            self.stdout.write(f"  Section {course.code}-{term.code}: {status}")

        # Get active students (or create minimal set)
        students = list(Student.objects.filter(school_id=school.id, is_active=True)[:25])
        
        if not students:
            self.stdout.write(self.style.WARNING("No active students found. Creating demo students..."))
            students = self._create_demo_students(school, count=25)

        # Create enrollments (idempotent)
        enrollment_count = 0
        for section in sections:
            for student in students:
                _, created = Enrollment.objects.get_or_create(
                    school_id=school.id,
                    section=section,
                    student=student,
                )
                if created:
                    enrollment_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"✓ Academics seeded: {len(courses)} courses, {len(sections)} sections, "
            f"{enrollment_count} enrollments ({len(students)} students)"
        ))

    def _wipe_academics(self, school: School) -> None:
        """Delete academics data in FK-safe order."""
        # 1. Delete enrollments first (references sections + students)
        deleted_enrollments, _ = Enrollment.objects.filter(school_id=school.id).delete()
        
        # 2. Delete sections (references courses + terms)
        deleted_sections, _ = Section.objects.filter(school_id=school.id).delete()
        
        # 3. Delete courses (no dependencies)
        deleted_courses, _ = Course.objects.filter(school_id=school.id).delete()
        
        # 4. Delete terms (no dependencies after sections deleted)
        deleted_terms, _ = Term.objects.filter(school_id=school.id).delete()
        
        self.stdout.write(
            f"  Deleted: {deleted_enrollments} enrollments, {deleted_sections} sections, "
            f"{deleted_courses} courses, {deleted_terms} terms"
        )

    def _create_demo_students(self, school: School, count: int = 25) -> list[Student]:
        """Create minimal demo students for academics (idempotent)."""
        students = []
        
        # Get or create demo household
        household, _ = Household.objects.get_or_create(
            school_id=school.id,
            name="Demo Household",
            defaults={"is_active": True}
        )
        
        for i in range(1, count + 1):
            student, created = Student.objects.get_or_create(
                school_id=school.id,
                household=household,
                first_name=f"Student{i}",
                last_name="Demo",
                defaults={
                    "grade_level": "9",
                    "is_active": True,
                }
            )
            students.append(student)
            if created:
                self.stdout.write(f"    Created student: {student.first_name} {student.last_name}")
        
        return students
