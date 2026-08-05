import uuid
from datetime import date
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.models import (
    AcademicYear,
    Family,
    GradeLevel,
    Guardian,
    School,
    Staff,
    Student,
    UserRole,
)
from crown_api.admissions_runtime import admissions_summary
from crown_api.dashboards.payload_contract import build_dashboard_payload, metric
from crown_api.dashboards.views import DASHBOARD_PAYLOAD_BUILDERS, _sample_dashboard_payloads_allowed
from crown_api.models_households import (
    Person,
    Student as IdentityStudent,
)
from crown_api.models_identity import UserPersonLink
from finance.models import FinanceInvoice, MoneyStatus
from sandbox_demo.catalog import DEMO_SCHOOL_ID, SANDBOX_PERSONAS


User = get_user_model()


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _create_user(*, school, username, role_code, first_name="", last_name="", staff=None, guardian=None):
    user = User.objects.create_user(
        username=username,
        email=username,
        first_name=first_name,
        last_name=last_name,
        school=school,
        staff=staff,
        guardian=guardian,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])
    UserRole.objects.create(school=school, user=user, role_code=role_code)
    return user


def _get_metric(payload, label):
    return next(item for item in payload["metrics"] if item["label"] == label)["value"]


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_teacher_dashboard_returns_live_tenant_scoped_identity_summary():
    school = School.objects.create(name="Teacher Persona School")
    other_school = School.objects.create(name="Other School")
    AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 5),
        is_current=True,
    )
    family = Family.objects.create(school=school, family_name="Teacher Test Family")
    other_family = Family.objects.create(school=other_school, family_name="Other Family")
    Student.objects.create(
        school=school,
        family=family,
        student_number="T-001",
        first_name="One",
        last_name="Student",
        dob=date(2012, 1, 1),
        status="ACTIVE",
    )
    Student.objects.create(
        school=other_school,
        family=other_family,
        student_number="O-001",
        first_name="Other",
        last_name="Student",
        dob=date(2012, 1, 1),
        status="ACTIVE",
    )
    staff = Staff.objects.create(
        school=school,
        first_name="Eleanor",
        last_name="Lower",
        email="teacher@example.org",
        role_type="TEACHER",
        status="ACTIVE",
    )
    user = _create_user(
        school=school,
        username="teacher@example.org",
        role_code="TEACHER",
        first_name="Eleanor",
        last_name="Lower",
        staff=staff,
    )

    response = _client_for(user).get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "teacher"}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["served_from"] == "live_db"
    assert payload["meta"]["school_id"] == str(school.id)
    assert _get_metric(payload, "Active staff profile") == "Yes"
    assert _get_metric(payload, "Active students at school") == "1"
    assert _get_metric(payload, "Current academic year") == "2026-2027"


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_parent_dashboard_returns_only_current_guardian_family_and_invoices():
    school = School.objects.create(name="Parent Persona School")
    family = Family.objects.create(school=school, family_name="Reed Family")
    guardian = Guardian.objects.create(
        school=school,
        family=family,
        first_name="Miriam",
        last_name="Reed",
        email="parent@example.org",
        relationship="MOTHER",
        portal_access=True,
    )
    grade = GradeLevel.objects.create(school=school, code="6", label="Grade 6", sort_order=7)
    Student.objects.create(
        school=school,
        family=family,
        student_number="P-001",
        first_name="Avery",
        last_name="Reed",
        dob=date(2013, 1, 1),
        status="ACTIVE",
        current_grade_level=grade,
    )
    user = _create_user(
        school=school,
        username="parent@example.org",
        role_code="PARENT",
        first_name="Miriam",
        last_name="Reed",
        guardian=guardian,
    )
    FinanceInvoice.objects.create(
        school=school,
        payer_user=user,
        status=MoneyStatus.OPEN,
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        due_date=date(2026, 8, 15),
        subtotal_cents=12500,
        total_cents=12500,
    )
    FinanceInvoice.objects.create(
        school=school,
        payer_user=user,
        status=MoneyStatus.OPEN,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        due_date=date(2026, 9, 15),
        subtotal_cents=8750,
        total_cents=8750,
    )

    response = _client_for(user).get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "parent"}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["served_from"] == "live_db"
    assert payload["meta"]["family_id"] == str(family.id)
    assert _get_metric(payload, "Guardian portal access") == "Active"
    assert _get_metric(payload, "Linked active students") == "1"
    assert _get_metric(payload, "Open invoices") == "2"
    assert _get_metric(payload, "Outstanding family balance") == "$212.50"


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_student_dashboard_uses_canonical_user_person_link():
    school = School.objects.create(name="Student Persona School")
    user = _create_user(
        school=school,
        username="student@example.org",
        role_code="STUDENT",
        first_name="Avery",
        last_name="Reed",
    )
    person = Person.objects.create(
        first_name="Avery",
        last_name="Reed",
        email="student@example.org",
    )
    identity_student = IdentityStudent.objects.create(
        person=person,
        grade_level="11",
        active=True,
    )
    person_link = UserPersonLink.objects.create(user=user, person=person)

    response = _client_for(user).get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "student"}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["served_from"] == "live_db"
    assert payload["meta"]["person_link_id"] == str(person_link.id)
    assert payload["meta"]["identity_student_id"] == str(identity_student.id)
    assert _get_metric(payload, "Student profile") == "Linked"
    assert _get_metric(payload, "Current grade") == "11"
    assert _get_metric(payload, "Student status") == "ACTIVE"


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_student_dashboard_does_not_guess_identity_from_matching_name():
    school = School.objects.create(name="Student Identity Guard School")
    family = Family.objects.create(school=school, family_name="Reed Family")
    Student.objects.create(
        school=school,
        family=family,
        student_number="S-UNLINKED",
        first_name="Avery",
        last_name="Reed",
        dob=date(2009, 1, 1),
        status="ACTIVE",
    )
    user = _create_user(
        school=school,
        username="unlinked-student@example.org",
        role_code="STUDENT",
        first_name="Avery",
        last_name="Reed",
    )

    response = _client_for(user).get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "student"}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["person_link_id"] is None
    assert payload["meta"]["identity_student_id"] is None
    assert _get_metric(payload, "Student profile") == "Not linked"
    assert _get_metric(payload, "Current grade") == "Not linked"


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_persona_dashboard_rejects_wrong_role():
    school = School.objects.create(name="Wrong Role School")
    user = _create_user(
        school=school,
        username="parent-wrong-role@example.org",
        role_code="PARENT",
    )

    response = _client_for(user).get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "teacher"}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_persona_dashboard_rejects_cross_tenant_access():
    school = School.objects.create(name="Persona Home School")
    other_school = School.objects.create(name="Persona Other School")
    user = _create_user(
        school=school,
        username="teacher-cross-tenant@example.org",
        role_code="TEACHER",
    )

    response = _client_for(user).get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "teacher"}),
        HTTP_X_SCHOOL_ID=str(other_school.id),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint,source",
    [
        ("/api/dashboards/me/", "core_identity"),
        ("/api/dashboards/summary/", "dashboard_service"),
        ("/api/dashboards/drilldown/?widget=alerts_flip", "dashboard_service"),
        ("/api/dashboards/alerts/", "dashboard_service"),
    ],
)
def test_canonical_dashboard_endpoints_report_live_provenance(endpoint, source):
    school = School.objects.create(name=f"Live Provenance {source}")
    user = User.objects.create_user(
        username=f"live-{source}-{school.id}",
        school=school,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(endpoint, HTTP_X_SCHOOL_ID=str(school.id))

    assert response.status_code == 200
    meta = response.json()["meta"]
    assert meta["served_from"] == "live"
    assert meta["source"] == source
    assert meta["school_id"] == str(school.id)


def test_successful_admissions_summary_adds_live_database_provenance():
    request = RequestFactory().get("/api/v1/admissions/summary/")
    with patch("crown_api.admissions_runtime.canonical_admissions_summary") as canonical_summary:
        canonical_summary.return_value = Response({"pipeline": {"total": 0}}, status=200)

        response = admissions_summary(request)

    assert response.status_code == 200
    assert response.data["meta"] == {
        "served_from": "live_db",
        "source": "applications",
    }
    canonical_summary.assert_called_once_with(request)


def test_failed_admissions_summary_does_not_claim_live_provenance():
    request = RequestFactory().get("/api/v1/admissions/summary/")
    with patch("crown_api.admissions_runtime.canonical_admissions_summary") as canonical_summary:
        canonical_summary.return_value = Response({"detail": "Forbidden."}, status=403)

        response = admissions_summary(request)

    assert response.status_code == 403
    assert "meta" not in response.data


@pytest.mark.django_db
def test_heritage_student_persona_receives_canonical_person_link():
    school = School.objects.create(
        id=uuid.UUID(DEMO_SCHOOL_ID),
        name="Heritage Student Identity Test",
    )
    persona = SANDBOX_PERSONAS["student"]

    user = User.objects.create_user(
        username=persona.email,
        email=persona.email,
        first_name=persona.first_name,
        last_name=persona.last_name,
        school=school,
    )

    link = UserPersonLink.objects.select_related("person").get(user=user)
    identity_student = IdentityStudent.objects.get(person=link.person)
    assert link.person.email == persona.email
    assert identity_student.grade_level == "11"
    assert identity_student.active is True


@pytest.mark.django_db
def test_non_sandbox_student_account_is_not_auto_linked():
    school = School.objects.create(name="Non Sandbox Identity Test")
    user = User.objects.create_user(
        username="non-sandbox-student@example.org",
        email="non-sandbox-student@example.org",
        school=school,
    )

    assert not UserPersonLink.objects.filter(user=user).exists()


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_school_board_summary_serves_verified_live_builder_in_production():
    school = School.objects.create(name="Board Live School")
    user = User.objects.create_user(username="board-live-dashboard-test", school=school)
    user.set_unusable_password()
    user.save(update_fields=["password"])

    def live_builder(school_id):
        return build_dashboard_payload(
            dashboard_key="school-board",
            metrics=[metric("Current enrollment", 42)],
            alerts=[],
            queue=[],
            meta={"school_id": str(school_id), "served_from": "live_db"},
        )

    with patch.dict(DASHBOARD_PAYLOAD_BUILDERS, {"school-board": live_builder}):
        response = _client_for(user).get(
            reverse("dashboard-summary", kwargs={"dashboard_key": "school-board"}),
            HTTP_X_SCHOOL_ID=str(school.id),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["served_from"] == "live_db"
    assert data["meta"]["school_id"] == str(school.id)
    assert data["metrics"][0]["value"] == "42"


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_school_board_summary_rejects_builder_sample_fallback_in_production():
    school = School.objects.create(name="Board Sample Rejection School")
    user = User.objects.create_user(username="board-sample-dashboard-test", school=school)
    user.set_unusable_password()
    user.save(update_fields=["password"])

    def sample_builder(school_id):
        return build_dashboard_payload(
            dashboard_key="school-board",
            metrics=[metric("Current enrollment", 0)],
            alerts=[],
            queue=[],
            meta={"school_id": str(school_id), "served_from": "sample"},
        )

    with patch.dict(DASHBOARD_PAYLOAD_BUILDERS, {"school-board": sample_builder}):
        response = _client_for(user).get(
            reverse("dashboard-summary", kwargs={"dashboard_key": "school-board"}),
            HTTP_X_SCHOOL_ID=str(school.id),
        )

    assert response.status_code == 503
    assert response.json()["code"] == "dashboard_live_data_required"


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_school_board_summary_rejects_cross_tenant_access():
    school = School.objects.create(name="Board Home School")
    other_school = School.objects.create(name="Board Other School")
    user = User.objects.create_user(username="board-cross-tenant-test", school=school)
    user.set_unusable_password()
    user.save(update_fields=["password"])

    def live_builder(school_id):
        return build_dashboard_payload(
            dashboard_key="school-board",
            metrics=[metric("Current enrollment", 42)],
            alerts=[],
            queue=[],
            meta={"school_id": str(school_id), "served_from": "live_db"},
        )

    with patch.dict(DASHBOARD_PAYLOAD_BUILDERS, {"school-board": live_builder}):
        response = _client_for(user).get(
            reverse("dashboard-summary", kwargs={"dashboard_key": "school-board"}),
            HTTP_X_SCHOOL_ID=str(other_school.id),
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_school_board_summary_rejects_invalid_tenant_header():
    school = School.objects.create(name="Board Invalid Header School")
    user = User.objects.create_user(username="board-invalid-tenant-test", school=school)
    user.set_unusable_password()
    user.save(update_fields=["password"])

    def live_builder(school_id):
        return build_dashboard_payload(
            dashboard_key="school-board",
            metrics=[metric("Current enrollment", 42)],
            alerts=[],
            queue=[],
            meta={"school_id": str(school_id), "served_from": "live_db"},
        )

    with patch.dict(DASHBOARD_PAYLOAD_BUILDERS, {"school-board": live_builder}):
        response = _client_for(user).get(
            reverse("dashboard-summary", kwargs={"dashboard_key": "school-board"}),
            HTTP_X_SCHOOL_ID="not-a-uuid",
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid X-School-Id (must be a UUID)."


@override_settings(CROWN_ENV="production", CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False)
@pytest.mark.django_db
def test_sample_payload_fallback_allows_authenticated_heritage_demo_session_only():
    school = School.objects.create(id=DEMO_SCHOOL_ID, name="Heritage Christian Academy")
    user = _create_user(
        school=school,
        username="heritage-admin@example.org",
        role_code="HEAD_OF_SCHOOL",
    )
    request = RequestFactory().get(
        "/api/v1/dashboards/admin/summary/",
        HTTP_X_DEMO_ROLE="school_admin",
        HTTP_X_SCHOOL_ID=DEMO_SCHOOL_ID,
    )
    request.user = user

    assert _sample_dashboard_payloads_allowed(request) is True


@override_settings(CROWN_ENV="production", CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False)
@pytest.mark.django_db
def test_sample_payload_fallback_rejects_non_heritage_user_with_demo_header():
    school = School.objects.create(name="Non Heritage School")
    user = _create_user(
        school=school,
        username="other-admin@example.org",
        role_code="SCHOOL_ADMIN",
    )
    request = RequestFactory().get(
        "/api/v1/dashboards/admin/summary/",
        HTTP_X_DEMO_ROLE="school_admin",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    request.user = user

    assert _sample_dashboard_payloads_allowed(request) is False
