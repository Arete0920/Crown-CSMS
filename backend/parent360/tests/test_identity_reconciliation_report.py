from __future__ import annotations

import io
import json

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from core.models import Family, Guardian as CoreGuardian, School
from households.models import Guardian, Household
from parent360.reconciliation import build_identity_reconciliation_report


pytestmark = pytest.mark.django_db


def _household_guardian(
    school: School,
    *,
    email: str = "parent@example.com",
    account=None,
    active: bool = True,
):
    household = Household.objects.create(
        school_id=school.id,
        name=f"Household {email}",
        is_active=active,
    )
    return Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=account,
        first_name="Pat",
        last_name="Parent",
        email=email,
        is_primary=True,
    )


def _account(school: School, *, email: str, active: bool = True, guardian=None):
    return get_user_model().objects.create_user(
        username=f"user-{school.id}-{email}",
        email=email,
        password="test-pass",
        school=school,
        is_active=active,
        guardian=guardian,
    )


def _core_guardian(school: School, *, email: str):
    family = Family.objects.create(
        school=school,
        family_name=f"Family {email}",
    )
    return CoreGuardian.objects.create(
        school=school,
        family=family,
        first_name="Canonical",
        last_name="Guardian",
        email=email,
        relationship="GUARDIAN",
    )


def _only_record(report: dict) -> dict:
    assert report["total"] == 1
    return report["records"][0]


def test_report_classifies_valid_explicit_link_as_mapped():
    school = School.objects.create(name="Mapped School")
    account = _account(school, email="mapped@example.com")
    guardian = _household_guardian(school, email="mapped@example.com", account=account)

    record = _only_record(build_identity_reconciliation_report(school_id=school.id))

    assert record["guardian_id"] == str(guardian.id)
    assert record["account_id"] == str(account.id)
    assert record["classification"] == "mapped"
    assert record["reason"] == "explicit_account_link_valid"


def test_report_never_treats_single_email_candidate_as_authorization():
    school = School.objects.create(name="Manual Review School")
    account = _account(school, email="candidate@example.com")
    _household_guardian(school, email="candidate@example.com")

    record = _only_record(build_identity_reconciliation_report(school_id=school.id))

    assert record["classification"] == "manual_review"
    assert record["account_id"] is None
    assert record["candidate_account_ids"] == [str(account.id)]
    assert record["reason"] == "single_email_candidate_is_not_authorization"


def test_report_classifies_duplicate_compatibility_emails():
    school = School.objects.create(name="Duplicate Email School")
    _household_guardian(school, email="duplicate@example.com")
    _household_guardian(school, email="DUPLICATE@example.com")

    report = build_identity_reconciliation_report(school_id=school.id)

    assert report["summary"] == {"duplicate_email": 2}
    assert all(record["account_id"] is None for record in report["records"])


def test_report_classifies_inactive_explicit_account_and_household():
    school = School.objects.create(name="Inactive School")
    inactive_account = _account(
        school,
        email="inactive-account@example.com",
        active=False,
    )
    _household_guardian(
        school,
        email="inactive-account@example.com",
        account=inactive_account,
    )
    _household_guardian(
        school,
        email="inactive-household@example.com",
        active=False,
    )

    report = build_identity_reconciliation_report(school_id=school.id)

    assert report["summary"] == {
        "inactive_account": 1,
        "inactive_household": 1,
    }


def test_report_flags_same_tenant_dual_guardian_models_for_manual_review():
    school = School.objects.create(name="Dual Identity School")
    canonical = _core_guardian(school, email="dual@example.com")
    account = _account(school, email="dual@example.com", guardian=canonical)
    _household_guardian(school, email="dual@example.com", account=account)

    record = _only_record(build_identity_reconciliation_report(school_id=school.id))

    assert record["classification"] == "manual_review"
    assert record["canonical_guardian_id"] == str(canonical.id)
    assert record["reason"] == "dual_guardian_models_have_no_immutable_crosswalk"


def test_management_command_is_read_only_and_emits_json():
    school = School.objects.create(name="Command School")
    account = _account(school, email="command@example.com")
    guardian = _household_guardian(school, email="command@example.com")
    before = {
        "guardians": Guardian.objects.count(),
        "accounts": get_user_model().objects.count(),
        "account_id": guardian.account_id,
    }
    output = io.StringIO()

    call_command(
        "report_parent360_identity_reconciliation",
        school_id=str(school.id),
        stdout=output,
    )

    payload = json.loads(output.getvalue())
    guardian.refresh_from_db()
    after = {
        "guardians": Guardian.objects.count(),
        "accounts": get_user_model().objects.count(),
        "account_id": guardian.account_id,
    }

    assert payload["read_only"] is True
    assert payload["automatic_linking"] is False
    assert payload["records"][0]["candidate_account_ids"] == [str(account.id)]
    assert before == after
