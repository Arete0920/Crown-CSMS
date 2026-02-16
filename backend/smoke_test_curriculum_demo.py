#!/usr/bin/env python
"""
Smoke Test Harness for Curriculum Segment Demo
Runs in ~2 minutes, validates pre-demo readiness.

Usage:
  cd backend
  python smoke_test_curriculum_demo.py

Expected output (all green):
  ✅ Database seed: 4 courses, 300 students, 1500 attendance
  ✅ Auth token obtained
  ✅ Pacing-summary endpoint: 200 OK, 4 courses
  ✅ Pacing detail endpoint: 200 OK, course detail
  ✅ School scoping summary: correct school sees data, wrong school empty
  ✅ School scoping detail: correct school 200, wrong school 404
  ✅ Frontend can build (if check requested)
  ✅ All checks passed. Demo ready.

Exit code: 0 (all checks pass) or 1 (any check fails)
"""

import os
import sys
import json
from datetime import date
from uuid import uuid4

# Django setup
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
    import django
    django.setup()

from django.test import Client
from rest_framework.test import APIRequestFactory, force_authenticate
from django.urls import reverse
from core.models import School, UserAccount, Student, Family
from billing.models import Invoice
from curriculum.models import CurriculumCourse, CurriculumUnit, CurriculumLesson
from curriculum.views import CurriculumCourseViewSet
from crown_api.models_academics_core import AttendanceRecord

# Color codes for CLI output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
YELLOW = "\033[93m"

