"""
Wizard Contract Test — Crown2026
=================================
Verifies every wizard session endpoint:
  1. Exists and is registered in urls.py (implicit: 401, not 404)
  2. Requires authentication (401 when no credentials)
  3. Requires X-School-Id header (400 when missing)
  4. Enforces tenant isolation (404 when school mismatch)

Add a new entry to WIZARD_ENDPOINTS whenever a new wizard is shipped.
This is the "seatbelt" that catches URL drift, missing wiring,
and broken auth/tenant behavior in a single place.
"""
import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserRole
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------------------
# Wizard registry — url prefix + description
# ---------------------------------------------------------------------------
WIZARD_ENDPOINTS = [
    # (description, base_url)
    ("reenrollment",    "/api/v1/reenrollment/sessions/"),
    ("billing",         "/api/v1/billing-wizard/sessions/"),
    ("financial_aid",   "/api/v1/aid-wizard/sessions/"),
    ("scheduling",      "/api/v1/scheduling-wizard/sessions/"),
    ("comms",           "/api/v1/comms-wizard/sessions/"),
    ("section_assign",            "/api/v1/section-assign-wizard/sessions/"),
    ("bell_schedule",             "/api/v1/bell-schedule-wizard/sessions/"),
    ("gradebook_setup",           "/api/v1/gradebook-setup-wizard/sessions/"),
    ("attendance_rules",          "/api/v1/attendance-rules-wizard/sessions/"),
    ("enrollment_conversion",     "/api/v1/enrollment-conversion-wizard/sessions/"),
    ("invoice_run",               "/api/v1/invoice-run-wizard/sessions/"),
    ("staff_onboarding",          "/api/v1/staff-onboarding-wizard/sessions/"),
    ("fee_schedule",               "/api/v1/fee-schedule-wizard/sessions/"),
    ("academic_year",              "/api/v1/academic-year-wizard/sessions/"),
    ("enrollment_period",           "/api/v1/enrollment-period-wizard/sessions/"),
    ("grade_scale",                  "/api/v1/grade-scale-wizard/sessions/"),
    ("term_structure",               "/api/v1/term-structure-wizard/sessions/"),
    # Add new wizards here ↓
    ("section_scheduler",            "/api/v1/section-scheduler-wizard/sessions/"),
    ("staff_setup",                  "/api/v1/staff-setup-wizard/sessions/"),
    ("course_catalog",               "/api/v1/course-catalog-wizard/sessions/"),
    ("room_setup",                   "/api/v1/room-setup-wizard/sessions/"),
    ("promotion",                    "/api/v1/promotion-wizard/sessions/"),
]


def _make_school(name=None):
    name = name or f"Contract School {uuid.uuid4().hex[:6]}"
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_authed_client(school):
    user = User.objects.create_user(
        username=f"contract_{uuid.uuid4().hex[:8]}", password="pw"
    )
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _make_authed_client_with_user(school):
    user = User.objects.create_user(
        username=f"contract_{uuid.uuid4().hex[:8]}", password="pw"
    )
    c = APIClient()
    c.force_authenticate(user=user)
    return c, user


def _grant_enrollment_conversion_access(user, school, role_code="REGISTRAR"):
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    perm, _ = CrownPermission.objects.get_or_create(
        code="admissions.edit",
        defaults={"description": "Edit admissions records"},
    )
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


def _grant_wizard_access_if_required(description, user, school):
    if description == "enrollment_conversion":
        _grant_enrollment_conversion_access(user, school)


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


# ---------------------------------------------------------------------------
# Contract: unauthenticated access → 401
# ---------------------------------------------------------------------------

