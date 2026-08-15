"""
API tests for Transcript Read-Only endpoint.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from core.models import AcademicYear, School, Staff, UserRole
from academics.models import Course, Enrollment, Section, Term, TranscriptEntry
from households.models import Guardian, Household, Student
from gradebook.models import GradeEntry

pytestmark = pytest.mark.django_db


def _mk_user(*, school: School, email: str):
    """Create a test user for the school."""
    User = get_user_model()
    return User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="test-pass",
        school=school,
    )


def _assign_role(*, user, school: School, role_code: str):
    """Assign a role to the user."""
    UserRole.objects.create(school=school, user=user, role_code=role_code)


def _seed_transcript_test_data(*, school: School):
    """Create minimal transcript test data: 1 student, 2 terms, 2 sections, grades."""
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )
    term1 = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        name="Fall 2026",
        school_year="2026-2027",
        ordering=1,
        active=True,
    )
    term2 = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2027-SPRING",
        name="Spring 2027",
        school_year="2026-2027",
        ordering=2,
        active=True,
    )

    course1 = Course.objects.create(school_id=school.id, code="MATH-101", name="Mathematics")
    course2 = Course.objects.create(school_id=school.id, code="ELA-101", name="English Language Arts")

    section1 = Section.objects.create(
        school_id=school.id,
        course=course1,
        term=term1.code,
        term_ref=term1,
        teacher_name="Teacher A",
    )
    section2 = Section.objects.create(
        school_id=school.id,
        course=course2,
        term=term2.code,
        term_ref=term2,
        teacher_name="Teacher B",
    )

    household = Household.objects.create(school_id=school.id, name="Test Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Test",
        last_name="Student",
        grade_level="3",
    )

    Enrollment.objects.create(school_id=school.id, section=section1, student=student)
    Enrollment.objects.create(school_id=school.id, section=section2, student=student)

    GradeEntry.objects.create(
        school_id=school.id,
        section=section1,
        student=student,
        assignment_name="Test 1",
        points_earned=90,
        points_possible=100,
    )
    GradeEntry.objects.create(
        school_id=school.id,
        section=section2,
        student=student,
        assignment_name="Quiz 1",
        points_earned=80,
        points_possible=100,
    )

    return student


def _get(client, path, school):
    return client.get(path, HTTP_X_SCHOOL_ID=str(school.id))


def test_transcript_ro_404_for_unknown_student():
    school = School.objects.create(name="Test School")
    user = _mk_user(school=school, email="registrar@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")

    client = APIClient()
    client.force_authenticate(user)

    unknown = uuid.uuid4()
    resp = _get(client, f"/api/v1/academics/transcript/{unknown}/", school)
    assert resp.status_code == 404


def test_transcript_ro_returns_terms_and_courses_for_demo_student():
    school = School.objects.create(name="Test School")
    user = _mk_user(school=school, email="registrar@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")

    student = _seed_transcript_test_data(school=school)

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/academics/transcript/{student.id}/", school)
    assert resp.status_code == 200, resp.content

    data = resp.json()
    assert "student" in data
    assert data["student"]["student_id"] == str(student.id)
    assert data["student"]["first_name"] == "Test"
    assert data["student"]["last_name"] == "Student"
    assert "terms" in data and isinstance(data["terms"], list)
    assert len(data["terms"]) == 2

    t0 = data["terms"][0]
    assert "term_code" in t0
    assert "courses" in t0
    assert len(t0["courses"]) >= 1

    c0 = t0["courses"][0]
    assert "section_id" in c0
    assert "course_code" in c0
    assert "course_name" in c0
    assert "teacher_name" in c0
    assert "final_percent" in c0
    assert "final_letter" in c0
    assert "credits" in c0

    assert "term_gpa_mvp" in t0
    assert "cumulative_gpa_mvp" in data
    assert "notes" in data


def test_transcript_ro_alias_returns_same_contract():
    school = School.objects.create(name="Test School")
    user = _mk_user(school=school, email="registrar@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")

    student = _seed_transcript_test_data(school=school)

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/transcripts/students/{student.id}/", school)
    assert resp.status_code == 200, resp.content

    data = resp.json()
    assert data["student"]["student_id"] == str(student.id)
    assert "terms" in data and isinstance(data["terms"], list)


def test_student_transcript_contract_shape():
    school = School.objects.create(name="Test School")
    user = _mk_user(school=school, email="registrar@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")

    student = _seed_transcript_test_data(school=school)

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/academics/students/{student.id}/transcript/", school)
    assert resp.status_code == 200, resp.content

    data = resp.json()
    assert data["student_id"] == str(student.id)
    assert "student_name" in data
    assert "school_years" in data and isinstance(data["school_years"], list)
    assert data["school_years"], data
    year0 = data["school_years"][0]
    assert "school_year" in year0
    assert "terms" in year0 and isinstance(year0["terms"], list)
    term0 = year0["terms"][0]
    assert "term_id" in term0
    assert "term_name" in term0
    assert "courses" in term0 and isinstance(term0["courses"], list)
    course0 = term0["courses"][0]
    assert "section_id" in course0
    assert "course_code" in course0
    assert "course_name" in course0
    assert "credits" in course0
    assert "teacher" in course0
    assert "final_grade" in course0
    assert "status" in course0


def test_transcript_ro_includes_dual_enrollment_metadata():
    school = School.objects.create(name="Metadata School")
    user = _mk_user(school=school, email="registrar-metadata@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")

    student = _seed_transcript_test_data(school=school)
    section = Section.objects.filter(school_id=school.id, course__code="MATH-101").first()
    assert section is not None

    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=section.course,
        term=section.term_ref,
        credit_value="1.00",
        final_letter_grade="A",
        final_percentage="90.00",
        gpa_points="4.00",
        provider="Acme Online Academy",
        dual_enrollment_label="Dual Enrollment",
    )

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/academics/transcript/{student.id}/", school)
    assert resp.status_code == 200, resp.content
    data = resp.json()

    all_courses = [c for term in data["terms"] for c in term["courses"]]
    math_course = next(c for c in all_courses if c["course_code"] == "MATH-101")
    assert math_course["provider"] == "Acme Online Academy"
    assert math_course["dual_enrollment_label"] == "Dual Enrollment"


def test_student_transcript_contract_includes_dual_enrollment_metadata():
    school = School.objects.create(name="Metadata School 2")
    user = _mk_user(school=school, email="registrar-metadata2@test.local")
    _assign_role(user=user, school=school, role_code="REGISTRAR")

    student = _seed_transcript_test_data(school=school)
    section = Section.objects.filter(school_id=school.id, course__code="MATH-101").first()
    assert section is not None

    TranscriptEntry.objects.create(
        school_id=school.id,
        student=student,
        course=section.course,
        term=section.term_ref,
        credit_value="1.00",
        final_letter_grade="A",
        final_percentage="90.00",
        gpa_points="4.00",
        provider="Acme Online Academy",
        dual_enrollment_label="Dual Enrollment",
    )

    client = APIClient()
    client.force_authenticate(user)

    resp = _get(client, f"/api/v1/academics/students/{student.id}/transcript/", school)
    assert resp.status_code == 200, resp.content
    data = resp.json()

    all_courses = [c for year in data["school_years"] for term in year["terms"] for c in term["courses"]]
    math_course = next(c for c in all_courses if c["course_code"] == "MATH-101")
    assert math_course["provider"] == "Acme Online Academy"
    assert math_course["dual_enrollment_label"] == "Dual Enrollment"


@pytest.mark.parametrize(
    "path_template",
    [
        "/api/v1/academics/transcript/{student_id}/",
        "/api/v1/transcripts/students/{student_id}/",
        "/api/v1/academics/students/{student_id}/transcript/",
    ],
)
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
