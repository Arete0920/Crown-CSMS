#!/usr/bin/env python
"""Quick gradebook seed - create minimal section + enrollments + grades"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from django.contrib.auth import get_user_model
from academics.models import Section, Enrollment, Course
from gradebook.models import GradeEntry
from decimal import Decimal

User = get_user_model()
school_id = "7d965a83-e714-413d-86ba-776c4176b50f"

# Create courses
course1, _ = Course.objects.get_or_create(
    code="MATH101",
    school_id=school_id,
    defaults={"name": "Mathematics 101"}
)

course2, _ = Course.objects.get_or_create(
    code="ELA201",
    school_id=school_id,
    defaults={"name": "English 201"}
)

# Create 2 test sections
section1, _ = Section.objects.get_or_create(
    school_id=school_id,
    course=course1,
    term="Spring 2026",
    defaults={
        "teacher_name": "Demo Teacher",
        "grade_band": "9-12"
    }
)

section2, _ = Section.objects.get_or_create(
    school_id=school_id,
    course=course2,
    term="Spring 2026",
    defaults={
        "teacher_name": "Demo Teacher",
        "grade_band": "9-12"
    }
)

# Create 3 test students
students = []
for i in range(1, 4):
    student, created = User.objects.get_or_create(
        email=f"student{i}@crown-demo.local",
        defaults={
            "username": f"student{i}",
            "first_name": f"Student",
            "last_name": f"Test{i}",
        }
    )
    if created:
        student.set_password("demo1234")
        student.save()
    students.append(student)

# Enroll students in section 1
for student in students:
    Enrollment.objects.get_or_create(
        section=section1,
        student=student,
        school_id=school_id
    )

# Create grades for section 1
assignments = [
    ("Quiz 1", Decimal("10.0")),
    ("Homework 1", Decimal("20.0")),
    ("Midterm", Decimal("50.0")),
]

for student in students:
    for idx, (assg_name, points) in enumerate(assignments):
        earned = points * Decimal("0.90")  # 90% score
        GradeEntry.objects.get_or_create(
            school_id=school_id,
            section=section1,
            student=student,
            assignment_name=assg_name,
            defaults={
                "assignment_order": idx,
                "earned": earned,
                "possible": points
            }
        )

print(f"✓ Created 2 sections")
print(f"✓ Enrolled 3 students in {course1.name}")
print(f"✓ Created {len(assignments)} assignments with grades")
print(f"\nSection 1 ID: {section1.id}")
print(f"Section 2 ID: {section2.id}")
