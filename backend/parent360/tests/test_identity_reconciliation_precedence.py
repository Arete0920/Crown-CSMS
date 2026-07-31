from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from core.models import School
from households.models import Guardian, Household
from parent360.reconciliation import build_identity_reconciliation_report


pytestmark = pytest.mark.django_db


def test_cross_tenant_account_conflict_precedes_inactive_household():
    home_school = School.objects.create(name="Reconciliation Home School")
    foreign_school = School.objects.create(name="Reconciliation Foreign School")
    household = Household.objects.create(
        school_id=home_school.id,
        name="Inactive Home Household",
        is_active=False,
    )
    foreign_account = get_user_model().objects.create_user(
        username="foreign-reconciliation-account",
        email="foreign-reconciliation@example.com",
        password="test-pass",
        school=foreign_school,
    )
    guardian = Guardian.objects.create(
        school_id=home_school.id,
        household=household,
        first_name="Pat",
        last_name="Conflict",
        email="foreign-reconciliation@example.com",
    )

    # Simulate legacy/inconsistent persisted data by bypassing model validation.
    Guardian.objects.filter(pk=guardian.pk).update(account_id=foreign_account.id)

    report = build_identity_reconciliation_report(school_id=home_school.id)

    assert report["total"] == 1
    assert report["summary"] == {"cross_tenant": 1}
    assert report["records"][0]["classification"] == "cross_tenant"
    assert report["records"][0]["reason"] == "guardian_account_school_mismatch"
