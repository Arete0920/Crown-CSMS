"""
staff_onboarding_wizard/tests/test_views.py

Tests for the Staff Onboarding Wizard (Wizard #13).

Covers:
  - Auth enforcement (401 when unauthenticated)
  - Tenant isolation (X-School-Id required, mismatch → 404)
  - Full happy path: create → configure → preview → commit → verify
  - Validation errors on configure (missing/invalid fields)
  - State machine guard on commit
  - Duplicate staff email: get_or_create idempotent, commit succeeds with created=False
"""
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, Staff, UserRole
from staff_onboarding_wizard.models import StaffOnboardingWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/staff-onboarding-wizard/sessions/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_school(suffix=""):
    name = f"SOW School {suffix or uuid.uuid4().hex[:6]}"
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _authed_client(school):
    user = _make_user()
    role_code = "staff_onboarding_test_hr_editor"
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    permission, _ = CrownPermission.objects.get_or_create(code="hr.edit")
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _configure_payload(**overrides):
    payload = {
        "first_name": "Alice",
        "last_name":  "Staffperson",
        "email":      f"alice_{uuid.uuid4().hex[:6]}@school.test",
        "role_type":  "TEACHER",
    }
    payload.update(overrides)
    return payload


def _advance_to_configured(client, school_id, **overrides):
    """Create + configure; return (session_id, email)."""
    r = client.post(BASE_URL, **_headers(school_id))
    assert r.status_code == 201, r.data
    sid = r.data["session_id"]
    payload = _configure_payload(**overrides)
    rc = client.post(
        f"{BASE_URL}{sid}/configure/",
        payload,
        format="json",
        **_headers(school_id),
    )
    assert rc.status_code == 200, rc.data
    return sid, payload["email"]


def _advance_to_previewed(client, school_id, **overrides):
    sid, email = _advance_to_configured(client, school_id, **overrides)
    rp = client.get(f"{BASE_URL}{sid}/preview/", **_headers(school_id))
    assert rp.status_code == 200, rp.data
    return sid, email


def _advance_to_committed(client, school_id, **overrides):
    sid, email = _advance_to_previewed(client, school_id, **overrides)
    rc = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school_id))
    assert rc.status_code == 200, rc.data
    return sid, email


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class StaffOnboardingAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)

    def test_configure_requires_auth(self):
        school = _make_school()
        client = _authed_client(school)
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = APIClient().post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(),
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 401)


# ---------------------------------------------------------------------------
# HR mutation authorization
# ---------------------------------------------------------------------------

class StaffOnboardingAuthorizationTest(TestCase):
    def _viewer(self, school):
        user = _make_user()
        role_code = "staff_onboarding_test_read_only"
        UserRole.objects.create(user=user, school=school, role_code=role_code)
        permission, _ = CrownPermission.objects.get_or_create(code="hr.view")
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_unprivileged_user_cannot_start_onboarding(self):
        school = _make_school()
        user = _make_user()
        UserRole.objects.create(user=user, school=school, role_code="staff_onboarding_test_no_grant")
        client = APIClient()
        client.force_authenticate(user=user)
        self.assertEqual(client.post(BASE_URL, **_headers(school.id)).status_code, 403)
        self.assertFalse(StaffOnboardingWizardSession.objects.exists())

    def test_view_only_cannot_mutate_onboarding_including_get_steps(self):
        school = _make_school()
        editor = _authed_client(school)
        sid, _ = _advance_to_configured(editor, school.id)
        viewer = self._viewer(school)
        self.assertEqual(viewer.post(BASE_URL, **_headers(school.id)).status_code, 403)
        self.assertEqual(
            viewer.get(f"{BASE_URL}{sid}/preview/", **_headers(school.id)).status_code,
            403,
        )
        self.assertEqual(
            StaffOnboardingWizardSession.objects.get(pk=sid).status,
            StaffOnboardingWizardSession.STATUS_CONFIGURED,
        )
        self.assertEqual(
            viewer.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id)).status_code,
            403,
        )
        self.assertEqual(
            viewer.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id)).status_code,
            403,
        )

    def test_inactive_editor_is_rejected(self):
        school = _make_school()
        editor = _authed_client(school)
        user = editor.handler._force_user
        user.is_active = False
        user.save(update_fields=["is_active"])
        self.assertEqual(editor.post(BASE_URL, **_headers(school.id)).status_code, 403)


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

