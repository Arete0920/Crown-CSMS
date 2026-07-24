from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from billing.models import BillingRun, Invoice
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from crown_api.billing_api.drf_views import BillingRunCreateApiView
from crown_api.billing_api.views import PaymentsApplyView, PaymentsCreateView
from households.models import Household
from ledger.models import Allocation, Charge, LedgerAccount, Payment


pytestmark = pytest.mark.django_db

MUTATION_CASES = (
    pytest.param(
        "/api/v1/billing/payments/",
        PaymentsCreateView,
        id="payment-create",
    ),
    pytest.param(
        f"/api/v1/billing/payments/{uuid.UUID(int=1)}/apply/",
        PaymentsApplyView,
        id="payment-apply",
    ),
    pytest.param(
        "/api/v1/billing/runs/api/",
        BillingRunCreateApiView,
        id="billing-run-create",
    ),
)

MUTATION_MODELS = (
    Payment,
    Allocation,
    BillingRun,
    Invoice,
    Charge,
    Household,
    LedgerAccount,
)


@pytest.fixture(autouse=True)
def _enforce_normal_tenant_controls(settings):
    settings.TENANT_HEADER_REQUIRED = True
    settings.CROWN_DEMO_MODE = False
    settings.DEMO_MODE = False


def _school(label: str) -> School:
    return School.objects.create(name=f"{label}-{uuid.uuid4()}")


def _user_with_role(school: School, role_code: str) -> UserAccount:
    token = uuid.uuid4()
    user = UserAccount.objects.create_user(
        username=f"billing-authz-{token}",
        email=f"billing-authz-{token}@example.test",
        password="TestAuthSecret-LocalOnly",
        school=school,
    )
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    return user


def _grant(role_code: str, *permission_codes: str) -> None:
    for permission_code in permission_codes:
        permission, _ = CrownPermission.objects.get_or_create(
            code=permission_code,
            defaults={"description": ""},
        )
        RolePermission.objects.get_or_create(
            role_code=role_code,
            permission=permission,
        )


def _revoke(role_code: str, *permission_codes: str) -> None:
    RolePermission.objects.filter(
        role_code=role_code,
        permission__code__in=permission_codes,
    ).delete()


def _client_for(user: UserAccount | None = None) -> APIClient:
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _mutation_counts() -> dict[type, int]:
    return {model: model.objects.count() for model in MUTATION_MODELS}


