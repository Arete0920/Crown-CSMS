from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounting.models import (
    AccountingDimension,
    Budget,
    BudgetLine,
    Fund,
    PayableBill,
    PayableBillLine,
    Vendor,
)
from apps.accounting.reports import balance_sheet, budget_vs_actual, income_statement, trial_balance
from apps.accounting.services.institutional import approve_payable_bill, post_payable_bill, void_payable_bill
from core.models import School, UserAccount
from journal.models import GLAccount, JournalEntry

pytestmark = pytest.mark.django_db


def _foundation():
    school = School.objects.create(name="Heritage Christian Academy")
    user = UserAccount.objects.create_user(
        username="finance",
        email="finance@example.test",
        password="test-pass",
        school=school,
    )
    expense = GLAccount.objects.create(
        school=school, code="6100", name="Instructional Supplies", account_type="EXPENSE"
    )
    payable = GLAccount.objects.create(
        school=school, code="2000", name="Accounts Payable", account_type="LIABILITY"
    )
    fund = Fund.objects.create(tenant_id=school.id, code="GENERAL", name="General Fund")
    department = AccountingDimension.objects.create(
        tenant_id=school.id,
        kind=AccountingDimension.Kind.DEPARTMENT,
        code="ACADEMICS",
        name="Academics",
    )
    vendor = Vendor.objects.create(
        tenant_id=school.id,
        code="V-001",
        legal_name="School Supply Company",
        default_expense_account=expense,
    )
    return school, user, expense, payable, fund, department, vendor


def _posted_bill():
    school, user, expense, payable, fund, department, vendor = _foundation()
    bill = PayableBill.objects.create(
        tenant_id=school.id,
        vendor=vendor,
        bill_number="INV-1001",
        bill_date=date(2026, 10, 1),
        due_date=date(2026, 10, 31),
        total_amount=Decimal("100.00"),
        liability_account=payable,
        created_by=user.id,
    )
    PayableBillLine.objects.create(
        tenant_id=school.id,
        bill=bill,
        description="Science lab supplies",
        amount=Decimal("100.00"),
        expense_account=expense,
        fund=fund,
        dimension=department,
    )
    bill = approve_payable_bill(bill=bill, actor_id=user.id)
    bill = post_payable_bill(bill=bill, created_by=user)
    return school, user, expense, payable, fund, department, vendor, bill


def test_vendor_rejects_cross_tenant_default_account():
    school = School.objects.create(name="School One")
    other = School.objects.create(name="School Two")
    other_expense = GLAccount.objects.create(
        school=other, code="6100", name="Supplies", account_type="EXPENSE"
    )

    with pytest.raises(ValidationError, match="same tenant"):
        Vendor.objects.create(
            tenant_id=school.id,
            code="V-001",
            legal_name="Wrong Tenant Vendor",
            default_expense_account=other_expense,
        )


def test_payable_bill_posts_balanced_dimensional_journal_and_reverses():
    _, _, _, _, _, _, _, bill = _posted_bill()

    assert bill.status == PayableBill.Status.POSTED
    assert bill.journal_entry_id is not None
    lines = list(bill.journal_entry.lines.all())
    assert sum((line.debit for line in lines), Decimal("0.00")) == Decimal("100.00")
    assert sum((line.credit for line in lines), Decimal("0.00")) == Decimal("100.00")
    expense_line = next(line for line in lines if line.debit == Decimal("100.00"))
    assert expense_line.fund_code == "GENERAL"
    assert expense_line.department_code == "ACADEMICS"

    bill = void_payable_bill(bill=bill, reason="Duplicate vendor invoice")
    assert bill.status == PayableBill.Status.VOID
    reversal = JournalEntry.objects.get(reversal_of=bill.journal_entry)
    reversed_expense = next(line for line in reversal.lines.all() if line.credit == Decimal("100.00"))
    assert reversed_expense.fund_code == "GENERAL"
    assert reversed_expense.department_code == "ACADEMICS"


def test_bill_approval_rejects_line_total_mismatch():
    school, user, expense, payable, _, _, vendor = _foundation()
    bill = PayableBill.objects.create(
        tenant_id=school.id,
        vendor=vendor,
        bill_number="INV-1002",
        bill_date=date(2026, 10, 1),
        due_date=date(2026, 10, 31),
        total_amount=Decimal("100.00"),
        liability_account=payable,
        created_by=user.id,
    )
    PayableBillLine.objects.create(
        tenant_id=school.id,
        bill=bill,
        description="Partial line",
        amount=Decimal("90.00"),
        expense_account=expense,
    )

    with pytest.raises(ValidationError, match="does not equal"):
        approve_payable_bill(bill=bill, actor_id=user.id)


def test_financial_statements_and_budget_actuals_derive_from_journal():
    school, _, expense, _, fund, department, _, _ = _posted_bill()

    budget = Budget.objects.create(
        tenant_id=school.id,
        name="FY 2026-27",
        fiscal_start=date(2026, 7, 1),
        fiscal_end=date(2027, 6, 30),
    )
    BudgetLine.objects.create(
        tenant_id=school.id,
        budget=budget,
        account=expense,
        fund=fund,
        dimension=department,
        amount=Decimal("120.00"),
    )

    tb = trial_balance(school_id=school.id, end_date=date(2026, 10, 31))
    assert tb["balanced"] is True
    assert tb["total_debit"] == Decimal("100.00")
    assert tb["total_credit"] == Decimal("100.00")

    pnl = income_statement(
        school_id=school.id,
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
    )
    assert pnl["expense_total"] == Decimal("100.00")
    assert pnl["net_income"] == Decimal("-100.00")

    bs = balance_sheet(school_id=school.id, as_of=date(2026, 10, 31))
    assert bs["liability_total"] == Decimal("100.00")
    assert bs["current_earnings"] == Decimal("-100.00")
    assert bs["difference"] == Decimal("0.00")

    variance = budget_vs_actual(budget=budget)
    assert variance["budget_total"] == Decimal("120.00")
    assert variance["actual_total"] == Decimal("100.00")
    assert variance["variance"] == Decimal("20.00")
