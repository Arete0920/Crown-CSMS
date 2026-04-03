#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from uuid import UUID
from applications.models import Application, Applicant, ApplicationEvent
from django.db.models import Count

sid = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')

print('=== Local DB State for a535 ===')
apps = Application.objects.filter(school_id=sid)
print(f'Applications: {apps.count()}')
applicants = Applicant.objects.filter(school_id=sid)
print(f'Applicants: {applicants.count()}')

# Check if duplicates by first_name
dupes = applicants.values('first_name').annotate(n=Count('id')).filter(n__gt=1)
print(f'Duplicate first_names: {dupes.count()}')
for d in dupes[:5]:
    print(f"  {d['first_name']}: {d['n']} copies")

# Sample first names
sample = applicants.values_list('first_name', flat=True).order_by('first_name').distinct()[:10]
print(f'\nFirst 10 unique names:')
for name in sample:
    count = applicants.filter(first_name=name).count()
    print(f'  {name}: {count}')

# Check source distribution
print('\nSource distribution:')
sources = applicants.values('source').annotate(n=Count('id')).order_by('-n')
for s in sources:
    print(f"  {s['source']}: {s['n']}")
