import csv
import io
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.utils import timezone

from aid.models import AidAward
from billing.models import BillingRun, Invoice
from core.models import AcademicYear, Family, School, Student
from households.models import Household
from journal.models import GLAccount, JournalEntry, JournalLine
from payments.authority_services import create_payment
from payments.models import (
    BankStatementEntry,
    BankStatementImport,
    CanonicalPaymentStatus,
    CanonicalRefundStatus,
    ProviderPayoutBatch,
    Refund,
)


pytestmark = pytest.mark.django_db


def _user(school, *, finance=False):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"finance-export-{uuid.uuid4()}",
        password="pass12345!",
        is_staff=finance,
    )
    if hasattr(user, "school_id"):
        user.school_id = school.id
        user.save(update_fields=["school_id"])
    group, _ = Group.objects.get_or_create(name="finance_admin" if finance else "parent")
    user.groups.add(group)
    return user


def _rows(response):
    text = b"".join(response.streaming_content).decode() if getattr(response, "streaming", False) else response.content.decode()
    return list(csv.DictReader(io.StringIO(text)))


def test_finance_handoff_export_is_school_scoped_and_reconciles_all_major_sections():
    school = School.objects.create(name="Finance Export School")
    foreign_school = School.objects.create(name="Foreign Finance Export School")
    user = _user(school, finance=True)
    household = Household.objects.create(school_id=school.id, name="Export Household")

    settled = create_payment(
        school_id=school.id,
        household_id=household.id,
        amount_cents=12_345,
        idempotency_key="export-settled-payment",
    )
    settled.status = CanonicalPaymentStatus.SETTLED
    settled.settled_at = timezone.now()
    settled.save(update_fields=["status", "settled_at", "updated_at"])

    pending = create_payment(
        school_id=school.id,
        household_id=household.id,
        amount_cents=5_000,
        idempotency_key="export-pending-payment",
    )
    foreign = create_payment(
        school_id=foreign_school.id,
        amount_cents=99_999,
        idempotency_key="export-foreign-payment",
    )
    foreign.status = CanonicalPaymentStatus.SETTLED
    foreign.settled_at = timezone.now()
    foreign.save(update_fields=["status", "settled_at", "updated_at"])

    refund = Refund.objects.create(
        school_id=school.id,
        payment=settled,
        amount_cents=2_345,
        currency="USD",
        status=CanonicalRefundStatus.SETTLED,
        idempotency_key="export-settled-refund",
        settled_at=timezone.now(),
    )

    billing_run = BillingRun.objects.create(
        school_id=school.id,
        term="2026-FALL",
        run_type="TUITION",
        description="Export reconciliation tuition",
        amount_per_student=Decimal("400.00"),
    )
    invoice = Invoice.objects.create(
        school_id=school.id,
        billing_run=billing_run,
        household=household,
        total_amount=Decimal("400.00"),
        due_on=date.today() - timedelta(days=45),
    )

    debit_account = GLAccount.objects.create(
        school=school,
        code="1100",
        name="Accounts Receivable",
        account_type="ASSET",
    )
    credit_account = GLAccount.objects.create(
        school=school,
        code="4100",
        name="Tuition Revenue",
        account_type="REVENUE",
    )
    entry = JournalEntry.objects.create(
        school=school,
        created_by=user,
        posting_date=date.today(),
        memo="Finance export proof",
        locked=False,
        reference_type="export_proof",
        reference_id=invoice.id,
        currency="USD",
    )
    JournalLine.objects.create(entry=entry, account=debit_account, debit=Decimal("400.00"), credit=Decimal("0.00"))
    JournalLine.objects.create(entry=entry, account=credit_account, debit=Decimal("0.00"), credit=Decimal("400.00"))

    year = AcademicYear.objects.create(
        school=school,
        name="2026-27",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 5, 31),
    )
    family = Family.objects.create(school=school, family_name="Export Family")
    student = Student.objects.create(
        school=school,
        family=family,
        student_number="EXPORT-001",
        first_name="Jordan",
        last_name="Export",
        dob=date(2012, 4, 5),
    )
    award = AidAward.objects.create(
        school=school,
        academic_year=year,
        student=student,
        award_type=AidAward.TYPE_NEED,
        awarded_cents=25_000,
        decision_status=AidAward.DECISION_ACCEPTED,
        decided_at=timezone.now(),
    )

    payout = ProviderPayoutBatch.objects.create(
        school_id=school.id,
        provider="compuwerx",
        payout_id="export-payout-1",
        status="settled",
        gross_amount=Decimal("100.00"),
        fee_amount=Decimal("2.00"),
        net_amount=Decimal("98.00"),
        currency="USD",
        expected_payment_count=1,
        settled_at=timezone.now(),
    )
    statement_import = BankStatementImport.objects.create(
        school_id=school.id,
        source_name="export-bank.csv",
        source_sha256="b" * 64,
        status="processed",
        row_count=1,
    )
    bank_entry = BankStatementEntry.objects.create(
        school_id=school.id,
        statement_import=statement_import,
        posted_date=date.today(),
        description="Provider deposit",
        reference="export-payout-1",
        amount=Decimal("98.00"),
        currency="USD",
        is_matched=True,
    )

    client = Client()
    client.force_login(user)
    response = client.get(
        "/api/v1/payments/exports/finance-handoff.csv",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )

    assert response.status_code == 200
    rows = _rows(response)
    sections = {row["section"] for row in rows}
    assert {
        "payment_register",
        "refund_register",
        "ar_aging",
        "general_ledger",
        "aid_credit",
        "deposit_reconciliation",
        "bank_statement",
        "control_total",
        "control_assertion",
    }.issubset(sections)

    payment_rows = [row for row in rows if row["section"] == "payment_register"]
    assert {row["record_id"] for row in payment_rows} == {str(settled.id), str(pending.id)}
    assert str(foreign.id) not in {row["record_id"] for row in rows}
    assert any(row["record_id"] == str(refund.id) for row in rows if row["section"] == "refund_register")
    assert any(row["record_id"] == str(invoice.id) for row in rows if row["section"] == "ar_aging")
    assert any(row["record_id"] == str(entry.id) for row in rows if row["section"] == "general_ledger")
    assert any(row["record_id"] == str(award.id) for row in rows if row["section"] == "aid_credit")
    assert any(row["record_id"] == str(payout.id) for row in rows if row["section"] == "deposit_reconciliation")
    assert any(row["record_id"] == str(bank_entry.id) for row in rows if row["section"] == "bank_statement")

    totals = {
        row["record_id"]: row["amount"]
        for row in rows
        if row["section"] == "control_total"
    }
    assert totals["canonical_payment_total"] == "123.45"
    assert totals["settled_refund_total"] == "23.45"
    assert totals["net_canonical_cash"] == "100.00"
    assert totals["ar_outstanding_total"] == "400.00"
    assert totals["ar_31-60"] == "400.00"
    assert totals["journal_debit_total"] == "400.00"
    assert totals["journal_credit_total"] == "400.00"
    assert totals["accepted_aid_total"] == "250.00"

    journal_control = next(
        row for row in rows
        if row["section"] == "control_assertion" and row["record_id"] == "journal_balanced"
    )
    assert journal_control["status"] == "PASS"
    assert journal_control["debit"] == "400.00"
    assert journal_control["credit"] == "400.00"


def test_finance_handoff_export_rejects_nonfinance_role():
    school = School.objects.create(name="Finance Export Access School")
    user = _user(school, finance=False)
    client = Client()
    client.force_login(user)

    response = client.get(
        "/api/v1/payments/exports/finance-handoff.csv",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )

    assert response.status_code == 403
