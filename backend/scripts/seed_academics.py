"""Deterministic local seed for Academics module (attendance + grades).

Safe-by-default:
- Refuses to run on Azure (WEBSITE_HOSTNAME/WEBSITE_INSTANCE_ID present)
- Uses get_or_create so it can be re-run without duplicating

Usage (PowerShell):
  cd backend
    .\\venv\\Scripts\\python.exe ..\\backend\\scripts\\seed_academics.py

Note: This seed expects students from seed_households.py (HCA-0001+).
"""

import os
from datetime import timedelta


def _refuse_if_azure() -> None:
    if os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"):
        raise SystemExit("Refusing to run seed_academics on Azure/production.")


def run() -> None:
    _refuse_if_azure()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django

    django.setup()

    from django.utils import timezone

    from crown_api.models import (
        AttendanceRecord,
        Course,
        CourseEnrollment,
        GradeRecord,
        StudentProfile,
    )

    # Courses
    math, _ = Course.objects.get_or_create(
        course_code="MATH-101",
        defaults={"name": "Mathematics", "term": "2026", "active": True},
    )
    ela, _ = Course.objects.get_or_create(
        course_code="ELA-101",
        defaults={"name": "English Language Arts", "term": "2026", "active": True},
    )

    students = list(StudentProfile.objects.select_related("student", "student__person").all())
    if not students:
        raise SystemExit(
            "No StudentProfile rows found. Run scripts/seed_households.py first."
        )

    # Enroll everyone in both courses.
    for sp in students:
        CourseEnrollment.objects.get_or_create(student=sp.student, course=math)
        CourseEnrollment.objects.get_or_create(student=sp.student, course=ela)

    today = timezone.localdate()
    posted_at = timezone.now()

    for idx, sp in enumerate(students):
        student = sp.student

        # Attendance: last 3 days, alternating statuses per student for determinism.
        for day_offset in range(3):
            date = today - timedelta(days=day_offset)
            status = AttendanceRecord.STATUS_PRESENT
            minutes_late = None
            if (idx + day_offset) % 5 == 0:
                status = AttendanceRecord.STATUS_TARDY
                minutes_late = 5
            elif (idx + day_offset) % 7 == 0:
                status = AttendanceRecord.STATUS_ABSENT

            AttendanceRecord.objects.get_or_create(
                student=student,
                course=math,
                date=date,
                defaults={
                    "status": status,
                    "minutes_late": minutes_late,
                    "notes_public": "",
                },
            )

        # Grades: 2 deterministic grade items per student.
        GradeRecord.objects.get_or_create(
            student=student,
            course=math,
            period="Q1",
            assignment_name="Unit 1 Quiz",
            defaults={
                "category": "Quiz",
                "score": 90 + (idx % 10),
                "score_max": 100,
                "letter_grade": "A",
                "posted_at": posted_at,
                "notes_public": "",
            },
        )
        GradeRecord.objects.get_or_create(
            student=student,
            course=ela,
            period="Q1",
            assignment_name="Reading Comprehension",
            defaults={
                "category": "Assignment",
                "score": 85 + (idx % 15),
                "score_max": 100,
                "letter_grade": "B",
                "posted_at": posted_at,
                "notes_public": "",
            },
        )

    print("Seeded academics:")
    print(f"- Courses: {Course.objects.count()}")
    print(f"- Course enrollments: {CourseEnrollment.objects.count()}")
    print(f"- Attendance records: {AttendanceRecord.objects.count()}")
    print(f"- Grade records: {GradeRecord.objects.count()}")


if __name__ == "__main__":
    run()
