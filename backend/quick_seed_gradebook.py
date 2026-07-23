#!/usr/bin/env python
"""Quick gradebook seed using the current households.Student compatibility spine."""
import logging
import os
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from academics.models import Course, Enrollment, Section
from core.models import School
from gradebook.models import GradeEntry
from households.models import Household, Student

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

school_id = os.getenv("DEMO_SCHOOL_ID")
if not school_id:
    school = School.objects.order_by("id").first()
    if not school:
        raise SystemExit("No School found. Set DEMO_SCHOOL_ID or seed a school first.")
    school_id = str(school.id)

course1, _ = Course.objects.get_or_create(
    code="MATH101",
    school_id=school_id,
    defaults={"name": "Mathematics 101"},
)
course2, _ = Course.objects.get_or_create(
    code="ELA201",
    school_id=school_id,
    defaults={"name": "English 201"},
)

section1, _ = Section.objects.get_or_create(
    school_id=school_id,
    course=course1,
    term="Spring 2026",
    defaults={"teacher_name": "Demo Teacher", "grade_band": "9-12"},
)
section2, _ = Section.objects.get_or_create(
    school_id=school_id,
    course=course2,
    term="Spring 2026",
    defaults={"teacher_name": "Demo Teacher", "grade_band": "9-12"},
)

household, _ = Household.objects.get_or_create(
    school_id=school_id,
    name="CROWN Gradebook Demo Household",
)

students = []
for i in range(1, 4):
    student, _ = Student.objects.get_or_create(
        school_id=school_id,
        household=household,
        first_name="Student",
        last_name=f"Test{i}",
        defaults={"grade_level": "9"},
    )
    students.append(student)

for student in students:
    Enrollment.objects.get_or_create(
        section=section1,
        student=student,
        defaults={"school_id": school_id},
    )

assignments = [
    ("Quiz 1", Decimal("10.0")),
    ("Homework 1", Decimal("20.0")),
    ("Midterm", Decimal("50.0")),
]

for student in students:
    for assignment_name, points_possible in assignments:
        GradeEntry.objects.get_or_create(
            school_id=school_id,
            section=section1,
            student=student,
            assignment_name=assignment_name,
            defaults={
                "points_earned": points_possible * Decimal("0.90"),
                "points_possible": points_possible,
            },
        )

logger.info("Created 2 sections")
logger.info("Enrolled 3 students in %s", course1.name)
logger.info("Created %s assignments with grades", len(assignments))
logger.info("Section 1 ID: %s", section1.id)
logger.info("Section 2 ID: %s", section2.id)
