import datetime
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course as AcademicCourse
from academics.models import Section as AcademicSection
from academics.models import Term
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from core.models import AcademicYear, School, UserRole
from room_setup_wizard.models import Room
from section_scheduler_wizard.models import Section as LegacySection
from section_scheduler_wizard.models import SectionPlacement
from term_structure_wizard.models import MarkingPeriod, TermStructure

TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
User = get_user_model()
BASE = "/api/v1/section-scheduler-wizard/sessions/"


def _uid():
    return uuid.uuid4().hex[:8]


def _client_for(school, role="HEAD_OF_SCHOOL"):
    user = User.objects.create_user(
        username=f"u{_uid()}",
        password=TEST_AUTH_SECRET,
        school=school,
    )
    if role:
        UserRole.objects.create(school=school, user=user, role_code=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _headers(school):
    return {"HTTP_X_SCHOOL_ID": str(school.id)}


def _fixtures():
    school = School.objects.create(
        name=f"Scheduling {_uid()}",
        timezone="America/New_York",
        is_active=True,
    )
    ay = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=datetime.date(2026, 8, 20),
        end_date=datetime.date(2027, 6, 10),
        is_current=True,
    )
    structure = TermStructure.objects.create(
        school=school,
        academic_year=ay,
        structure_type="SEMESTER",
        is_active=True,
    )
    period = MarkingPeriod.objects.create(
        term_structure=structure,
        code="S1",
        name="Semester 1",
        start_date=datetime.date(2026, 8, 20),
        end_date=datetime.date(2027, 1, 15),
        ordering=1,
        is_grade_term=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=ay,
        code="S1",
        name=period.name,
        school_year=ay.name,
        start_date=period.start_date,
        end_date=period.end_date,
        ordering=period.ordering,
        active=True,
    )
    course = AcademicCourse.objects.create(
        school_id=school.id,
        code="ENG1",
        name="English 1",
        department="English",
        credits="1.00",
    )
    section = AcademicSection.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term="S1",
        teacher_name="",
        grade_band="9",
    )
    schedule = BellSchedule.objects.create(
        school=school,
        academic_year=ay,
        name="Default",
        schedule_mode="SINGLE_DAY",
        is_active=True,
    )
    template = DayTemplate.objects.create(
        schedule=schedule,
        template_code="DEFAULT",
        ordering=0,
    )
    block = PeriodBlock.objects.create(
        template=template,
        code="P1",
        label="Period 1",
        start_time=datetime.time(8, 0),
        end_time=datetime.time(9, 0),
        ordering=0,
        is_instructional=True,
    )
    room = Room.objects.create(
        school=school,
        code="101",
        name="Room 101",
        capacity=24,
        is_active=True,
    )
    return school, ay, section, template, block, room


def _configured_session(client, school, ay):
    headers = _headers(school)
    created = client.post(BASE, {}, format="json", **headers)
    assert created.status_code == 201
    session_id = created.data["session_id"]
    configured = client.post(
        f"{BASE}{session_id}/configure/",
        {"academic_year_id": str(ay.id), "term_code": "S1"},
        format="json",
        **headers,
    )
    assert configured.status_code == 200
    return session_id


class SectionSchedulerCanonicalizationTests(TestCase):
    def test_unauthorized_role_cannot_create_session(self):
        school, _, _, _, _, _ = _fixtures()
        client = _client_for(school, role=None)
        response = client.post(BASE, {}, format="json", **_headers(school))
        self.assertEqual(response.status_code, 403)

    def test_options_return_canonical_section_and_setup_authorities(self):
        school, ay, section, template, block, room = _fixtures()
        client = _client_for(school)
        session_id = _configured_session(client, school, ay)
        response = client.get(f"{BASE}{session_id}/options/", **_headers(school))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sections"][0]["section_id"], str(section.id))
        self.assertEqual(response.data["rooms"][0]["room_id"], str(room.id))
        self.assertEqual(response.data["day_templates"][0]["day_template_id"], str(template.id))
        self.assertEqual(response.data["day_templates"][0]["blocks"][0]["period_block_id"], str(block.id))

    def test_publish_writes_placement_not_legacy_section(self):
        school, ay, section, template, block, room = _fixtures()
        client = _client_for(school)
        session_id = _configured_session(client, school, ay)
        before_legacy = LegacySection.objects.count()
        payload = {"sections": [{"section_id": str(section.id), "day_template_id": str(template.id), "period_block_id": str(block.id), "room_id": str(room.id)}]}
        staged = client.post(f"{BASE}{session_id}/sections/", payload, format="json", **_headers(school))
        self.assertEqual(staged.status_code, 200)
        committed = client.post(f"{BASE}{session_id}/commit/", {"confirm": True}, format="json", **_headers(school))
        self.assertEqual(committed.status_code, 200)
        self.assertEqual(LegacySection.objects.count(), before_legacy)
        placement = SectionPlacement.objects.get(section=section)
        self.assertEqual(placement.room_id, room.id)
        self.assertEqual(placement.period_block_id, block.id)

    def test_retry_is_idempotent(self):
        school, ay, section, template, block, room = _fixtures()
        client = _client_for(school)
        session_id = _configured_session(client, school, ay)
        payload = {"sections": [{"section_id": str(section.id), "day_template_id": str(template.id), "period_block_id": str(block.id), "room_id": str(room.id)}]}
        client.post(f"{BASE}{session_id}/sections/", payload, format="json", **_headers(school))
        first = client.post(f"{BASE}{session_id}/commit/", {"confirm": True}, format="json", **_headers(school))
        second = client.post(f"{BASE}{session_id}/commit/", {"confirm": True}, format="json", **_headers(school))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(SectionPlacement.objects.filter(section=section).count(), 1)

    def test_cross_tenant_section_is_rejected(self):
        school, ay, _, template, block, room = _fixtures()
        other_school, _, other_section, _, _, _ = _fixtures()
        self.assertNotEqual(school.id, other_school.id)
        client = _client_for(school)
        session_id = _configured_session(client, school, ay)
        response = client.post(
            f"{BASE}{session_id}/sections/",
            {"sections": [{"section_id": str(other_section.id), "day_template_id": str(template.id), "period_block_id": str(block.id), "room_id": str(room.id)}]},
            format="json",
            **_headers(school),
        )
        self.assertEqual(response.status_code, 400)

    def test_room_collision_rejects_whole_publish(self):
        school, ay, section, template, block, room = _fixtures()
        second_course = AcademicCourse.objects.create(
            school_id=school.id,
            code="MATH1",
            name="Math 1",
            department="Math",
            credits="1.00",
        )
        second_section = AcademicSection.objects.create(
            school_id=school.id,
            course=second_course,
            term_ref=section.term_ref,
            term="S1",
            teacher_name="",
            grade_band="9",
        )
        client = _client_for(school)
        session_id = _configured_session(client, school, ay)
        staged = client.post(
            f"{BASE}{session_id}/sections/",
            {"sections": [
                {"section_id": str(section.id), "day_template_id": str(template.id), "period_block_id": str(block.id), "room_id": str(room.id)},
                {"section_id": str(second_section.id), "day_template_id": str(template.id), "period_block_id": str(block.id), "room_id": str(room.id)},
            ]},
            format="json",
            **_headers(school),
        )
        self.assertEqual(staged.status_code, 200)
        committed = client.post(f"{BASE}{session_id}/commit/", {"confirm": True}, format="json", **_headers(school))
        self.assertEqual(committed.status_code, 400)
        self.assertEqual(SectionPlacement.objects.count(), 0)
