#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from applications.models import Application, Applicant
from django.db.models import Count

print("=== APPLICATION COUNTS ===")
print(f"Total Applications: {Application.objects.count()}")
print(f"Total Applicants: {Applicant.objects.count()}")

print("\n=== APPLICATION STATUS DISTRIBUTION ===")
statuses = Application.objects.values('status').annotate(n=Count('id')).order_by('-n')
for r in statuses:
    print(f"  {r['status']}: {r['n']}")

print("\n=== APPLICANT SAMPLE ===")
a = Applicant.objects.first()
if a:
    print(f"ID: {a.id}")
    print(f"School ID: {a.school_id}")
    print(f"Application ID: {a.application_id}")
    print(f"Student: {a.student}")
    print(f"Name: {a.first_name} {a.last_name}")
    print(f"Grade: {a.grade_applying_for}")
    print(f"Created: {a.created_at}")
    print(f"Updated: {a.updated_at}")
else:
    print("No applicants found")

print("\n=== APPLICATION SAMPLE ===")
app = Application.objects.first()
if app:
    print(f"ID: {app.id}")
    print(f"School ID: {app.school_id}")
    print(f"Household: {app.household}")
    print(f"Status: {app.status}")
    print(f"Submitted at: {app.submitted_at}")
    print(f"Decided at: {app.decided_at}")
    print(f"Created: {app.created_at}")
    print(f"Updated: {app.updated_at}")
else:
    print("No applications found")
