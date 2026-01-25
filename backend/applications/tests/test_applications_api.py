import uuid
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household
from applications.models import Application, ApplicationStatus


pytestmark = pytest.mark.django_db


def _mk_user_with_school_id(school_id):
    User = get_user_model()
    school, _ = School.objects.get_or_create(
        id=school_id,
        defaults={"name": f"School-{school_id}"},
    )
    u = User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=f"user-{uuid.uuid4()}@example.com",
        password="pass12345!",
        school=school,
    )
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school_id)
        u.save(update_fields=["school_id"])
    return u


def test_applications_list_is_scoped_no_leak():
    school_a = uuid.uuid4()
    school_b = uuid.uuid4()

    hh_a = Household.objects.create(school_id=school_a, name="A Household")
    hh_b = Household.objects.create(school_id=school_b, name="B Household")

    Application.objects.create(school_id=school_a, household=hh_a)
    Application.objects.create(school_id=school_b, household=hh_b)

    user = _mk_user_with_school_id(school_a)
    c = Client()
    c.force_login(user)

    resp = c.get("/api/v1/applications/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert len(body["data"]) == 1


def test_application_create_sets_school_and_is_draft():
    school_a = uuid.uuid4()
    hh_a = Household.objects.create(school_id=school_a, name="A Household")

    user = _mk_user_with_school_id(school_a)
    c = Client()
    c.force_login(user)

    resp = c.post(
        "/api/v1/applications/",
        data={"household_id": str(hh_a.id)},
        content_type="application/json",
    )
    assert resp.status_code == 201
    app = Application.objects.get(id=resp.json()["data"]["id"])
    assert app.school_id == school_a
    assert app.status == ApplicationStatus.DRAFT


def test_application_submit_transitions_and_sets_timestamp():
    school_a = uuid.uuid4()
    hh_a = Household.objects.create(school_id=school_a, name="A Household")
    app = Application.objects.create(school_id=school_a, household=hh_a, status=ApplicationStatus.DRAFT)

    user = _mk_user_with_school_id(school_a)
    c = Client()
    c.force_login(user)

    resp = c.post(f"/api/v1/applications/{app.id}/submit/", data={}, content_type="application/json")
    assert resp.status_code == 200
    app.refresh_from_db()
    assert app.status == ApplicationStatus.SUBMITTED
    assert app.submitted_at is not None
