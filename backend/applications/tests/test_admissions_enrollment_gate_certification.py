import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication
from applications.models import Application, Applicant, ApplicationEvent
from applications.views_admissions import ENROLLMENT_STATE_EVENT_TYPE
from core.models import AcademicYear, CrownPermission, RolePermission, School, UserRole
from households.models import Household


pytestmark = pytest.mark.django_db
User = get_user_model()


def _grant_admissions_edit(user, school):
    permission, _ = CrownPermission.objects.get_or_create(
        code="admissions.edit",
        defaults={"description": "Edit admissions"},
    )
    RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)
    UserRole.objects.get_or_create(user=user, school=school, role_code="REGISTRAR")


def _academic_year(school):
    return AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 15),
        is_current=True,
    )


def test_canonical_enrollment_confirmation_fails_closed_then_bridges_after_readiness():
    school = School.objects.create(name=f"Enrollment Gate {uuid.uuid4().hex[:8]}")
    _academic_year(school)
    household = Household.objects.create(school_id=school.id, name="Gate Household")
    application = Application.objects.create(
        school_id=school.id,
        household=household,
        status="DECIDED",
    )
    Applicant.objects.create(
        school_id=school.id,
        application=application,
        first_name="Grace",
        last_name="Student",
        grade_applying_for="5",
        source="church_referral",
    )
    ApplicationEvent.objects.create(
        school_id=school.id,
        application=application,
        event_type="decision_made",
        payload={"decision": "accepted"},
    )

    user = User.objects.create_user(
        username=f"registrar-{uuid.uuid4().hex[:8]}@example.test",
        password="AdmissionsGateOnly!",
    )
    _grant_admissions_edit(user, school)
    client = APIClient()
    client.force_authenticate(user=user)

    url = f"/api/v1/admissions/applications/{application.id}/lifecycle-chain/update/"

    blocked = client.post(
        url,
        {"mark_enrollment_confirmed": True},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert blocked.status_code == 409
    assert "countersigned contract" in blocked.data["detail"]
    assert not ApplicationEvent.objects.filter(
        school_id=school.id,
        application=application,
        event_type="enrollment_confirmed",
    ).exists()

    ApplicationEvent.objects.create(
        school_id=school.id,
        application=application,
        event_type=ENROLLMENT_STATE_EVENT_TYPE,
        payload={
            "contract_status": "countersigned",
            "deposit_status": "paid",
            "note": "certification fixture",
        },
    )

    confirmed = client.post(
        url,
        {
            "mark_enrollment_confirmed": True,
            "mark_classroom_ready": True,
            "mark_parent_portal_activated": True,
            "note": "certification path",
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert confirmed.status_code == 200, confirmed.data
    assert confirmed.data["applicant_to_student_status"] == "completed"
    assert confirmed.data["classroom_readiness_status"] == "completed"
    assert confirmed.data["parent_portal_activation_status"] == "completed"
    assert ApplicationEvent.objects.filter(
        school_id=school.id,
        application=application,
        event_type="enrollment_confirmed",
    ).exists()

    bridge = confirmed.data["legacy_conversion_bridge"]
    assert bridge["state"] == "enrolled"
    assert bridge["count"] == 1
    assert AdmissionsApplication.objects.filter(
        school=school,
        status=AdmissionsApplication.STATUS_ENROLLED,
        notes_internal__contains=f"canonical_application_id={application.id}",
    ).exists()


def test_canonical_lifecycle_chain_rejects_pre_acceptance_application():
    school = School.objects.create(name=f"Pre Acceptance {uuid.uuid4().hex[:8]}")
    _academic_year(school)
    household = Household.objects.create(school_id=school.id, name="Pre Acceptance Household")
    application = Application.objects.create(
        school_id=school.id,
        household=household,
        status="SUBMITTED",
    )
    user = User.objects.create_user(
        username=f"registrar-{uuid.uuid4().hex[:8]}@example.test",
        password="AdmissionsGateOnly!",
    )
    _grant_admissions_edit(user, school)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        f"/api/v1/admissions/applications/{application.id}/lifecycle-chain/update/",
        {"mark_enrollment_confirmed": True},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 409
    assert "only after acceptance" in response.data["detail"]
