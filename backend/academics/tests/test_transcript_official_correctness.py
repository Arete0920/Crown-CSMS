import hashlib

import pytest
from rest_framework.test import APIClient

from academics.models import Section, TranscriptEntry
from academics.tests.test_transcript_ro_api import _assign_role, _mk_user, _seed_transcript_test_data
from core.models import School
from crown_api.audit_models import AuditEvent


pytestmark = pytest.mark.django_db


def _client_for(*, school, role_code="REGISTRAR", email="registrar@test.local"):
    user = _mk_user(school=school, email=email)
    _assign_role(user=user, school=school, role_code=role_code)
    client = APIClient()
    client.force_authenticate(user)
    return client, user


def _recorded_entries(*, school, student):
    math = Section.objects.get(school_id=school.id, course__code="MATH-101")
    ela = Section.objects.get(school_id=school.id, course__code="ELA-101")
    math_entry = TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=math.course,
        term=math.term_ref,
        credit_value="0.50",
        final_letter_grade="A",
        final_percentage="97.00",
        gpa_points="5.00",
        provider="Honors Consortium",
        dual_enrollment_label="Honors",
    )
    ela_entry = TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=ela.course,
        term=ela.term_ref,
        credit_value="1.50",
        final_letter_grade="F",
        final_percentage="42.00",
        gpa_points="0.00",
        provider="",
        dual_enrollment_label="",
    )
    return math_entry, ela_entry


