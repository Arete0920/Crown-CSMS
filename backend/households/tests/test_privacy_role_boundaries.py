"""Canonical public privacy regression: real router, verified links, tenant roles."""
import uuid

import pytest
from rest_framework.test import APIClient

from core.models import School, UserAccount, UserRole, CrownPermission, RolePermission
from households.models import Household, Guardian, Student

pytestmark = pytest.mark.django_db


@pytest.fixture
def people(db, settings):
    settings.HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED = False
    school = School.objects.create(name="Synthetic Privacy A")
    foreign = School.objects.create(name="Synthetic Privacy B")
    home = Household.objects.create(school_id=school.pk, name="Private Home")
    other = Household.objects.create(school_id=school.pk, name="Other Home")
    outside = Household.objects.create(school_id=foreign.pk, name="Foreign Home")
    linked = UserAccount.objects.create_user(
        username=f"linked-{uuid.uuid4()}", email="shared@example.invalid", school=school
    )
    unlinked = UserAccount.objects.create_user(
        username=f"unlinked-{uuid.uuid4()}", email="unlinked@example.invalid", school=school
    )
    unknown = UserAccount.objects.create_user(
        username=f"unknown-{uuid.uuid4()}", email="unknown@example.invalid", school=school
    )
    for user in (linked, unlinked):
        UserRole.objects.create(user=user, school=school, role_code="PARENT")
    Guardian.objects.create(
        school_id=school.pk, household=home, account=linked, first_name="Linked",
        last_name="Parent", email="shared@example.invalid", phone="555-0101"
    )
    Guardian.objects.create(
        school_id=school.pk, household=other, first_name="Other",
        last_name="Parent", email="unlinked@example.invalid", phone="555-0202"
    )
    Guardian.objects.create(
        school_id=foreign.pk, household=outside, first_name="Foreign",
        last_name="Parent", email="foreign@example.invalid", phone="555-0303"
    )
    child = Student.objects.create(school_id=school.pk, household=home, first_name="Own", last_name="Child")
    Student.objects.create(school_id=school.pk, household=other, first_name="Other", last_name="Child")
    return locals()


def api(user, school):
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.pk))
    return client


@pytest.mark.parametrize("prefix", ["/api/", "/api/v1/"])
@pytest.mark.parametrize("resource", ["households", "guardians", "students"])
def test_unknown_role_cannot_enumerate_private_records(people, prefix, resource):
    response = api(people["unknown"], people["school"]).get(f"{prefix}{resource}/")
    assert response.status_code == 200
    assert response.json() == []
    target = people["home"] if resource == "households" else (
        Guardian.objects.filter(household=people["home"]).first() if resource == "guardians"
        else people["child"]
    )
    detail = api(people["unknown"], people["school"]).get(f"{prefix}{resource}/{target.pk}/")
    assert detail.status_code == 404


@pytest.mark.parametrize("prefix", ["/api/", "/api/v1/"])
@pytest.mark.parametrize("resource", ["households", "guardians", "students"])
def test_verified_parent_sees_only_linked_family(people, prefix, resource):
    client = api(people["linked"], people["school"])
    response = client.get(f"{prefix}{resource}/")
    assert response.status_code == 200, response.content
    assert len(response.json()) == 1
    other = people["other"] if resource == "households" else (
        Guardian.objects.filter(household=people["other"]).first()
        if resource == "guardians" else Student.objects.filter(household=people["other"]).first()
    )
    assert client.get(f"{prefix}{resource}/{other.pk}/").status_code == 404
    assert "unlinked@example.invalid" not in str(response.content)


@pytest.mark.parametrize("prefix", ["/api/", "/api/v1/"])
def test_parent_email_match_is_not_verified_identity(people, prefix):
    user = people["unlinked"]
    user.email = "unlinked@example.invalid"
    user.save(update_fields=["email"])
    for resource in ("households", "guardians", "students"):
        result = api(user, people["school"]).get(f"{prefix}{resource}/")
        assert result.status_code == 200
        assert result.json() == []