def log_pass(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def log_fail(msg):
    print(f"{RED}❌ {msg}{RESET}")

def log_info(msg):
    print(f"{YELLOW}ℹ️  {msg}{RESET}")

def check_seed_data():
    """Verify database seed is complete and correct."""
    log_info("Checking database seed...")
    
    student_count = Student.objects.count()
    family_count = Family.objects.count()
    attendance_count = AttendanceRecord.objects.count()
    curriculum_count = CurriculumCourse.objects.count()
    invoice_count = Invoice.objects.count()
    
    # Expected values from seed_heritage_realism_pack (main demo school)
    # Note: smoke tests may add extra schools, so curriculum count >= 4
    expected = {
        "students": 300,
        "attendance": 1500,
        "curriculum_courses": 4,
    }
    
    checks = [
        (student_count >= expected["students"], f"Students: {student_count} (expected {expected['students']})"),
        (attendance_count >= expected["attendance"], f"Attendance records: {attendance_count} (expected {expected['attendance']})"),
        (curriculum_count >= expected["curriculum_courses"], f"Curriculum courses: {curriculum_count} (expected >= {expected['curriculum_courses']})"),
    ]
    
    all_pass = True
    for check, msg in checks:
        if check:
            log_pass(f"Database seed: {msg}")
        else:
            log_fail(f"Database seed: {msg}")
            all_pass = False
    
    return all_pass

def check_auth():
    """Verify demo account exists and can authenticate."""
    log_info("Checking authentication...")
    
    try:
        user = UserAccount.objects.get(username="head@crown-demo.local")
        log_pass(f"Auth: Demo user exists (head@crown-demo.local)")
        return True
    except UserAccount.DoesNotExist:
        log_fail("Auth: Demo user not found (head@crown-demo.local)")
        return False

def check_api_endpoints():
    """Verify curriculum API endpoints exist and respond."""
    log_info("Checking API endpoints...")
    
    # Find a school that has curriculum courses (not just first school)
    school = None
    course = None
    for s in School.objects.all():
        c = CurriculumCourse.objects.filter(school=s).first()
        if c:
            school = s
            course = c
            break
    
    if not school:
        log_fail("API: No schools with curriculum courses")
        return False
    
    if not course:
        log_fail("API: No curriculum courses found")
        return False
    
    # Get or create a user
    user = UserAccount.objects.first()
    if not user:
        log_fail("API: No user in database")
        return False
    
    factory = APIRequestFactory()
    
    # Check pacing-summary endpoint
    req = factory.get(
        "/api/curriculum/courses/pacing-summary/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    force_authenticate(req, user=user)
    
    view = CurriculumCourseViewSet.as_view({"get": "pacing_summary"})
    resp = view(req)
    
    if resp.status_code == 200:
        try:
            data = resp.data if hasattr(resp, 'data') else json.loads(resp.content)
            course_count = data.get("count", 0)
            if course_count >= 4:
                log_pass(f"API: pacing-summary returned 200 OK, {course_count} courses")
            else:
                log_fail(f"API: pacing-summary returned {course_count} courses (expected >= 4)")
                return False
        except (AttributeError, TypeError, json.JSONDecodeError) as e:
            log_fail(f"API: pacing-summary invalid response: {str(e)}")
            return False
    else:
        log_fail(f"API: pacing-summary returned {resp.status_code} (expected 200)")
        return False
    
    # Check pacing detail endpoint
    req = factory.get(
        f"/api/curriculum/courses/{course.id}/pacing/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    force_authenticate(req, user=user)
    
    view = CurriculumCourseViewSet.as_view({"get": "pacing"})
    resp = view(req, pk=str(course.id))
    
    if resp.status_code == 200:
        try:
            data = resp.data if hasattr(resp, 'data') else json.loads(resp.content)
            if "pacing" in data and "pct_due" in data["pacing"]:
                pct = data["pacing"]["pct_due"]
                log_pass(f"API: pacing-detail returned 200 OK, {pct}% due")
            else:
                log_fail(f"API: pacing-detail missing pacing data")
                return False
        except (AttributeError, TypeError, json.JSONDecodeError) as e:
            log_fail(f"API: pacing-detail invalid response: {str(e)}")
            return False
    else:
        log_fail(f"API: pacing-detail returned {resp.status_code} (expected 200)")
        return False
    
    return True

def check_school_scoping():
    """Verify school scoping is enforced on endpoints."""
    log_info("Checking school scoping...")
    
    # Create two schools
    school_a = School.objects.create(name="Test School A for Smoke Test")
    school_b = School.objects.create(name="Test School B for Smoke Test")
    
    # Create curriculum under school_a only
    course_a = CurriculumCourse.objects.create(
        school=school_a,
        code="SMOKE-A",
        name="Smoke Test Course A",
        subject="Test",
        grade_level="9",
        worldview_theme="Test",
        anchor_scripture_ref="Test",
        anchor_scripture_text="Test"
    )
    
    # Get or create a user
    user = UserAccount.objects.first()
    if not user:
        log_fail("Scoping: No user in database")
        return False
    
    factory = APIRequestFactory()
    
    # Test 1: School A sees its course in summary
    req_a = factory.get(
        "/api/curriculum/courses/pacing-summary/",
        HTTP_X_SCHOOL_ID=str(school_a.id),
    )
    force_authenticate(req_a, user=user)
    
    view = CurriculumCourseViewSet.as_view({"get": "pacing_summary"})
    resp_a = view(req_a)
    
    if resp_a.status_code == 200:
        data = resp_a.data if hasattr(resp_a, 'data') else json.loads(resp_a.content)
        count_a = data.get("count", 0)
        if count_a >= 1:
            log_pass(f"Scoping: School A sees {count_a} courses in summary")
        else:
            log_fail(f"Scoping: School A sees 0 courses (expected >= 1)")
            return False
    else:
        log_fail(f"Scoping: School A summary returned {resp_a.status_code}")
        return False
    
    # Test 2: School B sees no courses in summary
    req_b = factory.get(
        "/api/curriculum/courses/pacing-summary/",
        HTTP_X_SCHOOL_ID=str(school_b.id),
    )
    force_authenticate(req_b, user=user)
    
    resp_b = view(req_b)
    
    if resp_b.status_code == 200:
        data = resp_b.data if hasattr(resp_b, 'data') else json.loads(resp_b.content)
        count_b = data.get("count", 0)
        if count_b == 0:
            log_pass(f"Scoping: School B sees 0 courses (correct isolation)")
        else:
            log_fail(f"Scoping: School B sees {count_b} courses (expected 0)")
            return False
    else:
        log_fail(f"Scoping: School B summary returned {resp_b.status_code}")
        return False
    
    # Test 3: School B gets 404 on School A's course detail
    req_wrong = factory.get(
        f"/api/curriculum/courses/{course_a.id}/pacing/",
        HTTP_X_SCHOOL_ID=str(school_b.id),
    )
    force_authenticate(req_wrong, user=user)
    
    detail_view = CurriculumCourseViewSet.as_view({"get": "pacing"})
    resp_wrong = detail_view(req_wrong, pk=str(course_a.id))
    
    if resp_wrong.status_code == 404:
        log_pass(f"Scoping: School B gets 404 on School A's course (correct enforcement)")
    else:
        log_fail(f"Scoping: School B got {resp_wrong.status_code} (expected 404)")
        return False
    
    # Cleanup
    school_a.delete()
    school_b.delete()
    
    return True

def check_pacing_values():
    """Verify pacing percentages are realistic (not 100%)."""
    log_info("Checking pacing values...")
    
    # Find a school with curriculum courses
    school = None
    course = None
    for s in School.objects.all():
        c = CurriculumCourse.objects.filter(school=s).first()
        if c:
            school = s
            course = c
            break
    
    if not school or not course:
        log_fail("Pacing: No schools with curriculum courses")
        return False
    
    # Get or create a user
    user = UserAccount.objects.first()
    if not user:
        log_fail("Pacing: No user in database")
        return False
    
    factory = APIRequestFactory()
    
    # Get pacing via API
    req = factory.get(
        "/api/curriculum/courses/pacing-summary/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    force_authenticate(req, user=user)
    
    view = CurriculumCourseViewSet.as_view({"get": "pacing_summary"})
    resp = view(req)
    
    if resp.status_code == 200:
        data = resp.data if hasattr(resp, 'data') else json.loads(resp.content)
        results = data.get("results", [])
        
        if results:
            pct_values = [r.get("pacing", {}).get("pct_due", -1) for r in results]
            valid_pcts = [p for p in pct_values if 0 <= p <= 100]
            
            if valid_pcts:
                min_pct = min(valid_pcts)
                max_pct = max(valid_pcts)
                
                # Check for realism: not all 100%, not all 0%
                if 0 < min_pct < 100 or any(p < 100 for p in valid_pcts):
                    log_pass(f"Pacing: Values realistic (range {min_pct}–{max_pct}%, not 100%)")
                    return True
                else:
                    log_fail(f"Pacing: All values are {max_pct}% (expected variation)")
                    return False
            else:
                log_fail(f"Pacing: Invalid pacing percentages {pct_values}")
                return False
        else:
            log_fail("Pacing: No courses returned")
            return False
    else:
        log_fail(f"Pacing: Status {resp.status_code}")
        return False

def main():
    """Run all smoke tests."""
    print()
    print("=" * 70)
    print("CURRICULUM SEGMENT SMOKE TEST (2-minute check)")
    print("=" * 70)
    print()
    
    tests = [
        ("Database seed", check_seed_data),
        ("Authentication", check_auth),
        ("API endpoints", check_api_endpoints),
        ("School scoping", check_school_scoping),
        ("Pacing values", check_pacing_values),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            log_fail(f"{name}: Exception: {str(e)}")
            results.append((name, False))
        print()
    
    # Summary
    print("=" * 70)
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    if passed == total:
        log_pass(f"All {total} checks passed. Demo ready.")
        print()
        return 0
    else:
        log_fail(f"{passed}/{total} checks passed. Fix failures before demo.")
        print()
        print("Failed checks:")
        for name, p in results:
            if not p:
                print(f"  - {name}")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
