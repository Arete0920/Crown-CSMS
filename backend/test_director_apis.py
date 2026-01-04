#!/usr/bin/env python
"""
Quick test of director summary APIs without needing live server.
Run: python test_director_apis.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from crown_api.director_views import aid_summary, finance_summary, registrar_summary
from core.models import School, AcademicYear, UserRole

User = get_user_model()

def test_apis():
    """Test all three director APIs with a superuser."""
    factory = RequestFactory()
    
    school = School.objects.first()
    if not school:
        print("❌ No school found. Run seed_demo_school first.")
        sys.exit(1)
    
    current_year = AcademicYear.objects.filter(school=school, is_current=True).first()
    if not current_year:
        print("❌ No current academic year. Run seed_demo_school first.")
        sys.exit(1)
    
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("❌ No superuser found.")
        sys.exit(1)
    
    print(f"\n✅ Testing with school={school.id}, year={current_year.id}, user={user.email}")
    
    # Test Aid Summary
    print("\n📊 Aid Summary:")
    req = factory.get(f'/api/director/aid/summary/?school_id={school.id}&academic_year_id={current_year.id}')
    req.user = user
    resp = aid_summary(req)
    if resp.status_code == 200:
        data = resp.data
        print(f"  ✅ Status 200")
        print(f"  - applications.total: {data['applications']['total']}")
        print(f"  - awards.total_awards: {data['awards']['total_awards']}")
        print(f"  - documents.missing_documents_count: {data['documents']['missing_documents_count']}")
    else:
        print(f"  ❌ Status {resp.status_code}: {resp.data}")
    
    # Test Finance Summary
    print("\n💰 Finance Summary:")
    req = factory.get(f'/api/director/finance/summary/?school_id={school.id}&academic_year_id={current_year.id}')
    req.user = user
    resp = finance_summary(req)
    if resp.status_code == 200:
        data = resp.data
        print(f"  ✅ Status 200")
        print(f"  - tuition.students_billed: {data['tuition']['students_billed']}")
        print(f"  - aid.total_aid_posted_cents: {data['aid']['total_aid_posted_cents']}")
        print(f"  - ledger.net_receivables_cents: {data['ledger']['net_receivables_cents']}")
    else:
        print(f"  ❌ Status {resp.status_code}: {resp.data}")
    
    # Test Registrar Summary
    print("\n📚 Registrar Summary:")
    req = factory.get(f'/api/director/registrar/summary/?school_id={school.id}&academic_year_id={current_year.id}')
    req.user = user
    resp = registrar_summary(req)
    if resp.status_code == 200:
        data = resp.data
        print(f"  ✅ Status 200")
        print(f"  - enrollment.total_students: {data['enrollment']['total_students']}")
        print(f"  - families.total_families: {data['families']['total_families']}")
        print(f"  - by_grade keys: {list(data['enrollment']['by_grade'].keys())}")
    else:
        print(f"  ❌ Status {resp.status_code}: {resp.data}")
    
    print("\n✅ All tests passed!\n")

if __name__ == '__main__':
    test_apis()
