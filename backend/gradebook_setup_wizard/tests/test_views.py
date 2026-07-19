import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import AssignmentCategory, Course, Section
from core.models import School
from gradebook_setup_wizard.models import GradebookSetupWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/gradebook-setup-wizard/sessions/"


def _make_school():
    return School.objects.create(name=f"GBW {uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _make_user(school):
    return User.objects.create_user(
        username=f"u{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        school=school,
    )


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for(school):
    c = APIClient()
    c.force_authenticate(user=_make_user(school))
    return c


def _make_section(school_id):
    course = Course.objects.create(
        school_id=school_id, code=f"GS{uuid.uuid4().hex[:4]}", name="Test Course"
    )
    return Section.objects.create(school_id=school_id, course=course, term="2026-FALL")


CATS_PAYLOAD = [
    {"name": "Homework", "weight_percent": 30, "sort_order": 0},
    {"name": "Quizzes", "weight_percent": 30, "sort_order": 1},
    {"name": "Tests", "weight_percent": 40, "sort_order": 2},
]

CATS_UNWEIGHTED = [
    {"name": "Homework", "weight_percent": 0, "sort_order": 0},
]


def _advance_to_configured(client, school_id, section_id):
    r = client.post(BASE_URL, **_headers(school_id))
    sid = r.data["session_id"]
    client.post(
        f"{BASE_URL}{sid}/configure/",
        {"section_id": str(section_id)},
        format="json",
        **_headers(school_id),
    )
    return sid


def _advance_to_categories_defined(client, school_id, section_id):
    sid = _advance_to_configured(client, school_id, section_id)
    client.post(
        f"{BASE_URL}{sid}/categories/",
        {"categories": CATS_PAYLOAD},
        format="json",
        **_headers(school_id),
    )
    return sid


def _advance_to_committed(client, school_id, section_id):
    sid = _advance_to_categories_defined(client, school_id, section_id)
    client.post(
        f"{BASE_URL}{sid}/commit/",
        {"confirm": True},
        format="json",
        **_headers(school_id),
    )
    return sid


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class GradebookSetupAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class GradebookSetupCreateTest(TestCase):
    def test_create_returns_201(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], GradebookSetupWizardSession.STATUS_DRAFT)


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class GradebookSetupConfigureTest(TestCase):
    def test_configure_ok(self):
        school = _make_school()
        section = _make_section(school.id)
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"section_id": str(section.id)},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], GradebookSetupWizardSession.STATUS_CONFIGURED)

    def test_configure_missing_section_id(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(f"{BASE_URL}{sid}/configure/", {}, format="json", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_configure_wrong_school_section_returns_404(self):
        school = _make_school()
        other = _make_school()
        section = _make_section(other.id)
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"section_id": str(section.id)},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 404)

    def test_configure_bad_uuid(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"section_id": "not-a-uuid"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)


# ---------------------------------------------------------------------------
# Define categories
# ---------------------------------------------------------------------------

class GradebookSetupCategoriesTest(TestCase):
    def test_define_categories_weighted_ok(self):
        school = _make_school()
        section = _make_section(school.id)
        c = _client_for(school)
        sid = _advance_to_configured(c, school.id, section.id)
        r = c.post(
            f"{BASE_URL}{sid}/categories/",
            {"categories": CATS_PAYLOAD},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], GradebookSetupWizardSession.STATUS_CATEGORIES_DEFINED)
        self.assertEqual(r.data["category_count"], 3)
        self.assertEqual(r.data["total_weight"], 100.0)

    def test_define_categories_unweighted_ok(self):
        school = _make_school()
        section = _make_section(school.id)
        c = _client_for(school)
        sid = _advance_to_configured(c, school.id, section.id)
        r = c.post(
            f"{BASE_URL}{sid}/categories/",
            {"categories": CATS_UNWEIGHTED},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["total_weight"], 0.0)

    def test_define_categories_bad_weight_sum(self):
        school = _make_school()
        section = _make_section(school.id)
        c = _client_for(school)
        sid = _advance_to_configured(c, school.id, section.id)
        r = c.post(
            f"{BASE_URL}{sid}/categories/",
            {"categories": [{"name": "HW", "weight_percent": 50}]},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_define_categories_empty_list(self):
        school = _make_school()
        section = _make_section(school.id)
        c = _client_for(school)
        sid = _advance_to_configured(c, school.id, section.id)
        r = c.post(
            f"{BASE_URL}{sid}/categories/",
            {"categories": []},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_define_categories_from_draft_rejected(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/categories/",
            {"categories": CATS_PAYLOAD},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class GradebookSetupCommitTest(TestCase):
    def test_commit_creates_db_records(self):
        school = _make_school()
        section = _make_section(school.id)
        c = _client_for(school)
        sid = _advance_to_categories_defined(c, school.id, section.id)
        r = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], GradebookSetupWizardSession.STATUS_COMMITTED)
        self.assertEqual(r.data["categories_created"], 3)
        db_count = AssignmentCategory.objects.filter(section=section, school_id=school.id).count()
        self.assertEqual(db_count, 3)

    def test_commit_requires_confirm(self):
        school = _make_school()
        section = _make_section(school.id)
        c = _client_for(school)
        sid = _advance_to_categories_defined(c, school.id, section.id)
        r = c.post(f"{BASE_URL}{sid}/commit/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_is_idempotent(self):
        school = _make_school()
        section = _make_section(school.id)
        c = _client_for(school)
        sid = _advance_to_committed(c, school.id, section.id)
        r2 = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], GradebookSetupWizardSession.STATUS_COMMITTED)
        db_count = AssignmentCategory.objects.filter(section=section).count()
        self.assertEqual(db_count, 3)


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class GradebookSetupVerifyTest(TestCase):
    def test_verify_ok(self):
        school = _make_school()
        section = _make_section(school.id)
        c = _client_for(school)
        sid = _advance_to_committed(c, school.id, section.id)
        r = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], GradebookSetupWizardSession.STATUS_VERIFIED)
        self.assertEqual(r.data["category_count"], 3)

    def test_verify_from_draft_rejected(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)
