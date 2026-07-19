import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School, UserRole
from households.models import Household

TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"


@pytest.mark.django_db
def test_school_override_header_ignored_for_nonstaff_user():
    school_a = School.objects.create(name="School A", timezone="America/New_York", is_active=True)
    school_b = School.objects.create(name="School B", timezone="America/New_York", is_active=True)

    hh_b = Household.objects.create(school_id=school_b.id, name="HH B")

    user_model = get_user_model()
    u = user_model.objects.create_user(username="u1", password=TEST_AUTH_SECRET, school=school_a)

    client = APIClient()
    client.force_authenticate(user=u)

    resp = client.get(
        f"/api/billing/households/{hh_b.id}/open-invoices/",
        HTTP_X_CROWN_SCHOOL_ID=str(school_b.id),
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_school_override_header_denies_ordinary_staff_user_switch():
    school_a = School.objects.create(name="School A", timezone="America/New_York", is_active=True)
    school_b = School.objects.create(name="School B", timezone="America/New_York", is_active=True)

    hh_b = Household.objects.create(school_id=school_b.id, name="HH B")

    user_model = get_user_model()
    u = user_model.objects.create_user(
        username="staff1",
        password=TEST_AUTH_SECRET,
        school=school_a,
        is_staff=True,
    )

    client = APIClient()
    client.force_authenticate(user=u)

    resp = client.get(
        f"/api/billing/households/{hh_b.id}/open-invoices/",
        HTTP_X_CROWN_SCHOOL_ID=str(school_b.id),
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_school_override_header_allows_support_user_switch():
    school_a = School.objects.create(name="School A", timezone="America/New_York", is_active=True)
    school_b = School.objects.create(name="School B", timezone="America/New_York", is_active=True)

    hh_b = Household.objects.create(school_id=school_b.id, name="HH B")

    user_model = get_user_model()
    u = user_model.objects.create_user(
        username="support1",
        password=TEST_AUTH_SECRET,
        school=school_a,
        is_staff=True,
    )
    UserRole.objects.create(user=u, school=school_a, role_code="SUPPORT")

    client = APIClient()
    client.force_authenticate(user=u)

    resp = client.get(
        f"/api/billing/households/{hh_b.id}/open-invoices/",
        HTTP_X_CROWN_SCHOOL_ID=str(school_b.id),
    )
    assert resp.status_code == 200
    assert resp.data["household_id"] == str(hh_b.id)


@pytest.mark.django_db
def test_school_override_header_invalid_uuid_is_400_for_staff():
    school = School.objects.create(name="School A", timezone="America/New_York", is_active=True)
    hh = Household.objects.create(school_id=school.id, name="HH")

    user_model = get_user_model()
    u = user_model.objects.create_user(
        username="staff2",
        password=TEST_AUTH_SECRET,
        school=school,
        is_staff=True,
    )

    client = APIClient()
    client.force_authenticate(user=u)

    resp = client.get(
        f"/api/billing/households/{hh.id}/open-invoices/",
        HTTP_X_CROWN_SCHOOL_ID="not-a-uuid",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_school_override_header_school_not_found_is_404_for_staff():
    school = School.objects.create(name="School A", timezone="America/New_York", is_active=True)
    hh = Household.objects.create(school_id=school.id, name="HH")

    missing = uuid.uuid4()

    user_model = get_user_model()
    u = user_model.objects.create_user(
        username="staff3",
        password=TEST_AUTH_SECRET,
        school=school,
        is_staff=True,
    )

    client = APIClient()
    client.force_authenticate(user=u)

    resp = client.get(
        f"/api/billing/households/{hh.id}/open-invoices/",
        HTTP_X_CROWN_SCHOOL_ID=str(missing),
    )
    assert resp.status_code == 404
