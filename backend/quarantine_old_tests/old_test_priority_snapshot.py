#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from crown_api.director_views import build_director_priority_snapshot
from core.models import School, AcademicYear

print("=" * 70)
print("Test: Priority Snapshot Builder")
print("=" * 70)

# Get demo data
school = School.objects.filter(name__icontains="demo").first()
year = AcademicYear.objects.filter(name__icontains="2026").first()

if not school or not year:
    print("❌ No demo school/year found. Run seed_demo_school first.")
    sys.exit(1)

print(f"\n✓ Using school: {school.name}")
print(f"✓ Using year: {year.name}")

# Build snapshot
snapshot = build_director_priority_snapshot(str(school.id), year)

if not snapshot:
    print("❌ Snapshot is None")
    sys.exit(1)

print("\n" + "=" * 70)
print("Snapshot Structure")
print("=" * 70)

print(f"\n✓ Aid section keys: {list(snapshot['aid'].keys())}")
print(f"  - needs_info: {len(snapshot['aid']['needs_info'])} items")
print(f"  - accepted_not_posted: {len(snapshot['aid']['accepted_not_posted'])} items")

print(f"\n✓ Finance section keys: {list(snapshot['finance'].keys())}")
print(f"  - balance_due: {len(snapshot['finance']['balance_due'])} items")

print("\n" + "=" * 70)
print("Sample Response Format (JSON-like)")
print("=" * 70)

response = {
    "action": "AID_MARK_NEEDS_INFO_EMAIL_SENT",
    "success_count": 2,
    "failure_count": 0,
    "priority_refresh": snapshot,
}

print(json.dumps({
    "action": response["action"],
    "success_count": response["success_count"],
    "failure_count": response["failure_count"],
    "priority_refresh": {
        "aid": {
            "needs_info_count": len(snapshot['aid']['needs_info']),
            "accepted_not_posted_count": len(snapshot['aid']['accepted_not_posted']),
        },
        "finance": {
            "balance_due_count": len(snapshot['finance']['balance_due']),
        }
    }
}, indent=2))

print("\n✅ Priority snapshot test passed!")
