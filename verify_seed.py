#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from uuid import UUID
from applications.models import Application, Applicant
from django.db.models import Count

sid = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')

print('=== Local DB State for a535 ===')
total = Applicant.objects.filter(school_id=sid).count()
print(f'Total Applicants: {total}')
print(f'Total Applications: {Application.objects.filter(school_id=sid).count()}')

print('\nSource distribution:')
sources = Applicant.objects.filter(school_id=sid).values('source').annotate(n=Count('id')).order_by('-n')
for s in sources:
    print(f"  {s['source']}: {s['n']}")
