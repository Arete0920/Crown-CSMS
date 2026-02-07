#!/usr/bin/env python
"""Create test grades and fetch real payload"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from academics.models import Section, Enrollment
from gradebook.models import GradeEntry
from decimal import Decimal
from django.db.models import Count
import json

school_id = "b45b8c5a-6708-4597-aad9-a226627b2962"

# Get section with enrollments
section = Section.objects.filter(school_id=school_id).annotate(ecount=Count('enrollments')).filter(ecount__gt=0).first()

if section:
    enrollments = section.enrollments.all()[:3]
    
    # Create grades for each enrolled student
    for enrollment in enrollments:
        for idx, (assg_name, points) in enumerate([("Quiz 1", Decimal("100.00")), ("Homework 1", Decimal("50.00"))]):
            earned = points * Decimal("0.85")
            GradeEntry.objects.get_or_create(
                school_id=school_id,
                section=section,
                student=enrollment.student,
                assignment_name=assg_name,
                defaults={
                    "points_earned": earned,
                    "points_possible": points
                }
            )
    
    print(f"✓ Created grades for section {section.id}")
    print(f"School ID: {school_id}")
else:
    print("ERROR: No section found")
