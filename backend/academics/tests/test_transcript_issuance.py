import base64
import hashlib
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import TranscriptEntry
from academics.tests.test_transcript_ro_api import _base_school, _section
from audit.models import AuditLog
from core.models import UserRole

pytestmark = pytest.mark.django_db


def _client(school, role):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"transcript-{uuid.uuid4()}",
        email=f"{role.lower()}-{uuid.uuid4()}@test.local",
        password="test-pass",
        school=school,
    )
    UserRole.objects.create(school=school, user=user, role_code=role)
    client = APIClient()
    client.force_authenticate(user)
    return client, user


def _fixture():
    school, year, student = _base_school()
    term, course, _ = _section(
        school=school, year=year, student=student, code="MATH-101",
        term_code="FALL", term_name="Fall 2026", ordering=1,
    )
    TranscriptEntry.objects.create(
        school_id=school.id, student=student, course=course, term=term,
        credit_value="1.00", final_letter_grade="A", final_percentage="96.00",
        gpa_points="4.00", provider="CROWN Academy",
    )
    return school, student


def _issue(client, school, student):
    return client.post(
        f"/api/v1/academics/students/{student.id}/transcript/issuances/",
        {}, format="json", HTTP_X_SCHOOL_ID=str(school.id),
    )


def _download(client, school, issuance_id):
    return client.get(
        f"/api/v1/academics/transcript-issuances/{issuance_id}/pdf/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )


def test_registrar_issues_immutable_snapshot_and_downloadable_pdf():
    school, student = _fixture()
    client, registrar = _client(school, "REGISTRAR")
    response = _issue(client, school, student)
    assert response.status_code == 201, response.content
    data = response.json()
    issuance = AuditLog.objects.get(pk=data["issuance_id"])
    metadata = issuance.metadata
    assert (issuance.action, issuance.model, issuance.object_id) == (
        "TRANSCRIPT_ISSUED", "academics.TranscriptIssuance", str(student.id)
    )
    assert metadata["school_id"] == str(school.id)
    assert metadata["student_id"] == str(student.id)
    assert metadata["issued_by_user_id"] == str(registrar.id)
    assert metadata["snapshot"]["cumulative_gpa"] == "4.00"
    assert metadata["snapshot"]["earned_credits"] == "1.00"
    artifact = base64.b64decode(metadata["artifact_b64"])
    assert artifact.startswith(b"%PDF")
    assert hashlib.sha256(artifact).hexdigest() == data["artifact_sha256"] == metadata["artifact_sha256"]
    download = _download(client, school, issuance.id)
    assert download.status_code == 200
    assert download["Content-Type"] == "application/pdf"
    assert download.content == artifact
    assert download["X-CROWN-Transcript-Issuance"] == str(issuance.id)
    assert download["X-CROWN-Artifact-SHA256"] == metadata["artifact_sha256"]


@pytest.mark.parametrize("role,expected", [("HEAD_OF_SCHOOL", 201), ("TEACHER", 403)])
def test_issuance_role_boundary(role, expected):
    school, student = _fixture()
    client, _ = _client(school, role)
    response = _issue(client, school, student)
    assert response.status_code == expected
    if expected != 201:
        assert not AuditLog.objects.filter(action="TRANSCRIPT_ISSUED").exists()


def test_cross_school_student_is_concealed_on_issuance():
    school, _ = _fixture()
    foreign_school, _year, foreign_student = _base_school()
    client, _ = _client(school, "REGISTRAR")
    assert _issue(client, school, foreign_student).status_code == 404
    assert foreign_school.id != school.id
    assert not AuditLog.objects.filter(action="TRANSCRIPT_ISSUED").exists()


def test_issuance_rejects_empty_transcript():
    school, _year, student = _base_school()
    client, _ = _client(school, "REGISTRAR")
    assert _issue(client, school, student).status_code == 400
    assert not AuditLog.objects.filter(action="TRANSCRIPT_ISSUED").exists()


def test_source_snapshot_and_artifact_provenance_are_repeatable_and_tamper_detected():
    school, student = _fixture()
    client, _ = _client(school, "REGISTRAR")
    first, second = _issue(client, school, student), _issue(client, school, student)
    assert first.status_code == second.status_code == 201
    assert first.json()["source_sha256"] == second.json()["source_sha256"]
    assert first.json()["issuance_id"] != second.json()["issuance_id"]
    log = AuditLog.objects.get(pk=first.json()["issuance_id"])
    metadata = dict(log.metadata)
    metadata["artifact_b64"] = base64.b64encode(b"not-a-pdf").decode("ascii")
    AuditLog.objects.filter(pk=log.id).update(metadata=metadata)
    assert _download(client, school, log.id).status_code == 409
