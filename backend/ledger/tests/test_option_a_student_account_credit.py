import uuid
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from households.models import Household
from ledger.models import Charge, Credit, LedgerAccount
from ledger.services import account_balance, build_account_statement, post_account_credit, void_account_credit


pytestmark = pytest.mark.django_db


def _account(school_id):
    household = Household.objects.create(school_id=school_id, name=f"HH-{uuid.uuid4()}")
    return LedgerAccount.objects.create(school_id=school_id, household=household)


def test_credit_reduces_receivable_without_creating_payment():
    school_id = uuid.uuid4()
    account = _account(school_id)
    Charge.objects.create(
        school_id=school_id,
        account=account,
        description="Tuition",
        amount=Decimal("1000.00"),
    )

    credit = post_account_credit(
        school_id=school_id,
        account=account,
        amount=Decimal("250.00"),
        source=Credit.SOURCE_FINANCIAL_AID,
        reference=f"aid_award:{uuid.uuid4()}",
        description="Financial Aid Award",
    )

    assert credit.amount == Decimal("250.00")
    assert account_balance(account) == Decimal("750.00")
    assert account.payments.count() == 0
    statement = build_account_statement(school_id=school_id, account=account)
    assert [entry["type"] for entry in statement["entries"]] == ["CHARGE", "CREDIT"]
    assert statement["balance"] == "750.00"


def test_credit_reference_is_idempotent_and_fails_on_changed_financial_facts():
    school_id = uuid.uuid4()
    account = _account(school_id)
    reference = f"aid_award:{uuid.uuid4()}"

    first = post_account_credit(
        school_id=school_id,
        account=account,
        amount=Decimal("100.00"),
        source=Credit.SOURCE_FINANCIAL_AID,
        reference=reference,
    )
    second = post_account_credit(
        school_id=school_id,
        account=account,
        amount=Decimal("100.00"),
        source=Credit.SOURCE_FINANCIAL_AID,
        reference=reference,
    )

    assert first.id == second.id
    assert Credit.objects.filter(school_id=school_id, source=Credit.SOURCE_FINANCIAL_AID, reference=reference).count() == 1

    with pytest.raises(ValidationError, match="different financial facts"):
        post_account_credit(
            school_id=school_id,
            account=account,
            amount=Decimal("101.00"),
            source=Credit.SOURCE_FINANCIAL_AID,
            reference=reference,
        )


def test_credit_cannot_cross_tenants_or_be_deleted_and_void_is_idempotent():
    school_id = uuid.uuid4()
    other_school_id = uuid.uuid4()
    account = _account(school_id)

    with pytest.raises(ValidationError, match="school mismatch"):
        post_account_credit(
            school_id=other_school_id,
            account=account,
            amount=Decimal("10.00"),
            source=Credit.SOURCE_ADJUSTMENT,
            reference=f"adjustment:{uuid.uuid4()}",
        )

    credit = post_account_credit(
        school_id=school_id,
        account=account,
        amount=Decimal("10.00"),
        source=Credit.SOURCE_ADJUSTMENT,
        reference=f"adjustment:{uuid.uuid4()}",
    )
    with pytest.raises(ValidationError, match="cannot be deleted"):
        credit.delete()

    first = void_account_credit(credit=credit)
    second = void_account_credit(credit=credit)
    assert first.is_void is True
    assert second.is_void is True
