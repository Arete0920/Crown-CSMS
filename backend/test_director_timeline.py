#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from crown_api.director_views import director_timeline
from core.models import School, AcademicYear
from aid.models import AidApplication
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

print("=" * 70)
print("Test: Director Timeline Endpoint")
print("=" * 70)

# Get demo data
school = School.objects.filter(name__icontains="demo").first()
year = AcademicYear.objects.filter(name__icontains="2026").first()

if not school or not year:
    print("❌ No demo school/year found. Run seed_demo_school first.")
    sys.exit(1)

print(f"\n✓ Using school: {school.name}")
print(f"✓ Using year: {year.name}")

# Create a fake request with query params
factory = RequestFactory()
request = factory.get(
    f'/api/director/timeline/?school_id={school.id}&year_id={year.id}&limit=20'
)
# Make it authenticated + allow dev access
request.user = AnonymousUser()

# Mock the crown_director_allowed to return True for testing
import crown_api.director_views as dv
original_crown_director_allowed = dv.crown_director_allowed

def mock_director_allowed(req):
    return True

dv.crown_director_allowed = mock_director_allowed

try:
    # Call endpoint
    response = director_timeline(request)
    
    print("\n" + "=" * 70)
    print("Timeline Response")
    print("=" * 70)
    
    data = response.data
    print(f"\nResponse data keys: {list(data.keys())}")
    print(f"Full response: {data}")
    
    # Check for errors
    if 'error' in data:
        print(f"\n❌ Error: {data['error']}")
        print(f"\nNote: Timeline requires director access. Testing with dev toggle...")
        sys.exit(1)
    
    timeline = data['timeline']
    print(f"\n✓ Timeline items: {len(timeline)}")
    
    if timeline:
        print(f"\n✓ Sample items (first 5):")
        for i, item in enumerate(timeline[:5], 1):
            ts = item.get('ts')
            item_type = item.get('type')
            actor = item.get('actor')
            summary = item.get('summary')
            amount = item.get('amount_cents')
            
            print(f"\n  [{i}] {ts.strftime('%Y-%m-%d %H:%M:%S') if ts else 'N/A'}")
            print(f"      Type: {item_type}")
            print(f"      Actor: {actor}")
            print(f"      Summary: {summary}")
            if amount:
                print(f"      Amount: ${amount/100:.2f}")
    
    print("\n" + "=" * 70)
    print("Sample JSON Response Format")
    print("=" * 70)
    
    sample_response = {
        "meta": data['meta'],
        "timeline": [
            {
                "ts": timeline[0]['ts'].isoformat() if timeline else "2026-01-03T00:00:00Z",
                "type": timeline[0]['type'] if timeline else "AID_CONTACT",
                "actor": timeline[0]['actor'] if timeline else "director@test.com",
                "entity": timeline[0]['entity'] if timeline else "AidApplication",
                "entity_id": timeline[0]['entity_id'] if timeline else "uuid-here",
                "summary": timeline[0]['summary'] if timeline else "NEEDS_INFO_EMAIL: contacted Family Name about financial aid application.",
            }
        ] if timeline else []
    }
    
    print(json.dumps(sample_response, indent=2, default=str))
    
    print("\n✅ Timeline endpoint test passed!")
    
finally:
    dv.crown_director_allowed = original_crown_director_allowed
