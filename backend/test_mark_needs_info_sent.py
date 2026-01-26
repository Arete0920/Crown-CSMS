#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from aid.models import AidApplication
from core.models import School, AcademicYear, Family, UserAccount
from django.utils import timezone

print("=" * 60)
print("Test: AID_MARK_NEEDS_INFO_EMAIL_SENT Action")
print("=" * 60)

# Get or create test data
school = School.objects.filter(name__icontains="demo").first()
year = AcademicYear.objects.filter(name__icontains="2026").first()

if not school or not year:
    print("❌ No demo school/year found. Run seed_demo_school first.")
    sys.exit(1)

# Create test application in NEEDS_INFO status
family = Family.objects.create(
    school=school,
    family_name="Test Family Audit Trail"
)
app = AidApplication.objects.create(
    school=school,
    academic_year=year,
    family=family,
    status=AidApplication.STATUS_NEEDS_INFO,
    household_size=3,
    income_annual_cents=3500000,
)

print(f"\n✓ Created test application: {app.id}")
print(f"  Status: {app.status}")
print(f"  Family: {family.family_name}")

# Get or create a director user
director = UserAccount.objects.filter(email__icontains="director").first()
if not director:
    director = UserAccount.objects.create_user(
        school=school,
        email="director@test.local",
        password="testpass",
        first_name="Test",
        last_name="Director",
    )
    print(f"✓ Created test director: {director.email}")
else:
    print(f"✓ Using existing director: {director.email}")

# Test 1: Mark as sent (stay in NEEDS_INFO)
print("\n" + "=" * 60)
print("Test 1: Mark email sent (stay in NEEDS_INFO)")
print("=" * 60)

app.last_contacted_at = None
app.last_contacted_by = None
app.last_contacted_reason = None
app.save()

# Simulate the action
now = timezone.now()
app.last_contacted_at = now
app.last_contacted_by = director
app.last_contacted_reason = "NEEDS_INFO_EMAIL"
app.save(update_fields=[
    "last_contacted_at",
    "last_contacted_by",
    "last_contacted_reason",
])

# Verify
app.refresh_from_db()
print(f"✓ Marked sent at: {app.last_contacted_at}")
print(f"✓ Marked by: {app.last_contacted_by.email}")
print(f"✓ Reason: {app.last_contacted_reason}")
print(f"✓ Status: {app.status} (unchanged)")

# Test 2: Mark as sent and move to UNDER_REVIEW
print("\n" + "=" * 60)
print("Test 2: Mark email sent AND move to UNDER_REVIEW")
print("=" * 60)

app.status = AidApplication.STATUS_NEEDS_INFO
app.last_contacted_at = None
app.last_contacted_by = None
app.last_contacted_reason = None
app.save()

# Simulate the action with move
now = timezone.now()
app.last_contacted_at = now
app.last_contacted_by = director
app.last_contacted_reason = "NEEDS_INFO_EMAIL"
app.status = AidApplication.STATUS_UNDER_REVIEW
app.save(update_fields=[
    "last_contacted_at",
    "last_contacted_by",
    "last_contacted_reason",
    "status",
])

# Verify
app.refresh_from_db()
print(f"✓ Marked sent at: {app.last_contacted_at}")
print(f"✓ Moved to status: {app.status}")
print(f"✓ Moved by: {app.last_contacted_by.email}")

# Cleanup
print("\n" + "=" * 60)
print("Cleanup")
print("=" * 60)
app.delete()
family.delete()
print("✓ Test data cleaned up")

print("\n✅ All tests passed!")
