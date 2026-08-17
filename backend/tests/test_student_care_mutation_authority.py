import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import CrownPermission, Family, RolePermission, School, Student, UserRole
from discipline.models import DisciplineAction, DisciplineIncident


User = get_user_model()
INCIDENTS_URL = "/api/discipline/incidents/"


def _school(tag):
    return School.objects.create(name=f"Student Care Unit 2 {tag}-{uuid.uuid4().hex[:6]}")


def _student(school, tag="student"):
    family = Family.objects.create(school=school, family_name=f"{tag}-{uuid.uuid4().hex[:6]}")
    return Student.objects.create(
        school=school,
        family=family,
        student_number=f"SC-{uuid.uuid4().hex[:8]}",
        first_name="Test",
        last_name="Student",
        dob="2012-01-15",
        status="ACTIVE",
    )


def _user(school, tag):
    suffix = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"sc_{tag}_{suffix}",
        email=f"sc_{tag}_{suffix}@example.com",
        password="Passw0rd!",
        school=school,
    )


def _grant(user, school, *codes, role_code=None):
    role_code = role_code or f"sc_unit2_{uuid.uuid4().hex[:10]}"
    UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)
    for code in codes:
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    return role_code


def _incident(school, student, actor, *, status="open"):
    incident = DisciplineIncident.objects.create(
        school=school,
        student=student,
        reported_by=actor,
        occurred_at=timezone.now(),
        category="disruption",
        severity="minor",
        status=status,
        summary="Student Care mutation test",
    )
    DisciplineAction.objects.create(
        incident=incident,
        actor=actor,
        action_type="created",
        note="Incident created",
    )
    return incident


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _hdr(school):
    return {"HTTP_X_SCHOOL_ID": str(school.id)}


class TestStudentCareCreateAuthority(TestCase):
    def setUp(self):
        self.school = _school("create")
        self.student = _student(self.school)
        self.actor = _user(self.school, "actor")
        self.client = _client(self.actor)
        self.payload = {
            "student": str(self.student.id),
            "occurred_at": "2026-08-16T12:00:00Z",
            "summary": "Create authority proof",
            "category": "disruption",
            "severity": "minor",
        }

    def test_create_requires_persistent_create_permission(self):
        _grant(self.actor, self.school, "student-care.view")

        response = self.client.post(INCIDENTS_URL, self.payload, format="json", **_hdr(self.school))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(DisciplineIncident.objects.filter(school=self.school).count(), 0)

    def test_create_permission_creates_open_incident_and_audit_action(self):
        _grant(self.actor, self.school, "student-care.create", "student-care.view")

        response = self.client.post(INCIDENTS_URL, self.payload, format="json", **_hdr(self.school))

        self.assertEqual(response.status_code, 201, getattr(response, "data", response.content))
        incident = DisciplineIncident.objects.get(school=self.school)
        self.assertEqual(incident.status, "open")
        self.assertEqual(incident.reported_by_id, self.actor.id)
        self.assertEqual(
            DisciplineAction.objects.filter(incident=incident, action_type="created").count(),
            1,
        )

    def test_create_cannot_bypass_lifecycle_with_non_open_initial_status(self):
        _grant(self.actor, self.school, "student-care.create")
        payload = {**self.payload, "status": "closed"}

        response = self.client.post(INCIDENTS_URL, payload, format="json", **_hdr(self.school))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(DisciplineIncident.objects.filter(school=self.school).count(), 0)


