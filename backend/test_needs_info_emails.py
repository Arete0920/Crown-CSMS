#!/usr/bin/env python
"""
Test script for AID_GENERATE_NEEDS_INFO_EMAILS action
"""

import os
import sys
import django
from uuid import uuid4

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from django.test import Client
from core.models import School, AcademicYear, Family, UserAccount
from aid.models import AidApplication
from rest_framework.authtoken.models import Token

def test_generate_needs_info_emails():
    """Test the AID_GENERATE_NEEDS_INFO_EMAILS action"""
    
    client = Client()
    
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
    family = Family.objects.create(school=school, family_name='Test Family for Needs Info')
    app = AidApplication.objects.create(
        school=school,
        family=family,
        academic_year=academic_year,
        status='NEEDS_INFO'  # Important: must be NEEDS_INFO
    )
    
    app_id = str(app.id)
    
    print(f"✓ Created test application: {app_id}")
    print(f"  School: {school_id}")
    print(f"  Year: {year_id}")
    
    # Test the action directly via Python
    print("\n=== Test: Generate Needs-Info Email Drafts ===")
    try:
        # Call director_actions directly
        from crown_api.director_views import director_actions
        from unittest.mock import MagicMock
        
        # Create a mock request
        mock_request = MagicMock()
        mock_request.data = {
            'action': 'AID_GENERATE_NEEDS_INFO_EMAILS',
            'school_id': school_id,
            'year_id': year_id,
            'ids': [app_id]
        }
        mock_request.user = MagicMock()
        
        # Call the function
        response = director_actions(mock_request)
        result = response.data
        
        print(f"✓ Action executed successfully")
        print(f"  Draft Count: {result.get('draft_count', 0)}")
        print(f"  Failures: {result.get('failure_count', 0)}")
        
        if result.get('drafts'):
            draft = result['drafts'][0]
            print(f"\n✓ Email Draft Generated:")
            print(f"  Application ID: {draft['application_id']}")
            print(f"  Family: {draft['family']}")
            print(f"  Subject: {draft['subject']}")
            print(f"\n  Body Preview (first 300 chars):")
            preview = draft['body'][:300].replace('\n', '\n    ')
            print(f"    {preview}...")
        
        if result.get('failures'):
            print(f"\nFailures: {result['failures']}")
        else:
            print(f"\n✅ No failures - email draft generated successfully!")
    
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    print("\n=== Cleanup ===")
    app.delete()
    family.delete()
    print("✓ Test data cleaned up")

if __name__ == '__main__':
    test_generate_needs_info_emails()
