#!/usr/bin/env python
"""Create test grades and fetch real payload"""
import os
import logging
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from academics.models import Section, Enrollment
from gradebook.models import GradeEntry
from decimal import Decimal
from django.db.models import Count
import json
from core.models import School


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

school_id = os.getenv("DEMO_SCHOOL_ID")
if not school_id:
    school = School.objects.order_by("id").first()
    if not school:
        raise SystemExit("No School found. Set DEMO_SCHOOL_ID or seed a school first.")
    school_id = str(school.id)

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
    
    logger.info("Created grades for section %s", section.id)
    logger.info("School ID: %s", school_id)
else:
    logger.info("ERROR: No section found")
