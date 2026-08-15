from datetime import date, timedelta
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Family, School, Student as CoreStudent, StudentIdentityLink
from crown_api.models import AttendanceRecord
from households.models import Household, Student as HouseholdStudent


pytestmark = pytest.mark.django_db


def _mk_user(*, school: School, email: str, first_name: str = "", last_name: str = ""):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"student360-{uuid.uuid4()}",
        email=email,
        password="pass12345!",
        first_name=first_name,
        last_name=last_name,
        is_staff=True,
    )
    if hasattr(user, "school_id"):
        user.school = school
        user.save(update_fields=["school"])
    return user


def _mk_identity_pair(*, school: School, account=None, status=StudentIdentityLink.STATUS_VERIFIED):
    household = Household.objects.create(school_id=school.id, name=f"Identity Household {uuid.uuid4().hex[:6]}")
    compatibility_student = HouseholdStudent.objects.create(
        school_id=school.id,
        household=household,
        account=account,
        first_name="Harper",
        last_name="Stone",
        grade_level="9",
    )
    family = Family.objects.create(school=school, family_name=f"Identity Family {uuid.uuid4().hex[:6]}")
    core_student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number=f"S-360-{uuid.uuid4().hex[:8]}",
        first_name="Harper",
        last_name="Canonical",
        dob=date(2011, 5, 14),
        status="ACTIVE",
    )
    link = StudentIdentityLink.objects.create(
        school=school,
        core_student=core_student,
        compatibility_student=compatibility_student,
        source=StudentIdentityLink.SOURCE_RECONCILIATION,
        verification_status=status,
        evidence_reference=("student360-test-evidence" if status == StudentIdentityLink.STATUS_VERIFIED else ""),
    )
    return compatibility_student, core_student, link


def test_student_overview_returns_200_for_core_student():
    school = School.objects.create(name="Student360 Overview School")
    family = Family.objects.create(school=school, family_name="Overview Family")
    student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number="S-360-001",
        first_name="Casey",
        last_name="Core",
        dob=date(2012, 1, 1),
        status="ACTIVE",
    )
    user = _mk_user(school=school, email="overview@test.local")

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        f"/api/v1/360/students/{student.id}/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    assert response.json()["student"]["id"] == str(student.id)


def test_student_overview_reads_canonical_attendance_statuses():
    school = School.objects.create(name="Student360 Attendance School")
    family = Family.objects.create(school=school, family_name="Attendance Family")
    student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number="S-360-ATT",
        first_name="Casey",
        last_name="Attendance",
        dob=date(2012, 1, 1),
        status="ACTIVE",
    )
    today = timezone.now().date()
    AttendanceRecord.objects.create(student=student, date=today, status=AttendanceRecord.STATUS_PRESENT)
    AttendanceRecord.objects.create(student=student, date=today - timedelta(days=1), status=AttendanceRecord.STATUS_ABSENT)
    user = _mk_user(school=school, email="attendance@test.local")

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(
        f"/api/v1/360/students/{student.id}/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    attendance = response.json()["attendance"]
    assert attendance["available"] is True
    assert attendance["last30_total"] == 2
    assert attendance["last30_present"] == 1
    assert attendance["last30_pct"] == 50.0
    assert response.json()["dashboard_v2"]["attendance"] == attendance


def test_student_self_overview_requires_linked_households_student_profile():
    school = School.objects.create(name="Student360 Self School")
    household = Household.objects.create(school_id=school.id, name="Stone Household")
    user = _mk_user(
        school=school,
        email="harper.stone@test.local",
        first_name="Harper",
        last_name="Stone",
    )
    student = HouseholdStudent.objects.create(
        school_id=school.id,
        household=household,
        account=user,
        first_name="Harper",
        last_name="Stone",
        grade_level="9",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        "/api/v1/360/me/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    assert response.json()["student"]["id"] == str(student.id)
    assert response.json()["student"]["name"] == "Harper Stone"
    assert response.json()["attendance"] == {"available": False}


def test_student_self_overview_uses_verified_identity_link_for_canonical_output():
    school = School.objects.create(name="Student360 Verified Bridge School")
    user = _mk_user(
        school=school,
        email="verified.bridge@test.local",
        first_name="Harper",
        last_name="Stone",
    )
    compatibility_student, core_student, _ = _mk_identity_pair(school=school, account=user)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        "/api/v1/360/me/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    assert response.json()["student"]["id"] == str(core_student.id)
    assert response.json()["student"]["id"] != str(compatibility_student.id)
    assert response.json()["student"]["name"] == "Harper Canonical"


def test_student_overview_compatibility_id_uses_verified_identity_link_for_staff():
    school = School.objects.create(name="Student360 Staff Bridge School")
    user = _mk_user(school=school, email="staff.bridge@test.local")
    compatibility_student, core_student, _ = _mk_identity_pair(school=school)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        f"/api/v1/360/students/{compatibility_student.id}/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    assert response.json()["student"]["id"] == str(core_student.id)


def test_student_self_overview_pending_identity_link_stays_on_compatibility_identity():
    school = School.objects.create(name="Student360 Pending Bridge School")
    user = _mk_user(
        school=school,
        email="pending.bridge@test.local",
        first_name="Harper",
        last_name="Stone",
    )
    compatibility_student, core_student, _ = _mk_identity_pair(
        school=school,
        account=user,
        status=StudentIdentityLink.STATUS_PENDING,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        "/api/v1/360/me/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    assert response.json()["student"]["id"] == str(compatibility_student.id)
    assert response.json()["student"]["id"] != str(core_student.id)
    assert response.json()["attendance"] == {"available": False}


def test_student_self_overview_does_not_promote_same_name_without_verified_link():
    school = School.objects.create(name="Student360 No Guess School")
    user = _mk_user(
        school=school,
        email="no.guess@test.local",
        first_name="Harper",
        last_name="Stone",
    )
    household = Household.objects.create(school_id=school.id, name="No Guess Household")
    compatibility_student = HouseholdStudent.objects.create(
        school_id=school.id,
        household=household,
        account=user,
        first_name="Harper",
        last_name="Stone",
        grade_level="9",
    )
    family = Family.objects.create(school=school, family_name="No Guess Family")
    same_name_core_student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number="S-360-NOGUESS",
        first_name="Harper",
        last_name="Stone",
        dob=date(2011, 5, 14),
        status="ACTIVE",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        "/api/v1/360/me/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    assert response.json()["student"]["id"] == str(compatibility_student.id)
    assert response.json()["student"]["id"] != str(same_name_core_student.id)


def test_student_self_overview_fails_closed_on_cross_school_corrupted_link():
    school = School.objects.create(name="Student360 Link School A")
    other_school = School.objects.create(name="Student360 Link School B")
    user = _mk_user(
        school=school,
        email="corrupt.bridge@test.local",
        first_name="Harper",
        last_name="Stone",
    )
    compatibility_student, _, link = _mk_identity_pair(school=school, account=user)

    other_family = Family.objects.create(school=other_school, family_name="Other Family")
    other_core_student = CoreStudent.objects.create(
        school=other_school,
        family=other_family,
        student_number="S-360-OTHER",
        first_name="Harper",
        last_name="Other",
        dob=date(2011, 5, 14),
        status="ACTIVE",
    )
    StudentIdentityLink.objects.filter(pk=link.pk).update(core_student=other_core_student)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        "/api/v1/360/me/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200, response.content
    assert response.json()["student"]["id"] == str(compatibility_student.id)
    assert response.json()["student"]["id"] != str(other_core_student.id)
