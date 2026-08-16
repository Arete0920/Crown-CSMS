import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from financial_aid.models import AidAward, AidBucket, FinancialAidApplication
from financial_aid_wizard.models import FinancialAidWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/aid-wizard/sessions/"

VALID_BUCKETS = ["need", "merit", "mission"]

VALID_AWARDS_TEMPLATE = []  # populated in setUp where we have app IDs


def _make_school(name="Aid School"):
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_user(school, username=None):
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(username=username, password=TEST_AUTH_SECRET, school=school)


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for(school):
    user = _make_user(school)
    c = APIClient()
    c.force_authenticate(user=user)
    c._school_id = school.id
    return c


def _make_application(school_id, academic_year="2026-2027"):
    return FinancialAidApplication.objects.create(
        school_id=school_id,
        household_id=uuid.uuid4(),
        academic_year=academic_year,
        household_income=50000,
        household_size=4,
        status="submitted",
    )


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
            {"aid_year": "2026-2027"},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_buckets_isolation(self):
        r = self.client_b.post(
            self._url("buckets/"),
            {"buckets": VALID_BUCKETS},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_awards_isolation(self):
        r = self.client_b.post(
            self._url("awards/"),
            {"awards": []},
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
            FinancialAidWizardSession.objects.filter(pk=r.data["session_id"]).exists()
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
        r = self._configure({"aid_year": "2026-2027"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")

    def test_configure_missing_aid_year(self):
        r = self._configure({})
        self.assertEqual(r.status_code, 400)

    def test_configure_aid_year_too_long(self):
        r = self._configure({"aid_year": "X" * 25})
        self.assertEqual(r.status_code, 400)

    def test_configure_reconfigure_allowed(self):
        self._configure({"aid_year": "2026-2027"})
        r = self._configure({"aid_year": "2027-2028"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")


# ---------------------------------------------------------------------------
# TestSaveBuckets
# ---------------------------------------------------------------------------

class TestSaveBuckets(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"aid_year": "2026-2027"},
            format="json",
            **_headers(self.school.id),
        )

    def _buckets(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/buckets/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_save_buckets_success(self):
        r = self._buckets({"buckets": VALID_BUCKETS})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "buckets_saved")
        self.assertEqual(len(r.data["active_buckets"]), 3)

    def test_empty_buckets_rejected(self):
        r = self._buckets({"buckets": []})
        self.assertEqual(r.status_code, 400)

    def test_invalid_bucket_rejected(self):
        r = self._buckets({"buckets": ["need", "fake_bucket"]})
        self.assertEqual(r.status_code, 400)

    def test_not_a_list_rejected(self):
        r = self._buckets({"buckets": "need"})
        self.assertEqual(r.status_code, 400)

    def test_single_bucket_allowed(self):
        r = self._buckets({"buckets": ["merit"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["active_buckets"], ["merit"])


# ---------------------------------------------------------------------------
# TestStageAwards
# ---------------------------------------------------------------------------

class TestStageAwards(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.app = _make_application(self.school.id)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        h = _headers(self.school.id)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"aid_year": "2026-2027"},
            format="json",
            **h,
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/buckets/",
            {"buckets": VALID_BUCKETS},
            format="json",
            **h,
        )

    def _awards(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/awards/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def _valid_award(self, bucket="need"):
        return {
            "application_id": str(self.app.id),
            "bucket": bucket,
            "amount": "2500.00",
            "rationale": "Need-based award",
        }

    def test_stage_awards_success(self):
        r = self._awards({"awards": [self._valid_award("need"), self._valid_award("merit")]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "awards_staged")
        self.assertEqual(r.data["awards_count"], 2)

    def test_empty_awards_allowed(self):
        r = self._awards({"awards": []})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["awards_count"], 0)

    def test_missing_application_id_rejected(self):
        bad = [{"bucket": "need", "amount": "1000"}]
        r = self._awards({"awards": bad})
        self.assertEqual(r.status_code, 400)

    def test_invalid_bucket_rejected(self):
        bad = [{"application_id": str(self.app.id), "bucket": "fake", "amount": "1000"}]
        r = self._awards({"awards": bad})
        self.assertEqual(r.status_code, 400)

    def test_negative_amount_rejected(self):
        bad = [{"application_id": str(self.app.id), "bucket": "need", "amount": "-500"}]
        r = self._awards({"awards": bad})
        self.assertEqual(r.status_code, 400)

    def test_not_a_list_rejected(self):
        r = self._awards({"awards": "single"})
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# TestCommit
# ---------------------------------------------------------------------------

class TestCommit(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.app = _make_application(self.school.id)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        h = _headers(self.school.id)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"aid_year": "2026-2027"},
            format="json",
            **h,
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/buckets/",
            {"buckets": VALID_BUCKETS},
            format="json",
            **h,
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/awards/",
            {
                "awards": [
                    {
                        "application_id": str(self.app.id),
                        "bucket": "need",
                        "amount": "2000.00",
                        "rationale": "Need award",
                    },
                    {
                        "application_id": str(self.app.id),
                        "bucket": "merit",
                        "amount": "500.00",
                        "rationale": "Merit award",
                    },
                ]
            },
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

    def test_commit_creates_aid_awards_in_db(self):
        self._commit()
        count = AidAward.objects.filter(
            school_id=self.school.id,
            application=self.app,
        ).count()
        self.assertEqual(count, 2)

    def test_commit_idempotent(self):
        self._commit()
        r2 = self._commit()
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], "committed")
        # No duplicates
        self.assertEqual(
            AidAward.objects.filter(school_id=self.school.id, application=self.app).count(),
            2,
        )

    def test_commit_requires_confirm_true(self):
        r = self._commit({"confirm": False})
        self.assertEqual(r.status_code, 400)

    def test_commit_with_empty_awards_allowed(self):
        # New session with an explicitly staged zero-award cycle.
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        sid2 = r.data["session_id"]
        h = _headers(self.school.id)
        self.client.post(f"{BASE_URL}{sid2}/configure/", {"aid_year": "2026-2027"}, format="json", **h)
        self.client.post(f"{BASE_URL}{sid2}/buckets/", {"buckets": ["need"]}, format="json", **h)
        self.client.post(f"{BASE_URL}{sid2}/awards/", {"awards": []}, format="json", **h)
        r2 = self.client.post(f"{BASE_URL}{sid2}/commit/", {"confirm": True}, format="json", **h)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], "committed")
        self.assertEqual(r2.data["awards_created"], 0)
        self.assertEqual(r2.data["awards_skipped"], 0)
        self.assertEqual(r2.data["errors"], [])

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


# ---------------------------------------------------------------------------
# TestVerify
# ---------------------------------------------------------------------------

class TestVerify(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.app = _make_application(self.school.id)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        h = _headers(self.school.id)
        self.client.post(f"{BASE_URL}{self.session_id}/configure/", {"aid_year": "2026-2027"}, format="json", **h)
        self.client.post(f"{BASE_URL}{self.session_id}/buckets/", {"buckets": ["need"]}, format="json", **h)
        self.client.post(
            f"{BASE_URL}{self.session_id}/awards/",
            {"awards": [{"application_id": str(self.app.id), "bucket": "need", "amount": "1000.00"}]},
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
        self.assertIn("awards_created", r.data)
