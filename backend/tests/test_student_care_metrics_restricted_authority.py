from __future__ import annotations

import uuid

import pytest
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole


pytestmark = pytest.mark.django_db
URL = "/api/discipline/metrics/"


def _school(name: str) -> School:
    return School.objects.create(name=name)


def _user(school: School) -> UserAccount:
    return UserAccount.objects.create_user(
        username=f"student-care-metrics-{uuid.uuid4()}",
        password="testpass",
        school=school,
    )


def _client(user: UserAccount, school: School) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def _grant(user: UserAccount, school: School, code: str) -> None:
    permission, _ = CrownPermission.objects.get_or_create(
        code=code,
        defaults={"description": f"Test permission {code}"},
    )
    role_code = "student_care_metrics_security_test"
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)


def test_student_care_view_only_cannot_read_sensitive_metrics():
    school = _school("Student Care metrics view only")
    user = _user(school)
    _grant(user, school, "student-care.view")

    response = _client(user, school).get(URL)

    assert response.status_code == 403


def test_restricted_student_care_authority_can_read_metrics():
    school = _school("Student Care metrics restricted")
    user = _user(school)
    _grant(user, school, "student-care.view")
    _grant(user, school, "student-care.view_restricted")

    response = _client(user, school).get(URL)

    assert response.status_code == 200
    assert response.json()["total"] == 0
