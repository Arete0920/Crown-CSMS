import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client

from core.models import School
from households.models import Guardian, Household, Student
from billing.models import (
    BillingPayer,
    BillingResponsibilityRule,
    BillingRun,
    Invoice,
    InvoicePayerShare,
    PayerAllocationAttribution,
)
from ledger.models import Allocation, Charge, LedgerAccount, Payment


pytestmark = pytest.mark.django_db


def _user(school, group_name=None):
    User = get_user_model()
    identity = uuid.uuid4()
    user = User.objects.create_user(
        username=f"user-{identity}",
        email=f"user-{identity}@example.org",
        password="pass12345!",
    )
    if hasattr(user, "school_id"):
        user.school_id = school.id
        user.save(update_fields=["school_id"])
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def _invoice(school, household, amount=Decimal("1000.00")):
    run = BillingRun.objects.create(
        school_id=school.id,
        term="2026-FALL",
        run_type="TUITION",
        amount_per_student=amount,
    )
    return Invoice.objects.create(
        school_id=school.id,
        household=household,
        billing_run=run,
        total_amount=amount,
    )


def test_finance_user_can_create_payer_and_responsibility_rule():
    school = School.objects.create(name="Split Payer API School")
    household = Household.objects.create(school_id=school.id, name="Family")
    finance = _user(school, "finance_admin")
    client = Client()
    client.force_login(finance)

    payer_resp = client.post(
        f"/api/v1/billing/households/{household.id}/payers/",
        data={
            "payer_type": "THIRD_PARTY",
            "display_name": "Supporting Grandparent",
            "email": "grandparent@example.org",
        },
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert payer_resp.status_code == 201
    payer_id = payer_resp.json()["payer_id"]

    rule_resp = client.post(
        f"/api/v1/billing/households/{household.id}/responsibility-rules/",
        data={
            "payer_id": payer_id,
            "charge_type": "TUITION",
            "percentage_bps": 10000,
        },
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert rule_resp.status_code == 201
    assert rule_resp.json()["configured_scope_bps"] == 10000
    assert BillingPayer.objects.filter(id=payer_id, household=household).exists()
    assert BillingResponsibilityRule.objects.filter(payer_id=payer_id, percentage_bps=10000).exists()


def test_nonfinance_user_cannot_configure_payers():
    school = School.objects.create(name="Split Payer Deny School")
    household = Household.objects.create(school_id=school.id, name="Family")
    user = _user(school, "admissions_team")
    client = Client()
    client.force_login(user)

    resp = client.post(
        f"/api/v1/billing/households/{household.id}/payers/",
        data={"payer_type": "THIRD_PARTY", "display_name": "Unauthorized"},
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert resp.status_code == 403


def test_payer_self_service_returns_only_authenticated_payer_share():
    school = School.objects.create(name="Payer Privacy School")
    household = Household.objects.create(school_id=school.id, name="Family")
    parent_a = _user(school)
    parent_b = _user(school)
    guardian_a = Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=parent_a,
        first_name="Parent",
        last_name="A",
        email="a@example.org",
    )
    guardian_b = Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=parent_b,
        first_name="Parent",
        last_name="B",
        email="b@example.org",
    )
    payer_a = BillingPayer.objects.create(
        school_id=school.id,
        household=household,
        guardian=guardian_a,
        account=parent_a,
        payer_type=BillingPayer.PayerType.GUARDIAN,
        display_name="Parent A",
    )
    payer_b = BillingPayer.objects.create(
        school_id=school.id,
        household=household,
        guardian=guardian_b,
        account=parent_b,
        payer_type=BillingPayer.PayerType.GUARDIAN,
        display_name="Parent B",
    )
    invoice = _invoice(school, household)
    InvoicePayerShare.objects.create(
        school_id=school.id, invoice=invoice, payer=payer_a, amount=Decimal("600.00")
    )
    InvoicePayerShare.objects.create(
        school_id=school.id, invoice=invoice, payer=payer_b, amount=Decimal("400.00")
    )

    client = Client()
    client.force_login(parent_a)
    resp = client.get(
        "/api/v1/billing/my-payer-shares/",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )

    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["assigned_amount"] == "600.00"
    response_text = str(resp.json())
    assert "400.00" not in response_text
    assert "b@example.org" not in response_text


def test_payer_attribution_cannot_exceed_share_balance():
    school = School.objects.create(name="Payer Attribution School")
    household = Household.objects.create(school_id=school.id, name="Family")
    finance = _user(school, "finance_admin")
    payer = BillingPayer.objects.create(
        school_id=school.id,
        household=household,
        payer_type=BillingPayer.PayerType.THIRD_PARTY,
        display_name="Sponsor",
    )
    invoice = _invoice(school, household, Decimal("100.00"))
    account = LedgerAccount.objects.create(school_id=school.id, household=household)
    charge = Charge.objects.create(
        school_id=school.id,
        account=account,
        description="Tuition",
        amount=Decimal("100.00"),
    )
    invoice.ledger_charge_id = charge.id
    invoice.save(update_fields=["ledger_charge_id"])
    share = InvoicePayerShare.objects.create(
        school_id=school.id,
        invoice=invoice,
        payer=payer,
        amount=Decimal("60.00"),
    )
    payment = Payment.objects.create(
        school_id=school.id,
        account=account,
        amount=Decimal("100.00"),
        source="MANUAL",
        reference="payer-attr",
    )
    allocation = Allocation.objects.create(
        school_id=school.id,
        payment=payment,
        charge=charge,
        amount=Decimal("100.00"),
    )

    client = Client()
    client.force_login(finance)
    resp = client.post(
        "/api/v1/billing/payer-attributions/",
        data={
            "share_id": str(share.id),
            "allocation_id": str(allocation.id),
            "amount_cents": 7000,
        },
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert resp.status_code == 400
    assert PayerAllocationAttribution.objects.count() == 0

    ok = client.post(
        "/api/v1/billing/payer-attributions/",
        data={
            "share_id": str(share.id),
            "allocation_id": str(allocation.id),
            "amount_cents": 6000,
        },
        content_type="application/json",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )
    assert ok.status_code == 201
    assert PayerAllocationAttribution.objects.get().amount == Decimal("60.00")


@pytest.mark.parametrize("foreign_school", [False, True])
@pytest.mark.parametrize("foreign_field", ["guardian", "payer", "student"])
def test_finance_configuration_rejects_foreign_household_and_tenant(foreign_school, foreign_field):
    school = School.objects.create(name="Authority School")
    other_school = School.objects.create(name="Foreign School") if foreign_school else school
    household = Household.objects.create(school_id=school.id, name="Family")
    other = Household.objects.create(school_id=other_school.id, name="Other Family")
    client = Client()
    client.force_login(_user(school, "finance_admin"))
    payer = BillingPayer.objects.create(school_id=school.id, household=household, payer_type="THIRD_PARTY", display_name="Payer")
    before = BillingPayer.objects.count()
    if foreign_field == "guardian":
        guardian = Guardian.objects.create(school_id=other_school.id, household=other, first_name="Other", last_name="Guardian")
        path = f"/api/v1/billing/households/{household.id}/payers/"
        data = {"guardian_id": str(guardian.id)}
    else:
        path = f"/api/v1/billing/households/{household.id}/responsibility-rules/"
        data = {"payer_id": str(payer.id), "percentage_bps": 10000}
        if foreign_field == "payer":
            foreign = BillingPayer.objects.create(school_id=other_school.id, household=other, payer_type="THIRD_PARTY", display_name="Other Payer")
            before += 1
            data["payer_id"] = str(foreign.id)
        else:
            student = Student.objects.create(school_id=other_school.id, household=other, first_name="Other", last_name="Student")
            data["student_id"] = str(student.id)
    response = client.post(path, data=data, content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 400
    assert BillingPayer.objects.count() == before
    assert BillingResponsibilityRule.objects.count() == 0


def _paid_split():
    school = School.objects.create(name="Refund Privacy School")
    household = Household.objects.create(school_id=school.id, name="Family")
    account = LedgerAccount.objects.create(school_id=school.id, household=household)
    invoice = _invoice(school, household, Decimal("100.00"))
    charge = Charge.objects.create(school_id=school.id, account=account, description="Tuition", amount=Decimal("100.00"))
    invoice.ledger_charge_id = charge.id
    invoice.save(update_fields=["ledger_charge_id"])
    users, shares, payments = [], [], []
    for name, amount in [("A", "60.00"), ("B", "40.00")]:
        user = _user(school)
        Guardian.objects.create(school_id=school.id, household=household, account=user, email=user.email, first_name="Parent", last_name=name)
        payer = BillingPayer.objects.create(school_id=school.id, household=household, account=user, payer_type="THIRD_PARTY", display_name=f"Secret {name}", email=user.email)
        share = InvoicePayerShare.objects.create(school_id=school.id, invoice=invoice, payer=payer, amount=Decimal(amount))
        payment = Payment.objects.create(school_id=school.id, account=account, amount=Decimal(amount), source="MANUAL", reference=f"private-bank-{name}")
        allocation = Allocation.objects.create(school_id=school.id, payment=payment, charge=charge, amount=Decimal(amount))
        PayerAllocationAttribution.objects.create(school_id=school.id, allocation=allocation, share=share, amount=Decimal(amount))
        users.append(user)
        shares.append(share)
        payments.append(payment)
    return school, account, users, shares, payments


def _payer_items(user, school):
    client = Client()
    client.force_login(user)
    response = client.get("/api/v1/billing/my-payer-shares/", HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 200
    return response.json()["items"]


def test_payment_reversal_restores_only_original_payer_and_retains_history():
    from ledger.services import account_balance

    school, account, users, shares, payments = _paid_split()
    client = Client()
    client.force_login(_user(school, "finance_admin"))
    for _ in range(2):
        response = client.post(f"/api/v1/ledger/payments/{payments[0].id}/void/", HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200
    assert _payer_items(users[0], school)[0]["balance"] == "60.00"
    assert _payer_items(users[1], school)[0]["balance"] == "0.00"
    assert PayerAllocationAttribution.objects.count() == 2
    assert Allocation.objects.count() == 2
    assert account_balance(account) == Decimal("60.00")


@pytest.mark.parametrize("refund_cents", [2000, 6000])
def test_refund_restores_only_refunded_payer_without_duplicate_ar(refund_cents):
    from finance.models import FinancePayment, Processor, PaymentStatus
    from finance.services import initiate_refund
    from billing.models import PayerRefundAttribution
    from ledger.services import account_balance

    school, account, users, shares, payments = _paid_split()
    finance_payment = FinancePayment.objects.create(school=school, payer_user=users[0], amount_cents=6000, status=PaymentStatus.SETTLED)
    # Real finance bridge identity; monetary facts remain unchanged.
    Payment.objects.filter(pk=payments[0].pk).update(source="FINANCE_SETTLED", reference=f"finance_payment:{finance_payment.id}")
    initiate_refund(payment=finance_payment, amount_cents=refund_cents, processor=Processor.MANUAL)
    assert _payer_items(users[0], school)[0]["balance"] == f"{Decimal(refund_cents) / 100:.2f}"
    assert _payer_items(users[1], school)[0]["balance"] == "0.00"
    assert account_balance(account) == Decimal(refund_cents) / 100
    assert Charge.objects.count() == 2  # original invoice plus canonical refund debit
    assert PayerRefundAttribution.objects.get().amount == Decimal(refund_cents) / 100
    assert Invoice.objects.count() == 1
    assert InvoicePayerShare.objects.count() == 2


def test_payer_statement_and_notice_content_do_not_expose_copayer_facts():
    from billing.payer_services import payer_share_statement

    school, account, users, shares, payments = _paid_split()
    content = payer_share_statement(shares[0])
    assert content == _payer_items(users[0], school)[0]
    assert set(content) == {"share_id", "invoice_id", "term", "charge_type", "due_on", "assigned_amount", "waived_amount", "paid_amount", "balance"}
    for secret in [users[1].email, "Secret B", "private-bank-B", str(shares[1].id), str(payments[1].id)]:
        assert secret not in str(content)
    client = Client()
    client.force_login(users[0])
    statement = client.get(f"/api/v1/ledger/accounts/{account.id}/statement/", HTTP_X_SCHOOL_ID=str(school.id))
    assert statement.status_code == 403
    assert "private-bank-B" not in statement.content.decode()


def test_ambiguous_refund_fails_atomically_without_moving_copayer_responsibility():
    from django.core.exceptions import ValidationError
    from finance.models import FinancePayment, FinanceRefund, Processor, PaymentStatus
    from finance.services import initiate_refund
    from billing.models import PayerRefundAttribution

    school, account, users, shares, payments = _paid_split()
    finance_payment = FinancePayment.objects.create(school=school, payer_user=users[1], amount_cents=6000, status=PaymentStatus.SETTLED)
    Payment.objects.filter(pk=payments[0].pk).update(source="FINANCE_SETTLED", reference=f"finance_payment:{finance_payment.id}")
    with pytest.raises(ValidationError, match="Refund payer"):
        initiate_refund(payment=finance_payment, amount_cents=2000, processor=Processor.MANUAL)
    assert FinanceRefund.objects.count() == 0
    assert PayerRefundAttribution.objects.count() == 0
    assert Charge.objects.count() == 1
    assert _payer_items(users[0], school)[0]["balance"] == "0.00"
    assert _payer_items(users[1], school)[0]["balance"] == "0.00"


def test_refund_reversal_restores_paid_amount_and_prevents_double_payment_reversal():
    from finance.models import FinancePayment, Processor, PaymentStatus
    from finance.services import initiate_refund
    from billing.models import PayerRefundAttribution
    from ledger.services import account_balance

    school, account, users, shares, payments = _paid_split()
    finance_payment = FinancePayment.objects.create(school=school, payer_user=users[0], amount_cents=6000, status=PaymentStatus.SETTLED)
    Payment.objects.filter(pk=payments[0].pk).update(source="FINANCE_SETTLED", reference=f"finance_payment:{finance_payment.id}")
    initiate_refund(payment=finance_payment, amount_cents=2000, processor=Processor.MANUAL)
    refund_charge = PayerRefundAttribution.objects.get().refund_charge
    client = Client()
    client.force_login(_user(school, "finance_admin"))
    assert client.post(f"/api/v1/ledger/payments/{payments[0].id}/void/", HTTP_X_SCHOOL_ID=str(school.id)).status_code == 400
    assert client.post(f"/api/v1/ledger/charges/{refund_charge.id}/void/", HTTP_X_SCHOOL_ID=str(school.id)).status_code == 200
    assert _payer_items(users[0], school)[0]["balance"] == "0.00"
    assert account_balance(account) == Decimal("0.00")
    assert PayerRefundAttribution.objects.count() == 1


def test_notice_recipient_is_bound_to_payer_and_contains_no_copayer_facts():
    from django.core.exceptions import PermissionDenied
    from billing.payer_services import build_payer_billing_notice

    school, account, users, shares, payments = _paid_split()
    notice = build_payer_billing_notice(share=shares[0], recipient=users[0])
    assert notice["recipient_id"] == users[0].pk
    for secret in [users[1].email, "Secret B", "private-bank-B", str(shares[1].id)]:
        assert secret not in str(notice)
    with pytest.raises(PermissionDenied):
        build_payer_billing_notice(share=shares[0], recipient=users[1])


@pytest.mark.parametrize("foreign_school", [False, True])
def test_attribution_rejects_allocation_from_other_household_or_school(foreign_school):
    school, account, users, shares, payments = _paid_split()
    other_school = School.objects.create(name="Other Tenant") if foreign_school else school
    other_household = Household.objects.create(school_id=other_school.id, name="Other Household")
    other_account = LedgerAccount.objects.create(school_id=other_school.id, household=other_household)
    charge = Charge.objects.create(school_id=other_school.id, account=other_account, amount=Decimal("10.00"))
    payment = Payment.objects.create(school_id=other_school.id, account=other_account, amount=Decimal("10.00"))
    allocation = Allocation.objects.create(school_id=other_school.id, charge=charge, payment=payment, amount=Decimal("10.00"))
    client = Client()
    client.force_login(_user(school, "finance_admin"))
    response = client.post("/api/v1/billing/payer-attributions/", data={"share_id": str(shares[0].id), "allocation_id": str(allocation.id), "amount_cents": 100}, content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == (404 if foreign_school else 400)
    assert PayerAllocationAttribution.objects.count() == 2


def test_copayer_cannot_reverse_payment_or_invoice_charge():
    school, account, users, shares, payments = _paid_split()
    client = Client()
    client.force_login(users[1])
    for path in [f"/api/v1/ledger/payments/{payments[0].id}/void/", f"/api/v1/ledger/charges/{shares[0].invoice.ledger_charge_id}/void/"]:
        assert client.post(path, HTTP_X_SCHOOL_ID=str(school.id)).status_code == 403
    payments[0].refresh_from_db()
    assert payments[0].is_void is False
    assert _payer_items(users[0], school)[0]["balance"] == "0.00"
