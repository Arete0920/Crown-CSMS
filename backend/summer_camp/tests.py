from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import School
from households.models import Household, Student

from .models import (
    SummerCampEnrollment,
    SummerCampPickupContact,
    SummerCampProgram,
    SummerCampSession,
)
from .services import compute_camper_readiness, enroll_camper, ensure_config


pytestmark = pytest.mark.django_db


@pytest.fixture
def school():
    return School.objects.create(name="Summer School")


@pytest.fixture
def staff_user(school):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="summer-staff",
        email="summer-staff@example.com",
        password=None,
        is_staff=True,
        school=school,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])
    return user


@pytest.fixture
def basic_user(school):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="summer-basic",
        email="summer-basic@example.com",
        password=None,
        is_staff=False,
        school=school,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])
    return user


@pytest.fixture
def household_student(school):
    household = Household.objects.create(school_id=school.id, name="Camp Family")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Camper",
        last_name="One",
        grade_level="5",
    )
    return household, student


@pytest.fixture
def session(school):
    program = SummerCampProgram.objects.create(
        school=school,
        name="STEM Camp",
        program_type="STEM",
        grade_band="3-6",
        location="Building A",
    )
    today = timezone.now().date()
    return SummerCampSession.objects.create(
        school=school,
        program=program,
        name="Week 1",
        start_date=today,
        end_date=today + timedelta(days=4),
        start_time=timezone.datetime(2026, 1, 1, 8, 0).time(),
        end_time=timezone.datetime(2026, 1, 1, 15, 0).time(),
        capacity=1,
        waitlist_capacity=10,
        price_cents=30000,
        deposit_cents=5000,
        status="PUBLISHED",
    )


def _client(user, school):
    client = APIClient()
    client.force_authenticate(user=user)
    client.defaults["HTTP_X_SCHOOL_ID"] = str(school.id)
    return client


def test_enroll_camper_waitlist_logic(school, household_student, session):
    _, student = household_student

    e1 = enroll_camper(
        school_id=school.id,
        student_id=student.id,
        session_id=session.id,
        payload={
            "household_id": student.household_id,
            "form_status": "COMPLETE",
            "payment_status": "PAID_IN_FULL",
            "health_status": "APPROVED",
            "pickup_status": "ACTIVE",
            "balance_due_cents": 0,
        },
    )
    assert e1.status == "REGISTERED"

    student2 = Student.objects.create(
        school_id=school.id,
        household=student.household,
        first_name="Camper",
        last_name="Two",
        grade_level="5",
    )
    e2 = enroll_camper(
        school_id=school.id,
        student_id=student2.id,
        session_id=session.id,
        payload={
            "household_id": student2.household_id,
            "form_status": "MISSING",
            "payment_status": "DEPOSIT_DUE",
            "health_status": "NEEDS_REVIEW",
            "pickup_status": "MISSING",
            "balance_due_cents": 100,
        },
    )
    assert e2.status == "WAITLISTED"
    assert e2.waitlist_position == 1


def test_compute_readiness_ready_after_pickup(school, household_student, session):
    _, student = household_student
    enrollment = SummerCampEnrollment.objects.create(
        school=school,
        session=session,
        student=student,
        household_id=student.household_id,
        status="REGISTERED",
        form_status="COMPLETE",
        payment_status="PAID_IN_FULL",
        health_status="APPROVED",
        pickup_status="ACTIVE",
        balance_due_cents=0,
    )

    SummerCampPickupContact.objects.create(
        school=school,
        enrollment=enrollment,
        name="Parent",
        relationship="Parent",
        phone="555-0100",
        is_active=True,
    )

    result = compute_camper_readiness(school.id, enrollment.id)
    assert result["status"] in {"READY", "BLOCKED"}
    if result["status"] == "READY":
        assert result["blockers"] == []


def test_api_contract_core_endpoints(staff_user, school, session, household_student):
    household, student = household_student
    client = _client(staff_user, school)

    config_resp = client.get("/api/v1/summer-camp/config/")
    assert config_resp.status_code == 200

    sessions_resp = client.get("/api/v1/summer-camp/sessions/")
    assert sessions_resp.status_code == 200

    create_enrollment_resp = client.post(
        "/api/v1/summer-camp/enrollments/",
        {
            "session_id": str(session.id),
            "student_id": str(student.id),
            "household_id": str(household.id),
            "registration_source": "EXISTING",
            "form_status": "MISSING",
            "payment_status": "DEPOSIT_DUE",
            "health_status": "NEEDS_REVIEW",
            "pickup_status": "MISSING",
            "balance_due_cents": 10000,
        },
        format="json",
    )
    assert create_enrollment_resp.status_code == 201, create_enrollment_resp.json()

    roster_resp = client.get(f"/api/v1/summer-camp/sessions/{session.id}/roster/")
    assert roster_resp.status_code == 200

    today_roster_resp = client.get("/api/v1/summer-camp/roster/today/")
    assert today_roster_resp.status_code == 200

    checkin_resp = client.post(
        "/api/v1/summer-camp/attendance/checkin/",
        {"session_id": str(session.id), "student_id": str(student.id)},
        format="json",
    )
    assert checkin_resp.status_code == 201

    checkout_resp = client.post(
        "/api/v1/summer-camp/attendance/checkout/",
        {"session_id": str(session.id), "student_id": str(student.id), "pickup_verified": True},
        format="json",
    )
    assert checkout_resp.status_code == 200

    incident_resp = client.post(
        "/api/v1/summer-camp/incidents/",
        {
            "session_id": str(session.id),
            "student_id": str(student.id),
            "severity": "LOW",
            "category": "Behavior",
            "description": "Minor incident",
        },
        format="json",
    )
    assert incident_resp.status_code == 201

    missing_forms_resp = client.get("/api/v1/summer-camp/forms/missing/")
    assert missing_forms_resp.status_code == 200

    parent_resp = client.get(f"/api/v1/summer-camp/parent/{student.id}/")
    assert parent_resp.status_code == 200

    board_resp = client.get("/api/v1/summer-camp/board/summary/")
    assert board_resp.status_code == 200


def test_api_forbidden_for_nonstaff_without_permissions(basic_user, school):
    client = _client(basic_user, school)

    board_resp = client.get("/api/v1/summer-camp/board/summary/")
    assert board_resp.status_code == 403

    enrollments_resp = client.get("/api/v1/summer-camp/enrollments/")
    assert enrollments_resp.status_code == 403


def test_wizard_setup_get_and_post(staff_user, school):
    client = _client(staff_user, school)

    get_resp = client.get("/api/v1/summer-camp/wizard/setup/")
    assert get_resp.status_code == 200

    post_resp = client.post(
        "/api/v1/summer-camp/wizard/setup/",
        {
            "camp_name": "Summer Test Program",
            "season_year": 2026,
            "season_label": "Summer",
            "allow_waitlist": True,
        },
        format="json",
    )
    assert post_resp.status_code == 200
