import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from aid.models import AidApplication, AidAuditEvent, AidAward
from core.models import AcademicYear, CrownPermission, Family, RolePermission, School, Student, UserRole
from financial_aid_wizard.models import FinancialAidWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
User = get_user_model()
BASE_URL = "/api/v1/aid-wizard/sessions/"
VALID_BUCKETS = ["need", "merit", "mission"]


def _make_school(name="Aid School"):
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_year(school, name="2026-2027", start_year=2026):
    return AcademicYear.objects.create(
        school=school,
        name=name,
        start_date=date(start_year, 8, 1),
        end_date=date(start_year + 1, 5, 31),
    )


def _make_user(school, username=None, grant_aid=True):
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=username, password=TEST_AUTH_SECRET, school=school)
    if grant_aid:
        UserRole.objects.create(user=user, school=school, role_code="AID_DIRECTOR")
        for code in ("financial_aid.view", "financial_aid.edit"):
            permission, _ = CrownPermission.objects.get_or_create(code=code, defaults={"description": ""})
            RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=permission)
    return user


def _make_family(school, family_name="Doe"):
    return Family.objects.create(school=school, family_name=family_name)


def _make_student(school, family, number="S001"):
    return Student.objects.create(
        school=school,
        family=family,
        student_number=number,
        first_name="Jane",
        last_name=family.family_name,
        dob=date(2012, 3, 15),
    )


def _make_application(school, academic_year, family):
    return AidApplication.objects.create(
        school=school,
        academic_year=academic_year,
        family=family,
        household_size=4,
        income_annual_cents=5_000_000,
        status=AidApplication.STATUS_SUBMITTED,
    )


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for(school):
    user = _make_user(school)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class TestAuth(TestCase):
    def setUp(self):
        self.school = _make_school()

    def test_create_requires_auth(self):
        response = APIClient().post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(response.status_code, 401)

    def test_configure_requires_auth(self):
        response = APIClient().post(
            f"{BASE_URL}{uuid.uuid4()}/configure/",
            **_headers(self.school.id),
        )
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_without_financial_aid_permission_is_denied(self):
        user = _make_user(self.school, grant_aid=False)
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(response.status_code, 403)


class TestTenantIsolation(TestCase):
    def setUp(self):
        self.school_a = _make_school("School A")
        self.school_b = _make_school("School B")
        _make_year(self.school_a)
        _make_year(self.school_b)
        self.client_a = _client_for(self.school_a)
        self.client_b = _client_for(self.school_b)
        response = self.client_a.post(BASE_URL, **_headers(self.school_a.id))
        self.session_id = response.data["session_id"]

    def _url(self, suffix=""):
        return f"{BASE_URL}{self.session_id}/{suffix}"

    def test_other_school_cannot_access_session_steps(self):
        attempts = [
            ("post", "configure/", {"aid_year": "2026-2027"}),
            ("post", "buckets/", {"buckets": VALID_BUCKETS}),
            ("post", "awards/", {"awards": []}),
            ("post", "commit/", {"confirm": True}),
        ]
        for method, suffix, payload in attempts:
            response = getattr(self.client_b, method)(
                self._url(suffix),
                payload,
                format="json",
                **_headers(self.school_b.id),
            )
            self.assertEqual(response.status_code, 404)
        response = self.client_b.get(self._url("verify/"), **_headers(self.school_b.id))
        self.assertEqual(response.status_code, 404)


class TestCreateSession(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)

    def test_create_returns_201_and_persists(self):
        response = self.client.post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "draft")
        self.assertTrue(FinancialAidWizardSession.objects.filter(pk=response.data["session_id"]).exists())


