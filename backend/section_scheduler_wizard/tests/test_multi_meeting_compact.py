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

User = get_user_model()
BASE = "/api/v1/section-scheduler-wizard/sessions/"


class MultiMeetingCompactTests(TestCase):
    def test_same_section_publishes_two_recurring_meetings(self):
        school = School.objects.create(name=f"MM-{uuid.uuid4().hex[:6]}", timezone="America/New_York", is_active=True)
        year = AcademicYear.objects.create(school=school, name="2026-2027", start_date=datetime.date(2026,8,1), end_date=datetime.date(2027,6,30), is_current=True)
        structure = TermStructure.objects.create(school=school, academic_year=year, structure_type="SEMESTER", is_active=True)
        period = MarkingPeriod.objects.create(term_structure=structure, code="S1", name="Semester 1", start_date=datetime.date(2026,8,20), end_date=datetime.date(2027,1,15), ordering=1, is_grade_term=True)
        term = Term.objects.create(school_id=school.id, academic_year=year, code="S1", name=period.name, school_year=year.name, start_date=period.start_date, end_date=period.end_date, ordering=1, active=True)
        course = Course.objects.create(school_id=school.id, code="BIO1", name="Biology")
        section = Section.objects.create(school_id=school.id, course=course, term_ref=term, term="S1")
        schedule = BellSchedule.objects.create(school=school, academic_year=year, name="Weekdays", schedule_mode="DAY_TEMPLATES", is_active=True)
        mon = DayTemplate.objects.create(schedule=schedule, template_code="MON", ordering=1)
        wed = DayTemplate.objects.create(schedule=schedule, template_code="WED", ordering=3)
        mon_p1 = PeriodBlock.objects.create(template=mon, code="P1", label="Period 1", start_time=datetime.time(8), end_time=datetime.time(9), ordering=1, is_instructional=True)
        wed_p1 = PeriodBlock.objects.create(template=wed, code="P1", label="Period 1", start_time=datetime.time(8), end_time=datetime.time(9), ordering=1, is_instructional=True)
        room = Room.objects.create(school=school, code="LAB", name="Lab", capacity=24, is_active=True)
        user = User.objects.create_user(username=f"mm-{uuid.uuid4().hex[:6]}", password="test-only", school=school)
        UserRole.objects.create(user=user, school=school, role_code="HEAD_OF_SCHOOL")
        client = APIClient(); client.force_authenticate(user=user)
        headers = {"HTTP_X_SCHOOL_ID": str(school.id)}
        created = client.post(BASE, {}, format="json", **headers)
        configured = client.post(f"{BASE}{created.data['session_id']}/configure/", {"academic_year_id": str(year.id), "term_code":"S1"}, format="json", **headers)
        self.assertEqual(configured.status_code, 200)
        rows = [
            {"section_id":str(section.id), "day_template_id":str(mon.id), "period_block_id":str(mon_p1.id), "room_id":str(room.id)},
            {"section_id":str(section.id), "day_template_id":str(wed.id), "period_block_id":str(wed_p1.id), "room_id":str(room.id)},
        ]
        staged = client.post(f"{BASE}{created.data['session_id']}/sections/", {"sections":rows}, format="json", **headers)
        self.assertEqual(staged.status_code, 200)
        committed = client.post(f"{BASE}{created.data['session_id']}/commit/", {"confirm":True}, format="json", **headers)
        self.assertEqual(committed.status_code, 200)
        self.assertEqual(SectionPlacement.objects.filter(section=section, is_active=True).count(), 2)
        verified = client.get(f"{BASE}{created.data['session_id']}/verify/", **headers)
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(verified.data["count"], 2)
