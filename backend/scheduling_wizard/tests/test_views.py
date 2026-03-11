import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Section
from core.models import School
from scheduling_wizard.models import SchedulingWizardSession

User = get_user_model()

BASE_URL = "/api/v1/scheduling-wizard/sessions/"

VALID_COURSES = [
    {"code": "MATH101", "name": "Algebra I", "department": "Mathematics", "credits": "1.0"},
    {"code": "ENG101", "name": "English Composition", "department": "English", "credits": "1.0"},
]

VALID_SECTIONS = [
    {"course_code": "MATH101", "teacher_name": "Mr. Smith", "grade_band": "9"},
    {"course_code": "ENG101", "teacher_name": "Ms. Jones", "grade_band": "9"},
]


def _make_school(name="Scheduling School"):
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_user(school, username=None):
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(username=username, password="pw")


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for(school):
    user = _make_user(school)
    c = APIClient()
    c.force_authenticate(user=user)
    c._school_id = school.id
    return c


# ---------------------------------------------------------------------------
# TestAuth
# ---------------------------------------------------------------------------

class TestAuth(TestCase):
    def setUp(self):
        self.school = _make_school()

    def test_create_requires_auth(self):
        c = APIClient()
        r = c.post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(r.status_code, 401)

    def test_configure_requires_auth(self):
        c = APIClient()
        session_id = uuid.uuid4()
        r = c.post(f"{BASE_URL}{session_id}/configure/", **_headers(self.school.id))
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# TestTenantIsolation
# ---------------------------------------------------------------------------

