from datetime import date

from django.test import TestCase

from aid.models import AidAward
from core.models import AcademicYear, Family, School, Student, UserAccount
from sandbox_demo.services import _clear_flagship_data


class FlagshipResetCleanupTests(TestCase):
    def test_clear_flagship_data_deletes_user_linked_aid_awards(self):
        heritage_school = School.objects.create(name="Heritage Test School")
        other_school = School.objects.create(name="Other Test School")
        academic_year = AcademicYear.objects.create(
            school=other_school,
            name="2026-2027",
            start_date=date(2026, 8, 15),
            end_date=date(2027, 6, 5),
            is_current=True,
        )
        family = Family.objects.create(school=other_school, family_name="Reed Family")
        student = Student.objects.create(
            school=other_school,
            family=family,
            student_number="HCA-TEST-0001",
            first_name="Avery",
            last_name="Reed",
            dob=date(2010, 1, 1),
            status="ACTIVE",
        )
        decider = UserAccount.objects.create_user(
            username="director@heritage.example.org",
            email="director@heritage.example.org",
            school=heritage_school,
            password="not-used-in-test",
        )
        award = AidAward.objects.create(
            school=other_school,
            academic_year=academic_year,
            student=student,
            award_type=AidAward.TYPE_NEED,
            awarded_cents=1000,
            decision_status=AidAward.DECISION_ACCEPTED,
            decided_by=decider,
        )

        _clear_flagship_data(heritage_school)

        self.assertFalse(AidAward.objects.filter(pk=award.pk).exists())
        self.assertFalse(UserAccount.objects.filter(pk=decider.pk).exists())
