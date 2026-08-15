import pytest
from rest_framework.test import APIClient

from core.models import School
from households.models import Guardian, Household

from academics.tests.test_transcript_ro_api import (
    _assign_role,
    _mk_user,
    _seed_transcript_test_data,
)

pytestmark = pytest.mark.django_db


TRANSCRIPT_PATHS = (
    "/api/v1/academics/transcript/{student_id}/",
    "/api/v1/transcripts/students/{student_id}/",
    "/api/v1/academics/students/{student_id}/transcript/",
)


def _get(client, path, school):
    return client.get(path, HTTP_X_SCHOOL_ID=str(school.id))


@pytest.mark.parametrize("path_template", TRANSCRIPT_PATHS)
def test_unrelated_same_school_user_cannot_read_transcript(path_template):
    school = School.objects.create(name="Disclosure School")
    student = _seed_transcript_test_data(school=school)
    user = _mk_user(school=school, email="unrelated@test.local")

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, path_template.format(student_id=student.id), school)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Student not found."


def test_head_of_school_can_read_transcript():
    school = School.objects.create(name="Head School")
    student = _seed_transcript_test_data(school=school)
    user = _mk_user(school=school, email="head@test.local")
    _assign_role(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/academics/transcript/{student.id}/", school)
    assert resp.status_code == 200, resp.content


def test_student_linked_account_can_read_own_transcript():
    school = School.objects.create(name="Student Self School")
    student = _seed_transcript_test_data(school=school)
    user = _mk_user(school=school, email="student@test.local")
    student.account = user
    student.save()

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/academics/students/{student.id}/transcript/", school)
    assert resp.status_code == 200, resp.content


def test_guardian_linked_to_household_can_read_child_transcript():
    school = School.objects.create(name="Guardian School")
    student = _seed_transcript_test_data(school=school)
    user = _mk_user(school=school, email="guardian@test.local")
    Guardian.objects.create(
        school_id=school.id,
        household=student.household,
        account=user,
        first_name="Grace",
        last_name="Guardian",
        email=user.email,
    )

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/academics/transcript/{student.id}/", school)
    assert resp.status_code == 200, resp.content


def test_guardian_cannot_read_unrelated_student_transcript():
    school = School.objects.create(name="Guardian Denial School")
    student = _seed_transcript_test_data(school=school)
    user = _mk_user(school=school, email="guardian-unrelated@test.local")
    other_household = Household.objects.create(school_id=school.id, name="Other Household")
    Guardian.objects.create(
        school_id=school.id,
        household=other_household,
        account=user,
        first_name="Other",
        last_name="Guardian",
        email=user.email,
    )

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/academics/transcript/{student.id}/", school)
    assert resp.status_code == 404


def test_teacher_role_does_not_grant_full_transcript_disclosure():
    school = School.objects.create(name="Teacher Denial School")
    student = _seed_transcript_test_data(school=school)
    user = _mk_user(school=school, email="teacher@test.local")
    _assign_role(user=user, school=school, role_code="TEACHER")

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/academics/transcript/{student.id}/", school)
    assert resp.status_code == 404


def test_cross_school_header_probe_is_concealed():
    school = School.objects.create(name="Home School")
    foreign_school = School.objects.create(name="Foreign School")
    foreign_student = _seed_transcript_test_data(school=foreign_school)
    user = _mk_user(school=school, email="registrar-home@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")

    client = APIClient()
    client.force_authenticate(user)

    resp = client.get(
        f"/api/v1/academics/transcript/{foreign_student.id}/",
        HTTP_X_SCHOOL_ID=str(foreign_school.id),
    )
    assert resp.status_code == 404
