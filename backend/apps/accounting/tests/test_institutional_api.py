import json
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.accounting.models import Budget, PayableBill, PurchaseOrder
from core.models import School, UserAccount
from journal.models import GLAccount, JournalEntry

pytestmark = pytest.mark.django_db


def _school(name="Heritage Christian Academy"):
    return School.objects.create(name=name)


def _user(school, username, *, finance=True):
    user = UserAccount.objects.create_user(
        username=username,
        email=f"{username}@example.test",
        password="test-pass",
        school=school,
    )
    if finance:
        group, _ = Group.objects.get_or_create(name="finance_admin")
        user.groups.add(group)
    return user


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _post(client, url, body, school):
    return client.post(
        url,
        data=json.dumps(body),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )


def _get(client, url, school):
    return client.get(url, HTTP_X_SCHOOL_ID=str(school.id))


def _account(school, code, name, account_type):
    return GLAccount.objects.create(
        school=school,
        code=code,
        name=name,
        account_type=account_type,
    )


def _setup():
    school = _school()
    user = _user(school, "finance")
    expense = _account(school, "6100", "Instructional Supplies", "EXPENSE")
    payable = _account(school, "2000", "Accounts Payable", "LIABILITY")
    client = _client(user)

    fund = _post(
        client,
        "/api/accounting/funds/",
        {"code": "GENERAL", "name": "General Fund", "restriction": "UNRESTRICTED"},
        school,
    ).json()

    dimension = _post(
        client,
        "/api/accounting/dimensions/",
        {"kind": "DEPARTMENT", "code": "ACADEMICS", "name": "Academics"},
        school,
    ).json()

    vendor = _post(
        client,
        "/api/accounting/vendors/",
        {
            "code": "V-001",
            "legal_name": "School Supply Company",
            "default_expense_account_id": expense.id,
        },
        school,
    ).json()

    return school, user, client, expense, payable, fund, dimension, vendor


def test_accounting_api_requires_finance_role():
    school = _school()
    user = _user(school, "teacher", finance=False)

    response = _get(_client(user), "/api/accounting/vendors/", school)

    assert response.status_code == 403


def test_vendor_and_reference_data_are_tenant_scoped():
    school, _, client, expense, _, fund, dimension, vendor = _setup()
    other = _school("Other School")
    other_user = _user(other, "other-finance")
    other_client = _client(other_user)

    own = _get(client, "/api/accounting/vendors/", school)
    other_rows = _get(other_client, "/api/accounting/vendors/", other)

    assert own.status_code == 200
    assert [row["id"] for row in own.json()["results"]] == [vendor["id"]]
    assert other_rows.status_code == 200
    assert other_rows.json()["results"] == []
    assert fund["code"] == "GENERAL"
    assert dimension["code"] == "ACADEMICS"

    response = _post(
        other_client,
        "/api/accounting/vendors/",
        {
            "code": "BAD",
            "legal_name": "Cross Tenant Vendor",
            "default_expense_account_id": expense.id,
        },
        other,
    )
    assert response.status_code == 400


def test_purchase_order_lifecycle_is_exposed_without_payment_side_effects():
    school, _, client, expense, _, fund, dimension, vendor = _setup()
    create = _post(
        client,
        "/api/accounting/purchase-orders/",
        {
            "vendor_id": vendor["id"],
            "number": "PO-2026-0001",
            "ordered_on": "2026-10-01",
            "lines": [
                {
                    "description": "Classroom materials",
                    "quantity": "2.00",
                    "unit_cost": "25.00",
                    "account_id": expense.id,
                    "fund_id": fund["id"],
                    "dimension_id": dimension["id"],
                }
            ],
        },
        school,
    )
    assert create.status_code == 201
    po_id = create.json()["id"]
    assert create.json()["status"] == "DRAFT"

    submitted = _post(client, f"/api/accounting/purchase-orders/{po_id}/submit/", {}, school)
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "SUBMITTED"

    approved = _post(client, f"/api/accounting/purchase-orders/{po_id}/approve/", {}, school)
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert PurchaseOrder.objects.get(pk=po_id).approved_by is not None


def test_payable_bill_posts_canonical_journal_and_reports():
    school, _, client, expense, payable, fund, dimension, vendor = _setup()
    create = _post(
        client,
        "/api/accounting/bills/",
        {
            "vendor_id": vendor["id"],
            "bill_number": "INV-1001",
            "bill_date": "2026-10-01",
            "due_date": "2026-10-31",
            "total_amount": "100.00",
            "liability_account_id": payable.id,
            "lines": [
                {
                    "description": "Science supplies",
                    "amount": "100.00",
                    "expense_account_id": expense.id,
                    "fund_id": fund["id"],
                    "dimension_id": dimension["id"],
                }
            ],
        },
        school,
    )
    assert create.status_code == 201
    bill_id = create.json()["id"]

    approved = _post(client, f"/api/accounting/bills/{bill_id}/approve/", {}, school)
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    posted = _post(client, f"/api/accounting/bills/{bill_id}/post/", {}, school)
    assert posted.status_code == 200
    assert posted.json()["status"] == "POSTED"
    bill = PayableBill.objects.get(pk=bill_id)
    assert bill.journal_entry_id is not None

    trial = _get(client, "/api/accounting/reports/trial-balance/?end_date=2026-10-31", school)
    assert trial.status_code == 200
    assert trial.json()["balanced"] is True

    pnl = _get(
        client,
        "/api/accounting/reports/income-statement/?start_date=2026-07-01&end_date=2027-06-30",
        school,
    )
    assert pnl.status_code == 200
    assert Decimal(str(pnl.json()["expense_total"])) == Decimal("100.00")

    balance = _get(client, "/api/accounting/reports/balance-sheet/?as_of=2026-10-31", school)
    assert balance.status_code == 200
    assert Decimal(str(balance.json()["difference"])) == Decimal("0.00")