class TestWizardRequiresAuth(TestCase):
    """
    Every wizard session endpoint must reject unauthenticated POST.
    The response must be 401, NOT 404 (which would indicate missing URL wiring).
    """

    def setUp(self):
        self.school = _make_school("Auth Test School")

    def _assert_401(self, description, url):
        c = APIClient()  # no credentials
        r = c.post(url, **_headers(self.school.id))
        self.assertEqual(
            r.status_code, 401,
            f"{description} ({url}): expected 401 for unauthed POST, got {r.status_code}. "
            f"If 404, the URL is not wired in crown_api/urls.py."
        )

    def test_all_wizards_require_auth(self):
        for description, url in WIZARD_ENDPOINTS:
            with self.subTest(wizard=description):
                self._assert_401(description, url)


# ---------------------------------------------------------------------------
# Contract: missing X-School-Id → 400
# ---------------------------------------------------------------------------

class TestWizardRequiresSchoolHeader(TestCase):
    """
    Every wizard session endpoint must reject requests missing X-School-Id.
    Auth is present; only the tenant header is missing.
    """

    def setUp(self):
        self.school = _make_school("Header Test School")
        self.client = _make_authed_client(self.school)

    def _assert_400(self, description, url):
        r = self.client.post(url)  # no school header
        self.assertIn(
            r.status_code, (400, 422),
            f"{description} ({url}): expected 400 for missing X-School-Id, got {r.status_code}."
        )

    def test_all_wizards_require_school_header(self):
        for description, url in WIZARD_ENDPOINTS:
            with self.subTest(wizard=description):
                self._assert_400(description, url)


# ---------------------------------------------------------------------------
# Contract: correct auth + school → 201
# ---------------------------------------------------------------------------

class TestWizardCreateSession(TestCase):
    """
    POST to a wizard base URL with valid auth + correct X-School-Id must
    return 201 and a session_id.
    """

    def setUp(self):
        self.school = _make_school("Create Session School")
        self.client, self.user = _make_authed_client_with_user(self.school)

    def _assert_201(self, description, url):
        _grant_wizard_access_if_required(description, self.user, self.school)
        r = self.client.post(url, **_headers(self.school.id))
        self.assertEqual(
            r.status_code, 201,
            f"{description} ({url}): expected 201, got {r.status_code}. Body: {r.data}"
        )
        self.assertIn(
            "session_id", r.data,
            f"{description} ({url}): response missing 'session_id' key."
        )

    def test_all_wizards_create_session(self):
        for description, url in WIZARD_ENDPOINTS:
            with self.subTest(wizard=description):
                self._assert_201(description, url)


# ---------------------------------------------------------------------------
# Contract: cross-tenant access → 404
# ---------------------------------------------------------------------------

class TestWizardTenantIsolation(TestCase):
    """
    A session created by School A must be invisible to School B.
    GET/POST on the session URL with School B's header must return 404.
    """

    def setUp(self):
        self.school_a = _make_school("Tenant A")
        self.school_b = _make_school("Tenant B")
        self.client_a, self.user_a = _make_authed_client_with_user(self.school_a)
        self.client_b, self.user_b = _make_authed_client_with_user(self.school_b)

    def _assert_tenant_isolation(self, description, url):
        _grant_wizard_access_if_required(description, self.user_a, self.school_a)
        _grant_wizard_access_if_required(description, self.user_b, self.school_b)

        # Create session under school_a
        r = self.client_a.post(url, **_headers(self.school_a.id))
        self.assertEqual(r.status_code, 201, f"{description}: session creation failed {r.status_code}")
        session_id = r.data["session_id"]

        # School B tries to access school A's session
        detail_url = f"{url}{session_id}/configure/"
        r2 = self.client_b.post(detail_url, {}, format="json", **_headers(self.school_b.id))
        self.assertEqual(
            r2.status_code, 404,
            f"{description} ({detail_url}): expected 404 for cross-tenant access, "
            f"got {r2.status_code}. Tenant isolation is BROKEN."
        )

    def test_all_wizards_isolate_tenants(self):
        for description, url in WIZARD_ENDPOINTS:
            with self.subTest(wizard=description):
                self._assert_tenant_isolation(description, url)
