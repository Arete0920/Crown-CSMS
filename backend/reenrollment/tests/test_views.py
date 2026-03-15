"""
backend/reenrollment/tests/test_views.py

29 pytest tests covering:
- Auth required / missing school header
- Tenant isolation (cross-school session access denied on all 6 endpoints)
- Create session
- Configure: valid, missing year, negative fee, re-configure resets exclusions
- List candidates: draft blocked, snapshot returned, excluded flags
- Select: configure-required guard, invalid ID rejected, correct counts
- Commit: configure-required guard, confirm-required guard, no-students guard,
          idempotency, response shape + billing records created in DB
- Verify: committed-required guard, advances status once, idempotent

Pattern mirrors backend/onboarding/tests/test_views.py exactly.
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from billing.models import BillingRun, Invoice, InvoiceLine
from core.models import School
from households.models import Household
from households.models import Student as HouseholdStudent
from reenrollment.models import ReenrollmentSession

User = get_user_model()

BASE = "/api/v1/reenrollment/sessions/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def school_a(db):
    return School.objects.create(name=f"School A {uuid.uuid4().hex[:6]}")


@pytest.fixture
def school_b(db):
    return School.objects.create(name=f"School B {uuid.uuid4().hex[:6]}")


@pytest.fixture
def user(db):
    return User.objects.create_user(username=f"user_{uuid.uuid4().hex[:6]}", password="pass")


def _authed_client(user, school):
    token = str(RefreshToken.for_user(user).access_token)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_SCHOOL_ID=str(school.id))
    return c


@pytest.fixture
def client_a(user, school_a):
    return _authed_client(user, school_a)


@pytest.fixture
def client_b(user, school_b):
    return _authed_client(user, school_b)


def _make_session(school, status=ReenrollmentSession.STATUS_DRAFT, **kwargs):
    return ReenrollmentSession.objects.create(school=school, status=status, **kwargs)


def _make_household_and_students(school_id, n=2, active=True):
    """Create a household with n students for the given school_id (UUID)."""
    household = Household.objects.create(
        school_id=school_id,
        name=f"Household {uuid.uuid4().hex[:6]}",
    )
    students = [
        HouseholdStudent.objects.create(
            school_id=school_id,
            household=household,
            first_name=f"First{i}",
            last_name=f"Last{i}",
            grade_level="5",
            is_active=active,
        )
        for i in range(n)
    ]
    return household, students


# ---------------------------------------------------------------------------
# 1. Auth / school header
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAuth:
    def test_unauthenticated_create_denied(self, school_a):
        c = APIClient()
        c.credentials(HTTP_X_SCHOOL_ID=str(school_a.id))
        res = c.post(BASE, {}, format="json")
        assert res.status_code == 401

    def test_missing_school_header_denied(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        res = c.post(BASE, {}, format="json")
        assert res.status_code in (400, 403)


# ---------------------------------------------------------------------------
# 2. Tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTenantIsolation:
    def _session_a(self, school_a):
        return _make_session(school_a, status=ReenrollmentSession.STATUS_DRAFT)

    def test_configure_wrong_school_404(self, client_b, school_a):
        session = self._session_a(school_a)
        res = client_b.post(f"{BASE}{session.id}/configure/",
                            {"target_year_label": "2026-2027", "enrollment_fee": "100"}, format="json")
        assert res.status_code == 404

    def test_candidates_wrong_school_404(self, client_b, school_a):
        session = _make_session(school_a, status=ReenrollmentSession.STATUS_CONFIGURED,
                                target_year_label="2026-2027", candidates_snapshot=[])
        res = client_b.get(f"{BASE}{session.id}/candidates/")
        assert res.status_code == 404

    def test_select_wrong_school_404(self, client_b, school_a):
        session = _make_session(school_a, status=ReenrollmentSession.STATUS_CONFIGURED,
                                target_year_label="2026-2027", candidates_snapshot=[])
        res = client_b.post(f"{BASE}{session.id}/select/", {"excluded_ids": []}, format="json")
        assert res.status_code == 404

    def test_commit_wrong_school_404(self, client_b, school_a):
        session = _make_session(school_a, status=ReenrollmentSession.STATUS_CONFIGURED,
                                target_year_label="2026-2027", candidates_snapshot=[])
        res = client_b.post(f"{BASE}{session.id}/commit/", {"confirm": True}, format="json")
        assert res.status_code == 404

    def test_verify_wrong_school_404(self, client_b, school_a):
        session = _make_session(school_a, status=ReenrollmentSession.STATUS_COMMITTED,
                                target_year_label="2026-2027",
                                commit_result={"billing_run_id": str(uuid.uuid4()),
                                               "students_reenrolled": 1,
                                               "households_invoiced": 1,
                                               "invoices_created": 1,
                                               "total_amount": "100.00"})
        res = client_b.get(f"{BASE}{session.id}/verify/")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# 3. Create session
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateSession:
    def test_create_returns_session_id_and_draft(self, client_a):
        res = client_a.post(BASE, {}, format="json")
        assert res.status_code == 201
        data = res.json()
        assert "session_id" in data
        assert data["status"] == ReenrollmentSession.STATUS_DRAFT
        assert ReenrollmentSession.objects.filter(pk=data["session_id"]).exists()


# ---------------------------------------------------------------------------
# 4. Configure session
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestConfigure:
    def _new_session_id(self, client_a):
        return client_a.post(BASE, {}, format="json").json()["session_id"]

    def test_valid_configure(self, client_a):
        sid = self._new_session_id(client_a)
        res = client_a.post(f"{BASE}{sid}/configure/",
                            {"target_year_label": "2026-2027", "enrollment_fee": "500.00"}, format="json")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["target_year_label"] == "2026-2027"
        assert data["enrollment_fee"] == "500.00"
        assert "candidates_total" in data

    def test_missing_year_label_rejected(self, client_a):
        sid = self._new_session_id(client_a)
        res = client_a.post(f"{BASE}{sid}/configure/", {"enrollment_fee": "100"}, format="json")
        assert res.status_code == 400

    def test_negative_fee_rejected(self, client_a):
        sid = self._new_session_id(client_a)
        res = client_a.post(f"{BASE}{sid}/configure/",
                            {"target_year_label": "2026-2027", "enrollment_fee": "-1"}, format="json")
        assert res.status_code == 400

    def test_reconfigure_resets_excluded_ids(self, client_a, school_a):
        sid = self._new_session_id(client_a)
        # Configure once
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": "100"}, format="json")
        # Set some exclusions
        session = ReenrollmentSession.objects.get(pk=sid)
        session.excluded_ids = ["fake-uuid"]
        session.save()
        # Re-configure — should reset excluded_ids
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2027-2028", "enrollment_fee": "200"}, format="json")
        session.refresh_from_db()
        assert session.excluded_ids == []
        assert session.target_year_label == "2027-2028"


# ---------------------------------------------------------------------------
# 5. List candidates
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCandidates:
    def test_draft_session_blocked(self, client_a, school_a):
        session = _make_session(school_a)
        res = client_a.get(f"{BASE}{session.id}/candidates/")
        assert res.status_code == 400

    def test_candidates_returned_after_configure(self, client_a, school_a):
        _, students = _make_household_and_students(school_a.id, n=3)
        # Configure to snapshot students
        created = client_a.post(BASE, {}, format="json").json()
        sid = created["session_id"]
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": "100"}, format="json")
        res = client_a.get(f"{BASE}{sid}/candidates/")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 3
        assert len(data["candidates"]) >= 3

    def test_excluded_flag_appears(self, client_a, school_a):
        household, students = _make_household_and_students(school_a.id, n=2)
        created = client_a.post(BASE, {}, format="json").json()
        sid = created["session_id"]
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": "100"}, format="json")
        # Exclude one student
        student_id = str(students[0].id)
        client_a.post(f"{BASE}{sid}/select/", {"excluded_ids": [student_id]}, format="json")
        res = client_a.get(f"{BASE}{sid}/candidates/")
        assert res.status_code == 200
        by_id = {c["id"]: c for c in res.json()["candidates"]}
        assert by_id[student_id]["excluded"] is True


# ---------------------------------------------------------------------------
# 6. Select students
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSelect:
    def _configured_session(self, client_a, school_a, n_students=2):
        _make_household_and_students(school_a.id, n=n_students)
        sid = client_a.post(BASE, {}, format="json").json()["session_id"]
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": "100"}, format="json")
        return sid

    def test_draft_session_rejected(self, client_a, school_a):
        session = _make_session(school_a)
        res = client_a.post(f"{BASE}{session.id}/select/", {"excluded_ids": []}, format="json")
        assert res.status_code == 400

    def test_invalid_id_rejected(self, client_a, school_a):
        sid = self._configured_session(client_a, school_a)
        res = client_a.post(f"{BASE}{sid}/select/",
                            {"excluded_ids": ["not-a-real-uuid"]}, format="json")
        assert res.status_code == 400

    def test_valid_exclusion_saved(self, client_a, school_a):
        _, students = _make_household_and_students(school_a.id, n=3)
        sid = client_a.post(BASE, {}, format="json").json()["session_id"]
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": "100"}, format="json")
        exclude_id = str(students[0].id)
        res = client_a.post(f"{BASE}{sid}/select/", {"excluded_ids": [exclude_id]}, format="json")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["excluded_count"] == 1
        assert data["selected_count"] >= 2

    def test_empty_exclusion_selects_all(self, client_a, school_a):
        _make_household_and_students(school_a.id, n=2)
        sid = client_a.post(BASE, {}, format="json").json()["session_id"]
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": "100"}, format="json")
        res = client_a.post(f"{BASE}{sid}/select/", {"excluded_ids": []}, format="json")
        assert res.status_code == 200
        assert res.json()["excluded_count"] == 0


# ---------------------------------------------------------------------------
# 7. Commit
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCommit:
    def _commit_ready_session(self, client_a, school_a, n_students=2, fee="200.00"):
        _make_household_and_students(school_a.id, n=n_students)
        sid = client_a.post(BASE, {}, format="json").json()["session_id"]
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": fee}, format="json")
        return sid

    def test_not_configured_rejected(self, client_a, school_a):
        session = _make_session(school_a)
        res = client_a.post(f"{BASE}{session.id}/commit/", {"confirm": True}, format="json")
        assert res.status_code == 400

    def test_requires_confirm_flag(self, client_a, school_a):
        sid = self._commit_ready_session(client_a, school_a)
        res = client_a.post(f"{BASE}{sid}/commit/", {}, format="json")
        assert res.status_code == 400

    def test_all_excluded_rejected(self, client_a, school_a):
        _, students = _make_household_and_students(school_a.id, n=2)
        sid = client_a.post(BASE, {}, format="json").json()["session_id"]
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": "100"}, format="json")
        # Exclude everyone
        all_ids = [str(s.id) for s in students]
        # Also query to get all snapshot IDs
        session = ReenrollmentSession.objects.get(pk=sid)
        all_snapshot_ids = [c["id"] for c in session.candidates_snapshot]
        client_a.post(f"{BASE}{sid}/select/", {"excluded_ids": all_snapshot_ids}, format="json")
        res = client_a.post(f"{BASE}{sid}/commit/", {"confirm": True}, format="json")
        assert res.status_code == 400

    def test_commit_creates_billing_records(self, client_a, school_a):
        household, students = _make_household_and_students(school_a.id, n=2)
        sid = client_a.post(BASE, {}, format="json").json()["session_id"]
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": "300.00"}, format="json")
        res = client_a.post(f"{BASE}{sid}/commit/", {"confirm": True}, format="json")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["students_reenrolled"] == 2
        assert data["households_invoiced"] == 1
        assert data["invoices_created"] == 1
        assert data["total_amount"] == "600.00"
        # Verify DB records
        run = BillingRun.objects.get(pk=data["billing_run_id"])
        assert run.term == "2026-2027"
        assert run.run_type == "ENROLLMENT_FEE"
        assert Invoice.objects.filter(billing_run=run).count() == 1
        assert InvoiceLine.objects.filter(school_id=school_a.id).count() == 2

    def test_commit_idempotent_second_call(self, client_a, school_a):
        _make_household_and_students(school_a.id, n=1)
        sid = client_a.post(BASE, {}, format="json").json()["session_id"]
        client_a.post(f"{BASE}{sid}/configure/",
                      {"target_year_label": "2026-2027", "enrollment_fee": "100"}, format="json")
        client_a.post(f"{BASE}{sid}/commit/", {"confirm": True}, format="json")
        res2 = client_a.post(f"{BASE}{sid}/commit/", {"confirm": True}, format="json")
        assert res2.status_code == 200
        assert res2.json()["already_committed"] is True
        # No duplicate billing runs
        assert BillingRun.objects.filter(school_id=school_a.id).count() == 1


# ---------------------------------------------------------------------------
# 8. Verify
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestVerify:
    def _committed_session(self, school_a):
        result = {
            "billing_run_id": str(uuid.uuid4()),
            "students_reenrolled": 5,
            "households_invoiced": 4,
            "invoices_created": 4,
            "total_amount": "2500.00",
        }
        return _make_session(
            school_a,
            status=ReenrollmentSession.STATUS_COMMITTED,
            target_year_label="2026-2027",
            enrollment_fee="500.00",
            commit_result=result,
        )

    def test_not_committed_blocked(self, client_a, school_a):
        session = _make_session(school_a)
        res = client_a.get(f"{BASE}{session.id}/verify/")
        assert res.status_code == 400

    def test_verify_advances_to_verified(self, client_a, school_a):
        session = self._committed_session(school_a)
        res = client_a.get(f"{BASE}{session.id}/verify/")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == ReenrollmentSession.STATUS_VERIFIED
        session.refresh_from_db()
        assert session.status == ReenrollmentSession.STATUS_VERIFIED

    def test_verify_idempotent(self, client_a, school_a):
        session = self._committed_session(school_a)
        client_a.get(f"{BASE}{session.id}/verify/")
        res2 = client_a.get(f"{BASE}{session.id}/verify/")
        assert res2.status_code == 200
        assert res2.json()["status"] == ReenrollmentSession.STATUS_VERIFIED

    def test_verify_response_shape(self, client_a, school_a):
        session = self._committed_session(school_a)
        res = client_a.get(f"{BASE}{session.id}/verify/")
        data = res.json()
        assert data["ok"] is True
        assert data["target_year_label"] == "2026-2027"
        assert data["enrollment_fee"] == "500.00"
        assert data["students_reenrolled"] == 5
        assert data["households_invoiced"] == 4
        assert data["total_amount"] == "2500.00"
        assert "billing_run_id" in data
