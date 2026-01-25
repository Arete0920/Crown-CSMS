import uuid
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge


pytestmark = pytest.mark.django_db


def _mk_user_with_school_id(school_id):
    School.objects.get_or_create(id=school_id, defaults={"name": f"School-{school_id}"})
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school_id)
        u.save(update_fields=["school_id"])
    return u


def test_ensure_account_scoped_and_creates():
    school_a = uuid.uuid4()
    school_b = uuid.uuid4()

    hh_a = Household.objects.create(school_id=school_a, name="A Household")
    Household.objects.create(school_id=school_b, name="B Household")

    user = _mk_user_with_school_id(school_a)
    c = Client()
    c.force_login(user)

    resp = c.post(
        "/api/v1/ledger/accounts/ensure/",
        data={"household_id": str(hh_a.id)},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert LedgerAccount.objects.filter(household=hh_a, school_id=school_a).count() == 1


def test_create_charge_requires_account_and_scopes():
    school_a = uuid.uuid4()
    hh_a = Household.objects.create(school_id=school_a, name="A Household")
    acct = LedgerAccount.objects.create(school_id=school_a, household=hh_a)

    user = _mk_user_with_school_id(school_a)
    c = Client()
    c.force_login(user)

    resp = c.post(
        "/api/v1/ledger/charges/",
        data={"account_id": str(acct.id), "description": "Tuition", "amount": "100.00"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    assert Charge.objects.filter(account=acct).count() == 1
