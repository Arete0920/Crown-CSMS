"""
Tests for Spiritual Life Module API.

Covers:
- Tenant scoping: invalid UUID header → 400, cross-school → 404
- Chapel Events: CRUD, date filters
- Chapel Attendance: record, upsert, list
- Small Groups: create, list, members, sessions, session attendance
- Student Spiritual Profiles: create/upsert, list, detail, patch
- Spiritual Assessments: create, list, filter by student
- Prayer Requests: create, list (RBAC visibility), private gate
- Pastoral Notes: RBAC (staff-only), create, list, filter, patch, delete
"""
from __future__ import annotations

import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Family, School, Student, UserRole
from spiritual_life.models import (
    ChapelEvent,
    ChapelAttendance,
    SmallGroup,
    SmallGroupMember,
    SmallGroupSession,
    PrayerRequest,
    PastoralNote,
    StudentSpiritualProfile,
    SpiritualAssessment,
)

pytestmark = pytest.mark.django_db

User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mk_school(name: str = "Crown Academy") -> School:
    return School.objects.create(name=name)


def _mk_family(school: School, name: str = "Test Family") -> Family:
    return Family.objects.create(school=school, family_name=name)


def _mk_student(school: School, family: Family, num: str = "S001") -> Student:
    return Student.objects.create(
        school=school,
        family=family,
        student_number=num,
        first_name="Grace",
        last_name="Hopper",
        dob="2010-01-15",
    )


def _mk_user(
    *,
    school: School,
    email: str,
    is_staff: bool = False,
    is_superuser: bool = False,
) -> User:
    return User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="test-pass",
        school=school,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )


def _assign_role(*, user: User, school: School, role_code: str) -> None:
    UserRole.objects.create(school=school, user=user, role_code=role_code)


def _client(user: User) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _chapel(school: School, user: User, title: str = "Chapel #1",
            event_date: str = "2026-03-01") -> ChapelEvent:
    return ChapelEvent.objects.create(
        school=school, title=title, event_date=event_date, created_by=user
    )


BASE = "/api/spiritual-life"


# ---------------------------------------------------------------------------
# 1. Tenant Scoping
# ---------------------------------------------------------------------------