class StaffOnboardingTenantTest(TestCase):
    def test_missing_school_header_returns_400(self):
        client = _authed_client(_make_school())
        r = client.post(BASE_URL)
        self.assertIn(r.status_code, (400, 403))

    def test_school_mismatch_returns_404(self):
        school_a = _make_school("A")
        school_b = _make_school("B")
        client = _authed_client(school_a)
        r = client.post(BASE_URL, **_headers(school_a.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(),
            format="json",
            **_headers(school_b.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class StaffOnboardingCreateTest(TestCase):
    def test_create_returns_201(self):
        school = _make_school()
        r = _authed_client(school).post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertIn("session_id", r.data)
        self.assertEqual(r.data["status"], StaffOnboardingWizardSession.STATUS_DRAFT)

    def test_create_persists_session(self):
        school = _make_school()
        r = _authed_client(school).post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        self.assertTrue(
            StaffOnboardingWizardSession.objects.filter(pk=sid).exists()
        )


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class StaffOnboardingConfigureTest(TestCase):
    def test_configure_happy_path(self):
        school = _make_school()
        client = _authed_client(school)
        sid, email = _advance_to_configured(client, school.id)
        session = StaffOnboardingWizardSession.objects.get(pk=sid)
        self.assertEqual(session.status, StaffOnboardingWizardSession.STATUS_CONFIGURED)
        self.assertEqual(session.email, email)

    def test_configure_missing_first_name(self):
        school = _make_school()
        client = _authed_client(school)
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(first_name=""),
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)
        self.assertIn("first_name is required", str(r2.data["errors"]))

    def test_configure_invalid_role(self):
        school = _make_school()
        client = _authed_client(school)
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(
            f"{BASE_URL}{sid}/configure/",
            _configure_payload(role_type="WIZARD_LORD"),
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)
        self.assertIn("role_type must be one of", str(r2.data["errors"]))

    def test_all_valid_roles_accepted(self):
        school = _make_school()
        client = _authed_client(school)
        for role in ("TEACHER", "DIRECTOR", "ADMIN", "SUPPORT"):
            r = client.post(BASE_URL, **_headers(school.id))
            sid = r.data["session_id"]
            r2 = client.post(
                f"{BASE_URL}{sid}/configure/",
                _configure_payload(role_type=role, email=f"{role.lower()}_{uuid.uuid4().hex[:4]}@test.com"),
                format="json",
                **_headers(school.id),
            )
            self.assertEqual(r2.status_code, 200, f"Role {role} failed: {r2.data}")


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

class StaffOnboardingPreviewTest(TestCase):
    def test_preview_on_draft_returns_400(self):
        school = _make_school()
        client = _authed_client(school)
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.get(f"{BASE_URL}{sid}/preview/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_preview_happy_path(self):
        school = _make_school()
        client = _authed_client(school)
        sid, email = _advance_to_configured(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/preview/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], StaffOnboardingWizardSession.STATUS_PREVIEWED)
        self.assertIn("preview", r.data)
        self.assertEqual(r.data["preview"]["email"], email)
        self.assertIsInstance(r.data["warnings"], list)

    def test_preview_warns_on_duplicate_email(self):
        school = _make_school()
        email = f"dupe_{uuid.uuid4().hex[:6]}@school.test"
        Staff.objects.create(
            school=school, first_name="Existing", last_name="Staff",
            email=email, role_type="ADMIN"
        )
        client = _authed_client(school)
        sid, _ = _advance_to_configured(client, school.id, email=email)
        r = client.get(f"{BASE_URL}{sid}/preview/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.data["warnings"]) > 0)


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class StaffOnboardingCommitTest(TestCase):
    def test_commit_creates_staff(self):
        school = _make_school()
        client = _authed_client(school)
        sid, email = _advance_to_committed(client, school.id)
        self.assertTrue(Staff.objects.filter(school=school, email=email).exists())

    def test_commit_returns_staff_id(self):
        school = _make_school()
        client = _authed_client(school)
        sid, email = _advance_to_previewed(client, school.id)
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn("staff_id", r.data["result"])
        self.assertTrue(r.data["result"]["created"])
        self.assertIn("message", r.data["result"])
        self.assertIn("created", r.data["result"]["message"].lower())

    def test_commit_on_draft_returns_400(self):
        school = _make_school()
        client = _authed_client(school)
        r = client.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_commit_duplicate_email_idempotent(self):
        school = _make_school()
        email = f"idempotent_{uuid.uuid4().hex[:6]}@school.test"
        Staff.objects.create(
            school=school, first_name="First", last_name="Staff",
            email=email, role_type="TEACHER"
        )
        client = _authed_client(school)
        sid, _ = _advance_to_previewed(client, school.id, email=email)
        r = client.post(f"{BASE_URL}{sid}/commit/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["result"]["created"])  # existing record found
        self.assertIn("already existed", r.data["result"]["message"])


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class StaffOnboardingVerifyTest(TestCase):
    def test_verify_confirms_staff(self):
        school = _make_school()
        client = _authed_client(school)
        sid, email = _advance_to_committed(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], StaffOnboardingWizardSession.STATUS_VERIFIED)
        self.assertTrue(r.data["staff_exists"])
        self.assertEqual(r.data["email"], email)

    def test_verify_before_commit_returns_400(self):
        school = _make_school()
        client = _authed_client(school)
        sid, _ = _advance_to_previewed(client, school.id)
        r = client.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 400)
