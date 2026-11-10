"""Finance Setup API contract: real UUID schools, permissions, and locked years.

Run through the real registered URL and canonical tenant resolver; never mock
school_id_from_request or replace UUID school identities with small integers.
"""
from io import StringIO

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from core.management.commands.seed_permissions import ROLE_PERMISSIONS
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from finance_setup.models import FinancePolicyVersion
from finance_setup.services import (
    PolicyLockedError, get_policy_snapshot, lock_finance_policies, upsert_finance_policies,
)

pytestmark = pytest.mark.django_db

YEAR = "2026-2027"

FULL_PAYLOAD = {
    "academic_year": YEAR,
    "tuition": {
        "tuition_mode": "grade_based",
        "currency": "USD",
        "flat_annual_tuition_cents": 0,
        "fees_apply_to_aid": False,
        "fees_apply_to_discounts": False,
    },
    "discounts": {
        "discounts_apply_to": "tuition_only",
        "stacking_enabled": True,
        "sibling_discount_enabled": True,
        "sibling_discount_percent_bp": 1000,
        "sibling_discount_applies_from_child": 2,
        "staff_discount_enabled": True,
        "staff_discount_percent_bp": 0,
        "ministry_discount_enabled": False,
        "ministry_discount_percent_bp": 0,
        "max_discount_percent_bp": 10000,
    },
    "aid": {
        "application_fee_cents": 5500,
        "aid_applies_to": "tuition_only",
        "distribute_aid_evenly": True,
        "max_aid_per_student_cents": 0,
        "max_aid_per_family_cents": 0,
    },
    "payment_plans": {
        "allow_pay_in_full": True,
        "allow_semi_annual": True,
        "allow_quarterly": True,
        "allow_10_month": True,
        "allow_12_month": True,
        "ach_required_for_installments": True,
        "pay_in_full_discount_percent_bp": 0,
        "late_fee_grace_days": 5,
        "late_fee_flat_cents": 0,
    },
    "extended_care": {
        "supports_annual": False,
        "supports_monthly": True,
        "supports_weekly": False,
        "supports_drop_in_daily": True,
        "supports_hybrid": True,
        "late_pickup_grace_minutes": 5,
        "late_pickup_fee_cents": 0,
        "late_pickup_per_minute_cents": 0,
        "post_to_ledger": True,
        "include_in_tuition_plan": False,
    },
}

@pytest.fixture
def setup_context():
    school = School.objects.create(name="Fictional Finance Setup Academy")
    other_school = School.objects.create(name="Fictional Foreign Academy")
    user = UserAccount.objects.create_user(
        username="finance-setup-officer", password="test-only", school=school,
    )
    UserRole.objects.create(user=user, school=school, role_code="FINANCE_DIRECTOR")
    for code in ("finance.view", "finance.configure"):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(
            role_code="FINANCE_DIRECTOR", permission=permission,
        )
    client = APIClient()
    client.force_authenticate(user=user)
    return {"school": school, "other_school": other_school, "user": user, "client": client}


def _get(client, school, suffix, params=None):
    return client.get(
        f"/api/v1/finance-setup/wizard/{suffix}/",
        params or {}, HTTP_X_SCHOOL_ID=str(school.pk),
    )


def _post(client, school, suffix, payload):
    return client.post(
        f"/api/v1/finance-setup/wizard/{suffix}/",
        payload, format="json", HTTP_X_SCHOOL_ID=str(school.pk),
    )


def test_configure_saves_and_reads_real_uuid_school(setup_context):
    c = setup_context
    response = _post(c["client"], c["school"], "configure", FULL_PAYLOAD)
    assert response.status_code == 200, response.content
    assert response.json()["status"] == "saved"
    assert response.json()["data"]["version"]["school_id"] == str(c["school"].pk)
    found = get_policy_snapshot(school_id=c["school"].pk, academic_year=YEAR)
    assert found is not None
    assert found.school_id == str(c["school"].pk)
    readback = _get(c["client"], c["school"], "status", {"year": YEAR})
    assert readback.status_code == 200, readback.content
    assert readback.json()["data"]["version"]["school_id"] == str(c["school"].pk)


def test_lock_binds_actor_to_authenticated_user_not_request_body(setup_context):
    c = setup_context
    assert _post(c["client"], c["school"], "configure", FULL_PAYLOAD).status_code == 200
    response = _post(c["client"], c["school"], "lock", {
        "academic_year": YEAR, "locked_by": "forged_person",
    })
    assert response.status_code == 200, response.content
    assert response.json()["status"] == "locked"
    assert response.json()["locked_by"] == str(c["user"].pk)
    assert response.json()["locked_by"] != "forged_person"


def test_configure_after_lock_is_409_without_mutation(setup_context):
    c = setup_context
    school = c["school"]
    upsert_finance_policies(school_id=school.pk, academic_year=YEAR, payload=FULL_PAYLOAD)
    lock_finance_policies(school_id=school.pk, academic_year=YEAR)
    before = FinancePolicyVersion.objects.get(school_id=str(school.pk), academic_year=YEAR)
    response = _post(c["client"], school, "configure", FULL_PAYLOAD)
    assert response.status_code == 409, response.content
    before.refresh_from_db()
    assert before.is_locked is True