class TestSpiritualLifeTenantScoping:
    def test_invalid_uuid_header_returns_400_on_chapel_events(self):
        school = _mk_school()
        user = _mk_user(school=school, email="scope1@test.com")
        c = _client(user)
        resp = c.get(f"{BASE}/chapel-events/", HTTP_X_SCHOOL_ID="not-a-uuid")
        assert resp.status_code == 400

    def test_invalid_uuid_header_returns_400_on_pastoral_notes(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="scope2@test.com", is_staff=True)
        c = _client(staff)
        resp = c.get(f"{BASE}/pastoral-notes/", HTTP_X_SCHOOL_ID="not-a-uuid")
        assert resp.status_code == 400

    def test_cross_school_chapel_event_returns_404(self):
        school_a = _mk_school("School A")
        school_b = _mk_school("School B")
        user_a = _mk_user(school=school_a, email="usera@test.com")
        user_b = _mk_user(school=school_b, email="userb@test.com")
        chapel = _chapel(school_b, user_b, title="B Chapel")
        # User A sends school B's UUID — non-staff, cross-tenant → 404
        c = _client(user_a)
        resp = c.get(
            f"{BASE}/chapel-events/{chapel.id}/",
            HTTP_X_SCHOOL_ID=str(school_b.id),
        )
        assert resp.status_code == 404

    def test_unauthenticated_request_returns_401_or_403(self):
        school = _mk_school()
        c = APIClient()
        resp = c.get(f"{BASE}/chapel-events/", HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 2. Chapel Events
# ---------------------------------------------------------------------------

class TestChapelEvents:
    def test_create_chapel_event_201(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chapel1@test.com", is_staff=True)
        c = _client(user)
        payload = {
            "title": "Morning Chapel",
            "event_date": "2026-03-10",
            "speaker": "Pastor James",
            "location": "Sanctuary",
        }
        resp = c.post(f"{BASE}/chapel-events/", payload, HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code == 201
        assert resp.data["title"] == "Morning Chapel"
        assert ChapelEvent.objects.filter(school=school, title="Morning Chapel").exists()

    def test_create_chapel_event_missing_title_returns_400(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chapel2@test.com", is_staff=True)
        c = _client(user)
        resp = c.post(
            f"{BASE}/chapel-events/",
            {"event_date": "2026-03-10"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 400

    def test_create_chapel_event_missing_date_returns_400(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chapel3@test.com", is_staff=True)
        c = _client(user)
        resp = c.post(
            f"{BASE}/chapel-events/",
            {"title": "No Date Chapel"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 400

    def test_list_chapel_events_200(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chapel4@test.com")
        _chapel(school, user, title="Chapel A", event_date="2026-02-01")
        _chapel(school, user, title="Chapel B", event_date="2026-03-01")
        c = _client(user)
        resp = c.get(f"{BASE}/chapel-events/", HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code == 200
        assert len(resp.data) == 2

    def test_list_chapel_events_date_from_filter(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chapel5@test.com")
        _chapel(school, user, title="Old Chapel", event_date="2025-12-01")
        _chapel(school, user, title="New Chapel", event_date="2026-03-01")
        c = _client(user)
        resp = c.get(
            f"{BASE}/chapel-events/?date_from=2026-01-01",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        titles = [e["title"] for e in resp.data]
        assert "New Chapel" in titles
        assert "Old Chapel" not in titles

    def test_chapel_event_detail_get(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chapel6@test.com")
        chapel = _chapel(school, user, title="Detail Chapel")
        c = _client(user)
        resp = c.get(
            f"{BASE}/chapel-events/{chapel.id}/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert resp.data["title"] == "Detail Chapel"

    def test_chapel_event_patch(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chapel7@test.com")
        chapel = _chapel(school, user, title="Before Patch")
        c = _client(user)
        resp = c.patch(
            f"{BASE}/chapel-events/{chapel.id}/",
            {"title": "After Patch"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert resp.data["title"] == "After Patch"


# ---------------------------------------------------------------------------
# 3. Chapel Attendance
# ---------------------------------------------------------------------------

class TestChapelAttendance:
    def test_record_chapel_attendance_201(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chatt1@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SA001")
        chapel = _chapel(school, user)
        c = _client(user)
        resp = c.post(
            f"{BASE}/chapel-events/{chapel.id}/attendance/",
            {"student_id": str(student.id), "status": "present"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 201
        assert resp.data["status"] == "present"

    def test_record_attendance_upserts_status(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chatt2@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SA002")
        chapel = _chapel(school, user)
        ChapelAttendance.objects.create(
            school=school, event=chapel, student=student, status="present"
        )
        c = _client(user)
        resp = c.post(
            f"{BASE}/chapel-events/{chapel.id}/attendance/",
            {"student_id": str(student.id), "status": "excused"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert resp.data["status"] == "excused"
        assert ChapelAttendance.objects.filter(event=chapel, student=student).count() == 1

    def test_list_chapel_attendance(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chatt3@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SA003")
        chapel = _chapel(school, user)
        ChapelAttendance.objects.create(
            school=school, event=chapel, student=student, status="present"
        )
        c = _client(user)
        resp = c.get(
            f"{BASE}/chapel-events/{chapel.id}/attendance/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_chapel_attendance_missing_student_id_returns_400(self):
        school = _mk_school()
        user = _mk_user(school=school, email="chatt4@test.com")
        chapel = _chapel(school, user)
        c = _client(user)
        resp = c.post(
            f"{BASE}/chapel-events/{chapel.id}/attendance/",
            {"status": "present"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 4. Small Groups
# ---------------------------------------------------------------------------

class TestSmallGroups:
    def test_create_small_group_201(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sg1@test.com")
        c = _client(user)
        resp = c.post(
            f"{BASE}/small-groups/",
            {"name": "Senior Bible Study"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 201
        assert resp.data["name"] == "Senior Bible Study"

    def test_create_small_group_missing_name_returns_400(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sg2@test.com")
        c = _client(user)
        resp = c.post(
            f"{BASE}/small-groups/",
            {"description": "No name"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 400

    def test_list_small_groups_active_only(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sg3@test.com")
        SmallGroup.objects.create(school=school, name="Active Group", is_active=True)
        SmallGroup.objects.create(school=school, name="Inactive Group", is_active=False)
        c = _client(user)
        resp = c.get(f"{BASE}/small-groups/", HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code == 200
        names = [g["name"] for g in resp.data]
        assert "Active Group" in names
        assert "Inactive Group" not in names

    def test_list_small_groups_all_when_active_only_false(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sg4@test.com")
        SmallGroup.objects.create(school=school, name="Active", is_active=True)
        SmallGroup.objects.create(school=school, name="Inactive", is_active=False)
        c = _client(user)
        resp = c.get(
            f"{BASE}/small-groups/?active_only=false",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert len(resp.data) == 2

    def test_add_member_to_small_group_201(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sg5@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SG001")
        group = SmallGroup.objects.create(school=school, name="Juniors")
        c = _client(user)
        resp = c.post(
            f"{BASE}/small-groups/{group.id}/members/",
            {"student_id": str(student.id)},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 201
        assert SmallGroupMember.objects.filter(group=group, student=student).exists()

    def test_add_member_idempotent(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sg6@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SG002")
        group = SmallGroup.objects.create(school=school, name="Freshmen")
        SmallGroupMember.objects.create(school=school, group=group, student=student)
        c = _client(user)
        resp = c.post(
            f"{BASE}/small-groups/{group.id}/members/",
            {"student_id": str(student.id)},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert SmallGroupMember.objects.filter(group=group, student=student).count() == 1

    def test_create_small_group_session_201(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sg7@test.com")
        group = SmallGroup.objects.create(school=school, name="Seniors")
        c = _client(user)
        resp = c.post(
            f"{BASE}/small-groups/{group.id}/sessions/",
            {"session_date": "2026-03-15", "topic": "Faith & Works"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 201
        assert resp.data["topic"] == "Faith & Works"

    def test_create_session_missing_date_returns_400(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sg8@test.com")
        group = SmallGroup.objects.create(school=school, name="Sophomores")
        c = _client(user)
        resp = c.post(
            f"{BASE}/small-groups/{group.id}/sessions/",
            {"topic": "No date"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 5. Small Group Attendance
# ---------------------------------------------------------------------------

class TestSmallGroupAttendance:
    def test_record_session_attendance_201(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sga1@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SGA001")
        group = SmallGroup.objects.create(school=school, name="Prayer Warriors")
        member = SmallGroupMember.objects.create(
            school=school, group=group, student=student
        )
        session = SmallGroupSession.objects.create(
            school=school, group=group, session_date="2026-03-20"
        )
        c = _client(user)
        resp = c.post(
            f"{BASE}/small-group-sessions/{session.id}/attendance/",
            {"member_id": str(member.id), "status": "present"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 201
        assert resp.data["status"] == "present"

    def test_session_attendance_upserts_status(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sga2@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SGA002")
        group = SmallGroup.objects.create(school=school, name="Discipleship")
        member = SmallGroupMember.objects.create(
            school=school, group=group, student=student
        )
        session = SmallGroupSession.objects.create(
            school=school, group=group, session_date="2026-03-21"
        )
        from spiritual_life.models import SmallGroupAttendance
        SmallGroupAttendance.objects.create(
            school=school, session=session, member=member, status="absent"
        )
        c = _client(user)
        resp = c.post(
            f"{BASE}/small-group-sessions/{session.id}/attendance/",
            {"member_id": str(member.id), "status": "excused"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert resp.data["status"] == "excused"

    def test_list_session_attendance(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sga3@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SGA003")
        group = SmallGroup.objects.create(school=school, name="Mentoring")
        member = SmallGroupMember.objects.create(
            school=school, group=group, student=student
        )
        session = SmallGroupSession.objects.create(
            school=school, group=group, session_date="2026-03-22"
        )
        from spiritual_life.models import SmallGroupAttendance
        SmallGroupAttendance.objects.create(
            school=school, session=session, member=member, status="present"
        )
        c = _client(user)
        resp = c.get(
            f"{BASE}/small-group-sessions/{session.id}/attendance/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert len(resp.data) == 1


# ---------------------------------------------------------------------------
# 6. Student Spiritual Profiles
# ---------------------------------------------------------------------------

class TestSpiritualProfiles:
    def test_create_profile_200(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sp1@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SP001")
        c = _client(user)
        payload = {
            "student_id": str(student.id),
            "faith_background": "Reformed",
            "baptized": True,
            "baptism_date": "2020-06-15",
        }
        resp = c.post(
            f"{BASE}/profiles/",
            payload,
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert resp.data["faith_background"] == "Reformed"

    def test_create_profile_upserts(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sp2@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SP002")
        StudentSpiritualProfile.objects.create(
            school=school, student=student, faith_background="Baptist"
        )
        c = _client(user)
        resp = c.post(
            f"{BASE}/profiles/",
            {"student_id": str(student.id), "faith_background": "Presbyterian"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert StudentSpiritualProfile.objects.filter(school=school, student=student).count() == 1
        assert resp.data["faith_background"] == "Presbyterian"

    def test_list_profiles(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sp3@test.com")
        family = _mk_family(school)
        s1 = _mk_student(school, family, num="SP003")
        s2 = _mk_student(school, family, num="SP004")
        StudentSpiritualProfile.objects.create(school=school, student=s1)
        StudentSpiritualProfile.objects.create(school=school, student=s2)
        c = _client(user)
        resp = c.get(f"{BASE}/profiles/", HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code == 200
        assert len(resp.data) == 2

    def test_profile_detail_get(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sp4@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SP005")
        profile = StudentSpiritualProfile.objects.create(
            school=school, student=student, faith_background="Lutheran"
        )
        c = _client(user)
        resp = c.get(
            f"{BASE}/profiles/{profile.id}/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert resp.data["faith_background"] == "Lutheran"

    def test_profile_patch(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sp5@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="SP006")
        profile = StudentSpiritualProfile.objects.create(
            school=school, student=student, spiritual_gifts="Teaching"
        )
        c = _client(user)
        resp = c.patch(
            f"{BASE}/profiles/{profile.id}/",
            {"spiritual_gifts": "Teaching, Evangelism"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert "Evangelism" in resp.data["spiritual_gifts"]

    def test_missing_student_id_returns_400(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sp6@test.com")
        c = _client(user)
        resp = c.post(
            f"{BASE}/profiles/",
            {"faith_background": "Baptist"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 7. Spiritual Assessments
# ---------------------------------------------------------------------------

class TestSpiritualAssessments:
    def test_create_assessment_201(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sa1@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="ASS001")
        c = _client(user)
        resp = c.post(
            f"{BASE}/assessments/",
            {
                "student_id": str(student.id),
                "assessment_title": "Worldview Test",
                "assessment_date": "2026-02-01",
                "score": "85.00",
                "max_score": "100.00",
            },
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 201
        assert resp.data["assessment_title"] == "Worldview Test"

    def test_list_assessments(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sa2@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="ASS002")
        SpiritualAssessment.objects.create(
            school=school, student=student,
            assessment_title="Quiz 1", assessment_date="2026-01-01"
        )
        c = _client(user)
        resp = c.get(f"{BASE}/assessments/", HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_filter_assessments_by_student(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sa3@test.com")
        family = _mk_family(school)
        s1 = _mk_student(school, family, num="ASS003")
        s2 = _mk_student(school, family, num="ASS004")
        SpiritualAssessment.objects.create(
            school=school, student=s1,
            assessment_title="For S1", assessment_date="2026-01-01"
        )
        SpiritualAssessment.objects.create(
            school=school, student=s2,
            assessment_title="For S2", assessment_date="2026-01-02"
        )
        c = _client(user)
        resp = c.get(
            f"{BASE}/assessments/?student_id={s1.id}",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        titles = [a["assessment_title"] for a in resp.data]
        assert "For S1" in titles
        assert "For S2" not in titles

    def test_create_assessment_missing_fields_returns_400(self):
        school = _mk_school()
        user = _mk_user(school=school, email="sa4@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="ASS005")
        c = _client(user)
        # Missing assessment_title
        resp = c.post(
            f"{BASE}/assessments/",
            {"student_id": str(student.id), "assessment_date": "2026-02-01"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 8. Prayer Requests
# ---------------------------------------------------------------------------

class TestPrayerRequests:
    def test_create_prayer_request_201(self):
        school = _mk_school()
        user = _mk_user(school=school, email="pr1@test.com")
        c = _client(user)
        resp = c.post(
            f"{BASE}/prayer-requests/",
            {
                "title": "Healing",
                "body": "Please pray for healing",
                "visibility": "staff",
            },
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 201
        assert resp.data["title"] == "Healing"

    def test_non_pastor_cannot_create_private_prayer_request(self):
        school = _mk_school()
        # Non-staff user with TEACHER role
        user = _mk_user(school=school, email="pr2@test.com")
        _assign_role(user=user, school=school, role_code="TEACHER")
        c = _client(user)
        resp = c.post(
            f"{BASE}/prayer-requests/",
            {"title": "Secret", "body": "Private prayer", "visibility": "private"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 403

    def test_staff_can_create_private_prayer_request(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="pr3@test.com", is_staff=True)
        c = _client(staff)
        resp = c.post(
            f"{BASE}/prayer-requests/",
            {"title": "Private Request", "body": "Staff only", "visibility": "private"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 201

    def test_non_staff_list_excludes_private_requests(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="pr4a@test.com", is_staff=True)
        teacher = _mk_user(school=school, email="pr4b@test.com")
        _assign_role(user=teacher, school=school, role_code="TEACHER")
        PrayerRequest.objects.create(
            school=school, title="Private", body="Secret",
            visibility="private", submitted_by=staff
        )
        PrayerRequest.objects.create(
            school=school, title="Staff", body="For staff",
            visibility="staff", submitted_by=teacher
        )
        c = _client(teacher)
        resp = c.get(f"{BASE}/prayer-requests/", HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code == 200
        titles = [r["title"] for r in resp.data]
        assert "Private" not in titles
        assert "Staff" in titles

    def test_staff_list_includes_private_requests(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="pr5@test.com", is_staff=True)
        PrayerRequest.objects.create(
            school=school, title="Private", body="Secret",
            visibility="private", submitted_by=staff
        )
        c = _client(staff)
        resp = c.get(f"{BASE}/prayer-requests/", HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code == 200
        titles = [r["title"] for r in resp.data]
        assert "Private" in titles

    def test_missing_title_returns_400(self):
        school = _mk_school()
        user = _mk_user(school=school, email="pr6@test.com")
        c = _client(user)
        resp = c.post(
            f"{BASE}/prayer-requests/",
            {"body": "No title"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 9. Pastoral Notes — Staff Only
# ---------------------------------------------------------------------------

class TestPastoralNotes:
    def test_non_staff_get_pastoral_notes_returns_403(self):
        school = _mk_school()
        teacher = _mk_user(school=school, email="pn1@test.com")
        _assign_role(user=teacher, school=school, role_code="TEACHER")
        c = _client(teacher)
        resp = c.get(f"{BASE}/pastoral-notes/", HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code == 403

    def test_non_staff_create_pastoral_note_returns_403(self):
        school = _mk_school()
        teacher = _mk_user(school=school, email="pn2@test.com")
        family = _mk_family(school)
        student = _mk_student(school, family, num="PN001")
        c = _client(teacher)
        resp = c.post(
            f"{BASE}/pastoral-notes/",
            {
                "student_id": str(student.id),
                "note_date": "2026-02-25",
                "body": "Should be blocked",
            },
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 403

    def test_staff_create_pastoral_note_201(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="pn3@test.com", is_staff=True)
        family = _mk_family(school)
        student = _mk_student(school, family, num="PN002")
        c = _client(staff)
        resp = c.post(
            f"{BASE}/pastoral-notes/",
            {
                "student_id": str(student.id),
                "note_date": "2026-02-25",
                "body": "Student expressed doubts in counseling session.",
            },
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 201
        assert "doubts" in resp.data["body"]
        assert PastoralNote.objects.filter(school=school, student=student).exists()

    def test_staff_list_pastoral_notes(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="pn4@test.com", is_staff=True)
        family = _mk_family(school)
        student = _mk_student(school, family, num="PN003")
        PastoralNote.objects.create(
            school=school, student=student, author=staff,
            note_date="2026-02-01", body="Note A"
        )
        c = _client(staff)
        resp = c.get(f"{BASE}/pastoral-notes/", HTTP_X_SCHOOL_ID=str(school.id))
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_staff_filter_pastoral_notes_by_student(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="pn5@test.com", is_staff=True)
        family = _mk_family(school)
        s1 = _mk_student(school, family, num="PN004")
        s2 = _mk_student(school, family, num="PN005")
        PastoralNote.objects.create(
            school=school, student=s1, author=staff,
            note_date="2026-02-01", body="Note for S1"
        )
        PastoralNote.objects.create(
            school=school, student=s2, author=staff,
            note_date="2026-02-02", body="Note for S2"
        )
        c = _client(staff)
        resp = c.get(
            f"{BASE}/pastoral-notes/?student_id={s1.id}",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        bodies = [n["body"] for n in resp.data]
        assert "Note for S1" in bodies
        assert "Note for S2" not in bodies

    def test_staff_patch_pastoral_note(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="pn6@test.com", is_staff=True)
        family = _mk_family(school)
        student = _mk_student(school, family, num="PN006")
        note = PastoralNote.objects.create(
            school=school, student=student, author=staff,
            note_date="2026-02-01", body="Original body"
        )
        c = _client(staff)
        resp = c.patch(
            f"{BASE}/pastoral-notes/{note.id}/",
            {"body": "Updated body"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 200
        assert resp.data["body"] == "Updated body"

    def test_staff_delete_pastoral_note_204(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="pn7@test.com", is_staff=True)
        family = _mk_family(school)
        student = _mk_student(school, family, num="PN007")
        note = PastoralNote.objects.create(
            school=school, student=student, author=staff,
            note_date="2026-02-01", body="To be deleted"
        )
        c = _client(staff)
        resp = c.delete(
            f"{BASE}/pastoral-notes/{note.id}/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 204
        assert not PastoralNote.objects.filter(id=note.id).exists()

    def test_missing_required_fields_returns_400(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="pn8@test.com", is_staff=True)
        family = _mk_family(school)
        student = _mk_student(school, family, num="PN008")
        c = _client(staff)
        # Missing body
        resp = c.post(
            f"{BASE}/pastoral-notes/",
            {"student_id": str(student.id), "note_date": "2026-02-25"},
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert resp.status_code == 400

    def test_tenant_isolation_pastoral_notes(self):
        """Staff at school A cannot see school B's pastoral notes."""
        school_a = _mk_school("School Alpha")
        school_b = _mk_school("School Beta")
        staff_a = _mk_user(school=school_a, email="pna@test.com", is_staff=True)
        staff_b = _mk_user(school=school_b, email="pnb@test.com", is_staff=True)
        family_b = _mk_family(school_b, "Beta Family")
        student_b = _mk_student(school_b, family_b, num="PNB001")
        PastoralNote.objects.create(
            school=school_b, student=student_b, author=staff_b,
            note_date="2026-02-01", body="School B note"
        )
        # Staff A (is_staff=True) can override tenant header — so should only see school A's notes
        c = _client(staff_a)
        resp = c.get(
            f"{BASE}/pastoral-notes/",
            HTTP_X_SCHOOL_ID=str(school_a.id),
        )
        assert resp.status_code == 200
        bodies = [n["body"] for n in resp.data]
        assert "School B note" not in bodies
