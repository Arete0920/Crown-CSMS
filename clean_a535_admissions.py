#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from uuid import UUID
from applications.models import Application, Applicant, ApplicationEvent

sid = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')

print('Deleting admissions data for a535...')
before_app = Application.objects.filter(school_id=sid).count()
before_appl = Applicant.objects.filter(school_id=sid).count()

# Delete in order: ApplicationEvent → Applicant → Application
ApplicationEvent.objects.filter(school_id=sid).delete()
Applicant.objects.filter(school_id=sid).delete()
Application.objects.filter(school_id=sid).delete()

after_app = Application.objects.filter(school_id=sid).count()
after_appl = Applicant.objects.filter(school_id=sid).count()

print(f'Applications: {before_app} → {after_app}')
print(f'Applicants: {before_appl} → {after_appl}')
print('✓ Cleaned. Ready for fresh seed.')
