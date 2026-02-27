import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from comms.models import OutboxMessage
from comms_wizard.models import CommsWizardSession
from core.models import School

User = get_user_model()

BASE_URL = "/api/v1/comms-wizard/sessions/"

VALID_CHANNELS = ["email", "sms"]
VALID_RECIPIENTS = [
    {"to": "parent1@example.com", "name": "Parent One"},
    {"to": "parent2@example.com", "name": "Parent Two"},
]


def _make_school(name="Comms School"):
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
    return c


# ---------------------------------------------------------------------------
# Helpers to advance session through states
# ---------------------------------------------------------------------------

def _advance_to_configured(client, school_id, purpose="Re-enrollment Reminder", channels=None):
    if channels is None:
        channels = ["email"]
    r = client.post(BASE_URL, **_headers(school_id))
    session_id = r.data["session_id"]
    client.post(
        f"{BASE_URL}{session_id}/configure/",
        {"purpose": purpose, "channels": channels},
        format="json",
        **_headers(school_id),
    )
    return session_id


def _advance_to_message_drafted(client, school_id):
    session_id = _advance_to_configured(client, school_id)
    client.post(
        f"{BASE_URL}{session_id}/message/",
        {"subject": "Test Subject", "body": "Test body content."},
        format="json",
        **_headers(school_id),
    )
    return session_id


def _advance_to_recipients_staged(client, school_id):
    session_id = _advance_to_message_drafted(client, school_id)
    client.post(
        f"{BASE_URL}{session_id}/recipients/",
        {"recipients": VALID_RECIPIENTS},
        format="json",
        **_headers(school_id),
    )
    return session_id


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
        r = c.post(f"{BASE_URL}{uuid.uuid4()}/configure/", **_headers(self.school.id))
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
            {"purpose": "Test", "channels": ["email"]},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_message_isolation(self):
        r = self.client_b.post(
            self._url("message/"),
            {"subject": "Hi", "body": "Body"},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_recipients_isolation(self):
        r = self.client_b.post(
            self._url("recipients/"),
            {"recipients": VALID_RECIPIENTS},
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
            CommsWizardSession.objects.filter(id=r.data["session_id"]).exists()
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
        r = self._configure({"purpose": "Enrollment Drive", "channels": ["email"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")

    def test_missing_purpose_rejected(self):
        r = self._configure({"channels": ["email"]})
        self.assertEqual(r.status_code, 400)

    def test_purpose_too_long_rejected(self):
        r = self._configure({"purpose": "X" * 129, "channels": ["email"]})
        self.assertEqual(r.status_code, 400)

    def test_invalid_channel_rejected(self):
        r = self._configure({"purpose": "Drive", "channels": ["fax"]})
        self.assertEqual(r.status_code, 400)

    def test_reconfigure_allowed(self):
        self._configure({"purpose": "First", "channels": ["email"]})
        r = self._configure({"purpose": "Second", "channels": ["email", "sms"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")


# ---------------------------------------------------------------------------
# TestDraftMessage
# ---------------------------------------------------------------------------

class TestDraftMessage(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.session_id = _advance_to_configured(self.client, self.school.id)

    def _message(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/message/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_draft_success(self):
        r = self._message({"subject": "Important Notice", "body": "Please review."})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "message_drafted")

    def test_missing_subject_rejected(self):
        r = self._message({"body": "A body."})
        self.assertEqual(r.status_code, 400)

    def test_missing_body_rejected(self):
        r = self._message({"subject": "A subject."})
        self.assertEqual(r.status_code, 400)

    def test_redraft_allowed(self):
        self._message({"subject": "First", "body": "First body."})
        r = self._message({"subject": "Revised", "body": "Revised body."})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "message_drafted")


# ---------------------------------------------------------------------------
# TestStageRecipients
# ---------------------------------------------------------------------------

class TestStageRecipients(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.session_id = _advance_to_message_drafted(self.client, self.school.id)

    def _recipients(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/recipients/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_stage_success(self):
        r = self._recipients({"recipients": VALID_RECIPIENTS})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "recipients_staged")
        self.assertEqual(r.data["recipients_count"], 2)

    def test_empty_recipients_rejected(self):
        r = self._recipients({"recipients": []})
        self.assertEqual(r.status_code, 400)

    def test_not_a_list_rejected(self):
        r = self._recipients({"recipients": "email@example.com"})
        self.assertEqual(r.status_code, 400)

    def test_missing_to_rejected(self):
        bad = [{"name": "No To Field"}]
        r = self._recipients({"recipients": bad})
        self.assertEqual(r.status_code, 400)

    def test_duplicate_to_rejected(self):
        bad = [
            {"to": "same@example.com", "name": "One"},
            {"to": "same@example.com", "name": "Two"},
        ]
        r = self._recipients({"recipients": bad})
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# TestCommit
# ---------------------------------------------------------------------------

class TestCommit(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.session_id = _advance_to_recipients_staged(self.client, self.school.id)

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

    def test_commit_creates_outbox_messages(self):
        self._commit()
        # 2 recipients × 1 channel (email) = 2 OutboxMessages
        self.assertEqual(
            OutboxMessage.objects.filter(school_id=str(self.school.id)).count(), 2
        )

    def test_commit_idempotent(self):
        self._commit()
        r2 = self._commit()
        self.assertEqual(r2.status_code, 200)
        # No new messages on re-commit
        self.assertEqual(
            OutboxMessage.objects.filter(school_id=str(self.school.id)).count(), 2
        )

    def test_commit_requires_confirm_true(self):
        r = self._commit({"confirm": False})
        self.assertEqual(r.status_code, 400)

    def test_commit_from_draft_rejected(self):
        r_new = self.client.post(BASE_URL, **_headers(self.school.id))
        sid = r_new.data["session_id"]
        r2 = self.client.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r2.status_code, 409)

    def test_commit_result_counts(self):
        r = self._commit()
        self.assertIn("messages_created", r.data)
        self.assertIn("messages_skipped", r.data)
        self.assertEqual(r.data["messages_created"], 2)
        self.assertEqual(r.data["messages_skipped"], 0)

    def test_commit_multi_channel_creates_correct_count(self):
        """With 2 channels × 2 recipients = 4 outbox messages."""
        school2 = _make_school("Multi Channel School")
        c2 = _client_for(school2)
        r = c2.post(BASE_URL, **_headers(school2.id))
        sid = r.data["session_id"]
        h = _headers(school2.id)
        c2.post(f"{BASE_URL}{sid}/configure/", {"purpose": "Drive", "channels": ["email", "sms"]}, format="json", **h)
        c2.post(f"{BASE_URL}{sid}/message/", {"subject": "Hi", "body": "Body"}, format="json", **h)
        c2.post(f"{BASE_URL}{sid}/recipients/", {"recipients": VALID_RECIPIENTS}, format="json", **h)
        r_commit = c2.post(f"{BASE_URL}{sid}/commit/", {"confirm": True}, format="json", **h)
        self.assertEqual(r_commit.status_code, 200)
        self.assertEqual(r_commit.data["messages_created"], 4)  # 2 channels × 2 recipients


# ---------------------------------------------------------------------------
# TestVerify
# ---------------------------------------------------------------------------

class TestVerify(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.session_id = _advance_to_recipients_staged(self.client, self.school.id)
        self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )

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
        self.assertIn("messages_created", r.data)
        self.assertIn("messages_skipped", r.data)
