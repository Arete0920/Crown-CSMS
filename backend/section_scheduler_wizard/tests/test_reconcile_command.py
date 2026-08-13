import datetime
import io
import uuid
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from academics.models import Course as AcademicCourse, Section as AcademicSection, Term
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from core.models import AcademicYear, School
from course_catalog_wizard.models import Course as LegacyCourse
from room_setup_wizard.models import Room
from section_scheduler_wizard.models import Section as LegacySection, SectionPlacement
from term_structure_wizard.models import MarkingPeriod, TermStructure


def build_fixture():
    school = School.objects.create(name=f"R{uuid.uuid4().hex[:6]}", timezone="America/New_York", is_active=True)
    ay = AcademicYear.objects.create(school=school, name="2026-2027", start_date=datetime.date(2026,8,20), end_date=datetime.date(2027,6,10), is_current=True)
    structure = TermStructure.objects.create(school=school, academic_year=ay, structure_type="SEMESTER", is_active=True)
    period = MarkingPeriod.objects.create(term_structure=structure, code="S1", name="Semester 1", start_date=datetime.date(2026,8,20), end_date=datetime.date(2027,1,15), ordering=1, is_grade_term=True)
    term = Term.objects.create(school_id=school.id, academic_year=ay, code="S1", name=period.name, school_year=ay.name, start_date=period.start_date, end_date=period.end_date, ordering=1, active=True)
    course = AcademicCourse.objects.create(school_id=school.id, code="ENG1", name="English 1", department="English", credits="1.00")
    section = AcademicSection.objects.create(school_id=school.id, course=course, term_ref=term, term="S1", teacher_name="", grade_band="9")
    legacy_course = LegacyCourse.objects.create(school=school, code="ENG1", name="English 1", credits="1.0", department="English", is_active=True)
    schedule = BellSchedule.objects.create(school=school, academic_year=ay, name="Default", schedule_mode="SINGLE_DAY", is_active=True)
    template = DayTemplate.objects.create(schedule=schedule, template_code="DEFAULT", ordering=0)
    PeriodBlock.objects.create(template=template, code="P1", label="Period 1", start_time=datetime.time(8,0), end_time=datetime.time(9,0), ordering=0, is_instructional=True)
    room = Room.objects.create(school=school, code="101", name="Room 101", capacity=24, is_active=True)
    LegacySection.objects.create(school=school, academic_year=ay, section_code="ENG1-A", course=legacy_course, term_code="S1", room=room, template_code="DEFAULT", block_code="P1", is_active=True)
    return school, ay, course, section, term


class ReconcileLegacySchedulerTests(TestCase):
    def test_dry_run_then_apply(self):
        school, ay, _, section, _ = build_fixture()
        out = io.StringIO()
        call_command("reconcile_legacy_scheduler", school_id=str(school.id), academic_year_id=str(ay.id), stdout=out)
        self.assertEqual(SectionPlacement.objects.count(), 0)
        self.assertIn('"planned": 1', out.getvalue())
        call_command("reconcile_legacy_scheduler", school_id=str(school.id), academic_year_id=str(ay.id), apply=True)
        self.assertEqual(SectionPlacement.objects.filter(section=section).count(), 1)
        self.assertEqual(LegacySection.objects.count(), 1)

    def test_ambiguous_mapping_blocks_all_writes(self):
        school, ay, course, _, term = build_fixture()
        AcademicSection.objects.create(school_id=school.id, course=course, term_ref=term, term="S1", teacher_name="", grade_band="9")
        with self.assertRaises(CommandError):
            call_command("reconcile_legacy_scheduler", school_id=str(school.id), academic_year_id=str(ay.id), apply=True)
        self.assertEqual(SectionPlacement.objects.count(), 0)
