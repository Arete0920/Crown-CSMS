import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from grade_weights_wizard.models import GradeWeightsWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/grade-weights-wizard/sessions/"

CATEGORIES_STAGED = [
    {"name": "Homework", "weight_pct": 30, "drop_lowest": 1, "description": "Daily work"},
    {"name": "Quizzes",  "weight_pct": 30, "drop_lowest": 0, "description": "Short assessments"},
    {"name": "Tests",    "weight_pct": 40, "drop_lowest": 0, "description": "Major assessments"},
]


def _school():
    return School.objects.create(name=f"S{uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _client(school):
    u = User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _h(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


class TestGradeWeightsWizardCreate(TestCase):
    def test_create_returns_201(self):
        school = _school()
        c = _client(school)
        r = c.post(BASE_URL, **_h(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertIn("session_id", r.data)

    def test_create_requires_auth(self):
        school = _school()
        r = self.client.post(BASE_URL, HTTP_X_SCHOOL_ID=str(school.id))
        self.assertEqual(r.status_code, 401)


class TestGradeWeightsWizardConfigure(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        self.session_id = r.data["session_id"]

    def test_configure_ok(self):
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"marking_period": "Q1-2026"},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")

    def test_configure_missing_marking_period(self):
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 400)


class TestGradeWeightsWizardStageCategories(TestCase):
    def setUp(self):
        self.school = _school()
        self.c = _client(self.school)
        r = self.c.post(BASE_URL, **_h(self.school.id))
        sid = r.data["session_id"]
        self.c.post(
            f"{BASE_URL}{sid}/configure/",
            {"marking_period": "Q1-2026"},
            format="json",
            **_h(self.school.id),
        )
        self.session_id = sid

    def test_stage_categories_ok(self):
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/stage_categories/",
            {"categories_staged": CATEGORIES_STAGED},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["category_count"], 3)
        self.assertEqual(r.data["total_weight_pct"], 100)

    def test_stage_categories_weight_not_100(self):
        bad = [{"name": "Homework", "weight_pct": 50}]  # only 50, not 100
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/stage_categories/",
            {"categories_staged": bad},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_stage_categories_missing_name(self):
        bad = [{"weight_pct": 100}]
        r = self.c.post(
            f"{BASE_URL}{self.session_id}/stage_categories/",
            {"categories_staged": bad},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(r.status_code, 400)


class TestGradeWeightsWizardTenantIsolation(TestCase):
    def test_cross_tenant_returns_404(self):
        school_a = _school()
        school_b = _school()
        c_a = _client(school_a)
        c_b = _client(school_b)
        r = c_a.post(BASE_URL, **_h(school_a.id))
        sid = r.data["session_id"]
        r2 = c_b.post(
            f"{BASE_URL}{sid}/configure/",
            {"marking_period": "Q1-2026"},
            format="json",
            **_h(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)
