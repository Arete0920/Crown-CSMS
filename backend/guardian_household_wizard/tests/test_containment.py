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


def _family(school, name=None):
    return Family.objects.create(
        school=school,
        family_name=name or f"Family {uuid.uuid4().hex[:8]}",
    )


def _student(school, family=None, first_name="Taylor"):
    family = family or _family(school)
    return Student.objects.create(
        school=school,
        family=family,
        student_number=f"STU-{uuid.uuid4().hex[:10]}",
        first_name=first_name,
        last_name="Smith",
        dob=date(2014, 1, 1),
        status="ACTIVE",
    )


def _guardians_added_session(client, school, family_name="Smith Family", email="jane@example.com"):
    created = client.post(BASE_URL, **_headers(school))
    session_id = created.data["session_id"]
    configured = client.post(
        f"{BASE_URL}{session_id}/configure/",
        {
            "household_data": {
                "name": family_name,
                "address": {
                    "street": "10 Main Street",
                    "city": "Middletown",
                    "state": "DE",
                    "zip": "19709",
                },
            }
        },
        format="json",
        **_headers(school),
    )
    assert configured.status_code == 200
    guardians = client.post(
        f"{BASE_URL}{session_id}/add_guardians/",
        {
            "guardian_data": [
                {
                    "name": "Jane Smith",
                    "email": email,
                    "phone": "302-555-0100",
                    "custody_type": "primary",
                }
            ]
        },
        format="json",
        **_headers(school),
    )
    assert guardians.status_code == 200
    return session_id


class GuardianHouseholdCanonicalCommitTests(TestCase):
    def setUp(self):
        self.school = _school()
        self.client = _client(self.school)
        self.family = _family(self.school, "Original Family")
        self.student = _student(self.school, self.family)
        self.session_id = _guardians_added_session(self.client, self.school)

    def _link(self, student_ids=None):
        student_ids = student_ids or [self.student.id]
        return self.client.post(
            f"{BASE_URL}{self.session_id}/link_students/",
            {
                "link_data": [
                    {"student_id": str(student_id), "relationship": "parent"}
                    for student_id in student_ids
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

    def test_full_commit_and_verify_use_core_only(self):
        self.assertEqual(self._link().status_code, 200)
        before_legacy = {
            "household": Household.objects.count(),
            "guardian": HouseholdGuardian.objects.count(),
            "student": HouseholdStudent.objects.count(),
            "bridge": HouseholdFamilyLink.objects.count(),
        }

        committed = self._commit()
        self.assertEqual(committed.status_code, 200)
        self.assertEqual(committed.data["status"], "committed")
        self.assertEqual(committed.data["canonical_model"], "core")
        self.assertEqual(committed.data["family_id"], str(self.family.id))
        self.assertEqual(committed.data["student_ids"], [str(self.student.id)])

        self.family.refresh_from_db()
        self.assertEqual(self.family.family_name, "Smith Family")
        self.assertEqual(self.family.address_line1, "10 Main Street")
        self.assertEqual(self.family.city, "Middletown")
        self.assertEqual(self.family.state, "DE")
        self.assertEqual(self.family.zip_code, "19709")

        guardian = Guardian.objects.get(school=self.school, email="jane@example.com")
        self.assertEqual(guardian.family, self.family)
        self.assertEqual(guardian.first_name, "Jane")
        self.assertEqual(guardian.last_name, "Smith")
        self.assertTrue(guardian.custody_flag)

        after_legacy = {
            "household": Household.objects.count(),
            "guardian": HouseholdGuardian.objects.count(),
            "student": HouseholdStudent.objects.count(),
            "bridge": HouseholdFamilyLink.objects.count(),
        }
        self.assertEqual(before_legacy, after_legacy)

        verified = self.client.get(
            f"{BASE_URL}{self.session_id}/verify/", **_headers(self.school)
        )
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(verified.data["status"], "verified")
        self.assertEqual(verified.data["family_id"], str(self.family.id))

    def test_repeated_commit_is_idempotent(self):
        self.assertEqual(self._link().status_code, 200)
        first = self._commit()
        counts = {
            "family": Family.objects.count(),
            "guardian": Guardian.objects.count(),
            "student": Student.objects.count(),
        }
        second = self._commit()

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data, second.data)
        self.assertEqual(
            counts,
            {
                "family": Family.objects.count(),
                "guardian": Guardian.objects.count(),
                "student": Student.objects.count(),
            },
        )

    def test_cross_school_student_is_denied_without_disclosure(self):
        other_student = _student(_school())
        response = self._link([other_student.id])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "One or more students were not found for the active school",
        )
        session = GuardianHouseholdWizardSession.objects.get(id=self.session_id)
        self.assertEqual(session.status, "guardians_added")
        self.assertEqual(session.link_data, [])

    def test_mixed_family_students_are_rejected_without_writes(self):
        other_student = _student(self.school, _family(self.school, "Other Family"), "Jordan")
        self.assertEqual(self._link([self.student.id, other_student.id]).status_code, 200)
        before = {
            "family_name": self.family.family_name,
            "guardians": Guardian.objects.count(),
        }

        response = self._commit()
        self.assertEqual(response.status_code, 409)
        self.assertIn("will not silently merge or reassign", response.data["error"])
        self.family.refresh_from_db()
        self.assertEqual(self.family.family_name, before["family_name"])
        self.assertEqual(Guardian.objects.count(), before["guardians"])
        session = GuardianHouseholdWizardSession.objects.get(id=self.session_id)
        self.assertEqual(session.status, "students_linked")
        self.assertIsNone(session.commit_result)

    def test_guardian_attached_to_other_family_rolls_back(self):
        other_family = _family(self.school, "Other Family")
        Guardian.objects.create(
            school=self.school,
            family=other_family,
            first_name="Existing",
            last_name="Guardian",
            email="jane@example.com",
            relationship="GUARDIAN",
        )
        self.assertEqual(self._link().status_code, 200)
        original_name = self.family.family_name

        response = self._commit()
        self.assertEqual(response.status_code, 409)
        self.assertIn("another family", response.data["error"])
        self.family.refresh_from_db()
        self.assertEqual(self.family.family_name, original_name)
        self.assertEqual(Guardian.objects.filter(email="jane@example.com").count(), 1)
        session = GuardianHouseholdWizardSession.objects.get(id=self.session_id)
        self.assertEqual(session.status, "students_linked")
        self.assertIsNone(session.commit_result)

    def test_invalid_guardian_name_rolls_back(self):
        session = GuardianHouseholdWizardSession.objects.get(id=self.session_id)
        session.guardian_data = [{"name": "Jane", "email": "jane@example.com"}]
        session.save(update_fields=["guardian_data", "updated_at"])
        self.assertEqual(self._link().status_code, 200)
        original_name = self.family.family_name

        response = self._commit()
        self.assertEqual(response.status_code, 400)
        self.assertIn("first and last name", response.data["error"])
        self.family.refresh_from_db()
        self.assertEqual(self.family.family_name, original_name)
        self.assertFalse(Guardian.objects.filter(email="jane@example.com").exists())
