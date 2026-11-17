"""Actual normal-login care transactions against fictional presenter records."""
from uuid import uuid4
import pytest
from django.core.management.base import CommandError
from django.utils import timezone
from rest_framework.test import APIClient
from aftercare.models import AftercareAttendance, AftercarePickupContact, DaycareAttendance, DaycareRelease
from core.models import School
from sandbox_demo.test_universal_access import operator_secrets, login
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_care import prepare_presenter_care
from subscriptions.models import Plan, SchoolModule
from summer_camp.models import SummerCampEnrollment
from tenants.models import TenantProfile

pytestmark = pytest.mark.django_db


@pytest.fixture
def care(local_runtime, operator_secrets):
    prepare_presenter(apply=True, enable_password_login=True)
    assert prepare_presenter_care()["mode"] == "PREFLIGHT"
    assert not Plan.objects.exists()
    return prepare_presenter_care(apply=True)


def test_daycare_login_checkin_readback_release_and_denials(care, operator_secrets):
    staff, tokens = login("daycare_staff", operator_secrets)
    parent, _ = login("parent", operator_secrets)
    payload = {key: care[key] for key in ("site_id", "room_id", "child_id")}
    payload.update(program_code="DAYCARE", request_key=str(uuid4()))
    path = "/api/v1/aftercare/daycare/attendance/checkin/"
    assert parent.post(path, payload, format="json").status_code == 403
    assert APIClient().post(path, payload, format="json", HTTP_X_SCHOOL_ID=care["school_id"]).status_code == 401
    created = staff.post(path, payload, format="json")
    assert created.status_code == 201, created.content
    attendance_id = created.json()["attendance_id"]
    assert DaycareAttendance.objects.filter(pk=attendance_id, school_id=care["school_id"]).exists()
    roster = f'/api/v1/aftercare/daycare/sites/{care["site_id"]}/roster/'
    for _ in range(2):
        assert staff.get(roster).json()["children_present"] == 1
    assert staff.post(path, {**payload, "request_key": str(uuid4())}, format="json").status_code == 409
    from aftercare.models import DaycareGuardianAuthority
    authority = DaycareGuardianAuthority.objects.get(child_id=care["child_id"])
    released = staff.post("/api/v1/aftercare/daycare/attendance/release/", {
        "site_id": care["site_id"], "room_id": care["room_id"], "attendance_id": attendance_id,
        "guardian_authority_id": str(authority.pk), "request_key": str(uuid4()),
        "identity_verified": True, "identity_method": "PERSONALLY_KNOWN"}, format="json")
    assert released.status_code == 201, released.content
    assert DaycareRelease.objects.filter(attendance_id=attendance_id, school_id=care["school_id"]).count() == 1
    assert staff.get(roster).json()["children_present"] == 0
    foreign = School.objects.create(name="Separate invented care tenant")
    staff.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}", HTTP_X_SCHOOL_ID=str(foreign.pk))
    assert staff.get(roster).status_code == 404


def test_am_pm_independent_custody_and_parent_readback(care, operator_secrets):
    staff, _ = login("school_admin", operator_secrets)
    parent, _ = login("parent", operator_secrets)
    child = care["care_student_id"]
    base = "/api/v1/aftercare/"
    body = {"student_id": child, "care_session": "AM"}
    assert parent.post(base + "attendance/checkin/", body, format="json").status_code == 403
    am = staff.post(base + "attendance/checkin/", body, format="json")
    assert am.status_code == 201, am.content
    handoff = staff.post(base + "attendance/school-handoff/", {"student_id": child}, format="json")
    assert handoff.status_code == 200, handoff.content
    pm = staff.post(base + "attendance/checkin/", {**body, "care_session": "PM"}, format="json")
    assert pm.status_code == 201, pm.content
    contact = AftercarePickupContact.objects.get(student_fk_id=child)
    released = staff.post(base + "attendance/checkout/", {"student_id": child,
        "care_session": "PM", "pickup_contact_id": contact.pk, "pickup_verified": True}, format="json")
    assert released.status_code == 200, released.content
    rows = list(AftercareAttendance.objects.filter(student_fk_id=child).order_by("care_session"))
    assert len(rows) == 2 and rows[0].handoff_verified and rows[1].pickup_verified
    for _ in range(2):
        response = parent.get(base + f"parent/{child}/")
        assert response.status_code == 200, response.content
    assert rows[0].pk != rows[1].pk


def test_camp_registration_is_blocked_pending_real_clearance(care, operator_secrets):
    director, _ = login("school_admin", operator_secrets)
    parent, _ = login("parent", operator_secrets)
    enrollment = SummerCampEnrollment.objects.get(school_id=care["school_id"])
    assert enrollment.readiness_status == "BLOCKED" and enrollment.payment_status == "NOT_BILLED"
    base = "/api/v1/summer-camp/"
    for _ in range(2):
        assert parent.get(base + f'parent/{care["care_student_id"]}/').status_code == 200
    body = {"session_id": enrollment.session_id, "student_id": care["care_student_id"]}
    denied = director.post(base + "attendance/checkin/", body, format="json")
    assert denied.status_code == 400, denied.content
    enrollment.refresh_from_db()
    assert enrollment.readiness_status == "BLOCKED"
    assert parent.post(base + "enrollments/", body, format="json").status_code == 403


def test_care_repeat_and_bootstrap_reset_refuse_without_changing_records(care):
    before = dict(TenantProfile.objects.values_list("pk", "payment_provider"))
    assert set(before.values()) == {"none"}
    with pytest.raises(CommandError):
        prepare_presenter_care(apply=True)
    with pytest.raises(CommandError):
        prepare_presenter(apply=True, reset=True)
    assert dict(TenantProfile.objects.values_list("pk", "payment_provider")) == before
    assert SchoolModule.objects.filter(school_id=care["school_id"]).count() == 3


def test_expired_care_license_denies_new_daycare_custody(care, operator_secrets):
    staff, _ = login("daycare_staff", operator_secrets)
    SchoolModule.objects.filter(school_id=care["school_id"], module_key="little_lambs").update(expiry_date=timezone.now() - timezone.timedelta(seconds=1))
    response = staff.post("/api/v1/aftercare/daycare/attendance/checkin/", {
        **{key: care[key] for key in ("site_id", "room_id", "child_id")},
        "program_code": "DAYCARE", "request_key": str(uuid4())}, format="json")
    assert response.status_code == 403
    assert not DaycareAttendance.objects.exists()


def test_camp_operator_can_create_edit_and_independently_read_program(care, operator_secrets):
    operator, _ = login("school_admin", operator_secrets)
    base = "/api/v1/summer-camp/programs/"
    created = operator.post(base, {"school": care["school_id"], "name": "Fictional Arts Camp", "program_type": "DAY_CAMP"}, format="json")
    assert created.status_code == 201, created.content
    program = created.json()
    updated = operator.put(base + str(program["id"]) + "/", {"school": care["school_id"], "name": "Fictional Arts and Music Camp", "program_type": "DAY_CAMP"}, format="json")
    assert updated.status_code == 200, updated.content
    for _ in range(2):
        rows = operator.get(base).json()
        assert any(row["id"] == program["id"] and row["name"] == "Fictional Arts and Music Camp" for row in rows)
    from summer_camp.models import SummerCampProgram
    assert SummerCampProgram.objects.get(pk=program["id"]).name == "Fictional Arts and Music Camp"
