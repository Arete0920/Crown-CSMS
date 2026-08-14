from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Term
from academic_year_wizard.models import AcademicYearWizardSession
from core.models import AcademicYear, School, UserRole


BASE_URL = "/api/v1/academic-year-wizard/sessions/"
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
User = get_user_model()


def _client():
    client = APIClient()
    user = User.objects.create_user(username="term-boundary-user", password=TEST_AUTH_SECRET)
    user.is_staff = True
    user.is_superuser = True
    user.save(update_fields=["is_staff", "is_superuser"])
    client.force_authenticate(user=user)
    return client


def _headers(school):
    return {"HTTP_X_SCHOOL_ID": str(school.id)}


def _configured_session(client, school):
    created = client.post(BASE_URL, **_headers(school))
    session_id = created.data["session_id"]
    configured = client.post(
        f"{BASE_URL}{session_id}/configure/",
        {
            "year_name": "2027-2028",
            "start_date": "2027-08-01",
            "end_date": "2028-05-31",
        },
        format="json",
        **_headers(school),
    )
    assert configured.status_code == 200, configured.data
    return session_id


class AcademicYearTermBoundaryTest(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Term Boundary School",
            timezone="America/Chicago",
            is_active=True,
        )
        self.client = _client()

    def test_ordinary_authenticated_user_cannot_start_rollover(self):
        user = User.objects.create_user(username="ordinary-rollover-user", password=TEST_AUTH_SECRET)
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(BASE_URL, **_headers(self.school))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(AcademicYearWizardSession.objects.count(), 0)

    def test_head_of_school_can_start_rollover(self):
        user = User.objects.create_user(username="head-rollover-user", password=TEST_AUTH_SECRET)
        UserRole.objects.create(school=self.school, user=user, role_code="HEAD_OF_SCHOOL")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(BASE_URL, **_headers(self.school))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(AcademicYearWizardSession.objects.filter(school=self.school).count(), 1)

    def test_set_terms_rejects_non_object_term(self):
        session_id = _configured_session(self.client, self.school)
        response = self.client.post(
            f"{BASE_URL}{session_id}/terms/",
            {"terms": ["not-an-object"]},
            format="json",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("terms[0] must be an object", response.data["errors"])

    def test_set_terms_rejects_term_outside_academic_year(self):
        session_id = _configured_session(self.client, self.school)
        response = self.client.post(
            f"{BASE_URL}{session_id}/terms/",
            {
                "terms": [
                    {
                        "code": "FALL-2028",
                        "name": "Fall 2028",
                        "start_date": "2028-08-25",
                        "end_date": "2028-12-20",
                        "ordering": 0,
                    }
                ]
            },
            format="json",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(any("configured academic year" in error for error in response.data["errors"]))

    def test_set_terms_rejects_reversed_term_dates(self):
        session_id = _configured_session(self.client, self.school)
        response = self.client.post(
            f"{BASE_URL}{session_id}/terms/",
            {
                "terms": [
                    {
                        "code": "FALL-2027",
                        "name": "Fall 2027",
                        "start_date": "2027-12-20",
                        "end_date": "2027-08-25",
                        "ordering": 0,
                    }
                ]
            },
            format="json",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(any("on or after start_date" in error for error in response.data["errors"]))

    def test_commit_rejects_empty_persisted_term_configuration(self):
        session_id = _configured_session(self.client, self.school)
        session = AcademicYearWizardSession.objects.get(pk=session_id)
        session.terms_config = []
        session.status = AcademicYearWizardSession.STATUS_TERMS_SET
        session.save(update_fields=["terms_config", "status", "updated_at"])

        response = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("terms must be a non-empty list", response.data["errors"])
        self.assertFalse(AcademicYear.objects.filter(school=self.school, name="2027-2028").exists())

    def test_commit_revalidates_persisted_term_configuration(self):
        session_id = _configured_session(self.client, self.school)
        session = AcademicYearWizardSession.objects.get(pk=session_id)
        session.terms_config = [
            {
                "code": "FALL-2028",
                "name": "Fall 2028",
                "start_date": "2028-08-25",
                "end_date": "2028-12-20",
                "ordering": 0,
            }
        ]
        session.status = AcademicYearWizardSession.STATUS_TERMS_SET
        session.save(update_fields=["terms_config", "status", "updated_at"])

        response = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            **_headers(self.school),
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(AcademicYear.objects.filter(school=self.school, name="2027-2028").exists())
        self.assertEqual(Term.objects.filter(school_id=self.school.id).count(), 0)
