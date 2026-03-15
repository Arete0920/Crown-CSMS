"""
Seed academics vertical slice demo data: curriculum hierarchy, assignments, submissions, grades.

Extends existing academics data with:
- Curriculum hierarchy (CurriculumSource, Unit, Lesson, PublisherObjective)
- Assignments linked to objectives
- Submissions with variety (submitted, late, missing)
- Grades with automatic mastery tracking

Usage:
    python manage.py seed_curriculum_vertical_slice --school-id <uuid>
"""
from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from academics.models import (
    Course, Section, Enrollment, Term, Assignment, AssignmentCategory,
    CurriculumSource, Unit, Lesson, PublisherObjective,
    Submission, Grade
)
from academics.services import upsert_grade_for_submission
from core.models import School
from households.models import Student

User = get_user_model()


class Command(BaseCommand):
    help = "Seed curriculum vertical slice (units, lessons, objectives, assignments, submissions, grades)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            type=str,
            required=True,
            help="UUID of school to seed curriculum for",
        )
        parser.add_argument(
            "--assignments-per-lesson",
            type=int,
            default=3,
            help="Number of assignments per lesson (default: 3)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        school_id_str = options["school_id"]
        try:
            school_uuid = uuid.UUID(school_id_str)
        except ValueError:
            self.stderr.write(self.style.ERROR(f"Invalid UUID: {school_id_str}"))
            return

        school = School.objects.filter(pk=school_uuid).first()
        if not school:
            self.stderr.write(self.style.ERROR(f"School {school_uuid} not found"))
            return

        self.stdout.write(self.style.SUCCESS(f"Seeding curriculum for school: {school.name}"))

        # Get or create curriculum source
        source, created = CurriculumSource.objects.get_or_create(
            school_id=school.id,
            name="BJU Press (Scope & Sequence)",
            defaults={
                "source_type": "pdf",
                "reference_link": "",
                "description": "Publisher curriculum from prior research PDFs",
            },
        )
        if created:
            self.stdout.write(f"Created curriculum source: {source.name}")

        # Get a course to attach curriculum to
        course = Course.objects.filter(school_id=school.id).order_by("code").first()
        if not course:
            self.stderr.write(self.style.ERROR("No courses found. Run seed_academics_demo first."))
            return

        self.stdout.write(f"Using course: {course.code} - {course.name}")

        # Create units
        unit1, _ = Unit.objects.get_or_create(
            school_id=school.id,
            course=course,
            sequence_order=1,
            defaults={
                "curriculum_source": source,
                "title": "Unit 1: Foundations",
                "description": "Introductory concepts and vocabulary",
            },
        )
        unit2, _ = Unit.objects.get_or_create(
            school_id=school.id,
            course=course,
            sequence_order=2,
            defaults={
                "curriculum_source": source,
                "title": "Unit 2: Core Concepts",
                "description": "Deep dive into primary topics",
            },
        )

        self.stdout.write(f"Created units: {unit1.title}, {unit2.title}")

        # Create lessons within units
        today = timezone.now().date()
        lessons = []
        for i in range(1, 4):  # 3 lessons per unit
            lesson, _ = Lesson.objects.get_or_create(
                school_id=school.id,
                unit=unit1,
                title=f"Lesson {i}: Topic {i}",
                defaults={
                    "lesson_date": today + timedelta(days=i),
                    "instructional_notes": f"Seed lesson notes for Topic {i}",
                },
            )
            lessons.append(lesson)

            # Create publisher objectives for each lesson
            PublisherObjective.objects.get_or_create(
                school_id=school.id,
                lesson=lesson,
                objective_code=f"BJU-{course.code}-U1-L{i}",
                defaults={
                    "description": f"Students will demonstrate understanding of Topic {i} concepts.",
                },
            )

        self.stdout.write(f"Created {len(lessons)} lessons with objectives")

        # Get a section to create assignments in
        section = Section.objects.filter(school_id=school.id, course=course).first()
        if not section:
            self.stderr.write(self.style.ERROR(f"No sections found for course {course.code}"))
            return

        # Get or create assignment category
        category, _ = AssignmentCategory.objects.get_or_create(
            school_id=school.id,
            section=section,
            name="Homework",
            defaults={
                "weight_percent": Decimal("25.00"),
                "sort_order": 1,
                "is_active": True,
            },
        )

        # Get teacher (first staff user or create demo teacher)
        teacher = User.objects.filter(is_staff=True).first()
        if not teacher:
            teacher = User.objects.filter(username="teacher1").first()
        if not teacher:
            teacher = User.objects.create_user(
                username="teacher_demo",
                email="teacher@demo.local",
                password="crownpass123!",
            )

        # Create assignments linked to lessons/objectives
        now = timezone.now()
        assignments_created = 0
        for idx, lesson in enumerate(lessons):
            objective = lesson.objectives.first()
            for j in range(1, options["assignments_per_lesson"] + 1):
                due_date = (today + timedelta(days=(idx * 7 + j * 2))).isoformat()
                
                assignment, created = Assignment.objects.get_or_create(
                    school_id=school.id,
                    section=section,
                    name=f"{lesson.title} - Assignment {j}",
                    defaults={
                        "category": category,
                        "lesson": lesson,
                        "objective": objective,
                        "points_possible": Decimal("100.00"),
                        "due_date": due_date,
                        "assigned_date": today,
                        "is_published": True,
                    },
                )
                if created:
                    assignments_created += 1

        self.stdout.write(f"Created {assignments_created} assignments")

        # Create submissions for enrolled students
        enrollments = Enrollment.objects.filter(section=section).select_related("student")[:10]
        if not enrollments.exists():
            self.stdout.write(self.style.WARNING("No enrollments found, skipping submissions"))
            return

        assignments = Assignment.objects.filter(section=section, lesson__isnull=False)
        submissions_created = 0
        grades_created = 0

        for enrollment in enrollments:
            student = enrollment.student
            
            # Simulate variety of student performance
            is_high_performer = student.id.hex[0] in "abcdef"  # ~50% high performers
            is_at_risk = student.id.hex[0] in "0123"  # ~25% at-risk

            for assignment in assignments:
                # Create submission
                submission, created = Submission.objects.get_or_create(
                    school_id=school.id,
                    assignment=assignment,
                    enrollment=enrollment,
                    defaults={
                        "status": Submission.Status.ASSIGNED,
                    },
                )
                
                if not created:
                    continue
                
                submissions_created += 1

                # At-risk students: some missing submissions
                if is_at_risk and submission.id.hex[0] in "01":
                    # Leave as ASSIGNED → will show missing
                    continue

                # Mark submitted
                submission.submitted_at = timezone.now() - timedelta(days=2)
                submission.status = Submission.Status.SUBMITTED
                submission.save()

                # Create grade with variety
                if is_high_performer:
                    numeric_score = Decimal("92.00") + Decimal(int(submission.id.hex[0], 16)) % Decimal("8.00")
                elif is_at_risk:
                    numeric_score = Decimal("65.00") + Decimal(int(submission.id.hex[0], 16)) % Decimal("15.00")
                else:
                    numeric_score = Decimal("78.00") + Decimal(int(submission.id.hex[0], 16)) % Decimal("12.00")

                grade = upsert_grade_for_submission(
                    submission=submission,
                    numeric_score=numeric_score,
                    graded_by=teacher,
                    feedback=f"Good work on {assignment.name}",
                )
                grades_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Curriculum vertical slice seeded:\n"
            f"   - Units: 2\n"
            f"   - Lessons: {len(lessons)}\n"
            f"   - Objectives: {len(lessons)}\n"
            f"   - Assignments: {assignments_created}\n"
            f"   - Submissions: {submissions_created}\n"
            f"   - Grades: {grades_created}\n"
            f"   - Mastery records auto-created from grades"
        ))