def test_bill_line_total_mismatch_cannot_be_approved():
    school, _, client, expense, payable, _, _, vendor = _setup()
    create = _post(
        client,
        "/api/accounting/bills/",
        {
            "vendor_id": vendor["id"],
            "bill_number": "INV-1002",
            "bill_date": "2026-10-01",
            "due_date": "2026-10-31",
            "total_amount": "100.00",
            "liability_account_id": payable.id,
            "lines": [
                {
                    "description": "Mismatch",
                    "amount": "90.00",
                    "expense_account_id": expense.id,
                }
            ],
        },
        school,
    )
    assert create.status_code == 201

    response = _post(client, f"/api/accounting/bills/{create.json()['id']}/approve/", {}, school)

    assert response.status_code == 400
    assert PayableBill.objects.get(pk=create.json()["id"]).status == PayableBill.Status.DRAFT


def test_cross_tenant_bill_action_returns_not_found():
    school, _, client, expense, payable, _, _, vendor = _setup()
    create = _post(
        client,
        "/api/accounting/bills/",
        {
            "vendor_id": vendor["id"],
            "bill_number": "INV-1003",
            "bill_date": "2026-10-01",
            "due_date": "2026-10-31",
            "total_amount": "10.00",
            "liability_account_id": payable.id,
            "lines": [{"description": "Item", "amount": "10.00", "expense_account_id": expense.id}],
        },
        school,
    )
    other = _school("Other")
    other_user = _user(other, "other")
    response = _post(
        _client(other_user),
        f"/api/accounting/bills/{create.json()['id']}/approve/",
        {},
        other,
    )
    assert response.status_code == 404


def test_budget_approval_and_variance_report_use_canonical_journal_actuals():
    school, _, client, expense, payable, fund, dimension, vendor = _setup()

    bill = _post(
        client,
        "/api/accounting/bills/",
        {
            "vendor_id": vendor["id"],
            "bill_number": "INV-BUDGET",
            "bill_date": "2026-10-01",
            "due_date": "2026-10-31",
            "total_amount": "100.00",
            "liability_account_id": payable.id,
            "lines": [
                {
                    "description": "Budget actual",
                    "amount": "100.00",
                    "expense_account_id": expense.id,
                    "fund_id": fund["id"],
                    "dimension_id": dimension["id"],
                }
            ],
        },
        school,
    ).json()
    _post(client, f"/api/accounting/bills/{bill['id']}/approve/", {}, school)
    _post(client, f"/api/accounting/bills/{bill['id']}/post/", {}, school)

    budget = _post(
        client,
        "/api/accounting/budgets/",
        {
            "name": "FY 2026-27",
            "fiscal_start": "2026-07-01",
            "fiscal_end": "2027-06-30",
            "lines": [
                {
                    "account_id": expense.id,
                    "fund_id": fund["id"],
                    "dimension_id": dimension["id"],
                    "amount": "120.00",
                }
            ],
        },
        school,
    )
    assert budget.status_code == 201
    budget_id = budget.json()["id"]

    approved = _post(client, f"/api/accounting/budgets/{budget_id}/approve/", {}, school)
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert Budget.objects.get(pk=budget_id).approved_by is not None

    variance = _get(
        client,
        f"/api/accounting/reports/budgets/{budget_id}/variance/",
        school,
    )
    assert variance.status_code == 200
    assert Decimal(str(variance.json()["budget_total"])) == Decimal("120.00")
    assert Decimal(str(variance.json()["actual_total"])) == Decimal("100.00")
    assert Decimal(str(variance.json()["variance"])) == Decimal("20.00")


def test_void_posted_bill_creates_reversal_not_delete():
    school, _, client, expense, payable, _, _, vendor = _setup()
    bill = _post(
        client,
        "/api/accounting/bills/",
        {
            "vendor_id": vendor["id"],
            "bill_number": "INV-VOID",
            "bill_date": "2026-10-01",
            "due_date": "2026-10-31",
            "total_amount": "25.00",
            "liability_account_id": payable.id,
            "lines": [{"description": "Void me", "amount": "25.00", "expense_account_id": expense.id}],
        },
        school,
    ).json()
    _post(client, f"/api/accounting/bills/{bill['id']}/approve/", {}, school)
    posted = _post(client, f"/api/accounting/bills/{bill['id']}/post/", {}, school).json()

    response = _post(
        client,
        f"/api/accounting/bills/{bill['id']}/void/",
        {"reason": "Duplicate invoice"},
        school,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "VOID"
    assert JournalEntry.objects.filter(reversal_of_id=posted["journal_entry_id"]).exists()
