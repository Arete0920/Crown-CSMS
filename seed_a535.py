#!/usr/bin/env python
"""Manual seeding script for a535... school_id admissions funnel."""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from uuid import UUID
from datetime import date
from core.models import School, AcademicYear
from applications.models import Applicant
from households.models import Household
from core.management.commands.golden_path_bootstrap import seed_admissions_funnel

sid = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')

# Ensure School and AcademicYear exist
school, _ = School.objects.get_or_create(
    id=sid,
    defaults={'name': 'Crown Demo School', 'timezone': 'America/New_York', 'is_active': True}
)
print(f'✓ School: {school.name}')

ay, ay_created = AcademicYear.objects.get_or_create(
    school_id=sid,
    name='2025-2026',
    defaults={'start_date': date(2025, 8, 1), 'end_date': date(2026, 6, 30), 'is_current': True}
)
print(f'✓ AcademicYear: {ay.name} (is_current={ay.is_current}, created={ay_created})')

# Ensure at least one Household exists for this school
household, _ = Household.objects.get_or_create(
    school_id=sid,
    name='Demo Household'
)
print(f'✓ Household: {household.name}')

# Count before
before_count = Applicant.objects.filter(school_id=sid).count()
print(f'✓ Applicants before: {before_count}')

# Seed admissions funnel
seed_admissions_funnel(school_id=sid)

# Count after
after_count = Applicant.objects.filter(school_id=sid).count()
print(f'✓ Applicants after: {after_count}')
print(f'✓ Seeded {after_count - before_count} applicants')
print(f'\n✓ SUCCESS: Ready for smoke test with $SCHOOL_ID = "a5351136-98fe-4d48-add0-fa8f62d9ceff"')
