from __future__ import annotations

import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import (
    Assignment,
    AssignmentCategory,
    Course,
    Enrollment,
    Section,
    TeacherAssignment,
)
from core.models import (
    Family,
    School,
    Staff,
    Student as CoreStudent,
    StudentIdentityLink,
    UserRole,
)
from crown_api.models import AttendanceRecord
from households.models import Household, Student as HouseholdStudent


pytestmark = pytest.mark.django_db
User = get_user_model()


def setup_teacher_section(code="ELA-500"):
    school = School.objects.create(name=f"Teacher Classwork {uuid.uuid4().hex[:8]}")
    staff = Staff.objects.create(
        school=school,
        first_name="Eleanor",
        last_name="Teacher",
        email=f"teacher-{uuid.uuid4().hex[:8]}@example.org",
        role_type="TEACHER",
        status="ACTIVE",
    )
    teacher = User.objects.create_user(
        username=staff.email,
        email=staff.email,
        password="test-pass",
        school=school,
        staff=staff,
    )
    UserRole.objects.create(school=school, user=teacher, role_code="TEACHER")
    course = Course.objects.create(school_id=school.id, code=code, name="English Language Arts")
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
        teacher=teacher,
        teacher_name="Eleanor Teacher",
        grade_band="5",
    )
    TeacherAssignment.objects.create(school_id=school.id, section=section, staff=staff)
    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Classwork",
        weight_percent=0,
        sort_order=1,
        is_active=True,
    )
    return school, teacher, section, category


def client_for(user, school):
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def test_assigned_teacher_can_create_reopen_and_update_assignment():
    school, teacher, section, category = setup_teacher_section()
    client = client_for(teacher, school)
    created = client.post(f"/api/v1/academics/sections/{section.id}/assignments/", {"name": "Narrative Paragraph", "category_id": str(category.id), "points_possible": "20", "assigned_date": "2026-08-10", "is_published": True}, format="json")
    assert created.status_code == 201, created.data
    assignment_id = created.data["id"]
    assert Assignment.objects.filter(id=assignment_id, section=section).exists()
    reopened = client.get(f"/api/v1/academics/sections/{section.id}/assignments/")
    assert reopened.status_code == 200
    assert any(row["id"] == assignment_id for row in reopened.data["assignments"])
    updated = client.patch(f"/api/v1/academics/assignments/{assignment_id}/", {"points_possible": "25"}, format="json")
    assert updated.status_code == 200
    assert updated.data["points_possible"] == "25.00"


def test_unassigned_teacher_cannot_create_assignment_for_other_section():
    school, teacher, _section, _category = setup_teacher_section("ELA-501")
    other_course = Course.objects.create(school_id=school.id, code="SCI-501", name="Science")
    other = Section.objects.create(school_id=school.id, course=other_course, term="2026-FALL")
    category = AssignmentCategory.objects.create(school_id=school.id, section=other, name="Classwork", weight_percent=0)
    client = client_for(teacher, school)
    denied = client.post(f"/api/v1/academics/sections/{other.id}/assignments/", {"name": "Out of scope", "category_id": str(category.id), "points_possible": "10"}, format="json")
    assert denied.status_code == 403


def test_teacher_roster_id_bridge_persists_attendance_record():
    school, teacher, section, _category = setup_teacher_section("ELA-502")
    stable_id = uuid.uuid4()
    household = Household.objects.create(school_id=school.id, name="Roster Family")
    hh_student = HouseholdStudent.objects.create(id=stable_id, school_id=school.id, household=household, first_name="Caleb", last_name="Demo", grade_level="5", is_active=True)
    family = Family.objects.create(school=school, family_name="Roster Family")
    core_student = CoreStudent.objects.create(id=stable_id, school=school, family=family, student_number="TCHR-001", first_name="Caleb", last_name="Demo", dob=date(2015, 1, 1), status="ACTIVE")
    StudentIdentityLink.objects.create(
        school=school,
        core_student=core_student,
        compatibility_student=hh_student,
        source=StudentIdentityLink.SOURCE_MANUAL,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference="test:teacher-roster-attendance-bridge",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=hh_student)
    client = client_for(teacher, school)
    roster = client.get(f"/api/v1/academics/sections/{section.id}/roster/")
    assert roster.status_code == 200
    assert roster.data["students"][0]["student_id"] == str(stable_id)
    saved = client.post(f"/api/v1/academics/sections/{section.id}/attendance/", {"date": "2026-08-10", "items": [{"student_id": str(stable_id), "status": "ABSENT"}]}, format="json")
    assert saved.status_code == 200, saved.data
    assert saved.data["created"] == 1
    assert AttendanceRecord.objects.filter(student_id=stable_id, date="2026-08-10", status="ABSENT").exists()


