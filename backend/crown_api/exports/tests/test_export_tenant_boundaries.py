from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate

from billing.models import BillingRun, Invoice
from crown_api.exports.permissions import IsFinanceRole
from crown_api.exports.views import HouseholdsCSVExportView, InvoicesCSVExportView
from households.models import Household


pytestmark = pytest.mark.django_db


def _superuser(django_user_model):
    user = django_user_model.objects.create_user(
        username=f"finance-{uuid.uuid4()}@example.test",
        email=f"finance-{uuid.uuid4()}@example.test",
        password="export-test-password-only",
    )
    user.is_superuser = True
    user.is_staff = True
    user.save(update_fields=["is_superuser", "is_staff"])
    return user


def _stream_text(response) -> str:
    return b"".join(response.streaming_content).decode("utf-8")


def test_invoice_export_excludes_other_school_records(django_user_model):
    school_a = uuid.uuid4()
    school_b = uuid.uuid4()

    household_a = Household.objects.create(school_id=school_a, name="Alpha Family")
    household_b = Household.objects.create(school_id=school_b, name="Beta Family")
    run_a = BillingRun.objects.create(school_id=school_a, term="2026-FALL")
    run_b = BillingRun.objects.create(school_id=school_b, term="2026-FALL")
    invoice_a = Invoice.objects.create(
        school_id=school_a,
        billing_run=run_a,
        household=household_a,
        due_on=date(2026, 9, 1),
        total_amount=Decimal("100.00"),
    )
    invoice_b = Invoice.objects.create(
        school_id=school_b,
        billing_run=run_b,
        household=household_b,
        due_on=date(2026, 9, 1),
        total_amount=Decimal("900.00"),
    )

    request = APIRequestFactory().get("/exports/invoices.csv")
    force_authenticate(request, user=_superuser(django_user_model))

    with patch("crown_api.exports.views.get_request_school_id", return_value=school_a):
        response = InvoicesCSVExportView.as_view()(request)

    assert response.status_code == 200
    body = _stream_text(response)
    assert str(invoice_a.id) in body
    assert str(invoice_b.id) not in body
    assert "100.00" in body
    assert "900.00" not in body


def test_invoice_export_denies_authenticated_non_finance_user(django_user_model):
    user = django_user_model.objects.create_user(
        username=f"teacher-{uuid.uuid4()}@example.test",
        email=f"teacher-{uuid.uuid4()}@example.test",
        password="export-test-password-only",
    )
    request = APIRequestFactory().get("/exports/invoices.csv")
    force_authenticate(request, user=user)

    response = InvoicesCSVExportView.as_view()(request)

    assert response.status_code == 403


def test_finance_permission_fails_closed_for_missing_or_broken_identity():
    permission = IsFinanceRole()

    anonymous_request = type("Request", (), {"user": AnonymousUser()})()
    assert permission.has_permission(anonymous_request, None) is False

    class BrokenGroups:
        def values_list(self, *args, **kwargs):
            raise RuntimeError("group lookup failed")

    broken_user = type(
        "BrokenUser",
        (),
        {
            "is_authenticated": True,
            "is_superuser": False,
            "groups": BrokenGroups(),
        },
    )()
    broken_request = type("Request", (), {"user": broken_user})()
    assert permission.has_permission(broken_request, None) is False


def test_generic_school_scoped_export_returns_no_data_without_school_context(django_user_model):
    school_id = uuid.uuid4()
    household = Household.objects.create(school_id=school_id, name="Should Not Export")

    request = APIRequestFactory().get("/exports/households.csv")
    force_authenticate(request, user=_superuser(django_user_model))

    with patch("crown_api.exports.views.get_request_school_id", return_value=None):
        response = HouseholdsCSVExportView.as_view()(request)

    assert response.status_code == 403
    assert str(household.id) not in _stream_text(response)
