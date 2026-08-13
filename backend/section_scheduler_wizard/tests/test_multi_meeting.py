import datetime
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Section, Term
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from core.models import AcademicYear, School, UserRole
from room_setup_wizard.models import Room
from section_scheduler_wizard.models import SectionPlacement
from term_structure_wizard.models import MarkingPeriod, TermStructure


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
User = get_user_model()
BASE = "/api/v1/section-scheduler-wizard/sessions/"


class MultiMeetingSectionTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name=f"Multi Meeting {uuid.uuid4().hex[:8]}",
            timezone="America/New_York",
            is_active=True,
        )
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=datetime.date(2026, 8, 20),
            end_date=datetime.date(2027, 6, 10),
            is_current=True,
        )
        structure = TermStructure.objects.create(
            school=self.school,
            academic_year=self.year,
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
            school_id=self.school.id,
            academic_year=self.year,
            code="S1",
            name=period.name,
            school_year=self.year.name,
            start_date=period.start_date,
            end_date=period.end_date,
            ordering=1,
            active=True,
        )
        course = Course.objects.create(
            school_id=self.school.id,
            code="BIO1",
            name="Biology",
            credits="1.00",
        )
        self.section = Section.objects.create(
            school_id=self.school.id,
            course=course,
            term_ref=term,
            term="S1",
            grade_band="10",
        )
        schedule = BellSchedule.objects.create(
            school=self.school,
            academic_year=self.year,
            name="Weekday Rotation",
            schedule_mode="DAY_TEMPLATES",
            is_active=True,
        )
        self.mon = DayTemplate.objects.create(schedule=schedule, template_code="MON", ordering=1)
        self.wed = DayTemplate.objects.create(schedule=schedule, template_code="WED", ordering=3)
        self.mon_p1 = PeriodBlock.objects.create(
            template=self.mon,
            code="P1",
            label="Period 1",
            start_time=datetime.time(8, 0),
            end_time=datetime.time(9, 0),
            ordering=1,
            is_instructional=True,
        )
        self.wed_p1 = PeriodBlock.objects.create(
            template=self.wed,
            code="P1",
            label="Period 1",
            start_time=datetime.time(8, 0),
            end_time=datetime.time(9, 0),
            ordering=1,
            is_instructional=True,
        )
        self.room = Room.objects.create(
            school=self.school,
            code="LAB1",
            name="Science Lab",
            capacity=24,
            is_active=True,
        )
        user = User.objects.create_user(
            username=f"scheduler-{uuid.uuid4().hex[:8]}",
            password=TEST_AUTH_SECRET,
            school=self.school,
        )
        UserRole.objects.create(school=self.school, user=user, role_code="HEAD_OF_SCHOOL")
        self.client = APIClient()
        self.client.force_authenticate(user=user)
        self.headers = {"HTTP_X_SCHOOL_ID": str(self.school.id)}

        created = self.client.post(BASE, {}, format="json", **self.headers)
        self.assertEqual(created.status_code, 201)
        self.session_id = created.data["session_id"]
        configured = self.client.post(
            f"{BASE}{self.session_id}/configure/",
            {"academic_year_id": str(self.year.id), "term_code": "S1"},
            format="json",
            **self.headers,
        )
        self.assertEqual(configured.status_code, 200)

    def _meetings(self):
        return [
            {
                "section_id": str(self.section.id),
                "day_template_id": str(self.mon.id),
                "period_block_id": str(self.mon_p1.id),
                "room_id": str(self.room.id),
            },
            {
                "section_id": str(self.section.id),
                "day_template_id": str(self.wed.id),
                "period_block_id": str(self.wed_p1.id),
                "room_id": str(self.room.id),
            },
        ]

    def test_same_section_can_stage_two_recurring_meetings(self):
        response = self.client.post(
            f"{BASE}{self.session_id}/sections/",
            {"sections": self._meetings()},
            format="json",
            **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

    def test_duplicate_exact_meeting_is_rejected(self):
        meeting = self._meetings()[0]
        response = self.client.post(
            f"{BASE}{self.session_id}/sections/",
            {"sections": [meeting, dict(meeting)]},
            format="json",
            **self.headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_publish_persists_both_meetings_and_verify_matches(self):
        staged = self.client.post(
            f"{BASE}{self.session_id}/sections/",
            {"sections": self._meetings()},
            format="json",
            **self.headers,
        )
        self.assertEqual(staged.status_code, 200)
        committed = self.client.post(
            f"{BASE}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **self.headers,
        )
        self.assertEqual(committed.status_code, 200)
        self.assertEqual(committed.data["created"], 2)
        self.assertEqual(
            SectionPlacement.objects.filter(section=self.section, is_active=True).count(),
            2,
        )
        verified = self.client.get(
            f"{BASE}{self.session_id}/verify/",
            **self.headers,
        )
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(verified.data["count"], 2)
        self.assertEqual(
            {row["template_code"] for row in verified.data["sections"]},
            {"MON", "WED"},
        )

    def test_publish_retry_is_idempotent_for_multi_meeting(self):
        self.client.post(
            f"{BASE}{self.session_id}/sections/",
            {"sections": self._meetings()},
            format="json",
            **self.headers,
        )
        first = self.client.post(
            f"{BASE}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **self.headers,
        )
        second = self.client.post(
            f"{BASE}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **self.headers,
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            SectionPlacement.objects.filter(section=self.section, is_active=True).count(),
            2,
        )
