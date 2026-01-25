import uuid
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household, Student
from applications.models import Application, ApplicationStatus
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


def test_accept_creates_student_and_ledger_and_charge():
    school_id = uuid.uuid4()
    hh = Household.objects.create(school_id=school_id, name="Household")
    app = Application.objects.create(
        school_id=school_id,
        household=hh,
        status=ApplicationStatus.SUBMITTED,
    )

    # fake applicant
    app.applicants.create(
        school_id=school_id,
        first_name="John",
        last_name="Doe",
        grade_applying_for="5",
    )

    user = _mk_user_with_school_id(school_id)
    c = Client()
    c.force_login(user)

    resp = c.post(
        f"/api/v1/applications/{app.id}/decision/",
        data={
            "decision": "ACCEPT",
            "enrollment_fee": "250.00",
        },
        content_type="application/json",
    )
    assert resp.status_code == 200

    app.refresh_from_db()
    assert app.status == ApplicationStatus.DECIDED

    assert Student.objects.filter(household=hh).count() == 1
    acct = LedgerAccount.objects.get(household=hh)
    assert Charge.objects.filter(account=acct).count() == 1


def test_deny_creates_no_students_or_charges():
    school_id = uuid.uuid4()
    hh = Household.objects.create(school_id=school_id, name="Household")
    app = Application.objects.create(
        school_id=school_id,
        household=hh,
        status=ApplicationStatus.SUBMITTED,
    )

    app.applicants.create(
        school_id=school_id,
        first_name="Jane",
        last_name="Smith",
        grade_applying_for="3",
    )

    user = _mk_user_with_school_id(school_id)
    c = Client()
    c.force_login(user)

    resp = c.post(
        f"/api/v1/applications/{app.id}/decision/",
        data={"decision": "DENY"},
        content_type="application/json",
    )
    assert resp.status_code == 200

    assert Student.objects.count() == 0
    assert LedgerAccount.objects.count() == 0
    assert Charge.objects.count() == 0
