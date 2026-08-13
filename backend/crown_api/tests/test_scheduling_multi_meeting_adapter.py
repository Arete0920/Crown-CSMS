import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Section, Term
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from core.models import AcademicYear, School, UserAccount
from room_setup_wizard.models import Room
from section_scheduler_wizard.models import SectionPlacement


class SchedulingMultiMeetingAdapterTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Adapter Multi Meeting")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2027, 6, 30),
            is_current=True,
        )
        self.term = Term.objects.create(
            school_id=self.school.id,
            academic_year=self.year,
            code="S1",
            name="Semester 1",
            school_year=self.year.name,
            start_date=datetime.date(2026, 8, 20),
            end_date=datetime.date(2027, 1, 15),
            ordering=1,
            active=True,
        )
        course = Course.objects.create(school_id=self.school.id, code="SCI1", name="Science")
        self.section = Section.objects.create(
            school_id=self.school.id,
            course=course,
            term_ref=self.term,
            term=self.term.code,
        )
        schedule = BellSchedule.objects.create(
            school=self.school,
            academic_year=self.year,
            name="Weekdays",
            schedule_mode="DAY_TEMPLATES",
            is_active=True,
        )
        mon = DayTemplate.objects.create(schedule=schedule, template_code="MON", ordering=1)
        wed = DayTemplate.objects.create(schedule=schedule, template_code="WED", ordering=3)
        mon_block = PeriodBlock.objects.create(
            template=mon,
            code="P1",
            label="Period 1",
            start_time=datetime.time(8, 0),
            end_time=datetime.time(9, 0),
            ordering=1,
            is_instructional=True,
        )
        wed_block = PeriodBlock.objects.create(
            template=wed,
            code="P1",
            label="Period 1",
            start_time=datetime.time(8, 0),
            end_time=datetime.time(9, 0),
            ordering=1,
            is_instructional=True,
        )
        room = Room.objects.create(
            school=self.school,
            code="201",
            name="Room 201",
            capacity=25,
            is_active=True,
        )
        SectionPlacement.objects.create(
            school=self.school,
            academic_year=self.year,
            section=self.section,
            room=room,
            day_template=mon,
            period_block=mon_block,
            is_active=True,
        )
        SectionPlacement.objects.create(
            school=self.school,
            academic_year=self.year,
            section=self.section,
            room=room,
            day_template=wed,
            period_block=wed_block,
            is_active=True,
        )
        self.user = UserAccount.objects.create_user(
            username="adapter-staff",
            password="test-only",
            is_staff=True,
            school=self.school,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_term_sections_exposes_all_recurring_meetings(self):
        response = self.client.get(
            f"/api/terms/{self.term.id}/sections/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row["section_id"], str(self.section.id))
        self.assertEqual(len(row["meetings"]), 2)
        self.assertEqual(
            [meeting["template_code"] for meeting in row["meetings"]],
            ["MON", "WED"],
        )
        self.assertEqual(row["meeting_days"], "MON")
