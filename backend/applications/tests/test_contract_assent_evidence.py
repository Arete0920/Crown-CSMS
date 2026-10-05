import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from applications.models import (
    Application,
    ApplicationEvent,
    ApplicationStatus,
    ContractAssentEvidence,
    EnrollmentContract,
    EnrollmentContractStatus,
)
from core.models import CrownPermission, RolePermission, School, UserRole
from households.models import Guardian, Household


pytestmark = pytest.mark.django_db


def _user(*, school, email):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"contract-{uuid.uuid4()}",
        email=email,
        password="pass12345!",
    )
    if hasattr(user, "school_id"):
        user.school_id = school.id
        user.save(update_fields=["school_id"])
    return user


def _application_with_issued_contract(*, school, household):
    app = Application.objects.create(
        school_id=school.id,
        household=household,
        status=ApplicationStatus.DECIDED,
    )
    ApplicationEvent.objects.create(
        school_id=school.id,
        application=app,
        event_type="decision_made",
        payload={"decision": "accepted"},
    )
    contract = EnrollmentContract.objects.create(
        school_id=school.id,
        application=app,
        version=1,
        status=EnrollmentContractStatus.ISSUED,
        line_items=[{"label": "Tuition", "amount_cents": 100000}],
        contract_totals={"gross_tuition_cents": 100000, "net_family_obligation_cents": 100000},
        net_amount_cents=100000,
        responsible_payer="parent@example.org",
    )
    return app, contract


def test_authenticated_household_guardian_signs_exact_contract_version():
    school = School.objects.create(name="Contract Evidence School")
    household = Household.objects.create(school_id=school.id, name="Family")
    parent = _user(school=school, email="parent@example.org")
    Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=parent,
        first_name="Pat",
        last_name="Parent",
        email=parent.email,
        is_primary=True,
    )
    app, contract = _application_with_issued_contract(school=school, household=household)

    client = APIClient()
    client.force_authenticate(parent)
    response = client.post(
        f"/api/v1/admissions/applications/{app.id}/contract/assent/",
        {
            "action": "SIGN",
            "signer_name": "Pat Parent",
            "signer_email": parent.email,
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
        HTTP_USER_AGENT="CROWN contract test",
        HTTP_X_REQUEST_ID="contract-test-request-1",
    )

    assert response.status_code == 200, response.data
    contract.refresh_from_db()
    assert contract.status == EnrollmentContractStatus.SIGNED
    assert contract.signed_at is not None

    evidence = ContractAssentEvidence.objects.get(contract=contract)
    assert evidence.action == ContractAssentEvidence.Action.SIGN
    assert evidence.actor_user_id == parent.id
    assert evidence.signer_name == "Pat Parent"
    assert len(evidence.contract_sha256) == 64
    assert evidence.request_id == "contract-test-request-1"


def test_unrelated_parent_cannot_sign_contract():
    school = School.objects.create(name="Contract Privacy School")
    household = Household.objects.create(school_id=school.id, name="Family A")
    other_household = Household.objects.create(school_id=school.id, name="Family B")
    parent = _user(school=school, email="other@example.org")
    Guardian.objects.create(
        school_id=school.id,
        household=other_household,
        account=parent,
        first_name="Other",
        last_name="Parent",
        email=parent.email,
    )
    app, contract = _application_with_issued_contract(school=school, household=household)

    client = APIClient()
    client.force_authenticate(parent)
    response = client.post(
        f"/api/v1/admissions/applications/{app.id}/contract/assent/",
        {"action": "SIGN", "signer_name": "Other Parent"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 403
    contract.refresh_from_db()
    assert contract.status == EnrollmentContractStatus.ISSUED
    assert ContractAssentEvidence.objects.count() == 0


def test_generic_contract_update_cannot_bypass_assent_evidence():
    school = School.objects.create(name="Contract Bypass School")
    household = Household.objects.create(school_id=school.id, name="Family")
    staff = _user(school=school, email="registrar@example.org")
    permission, _ = CrownPermission.objects.get_or_create(
        code="admissions.edit",
        defaults={"description": "Edit admissions"},
    )
    RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)
    UserRole.objects.create(user=staff, school=school, role_code="REGISTRAR")
    app, contract = _application_with_issued_contract(school=school, household=household)

    client = APIClient()
    client.force_authenticate(staff)
    response = client.post(
        f"/api/v1/admissions/applications/{app.id}/contract/update/",
        {"status": "signed"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 409
    contract.refresh_from_db()
    assert contract.status == EnrollmentContractStatus.ISSUED
    assert ContractAssentEvidence.objects.count() == 0


def test_authorized_staff_countersigns_only_after_guardian_signature():
    school = School.objects.create(name="Contract Countersign School")
    household = Household.objects.create(school_id=school.id, name="Family")
    parent = _user(school=school, email="parent@example.org")
    staff = _user(school=school, email="registrar@example.org")
    Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=parent,
        first_name="Pat",
        last_name="Parent",
        email=parent.email,
        is_primary=True,
    )
    permission, _ = CrownPermission.objects.get_or_create(
        code="admissions.edit",
        defaults={"description": "Edit admissions"},
    )
    RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)
    UserRole.objects.create(user=staff, school=school, role_code="REGISTRAR")
    app, contract = _application_with_issued_contract(school=school, household=household)

    parent_client = APIClient()
    parent_client.force_authenticate(parent)
    signed = parent_client.post(
        f"/api/v1/admissions/applications/{app.id}/contract/assent/",
        {"action": "SIGN", "signer_name": "Pat Parent"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert signed.status_code == 200, signed.data

    staff_client = APIClient()
    staff_client.force_authenticate(staff)
    countersigned = staff_client.post(
        f"/api/v1/admissions/applications/{app.id}/contract/assent/",
        {"action": "COUNTERSIGN", "signer_name": "School Registrar"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert countersigned.status_code == 200, countersigned.data

    contract.refresh_from_db()
    assert contract.status == EnrollmentContractStatus.COUNTERSIGNED
    assert contract.countersigned_at is not None
    assert list(
        ContractAssentEvidence.objects.filter(contract=contract).values_list("action", flat=True)
    ) == ["SIGN", "COUNTERSIGN"]
