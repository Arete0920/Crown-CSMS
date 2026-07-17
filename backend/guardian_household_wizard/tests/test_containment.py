import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Family, Guardian, HouseholdFamilyLink, School, Student
from guardian_household_wizard.models import GuardianHouseholdWizardSession
from households.models import Guardian as HouseholdGuardian
from households.models import Household
from households.models import Student as HouseholdStudent


User = get_user_model()
BASE_URL = "/api/v1/guardian-household-wizard/sessions/"
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"


def _school():
    return School.objects.create(
        name=f"School {uuid.uuid4().hex[:8]}",
        timezone="America/New_York",
        is_active=True,
    )


def _client(school):
    user = User.objects.create_user(
        username=f"user-{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        school=school,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _headers(school):
    return {"HTTP_X_SCHOOL_ID": str(school.id)}


def _student(school):
    family = Family.objects.create(
        school=school,
        family_name=f"Family {uuid.uuid4().hex[:8]}",
    )
    return Student.objects.create(
        school=school,
        family=family,
        student_number=f"STU-{uuid.uuid4().hex[:10]}",
        first_name="Taylor",
        last_name="Smith",
        dob=date(2014, 1, 1),
        status="ACTIVE",
    )


def _guardians_added_session(client, school):
    created = client.post(BASE_URL, **_headers(school))
    session_id = created.data["session_id"]
    client.post(
        f"{BASE_URL}{session_id}/configure/",
        {"household_data": {"name": "Smith Family", "address": {}}},
        format="json",
        **_headers(school),
    )
    client.post(
        f"{BASE_URL}{session_id}/add_guardians/",
        {
            "guardian_data": [
                {
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "custody_type": "primary",
                }
            ]
        },
        format="json",
        **_headers(school),
    )
    return session_id


class GuardianHouseholdContainmentTests(TestCase):
    def setUp(self):
        self.school = _school()
        self.client = _client(self.school)
        self.student = _student(self.school)
        self.session_id = _guardians_added_session(self.client, self.school)

    def _link(self, student_id=None):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/link_students/",
            {
                "link_data": [
                    {
                        "student_id": str(student_id or self.student.id),
                        "relationship": "parent",
                    }
                ]
            },
            format="json",
            **_headers(self.school),
        )

    def _commit(self):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school),
        )

    def test_link_students_accepts_same_school_student(self):
        response = self._link()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "students_linked")

    def test_link_students_denies_cross_school_student_without_disclosure(self):
        other_student = _student(_school())
        response = self._link(other_student.id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "One or more students were not found for the active school",
        )
        session = GuardianHouseholdWizardSession.objects.get(id=self.session_id)
        self.assertEqual(session.status, "guardians_added")
        self.assertEqual(session.link_data, [])

    def test_repeated_commit_fails_closed_and_creates_no_identity_records(self):
        self.assertEqual(self._link().status_code, 200)
        before = {
            "core_family": Family.objects.count(),
            "core_guardian": Guardian.objects.count(),
            "core_student": Student.objects.count(),
            "household": Household.objects.count(),
            "household_guardian": HouseholdGuardian.objects.count(),
            "household_student": HouseholdStudent.objects.count(),
            "bridge": HouseholdFamilyLink.objects.count(),
        }

        first = self._commit()
        second = self._commit()

        after = {
            "core_family": Family.objects.count(),
            "core_guardian": Guardian.objects.count(),
            "core_student": Student.objects.count(),
            "household": Household.objects.count(),
            "household_guardian": HouseholdGuardian.objects.count(),
            "household_student": HouseholdStudent.objects.count(),
            "bridge": HouseholdFamilyLink.objects.count(),
        }

        self.assertEqual(first.status_code, 409)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(first.data["code"], "identity_write_target_unresolved")
        self.assertEqual(first.data["architecture_issue"], 1353)
        self.assertEqual(first.data, second.data)
        self.assertEqual(before, after)

        session = GuardianHouseholdWizardSession.objects.get(id=self.session_id)
        self.assertEqual(session.status, "students_linked")
        self.assertIsNone(session.commit_result)
