import uuid
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment
from ledger.models import Allocation as PaymentAllocation

pytestmark = pytest.mark.django_db

TEST_AUTH_SECRET = "testpass"


def _mk_user_with_school(school: School):
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password=TEST_AUTH_SECRET)
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


def test_account_statement_running_balance():
    school = School.objects.create(name="Test School")
    hh = Household.objects.create(school_id=school.id, name="Household")
    acct = LedgerAccount.objects.create(school_id=school.id, household=hh)

    ch1 = Charge.objects.create(school_id=school.id, account=acct, description="Tuition", amount=Decimal("1000.00"))
    ch2 = Charge.objects.create(school_id=school.id, account=acct, description="Fee", amount=Decimal("200.00"))

    # Aid payment allocation (400)
    aid = Payment.objects.create(school_id=school.id, account=acct, amount=Decimal("400.00"), source="FINANCIAL_AID", reference="award:x")
    PaymentAllocation.objects.create(school_id=school.id, payment=aid, charge=ch1, amount=Decimal("400.00"))

    # External payment allocation (300)
    pay = Payment.objects.create(school_id=school.id, account=acct, amount=Decimal("300.00"), source="EXTERNAL", reference="rcpt:1")
    PaymentAllocation.objects.create(school_id=school.id, payment=pay, charge=ch1, amount=Decimal("300.00"))

    user = _mk_user_with_school(school)
    c = Client()
    c.force_login(user)

    resp = c.get(f"/api/v1/ledger/accounts/{acct.id}/statement/")
    assert resp.status_code == 200

    data = resp.json()["data"]
    # Balance = (1000 + 200) - (400 + 300) = 500
    assert Decimal(data["balance"]) == Decimal("500.00")

    # Entries exist and have running_balance
    assert len(data["entries"]) >= 4
    assert "running_balance" in data["entries"][-1]

