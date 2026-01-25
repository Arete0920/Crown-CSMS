import uuid
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment


pytestmark = pytest.mark.django_db


def _mk_user_with_school(school: School):
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


def test_payment_allocation_fifo_and_balances():
    school = School.objects.create(name="Test School")
    hh = Household.objects.create(school_id=school.id, name="Household")
    acct = LedgerAccount.objects.create(school_id=school.id, household=hh)

    # Two charges: 1000 + 500
    ch1 = Charge.objects.create(school_id=school.id, account=acct, description="Tuition A", amount=Decimal("1000.00"))
    ch2 = Charge.objects.create(school_id=school.id, account=acct, description="Tuition B", amount=Decimal("500.00"))

    # One payment: 1200
    pay = Payment.objects.create(school_id=school.id, account=acct, amount=Decimal("1200.00"))

    user = _mk_user_with_school(school)
    c = Client()
    c.force_login(user)

    # allocate
    resp = c.post(f"/api/v1/ledger/payments/{pay.id}/allocate/", data={}, content_type="application/json")
    assert resp.status_code == 200

    # charge balances
    resp = c.get(f"/api/v1/ledger/charges/{ch1.id}/balance/")
    assert resp.status_code == 200
    assert Decimal(resp.json()["data"]["remaining_balance"]) == Decimal("0.00")

    resp = c.get(f"/api/v1/ledger/charges/{ch2.id}/balance/")
    assert resp.status_code == 200
    assert Decimal(resp.json()["data"]["remaining_balance"]) == Decimal("300.00")

    # account balance = 1500 - 1200 = 300
    resp = c.get(f"/api/v1/ledger/accounts/{acct.id}/balance/")
    assert resp.status_code == 200
    assert Decimal(resp.json()["data"]["balance"]) == Decimal("300.00")
