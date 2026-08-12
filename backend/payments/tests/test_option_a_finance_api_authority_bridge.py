import json
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from core.models import School, UserAccount
from finance.models import (
    FinanceObligation,
    FinancePayment,
    MoneyStatus,
    ObligationType,
)
from households.models import Guardian as HouseholdGuardian, Household
from ledger.models import LedgerAccount
from payments.models import (
    CanonicalPaymentStatus,
    CanonicalRefundStatus,
    Payment,
    Refund,
)


pytestmark = pytest.mark.django_db


def _user(username, *, is_staff=False):
    return UserAccount.objects.create_user(
        username=username,
        password="pass",
        email=f"{username}@test.example.com",
        is_staff=is_staff,
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _post(client, url, body, school_id):
    return client.post(
        url,
        data=json.dumps(body),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school_id),
    )


def _household(school, payer):
    household = Household.objects.create(school_id=school.id, name=f"HH-{payer.username}")
    HouseholdGuardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="Canonical",
        last_name="Guardian",
        email=payer.email,
        is_primary=True,
    )
    LedgerAccount.objects.create(school_id=school.id, household=household)
    return household


def _obligation(school, payer, amount_cents=10_000):
    return FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.TUITION,
        status=MoneyStatus.OPEN,
        description="Canonical API tuition",
        due_date=date.today() + timedelta(days=30),
        amount_cents=amount_cents,
    )


def test_finance_payment_urls_write_through_canonical_payments_authority():
    school = School.objects.create(name="Canonical Finance API")
    payer = _user("canonical_finance_parent")
    staff = _user("canonical_finance_staff", is_staff=True)
    household = _household(school, payer)
    obligation = _obligation(school, payer)

    create_response = _post(
        _client(payer),
        "/api/finance/payments/intent/",
        {"amount_cents": 10_000, "processor": "manual", "idempotency_key": "bridge-pay-1"},
        school.id,
    )
    assert create_response.status_code == 201
    finance_payment = FinancePayment.objects.get(pk=create_response.json()["id"])
    canonical_payment = Payment.objects.get(finance_payment_id=finance_payment.pk)
    assert canonical_payment.school_id == school.id
    assert canonical_payment.household_id == household.id
    assert canonical_payment.amount_cents == 10_000
    assert canonical_payment.status == CanonicalPaymentStatus.PENDING

    settle_response = _post(
        _client(staff),
        f"/api/finance/payments/{finance_payment.pk}/settle/",
        {"allocations": [{"obligation_id": obligation.id, "amount_cents": 10_000}]},
        school.id,
    )
    assert settle_response.status_code == 200
    canonical_payment.refresh_from_db()
    finance_payment.refresh_from_db()
    assert canonical_payment.status == CanonicalPaymentStatus.SETTLED
    assert finance_payment.status == "settled"

    refund_response = _post(
        _client(staff),
        f"/api/finance/payments/{finance_payment.pk}/refund/",
        {"amount_cents": 2_500, "idempotency_key": "bridge-refund-1"},
        school.id,
    )
    assert refund_response.status_code == 201
    canonical_refund = Refund.objects.get(payment=canonical_payment)
    canonical_payment.refresh_from_db()
    assert canonical_refund.status == CanonicalRefundStatus.SETTLED
    assert canonical_refund.finance_refund_id == refund_response.json()["id"]
    assert canonical_payment.status == CanonicalPaymentStatus.PARTIALLY_REFUNDED


def test_finance_payment_idempotency_reuses_same_canonical_and_compatibility_facts():
    school = School.objects.create(name="Canonical Finance Idempotency")
    payer = _user("canonical_idem_parent")
    _household(school, payer)
    client = _client(payer)
    body = {"amount_cents": 4_000, "processor": "manual", "idempotency_key": "bridge-idem-1"}

    first = _post(client, "/api/finance/payments/intent/", body, school.id)
    second = _post(client, "/api/finance/payments/intent/", body, school.id)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    finance_payment = FinancePayment.objects.get(pk=first.json()["id"])
    assert Payment.objects.filter(finance_payment_id=finance_payment.pk).count() == 1


def test_provider_backed_legacy_finance_payment_entry_point_remains_fail_closed():
    school = School.objects.create(name="Canonical Finance Provider Hold")
    payer = _user("canonical_hold_parent")
    _household(school, payer)

    before_legacy = FinancePayment.objects.count()
    before_canonical = Payment.objects.count()
    response = _post(
        _client(payer),
        "/api/finance/payments/intent/",
        {"amount_cents": 5_000, "processor": "stripe", "idempotency_key": "held-provider-1"},
        school.id,
    )

    assert response.status_code == 503
    assert response.json()["code"] == "payment_integration_on_hold"
    assert FinancePayment.objects.count() == before_legacy
    assert Payment.objects.count() == before_canonical
