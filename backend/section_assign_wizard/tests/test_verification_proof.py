"""Session-scoped classroom roster verification, not whole-section counts."""
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from core.models import CrownPermission, RolePermission, School, UserRole
from households.models import Household, Student
from section_assign_wizard.models import SectionAssignWizardSession

pytestmark = pytest.mark.django_db


def _context():
    school = School.objects.create(name=f"Roster Proof {uuid.uuid4().hex[:8]}")
    user = get_user_model().objects.create_user(
        username=f"registrar-{uuid.uuid4().hex}", password="test-only",
        school=school,
    )
    UserRole.objects.create(user=user, school=school, role_code="REGISTRAR")
    permission, _ = CrownPermission.objects.get_or_create(
        code="academics.view",
        defaults={"description": "Inspect section enrollment"},
    )
    RolePermission.objects.get_or_create(
        role_code="REGISTRAR", permission=permission,
    )
    course = Course.objects.create(school_id=school.id, code="HIST6", name="History")
    section = Section.objects.create(
        school_id=school.id, course=course, term="2026-FALL",
    )
    household = Household.objects.create(
        school_id=school.id, name="Synthetic Test Household",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return school, user, section, household, client


def _student(school, household):
    return Student.objects.create(
        school_id=school.id, household=household,
        first_name="Test", last_name=uuid.uuid4().hex[:8],
    )


def _session(school, user, section, changes, *, state=None):
    return SectionAssignWizardSession.objects.create(
        school=school,
        created_by=user,
        section_id=section.id,
        term=section.term,
        student_pool=[change["student_id"] for change in changes],
        roster_changes=changes,
        commit_result={"enrolled": sum(c["action"] == "add" for c in changes),
                       "removed": sum(c["action"] == "remove" for c in changes)},
        status=state or SectionAssignWizardSession.STATUS_COMMITTED,
    )


def _verify(client, school, session):
    return client.get(
        f"/api/v1/section-assign-wizard/sessions/{session.id}/verify/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )


def test_unrelated_enrollment_cannot_verify_missing_selected_add():
    school, user, section, household, client = _context()
    target = _student(school, household)
    unrelated = _student(school, household)
    Enrollment.objects.create(
        school_id=school.id, section=section, student=unrelated,
    )
    session = _session(
        school, user, section,
        [{"student_id": str(target.id), "action": "add"}],
    )
    response = _verify(client, school, session)
    assert response.status_code == 409, response.data
    assert response.data["code"] == "roster_verification_mismatch"
    session.refresh_from_db()
    assert session.status == SectionAssignWizardSession.STATUS_COMMITTED
    assert Enrollment.objects.filter(section=section).count() == 1


def test_remove_still_present_is_not_certified():
    school, user, section, household, client = _context()
    target = _student(school, household)
    Enrollment.objects.create(
        school_id=school.id, section=section, student=target,
    )
    session = _session(
        school, user, section,
        [{"student_id": str(target.id), "action": "remove"}],
    )
    response = _verify(client, school, session)
    assert response.status_code == 409, response.data
    session.refresh_from_db()
    assert session.status == SectionAssignWizardSession.STATUS_COMMITTED


def test_exact_mixed_add_remove_cohort_verifies_even_with_unrelated_members():
    school, user, section, household, client = _context()
    added = _student(school, household)
    removed = _student(school, household)
    unrelated = _student(school, household)
    Enrollment.objects.create(
        school_id=school.id, section=section, student=added,
    )
    Enrollment.objects.create(
        school_id=school.id, section=section, student=unrelated,
    )
    session = _session(school, user, section, [
        {"student_id": str(added.id), "action": "add"},
        {"student_id": str(removed.id), "action": "remove"},
    ])
    first = _verify(client, school, session)
    assert first.status_code == 200, first.data
    assert first.data["status"] == "verified"
    assert first.data["enrollment_count"] == 2
    assert first.data["enrolled"] == 1
    assert first.data["removed"] == 1
    second = _verify(client, school, session)
    assert second.status_code == 200, second.data
    session.refresh_from_db()
    assert session.status == SectionAssignWizardSession.STATUS_VERIFIED


def test_previously_verified_session_rejects_stale_roster_readback():
    school, user, section, household, client = _context()
    selected = _student(school, household)
    Enrollment.objects.create(
        school_id=school.id, section=section, student=selected,
    )
    session = _session(
        school, user, section,
        [{"student_id": str(selected.id), "action": "add"}],
    )
    assert _verify(client, school, session).status_code == 200
    Enrollment.objects.filter(section=section, student=selected).delete()
    second = _verify(client, school, session)
    assert second.status_code == 409, second.data
    session.refresh_from_db()
    # Preserve historical status, but never return a fresh false success.
    assert session.status == SectionAssignWizardSession.STATUS_VERIFIED


def test_invalid_or_duplicated_commit_evidence_fails_closed():
    school, user, section, household, client = _context()
    target = _student(school, household)
    Enrollment.objects.create(
        school_id=school.id, section=section, student=target,
    )
    session = _session(school, user, section, [
        {"student_id": str(target.id), "action": "add"},
        {"student_id": str(target.id), "action": "add"},
    ])
    response = _verify(client, school, session)
    assert response.status_code == 409, response.data
    session.refresh_from_db()
    assert session.status == SectionAssignWizardSession.STATUS_COMMITTED


def test_other_school_student_cannot_satisfy_staged_cohort():
    school, user, section, household, client = _context()
    other = School.objects.create(name="Another School")
    other_household = Household.objects.create(
        school_id=other.id, name="Foreign Household",
    )
    foreign_student = _student(other, other_household)
    session = _session(
        school, user, section,
        [{"student_id": str(foreign_student.id), "action": "remove"}],
    )
    response = _verify(client, school, session)
    assert response.status_code == 409, response.data
    session.refresh_from_db()
    assert session.status == SectionAssignWizardSession.STATUS_COMMITTED
