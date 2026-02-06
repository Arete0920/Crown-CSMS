#!/usr/bin/env python
"""Create one real grade entry for real API test"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from academics.models import Section, Enrollment
from gradebook.models import GradeEntry
from decimal import Decimal
from django.db.models import Count

school_id = "7d965a83-e714-413d-86ba-776c4176b50f"

# Get first section with enrollments
section = Section.objects.filter(school_id=school_id).annotate(ecount=Count('enrollments')).filter(ecount__gt=0).first()

if section:
    enrollment = section.enrollments.first()
    if enrollment:
        # Create one grade entry
        ge, created = GradeEntry.objects.get_or_create(
            school_id=school_id,
            section=section,
            student=enrollment.student,
            assignment_name="Quiz 1",
            defaults={
                "points_earned": Decimal("85.50"),
                "points_possible": Decimal("100.00")
            }
        )
        # Create another for variety
        GradeEntry.objects.get_or_create(
            school_id=school_id,
            section=section,
            student=enrollment.student,
            assignment_name="Homework 1",
            defaults={
                "points_earned": Decimal("92.00"),
                "points_possible": Decimal("100.00")
            }
        )
        print(f"✓ Section: {section.id}")
        print(f"✓ Student: {enrollment.student.id}")
        print(f"✓ Grades created")
else:
    print("No sections with enrollments")
