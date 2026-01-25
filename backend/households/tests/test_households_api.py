import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School
from households.models import Household, Guardian, Student


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
    # Attach school_id if the model supports it
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school_id)
        u.save(update_fields=["school_id"])
    return u


def test_households_list_is_scoped_no_leak():
    school_a = uuid.uuid4()
    school_b = uuid.uuid4()

    hh_a = Household.objects.create(school_id=school_a, name="Megahan Household")
    Household.objects.create(school_id=school_b, name="Other School Household")

    user = _mk_user_with_school_id(school_a)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/v1/households/")
    assert resp.status_code == 200
    ids = [row["id"] for row in resp.json()]
    assert str(hh_a.id) in ids
    assert len(ids) == 1


def test_household_retrieve_is_scoped_forbidden_by_empty_result():
    school_a = uuid.uuid4()
    school_b = uuid.uuid4()

    hh_b = Household.objects.create(school_id=school_b, name="Other School Household")

    user = _mk_user_with_school_id(school_a)
    client = APIClient()
    client.force_authenticate(user=user)

    # ReadOnlyModelViewSet returns 404 when not in queryset — which is what we want for no-leak.
    resp = client.get(f"/api/v1/households/{hh_b.id}/")
    assert resp.status_code == 404


def test_household_nested_entities_return_and_are_scoped():
    school_a = uuid.uuid4()

    hh = Household.objects.create(school_id=school_a, name="Heritage Household")
    Guardian.objects.create(
        school_id=school_a,
        household=hh,
        first_name="Joanne",
        last_name="Megahan",
        email="joanne@example.com",
        phone="555-1111",
        is_primary=True,
    )
    Student.objects.create(
        school_id=school_a,
        household=hh,
        first_name="TC",
        last_name="Megahan",
        grade_level="12",
        is_active=True,
    )

    user = _mk_user_with_school_id(school_a)
    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get(f"/api/v1/households/{hh.id}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Heritage Household"
    assert len(data["guardians"]) == 1
    assert len(data["students"]) == 1