class TestTenantIsolation(TestCase):
    def setUp(self):
        self.school_a = _make_school("School A")
        self.school_b = _make_school("School B")
        self.client_a = _client_for(self.school_a)
        self.client_b = _client_for(self.school_b)

        r = self.client_a.post(BASE_URL, **_headers(self.school_a.id))
        self.session_id = r.data["session_id"]

    def _url(self, suffix=""):
        return f"{BASE_URL}{self.session_id}/{suffix}"

    def test_configure_isolation(self):
        r = self.client_b.post(
            self._url("configure/"),
            {"term": "2026-FALL", "school_year": "2026-2027"},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_courses_isolation(self):
        r = self.client_b.post(
            self._url("courses/"),
            {"courses": VALID_COURSES},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_sections_isolation(self):
        r = self.client_b.post(
            self._url("sections/"),
            {"sections": VALID_SECTIONS},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_commit_isolation(self):
        r = self.client_b.post(
            self._url("commit/"),
            {"confirm": True},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_verify_isolation(self):
        r = self.client_b.get(self._url("verify/"), **_headers(self.school_b.id))
        self.assertEqual(r.status_code, 404)


# ---------------------------------------------------------------------------
# TestCreateSession
# ---------------------------------------------------------------------------

class TestCreateSession(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)

    def test_create_returns_201(self):
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(r.status_code, 201)
        self.assertIn("session_id", r.data)
        self.assertEqual(r.data["status"], "draft")

    def test_create_persists_in_db(self):
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.assertTrue(
            SchedulingWizardSession.objects.filter(pk=r.data["session_id"]).exists()
        )


# ---------------------------------------------------------------------------
# TestConfigure
# ---------------------------------------------------------------------------

class TestConfigure(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]

    def _configure(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_configure_success(self):
        r = self._configure({"term": "2026-FALL", "school_year": "2026-2027"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")

    def test_configure_missing_term(self):
        r = self._configure({"school_year": "2026-2027"})
        self.assertEqual(r.status_code, 400)

    def test_configure_term_too_long(self):
        r = self._configure({"term": "X" * 25})
        self.assertEqual(r.status_code, 400)

    def test_configure_reconfigure_allowed(self):
        self._configure({"term": "2026-FALL", "school_year": "2026-2027"})
        r = self._configure({"term": "2026-SPRING", "school_year": "2026-2027"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")


# ---------------------------------------------------------------------------
# TestSaveCourses
# ---------------------------------------------------------------------------

class TestSaveCourses(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL", "school_year": "2026-2027"},
            format="json",
            **_headers(self.school.id),
        )

    def _courses(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/courses/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_save_courses_success(self):
        r = self._courses({"courses": VALID_COURSES})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "courses_saved")
        self.assertEqual(r.data["courses_count"], 2)

    def test_empty_courses_rejected(self):
        r = self._courses({"courses": []})
        self.assertEqual(r.status_code, 400)

    def test_not_a_list_rejected(self):
        r = self._courses({"courses": "MATH101"})
        self.assertEqual(r.status_code, 400)

    def test_missing_code_rejected(self):
        bad = [{"name": "No Code Course", "department": "Math", "credits": "1.0"}]
        r = self._courses({"courses": bad})
        self.assertEqual(r.status_code, 400)

    def test_missing_name_rejected(self):
        bad = [{"code": "MATH101", "department": "Math", "credits": "1.0"}]
        r = self._courses({"courses": bad})
        self.assertEqual(r.status_code, 400)

    def test_duplicate_code_rejected(self):
        bad = [
            {"code": "MATH101", "name": "Algebra", "credits": "1.0"},
            {"code": "MATH101", "name": "Algebra II", "credits": "1.0"},
        ]
        r = self._courses({"courses": bad})
        self.assertEqual(r.status_code, 400)

    def test_negative_credits_rejected(self):
        bad = [{"code": "MATH101", "name": "Algebra", "credits": "-1"}]
        r = self._courses({"courses": bad})
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# TestStageSections
# ---------------------------------------------------------------------------

class TestStageSections(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        h = _headers(self.school.id)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL", "school_year": "2026-2027"},
            format="json",
            **h,
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/courses/",
            {"courses": VALID_COURSES},
            format="json",
            **h,
        )

    def _sections(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/sections/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_stage_sections_success(self):
        r = self._sections({"sections": VALID_SECTIONS})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "sections_staged")
        self.assertEqual(r.data["sections_count"], 2)

    def test_empty_sections_rejected(self):
        r = self._sections({"sections": []})
        self.assertEqual(r.status_code, 400)

    def test_not_a_list_rejected(self):
        r = self._sections({"sections": "MATH101"})
        self.assertEqual(r.status_code, 400)

    def test_missing_course_code_rejected(self):
        bad = [{"teacher_name": "Mr. Smith", "grade_band": "9"}]
        r = self._sections({"sections": bad})
        self.assertEqual(r.status_code, 400)

    def test_unknown_course_code_rejected(self):
        bad = [{"course_code": "FAKE999", "teacher_name": "Mr. X"}]
        r = self._sections({"sections": bad})
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# TestCommit
# ---------------------------------------------------------------------------

class TestCommit(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        h = _headers(self.school.id)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL", "school_year": "2026-2027"},
            format="json",
            **h,
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/courses/",
            {"courses": VALID_COURSES},
            format="json",
            **h,
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/sections/",
            {"sections": VALID_SECTIONS},
            format="json",
            **h,
        )

    def _commit(self, payload=None):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            payload or {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )

    def test_commit_success(self):
        r = self._commit()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "committed")

    def test_commit_creates_courses_in_db(self):
        self._commit()
        self.assertEqual(
            Course.objects.filter(school_id=self.school.id, code="MATH101").count(), 1
        )
        self.assertEqual(
            Course.objects.filter(school_id=self.school.id, code="ENG101").count(), 1
        )

    def test_commit_creates_sections_in_db(self):
        self._commit()
        self.assertEqual(
            Section.objects.filter(school_id=self.school.id, term="2026-FALL").count(), 2
        )

    def test_commit_idempotent(self):
        self._commit()
        r2 = self._commit()
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], "committed")
        # No duplicate sections
        self.assertEqual(
            Section.objects.filter(school_id=self.school.id, term="2026-FALL").count(), 2
        )

    def test_commit_requires_confirm_true(self):
        r = self._commit({"confirm": False})
        self.assertEqual(r.status_code, 400)

    def test_commit_from_draft_rejected(self):
        r_new = self.client.post(BASE_URL, **_headers(self.school.id))
        sid_draft = r_new.data["session_id"]
        r2 = self.client.post(
            f"{BASE_URL}{sid_draft}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r2.status_code, 409)

    def test_commit_result_counts(self):
        r = self._commit()
        self.assertIn("courses_created", r.data)
        self.assertIn("sections_created", r.data)
        self.assertEqual(r.data["courses_created"], 2)
        self.assertEqual(r.data["sections_created"], 2)


# ---------------------------------------------------------------------------
# TestVerify
# ---------------------------------------------------------------------------

class TestVerify(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        h = _headers(self.school.id)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL", "school_year": "2026-2027"},
            format="json",
            **h,
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/courses/",
            {"courses": [{"code": "MATH101", "name": "Algebra", "credits": "1.0"}]},
            format="json",
            **h,
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/sections/",
            {"sections": [{"course_code": "MATH101", "teacher_name": "Mr. Smith"}]},
            format="json",
            **h,
        )
        self.client.post(f"{BASE_URL}{self.session_id}/commit/", {"confirm": True}, format="json", **h)

    def _verify(self):
        return self.client.get(
            f"{BASE_URL}{self.session_id}/verify/",
            **_headers(self.school.id),
        )

    def test_verify_transitions_to_verified(self):
        r = self._verify()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "verified")

    def test_verify_idempotent(self):
        self._verify()
        r2 = self._verify()
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], "verified")

    def test_verify_requires_committed_status(self):
        r_new = self.client.post(BASE_URL, **_headers(self.school.id))
        sid2 = r_new.data["session_id"]
        r2 = self.client.get(f"{BASE_URL}{sid2}/verify/", **_headers(self.school.id))
        self.assertEqual(r2.status_code, 409)

    def test_verify_returns_commit_summary(self):
        r = self._verify()
        self.assertEqual(r.status_code, 200)
        self.assertIn("courses_created", r.data)
        self.assertIn("sections_created", r.data)
