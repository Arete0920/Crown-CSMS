"""
Seed deterministic academics data (courses, sections, enrollments) for DEV demos.

Designed for Azure DEV OPS reset workflow:
- Idempotent: get_or_create for all models with unique constraints
- Deterministic: fixed codes (MATH-101, ENG-101, SCI-101), no random collisions
- Multi-run safe: can be called multiple times without duplication

Creates:
- 3 Courses (MATH-101, ENG-101, SCI-101)
- 2 Terms (Fall, Spring)
- 4 Sections (distributed across courses and terms)
- 1 teacher per section
- 12-18 students per section

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
from django.contrib.auth import get_user_model
from households.models import Student, Household

User = get_user_model()


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
            }s (Fall and Spring)
        term_fall, _ = Term.objects.get_or_create(
            school_id=school.id,
            academic_year=academic_year,
            code="2026-FALL",
            defaults={
                "name": "Fall 2026",
                "school_year": academic_year.name,
                "start_date": date(2025, 8, 15),
                "end_date": date(2025, 12, 20),
                "ordering": 1,
                "active": True,
            }
        )

        term_spring, _ = Term.objects.get_or_create(
            school_id=school.id,
            academic_year=academic_year,
            code="2026-SPRING",
            defaults={
                "name": "Spring 2026",
                "school_year": academic_year.name,
                "start_date": date(2026, 1, 15),
                "end_date": date(2026, 6, 10),
                "ordering": 2,
                "active": True,
            }
        )

        terms = [term_fall, term_spring]

        # Create courses (idempotent) - 3 courses
        course_specs = [
            ("MATH-101", "Mathematics 101", "Mathematics", "1.00"),
            ("ENG-101", "English 101", "English", "1.00"),
            ("SCI-101", "Science 101", "Science
        course_specs = [
            ("MATH-101", "Mathematics 101", "Mathematics", "1.00"),
            ("ENG-101", "English 101", "English", "1.00"),
        ]Get or create demo teachers (1 per section = 4 teachers)
        teachers = []
        for i in range(1, 5):
            teacher, created = User.objects.get_or_create(
                username=f"teacher{i}@demo.school",
                defaults={
                    "email": f"teacher{i}@demo.school",
                    "first_name": f"Teacher{i}",
                    "last_name": "Demo",
                    "is_staff": False,
                    "school": school,
                }
            )
            teachers.append(teacher)
            status = "created" if created else "exists"
            self.stdout.write(f"  Teacher {teacher.username}: {status}")

        # Create sections (idempotent) - 4 sections across courses and terms
        # Distribution: MATH-Fall, MATH-Spring, ENG-Fall, SCI-Fall
        section_specs = [
            (courses[0], terms[0], teachers[0], "MATH-101 Fall"),  # Math Fall
            (courses[0], terms[1], teachers[1], "MATH-101 Spring"),  # Math Spring
            (courses[1], terms[0], teachers[2], "ENG-101 Fall"),  # English Fall
            (courses[2], terms[0], teachers[3], "SCI-101 Fall"),  # Science Fall
        ]

        sections = []
        for course, term, teacher, label in section_specs:
            section, created = Section.objects.get_or_create(
                school_id=school.id,
                course=course,
                term=term.code,
                defaults={
                    "term_ref": term,
                    "teacher": teacher,
                    "teacher_name": f"{teacher.first_name} {teacher.last_name}",
                    "grade_band": "9-12",
                }
            )
            # Update teacher FK if section already exists but teacher wasn't set
            if not created and section.teacher is None:
                section.teacher = teacher
                section.teacher_name = f"{teacher.first_name} {teacher.last_name}"
                section.save(update_fields=["teacher", "teacher_name"])
            
            sections.append(section)
            status = "created" if created else "exists"
            self.stdout.write(f"  Section {label}: {status}")

        # Get active students (12-18 per section = 48-72 total needed)
        # For demo, aim for ~60 students to distribute
        students = list(Student.objects.filter(school_id=school.id, is_active=True)[:60])
        
        if len(students) < 48:
            self.stdout.write(self.style.WARNING(f"Only {len(students)} students found. Creating more..."))
            needed = 60 - len(students)
            new_students = self._create_demo_students(school, count=needed)
            students.extend(new_students)

        # Create enrollments (12-18 students per section)
        enrollment_count = 0
        students_per_section = [15, 12, 18, 15]  # Varied realistic distribution
        offset = 0
        
        for idx, section in enumerate(sections):
            count = students_per_section[idx]
            section_students = students[offset : offset + count]
            
            for student in section_students:
                _, created = Enrollment.objects.get_or_create(
                    school_id=school.id,
                    section=section,
                    student=student,
                )
                if created:
                    enrollment_count += 1
            
            offset += count
            self.stdout.write(f"    Section {idx+1}: {len(section_students)} enrolled")

        self.stdout.write(self.style.SUCCESS(
            f"✓ Academics seeded: {len(courses)} courses, {len(terms)} terms, "
            f"{len(sections)} sections, {enrollment_count} enrollmentsund. Creating demo students..."))
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