class TestConfigure(TestCase):
    def setUp(self):
        self.school = _make_school()
        _make_year(self.school, "2026-2027", 2026)
        _make_year(self.school, "2027-2028", 2027)
        self.client = _client_for(self.school)
        response = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = response.data["session_id"]

    def _configure(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_configure_accepts_cycle_label_before_canonical_year_resolution(self):
        response = self._configure({"aid_year": "2026-2027"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "configured")

        synthetic = self._configure({"aid_year": "2030-2031-E2E"})
        self.assertEqual(synthetic.status_code, 200)

    def test_configure_rejects_empty_or_too_long_year(self):
        self.assertEqual(self._configure({}).status_code, 400)
        self.assertEqual(self._configure({"aid_year": "X" * 25}).status_code, 400)

    def test_configure_reconfigure_allowed(self):
        self._configure({"aid_year": "2026-2027"})
        response = self._configure({"aid_year": "2027-2028"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "configured")


class WizardConfiguredMixin:
    def setUp(self):
        self.school = _make_school()
        self.year = _make_year(self.school)
        self.family = _make_family(self.school)
        self.student = _make_student(self.school, self.family)
        self.application = _make_application(self.school, self.year, self.family)
        self.client = _client_for(self.school)
        response = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = response.data["session_id"]
        headers = _headers(self.school.id)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"aid_year": self.year.name},
            format="json",
            **headers,
        )

    def _stage_buckets(self, buckets=None):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/buckets/",
            {"buckets": buckets or VALID_BUCKETS},
            format="json",
            **_headers(self.school.id),
        )

    def _valid_award(self, bucket="need", amount="2500.00", student=None, application=None):
        return {
            "application_id": str((application or self.application).id),
            "student_id": str((student or self.student).id),
            "bucket": bucket,
            "amount": amount,
            "rationale": "Need-based award",
        }


class TestSaveBuckets(WizardConfiguredMixin, TestCase):
    def test_save_buckets_success(self):
        response = self._stage_buckets()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "buckets_saved")
        self.assertEqual(response.data["active_buckets"], VALID_BUCKETS)

    def test_bucket_validation(self):
        self.assertEqual(self._stage_buckets([]).status_code, 200)
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/buckets/",
            {"buckets": []},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            f"{BASE_URL}{self.session_id}/buckets/",
            {"buckets": ["need", "fake_bucket"]},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(response.status_code, 400)


class TestStageAwards(WizardConfiguredMixin, TestCase):
    def setUp(self):
        super().setUp()
        self._stage_buckets()

    def _awards(self, payload):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/awards/",
            payload,
            format="json",
            **_headers(self.school.id),
        )

    def test_stage_awards_requires_explicit_application_and_student(self):
        response = self._awards({"awards": [self._valid_award("need"), self._valid_award("merit")]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "awards_staged")
        self.assertEqual(response.data["awards_count"], 2)

        missing_student = self._valid_award()
        missing_student.pop("student_id")
        self.assertEqual(self._awards({"awards": [missing_student]}).status_code, 400)

        missing_app = self._valid_award()
        missing_app.pop("application_id")
        self.assertEqual(self._awards({"awards": [missing_app]}).status_code, 400)

    def test_stage_rejects_non_uuid_student_identifiers(self):
        for invalid in (1, "1", "not-a-uuid", "", None):
            award = self._valid_award()
            award["student_id"] = invalid
            with self.subTest(student_id=invalid):
                self.assertEqual(self._awards({"awards": [award]}).status_code, 400)

    def test_stage_rejects_nonfinite_award_amounts(self):
        for invalid in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(amount=invalid):
                self.assertEqual(self._awards({"awards": [self._valid_award("need", invalid)]}).status_code, 400)

    def test_stage_rejects_amounts_outside_canonical_cents_range(self):
        for invalid in ("21474836.48", "1E1000"):
            with self.subTest(amount=invalid):
                response = self._awards({"awards": [self._valid_award("need", invalid)]})
                self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self._awards({"awards": [self._valid_award("need", "21474836.47")]}).status_code,
            200,
        )

    def test_stage_validation(self):
        self.assertEqual(self._awards({"awards": []}).status_code, 200)
        self.assertEqual(self._awards({"awards": "single"}).status_code, 400)

        invalid_bucket = self._valid_award("hardship")
        self.assertEqual(self._awards({"awards": [invalid_bucket]}).status_code, 400)

        negative = self._valid_award("need", "-500")
        self.assertEqual(self._awards({"awards": [negative]}).status_code, 400)


