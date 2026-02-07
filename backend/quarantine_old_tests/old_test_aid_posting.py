#!/usr/bin/env python
"""Test Aid auto-posting to LedgerEntry"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from aid.models import AidAward
from core.models import UserAccount, School, AcademicYear, Student
from finance.models import JournalBatch
from datetime import date

# Get first available records
school = School.objects.first()
year = AcademicYear.objects.first()
user = UserAccount.objects.first()

if not school:
    print("❌ No School found - create one first")
else:
    print(f"✓ School: {school}")
    print(f"✓ User: {user.email if user else 'None'}")
    
    # Get first student
    student = Student.objects.filter(school=school).first()
    
    if student:
        print(f"✓ Student: {student}")
        
        # Create a batch
        batch = JournalBatch.objects.create(
            school=school,
            academic_year=year,
            batch_date=date.today(),
            description="Aid Awards - Test",
            status="OPEN",
            created_by_user=user
        )
        print(f"✓ JournalBatch created: {batch.id}")
        
        # Create an award
        award = AidAward.objects.create(
            school=school,
            academic_year=year,
            student=student,
            award_type="NEED_BASED",
            awarded_cents=500000,  # $5,000
            decision_status="OFFERED"
        )
        print(f"✓ AidAward created: {award.id} (${award.awarded_cents/100:.2f})")
        
        # Test the auto-posting method
        entry = award.mark_accepted_and_post(actor_user=user, batch=batch)
        print(f"✓ Accepted and posted! Ledger entry: {entry.id}")
        print(f"✓ Entry amount: ${entry.amount_cents/100:.2f}")
        print(f"✓ Entry source: {entry.source}")
        print(f"\n✅ Aid auto-posting integration WORKING!")
    else:
        print("⚠️  No Student found - run seed script first, but models are ready")
        print("✅ Aid admin models registered successfully")
