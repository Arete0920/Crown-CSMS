from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from academics.models import (
    Assignment,
    AssignmentCategory,
    Course,
    Enrollment,
    Grade,
    Section,
    Submission,
    TeacherAssignment,
    Term,
)
from core.models import AcademicYear, Family, School, UserAccount
from households.models import Household, Student
from sandbox_demo.catalog import SANDBOX_PERSONAS
from sandbox_demo.services import seed_heritage_flagship


pytestmark = pytest.mark.django_db
SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d"
SESSION_URL = "/api/v1/sandbox/session/"
GRADES_URL = "/api/v1/academics/grades/"


def _sandbox_session(client: APIClient, role: str) -> dict:
    response = client.post(
        SESSION_URL,
        {
            "role": role,
            "school": "heritage-core",
            "track": "school",
            "guidance": "guided",
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    return response.json()


def _bearer_client(session: dict) -> APIClient:
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {session['access']}",
        HTTP_X_SCHOOL_ID=session["school_id"],
    )
    return client


def _seed_teacher_submission(school: School, teacher_user: UserAccount) -> Submission:
    academic_year = AcademicYear.objects.get(school=school, name="2026-2027")
    term, _ = Term.objects.get_or_create(
        school_id=school.id,
        academic_year=academic_year,
        code="SANDBOX-PROOF-TERM",
        defaults={
            "name": "Sandbox Proof Term",
            "school_year": academic_year.name,
            "active": True,
        },
    )
    course, _ = Course.objects.get_or_create(
        school_id=school.id,
        code="SANDBOX-PROOF-101",
        defaults={"name": "Sandbox Transaction Proof"},
    )
    section, _ = Section.objects.get_or_create(
        school_id=school.id,
        course=course,
        term=term.code,
        defaults={
            "term_ref": term,
            "teacher_name": "Eleanor Lower",
        },
    )
    TeacherAssignment.objects.get_or_create(
        school_id=school.id,
        section=section,
        staff=teacher_user.staff,
    )
    category, _ = AssignmentCategory.objects.get_or_create(
        school_id=school.id,
        section=section,
        name="Sandbox Proof",
        defaults={
            "weight_percent": "100.00",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assignment, _ = Assignment.objects.get_or_create(
        school_id=school.id,
        section=section,
        category=category,
        name="Transactional Proof Assignment",
        defaults={
            "points_possible": "100.00",
            "is_published": True,
        },
    )
    household, _ = Household.objects.get_or_create(
        school_id=school.id,
        name="Sandbox Transaction Proof Household",
    )
    student, _ = Student.objects.get_or_create(
        school_id=school.id,
        household=household,
        first_name="Sandbox",
        last_name="Learner",
        defaults={"grade_level": "5"},
    )
    enrollment, _ = Enrollment.objects.get_or_create(
        school_id=school.id,
        section=section,
        student=student,
    )
    submission, _ = Submission.objects.get_or_create(
        school_id=school.id,
        assignment=assignment,
        enrollment=enrollment,
    )
    return submission


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_all_advertised_personas_receive_real_role_aware_sandbox_sessions():
    seed_heritage_flagship(reset=True)
    client = APIClient()

    for role, persona in SANDBOX_PERSONAS.items():
        if role == "board":
            continue
        session = _sandbox_session(client, role)
        assert session["school_id"] == SCHOOL_ID
        assert session["role"] == role
        assert session["role_code"] == persona.role_code
        assert session["route"] == persona.route
        assert session["access"]
        assert session["refresh"]


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_flagship_reset_reseed_is_deterministic_after_mutation():
    baseline = seed_heritage_flagship(reset=True)
    school = School.objects.get(pk=SCHOOL_ID)
    Family.objects.create(
        school=school,
        family_name=f"Transient Proof Family {uuid.uuid4().hex[:8]}",
    )

    restored = seed_heritage_flagship(reset=True)
    repeated = seed_heritage_flagship(reset=True)

    assert restored == baseline
    assert repeated == baseline


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_teacher_sandbox_jwt_can_mutate_and_reload_grade_parent_cannot():
    seed_heritage_flagship(reset=True)
    session_client = APIClient()
    teacher_session = _sandbox_session(session_client, "teacher")
    parent_session = _sandbox_session(session_client, "parent")

    school = School.objects.get(pk=SCHOOL_ID)
    teacher_user = UserAccount.objects.get(
        school=school,
        username="teacher.lower@heritage.example.org",
    )
    assert teacher_user.staff_id is not None
    submission = _seed_teacher_submission(school, teacher_user)

    teacher_client = _bearer_client(teacher_session)
    response = teacher_client.post(
        f"{GRADES_URL}grade/",
        {
            "submission_id": str(submission.id),
            "numeric_score": "91.00",
            "teacher_feedback": "Sandbox transactional proof",
        },
        format="json",
    )
    assert response.status_code == 200, response.content

    grade = Grade.objects.get(submission=submission, school_id=school.id)
    assert grade.numeric_score == Decimal("91.00")
    assert grade.teacher_feedback == "Sandbox transactional proof"

    reload_response = teacher_client.get(
        GRADES_URL,
        {"submission_id": str(submission.id)},
    )
    assert reload_response.status_code == 200, reload_response.content
    payload = reload_response.json()
    rows = payload.get("results", payload) if isinstance(payload, dict) else payload
    assert any(
        str(row.get("submission_id")) == str(submission.id)
        and Decimal(str(row.get("numeric_score"))) == Decimal("91.00")
        for row in rows
    )

    parent_client = _bearer_client(parent_session)
    denied = parent_client.post(
        f"{GRADES_URL}grade/",
        {
            "submission_id": str(submission.id),
            "numeric_score": "100.00",
        },
        format="json",
    )
    assert denied.status_code == 403

    grade.refresh_from_db()
    assert grade.numeric_score == Decimal("91.00")


def test_teacher_sandbox_token_cannot_override_tenant_header():
    seed_heritage_flagship(reset=True)
    other_school = School.objects.create(name="Other Sandbox Isolation School")

    with override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True):
        session = _sandbox_session(APIClient(), "teacher")

    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {session['access']}",
        HTTP_X_SCHOOL_ID=str(other_school.id),
    )
    response = client.get(GRADES_URL)
    assert response.status_code in (403, 404)
