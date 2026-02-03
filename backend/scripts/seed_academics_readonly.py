"""Deterministic local seed for Academics read-only spine.

Safe-by-default:
- Refuses to run on Azure (WEBSITE_HOSTNAME/WEBSITE_INSTANCE_ID present)
- Uses get_or_create so it can be re-run without duplicating

Usage (PowerShell):
  cd backend
    .\\venv\\Scripts\\python.exe ..\\backend\\scripts\\seed_academics_readonly.py
"""

import os
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def _refuse_if_azure() -> None:
    if os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"):
        raise SystemExit("Refusing to run seed_academics_readonly on Azure/production.")


def run() -> None:
    _refuse_if_azure()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django

    django.setup()

    from core.models import AcademicYear, School, Staff
    from households.models import Guardian, Household, Student
    from academics.models import Course, Enrollment, Section, TeacherAssignment, Term

    school, _ = School.objects.get_or_create(
        name="Heritage Christian Academy",
        defaults={"timezone": "America/New_York", "is_active": True},
    )

    year, _ = AcademicYear.objects.get_or_create(
        school=school,
        name="2026-2027",
        defaults={
            "start_date": date(2026, 8, 15),
            "end_date": date(2027, 6, 10),
            "is_current": True,
        },
    )

    AcademicYear.objects.filter(school=school).exclude(id=year.id).update(is_current=False)

    term_fall, _ = Term.objects.get_or_create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        defaults={
            "name": "Fall 2026",
            "start_date": date(2026, 8, 15),
            "end_date": date(2026, 12, 15),
            "active": True,
        },
    )
    term_spring, _ = Term.objects.get_or_create(
        school_id=school.id,
        academic_year=year,
        code="2027-SPRING",
        defaults={
            "name": "Spring 2027",
            "start_date": date(2027, 1, 10),
            "end_date": date(2027, 6, 10),
            "active": True,
        },
    )

    course_defs = [
        ("MATH-101", "Mathematics"),
        ("ELA-101", "English Language Arts"),
        ("SCI-101", "Science"),
        ("HIST-101", "History"),
        ("BIBLE-101", "Bible"),
        ("ART-101", "Art"),
        ("MUS-101", "Music"),
        ("PE-101", "Physical Education"),
        ("CS-101", "Computer Science"),
        ("SPAN-101", "Spanish"),
        ("GEOG-101", "Geography"),
        ("ECON-101", "Economics"),
    ]

    courses = []
    for code, name in course_defs:
        c, _ = Course.objects.get_or_create(
            school_id=school.id,
            code=code,
            defaults={"name": name},
        )
        if c.name != name:
            c.name = name
            c.save(update_fields=["name", "updated_at"])
        courses.append(c)

    staff_defs = [
        ("Alice", "Brooks", "alice.brooks@heritage.edu"),
        ("Brian", "Cruz", "brian.cruz@heritage.edu"),
        ("Clara", "Diaz", "clara.diaz@heritage.edu"),
    ]

    teachers = []
    for first, last, email in staff_defs:
        staff, _ = Staff.objects.get_or_create(
            school=school,
            email=email,
            defaults={
                "first_name": first,
                "last_name": last,
                "role_type": "TEACHER",
                "status": "ACTIVE",
            },
        )
        teachers.append(staff)

    sections = []
    section_count = 0
    for idx, course in enumerate(courses):
        for term in (term_fall, term_spring):
            if section_count >= 20:
                break
            section_code = f"A{idx + 1:02d}"
            teacher = teachers[section_count % len(teachers)]
            section, _ = Section.objects.get_or_create(
                school_id=school.id,
                course=course,
                term=term.code,
                defaults={
                    "term_ref": term,
                    "teacher_name": f"{teacher.first_name} {teacher.last_name}",
                    "grade_band": "K-5",
                },
            )
            if section.term_ref_id != term.id:
                section.term_ref = term
                section.save(update_fields=["term_ref", "updated_at"])
            sections.append(section)
            section_count += 1
        if section_count >= 20:
            break

    households = list(Household.objects.filter(school_id=school.id))
    if not households:
        h1 = Household.objects.create(school_id=school.id, name="Heritage Household A")
        h2 = Household.objects.create(school_id=school.id, name="Heritage Household B")
        households = [h1, h2]

        Guardian.objects.get_or_create(
            school_id=school.id,
            household=h1,
            defaults={
                "first_name": "Pat",
                "last_name": "Anderson",
                "email": "pat.anderson@heritage.edu",
            },
        )
        Guardian.objects.get_or_create(
            school_id=school.id,
            household=h2,
            defaults={
                "first_name": "Morgan",
                "last_name": "Lee",
                "email": "morgan.lee@heritage.edu",
            },
        )

    students = list(Student.objects.filter(school_id=school.id))
    if not students:
        students = [
            Student.objects.create(
                school_id=school.id,
                household=households[0],
                first_name="Ava",
                last_name="Brooks",
                grade_level="3",
            ),
            Student.objects.create(
                school_id=school.id,
                household=households[0],
                first_name="Ben",
                last_name="Brooks",
                grade_level="5",
            ),
            Student.objects.create(
                school_id=school.id,
                household=households[1],
                first_name="Chloe",
                last_name="Cruz",
                grade_level="4",
            ),
            Student.objects.create(
                school_id=school.id,
                household=households[1],
                first_name="Dylan",
                last_name="Cruz",
                grade_level="2",
            ),
        ]

    for idx, section in enumerate(sections):
        teacher = teachers[idx % len(teachers)]
        TeacherAssignment.objects.get_or_create(
            school_id=school.id,
            section=section,
            staff=teacher,
        )

    for idx, student in enumerate(students):
        assigned = sections[idx : idx + 3]
        if len(assigned) < 3:
            assigned = sections[:3]
        for section in assigned:
            Enrollment.objects.get_or_create(
                school_id=school.id,
                section=section,
                student=student,
            )

    print("Seeded academics (read-only):")
    print(f"- AcademicYear: {AcademicYear.objects.filter(school=school).count()}")
    print(f"- Terms: {Term.objects.filter(school_id=school.id).count()}")
    print(f"- Courses: {Course.objects.filter(school_id=school.id).count()}")
    print(f"- Sections: {Section.objects.filter(school_id=school.id).count()}")
    print(f"- Enrollments: {Enrollment.objects.filter(school_id=school.id).count()}")
    print(f"- TeacherAssignments: {TeacherAssignment.objects.filter(school_id=school.id).count()}")


if __name__ == "__main__":
    run()
