import uuid
import datetime
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School, AcademicYear
from term_structure_wizard.models import TermStructure, MarkingPeriod
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from course_catalog_wizard.models import Course
from staff_setup_wizard.models import StaffMember
from room_setup_wizard.models import Room

User = get_user_model()
BASE = "/api/v1/section-scheduler-wizard/sessions/"


def _uid():
    return uuid.uuid4().hex[:6]


def _user():
    return User.objects.create_user(username=f"u{_uid()}", password="pw")


def _authed():
    c = APIClient()
    c.force_authenticate(user=_user())
    return c


def _hdr(sid):
    return {"HTTP_X_SCHOOL_ID": str(sid)}


def _fixtures():
    """Return (school, ay, client, extra_context) with all required fixtures."""
    school = School.objects.create(name=f"S{_uid()}", timezone="America/New_York", is_active=True)
    ay = AcademicYear.objects.create(
        school=school,
        name="2025-2026",
        start_date=datetime.date(2025, 9, 1),
        end_date=datetime.date(2026, 6, 30),
        is_current=True,
    )
    ts = TermStructure.objects.create(
        school=school,
        academic_year=ay,
        structure_type="SEMESTER",
        is_active=True,
    )
    MarkingPeriod.objects.create(
        term_structure=ts,
        code="S1",
        name="Semester 1",
        start_date=datetime.date(2025, 9, 1),
        end_date=datetime.date(2026, 1, 31),
        ordering=1,
        is_grade_term=True,
    )
    sched = BellSchedule.objects.create(
        school=school,
        academic_year=ay,
        name="Default",
        schedule_mode="SINGLE_DAY",
        is_active=True,
    )
    tpl = DayTemplate.objects.create(schedule=sched, template_code="DEFAULT", ordering=0)
    PeriodBlock.objects.create(
        template=tpl,
        code="P1",
        label="Period 1",
        start_time=datetime.time(8, 0),
        end_time=datetime.time(9, 0),
        ordering=0,
        is_instructional=True,
    )
    Course.objects.create(school=school, code="ENG1", name="English 1", is_active=True)
    return school, ay, _authed()


class SectionSchedulerWizardSmoke(TestCase):
    def test_happy(self):
        school, ay, c = _fixtures()
        h = _hdr(school.id)

        r = c.post(BASE, **h)
        self.assertEqual(r.status_code, 201)
        sid = r.data["session_id"]

        r2 = c.post(
            f"{BASE}{sid}/configure/",
            {"academic_year_id": str(ay.id), "term_code": "S1"},
            format="json",
            **h,
        )
        self.assertEqual(r2.status_code, 200)

        sections = [{"section_code": "ENG1-A", "course_code": "ENG1", "template_code": "DEFAULT", "block_code": "P1"}]
        r3 = c.post(f"{BASE}{sid}/sections/", {"sections": sections}, format="json", **h)
        self.assertEqual(r3.status_code, 200)

        r4 = c.post(f"{BASE}{sid}/commit/", format="json", **h)
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(r4.data["total"], 1)

        r5 = c.get(f"{BASE}{sid}/verify/", **h)
        self.assertEqual(r5.status_code, 200)
        self.assertEqual(r5.data["count"], 1)

    def test_invalid_term_code_rejected(self):
        school, ay, c = _fixtures()
        h = _hdr(school.id)
        r = c.post(BASE, **h)
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE}{sid}/configure/",
            {"academic_year_id": str(ay.id), "term_code": "BADTERM"},
            format="json",
            **h,
        )
        self.assertEqual(r2.status_code, 400)

    def test_invalid_block_code_rejected(self):
        school, ay, c = _fixtures()
        h = _hdr(school.id)
        r = c.post(BASE, **h)
        sid = r.data["session_id"]
        c.post(
            f"{BASE}{sid}/configure/",
            {"academic_year_id": str(ay.id), "term_code": "S1"},
            format="json",
            **h,
        )
        sections = [{"section_code": "ENG1-A", "course_code": "ENG1", "template_code": "DEFAULT", "block_code": "BADBLOCK"}]
        r3 = c.post(f"{BASE}{sid}/sections/", {"sections": sections}, format="json", **h)
        self.assertEqual(r3.status_code, 400)
