import datetime as dt
import uuid

import pytest
from django.urls import resolve, reverse
from rest_framework.test import APIClient

from core.models import Family, School, Student, UserAccount


pytestmark = pytest.mark.django_db


def _school(name: str) -> School:
    return School.objects.create(name=f"{name}-{uuid.uuid4()}")


def _family(school: School, name: str) -> Family:
    return Family.objects.create(school=school, family_name=name)


def _student(school: School, family: Family, number: str, first: str, last: str) -> Student:
    return Student.objects.create(
        school=school,
        family=family,
        student_number=number,
        first_name=first,
        last_name=last,
        dob=dt.date(2016, 1, 15),
        status="ACTIVE",
    )


def _auth_client(user: UserAccount) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_url_resolution_contracts():
    list_match = resolve("/api/v1/student-records/")
    assert list_match.url_name == "student-records-list"

    detail_path = f"/api/v1/student-records/{uuid.uuid4()}/"
    detail_match = resolve(detail_path)
    assert detail_match.url_name == "student-records-detail"


def test_requires_authentication_for_list():
    school = _school("records-auth")
    user = UserAccount.objects.create_user(username=f"user-{uuid.uuid4()}", password="Passw0rd!")
    url = reverse("student-records-list")

    client = APIClient()
    response = client.get(url, HTTP_X_SCHOOL_ID=str(school.id))

    assert response.status_code in (401, 403)


def test_missing_school_header_returns_400():
    _school("records-missing-header")
    user = UserAccount.objects.create_user(username=f"user-{uuid.uuid4()}", password="Passw0rd!")
    client = _auth_client(user)

    response = client.get(reverse("student-records-list"))

    assert response.status_code == 400


def test_list_scopes_to_tenant_school():
    school_a = _school("records-A")
    school_b = _school("records-B")
    fam_a = _family(school_a, "Fam A")
    fam_b = _family(school_b, "Fam B")
    student_a = _student(school_a, fam_a, "A-001", "Alice", "A")
    _student(school_b, fam_b, "B-001", "Bob", "B")

    user = UserAccount.objects.create_user(username=f"user-{uuid.uuid4()}", password="Passw0rd!", school=school_a)
    client = _auth_client(user)

    response = client.get(reverse("student-records-list"), HTTP_X_SCHOOL_ID=str(school_a.id))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(student_a.id)


def test_detail_cross_tenant_returns_404():
    school_a = _school("records-cross-A")
    school_b = _school("records-cross-B")
    fam_a = _family(school_a, "Fam A")
    fam_b = _family(school_b, "Fam B")
    _student(school_a, fam_a, "A-100", "Amy", "A")
    student_b = _student(school_b, fam_b, "B-100", "Ben", "B")

    user = UserAccount.objects.create_user(username=f"user-{uuid.uuid4()}", password="Passw0rd!", school=school_a)
    client = _auth_client(user)

    response = client.get(
        reverse("student-records-detail", kwargs={"student_id": student_b.id}),
        HTTP_X_SCHOOL_ID=str(school_a.id),
    )

    assert response.status_code == 404


def test_detail_not_found_returns_404_with_valid_tenant():
    school = _school("records-not-found")
    user = UserAccount.objects.create_user(username=f"user-{uuid.uuid4()}", password="Passw0rd!", school=school)
    client = _auth_client(user)

    response = client.get(
        reverse("student-records-detail", kwargs={"student_id": uuid.uuid4()}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 404


def test_detail_happy_path_200():
    school = _school("records-detail")
    fam = _family(school, "Fam Detail")
    student = _student(school, fam, "D-001", "Dana", "Detail")
    user = UserAccount.objects.create_user(username=f"user-{uuid.uuid4()}", password="Passw0rd!", school=school)
    client = _auth_client(user)

    response = client.get(
        reverse("student-records-detail", kwargs={"student_id": student.id}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(student.id)
    assert payload["student_number"] == "D-001"
