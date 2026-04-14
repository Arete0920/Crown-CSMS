from __future__ import annotations
import uuid
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import School
from outreach.models import (
    Badge,
    Opportunity,
    PartnerOrganization,
    ReflectionPrompt,
    ServiceGoal,
    ServiceLog,
    STATUS_APPROVED,
    STATUS_DRAFT,
    STATUS_NEEDS_INFO,
    STATUS_SUBMITTED,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


def _mk_school(name="Crown Academy"):
    return School.objects.create(name=name)


def _mk_staff(school, username=None):
    return User.objects.create_user(
        username=username or f"staff-{uuid.uuid4()}", password="x", is_staff=True
    )


def _mk_user(school, username=None):
    return User.objects.create_user(
        username=username or f"user-{uuid.uuid4()}", password="x"
    )


def _staff_client(user, school):
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id), HTTP_X_ROLE="staff")
    return c


def _student_client(user, school):
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id), HTTP_X_ROLE="student")
    return c


def _partner(school, name="Test Partner"):
    return PartnerOrganization.objects.create(school_id=school.id, name=name)


def _opp(school, partner, title="Sort food"):
    return Opportunity.objects.create(school_id=school.id, partner=partner, title=title)


def _log(school, status=STATUS_DRAFT, **kw):
    kw.setdefault("participant_type", "STUDENT")
    kw.setdefault("hours", Decimal("2.0"))
    kw["status"] = status
    return ServiceLog.objects.create(school_id=school.id, **kw)


# ---------------------------------------------------------------------------
# Tenant Isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    def test_invalid_school_id_400(self):
        user = _mk_staff(_mk_school())
        c = APIClient()
        c.force_authenticate(user=user)
        c.credentials(HTTP_X_SCHOOL_ID="not-a-uuid", HTTP_X_ROLE="staff")
        r = c.get("/api/outreach/partners/")
        assert r.status_code == 400

    def test_cross_tenant_partner_hidden(self):
        sa = _mk_school("A"); sb = _mk_school("B")
        PartnerOrganization.objects.create(school_id=sb.id, name="B Partner")
        PartnerOrganization.objects.create(school_id=sa.id, name="A Partner")
        c = _staff_client(_mk_staff(sa), sa)
        r = c.get("/api/outreach/partners/")
        assert r.status_code == 200
        names = [x["name"] for x in r.json()]
        assert "A Partner" in names
        assert "B Partner" not in names

    def test_unauthenticated_rejected(self):
        school = _mk_school()
        c = APIClient()
        c.credentials(HTTP_X_SCHOOL_ID=str(school.id), HTTP_X_ROLE="staff")
        r = c.get("/api/outreach/partners/")
        assert r.status_code in (401, 403)

    def test_student_cannot_create_partner(self):
        school = _mk_school()
        c = _student_client(_mk_user(school), school)
        r = c.post("/api/outreach/partners/", {"name": "Forbidden Partner"}, format="json")
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# PartnerOrganization CRUD
# ---------------------------------------------------------------------------

