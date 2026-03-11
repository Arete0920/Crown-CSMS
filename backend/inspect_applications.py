#!/usr/bin/env python
import os
import logging
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from applications.models import Application, Applicant
from django.db.models import Count


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

logger.info("=== APPLICATION COUNTS ===")
logger.info("Total Applications: %s", Application.objects.count())
logger.info("Total Applicants: %s", Applicant.objects.count())

logger.info("\n=== APPLICATION STATUS DISTRIBUTION ===")
statuses = Application.objects.values('status').annotate(n=Count('id')).order_by('-n')
for r in statuses:
    logger.info("  %s: %s", r['status'], r['n'])

logger.info("\n=== APPLICANT SAMPLE ===")
a = Applicant.objects.first()
if a:
    logger.info("ID: %s", a.id)
    logger.info("School ID: %s", a.school_id)
    logger.info("Application ID: %s", a.application_id)
    logger.info("Student: %s", a.student)
    logger.info("Name: %s %s", a.first_name, a.last_name)
    logger.info("Grade: %s", a.grade_applying_for)
    logger.info("Created: %s", a.created_at)
    logger.info("Updated: %s", a.updated_at)
else:
    logger.info("No applicants found")

logger.info("\n=== APPLICATION SAMPLE ===")
app = Application.objects.first()
if app:
    logger.info("ID: %s", app.id)
    logger.info("School ID: %s", app.school_id)
    logger.info("Household: %s", app.household)
    logger.info("Status: %s", app.status)
    logger.info("Submitted at: %s", app.submitted_at)
    logger.info("Decided at: %s", app.decided_at)
    logger.info("Created: %s", app.created_at)
    logger.info("Updated: %s", app.updated_at)
else:
    logger.info("No applications found")
