import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication
from core.models import AcademicYear, CrownPermission, Family, RolePermission, School, UserRole
from enrollment_conversion_wizard.models import EnrollmentConversionWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/enrollment-conversion-wizard/sessions/"


def _make_school():
    return School.objects.create(name=f"ECW {uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _make_user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:8]}", password=TEST_AUTH_SECRET)


def _grant_enrollment_conversion_access(user, school, role_code="REGISTRAR"):
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    perm, _ = CrownPermission.objects.get_or_create(
        code="admissions.edit",
        defaults={"description": "Edit admissions records"},
    )
    RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for(school, with_access=True):
    c = APIClient()
    user = _make_user()
    if with_access:
        _grant_enrollment_conversion_access(user, school)
    c.force_authenticate(user=user)
    return c


def _make_academic_year(school, name="2026-2027"):
    ay, _ = AcademicYear.objects.get_or_create(
        school=school,
        name=name,
        defaults={"start_date": date(2026, 9, 1), "end_date": date(2027, 6, 15)},
    )
    return ay


def _make_application(school, ay, status="ACCEPTED"):
    family = Family.objects.create(school=school, family_name=f"Fam {uuid.uuid4().hex[:6]}")
    return AdmissionsApplication.objects.create(
        school=school, academic_year=ay, family=family, status=status
    )


def _advance_to_configured(client, school_id):
    r = client.post(BASE_URL, **_headers(school_id))
    sid = r.data["session_id"]
    client.post(
        f"{BASE_URL}{sid}/configure/",
        {"academic_year_label": "2026-2027", "from_status": "ACCEPTED"},
        format="json",
        **_headers(school_id),
    )
    return sid


def _advance_to_loaded(client, school_id):
    sid = _advance_to_configured(client, school_id)
    client.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school_id))
    return sid


def _advance_to_committed(client, school_id):
    sid = _advance_to_loaded(client, school_id)
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

class EnrollmentConversionAuthTest(TestCase):
    def test_create_requires_auth(self):
        school = _make_school()
        r = APIClient().post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class EnrollmentConversionCreateTest(TestCase):
    def test_create_returns_201(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["status"], EnrollmentConversionWizardSession.STATUS_DRAFT)

    def test_create_forbidden_without_role_permission(self):
        school = _make_school()
        c = _client_for(school, with_access=False)
        r = c.post(BASE_URL, **_headers(school.id))
        self.assertEqual(r.status_code, 403)


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------

class EnrollmentConversionConfigureTest(TestCase):
    def test_configure_ok(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"academic_year_label": "2026-2027", "from_status": "ACCEPTED"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], EnrollmentConversionWizardSession.STATUS_CONFIGURED)

    def test_configure_missing_academic_year_label(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"from_status": "ACCEPTED"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_configure_invalid_from_status(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"academic_year_label": "2026-2027", "from_status": "REJECTED"},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_configure_wrong_school_returns_404(self):
        school = _make_school()
        other = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE_URL}{sid}/configure/",
            {"academic_year_label": "2026-2027", "from_status": "ACCEPTED"},
            format="json",
            **_headers(other.id),
        )
        self.assertEqual(r2.status_code, 404)


# ---------------------------------------------------------------------------
# Load applicants
# ---------------------------------------------------------------------------

class EnrollmentConversionLoadTest(TestCase):
    def test_load_returns_applicant_count(self):
        school = _make_school()
        ay = _make_academic_year(school)
        _make_application(school, ay, status="ACCEPTED")
        _make_application(school, ay, status="ACCEPTED")
        _make_application(school, ay, status="WAITLISTED")  # not included
        c = _client_for(school)
        sid = _advance_to_configured(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], EnrollmentConversionWizardSession.STATUS_APPLICANTS_LOADED)
        self.assertEqual(r.data["applicant_count"], 2)

    def test_load_from_draft_rejected(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)

    def test_load_zero_applicants_ok(self):
        school = _make_school()
        c = _client_for(school)
        sid = _advance_to_configured(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/load/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["applicant_count"], 0)


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class EnrollmentConversionCommitTest(TestCase):
    def test_commit_converts_applications(self):
        school = _make_school()
        ay = _make_academic_year(school)
        _make_application(school, ay, status="ACCEPTED")
        _make_application(school, ay, status="ACCEPTED")
        c = _client_for(school)
        sid = _advance_to_loaded(c, school.id)
        r = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], EnrollmentConversionWizardSession.STATUS_COMMITTED)
        self.assertEqual(r.data["converted"], 2)
        enrolled = AdmissionsApplication.objects.filter(
            school=school, status=AdmissionsApplication.STATUS_ENROLLED
        ).count()
        self.assertEqual(enrolled, 2)

    def test_commit_requires_confirm(self):
        school = _make_school()
        c = _client_for(school)
        sid = _advance_to_loaded(c, school.id)
        r = c.post(f"{BASE_URL}{sid}/commit/", {}, format="json", **_headers(school.id))
        self.assertEqual(r.status_code, 400)

    def test_commit_is_idempotent(self):
        school = _make_school()
        ay = _make_academic_year(school)
        _make_application(school, ay, status="ACCEPTED")
        c = _client_for(school)
        sid = _advance_to_committed(c, school.id)
        r2 = c.post(
            f"{BASE_URL}{sid}/commit/",
            {"confirm": True},
            format="json",
            **_headers(school.id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], EnrollmentConversionWizardSession.STATUS_COMMITTED)


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class EnrollmentConversionVerifyTest(TestCase):
    def test_verify_ok(self):
        school = _make_school()
        ay = _make_academic_year(school)
        _make_application(school, ay, status="ACCEPTED")
        c = _client_for(school)
        sid = _advance_to_committed(c, school.id)
        r = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], EnrollmentConversionWizardSession.STATUS_VERIFIED)
        self.assertIn("enrolled_count", r.data)

    def test_verify_from_draft_rejected(self):
        school = _make_school()
        c = _client_for(school)
        r = c.post(BASE_URL, **_headers(school.id))
        sid = r.data["session_id"]
        r2 = c.get(f"{BASE_URL}{sid}/verify/", **_headers(school.id))
        self.assertEqual(r2.status_code, 400)
