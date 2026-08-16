import base64
import hashlib
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section, Term, TranscriptEntry
from audit.models import AuditLog
from core.models import AcademicYear, School, UserRole
from households.models import Household, Student


pytestmark = pytest.mark.django_db


def _user(*, school, role_code, email):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"transcript-{uuid.uuid4()}",
        email=email,
        password="test-pass",
        school=school,
    )
    UserRole.objects.create(school=school, user=user, role_code=role_code)
    return user


def _fixture():
    school = School.objects.create(name="Issuance School")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="FALL",
        name="Fall 2026",
        school_year=year.name,
        ordering=1,
        active=True,
    )
    course = Course.objects.create(
        school_id=school.id,
        code="MATH-101",
        name="Mathematics",
        credits="1.00",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=term.code,
        term_ref=term,
        teacher_name="Teacher",
    )
    household = Household.objects.create(school_id=school.id, name="Issuance Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Official",
        last_name="Student",
        grade_level="12",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)
    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=course,
        term=term,
        credit_value="1.00",
        final_letter_grade="A",
        final_percentage="96.00",
        gpa_points="4.00",
        provider="CROWN Academy",
    )
    return school, student


def _issue(client, school, student):
    return client.post(
        f"/api/v1/academics/students/{student.id}/transcript/issuances/",
        {},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )


def test_registrar_issues_immutable_snapshot_and_downloadable_pdf():
    school, student = _fixture()
    registrar = _user(school=school, role_code="REGISTRAR", email="registrar@issuance.test")
    client = APIClient()
    client.force_authenticate(registrar)

    response = _issue(client, school, student)
    assert response.status_code == 201, response.content
    data = response.json()
    issuance = AuditLog.objects.get(pk=data["issuance_id"])
    metadata = issuance.metadata

    assert issuance.action == "TRANSCRIPT_ISSUED"
    assert issuance.model == "academics.TranscriptIssuance"
    assert issuance.object_id == str(student.id)
    assert metadata["student_id"] == str(student.id)
    assert metadata["school_id"] == str(school.id)
    assert metadata["issued_by_user_id"] == str(registrar.id)
    assert metadata["snapshot"]["cumulative_gpa"] == "4.00"
    assert metadata["snapshot"]["earned_credits"] == "1.00"

    artifact = base64.b64decode(metadata["artifact_b64"])
    assert artifact.startswith(b"%PDF")
    assert hashlib.sha256(artifact).hexdigest() == metadata["artifact_sha256"]
    assert data["artifact_sha256"] == metadata["artifact_sha256"]

    download = client.get(
        f"/api/v1/academics/transcript-issuances/{issuance.id}/pdf/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert download.status_code == 200
    assert download["Content-Type"] == "application/pdf"
    assert download.content == artifact
    assert download["X-CROWN-Transcript-Issuance"] == str(issuance.id)
    assert download["X-CROWN-Artifact-SHA256"] == metadata["artifact_sha256"]


def test_head_of_school_can_issue_official_transcript():
    school, student = _fixture()
    head = _user(school=school, role_code="HEAD_OF_SCHOOL", email="head@issuance.test")
    client = APIClient()
    client.force_authenticate(head)
    assert _issue(client, school, student).status_code == 201


def test_teacher_cannot_issue_official_transcript():
    school, student = _fixture()
    teacher = _user(school=school, role_code="TEACHER", email="teacher@issuance.test")
    client = APIClient()
    client.force_authenticate(teacher)

    response = _issue(client, school, student)
    assert response.status_code == 403
    assert not AuditLog.objects.filter(action="TRANSCRIPT_ISSUED").exists()


def test_cross_school_student_is_concealed_on_issuance():
    school, _student = _fixture()
    other_school = School.objects.create(name="Other School")
    other_household = Household.objects.create(school_id=other_school.id, name="Other Household")
    other_student = Student.objects.create(
        school_id=other_school.id,
        household=other_household,
        first_name="Other",
        last_name="Student",
        grade_level="12",
    )
    registrar = _user(school=school, role_code="REGISTRAR", email="registrar2@issuance.test")
    client = APIClient()
    client.force_authenticate(registrar)

    response = _issue(client, school, other_student)
    assert response.status_code == 404
    assert not AuditLog.objects.filter(action="TRANSCRIPT_ISSUED").exists()


def test_issuance_rejects_empty_transcript():
    school = School.objects.create(name="Empty Transcript School")
    household = Household.objects.create(school_id=school.id, name="Empty Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Empty",
        last_name="Student",
        grade_level="12",
    )
    registrar = _user(school=school, role_code="REGISTRAR", email="registrar3@issuance.test")
    client = APIClient()
    client.force_authenticate(registrar)

    response = _issue(client, school, student)
    assert response.status_code == 400
    assert not AuditLog.objects.filter(action="TRANSCRIPT_ISSUED").exists()


def test_source_snapshot_and_artifact_provenance_are_repeatable_and_tamper_detected():
    school, student = _fixture()
    registrar = _user(school=school, role_code="REGISTRAR", email="registrar4@issuance.test")
    client = APIClient()
    client.force_authenticate(registrar)

    first = _issue(client, school, student)
    second = _issue(client, school, student)
    assert first.status_code == second.status_code == 201
    assert first.json()["source_sha256"] == second.json()["source_sha256"]
    assert first.json()["issuance_id"] != second.json()["issuance_id"]

    log = AuditLog.objects.get(pk=first.json()["issuance_id"])
    metadata = dict(log.metadata)
    metadata["artifact_b64"] = base64.b64encode(b"not-a-pdf").decode("ascii")
    AuditLog.objects.filter(pk=log.id).update(metadata=metadata)

    download = client.get(
        f"/api/v1/academics/transcript-issuances/{log.id}/pdf/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert download.status_code == 409