class TestStudentCareActionAuthority(TestCase):
    def setUp(self):
        self.school = _school("actions")
        self.student = _student(self.school)
        self.actor = _user(self.school, "actor")
        self.incident = _incident(self.school, self.student, self.actor)
        self.client = _client(self.actor)
        self.actions_url = f"{INCIDENTS_URL}{self.incident.id}/actions/"

    def test_note_requires_edit_permission(self):
        _grant(self.actor, self.school, "student-care.view")
        before = DisciplineAction.objects.filter(incident=self.incident).count()

        response = self.client.post(
            self.actions_url,
            {"action_type": "note", "note": "Not authorized"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(DisciplineAction.objects.filter(incident=self.incident).count(), before)

    def test_edit_permission_allows_note(self):
        _grant(self.actor, self.school, "student-care.edit")

        response = self.client.post(
            self.actions_url,
            {"action_type": "note", "note": "Authorized note"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 200, getattr(response, "data", response.content))
        self.assertTrue(
            DisciplineAction.objects.filter(
                incident=self.incident, action_type="note", note="Authorized note"
            ).exists()
        )

    def test_edit_permission_is_revalidated_after_revocation(self):
        role_code = _grant(self.actor, self.school, "student-care.edit")
        first = self.client.post(
            self.actions_url,
            {"action_type": "note", "note": "Before revocation"},
            format="json",
            **_hdr(self.school),
        )
        self.assertEqual(first.status_code, 200)

        edit_permission = CrownPermission.objects.get(code="student-care.edit")
        RolePermission.objects.filter(role_code=role_code, permission=edit_permission).delete()
        before = DisciplineAction.objects.filter(incident=self.incident).count()

        second = self.client.post(
            self.actions_url,
            {"action_type": "note", "note": "After revocation"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(second.status_code, 403)
        self.assertEqual(DisciplineAction.objects.filter(incident=self.incident).count(), before)

    def test_cross_school_incident_is_concealed(self):
        _grant(self.actor, self.school, "student-care.edit")
        other_school = _school("other")
        other_student = _student(other_school)
        other_actor = _user(other_school, "other")
        other_incident = _incident(other_school, other_student, other_actor)

        response = self.client.post(
            f"{INCIDENTS_URL}{other_incident.id}/actions/",
            {"action_type": "note", "note": "Tenant pivot"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 404)


class TestStudentCareAssigneeIntegrity(TestCase):
    def setUp(self):
        self.school = _school("assignee")
        self.student = _student(self.school)
        self.actor = _user(self.school, "actor")
        _grant(self.actor, self.school, "student-care.edit")
        self.incident = _incident(self.school, self.student, self.actor)
        self.client = _client(self.actor)
        self.actions_url = f"{INCIDENTS_URL}{self.incident.id}/actions/"

    def test_same_school_non_portal_role_can_be_assigned(self):
        assignee = _user(self.school, "assignee")
        _grant(assignee, self.school, role_code="SUPPORT")

        response = self.client.post(
            self.actions_url,
            {"action_type": "assigned", "assigned_to": str(assignee.id)},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 200, getattr(response, "data", response.content))
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.assigned_to_id, assignee.id)

    def test_cross_school_assignee_fails_closed(self):
        other_school = _school("assignee-other")
        assignee = _user(other_school, "other-assignee")
        _grant(assignee, other_school, role_code="SUPPORT")

        response = self.client.post(
            self.actions_url,
            {"action_type": "assigned", "assigned_to": str(assignee.id)},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 404)
        self.incident.refresh_from_db()
        self.assertIsNone(self.incident.assigned_to_id)

    def test_portal_only_parent_role_cannot_be_assigned(self):
        assignee = _user(self.school, "parent")
        _grant(assignee, self.school, role_code="PARENT")

        response = self.client.post(
            self.actions_url,
            {"action_type": "assigned", "assigned_to": str(assignee.id)},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 404)
        self.incident.refresh_from_db()
        self.assertIsNone(self.incident.assigned_to_id)


class TestStudentCareTransitionIntegrity(TestCase):
    def setUp(self):
        self.school = _school("transitions")
        self.student = _student(self.school)
        self.actor = _user(self.school, "actor")
        self.client = _client(self.actor)

    def test_status_changed_requires_target_status(self):
        _grant(self.actor, self.school, "student-care.edit")
        incident = _incident(self.school, self.student, self.actor)
        before = DisciplineAction.objects.filter(incident=incident).count()

        response = self.client.post(
            f"{INCIDENTS_URL}{incident.id}/actions/",
            {"action_type": "status_changed"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(DisciplineAction.objects.filter(incident=incident).count(), before)

    def test_edit_permission_allows_open_to_investigating(self):
        _grant(self.actor, self.school, "student-care.edit")
        incident = _incident(self.school, self.student, self.actor)

        response = self.client.post(
            f"{INCIDENTS_URL}{incident.id}/actions/",
            {"action_type": "status_changed", "status": "investigating"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 200, getattr(response, "data", response.content))
        incident.refresh_from_db()
        self.assertEqual(incident.status, "investigating")

    def test_edit_permission_cannot_bypass_close_permission(self):
        _grant(self.actor, self.school, "student-care.edit")
        incident = _incident(self.school, self.student, self.actor)

        response = self.client.post(
            f"{INCIDENTS_URL}{incident.id}/actions/",
            {"action_type": "status_changed", "status": "closed"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 403)
        incident.refresh_from_db()
        self.assertEqual(incident.status, "open")

    def test_close_action_requires_close_permission(self):
        _grant(self.actor, self.school, "student-care.edit")
        incident = _incident(self.school, self.student, self.actor)

        response = self.client.post(
            f"{INCIDENTS_URL}{incident.id}/actions/",
            {"action_type": "closed"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 403)
        incident.refresh_from_db()
        self.assertEqual(incident.status, "open")

    def test_close_permission_closes_open_incident(self):
        _grant(self.actor, self.school, "student-care.close")
        incident = _incident(self.school, self.student, self.actor)

        response = self.client.post(
            f"{INCIDENTS_URL}{incident.id}/actions/",
            {"action_type": "closed", "note": "Resolved"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 200, getattr(response, "data", response.content))
        incident.refresh_from_db()
        self.assertEqual(incident.status, "closed")
        self.assertTrue(
            DisciplineAction.objects.filter(incident=incident, action_type="closed").exists()
        )

    def test_duplicate_status_transition_is_rejected_without_audit_append(self):
        _grant(self.actor, self.school, "student-care.edit")
        incident = _incident(self.school, self.student, self.actor, status="investigating")
        before = DisciplineAction.objects.filter(incident=incident).count()

        response = self.client.post(
            f"{INCIDENTS_URL}{incident.id}/actions/",
            {"action_type": "status_changed", "status": "investigating"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(DisciplineAction.objects.filter(incident=incident).count(), before)

    def test_closed_incident_cannot_reopen(self):
        _grant(self.actor, self.school, "student-care.edit", "student-care.close")
        incident = _incident(self.school, self.student, self.actor, status="closed")
        before = DisciplineAction.objects.filter(incident=incident).count()

        response = self.client.post(
            f"{INCIDENTS_URL}{incident.id}/actions/",
            {"action_type": "status_changed", "status": "open"},
            format="json",
            **_hdr(self.school),
        )

        self.assertEqual(response.status_code, 400)
        incident.refresh_from_db()
        self.assertEqual(incident.status, "closed")
        self.assertEqual(DisciplineAction.objects.filter(incident=incident).count(), before)
