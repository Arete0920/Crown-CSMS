from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import UserAccount, School, Family, Student, HouseholdFamilyLink
from crown_api.models import Course, Household, HouseholdMember, Person, Section, SectionEnrollment, Term, UserPersonLink
from crown_api.models_households import ROLE_GUARDIAN


class SchedulingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.school = School.objects.create(name="Test School")

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass",
            is_staff=True,
            school=self.school,
        )

        self.parent_user = UserAccount.objects.create_user(
            username="parentuser",
            email="parent@example.com",
            password="testpass",
            is_staff=False,
            school=self.school,
        )

        self.household_a = Household.objects.create(household_name="Household A")
        self.household_b = Household.objects.create(household_name="Household B")

        self.parent_person = Person.objects.create(
            first_name="Parent",
            last_name="A",
            email="parent@example.com",
        )
        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
        HouseholdMember.objects.create(
            household=self.household_a,
            person=self.parent_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        # Create core School and Family for core.models.Student
        # school created above; Family and Student follow
        self.family_a = Family.objects.create(school=self.school, family_name="Family A")
        self.family_b = Family.objects.create(school=self.school, family_name="Family B")

        # Create core.models.Student objects
        self.student_a = Student.objects.create(
            school=self.school,
            family=self.family_a,
            student_number="STU001",
            first_name="Student",
            last_name="A",
            dob=date(2018, 1, 1),
            status='ACTIVE',
        )
        self.student_b = Student.objects.create(
            school=self.school,
            family=self.family_b,
            student_number="STU002",
            first_name="Student",
            last_name="B",
            dob=date(2016, 1, 1),
            status='ACTIVE',
        )
        
        # Link families to households for parent scoping
        from admissions.models import AdmissionsApplication
        from core.models import AcademicYear
        from datetime import datetime
        ay = AcademicYear.objects.create(
            school=self.school,
            name="2026",
            start_date=datetime(2026, 1, 1).date(),
            end_date=datetime(2026, 12, 31).date(),
            is_current=True,
        )
        AdmissionsApplication.objects.create(
            school=self.school,
            academic_year=ay,
            family=self.family_a,
            student=self.student_a,
            household=self.household_a,
        )
        AdmissionsApplication.objects.create(
            school=self.school,
            academic_year=ay,
            family=self.family_b,
            student=self.student_b,
            household=self.household_b,
        )

        # HouseholdFamilyLink is required by get_core_student_or_404_for_request
        # for parent schedule scoping (replaces AdmissionsApplication bridge)
        HouseholdFamilyLink.objects.create(
            school=self.school,
            household_id=self.household_a.id,
            family=self.family_a,
            source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
        )

        self.term_active = Term.objects.create(
            code="2026-SPR",
            name="Spring 2026",
            active=True,
            start_date=date(2026, 1, 10),
            end_date=date(2026, 5, 20),
        )
        self.term_inactive = Term.objects.create(
            code="2025-FALL",
            name="Fall 2025",
            active=False,
            start_date=date(2025, 8, 20),
            end_date=date(2025, 12, 15),
        )

        self.course_math = Course.objects.create(course_code="MATH-101", name="Math", term="2026", active=True)
        self.course_ela = Course.objects.create(course_code="ELA-101", name="ELA", term="2026", active=True)

        self.teacher = Person.objects.create(first_name="Teacher", last_name="One", email="teacher@example.com")

        # Sections in active term
        self.section_math_a = Section.objects.create(
            term=self.term_active,
            course=self.course_math,
            section_code="A",
            teacher=self.teacher,
            room="101",
            meeting_days="MWF",
            meeting_time="09:00",
        )
        self.section_math_b = Section.objects.create(
            term=self.term_active,
            course=self.course_math,
            section_code="B",
            teacher=None,
            room="102",
            meeting_days="TR",
            meeting_time="10:00",
        )
        self.section_ela_a = Section.objects.create(
            term=self.term_active,
            course=self.course_ela,
            section_code="A",
            teacher=self.teacher,
            room="201",
            meeting_days="MWF",
            meeting_time="11:00",
        )

        # Enroll only student_a into two sections
        SectionEnrollment.objects.create(section=self.section_math_a, student=self.student_a, active=True)
        SectionEnrollment.objects.create(section=self.section_ela_a, student=self.student_a, active=True)

        # Enroll student_b into math_b so staff sees it, parent does not
        SectionEnrollment.objects.create(section=self.section_math_b, student=self.student_b, active=True)

    def test_staff_terms_sections_and_schedule(self):
        self.client.force_authenticate(user=self.staff_user)

        resp_terms = self.client.get("/api/terms/")
        self.assertEqual(resp_terms.status_code, 200)
        self.assertEqual({t["code"] for t in resp_terms.json()}, {"2026-SPR", "2025-FALL"})

        resp_sections = self.client.get(f"/api/terms/{self.term_active.id}/sections/")
        self.assertEqual(resp_sections.status_code, 200)
        section_ids = {row["section_id"] for row in resp_sections.json()}
        self.assertEqual(
            section_ids,
            {str(self.section_math_a.id), str(self.section_math_b.id), str(self.section_ela_a.id)},
        )

        resp_sched = self.client.get(f"/api/students/{self.student_a.id}/schedule/")
        self.assertEqual(resp_sched.status_code, 200)

    def test_parent_scoped_terms_sections_and_schedule(self):
        self.client.force_authenticate(user=self.parent_user)

        resp_terms = self.client.get("/api/terms/")
        self.assertEqual(resp_terms.status_code, 200)
        # Non-staff sees active terms only
        self.assertEqual({t["code"] for t in resp_terms.json()}, {"2026-SPR"})

        resp_sections = self.client.get(f"/api/terms/{self.term_active.id}/sections/")
        self.assertEqual(resp_sections.status_code, 200)
        section_ids = {row["section_id"] for row in resp_sections.json()}
        self.assertEqual(section_ids, {str(self.section_math_a.id), str(self.section_ela_a.id)})

        resp_sched = self.client.get(f"/api/students/{self.student_a.id}/schedule/")
        self.assertEqual(resp_sched.status_code, 200)
        body = resp_sched.json()
        self.assertEqual(len(body), 2)

        # Out-of-scope student schedule should 404
        resp_other = self.client.get(f"/api/students/{self.student_b.id}/schedule/")
        self.assertEqual(resp_other.status_code, 404)

    def test_unauth_terms_403(self):
        # IsAuthenticated + JWT configured → DRF emits 401 (not 403) for unauthenticated
        resp = self.client.get("/api/terms/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 401)