class TestCommit(WizardConfiguredMixin, TestCase):
    def setUp(self):
        super().setUp()
        self._stage_buckets()
        self.client.post(
            f"{BASE_URL}{self.session_id}/awards/",
            {
                "awards": [
                    self._valid_award("need", "2000.00"),
                    self._valid_award("merit", "500.00"),
                ]
            },
            format="json",
            **_headers(self.school.id),
        )

    def _commit(self, payload=None):
        return self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            payload if payload is not None else {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )

    def test_commit_creates_canonical_offered_awards_and_audit_events(self):
        response = self._commit()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "committed")
        self.assertEqual(response.data["awards_created"], 2)

        awards = AidAward.objects.filter(
            school=self.school,
            aid_application=self.application,
            student=self.student,
        )
        self.assertEqual(awards.count(), 2)
        self.assertTrue(all(a.decision_status == AidAward.DECISION_OFFERED for a in awards))
        self.assertEqual(
            set(awards.values_list("award_type", flat=True)),
            {AidAward.TYPE_NEED, AidAward.TYPE_MERIT},
        )
        self.assertEqual(
            AidAuditEvent.objects.filter(
                school=self.school,
                entity_type=AidAuditEvent.ENTITY_AWARD,
                action="AWARD_STAGED",
            ).count(),
            2,
        )

    def test_commit_is_idempotent_at_session_boundary(self):
        self._commit()
        response = self._commit()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "committed")
        self.assertEqual(
            AidAward.objects.filter(
                school=self.school,
                aid_application=self.application,
                student=self.student,
            ).count(),
            2,
        )

    def test_commit_rejects_student_from_another_family(self):
        other_family = _make_family(self.school, "Smith")
        other_student = _make_student(self.school, other_family, "S999")

        response = self.client.post(BASE_URL, **_headers(self.school.id))
        session_id = response.data["session_id"]
        headers = _headers(self.school.id)
        self.client.post(
            f"{BASE_URL}{session_id}/configure/",
            {"aid_year": self.year.name},
            format="json",
            **headers,
        )
        self.client.post(
            f"{BASE_URL}{session_id}/buckets/",
            {"buckets": ["need"]},
            format="json",
            **headers,
        )
        self.client.post(
            f"{BASE_URL}{session_id}/awards/",
            {"awards": [self._valid_award(student=other_student)]},
            format="json",
            **headers,
        )
        commit = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **headers,
        )
        self.assertEqual(commit.status_code, 400)
        self.assertEqual(commit.data["error"], "Award validation failed")
        self.assertEqual(len(commit.data["errors"]), 1)
        self.assertFalse(AidAward.objects.filter(student=other_student).exists())
        session = FinancialAidWizardSession.objects.get(pk=session_id)
        self.assertEqual(session.status, FinancialAidWizardSession.STATUS_AWARDS_STAGED)

    def test_commit_requires_confirmation(self):
        self.assertEqual(self._commit({"confirm": False}).status_code, 400)

    def test_zero_award_cycle_can_commit_without_resolving_academic_year(self):
        response = self.client.post(BASE_URL, **_headers(self.school.id))
        session_id = response.data["session_id"]
        headers = _headers(self.school.id)
        self.client.post(
            f"{BASE_URL}{session_id}/configure/",
            {"aid_year": "2026-2027-E2E"},
            format="json",
            **headers,
        )
        self.client.post(
            f"{BASE_URL}{session_id}/buckets/",
            {"buckets": ["need"]},
            format="json",
            **headers,
        )
        self.client.post(
            f"{BASE_URL}{session_id}/awards/",
            {"awards": []},
            format="json",
            **headers,
        )
        commit = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **headers,
        )
        self.assertEqual(commit.status_code, 200)
        self.assertEqual(commit.data["awards_created"], 0)
        self.assertEqual(commit.data["errors"], [])

    def test_commit_from_draft_rejected(self):
        response = self.client.post(BASE_URL, **_headers(self.school.id))
        draft_id = response.data["session_id"]
        blocked = self.client.post(
            f"{BASE_URL}{draft_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(blocked.status_code, 409)


class TestVerify(WizardConfiguredMixin, TestCase):
    def setUp(self):
        super().setUp()
        self._stage_buckets(["need"])
        headers = _headers(self.school.id)
        self.client.post(
            f"{BASE_URL}{self.session_id}/awards/",
            {"awards": [self._valid_award("need", "1000.00")]},
            format="json",
            **headers,
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **headers,
        )

    def _verify(self):
        return self.client.get(
            f"{BASE_URL}{self.session_id}/verify/",
            **_headers(self.school.id),
        )

    def test_verify_transitions_and_is_idempotent(self):
        first = self._verify()
        second = self._verify()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["status"], "verified")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["status"], "verified")
        self.assertIn("awards_created", second.data)

    def test_verify_requires_committed_status(self):
        response = self.client.post(BASE_URL, **_headers(self.school.id))
        draft_id = response.data["session_id"]
        blocked = self.client.get(
            f"{BASE_URL}{draft_id}/verify/",
            **_headers(self.school.id),
        )
        self.assertEqual(blocked.status_code, 409)
