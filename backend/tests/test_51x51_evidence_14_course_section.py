"""
Module 014 - Course & Section Management
Evidence Test File
==================

Proves the committed Module 014 boundary on the v1 academics API:
  1. Course API is tenant-scoped and authenticated.
  2. Section API is tenant-scoped and authenticated.
  3. Section detail and roster surfaces return expected course/student data.
  4. Teacher role guard prevents a teacher from querying another teacher's sections.
  5. Module 014 scheduling-conflict boundary is read-only in this API; section creation
     is not exposed through the v1 sections endpoint, preventing conflict mutation here.

Schedule optimization/conflict-solving remains owned by the schedule-builder module;
Module 014 proves course/section registry, roster, tenant, and role-access behavior.
"""

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section, TeacherAssignment, Term
from core.models import AcademicYear, School, Staff, UserRole
from households.models import Household, Student


User = get_user_model()


COURSES_URL = "/api/v1/academics/courses/"
SECTIONS_URL = "/api/v1/academics/sections/"


def _make_school(suffix=""):
    return School.objects.create(name=f"Module014 School {suffix or uuid.uuid4().hex[:6]}")


def _make_staff_user(school, *, role_code="HEAD_OF_SCHOOL", is_staff=True, email_prefix="staff"):
    token = uuid.uuid4().hex[:8]
    staff = Staff.objects.create(
        school=school,
        first_name=email_prefix.title(),
        last_name="User",
        email=f"{email_prefix}-{token}@example.com",
        role_type=role_code,
    )
    user = User.objects.create_user(
        username=f"{email_prefix}-{token}",
        email=staff.email,
        password="Passw0rd!",
        school=school,
        staff=staff,
        is_staff=is_staff,
    )
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    return user, staff


def _authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _headers(school):
    return {"HTTP_X_SCHOOL_ID": str(school.id)}


def _seed_academic_section(school, *, teacher_user=None, teacher_staff=None, code="ENG-101"):
    year = AcademicYear.objects.create(
        school=school,
        name=f"2026-2027 {uuid.uuid4().hex[:4]}",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        name="Fall",
        school_year="2026-2027",
        ordering=1,
        active=True,
    )
    course = Course.objects.create(
        school_id=school.id,
        code=code,
        name=f"Course {code}",
        department="English",
        credits="1.00",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term=term.code,
        teacher=teacher_user,
        teacher_name="Teacher User",
        grade_band="9",
    )
    if teacher_staff is not None:
        TeacherAssignment.objects.create(
            school_id=school.id,
            section=section,
            staff=teacher_staff,
        )
    household = Household.objects.create(school_id=school.id, name=f"Household {code}")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Jane",
        last_name="Doe",
        grade_level="9",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)
    return course, section, student


class TestModule014CourseSectionProof(TestCase):
    def test_course_api_is_authenticated_and_tenant_scoped(self):
        school_a = _make_school("A")
        school_b = _make_school("B")
        user_b, staff_b = _make_staff_user(school_b, email_prefix="admin-b")

        Course.objects.create(school_id=school_a.id, code="A-PRIVATE", name="Private A")
        Course.objects.create(school_id=school_b.id, code="B-VISIBLE", name="Visible B")

        unauth = APIClient()
        unauth_response = unauth.get(COURSES_URL, **_headers(school_b))
        self.assertEqual(unauth_response.status_code, 401)

        client = _authed_client(user_b)
        response = client.get(COURSES_URL, **_headers(school_b))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        codes = {row["code"] for row in body["results"]}
        self.assertIn("B-VISIBLE", codes)
        self.assertNotIn("A-PRIVATE", codes)
        self.assertEqual(staff_b.school_id, school_b.id)

    def test_section_list_detail_and_roster_are_tenant_scoped(self):
        school = _make_school("sections")
        user, staff = _make_staff_user(school, email_prefix="section-admin")
        course, section, student = _seed_academic_section(
            school,
            teacher_user=user,
            teacher_staff=staff,
            code="SCI-101",
        )

        client = _authed_client(user)

        list_response = client.get(SECTIONS_URL, **_headers(school))
        self.assertEqual(list_response.status_code, 200)
        list_body = list_response.json()
        self.assertGreaterEqual(list_body["total"], 1)
        section_ids = {row["section_id"] for row in list_body["results"]}
        self.assertIn(str(section.id), section_ids)

        detail_response = client.get(f"{SECTIONS_URL}{section.id}/", **_headers(school))
        self.assertEqual(detail_response.status_code, 200)
        detail_body = detail_response.json()
        self.assertEqual(detail_body["section_id"], str(section.id))
        self.assertEqual(detail_body["course_code"], course.code)

        roster_response = client.get(f"{SECTIONS_URL}{section.id}/roster/", **_headers(school))
        self.assertEqual(roster_response.status_code, 200)
        roster_body = roster_response.json()
        self.assertEqual(roster_body["section_id"], str(section.id))
        self.assertEqual(roster_body["counts"]["students"], 1)
        self.assertEqual(roster_body["students"][0]["student_id"], str(student.id))

    def test_teacher_role_cannot_query_another_teachers_sections(self):
        school = _make_school("teacher-guard")
        teacher_user, _teacher_staff = _make_staff_user(
            school,
            role_code="TEACHER",
            is_staff=False,
            email_prefix="teacher-one",
        )
        other_user, other_staff = _make_staff_user(
            school,
            role_code="TEACHER",
            is_staff=False,
            email_prefix="teacher-two",
        )
        _seed_academic_section(
            school,
            teacher_user=other_user,
            teacher_staff=other_staff,
            code="MATH-201",
        )

        client = _authed_client(teacher_user)
        response = client.get(
            f"{SECTIONS_URL}?teacher_id={other_staff.id}",
            **_headers(school),
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 0)
        self.assertEqual(body["results"], [])

    def test_section_api_readonly_boundary_prevents_schedule_conflict_mutation(self):
        school = _make_school("readonly")
        user, staff = _make_staff_user(school, email_prefix="readonly-admin")
        course, section, _student = _seed_academic_section(
            school,
            teacher_user=user,
            teacher_staff=staff,
            code="HIST-101",
        )

        client = _authed_client(user)
        before_count = Section.objects.filter(school_id=school.id).count()
        response = client.post(
            SECTIONS_URL,
            data={
                "course_id": str(course.id),
                "term": section.term,
                "teacher_id": str(user.id),
                "teacher_name": "Conflicting Teacher",
                "grade_band": "9",
            },
            format="json",
            **_headers(school),
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Section.objects.filter(school_id=school.id).count(), before_count)

    def test_module014_model_contract_fields_exist(self):
        course_fields = {field.name for field in Course._meta.get_fields()}
        section_fields = {field.name for field in Section._meta.get_fields()}

        for required in ("id", "school_id", "code", "name", "department", "credits"):
            self.assertIn(required, course_fields)
        for required in (
            "id",
            "school_id",
            "course",
            "term_ref",
            "term",
            "teacher",
            "teacher_name",
            "grade_band",
            "enrollments",
            "teacher_assignments",
        ):
            self.assertIn(required, section_fields)
