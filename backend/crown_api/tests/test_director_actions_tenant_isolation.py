import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from aid.models import AidAward
from core.models import AcademicYear, Family, School, Student, UserRole


class DirectorTenantIsolationTest(TestCase):

    def setUp(self):
        User = get_user_model()

        self.school_a = School.objects.create(name="School A")
        self.school_b = School.objects.create(name="School B")

        self.director = User.objects.create_user(
            username="director",
            password="pass",
            is_staff=True,
        )
        self.director.school = self.school_a
        self.director.save()
        UserRole.objects.create(
            user=self.director,
            school=self.school_a,
            role_code="AID_DIRECTOR",
        )

        academic_year = AcademicYear.objects.create(
            school=self.school_b,
            name="2026",
            start_date=datetime.date(2025, 8, 1),
            end_date=datetime.date(2026, 6, 1),
        )
        family_b = Family.objects.create(
            school=self.school_b,
            family_name="Test Family",
        )
        student = Student.objects.create(
            school=self.school_b,
            family=family_b,
            student_number="S99999",
            first_name="Test",
            last_name="Student",
            dob=datetime.date(2010, 1, 1),
        )

        self.award_other_school = AidAward.objects.create(
            school=self.school_b,
            academic_year=academic_year,
            student=student,
            award_type="NEED",
            awarded_cents=100000,
            decision_status=AidAward.DECISION_OFFERED,
        )

    def test_director_cannot_modify_other_school_award(self):
        self.client.login(username="director", password="pass")

        response = self.client.post(
            reverse("director_actions"),
            data={
                "action": "POST_ACCEPTED_AWARDS",
                "school_id": str(self.school_b.id),
                "ids": [str(self.award_other_school.id)],
            },
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(self.school_a.id),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "X-School-Id must match the request school_id.",
        )
