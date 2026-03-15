import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from billing.models import InstallmentPlan
from billing_wizard.models import BillingWizardSession

User = get_user_model()

BASE_URL = "/api/v1/billing-wizard/sessions/"

VALID_PLANS = [
    {
        "name": "Annual Pay",
        "installment_count": 1,
        "first_due_on": "2026-08-01",
        "cadence_days": 0,
        "total_amount": "10500.00",
    },
    {
        "name": "10-Pay",
        "installment_count": 10,
        "first_due_on": "2026-08-01",
        "cadence_days": 30,
        "total_amount": "10500.00",
    },
]

VALID_FEES = [
    {"name": "Registration Fee", "fee_type": "REGISTRATION", "amount": "250.00", "is_recurring": False},
    {"name": "Tech Fee", "fee_type": "TECH", "amount": "150.00", "is_recurring": True},
]


def _make_school(name="Test School"):
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

        # Create a session under school_a
        r = self.client_a.post(BASE_URL, **_headers(self.school_a.id))
        self.session_id = r.data["session_id"]

    def _url(self, suffix=""):
        return f"{BASE_URL}{self.session_id}/{suffix}"

    def test_configure_isolation(self):
        r = self.client_b.post(self._url("configure/"), {"term": "2026-FALL", "billing_mode": "simple"}, format="json", **_headers(self.school_b.id))
        self.assertEqual(r.status_code, 404)

    def test_plans_isolation(self):
        r = self.client_b.post(self._url("plans/"), {"plans": VALID_PLANS}, format="json", **_headers(self.school_b.id))
        self.assertEqual(r.status_code, 404)

    def test_fees_isolation(self):
        r = self.client_b.post(self._url("fees/"), {"fees": VALID_FEES}, format="json", **_headers(self.school_b.id))
        self.assertEqual(r.status_code, 404)

    def test_commit_isolation(self):
        r = self.client_b.post(self._url("commit/"), {"confirm": True}, format="json", **_headers(self.school_b.id))
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
        self.assertTrue(BillingWizardSession.objects.filter(pk=r.data["session_id"]).exists())


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
        r = self._configure({"term": "2026-FALL", "billing_mode": "simple"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")

    def test_configure_missing_term(self):
        r = self._configure({"billing_mode": "simple"})
        self.assertEqual(r.status_code, 400)

    def test_configure_invalid_mode(self):
        r = self._configure({"term": "2026-FALL", "billing_mode": "turbo"})
        self.assertEqual(r.status_code, 400)

    def test_configure_reconfigure_allowed(self):
        self._configure({"term": "2026-FALL", "billing_mode": "simple"})
        r = self._configure({"term": "2026-SPRING", "billing_mode": "advanced"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")

    def test_configure_term_too_long(self):
        r = self._configure({"term": "X" * 25, "billing_mode": "simple"})
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# TestSavePlans
# ---------------------------------------------------------------------------

class TestSavePlans(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL", "billing_mode": "simple"},
            format="json",
            **_headers(self.school.id),
        )

    def _plans(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/plans/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_save_plans_success(self):
        r = self._plans({"plans": VALID_PLANS})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "plans_saved")
        self.assertEqual(r.data["plans_count"], 2)

    def test_empty_plans_list_rejected(self):
        r = self._plans({"plans": []})
        self.assertEqual(r.status_code, 400)

    def test_not_a_list_rejected(self):
        r = self._plans({"plans": "annual"})
        self.assertEqual(r.status_code, 400)

    def test_missing_name_rejected(self):
        bad = [{"installment_count": 1, "first_due_on": "2026-08-01", "cadence_days": 0, "total_amount": "1000"}]
        r = self._plans({"plans": bad})
        self.assertEqual(r.status_code, 400)

    def test_installment_count_zero_rejected(self):
        bad = [{"name": "Bad Plan", "installment_count": 0, "first_due_on": "2026-08-01", "cadence_days": 30, "total_amount": "1000"}]
        r = self._plans({"plans": bad})
        self.assertEqual(r.status_code, 400)

    def test_invalid_date_rejected(self):
        bad = [{"name": "Bad", "installment_count": 1, "first_due_on": "not-a-date", "cadence_days": 0, "total_amount": "1000"}]
        r = self._plans({"plans": bad})
        self.assertEqual(r.status_code, 400)

    def test_negative_amount_rejected(self):
        bad = [{"name": "Bad", "installment_count": 1, "first_due_on": "2026-08-01", "cadence_days": 0, "total_amount": "-100"}]
        r = self._plans({"plans": bad})
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# TestSaveFees
# ---------------------------------------------------------------------------

class TestSaveFees(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL", "billing_mode": "simple"},
            format="json",
            **_headers(self.school.id),
        )

    def _fees(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/fees/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_save_fees_success(self):
        r = self._fees({"fees": VALID_FEES})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "fees_saved")
        self.assertEqual(r.data["fees_count"], 2)

    def test_empty_fees_allowed(self):
        # Schools with no separate fees (all-inclusive tuition) is valid
        r = self._fees({"fees": []})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["fees_count"], 0)

    def test_invalid_fee_type_rejected(self):
        bad = [{"name": "Mystery Fee", "fee_type": "UNKNOWN", "amount": "50.00", "is_recurring": False}]
        r = self._fees({"fees": bad})
        self.assertEqual(r.status_code, 400)

    def test_missing_fee_name_rejected(self):
        bad = [{"fee_type": "TECH", "amount": "50.00", "is_recurring": False}]
        r = self._fees({"fees": bad})
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
        sid = self.session_id
        h = _headers(self.school.id)
        self.client.post(f"{BASE_URL}{sid}/configure/", {"term": "2026-FALL", "billing_mode": "simple"}, format="json", **h)
        self.client.post(f"{BASE_URL}{sid}/plans/", {"plans": VALID_PLANS}, format="json", **h)
        self.client.post(f"{BASE_URL}{sid}/fees/", {"fees": VALID_FEES}, format="json", **h)

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
        self.assertIn("result", r.data)
        self.assertEqual(len(r.data["result"]["plans"]), 2)

    def test_commit_creates_installment_plans_in_db(self):
        self._commit()
        count = InstallmentPlan.objects.filter(school_id=self.school.id, term="2026-FALL").count()
        self.assertEqual(count, 2)

    def test_commit_idempotent(self):
        self._commit()
        r2 = self._commit()
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], "committed")
        # Should not create duplicates
        count = InstallmentPlan.objects.filter(school_id=self.school.id, term="2026-FALL").count()
        self.assertEqual(count, 2)

    def test_commit_requires_confirm_true(self):
        r = self._commit({"confirm": False})
        self.assertEqual(r.status_code, 400)

    def test_commit_without_plans_rejected(self):
        # New session, configured but no plans
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        sid2 = r.data["session_id"]
        h = _headers(self.school.id)
        self.client.post(f"{BASE_URL}{sid2}/configure/", {"term": "2026-SP", "billing_mode": "simple"}, format="json", **h)
        r2 = self.client.post(f"{BASE_URL}{sid2}/commit/", {"confirm": True}, format="json", **h)
        self.assertEqual(r2.status_code, 400)

    def test_commit_from_draft_rejected(self):
        # A fresh session in draft state has no plans and no configure
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
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]
        sid = self.session_id
        h = _headers(self.school.id)
        self.client.post(f"{BASE_URL}{sid}/configure/", {"term": "2026-FALL", "billing_mode": "advanced"}, format="json", **h)
        self.client.post(f"{BASE_URL}{sid}/plans/", {"plans": VALID_PLANS}, format="json", **h)
        self.client.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **h)

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
        # New session still in draft → 409
        r_new = self.client.post(BASE_URL, **_headers(self.school.id))
        sid2 = r_new.data["session_id"]
        r2 = self.client.get(
            f"{BASE_URL}{sid2}/verify/",
            **_headers(self.school.id),
        )
        self.assertEqual(r2.status_code, 409)