class TestPartnerOrganization:
    def setup_method(self):
        self.school = _mk_school()
        self.client = _staff_client(_mk_staff(self.school), self.school)

    def test_create(self):
        r = self.client.post(
            "/api/outreach/partners/",
            {"name": "Food Pantry", "category": "food", "approved": True},
            format="json",
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Food Pantry"

    def test_list(self):
        _partner(self.school, "P1"); _partner(self.school, "P2")
        r = self.client.get("/api/outreach/partners/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_retrieve(self):
        p = _partner(self.school, "Retrieve Me")
        r = self.client.get(f"/api/outreach/partners/{p.id}/")
        assert r.status_code == 200
        assert r.json()["name"] == "Retrieve Me"

    def test_update(self):
        p = _partner(self.school, "Old")
        r = self.client.patch(f"/api/outreach/partners/{p.id}/", {"name": "New"}, format="json")
        assert r.status_code == 200
        assert r.json()["name"] == "New"

    def test_delete(self):
        p = _partner(self.school)
        r = self.client.delete(f"/api/outreach/partners/{p.id}/")
        assert r.status_code == 204
        assert not PartnerOrganization.objects.filter(pk=p.id).exists()


# ---------------------------------------------------------------------------
# Opportunity
# ---------------------------------------------------------------------------

class TestOpportunity:
    def setup_method(self):
        self.school = _mk_school()
        self.client = _staff_client(_mk_staff(self.school), self.school)
        self.partner = _partner(self.school)

    def test_create(self):
        r = self.client.post(
            "/api/outreach/opportunities/",
            {"partner": str(self.partner.id), "title": "Sort Cans"},
            format="json",
        )
        assert r.status_code == 201
        assert r.json()["title"] == "Sort Cans"
        assert r.json()["partner_name"] == self.partner.name

    def test_list(self):
        _opp(self.school, self.partner, "O1"); _opp(self.school, self.partner, "O2")
        r = self.client.get("/api/outreach/opportunities/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_cross_tenant_hidden(self):
        sb = _mk_school("B"); pb = _partner(sb, "B Partner")
        _opp(sb, pb, "B Opp"); _opp(self.school, self.partner, "A Opp")
        r = self.client.get("/api/outreach/opportunities/")
        assert r.status_code == 200
        titles = [x["title"] for x in r.json()]
        assert "A Opp" in titles
        assert "B Opp" not in titles


# ---------------------------------------------------------------------------
# ServiceLog workflow
# ---------------------------------------------------------------------------

class TestServiceLogWorkflow:
    def setup_method(self):
        self.school = _mk_school()
        self.staff = _mk_staff(self.school)
        self.client = _staff_client(self.staff, self.school)
        self.partner = _partner(self.school)
        self.opp = _opp(self.school, self.partner)

    def test_create_draft(self):
        r = self.client.post(
            "/api/outreach/service-logs/",
            {"participant_type": "STUDENT", "opportunity": str(self.opp.id),
             "partner": str(self.partner.id), "service_date": "2026-02-25", "hours": "3.0"},
            format="json",
        )
        assert r.status_code == 201
        assert r.json()["status"] == STATUS_DRAFT

    def test_submit(self):
        log = _log(self.school, partner=self.partner, opportunity=self.opp)
        r = self.client.post(f"/api/outreach/service-logs/{log.id}/submit/")
        assert r.status_code == 200
        log.refresh_from_db()
        assert log.status == STATUS_SUBMITTED
        assert log.submitted_at is not None

    def test_approve(self):
        log = _log(self.school, partner=self.partner, status=STATUS_SUBMITTED)
        r = self.client.post(
            f"/api/outreach/service-logs/{log.id}/approve/",
            {"reviewer_notes": "Approved"}, format="json"
        )
        assert r.status_code == 200
        log.refresh_from_db()
        assert log.status == STATUS_APPROVED
        assert log.reviewer_notes == "Approved"
        assert log.reviewed_at is not None

    def test_reject(self):
        log = _log(self.school, partner=self.partner, status=STATUS_SUBMITTED)
        r = self.client.post(f"/api/outreach/service-logs/{log.id}/reject/", {}, format="json")
        assert r.status_code == 200
        log.refresh_from_db()
        assert log.status == "REJECTED"

    def test_needs_info(self):
        log = _log(self.school, partner=self.partner, status=STATUS_SUBMITTED)
        r = self.client.post(f"/api/outreach/service-logs/{log.id}/needs-info/", {}, format="json")
        assert r.status_code == 200
        log.refresh_from_db()
        assert log.status == STATUS_NEEDS_INFO

    def test_submit_approved_is_400(self):
        log = _log(self.school, partner=self.partner, status=STATUS_APPROVED)
        r = self.client.post(f"/api/outreach/service-logs/{log.id}/submit/")
        assert r.status_code == 400

    def test_approve_draft_is_400(self):
        log = _log(self.school, partner=self.partner)
        r = self.client.post(f"/api/outreach/service-logs/{log.id}/approve/", {}, format="json")
        assert r.status_code == 400

    def test_needs_info_then_resubmit(self):
        log = _log(self.school, partner=self.partner, status=STATUS_SUBMITTED)
        self.client.post(f"/api/outreach/service-logs/{log.id}/needs-info/")
        log.refresh_from_db()
        assert log.status == STATUS_NEEDS_INFO
        r = self.client.post(f"/api/outreach/service-logs/{log.id}/submit/")
        assert r.status_code == 200
        log.refresh_from_db()
        assert log.status == STATUS_SUBMITTED


# ---------------------------------------------------------------------------
# ServiceLog scoping
# ---------------------------------------------------------------------------

class TestServiceLogScoping:
    def setup_method(self):
        self.school = _mk_school()
        self.client = _staff_client(_mk_staff(self.school), self.school)
        self.partner = _partner(self.school)

    def test_student_no_filter_empty(self):
        user = _mk_user(self.school)
        c = _student_client(user, self.school)
        _log(self.school, partner=self.partner)
        r = c.get("/api/outreach/service-logs/")
        assert r.status_code == 200
        assert len(r.json()) == 0

    def test_staff_filter_by_status(self):
        _log(self.school, partner=self.partner, status=STATUS_DRAFT)
        _log(self.school, partner=self.partner, status=STATUS_SUBMITTED)
        _log(self.school, partner=self.partner, status=STATUS_APPROVED)
        r = self.client.get("/api/outreach/service-logs/?status=SUBMITTED")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["status"] == STATUS_SUBMITTED

    def test_cross_tenant_not_visible(self):
        sb = _mk_school("B")
        ServiceLog.objects.create(school_id=sb.id, participant_type="STUDENT", hours=1)
        _log(self.school)
        r = self.client.get("/api/outreach/service-logs/")
        assert r.status_code == 200
        assert len(r.json()) == 1


# ---------------------------------------------------------------------------
# ServiceGoal
# ---------------------------------------------------------------------------

class TestServiceGoal:
    def setup_method(self):
        self.school = _mk_school()
        self.client = _staff_client(_mk_staff(self.school), self.school)

    def test_create(self):
        r = self.client.post(
            "/api/outreach/goals/",
            {"name": "Grade 10", "school_year": "2025-2026", "grade": 10,
             "required_hours": "20.0", "active": True},
            format="json",
        )
        assert r.status_code == 201
        assert Decimal(r.json()["required_hours"]) == Decimal("20.0")

    def test_list(self):
        ServiceGoal.objects.create(school_id=self.school.id, required_hours=20)
        ServiceGoal.objects.create(school_id=self.school.id, required_hours=30)
        r = self.client.get("/api/outreach/goals/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_student_blocked(self):
        user = _mk_user(self.school)
        c = _student_client(user, self.school)
        r = c.post("/api/outreach/goals/", {"name": "Forbidden Goal", "required_hours": "999"}, format="json")
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# ReflectionPrompt
# ---------------------------------------------------------------------------

class TestReflectionPrompt:
    def setup_method(self):
        self.school = _mk_school()
        self.client = _staff_client(_mk_staff(self.school), self.school)

    def test_create(self):
        r = self.client.post(
            "/api/outreach/prompts/",
            {"title": "Faithful Service", "prompt": "How did you serve Christ?", "active": True},
            format="json",
        )
        assert r.status_code == 201
        assert r.json()["title"] == "Faithful Service"

    def test_list(self):
        ReflectionPrompt.objects.create(school_id=self.school.id, title="P1", prompt="Q")
        r = self.client.get("/api/outreach/prompts/")
        assert r.status_code == 200
        assert len(r.json()) >= 1


# ---------------------------------------------------------------------------
# Badge
# ---------------------------------------------------------------------------

class TestBadge:
    def setup_method(self):
        self.school = _mk_school()
        self.client = _staff_client(_mk_staff(self.school), self.school)

    def test_create(self):
        r = self.client.post(
            "/api/outreach/badges/",
            {"name": "10 Hour Hero", "threshold_hours": "10.0", "active": True},
            format="json",
        )
        assert r.status_code == 201
        assert r.json()["name"] == "10 Hour Hero"

    def test_list(self):
        Badge.objects.create(school_id=self.school.id, name="A")
        Badge.objects.create(school_id=self.school.id, name="B")
        r = self.client.get("/api/outreach/badges/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_cross_tenant_hidden(self):
        sb = _mk_school("B")
        Badge.objects.create(school_id=self.school.id, name="Ours")
        Badge.objects.create(school_id=sb.id, name="Theirs")
        r = self.client.get("/api/outreach/badges/")
        assert r.status_code == 200
        names = [x["name"] for x in r.json()]
        assert "Ours" in names
        assert "Theirs" not in names


# ---------------------------------------------------------------------------
# Report: summary
# ---------------------------------------------------------------------------

class TestReportSummary:
    def setup_method(self):
        self.school = _mk_school()
        self.client = _staff_client(_mk_staff(self.school), self.school)
        self.partner = _partner(self.school, "Local Mission")

    def test_approved_hours_only(self):
        _log(self.school, partner=self.partner, status=STATUS_APPROVED, hours=Decimal("5.0"))
        _log(self.school, partner=self.partner, status=STATUS_APPROVED, hours=Decimal("3.0"))
        _log(self.school, partner=self.partner, status=STATUS_DRAFT, hours=Decimal("10.0"))
        r = self.client.get("/api/outreach/service-logs/report/summary/")
        assert r.status_code == 200
        assert Decimal(r.json()["total_hours"]) == Decimal("8.0")

    def test_student_blocked(self):
        school = _mk_school()
        c = _student_client(_mk_user(school), school)
        r = c.get("/api/outreach/service-logs/report/summary/")
        assert r.status_code == 403

    def test_response_shape(self):
        r = self.client.get("/api/outreach/service-logs/report/summary/")
        assert r.status_code == 200
        data = r.json()
        assert "top_partners" in data
        assert "hours_by_grade" in data


# ---------------------------------------------------------------------------
# Report: student-progress
# ---------------------------------------------------------------------------

class TestReportStudentProgress:
    def setup_method(self):
        self.school = _mk_school()
        self.client = _staff_client(_mk_staff(self.school), self.school)

    def test_requires_student_id(self):
        r = self.client.get("/api/outreach/service-logs/report/student-progress/")
        assert r.status_code == 400

    def test_nonexistent_student_returns_zero(self):
        fake = str(uuid.uuid4())
        r = self.client.get(f"/api/outreach/service-logs/report/student-progress/?student_id={fake}")
        assert r.status_code == 200
        data = r.json()
        assert Decimal(data["approved_hours"]) == Decimal("0")
        assert data["goal"] is None

    def test_schoolwide_goal_fallback(self):
        ServiceGoal.objects.create(
            school_id=self.school.id, name="Schoolwide", required_hours=25, active=True, grade=None
        )
        fake = str(uuid.uuid4())
        r = self.client.get(f"/api/outreach/service-logs/report/student-progress/?student_id={fake}")
        assert r.status_code == 200
        data = r.json()
        assert data["goal"] is not None
        assert Decimal(data["required_hours"]) == Decimal("25")

    def test_progress_pct_zero_no_goal(self):
        fake = str(uuid.uuid4())
        r = self.client.get(f"/api/outreach/service-logs/report/student-progress/?student_id={fake}")
        assert r.status_code == 200
        assert abs(r.json()["progress_pct"] - 0.0) < 1e-9


# ---------------------------------------------------------------------------
# Serializer validation
# ---------------------------------------------------------------------------

class TestSerializerValidation:
    def setup_method(self):
        self.school = _mk_school()
        self.client = _staff_client(_mk_staff(self.school), self.school)

    def test_mismatched_partner_rejected(self):
        pa = _partner(self.school, "Partner A")
        pb = _partner(self.school, "Partner B")
        o = _opp(self.school, pa, "A Opp")
        r = self.client.post(
            "/api/outreach/service-logs/",
            {"participant_type": "STUDENT", "opportunity": str(o.id),
             "partner": str(pb.id), "service_date": "2026-02-25", "hours": "2.0"},
            format="json",
        )
        assert r.status_code == 400


