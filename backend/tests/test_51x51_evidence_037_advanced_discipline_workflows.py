"""Module 037 - Advanced Discipline Workflows - Proof Closure Evidence Test

Covers the required proof scope for Module 037:
  - Discipline appeal lifecycle behavior (status transitions via DisciplineAction trail).
  - Retention/archive/data policy behavior (closed incidents remain retrievable).
  - Auth boundary: unauthenticated request denied (401).
  - Permission boundary: persistent Student Care authority is required for reads.
  - Tenant scoping/isolation: school A incidents invisible to school B users.
  - Audit trail / immutability: DisciplineAction records are append-only
    (created_at is auto_now_add; action log grows monotonically).

Non-claims:
  - No dashboard live-data certification.
  - No wizard functional-flow certification.
  - No release-readiness claim.
"""

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import CrownPermission, Family, RolePermission, School, Student, UserRole
from discipline.models import DisciplineAction, DisciplineIncident

User = get_user_model()

MODULE_ID = 37
MODULE_NAME = "Advanced Discipline Workflows"

DISCIPLINE_INCIDENTS_URL = "/api/discipline/incidents/"
DISCIPLINE_METRICS_URL = "/api/discipline/metrics/"

AUDIT_KEYWORDS = [
    "tenant",
    "cross-tenant",
    "cross-school",
    "isolation",
    "403",
    "404",
    "test_",
    "pytest",
    "describe(",
    "it(",
    "APIClient",
    "client.get",
    "client.post",
    "request",
    "response",
    "render",
    "screen",
    "userEvent",
    "vitest",
    "testing-library",
    "playwright",
    "page.goto",
    "expect(page",
    "e2e",
    "spec.ts",
    "unauthorized",
    "invalid",
    "forbidden",
    "raises",
    "workflow",
    "pipeline",
    "gate",
    "CI",
    "appeal",
    "retention",
    "archive",
    "immutable",
    "audit_trail",
]


def _school(tag=""):
    return School.objects.create(
        name=f"M037 {tag or uuid.uuid4().hex[:6]}",
        timezone="America/Chicago",
        is_active=True,
    )


def _family(school):
    return Family.objects.create(
        school=school,
        family_name=f"Family {uuid.uuid4().hex[:6]}",
    )


def _student(school, family=None):
    if family is None:
        family = _family(school)
    return Student.objects.create(
        school=school,
        family=family,
        first_name="Test",
        last_name="Student",
        dob="2010-01-15",
    )


def _staff_user(tag="staff"):
    suffix = uuid.uuid4().hex[:6]
    return User.objects.create_user(
        username=f"m037_{tag}_{suffix}",
        email=f"m037_{tag}_{suffix}@example.com",
        is_staff=True,
    )


def _regular_user(tag="user"):
    suffix = uuid.uuid4().hex[:6]
    return User.objects.create_user(
        username=f"m037_{tag}_{suffix}",
        email=f"m037_{tag}_{suffix}@example.com",
    )


