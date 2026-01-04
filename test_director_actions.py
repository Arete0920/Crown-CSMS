#!/usr/bin/env python
"""
Test script for the director_actions POST endpoint.

This script demonstrates how to test the new POST /api/director/actions/ endpoint.
"""

import os
import sys
import django
import json
from uuid import uuid4

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from crown_api.models import School, AcademicYear, Student, Family, StudentAid
from rest_framework.authtoken.models import Token

def test_post_director_actions():
    """Test the director_actions endpoint."""
    
    client = Client()
    
    # Create a test superuser (director)
    print("Creating test user...")
    user = User.objects.create_superuser('testdirector', 'test@test.com', 'password123')
    token = Token.objects.get_or_create(user=user)[0]
    
    # Create test data
    print("Creating test school and year...")
    school = School.objects.create(
        name='Test School',
        school_code='TEST001'
    )
    
    year = AcademicYear.objects.create(
        school=school,
        year='2024-2025'
    )
    
    # Create a family
    family = Family.objects.create(
        school=school,
        family_name='Test Family'
    )
    
    # Create a student
    student = Student.objects.create(
        school=school,
        family=family,
        first_name='John',
        last_name='Doe'
    )
    
    # Create an accepted award
    print("Creating test award...")
    award = StudentAid.objects.create(
        student=student,
        academic_year=year,
        awarded_cents=50000,  # $500
        status='ACCEPTED'
    )
    
    award_id = str(award.id)
    school_id = str(school.id)
    year_id = str(year.id)
    
    # Test 1: POST without authentication
    print("\n--- Test 1: POST without authentication ---")
    response = client.post(
        '/api/director/actions/',
        data=json.dumps({
            'action': 'POST_ACCEPTED_AWARDS',
            'school_id': school_id,
            'year_id': year_id,
            'ids': [award_id]
        }),
        content_type='application/json'
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: POST with authentication (success case)
    print("\n--- Test 2: POST with valid authentication ---")
    response = client.post(
        '/api/director/actions/',
        data=json.dumps({
            'action': 'POST_ACCEPTED_AWARDS',
            'school_id': school_id,
            'year_id': year_id,
            'ids': [award_id]
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: POST with missing action
    print("\n--- Test 3: POST with missing action ---")
    response = client.post(
        '/api/director/actions/',
        data=json.dumps({
            'school_id': school_id,
            'year_id': year_id,
            'ids': [award_id]
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 4: POST with unknown action
    print("\n--- Test 4: POST with unknown action ---")
    response = client.post(
        '/api/director/actions/',
        data=json.dumps({
            'action': 'UNKNOWN_ACTION',
            'school_id': school_id,
            'year_id': year_id,
            'ids': [award_id]
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 5: POST with missing ids
    print("\n--- Test 5: POST with missing ids ---")
    response = client.post(
        '/api/director/actions/',
        data=json.dumps({
            'action': 'POST_ACCEPTED_AWARDS',
            'school_id': school_id,
            'year_id': year_id,
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 6: POST with non-existent award id
    print("\n--- Test 6: POST with non-existent award id ---")
    fake_uuid = str(uuid4())
    response = client.post(
        '/api/director/actions/',
        data=json.dumps({
            'action': 'POST_ACCEPTED_AWARDS',
            'school_id': school_id,
            'year_id': year_id,
            'ids': [fake_uuid]
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n=== All tests completed ===")
    
    # Cleanup
    print("\nCleaning up...")
    award.delete()
    student.delete()
    family.delete()
    year.delete()
    school.delete()
    token.delete()
    user.delete()

if __name__ == '__main__':
    test_post_director_actions()
