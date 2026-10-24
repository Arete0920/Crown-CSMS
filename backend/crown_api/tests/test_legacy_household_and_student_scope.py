"""School/household isolation for legacy read-only student and household routes.

All fixtures are synthetic. Test both selected-school staff and persisted
guardian links; never use email matching as household identity proof.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from core.models import Family, HouseholdFamilyLink, School
from crown_api.models import (
    Household, HouseholdMember, Person, Student, UserPersonLink,
)
from crown_api.models_households import ROLE_AUTHORIZED_PICKUP, ROLE_GUARDIAN


@pytest.fixture(autouse=True)
def strict_tenant(settings):
    settings.TENANT_HEADER_REQUIRED = True
    settings.CROWN_DEV_OPEN_API = False
    settings.CROWN_ENV = "development"


@pytest.fixture
def scope(db):
    a = School.objects.create(name="Synthetic Legacy Scope A")
    b = School.objects.create(name="Synthetic Legacy Scope B")
    fa = Family.objects.create(school=a, family_name="Synthetic Family A")
    fb = Family.objects.create(school=b, family_name="Synthetic Family B")
    ha = Household.objects.create(household_name="Synthetic Household A")
    hb = Household.objects.create(household_name="Synthetic Household B")
    for school, household, family in ((a, ha, fa), (b, hb, fb)):
        HouseholdFamilyLink.objects.create(
            school=school, household_id=household.pk, family=family,
            source=HouseholdFamilyLink.SOURCE_MANUAL,
        )
    pa = Person.objects.create(first_name="Child", last_name="A")
    pb = Person.objects.create(first_name="Child", last_name="B")
    sa = Student.objects.create(person=pa, household=ha, grade_level="5")
    sb = Student.objects.create(person=pb, household=hb, grade_level="6")
    Account = get_user_model()
    staff = Account.objects.create_user(
        username="synthetic-legacy-staff-a", email="synthetic-legacy-staff-a@example.invalid",
        school=a, is_staff=True,
    )
    guardian = Account.objects.create_user(
        username="synthetic-legacy-guardian-a", email="synthetic-legacy-guardian-a@example.invalid",
        school=a,
    )
    person = Person.objects.create(first_name="Guardian", last_name="A")
    UserPersonLink.objects.create(user=guardian, person=person)
    HouseholdMember.objects.create(
        household=ha, person=person, role=ROLE_GUARDIAN, is_primary=True,
    )
    pickup = Account.objects.create_user(
        username="synthetic-legacy-pickup-a", email="synthetic-legacy-pickup-a@example.invalid",
        school=a,
    )
    pickup_person = Person.objects.create(first_name="Pickup", last_name="A")
    UserPersonLink.objects.create(user=pickup, person=pickup_person)
    HouseholdMember.objects.create(
        household=ha, person=pickup_person, role=ROLE_AUTHORIZED_PICKUP,
    )
    return {
        "a": a, "b": b, "fa": fa, "fb": fb, "ha": ha, "hb": hb,
        "sa": sa, "sb": sb, "staff": staff, "guardian": guardian,
        "pickup": pickup,
    }


def _client(user):
    client = APIClient()
    client.force_login(user)
    return client


@pytest.mark.parametrize("endpoint,key", [
    ("/api/households/", "ha"),
    ("/api/students/", "sa"),
])
def test_staff_list_is_limited_to_selected_school(scope, endpoint, key):
    response = _client(scope["staff"]).get(
        endpoint, HTTP_X_SCHOOL_ID=str(scope["a"].pk),
    )
    assert response.status_code == 200, response.content[:250]
    rows = response.json()
    field = "id" if key == "ha" else "student_id"
    assert [str(row[field]) for row in rows] == [str(scope[key].pk)]
    assert str(scope["hb"].pk) not in str(response.content)
    assert str(scope["sb"].pk) not in str(response.content)


@pytest.mark.parametrize("endpoint,foreign", [
    ("/api/households/{id}/", "hb"),
    ("/api/students/{id}/", "sb"),
])
def test_staff_foreign_detail_and_header_denied(scope, endpoint, foreign):
    client = _client(scope["staff"])
    url = endpoint.format(id=scope[foreign].pk)
    selected = client.get(url, HTTP_X_SCHOOL_ID=str(scope["a"].pk))
    assert selected.status_code == 404
    wrong_header = client.get(url, HTTP_X_SCHOOL_ID=str(scope["b"].pk))
    assert wrong_header.status_code == 404


@pytest.mark.parametrize("endpoint,key", [
    ("/api/households/", "ha"),
    ("/api/students/", "sa"),
])
def test_verified_guardian_only_sees_own_school_records(scope, endpoint, key):
    response = _client(scope["guardian"]).get(
        endpoint, HTTP_X_SCHOOL_ID=str(scope["a"].pk),
    )
    assert response.status_code == 200, response.content[:250]
    field = "id" if key == "ha" else "student_id"
    assert [str(row[field]) for row in response.json()] == [str(scope[key].pk)]
    denied = _client(scope["pickup"]).get(
        endpoint, HTTP_X_SCHOOL_ID=str(scope["a"].pk),
    )
    assert denied.status_code == 200
    assert denied.json() == []


def test_ambiguous_cross_school_household_rejected_for_staff_and_guardian(scope):
    HouseholdFamilyLink.objects.create(
        school=scope["b"], household_id=scope["ha"].pk,
        family=scope["fb"], source=HouseholdFamilyLink.SOURCE_MANUAL,
    )
    for user in (scope["staff"], scope["guardian"]):
        client = _client(user)
        for url in (
            "/api/households/",
            "/api/students/",
        ):
            response = client.get(url, HTTP_X_SCHOOL_ID=str(scope["a"].pk))
            assert response.status_code == 200
            assert response.json() == []
        for url in (
            f"/api/households/{scope['ha'].pk}/",
            f"/api/students/{scope['sa'].pk}/",
        ):
            assert client.get(
                url, HTTP_X_SCHOOL_ID=str(scope["a"].pk)
            ).status_code == 404


def test_missing_verified_user_person_link_fails_closed(scope):
    UserPersonLink.objects.filter(user=scope["guardian"]).delete()
    client = _client(scope["guardian"])
    for url in ("/api/households/", "/api/students/"):
        response = client.get(url, HTTP_X_SCHOOL_ID=str(scope["a"].pk))
        assert response.status_code == 200
        assert response.json() == []


def test_real_jwt_staff_is_school_scoped(scope):
    client = APIClient()
    token = AccessToken.for_user(scope["staff"])
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = client.get(
        "/api/households/", HTTP_X_SCHOOL_ID=str(scope["a"].pk),
    )
    assert response.status_code == 200, response.content[:250]
    assert [str(h["id"]) for h in response.json()] == [str(scope["ha"].pk)]


def test_inactive_school_and_malformed_header_fail_closed(scope):
    client = _client(scope["staff"])
    malformed = client.get("/api/students/", HTTP_X_SCHOOL_ID="not-a-uuid")
    assert malformed.status_code == 400
    scope["a"].is_active = False
    scope["a"].save(update_fields=["is_active"])
    inactive = client.get(
        "/api/households/", HTTP_X_SCHOOL_ID=str(scope["a"].pk),
    )
    assert inactive.status_code == 404
