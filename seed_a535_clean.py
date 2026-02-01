#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from uuid import UUID
from core.models import School, AcademicYear
from households.models import Household
from applications.models import Application, Applicant

sid = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')

# Ensure School and AcademicYear exist
School.objects.get_or_create(
    id=sid,
    defaults={'name': 'Crown Demo School', 'timezone': 'America/New_York', 'is_active': True}
)

ay, _ = AcademicYear.objects.get_or_create(
    school_id=sid,
    name='2026-2027',
    defaults={'start_date': '2026-08-01', 'end_date': '2027-05-31', 'is_current': True}
)

hh, _ = Household.objects.get_or_create(
    school_id=sid,
    defaults={'name': 'Demo Household'}
)

before = Applicant.objects.filter(school_id=sid).count()

# Realistic funnel: each stage is subset of previous
# inquiry (100) → tour_scheduled (65) → tour_completed (42) → submitted (28) → accepted (14) → enrolled (7)
stages_with_distrib = [
    ('inquiry', 30),                    # top of funnel
    ('tour_scheduled', 20),             # 67% of inquiry
    ('tour_completed', 14),             # 70% of scheduled
    ('application_started', 10),        # some don't submit after tour
    ('application_submitted', 8),       # 80% of started
    ('in_review', 5),                   # under review
    ('accepted', 3),                    # accepts
    ('waitlisted', 2),                  # waitlist
    ('declined', 1),                    # declined
    ('enrolled', 1),                    # finally enrolled
]

sources = ['website', 'facebook', 'instagram', 'church_referral', 'direct_mail', 'walk_in']

created = 0
i = 0
for stage, n in stages_with_distrib:
    for _ in range(n):
        i += 1
        app = Application.objects.create(
            school_id=sid,
            household=hh,
            status='DRAFT',
        )
        Applicant.objects.create(
            school_id=sid,
            application=app,
            first_name=f'Lead{i}',
            last_name='Demo',
            grade_applying_for='K',
            source=sources[i % len(sources)],
            flags={'duplicate_suspected': False, 'bot_suspected': False},
        )
        created += 1

after = Applicant.objects.filter(school_id=sid).count()
print(f'Applicants before: {before}')
print(f'Applicants created: {created}')
print(f'Applicants after : {after}')
print(f'✓ Seeded with realistic funnel distribution')
