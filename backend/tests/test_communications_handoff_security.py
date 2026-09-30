from __future__ import annotations

import uuid

import pytest
from rest_framework.test import APIClient

from core.models import (
    CrownPermission,
    Family,
    HouseholdFamilyLink,
    RolePermission,
    School,
    UserAccount,
    UserRole,
)
from crown_api.models_comms_core import MessageThread
from crown_api.models_households import Household


pytestmark = pytest.mark.django_db


def _school(name: str) -> School:
    return School.objects.create(name=name)


def _user(school: School, *, is_staff: bool = False) -> UserAccount:
    return UserAccount.objects.create_user(
        username=f"comms-security-{uuid.uuid4()}",
        password="testpass",
        school=school,
        is_staff=is_staff,
    )


def _grant_communications(user: UserAccount, school: School) -> None:
    permission, _ = CrownPermission.objects.get_or_create(
        code="communications.view",
        defaults={"description": "View communications dashboard"},
    )
    role_code = "communications_security_test"
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)


def _thread_for_school(school: School, label: str) -> MessageThread:
    household = Household.objects.create(household_name=f"{label} Household")
    family = Family.objects.create(school=school, family_name=f"{label} Family")
    HouseholdFamilyLink.objects.create(
        school=school,
        household_id=household.id,
        family=family,
        source=HouseholdFamilyLink.SOURCE_MANUAL,
    )
    return MessageThread.objects.create(household=household, subject=label)


def _client(user: UserAccount, school: School) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def test_communications_staff_access_is_persistent_permission_not_django_staff():
    school = _school("Comms staff bypass")
    user = _user(school, is_staff=True)
    response = _client(user, school).get("/api/threads/")
    assert response.status_code == 403


def test_communications_staff_thread_read_is_tenant_scoped():
    school_a = _school("Comms school A")
    school_b = _school("Comms school B")
    thread_a = _thread_for_school(school_a, "A")
    thread_b = _thread_for_school(school_b, "B")
    user = _user(school_a)
    _grant_communications(user, school_a)

    response = _client(user, school_a).get("/api/threads/")
    assert response.status_code == 200
    ids = {row["thread_id"] for row in response.json()}
    assert str(thread_a.id) in ids
    assert str(thread_b.id) not in ids


def test_duplicate_broken_compose_route_is_retired_fail_closed():
    school = _school("Comms compose retired")
    user = _user(school)
    _grant_communications(user, school)
    response = _client(user, school).post(
        "/api/comms/compose/",
        {"subject": "Unsafe", "body": "Unsafe"},
        format="json",
    )
    assert response.status_code == 404


def test_arbitrary_recipient_smoke_email_route_is_retired_fail_closed():
    school = _school("Comms smoke retired")
    user = _user(school)
    _grant_communications(user, school)
    response = _client(user, school).post(
        "/api/comms/send-test-email/",
        {"to": "outside@example.com", "school_id": str(uuid.uuid4())},
        format="json",
    )
    assert response.status_code == 404