def test_recorded_transcript_entries_are_official_credit_and_gpa_authority():
    school = School.objects.create(name="Transcript Correctness School")
    student = _seed_transcript_test_data(school=school)
    _recorded_entries(school=school, student=student)
    client, _ = _client_for(school=school)

    response = client.get(
        f"/api/v1/academics/transcript/{student.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200, response.content
    data = response.json()

    assert "cumulative_gpa_mvp" not in data
    assert data["cumulative_gpa"] == "1.25"
    assert data["attempted_credits"] == "2.00"
    assert data["earned_credits"] == "0.50"

    courses = [row for term in data["terms"] for row in term["courses"]]
    math = next(row for row in courses if row["course_code"] == "MATH-101")
    ela = next(row for row in courses if row["course_code"] == "ELA-101")

    assert math["final_letter"] == "A"
    assert math["final_percent"] == 97.0
    assert math["credits"] == "0.50"
    assert math["gpa_points"] == "5.00"
    assert math["grade_source"] == "transcript_entry"
    assert math["credit_source"] == "transcript_entry"
    assert math["provider"] == "Honors Consortium"
    assert math["dual_enrollment_label"] == "Honors"

    # The live Gradebook seed is 80%/B, but the recorded transcript result is F.
    assert ela["final_letter"] == "F"
    assert ela["final_percent"] == 42.0
    assert ela["earned_credits"] == "0.00"
    assert ela["attempted_credits"] == "1.50"

    for term in data["terms"]:
        assert "term_gpa_mvp" not in term
        assert "term_gpa" in term


def test_in_progress_gradebook_preview_does_not_enter_official_gpa_or_credit_totals():
    school = School.objects.create(name="Transcript Preview School")
    student = _seed_transcript_test_data(school=school)
    client, _ = _client_for(school=school, email="preview-registrar@test.local")

    response = client.get(
        f"/api/v1/academics/transcript/{student.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200, response.content
    data = response.json()

    assert data["cumulative_gpa"] is None
    assert data["attempted_credits"] == "0.00"
    assert data["earned_credits"] == "0.00"
    courses = [row for term in data["terms"] for row in term["courses"]]
    assert courses
    assert all(row["status"] == "in_progress" for row in courses)
    assert all(row["grade_source"] == "gradebook_preview" for row in courses)
    assert all(row["gpa_included"] is False for row in courses)


def test_contract_and_ro_outputs_share_authoritative_recorded_facts():
    school = School.objects.create(name="Transcript Contract School")
    student = _seed_transcript_test_data(school=school)
    _recorded_entries(school=school, student=student)
    client, _ = _client_for(school=school, email="contract-registrar@test.local")

    ro = client.get(
        f"/api/v1/academics/transcript/{student.id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    contract = client.get(
        f"/api/v1/academics/students/{student.id}/transcript/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert ro.status_code == 200, ro.content
    assert contract.status_code == 200, contract.content

    ro_data = ro.json()
    contract_data = contract.json()
    assert contract_data["cumulative_gpa"] == ro_data["cumulative_gpa"]
    assert contract_data["attempted_credits"] == ro_data["attempted_credits"]
    assert contract_data["earned_credits"] == ro_data["earned_credits"]

    ro_courses = {row["course_code"]: row for term in ro_data["terms"] for row in term["courses"]}
    contract_courses = {
        row["course_code"]: row
        for year in contract_data["school_years"]
        for term in year["terms"]
        for row in term["courses"]
    }
    assert contract_courses["MATH-101"]["credits"] == ro_courses["MATH-101"]["credits"]
    assert contract_courses["MATH-101"]["final_grade"] == ro_courses["MATH-101"]["final_letter"]
    assert contract_courses["MATH-101"]["gpa_points"] == ro_courses["MATH-101"]["gpa_points"]


def test_registrar_can_issue_and_reproduce_immutable_official_pdf():
    school = School.objects.create(name="Transcript Issuance School")
    student = _seed_transcript_test_data(school=school)
    math_entry, _ = _recorded_entries(school=school, student=student)
    client, user = _client_for(school=school, email="issuer@test.local")

    issued = client.post(
        f"/api/v1/academics/students/{student.id}/transcript/issue/",
        {},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert issued.status_code == 201, issued.content
    payload = issued.json()

    event = AuditEvent.objects.get(id=payload["issuance_id"])
    assert event.action == "transcript.issued"
    assert str(event.school_id) == str(school.id)
    assert str(event.actor_id) == str(user.id)
    assert event.meta["schema"] == "crown.official-transcript.v1"
    assert event.meta["source_sha256"] == payload["source_sha256"]
    assert event.meta["document_sha256"] == payload["document_sha256"]

    # Change live source data after issuance; the issued snapshot must remain unchanged.
    math_entry.final_letter_grade = "C"
    math_entry.gpa_points = "2.00"
    math_entry.save(update_fields=["final_letter_grade", "gpa_points"])

    downloaded = client.get(
        f"/api/v1/academics/transcript-issuances/{payload['issuance_id']}/pdf/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert downloaded.status_code == 200, downloaded.content
    assert downloaded["Content-Type"] == "application/pdf"
    assert downloaded["X-Transcript-Source-SHA256"] == payload["source_sha256"]
    assert downloaded["X-Transcript-Document-SHA256"] == payload["document_sha256"]
    assert hashlib.sha256(downloaded.content).hexdigest() == payload["document_sha256"]
    assert downloaded.content.startswith(b"%PDF")


def test_teacher_cannot_issue_official_transcript():
    school = School.objects.create(name="Transcript Issuance Denial School")
    student = _seed_transcript_test_data(school=school)
    _recorded_entries(school=school, student=student)
    client, _ = _client_for(
        school=school,
        role_code="TEACHER",
        email="teacher-issuer@test.local",
    )

    response = client.post(
        f"/api/v1/academics/students/{student.id}/transcript/issue/",
        {},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 403
    assert AuditEvent.objects.filter(action="transcript.issued").count() == 0


def test_issuance_requires_at_least_one_recorded_transcript_entry():
    school = School.objects.create(name="Transcript Issuance Empty School")
    student = _seed_transcript_test_data(school=school)
    client, _ = _client_for(school=school, email="empty-issuer@test.local")

    response = client.post(
        f"/api/v1/academics/students/{student.id}/transcript/issue/",
        {},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 409
    assert AuditEvent.objects.filter(action="transcript.issued").count() == 0