def test_staff_requires_distinct_persisted_school_grants(people):
    staff = UserAccount.objects.create_user(
        username=f"staff-{uuid.uuid4()}", email="staff-private@example.invalid",
        school=people["school"], is_staff=True
    )
    UserRole.objects.create(user=staff, school=people["school"], role_code="REGISTRAR")
    client = api(staff, people["school"])
    assert client.get("/api/households/").json() == []
    for code in ("households.view", "guardians.view"):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)
    assert len(client.get("/api/households/").json()) == 2
    assert len(client.get("/api/guardians/").json()) == 2
    assert client.get(f"/api/households/{people['outside'].pk}/").status_code == 404


def test_parent_role_in_different_school_cannot_expand_scope(people):
    outsider = UserAccount.objects.create_user(
        username=f"outsider-{uuid.uuid4()}", email="outsider@example.invalid",
        school=people["foreign"]
    )
    UserRole.objects.create(user=outsider, school=people["foreign"], role_code="PARENT")
    client = api(outsider, people["foreign"])
    assert client.get(f"/api/households/{people['home'].pk}/").status_code == 404



@pytest.mark.parametrize("prefix", ["/api/", "/api/v1/"])
def test_parent_does_not_inherit_co_guardian_contact_access(people, prefix):
    """A linked parent may only read their own Guardian.account contact."""
    f = people
    other_adult = Guardian.objects.create(
        school_id=f["school"].pk, household=f["home"],
        first_name="Private", last_name="CoGuardian",
        email="coguardian-private@example.invalid", phone="555-9988",
    )
    c = api(f["linked"], f["school"])
    contacts = c.get(f"{prefix}guardians/")
    assert contacts.status_code == 200
    assert len(contacts.json()) == 1
    assert contacts.json()[0]["email"] == "shared@example.invalid"
    assert c.get(f"{prefix}guardians/{other_adult.pk}/").status_code == 404
    household = c.get(f"{prefix}households/{f['home'].pk}/")
    assert household.status_code == 200
    assert "guardians" not in household.json()
    assert "coguardian-private@example.invalid" not in str(household.content)
    assert "555-9988" not in str(household.content)



@pytest.mark.parametrize("prefix", ["/api/", "/api/v1/"])
def test_mismatched_school_related_rows_never_leak_in_nested_or_direct_reads(
    people, prefix
):
    """A foreign-school child/guardian cannot travel through a local FK.

    Model clean() is not called by every Django write path; the public read
    boundary therefore must independently validate both school IDs.
    """
    f = people
    foreign_child = Student.objects.create(
        school_id=f["foreign"].pk,
        household=f["home"],
        first_name="ForeignTenant", last_name="SyntheticChild",
    )
    foreign_contact = Guardian.objects.create(
        school_id=f["foreign"].pk,
        household=f["home"],
        first_name="ForeignTenant", last_name="SyntheticGuardian",
        email="mismatched-contact@example.invalid",
    )
    staff_a = UserAccount.objects.create_user(
        username=f"boundary-a-{uuid.uuid4()}",
        email=f"boundary-a-{uuid.uuid4()}@example.invalid",
        school=f["school"], is_staff=True,
    )
    staff_b = UserAccount.objects.create_user(
        username=f"boundary-b-{uuid.uuid4()}",
        email=f"boundary-b-{uuid.uuid4()}@example.invalid",
        school=f["foreign"], is_staff=True,
    )
    for staff, school in ((staff_a, f["school"]), (staff_b, f["foreign"])):
        UserRole.objects.create(user=staff, school=school, role_code="REGISTRAR")
    for code in ("households.view", "guardians.view"):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(
            role_code="REGISTRAR", permission=permission,
        )

    for actor in (f["linked"], staff_a):
        response = api(actor, f["school"]).get(
            f"{prefix}households/{f['home'].pk}/",
        )
        assert response.status_code == 200
        assert str(foreign_child.pk) not in str(response.content)
        assert str(foreign_contact.pk) not in str(response.content)
        assert "ForeignTenant" not in str(response.content)
        assert "mismatched-contact@example.invalid" not in str(response.content)

    # The foreign-school registrar must not be able to read a record whose
    # related household actually belongs to another school.
    client_b = api(staff_b, f["foreign"])
    for path, pk in (("students", foreign_child.pk), ("guardians", foreign_contact.pk)):
        result = client_b.get(f"{prefix}{path}/{pk}/")
        assert result.status_code == 404
        assert "ForeignTenant" not in str(result.content)
