import uuid
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from admissions.models import AdmissionsApplication
from applications.models import Applicant, Application, ApplicationEvent, ApplicationStatus
from applications.views_admissions import (
    CONTRACT_COUNTERSIGNED,
    DEPOSIT_PAID,
    ENROLLMENT_STATE_EVENT_TYPE,
)
from core.models import AcademicYear, CrownPermission, Family, GradeLevel, RolePermission, School, UserRole, Student as CoreStudent
from crown_api.models_households import Household as CrownHousehold, Person, Student as CrownStudent
from households.models import Household, Student


pytestmark = pytest.mark.django_db
User = get_user_model()


def _staff_user(school: School, username: str = "golden-admin"):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="Passw0rd!",
        is_staff=True,
        school=school,
    )
    return user


def _registrar_user(school: School, username: str = "golden-registrar"):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="Passw0rd!",
        school=school,
    )
    perm, _ = CrownPermission.objects.get_or_create(code="admissions.view", defaults={"description": "View admissions"})
    RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=perm)
    UserRole.objects.get_or_create(user=user, school=school, role_code="REGISTRAR")
    return user


def _school_year(school: School) -> AcademicYear:
    return AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 5, 31),
        is_current=True,
    )


def _link_ready_canonical_application(legacy):
    household = Household.objects.create(
        school_id=legacy.school_id,
        name=f"Golden Canonical Household {uuid.uuid4().hex[:6]}",
    )
    canonical = Application.objects.create(
        school_id=legacy.school_id,
        household=household,
        status=ApplicationStatus.DECIDED,
    )
    ApplicationEvent.objects.create(
        school_id=legacy.school_id,
        application=canonical,
        event_type="decision_made",
        payload={"decision": "accepted"},
    )
    ApplicationEvent.objects.create(
        school_id=legacy.school_id,
        application=canonical,
        event_type=ENROLLMENT_STATE_EVENT_TYPE,
        payload={
            "contract_status": CONTRACT_COUNTERSIGNED,
            "deposit_status": DEPOSIT_PAID,
        },
    )
    legacy.notes_internal = f"canonical_application_id={canonical.id}"
    legacy.save(update_fields=["notes_internal", "updated_at"])
    return canonical


def test_admissions_summary_returns_expected_pipeline_shape():
    school = School.objects.create(name="Golden Path School")
    user = _registrar_user(school)
    household = Household.objects.create(school_id=school.id, name="Golden Household")
    app = Application.objects.create(school_id=school.id, household=household, status="SUBMITTED")
    Applicant.objects.create(
        school_id=school.id,
        application=app,
        first_name="Jane",
        last_name="Doe",
        grade_applying_for="5",
        source="website",
        flags={"duplicate_suspected": False, "bot_suspected": False},
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/v1/admissions/summary/", HTTP_X_SCHOOL_ID=str(school.id))

    assert response.status_code == 200
    assert "pipeline" in response.data
    assert "conversion" in response.data
    assert response.data["pipeline"]["total"] >= 1


def test_enrollment_transition_marks_application_enrolled_and_activates_student():
    school = School.objects.create(name="Enrollment School")
    academic_year = _school_year(school)
    family = Family.objects.create(school=school, family_name="Doe")
    grade = GradeLevel.objects.create(school=school, code="5", label="Grade 5", sort_order=5)
    core_student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number="S-100",
        first_name="Jane",
        last_name="Doe",
        dob=date(2015, 1, 1),
        current_grade_level=grade,
        status="APPLICANT",
    )
    person = Person.objects.create(first_name="Jane", last_name="Doe")
    crown_household = CrownHousehold.objects.create(household_name="Doe Household")
    sis_student = CrownStudent.objects.create(person=person, household=crown_household, grade_level="5", active=False)
    app = AdmissionsApplication.objects.create(
        school=school,
        academic_year=academic_year,
        family=family,
        student=core_student,
        sis_student=sis_student,
        status=AdmissionsApplication.STATUS_ACCEPTED,
    )
    _link_ready_canonical_application(app)

    user = _staff_user(school, username=f"enroll-{uuid.uuid4()}")
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(
        "/api/admissions/enroll/",
        {"application_id": app.id},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    app.refresh_from_db()
    sis_student.refresh_from_db()
    assert app.status == AdmissionsApplication.STATUS_ENROLLED
    assert sis_student.active is True


def test_billing_run_creation_generates_invoice_for_enrolled_students():
    school = School.objects.create(name="Billing School")
    household = Household.objects.create(school_id=school.id, name="Billing Household")
    student_one = Student.objects.create(school_id=school.id, household=household, first_name="A", last_name="One", grade_level="5", is_active=True)
    student_two = Student.objects.create(school_id=school.id, household=household, first_name="B", last_name="Two", grade_level="5", is_active=True)
    course = Course.objects.create(school_id=school.id, code="MATH5", name="Math 5")
    section = Section.objects.create(school_id=school.id, course=course, term="2026-FALL", teacher_name="Teacher", grade_band="5")
    Enrollment.objects.create(school_id=school.id, section=section, student=student_one)
    Enrollment.objects.create(school_id=school.id, section=section, student=student_two)

    user = _staff_user(school, username=f"billing-{uuid.uuid4()}")
    finance_group, _ = Group.objects.get_or_create(name="finance_admin")
    user.groups.add(finance_group)
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(
        "/api/v1/billing/runs/",
        {"term": "2026-FALL", "amount_per_student": "1000.00"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 201
    assert response.json()["ok"] is True


def test_attendance_submit_accepts_school_scoped_write():
    school = School.objects.create(name="Attendance School")
    family = Family.objects.create(school=school, family_name="Smith")
    grade = GradeLevel.objects.create(school=school, code="4", label="Grade 4", sort_order=4)
    student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number="S-200",
        first_name="Alex",
        last_name="Smith",
        dob=date(2016, 2, 2),
        current_grade_level=grade,
        status="ACTIVE",
    )
    course = Course.objects.create(school_id=school.id, code="SCI4", name="Science 4")
    section = Section.objects.create(school_id=school.id, course=course, term="2026-FALL", teacher_name="Teacher", grade_band="4")

    token = uuid.uuid4()
    user = User.objects.create_user(
        username=f"attendance-{token}",
        email=f"attendance-{token}@example.com",
        password="Passw0rd!",
        school=school,
    )
    UserRole.objects.create(user=user, school=school, role_code="HEAD_OF_SCHOOL")

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(
        f"/api/v1/academics/sections/{section.id}/attendance/",
        {"date": "2026-04-01", "records": [{"student_id": str(student.id), "status": "present"}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    assert response.data["ok"] is True
    assert response.data["created"] == 1
