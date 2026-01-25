import uuid
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from households.models import Household
from core.models import School
from financial_aid.models import AidApplication, AidStatus, AidAward, AwardStatus


pytestmark = pytest.mark.django_db


def _mk_user_with_school(school: School):
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


def test_aid_flow_submit_decide_disburse():
    school = School.objects.create(name="Test School")
    hh = Household.objects.create(school_id=school.id, name="Household")

    user = _mk_user_with_school(school)
    c = Client()
    c.force_login(user)

    # create application
    resp = c.post(
        "/api/v1/financial-aid/applications/",
        data={"household_id": str(hh.id), "academic_year": "2026-2027"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    app_id = resp.json()["data"]["id"]

    # submit
    resp = c.post(f"/api/v1/financial-aid/applications/{app_id}/submit/", data={}, content_type="application/json")
    assert resp.status_code == 200
    assert AidApplication.objects.get(id=app_id).status == AidStatus.SUBMITTED

    # decide approve
    resp = c.post(
        f"/api/v1/financial-aid/applications/{app_id}/decide/",
        data={"decision": "APPROVE", "amount_annual": "1500.00"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    award_id = resp.json()["data"]["award"]["id"]
    award = AidAward.objects.get(id=award_id)
    assert award.status == AwardStatus.APPROVED

    # disburse
    resp = c.post(
        f"/api/v1/financial-aid/awards/{award_id}/disburse/",
        data={"amount": "500.00", "disbursed_on": "2026-09-01"},
        content_type="application/json",
    )
    assert resp.status_code == 201
