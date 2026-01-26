#!/usr/bin/env python
"""
Test script for the director_actions POST endpoint.

This script demonstrates how to test the new POST /api/director/actions/ endpoint.
"""

import os
import sys
import django
import json
from datetime import date
from uuid import uuid4

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

# The Django test Client uses HTTP_HOST=testserver by default. When this script
# runs outside pytest/Django's test runner, that host can be rejected by
# ALLOWED_HOSTS. Make it safe locally without touching settings.py.
from django.conf import settings

if "testserver" not in getattr(settings, "ALLOWED_HOSTS", []):
    settings.ALLOWED_HOSTS.append("testserver")

from django.test import Client
from django.contrib.auth import get_user_model

from aid.models import AidAward, AidAuditEvent
from core.models import AcademicYear, Family, School, Student
from finance.models import ChartAccount

from django.db.models.deletion import ProtectedError
from django.db.utils import OperationalError, ProgrammingError

def test_post_director_actions():
    """Test the director_actions endpoint."""
    
    client = Client()
    
    user = None
    school = None
    year = None
    family = None
    student = None
    award = None

    try:
        # Create a test superuser (director)
        print("Creating test user...")
        User = get_user_model()
        username = f"testdirector_{uuid4().hex[:8]}"
        user = User.objects.create_superuser(
            username=username,
            email=f"{username}@test.com",
            password="password123",
        )
    
    # Create test data
        print("Creating test school and year...")
        school = School.objects.create(name="Test School")

        year = AcademicYear.objects.create(
            school=school,
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 10),
            is_current=True,
        )

        # Ensure the AID chart account exists (required for ledger posting)
        ChartAccount.objects.get_or_create(
            school=school,
            code="AID",
            defaults={"name": "Financial Aid", "account_type": "INCOME", "is_active": True},
        )
    
    # Create a family
        family = Family.objects.create(school=school, family_name="Test Family")
    
    # Create a student
        student = Student.objects.create(
            school=school,
            family=family,
            student_number="S00001",
            first_name="John",
            last_name="Doe",
            dob=date(2010, 1, 1),
        )
    
    # Create an accepted award
        print("Creating test award...")
        award = AidAward.objects.create(
            school=school,
            student=student,
            academic_year=year,
            awarded_cents=50000,  # $500
            decision_status=AidAward.DECISION_ACCEPTED,
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

        if response.status_code != 401:
            raise AssertionError(f"Expected 401 for unauthenticated request, got {response.status_code}")

        # Ensure nothing was posted
        award.refresh_from_db()
        if award.ledger_entry_id is not None:
            raise AssertionError("Unauthenticated request posted an award (ledger_entry_id is set)")

        # Test 2: POST with authentication (success case)
        print("\n--- Test 2: POST with valid authentication ---")

        client.force_login(user)
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

        if response.status_code != 200:
            raise AssertionError(f"Expected 200 for authenticated staff request, got {response.status_code}")

        # Test 3: POST with missing action
        print("\n--- Test 3: POST with missing action ---")
        response = client.post(
            '/api/director/actions/',
            data=json.dumps({
                'school_id': school_id,
                'year_id': year_id,
                'ids': [award_id]
            }),
            content_type='application/json'
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
            content_type='application/json'
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
            content_type='application/json'
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        # Test 6: POST with non-existent award id
        print("\n--- Test 6: POST with non-existent award id ---")
        fake_id = 999999999
        response = client.post(
            '/api/director/actions/',
            data=json.dumps({
                'action': 'POST_ACCEPTED_AWARDS',
                'school_id': school_id,
                'year_id': year_id,
                'ids': [fake_id]
            }),
            content_type='application/json'
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        print("\n=== All tests completed ===")
    finally:
        # Cleanup best-effort (keeps repeated runs stable)
        # Order matters due to PROTECT relationships.
        if award is not None:
            # If a ledger entry was created, delete award first so the ledger entry isn't protected.
            ledger_entry_id = getattr(award, "ledger_entry_id", None)
            try:
                award.delete()
            except ProtectedError:
                pass
            if ledger_entry_id:
                from core.models import LedgerEntry

                try:
                    LedgerEntry.objects.filter(id=ledger_entry_id).delete()
                except ProtectedError:
                    pass

        if school is not None:
            from core.models import LedgerEntry

            try:
                AidAuditEvent.objects.filter(school=school).delete()
            except ProtectedError:
                pass

            # Ensure ledger entries are removed before deleting ChartAccounts
            try:
                LedgerEntry.objects.filter(school=school).delete()
            except ProtectedError:
                pass

            try:
                ChartAccount.objects.filter(school=school).delete()
            except ProtectedError:
                pass
        if student is not None:
            try:
                student.delete()
            except ProtectedError:
                pass
        if family is not None:
            try:
                family.delete()
            except ProtectedError:
                pass
        if year is not None:
            try:
                year.delete()
            except ProtectedError:
                pass
        if school is not None:
            try:
                school.delete()
            except ProtectedError:
                pass
        if user is not None:
            try:
                user.delete()
            except (ProtectedError, OperationalError, ProgrammingError):
                pass

if __name__ == '__main__':
    test_post_director_actions()
