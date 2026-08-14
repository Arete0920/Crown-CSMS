import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import (
    Family,
    HouseholdFamilyLink,
    School,
    Student as CoreStudent,
    StudentIdentityLink,
)
from households.models import Household, Student
from applications.models import Application, ApplicationStatus
from ledger.models import LedgerAccount, Charge


pytestmark = pytest.mark.django_db


def _mk_user_with_school_id(school_id):
    School.objects.get_or_create(id=school_id, defaults={"name": f"School-{school_id}"})
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school_id)
        u.save(update_fields=["school_id"])
    return u


def _mk_application_with_family_bridge(*, applicant_dob=date(2015, 5, 10)):
    school = School.objects.create(name=f"School-{uuid.uuid4()}")
    hh = Household.objects.create(school_id=school.id, name="Household")
    family = Family.objects.create(school=school, family_name=f"Family-{uuid.uuid4()}")
    HouseholdFamilyLink.objects.create(
        school=school,
        household_id=hh.id,
        family=family,
        source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    )
    app = Application.objects.create(
        school_id=school.id,
        household=hh,
        status=ApplicationStatus.SUBMITTED,
    )
    applicant = app.applicants.create(
        school_id=school.id,
        first_name="John",
        last_name="Doe",
        grade_applying_for="5",
        dob=applicant_dob,
    )
    return school, hh, family, app, applicant


def _client_for_school(school_id):
    c = Client()
    c.force_login(_mk_user_with_school_id(school_id))
    return c


def test_accept_creates_canonical_compatibility_link_and_charge():
    school, hh, family, app, applicant = _mk_application_with_family_bridge()
    c = _client_for_school(school.id)

    resp = c.post(
        f"/api/v1/applications/{app.id}/decision/",
        data={
            "decision": "ACCEPT",
            "enrollment_fee": "250.00",
            "student_numbers": {str(applicant.id): "S-1001"},
        },
        content_type="application/json",
    )
    assert resp.status_code == 200

    app.refresh_from_db()
    applicant.refresh_from_db()
    assert app.status == ApplicationStatus.DECIDED
    assert applicant.student_id is not None

    compatibility_student = Student.objects.get(pk=applicant.student_id)
    canonical_student = CoreStudent.objects.get(school=school, student_number="S-1001")
    assert canonical_student.family == family
    assert canonical_student.dob == applicant.dob
    assert canonical_student.status == "ACTIVE"

    link = StudentIdentityLink.objects.get(
        core_student=canonical_student,
        compatibility_student=compatibility_student,
    )
    assert link.school == school
    assert link.source == StudentIdentityLink.SOURCE_ADMISSIONS
    assert link.verification_status == StudentIdentityLink.STATUS_VERIFIED
    assert str(app.id) in link.evidence_reference
    assert str(applicant.id) in link.evidence_reference

    acct = LedgerAccount.objects.get(household=hh)
    assert Charge.objects.filter(account=acct).count() == 1


def test_accept_fails_closed_without_explicit_student_number():
    school, hh, _family, app, _applicant = _mk_application_with_family_bridge()
    c = _client_for_school(school.id)

    resp = c.post(
        f"/api/v1/applications/{app.id}/decision/",
        data={"decision": "ACCEPT"},
        content_type="application/json",
    )
    assert resp.status_code == 400

    app.refresh_from_db()
    assert app.status == ApplicationStatus.SUBMITTED
    assert Student.objects.filter(household=hh).count() == 0
    assert CoreStudent.objects.filter(school=school).count() == 0
    assert StudentIdentityLink.objects.filter(school=school).count() == 0
    assert LedgerAccount.objects.filter(household=hh).count() == 0


def test_accept_fails_closed_without_verified_dob():
    school, hh, _family, app, applicant = _mk_application_with_family_bridge(applicant_dob=None)
    c = _client_for_school(school.id)

    resp = c.post(
        f"/api/v1/applications/{app.id}/decision/",
        data={
            "decision": "ACCEPT",
            "student_numbers": {str(applicant.id): "S-1002"},
        },
        content_type="application/json",
    )
    assert resp.status_code == 400

    app.refresh_from_db()
    assert app.status == ApplicationStatus.SUBMITTED
    assert Student.objects.filter(household=hh).count() == 0
    assert CoreStudent.objects.filter(school=school).count() == 0


def test_accept_rejects_existing_student_number_without_guessing_identity():
    school, hh, family, app, applicant = _mk_application_with_family_bridge()
    CoreStudent.objects.create(
        school=school,
        family=family,
        student_number="S-EXISTING",
        first_name="Different",
        last_name="Student",
        dob=date(2014, 1, 1),
        status="ACTIVE",
    )
    c = _client_for_school(school.id)

    resp = c.post(
        f"/api/v1/applications/{app.id}/decision/",
        data={
            "decision": "ACCEPT",
            "student_numbers": {str(applicant.id): "S-EXISTING"},
        },
        content_type="application/json",
    )
    assert resp.status_code == 400

    app.refresh_from_db()
    assert app.status == ApplicationStatus.SUBMITTED
    assert Student.objects.filter(household=hh).count() == 0
    assert StudentIdentityLink.objects.filter(school=school).count() == 0


def test_accept_reuses_existing_verified_identity_link_without_new_number():
    school, hh, family, app, applicant = _mk_application_with_family_bridge()
    compatibility_student = Student.objects.create(
        school_id=school.id,
        household=hh,
        first_name=applicant.first_name,
        last_name=applicant.last_name,
        grade_level="5",
        is_active=True,
    )
    applicant.student = compatibility_student
    applicant.save(update_fields=["student", "updated_at"])

    canonical_student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number="S-VERIFIED",
        first_name=applicant.first_name,
        last_name=applicant.last_name,
        dob=applicant.dob,
        status="ACTIVE",
    )
    StudentIdentityLink.objects.create(
        school=school,
        core_student=canonical_student,
        compatibility_student=compatibility_student,
        source=StudentIdentityLink.SOURCE_MANUAL,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference="test:preverified",
    )

    c = _client_for_school(school.id)
    resp = c.post(
        f"/api/v1/applications/{app.id}/decision/",
        data={"decision": "ACCEPT"},
        content_type="application/json",
    )
    assert resp.status_code == 200

    app.refresh_from_db()
    assert app.status == ApplicationStatus.DECIDED
    assert CoreStudent.objects.filter(school=school).count() == 1
    assert Student.objects.filter(household=hh).count() == 1
    assert StudentIdentityLink.objects.filter(school=school).count() == 1


def test_deny_creates_no_students_or_charges():
    school_id = uuid.uuid4()
    hh = Household.objects.create(school_id=school_id, name="Household")
    app = Application.objects.create(
        school_id=school_id,
        household=hh,
        status=ApplicationStatus.SUBMITTED,
    )

    app.applicants.create(
        school_id=school_id,
        first_name="Jane",
        last_name="Smith",
        grade_applying_for="3",
    )

    c = _client_for_school(school_id)
    resp = c.post(
        f"/api/v1/applications/{app.id}/decision/",
        data={"decision": "DENY"},
        content_type="application/json",
    )
    assert resp.status_code == 200

    assert Student.objects.count() == 0
    assert CoreStudent.objects.count() == 0
    assert StudentIdentityLink.objects.count() == 0
    assert LedgerAccount.objects.count() == 0
    assert Charge.objects.count() == 0