def test_assignment_create_validates_required_fields_and_positive_points():
    school, teacher, section, category = setup_teacher_section("ELA-503")
    client = client_for(teacher, school)
    url = f"/api/v1/academics/sections/{section.id}/assignments/"
    assert client.post(url, {"category_id": str(category.id), "points_possible": "10"}, format="json").status_code == 400
    assert client.post(url, {"name": "Missing category", "points_possible": "10"}, format="json").status_code == 400
    assert client.post(url, {"name": "Invalid points", "category_id": str(category.id), "points_possible": "abc"}, format="json").status_code == 400
    assert client.post(url, {"name": "Zero points", "category_id": str(category.id), "points_possible": "0"}, format="json").status_code == 400


def test_admin_can_create_and_teacher_can_patch_all_fields_then_delete():
    school, teacher, section, category = setup_teacher_section("ELA-504")
    admin = User.objects.create_user(username=f"admin-{uuid.uuid4().hex[:8]}@example.org", email=f"admin-{uuid.uuid4().hex[:8]}@example.org", password="test-pass", school=school)
    UserRole.objects.create(school=school, user=admin, role_code="ADMIN")
    created = client_for(admin, school).post(f"/api/v1/academics/sections/{section.id}/assignments/", {"name": "Admin Created", "category_id": str(category.id), "points_possible": "15", "is_published": False}, format="json")
    assert created.status_code == 201, created.data
    assignment_id = created.data["id"]
    second_category = AssignmentCategory.objects.create(school_id=school.id, section=section, name="Projects", weight_percent=0, sort_order=2, is_active=True)
    teacher_client = client_for(teacher, school)
    updated = teacher_client.patch(f"/api/v1/academics/assignments/{assignment_id}/", {"name": "Teacher Revised", "category_id": str(second_category.id), "points_possible": "30", "due_date": "2026-08-20", "assigned_date": "2026-08-11", "is_published": True}, format="json")
    assert updated.status_code == 200, updated.data
    assert updated.data["name"] == "Teacher Revised"
    assert updated.data["category_id"] == str(second_category.id)
    assert updated.data["points_possible"] == "30.00"
    assert updated.data["due_date"] == "2026-08-20"
    assert updated.data["assigned_date"] == "2026-08-11"
    assert updated.data["is_published"] is True
    assert teacher_client.patch(f"/api/v1/academics/assignments/{assignment_id}/", {"name": "   "}, format="json").status_code == 400
    assert teacher_client.delete(f"/api/v1/academics/assignments/{assignment_id}/").status_code == 204
    assert not Assignment.objects.filter(id=assignment_id).exists()


def test_direct_section_teacher_authorization_does_not_require_teacher_assignment_row():
    school, teacher, section, category = setup_teacher_section("ELA-505")
    TeacherAssignment.objects.filter(school_id=school.id, section=section).delete()
    created = client_for(teacher, school).post(f"/api/v1/academics/sections/{section.id}/assignments/", {"name": "Direct teacher", "category_id": str(category.id), "points_possible": "5"}, format="json")
    assert created.status_code == 201, created.data


def test_teacher_without_staff_link_is_denied_and_category_is_section_scoped():
    school, teacher, section, category = setup_teacher_section("ELA-506")
    teacher.staff = None
    teacher.save(update_fields=["staff"])
    client = client_for(teacher, school)
    denied = client.post(f"/api/v1/academics/sections/{section.id}/assignments/", {"name": "No staff link", "category_id": str(category.id), "points_possible": "10"}, format="json")
    assert denied.status_code == 403
    school2, teacher2, section2, category2 = setup_teacher_section("ELA-507")
    client2 = client_for(teacher2, school2)
    wrong_category = client2.post(f"/api/v1/academics/sections/{section2.id}/assignments/", {"name": "Wrong tenant category", "category_id": str(category.id), "points_possible": "10"}, format="json")
    assert wrong_category.status_code == 404
    assert category2.school_id == school2.id