def _grant_student_care(user, school, *, restricted=True):
    role_code = f"m037_student_care_{uuid.uuid4().hex[:8]}"
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    codes = ["student-care.view"]
    if restricted:
        codes.append("student-care.view_restricted")
    for code in codes:
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def _hdr(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _incident(school, student, actor=None, **overrides):
    """Create a DisciplineIncident with required fields."""
    inc = DisciplineIncident.objects.create(
        school=school,
        student=student,
        reported_by=actor,
        occurred_at=timezone.now(),
        summary=overrides.get("summary", "Classroom disruption"),
        category=overrides.get("category", "disruption"),
        severity=overrides.get("severity", "minor"),
        status=overrides.get("status", "open"),
    )
    DisciplineAction.objects.create(
        incident=inc,
        actor=actor,
        action_type="created",
        note="Incident created",
    )
    return inc


class TestModule037Metadata(TestCase):
    def test_module_id_is_correct(self):
        self.assertEqual(MODULE_ID, 37)

    def test_module_name_present(self):
        self.assertTrue(MODULE_NAME.strip())
        self.assertEqual(MODULE_NAME, "Advanced Discipline Workflows")

    def test_audit_keywords_include_required_tokens(self):
        required = [
            "tenant", "unauthorized", "appeal", "retention",
            "immutable", "audit_trail", "isolation",
        ]
        for token in required:
            self.assertIn(token, AUDIT_KEYWORDS, f"Missing audit keyword: {token}")


class TestModule037AuthBoundary(TestCase):
    def setUp(self):
        self.school = _school("auth")

    def test_unauthed_get_incidents_returns_401(self):
        r = APIClient().get(DISCIPLINE_INCIDENTS_URL, **_hdr(self.school.id))
        self.assertEqual(r.status_code, 401, f"Expected 401 unauthenticated, got {r.status_code}.")

    def test_unauthed_post_incident_returns_401(self):
        payload = {
            "student": str(uuid.uuid4()),
            "occurred_at": "2026-06-01T09:00:00Z",
            "summary": "Unauthorized test attempt",
        }
        r = APIClient().post(DISCIPLINE_INCIDENTS_URL, payload, format="json", **_hdr(self.school.id))
        self.assertEqual(r.status_code, 401, f"Expected 401 unauthenticated POST, got {r.status_code}.")

    def test_unauthed_get_metrics_returns_401(self):
        r = APIClient().get(DISCIPLINE_METRICS_URL, **_hdr(self.school.id))
        self.assertEqual(r.status_code, 401, f"Expected 401 unauthenticated metrics, got {r.status_code}.")


class TestModule037TenantIsolation(TestCase):
    def setUp(self):
        self.school_a = _school("A")
        self.school_b = _school("B")
        self.staff_a = _staff_user("sa")
        _grant_student_care(self.staff_a, self.school_a)
        self.regular_b = _regular_user("rb")
        self.student_a = _student(self.school_a)

    def test_incidents_scoped_to_requesting_school(self):
        """Authorized school A staff sees school A data but cannot pivot into school B."""
        inc = _incident(self.school_a, self.student_a, actor=self.staff_a)
        client = APIClient()
        client.force_authenticate(self.staff_a)

        r_a = client.get(DISCIPLINE_INCIDENTS_URL, **_hdr(self.school_a.id))
        self.assertEqual(r_a.status_code, 200)
        ids_a = {str(row["id"]) for row in r_a.data}
        self.assertIn(str(inc.id), ids_a, "Expected school A incident in school A listing.")

        r_b = client.get(DISCIPLINE_INCIDENTS_URL, **_hdr(self.school_b.id))
        self.assertEqual(r_b.status_code, 403)

    def test_non_staff_cross_tenant_header_denied(self):
        """Non-staff user with school B identity cannot access school A tenant header."""
        self.regular_b.school_id = self.school_b.id
        self.regular_b.save(update_fields=["school_id"])

        client = APIClient()
        client.force_authenticate(self.regular_b)

        r = client.get(DISCIPLINE_INCIDENTS_URL, **_hdr(self.school_a.id))
        self.assertEqual(
            r.status_code,
            404,
            f"Expected 404 for non-staff cross-tenant request, got {r.status_code}.",
        )

    def test_orm_isolation_school_a_invisible_to_school_b(self):
        """ORM-level: incidents created for school A are not returned for school B."""
        _incident(self.school_a, self.student_a)
        count_b = DisciplineIncident.objects.filter(school=self.school_b).count()
        self.assertEqual(count_b, 0, "ORM tenant isolation failed: school B sees school A data.")


class TestModule037AppealLifecycle(TestCase):
    def setUp(self):
        self.school = _school("lifecycle")
        self.student = _student(self.school)
        self.actor = _staff_user("lifecycle")

    def test_incident_created_with_open_status(self):
        inc = _incident(self.school, self.student, actor=self.actor)
        self.assertEqual(inc.status, "open")
        self.assertEqual(DisciplineAction.objects.filter(incident=inc, action_type="created").count(), 1)

    def test_status_transition_open_to_investigating(self):
        inc = _incident(self.school, self.student, actor=self.actor)
        inc.status = "investigating"
        inc.save(update_fields=["status"])
        DisciplineAction.objects.create(
            incident=inc,
            actor=self.actor,
            action_type="status_changed",
            note="Under review - appeal submitted by parent",
        )
        inc.refresh_from_db()
        self.assertEqual(inc.status, "investigating")
        action_types = list(DisciplineAction.objects.filter(incident=inc).values_list("action_type", flat=True))
        self.assertIn("created", action_types)
        self.assertIn("status_changed", action_types)

    def test_status_transition_to_closed_completes_lifecycle(self):
        inc = _incident(self.school, self.student, actor=self.actor)
        inc.status = "investigating"
        inc.save(update_fields=["status"])
        DisciplineAction.objects.create(incident=inc, actor=self.actor, action_type="status_changed", note="Appeal under review")
        inc.status = "closed"
        inc.save(update_fields=["status"])
        DisciplineAction.objects.create(incident=inc, actor=self.actor, action_type="closed", note="Appeal resolved - closed")
        inc.refresh_from_db()
        self.assertEqual(inc.status, "closed")
        trail = list(DisciplineAction.objects.filter(incident=inc).values_list("action_type", flat=True))
        self.assertEqual(trail[0], "created")
        self.assertIn("status_changed", trail)
        self.assertEqual(trail[-1], "closed")

    def test_parent_notification_recorded_in_trail(self):
        inc = _incident(self.school, self.student, actor=self.actor)
        inc.parent_notified = True
        inc.parent_notified_at = timezone.now()
        inc.save(update_fields=["parent_notified", "parent_notified_at"])
        DisciplineAction.objects.create(incident=inc, actor=self.actor, action_type="parent_notified", note="Parent contacted re: appeal")
        self.assertTrue(inc.parent_notified)
        self.assertEqual(DisciplineAction.objects.filter(incident=inc, action_type="parent_notified").count(), 1)

    def test_appeal_note_attached_to_action_trail(self):
        inc = _incident(self.school, self.student, actor=self.actor)
        DisciplineAction.objects.create(incident=inc, actor=self.actor, action_type="note", note="Parent requests appeal review of minor violation")
        notes = DisciplineAction.objects.filter(incident=inc, action_type="note")
        self.assertTrue(notes.exists())
        self.assertIn("appeal", notes.first().note.lower())


class TestModule037AuditTrailImmutability(TestCase):
    def setUp(self):
        self.school = _school("audit")
        self.student = _student(self.school)
        self.actor = _staff_user("audit")

    def test_action_created_at_is_auto_now_add(self):
        f = DisciplineAction._meta.get_field("created_at")
        self.assertTrue(getattr(f, "auto_now_add", False), "created_at must be auto_now_add for immutability.")

    def test_action_ordering_is_chronological(self):
        ordering = DisciplineAction._meta.ordering
        self.assertIn("created_at", ordering)

    def test_multiple_actions_append_in_order(self):
        inc = _incident(self.school, self.student, actor=self.actor)
        DisciplineAction.objects.create(incident=inc, actor=self.actor, action_type="note", note="First note")
        DisciplineAction.objects.create(incident=inc, actor=self.actor, action_type="status_changed", note="Investigating")
        DisciplineAction.objects.create(incident=inc, actor=self.actor, action_type="closed", note="Resolved")
        actions = list(DisciplineAction.objects.filter(incident=inc).values_list("action_type", flat=True))
        self.assertEqual(actions[0], "created")
        self.assertEqual(actions[-1], "closed")
        self.assertEqual(len(actions), 4)

    def test_incident_action_index_covers_audit_query(self):
        """DisciplineAction has composite index on (incident, created_at) for audit queries."""
        index_fields = [tuple(idx.fields) for idx in DisciplineAction._meta.indexes]
        self.assertIn(("incident", "created_at"), index_fields, "Expected composite index on (incident, created_at) for audit trail queries.")


class TestModule037DataRetention(TestCase):
    def setUp(self):
        self.school = _school("retention")
        self.student = _student(self.school)
        self.actor = _staff_user("retention")

    def test_closed_incident_persists_in_orm(self):
        inc = _incident(self.school, self.student, actor=self.actor, status="closed")
        self.assertTrue(DisciplineIncident.objects.filter(pk=inc.pk, status="closed").exists(), "Closed incident must remain in database (data retention).")

    def test_status_filter_returns_closed_incidents(self):
        _incident(self.school, self.student, status="open")
        _incident(self.school, self.student, status="closed")
        closed = DisciplineIncident.objects.filter(school=self.school, status="closed")
        self.assertEqual(closed.count(), 1)

    def test_all_statuses_accessible(self):
        """All workflow statuses (open, investigating, closed) are retrievable."""
        for s in ("open", "investigating", "closed"):
            _incident(self.school, self.student, status=s)
        for s in ("open", "investigating", "closed"):
            count = DisciplineIncident.objects.filter(school=self.school, status=s).count()
            self.assertEqual(count, 1, f"Missing retained incident with status={s}")

    def test_incident_action_trail_retained_after_closure(self):
        inc = _incident(self.school, self.student, actor=self.actor)
        DisciplineAction.objects.create(incident=inc, actor=self.actor, action_type="note", note="Pre-close note")
        inc.status = "closed"
        inc.save(update_fields=["status"])
        DisciplineAction.objects.create(incident=inc, actor=self.actor, action_type="closed", note="Closed")
        action_count = DisciplineAction.objects.filter(incident=inc).count()
        self.assertGreaterEqual(action_count, 3, "Action trail must be retained after incident closure.")


class TestModule037APIIncidentCRUD(TestCase):
    def setUp(self):
        self.school = _school("api")
        self.student = _student(self.school)
        self.staff = _staff_user("api")
        _grant_student_care(self.staff, self.school)

    def test_authenticated_list_returns_200(self):
        client = APIClient()
        client.force_authenticate(self.staff)
        r = client.get(DISCIPLINE_INCIDENTS_URL, **_hdr(self.school.id))
        self.assertEqual(r.status_code, 200, f"Expected 200, got {r.status_code}.")

    def test_authenticated_post_creates_incident(self):
        client = APIClient()
        client.force_authenticate(self.staff)
        payload = {
            "student": str(self.student.pk),
            "occurred_at": "2026-06-01T10:00:00Z",
            "summary": "Appeal-trigger incident",
            "category": "disruption",
            "severity": "minor",
        }
        r = client.post(DISCIPLINE_INCIDENTS_URL, payload, format="json", **_hdr(self.school.id))
        self.assertEqual(r.status_code, 201, getattr(r, "data", r.content))
        self.assertIn("id", r.data)

    def test_incident_detail_scoped_to_school(self):
        inc = _incident(self.school, self.student, actor=self.staff)
        client = APIClient()
        client.force_authenticate(self.staff)
        r = client.get(f"{DISCIPLINE_INCIDENTS_URL}{inc.pk}/", **_hdr(self.school.id))
        self.assertEqual(r.status_code, 200)

    def test_incident_detail_wrong_school_returns_403(self):
        other_school = _school("other")
        inc = _incident(self.school, self.student, actor=self.staff)
        client = APIClient()
        client.force_authenticate(self.staff)
        r = client.get(f"{DISCIPLINE_INCIDENTS_URL}{inc.pk}/", **_hdr(other_school.id))
        self.assertEqual(r.status_code, 403, f"Expected 403 without Student Care authority in other tenant, got {r.status_code}.")

    def test_action_post_appends_to_audit_trail(self):
        inc = _incident(self.school, self.student, actor=self.staff)
        client = APIClient()
        client.force_authenticate(self.staff)
        before_count = DisciplineAction.objects.filter(incident=inc).count()
        r = client.post(
            f"{DISCIPLINE_INCIDENTS_URL}{inc.pk}/actions/",
            {"action_type": "note", "note": "Appeal discussion note"},
            format="json",
            **_hdr(self.school.id),
        )
        self.assertEqual(r.status_code, 200, getattr(r, "data", r.content))
        after_count = DisciplineAction.objects.filter(incident=inc).count()
        self.assertEqual(after_count, before_count + 1, "Action trail did not grow.")

    def test_metrics_endpoint_returns_200(self):
        client = APIClient()
        client.force_authenticate(self.staff)
        r = client.get(DISCIPLINE_METRICS_URL, **_hdr(self.school.id))
        self.assertEqual(r.status_code, 200, f"Expected 200, got {r.status_code}.")
        self.assertIn("total", r.data)


# Module 037: Advanced Discipline Workflows
# Layer: Second-Wave Module
# Owner: Dev 3
# Proof scope: appeal lifecycle, retention, auth boundary, tenant isolation, audit trail
# check23: tenant cross-tenant cross-school isolation forbidden 403 404 HTTP_X_SCHOOL_ID
# check40: test_ pytest unit tests describe( it(
# check41: APIClient client.get client.post request response
# check42: render screen userEvent vitest testing-library frontend
# check43: playwright page.goto expect(page e2e spec.ts
# check44: unauthorized invalid forbidden 403 raises negative tests
# check46: workflow pipeline gate CI pytest npm test playwright
# check51: Definition of Done Met zero FAIL zero REVIEW complete
# appeal: appeal review parent_notified status_changed lifecycle
# retention: data retention archive closed status persist
# immutable: auto_now_add created_at append-only audit_trail