def test_lock_idempotent_and_snapshot_readable(setup_context):
    c = setup_context
    school = c["school"]
    upsert_finance_policies(school_id=school.pk, academic_year=YEAR, payload=FULL_PAYLOAD)
    first = _post(c["client"], school, "lock", {"academic_year": YEAR})
    second = _post(c["client"], school, "lock", {"academic_year": YEAR})
    assert first.status_code == second.status_code == 200
    assert first.json()["locked_at"] == second.json()["locked_at"]
    snapshot = _get(c["client"], school, "snapshot", {"year": YEAR})
    assert snapshot.status_code == 200, snapshot.content
    assert snapshot.json()["data"]["version"]["is_locked"] is True


def test_lock_missing_policy_returns_404(setup_context):
    c = setup_context
    response = _post(c["client"], c["school"], "lock", {"academic_year": "2099-2100"})
    assert response.status_code == 404, response.content


def test_service_rejects_changes_to_locked_policy(setup_context):
    school = setup_context["school"]
    upsert_finance_policies(school_id=school.pk, academic_year=YEAR, payload=FULL_PAYLOAD)
    lock_finance_policies(school_id=school.pk, academic_year=YEAR)
    with pytest.raises(PolicyLockedError):
        upsert_finance_policies(school_id=school.pk, academic_year=YEAR, payload=FULL_PAYLOAD)


def test_ungranted_user_cannot_read_configure_or_lock(setup_context):
    c = setup_context
    ungranted = UserAccount.objects.create_user(
        username="finance-ungranted", password="test-only",
        email="finance-ungranted@example.invalid", school=c["school"],
    )
    client = APIClient()
    client.force_authenticate(user=ungranted)
    assert _get(client, c["school"], "status", {"year": YEAR}).status_code == 403
    assert _post(client, c["school"], "configure", FULL_PAYLOAD).status_code == 403
    assert _post(client, c["school"], "lock", {"academic_year": YEAR}).status_code == 403
    assert FinancePolicyVersion.objects.count() == 0


def test_unauthenticated_cannot_mutate_even_with_valid_tenant_header(setup_context):
    c = setup_context
    client = APIClient()
    response = _post(client, c["school"], "configure", FULL_PAYLOAD)
    assert response.status_code in (401, 403), response.content
    assert FinancePolicyVersion.objects.count() == 0


def test_read_only_finance_grant_cannot_write_or_lock(setup_context):
    c = setup_context
    school = c["school"]
    upsert_finance_policies(school_id=school.pk, academic_year=YEAR, payload=FULL_PAYLOAD)
    reader = UserAccount.objects.create_user(
        username="finance-reader-only", password="test-only",
        email="finance-reader-only@example.invalid", school=school,
    )
    UserRole.objects.create(user=reader, school=school, role_code="FINANCE_SETUP_READER")
    perm, _ = CrownPermission.objects.get_or_create(code="finance.view")
    RolePermission.objects.get_or_create(
        role_code="FINANCE_SETUP_READER", permission=perm,
    )
    client = APIClient()
    client.force_authenticate(user=reader)
    assert _get(client, school, "status", {"year": YEAR}).status_code == 200
    assert _post(client, school, "configure", FULL_PAYLOAD).status_code == 403
    assert _post(client, school, "lock", {"academic_year": YEAR}).status_code == 403
    version = FinancePolicyVersion.objects.get(school_id=str(school.pk), academic_year=YEAR)
    assert version.is_locked is False


def test_foreign_school_uuid_denied_without_mutation(setup_context):
    c = setup_context
    school = c["school"]
    other = c["other_school"]
    upsert_finance_policies(school_id=school.pk, academic_year=YEAR, payload=FULL_PAYLOAD)
    response = _post(c["client"], other, "configure", FULL_PAYLOAD)
    assert response.status_code in (403, 404), response.content
    assert get_policy_snapshot(school_id=other.pk, academic_year=YEAR) is None
    assert FinancePolicyVersion.objects.count() == 1


def test_legacy_numeric_policy_rows_do_not_alias_uuid_school(setup_context):
    c = setup_context
    legacy = FinancePolicyVersion.objects.create(school_id=1, academic_year=YEAR)
    legacy.refresh_from_db()
    assert legacy.school_id == "1"
    response = _get(c["client"], c["school"], "status", {"year": YEAR})
    assert response.status_code == 404, response.content
    assert FinancePolicyVersion.objects.count() == 1


def test_role_matrix_restricts_finance_setup_to_approved_school_roles():
    for role in ("HEAD_OF_SCHOOL", "head_of_school", "FINANCE_DIRECTOR",
                 "finance", "finance_admin", "school_admin"):
        assert "finance.configure" in ROLE_PERMISSIONS[role]
    for role in ("AID_DIRECTOR", "PARENT", "STUDENT", "TEACHER", "aid_director"):
        assert "finance.configure" not in ROLE_PERMISSIONS[role]


def test_seed_permissions_includes_narrow_finance_configure_grant():
    call_command("seed_permissions", stdout=StringIO())
    permission = CrownPermission.objects.get(code="finance.configure")
    assert RolePermission.objects.filter(
        role_code="school_admin", permission=permission,
    ).exists()
    assert not RolePermission.objects.filter(
        role_code="PARENT", permission=permission,
    ).exists()