def _block_if_view_runs(monkeypatch, view_class):
    calls = []

    def _unexpected_post(self, request, *args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("billing mutation view executed after authorization should have denied")

    monkeypatch.setattr(view_class, "post", _unexpected_post)
    return calls


def _seed_account(school: School):
    household = Household.objects.create(
        school_id=school.id,
        name=f"Billing Household {uuid.uuid4()}",
    )
    account = LedgerAccount.objects.create(
        school_id=school.id,
        household=household,
    )
    charge = Charge.objects.create(
        school_id=school.id,
        account=account,
        description="Tuition",
        amount=Decimal("100.00"),
    )
    return household, account, charge


@pytest.mark.parametrize("path,view_class", MUTATION_CASES)
def test_anonymous_access_is_denied_before_view_or_database_mutation(
    monkeypatch,
    path,
    view_class,
):
    school = _school("Anonymous Billing")
    calls = _block_if_view_runs(monkeypatch, view_class)
    before = _mutation_counts()

    response = _client_for().post(
        path,
        data={},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code in {401, 403}
    assert calls == []
    assert _mutation_counts() == before


@pytest.mark.parametrize("path,view_class", MUTATION_CASES)
@pytest.mark.parametrize(
    "role_code,permission_codes",
    (
        pytest.param("TEACHER", ("teacher.view",), id="non-finance-role"),
        pytest.param(
            "FINANCE_DIRECTOR",
            ("finance.view", "billing.view"),
            id="finance-read-only",
        ),
    ),
)
def test_authenticated_user_without_finance_edit_is_denied_before_view_or_mutation(
    monkeypatch,
    path,
    view_class,
    role_code,
    permission_codes,
):
    school = _school("Unauthorized Billing")
    user = _user_with_role(school, role_code)
    _grant(role_code, *permission_codes)
    _revoke(role_code, "finance.edit")
    calls = _block_if_view_runs(monkeypatch, view_class)
    before = _mutation_counts()

    response = _client_for(user).post(
        path,
        data={},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 403
    assert calls == []
    assert _mutation_counts() == before


@pytest.mark.parametrize("path,view_class", MUTATION_CASES)
def test_malformed_tenant_context_is_rejected_before_view_or_mutation(
    monkeypatch,
    path,
    view_class,
):
    school = _school("Malformed Tenant Billing")
    user = _user_with_role(school, "FINANCE_DIRECTOR")
    _grant("FINANCE_DIRECTOR", "finance.edit")
    calls = _block_if_view_runs(monkeypatch, view_class)
    before = _mutation_counts()

    response = _client_for(user).post(
        path,
        data={},
        format="json",
        HTTP_X_SCHOOL_ID="not-a-uuid",
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_tenant_header"
    assert calls == []
    assert _mutation_counts() == before


@pytest.mark.parametrize("path,view_class", MUTATION_CASES)
def test_cross_tenant_attempt_is_rejected_before_view_or_mutation(
    monkeypatch,
    path,
    view_class,
):
    authorized_school = _school("Authorized Billing Tenant")
    target_school = _school("Target Billing Tenant")
    user = _user_with_role(authorized_school, "FINANCE_DIRECTOR")
    _grant("FINANCE_DIRECTOR", "finance.edit")
    calls = _block_if_view_runs(monkeypatch, view_class)
    before = _mutation_counts()

    response = _client_for(user).post(
        path,
        data={},
        format="json",
        HTTP_X_SCHOOL_ID=str(target_school.id),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "tenant_access_denied"
    assert calls == []
    assert _mutation_counts() == before


@pytest.mark.parametrize("role_code", ("FINANCE_DIRECTOR", "finance_admin"))
def test_authorized_finance_roles_can_create_same_tenant_payment(role_code):
    school = _school("Authorized Payment Create")
    user = _user_with_role(school, role_code)
    _grant(role_code, "finance.edit")
    household, account, charge = _seed_account(school)

    response = _client_for(user).post(
        "/api/v1/billing/payments/",
        data={
            "household_id": str(household.id),
            "account_id": str(account.id),
            "amount": "25.00",
            "reference": f"AUTHZ-{uuid.uuid4()}",
            "source": "manual",
            "allocations": [
                {
                    "charge_id": str(charge.id),
                    "amount": "25.00",
                }
            ],
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 201
    payment = Payment.objects.get(pk=response.data["payment_id"])
    allocation = Allocation.objects.get(payment=payment, charge=charge)
    assert payment.school_id == school.id
    assert payment.account_id == account.id
    assert payment.amount == Decimal("25.00")
    assert allocation.school_id == school.id
    assert allocation.amount == Decimal("25.00")


def test_authorized_finance_role_can_apply_same_tenant_payment():
    school = _school("Authorized Payment Apply")
    user = _user_with_role(school, "FINANCE_DIRECTOR")
    _grant("FINANCE_DIRECTOR", "finance.edit")
    _, account, charge = _seed_account(school)
    payment = Payment.objects.create(
        school_id=school.id,
        account=account,
        source="manual",
        reference=f"APPLY-{uuid.uuid4()}",
        amount=Decimal("50.00"),
    )

    response = _client_for(user).post(
        f"/api/v1/billing/payments/{payment.id}/apply/",
        data={
            "allocations": [
                {
                    "charge_id": str(charge.id),
                    "amount": "20.00",
                }
            ]
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 201
    allocation = Allocation.objects.get(payment=payment, charge=charge)
    assert allocation.school_id == school.id
    assert allocation.amount == Decimal("20.00")


def test_authorized_finance_role_can_create_same_tenant_billing_run():
    school = _school("Authorized Billing Run")
    user = _user_with_role(school, "FINANCE_DIRECTOR")
    _grant("FINANCE_DIRECTOR", "finance.edit")

    response = _client_for(user).post(
        "/api/v1/billing/runs/api/",
        data={
            "term": "2026-2027",
            "description": "Authorization proof billing run",
            "amount_per_student": "250.00",
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 201
    payload = response.data["data"]
    billing_run = BillingRun.objects.get(pk=payload["billing_run_id"])
    invoice = Invoice.objects.get(pk=payload["invoice_id"])
    charge = Charge.objects.get(pk=payload["ledger_charge_id"])
    household = Household.objects.get(pk=payload["household_id"])
    account = LedgerAccount.objects.get(household=household)
    assert billing_run.school_id == school.id
    assert invoice.school_id == school.id
    assert charge.school_id == school.id
    assert household.school_id == school.id
    assert account.school_id == school.id
    assert billing_run.amount_per_student == Decimal("250.00")
