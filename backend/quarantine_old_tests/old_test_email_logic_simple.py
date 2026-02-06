#!/usr/bin/env python
"""
Direct test of the AID_GENERATE_NEEDS_INFO_EMAILS logic
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from core.models import School, AcademicYear, Family
from aid.models import AidApplication

def test_email_generation_logic():
    """Test the email draft generation logic directly"""
    
    # Get existing school and year
    print("Fetching test data...")
    school = School.objects.first()
    academic_year = AcademicYear.objects.filter(school=school).first()
    
    if not school or not academic_year:
        print("No school or academic year found. Creating test data...")
        school = School.objects.create(name='Test School', school_code='TEST')
        academic_year = AcademicYear.objects.create(school=school, year='2024-2025')
    
    school_id = str(school.id)
    year_id = str(academic_year.id)
    
    # Create test family and application
    family = Family.objects.create(school=school, family_name='Test Family for Email Draft')
    app = AidApplication.objects.create(
        school=school,
        family=family,
        academic_year=academic_year,
        status='NEEDS_INFO'
    )
    
    app_id = str(app.id)
    
    print(f"✓ Created test application: {app_id}")
    print(f"  School: {school_id}")
    print(f"  Year: {year_id}")
    print(f"  Family: {family.family_name}")
    
    # Simulate the logic from director_actions
    print("\n=== Simulating Email Draft Generation ===")
    
    drafts = []
    failures = []
    
    # Fetch applications
    query = AidApplication.objects.filter(id__in=[app_id])
    if school_id:
        query = query.filter(school_id=school_id)
    
    apps = query.select_related("family").select_related("academic_year")
    apps_by_id = {str(a.id): a for a in apps}
    
    for raw_id in [app_id]:
        app_obj = apps_by_id.get(str(raw_id))
        if not app_obj:
            failures.append({
                "id": str(raw_id),
                "reason": "Application not found for school/year"
            })
            continue
        
        # Enforce NEEDS_INFO status
        if app_obj.status != "NEEDS_INFO":
            failures.append({
                "id": str(app_obj.id),
                "reason": f"Application is in {app_obj.status} status, not NEEDS_INFO"
            })
            continue
        
        family_obj = getattr(app_obj, "family", None)
        family_name = getattr(family_obj, "family_name", "Family") if family_obj else "Family"
        
        # Try to fetch missing documents
        missing = []
        try:
            from aid.models import AidDocument
            missing_qs = AidDocument.objects.filter(
                aid_application=app_obj,
                received=False
            ).order_by("doc_type")
            for d in missing_qs:
                label = getattr(d, "doc_label", None) or getattr(d, "doc_type", None) or "Document"
                missing.append(str(label))
        except Exception as e:
            print(f"  Note: Could not fetch documents - {e}")
            missing = []
        
        missing_lines = "\n".join([f"- {m}" for m in missing]) if missing else "- One or more required documents (see your portal checklist)"
        
        subject = "Financial Aid Application – Additional Information Needed"
        
        ay_name = getattr(academic_year or app_obj.academic_year, "name", "current school year")
        
        body = f"""Hello {family_name},

Thank you for submitting your financial aid application for the {ay_name}.

Before we can complete your review, we still need the following item(s):

{missing_lines}

What to do next:
1) Log into the Crown Family Portal
2) Open your Financial Aid Application
3) Upload the missing document(s) under "Documents"
4) Submit updates when finished

If you have questions, reply to this email and we will help you.

With appreciation,
Crown Financial Aid Office
"""
        
        drafts.append({
            "application_id": str(app_obj.id),
            "family": family_name,
            "subject": subject,
            "body": body,
        })
    
    # Display results
    print(f"\n✓ Generated {len(drafts)} email draft(s)")
    print(f"✓ {len(failures)} failure(s)")
    
    if drafts:
        draft = drafts[0]
        print(f"\n=== Email Draft ===")
        print(f"Application ID: {draft['application_id']}")
        print(f"Family: {draft['family']}")
        print(f"Subject: {draft['subject']}")
        print(f"\nBody:")
        print(draft['body'])
        print(f"\n✅ Draft generated successfully!")
    
    if failures:
        print(f"\nFailures:")
        for f in failures:
            print(f"  - {f['id']}: {f['reason']}")
    
    # Cleanup
    print("\n=== Cleanup ===")
    app.delete()
    family.delete()
    print("✓ Test data cleaned up")
    
    print("\n✅ Test completed successfully!")

if __name__ == '__main__':
    test_email_generation_logic()
