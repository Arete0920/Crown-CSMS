"""Synthetic school/requester boundaries and mandatory support audit evidence."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from core.models import CrownPermission, RolePermission, School, UserRole
from support.models import SupportTicket, SupportTicketEvent
from support.services import create_ticket, resolve_ticket_for_school


@override_settings(TENANT_HEADER_REQUIRED=True, CROWN_DEMO_MODE=False)
class SupportTicketWorkflowTests(TestCase):
    """Exercise existing mounted endpoints rather than mock tenant resolution."""

    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name="Synthetic Heritage")
        cls.other = School.objects.create(name="Synthetic Second School")
        User = get_user_model()
        cls.requester = User.objects.create_user(
            username="support-requester",
            email="support-requester@example.invalid",
            school=cls.school,
        )
        cls.peer = User.objects.create_user(
            username="support-peer",
            email="support-peer@example.invalid",
            school=cls.school,
        )
        cls.staff = User.objects.create_user(
            username="support-staff",
            email="support-staff@example.invalid",
            school=cls.school,
            is_staff=True,
        )
        cls.manager = User.objects.create_user(
            username="support-manager",
            email="support-manager@example.invalid",
            school=cls.school,
        )
        cls.viewer = User.objects.create_user(
            username="support-viewer",
            email="support-viewer@example.invalid",
            school=cls.school,
        )
        cls.school_superuser = User.objects.create_user(
            username="support-school-root",
            email="support-school-root@example.invalid",
            school=cls.school,
            is_superuser=True,
        )
        cls.operator = User.objects.create_superuser(
            username="support-platform",
            email="support-platform@example.invalid",
        )
        cls.foreign = User.objects.create_user(
            username="support-foreign",
            email="support-foreign@example.invalid",
            school=cls.other,
        )
        for role, user, code in (
            ("HEAD_OF_SCHOOL", cls.manager, "support.manage"),
            ("REGISTRAR", cls.viewer, "support.view"),
        ):
            permission = CrownPermission.objects.create(code=code, description=code)
            RolePermission.objects.create(role_code=role, permission=permission)
            UserRole.objects.create(user=user, school=cls.school, role_code=role)

    def client_for(self, user=None, school=None, *, bearer=False):
        """Select an explicit school; bearer cases test the real authenticator."""
        client = APIClient()
        if user:
            if bearer:
                client.credentials(
                    HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}"
                )
            else:
                client.force_authenticate(user=user)
        client.defaults["HTTP_X_SCHOOL_ID"] = str((school or self.school).pk)
        return client

    def ticket(self, requester=None, school=None, **changes):
        """Create clearly synthetic fixtures, including legacy unowned records."""
        return SupportTicket.objects.create(
            school_id=(school or self.school).pk,
            requester=requester,
            title="Synthetic operational question",
            description="No real records or credentials.",
            priority="medium",
            **changes,
        )

    def test_anonymous_denied_on_both_existing_mounts(self):
        for path in ("/api/v1/support/tickets/", "/api/v1/v1/support/tickets/"):
            with self.subTest(path=path):
                self.assertIn(self.client_for().get(path).status_code, (401, 403))

    def test_real_bearer_intake_is_attributed_and_rejects_foreign_scope(self):
        client = self.client_for(self.requester, bearer=True)
        response = client.post(
            "/api/v1/support/tickets/",
            {
                "title": "Import guidance",
                "description": "Synthetic import question",
                "priority": "medium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        ticket = SupportTicket.objects.get(pk=response.data["id"])
        self.assertEqual(ticket.requester_id, self.requester.pk)
        self.assertEqual(ticket.school_id, self.school.pk)
        event = ticket.events.get()
        self.assertEqual((event.actor_id, event.action), (self.requester.pk, "created"))
        denied = self.client_for(self.requester, self.other, bearer=True).get(
            "/api/v1/support/tickets/",
        )
        self.assertEqual(denied.status_code, 404)

    def test_requester_sees_only_own_tickets_including_closed_filter(self):
        own = self.ticket(self.requester)
        closed = self.ticket(self.requester, status="closed")
        self.ticket(self.peer)
        self.ticket()  # Do not guess the requester of a historical ticket.
        self.ticket(self.foreign, self.other)
        client = self.client_for(self.requester)
        response = client.get("/api/v1/support/tickets/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual([row["id"] for row in response.data["tickets"]], [own.pk])
        response = client.get("/api/v1/support/tickets/?status=closed")
        self.assertEqual([row["id"] for row in response.data["tickets"]], [closed.pk])

    def test_explicit_viewer_queue_is_scoped_and_paginates(self):
        for _ in range(5):
            self.ticket(self.peer)
        self.ticket()
        self.ticket(self.foreign, self.other)
        client = self.client_for(self.viewer)
        first = client.get("/api/v1/support/tickets/?per_page=3&page=1")
        second = client.get("/api/v1/support/tickets/?per_page=3&page=2")
        self.assertEqual(first.status_code, 200, first.content)
        self.assertEqual(first.data["total"], 6)
        first_ids = {row["id"] for row in first.data["tickets"]}
        second_ids = {row["id"] for row in second.data["tickets"]}
        self.assertEqual(len(first_ids | second_ids), 6)
        self.assertFalse(first_ids & second_ids)
        self.assertNotIn("description", first.data["tickets"][0])

    def test_staff_and_school_superuser_are_not_support_managers(self):
        ticket = self.ticket(self.peer)
        for user in (self.requester, self.staff, self.school_superuser, self.viewer):
            client = self.client_for(user)
            with self.subTest(user=user.username):
                self.assertEqual(
                    client.post(
                        f"/api/v1/support/tickets/{ticket.pk}/resolve/",
                        {"resolution_summary": "Not authorized"},
                        format="json",
                    ).status_code,
                    403,
                )
                with patch(
                    "support.api_support.escalate_overdue_tickets"
                ) as escalation:
                    self.assertEqual(
                        client.post(
                            "/api/v1/support/escalation/run/",
                            {},
                            format="json",
                        ).status_code,
                        403,
                    )
                    escalation.assert_not_called()
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "open")
        self.assertEqual(SupportTicketEvent.objects.count(), 0)

    def test_manager_resolution_is_audited_idempotent_and_foreign_concealed(self):
        ticket = self.ticket(self.peer)
        foreign = self.ticket(self.foreign, self.other)
        client = self.client_for(self.manager, bearer=True)
        path = f"/api/v1/support/tickets/{ticket.pk}/resolve/"
        response = client.post(
            path, {"resolution_summary": "Verified synthetic fix"}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        ticket.refresh_from_db()
        original_time = ticket.resolved_at
        self.assertEqual(ticket.resolution_summary, "Verified synthetic fix")
        self.assertEqual(ticket.events.get().actor_id, self.manager.pk)
        self.assertEqual(
            client.post(
                path,
                {
                    "resolution_summary": "Repeated request must not replace evidence",
                },
                format="json",
            ).status_code,
            200,
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.resolved_at, original_time)
        self.assertEqual(ticket.resolution_summary, "Verified synthetic fix")
        self.assertEqual(ticket.events.count(), 1)
        self.assertEqual(
            client.post(
                f"/api/v1/support/tickets/{foreign.pk}/resolve/",
                {"resolution_summary": "Foreign"},
                format="json",
            ).status_code,
            404,
        )

    def test_disabled_user_and_inactive_school_are_denied(self):
        self.requester.is_active = False
        self.requester.save(update_fields=["is_active"])
        response = self.client_for(self.requester).get("/api/v1/support/tickets/")
        self.assertEqual(response.status_code, 403)
        self.school.is_active = False
        self.school.save(update_fields=["is_active"])
        self.assertIn(
            self.client_for(self.manager)
            .get(
                "/api/v1/support/tickets/",
            )
            .status_code,
            (403, 404),
        )

    def test_input_rejects_spoofed_ownership_types_and_unbounded_text(self):
        valid = {"title": "Synthetic", "description": "Question", "priority": "medium"}
        cases = [
            {"school_id": str(self.other.pk)},
            {"requester": str(self.peer.pk)},
            {"status": "closed"},
            {"title": 123},
            {"title": " "},
            {"title": "x" * 201},
            {"description": "x" * 10001},
            {"description": []},
            {"priority": "invalid"},
        ]
        client = self.client_for(self.requester)
        for changes in cases:
            with self.subTest(changes=list(changes)):
                response = client.post(
                    "/api/v1/support/tickets/", valid | changes, format="json"
                )
                self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(SupportTicket.objects.count(), 0)
        self.assertEqual(SupportTicketEvent.objects.count(), 0)

    def test_invalid_list_options_and_resolution_are_rejected(self):
        client = self.client_for(self.manager)
        for query in (
            "page=0",
            "page=bad",
            "per_page=101",
            "status=bad",
            "school_id=other",
        ):
            self.assertEqual(
                client.get(f"/api/v1/support/tickets/?{query}").status_code, 400
            )
        ticket = self.ticket(self.peer)
        for data in ({}, {"resolution_summary": " "}, {"resolution_summary": 12}):
            self.assertEqual(
                client.post(
                    f"/api/v1/support/tickets/{ticket.pk}/resolve/",
                    data,
                    format="json",
                ).status_code,
                400,
            )
        self.assertEqual(ticket.events.count(), 0)

    def test_mandatory_audit_failure_rolls_back_both_mutations(self):
        with patch(
            "support.services.SupportTicketEvent.objects.create",
            side_effect=RuntimeError("synthetic outage"),
        ):
            with self.assertRaises(RuntimeError):
                create_ticket(
                    actor=self.requester,
                    school=self.school,
                    data={
                        "title": "Synthetic",
                        "description": "Question",
                        "priority": "low",
                    },
                )
        self.assertEqual(SupportTicket.objects.count(), 0)
        ticket = self.ticket(self.peer)
        with patch(
            "support.services.SupportTicketEvent.objects.create",
            side_effect=RuntimeError("synthetic outage"),
        ):
            with self.assertRaises(RuntimeError):
                resolve_ticket_for_school(
                    actor=self.manager,
                    school=self.school,
                    ticket_id=ticket.pk,
                    data={"resolution_summary": "Verified"},
                )
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "open")
        self.assertIsNone(ticket.resolved_at)
        self.assertEqual(ticket.resolution_summary, "")

    def test_direct_services_do_not_trust_caller_school_or_staff(self):
        with self.assertRaises(PermissionDenied):
            create_ticket(actor=self.requester, school=self.other, data={})
        with self.assertRaises(PermissionDenied):
            resolve_ticket_for_school(
                actor=self.staff, school=self.school, ticket_id=1, data={}
            )

    def test_permission_seed_preserves_academic_support_separation(self):
        call_command("seed_permissions", verbosity=0)
        self.assertTrue(
            RolePermission.objects.filter(
                role_code="HEAD_OF_SCHOOL",
                permission__code="support.manage",
            ).exists()
        )
        self.assertFalse(
            RolePermission.objects.filter(
                role_code="SUPPORT",
                permission__code__startswith="support.",
            ).exists()
        )


def _require_disposable_postgresql():
    """Never run schema/concurrency proof against a hosted or non-test database."""
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("Real PostgreSQL is required for schema and row-lock proof")
    assert str(connection.settings_dict["NAME"]).startswith("test_")
    assert connection.settings_dict.get("HOST") in ("localhost", "127.0.0.1", "::1")


@pytest.mark.django_db(transaction=True)
def test_support_migration_preserves_unowned_legacy_ticket():
    """Rehearse the additive migration on an isolated synthetic PostgreSQL DB."""
    import uuid
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    _require_disposable_postgresql()
    before = [("support", "0001_initial")]
    after = [("support", "0002_ticket_attribution")]
    executor = MigrationExecutor(connection)
    try:
        executor.migrate(before)
        LegacyTicket = executor.loader.project_state(before).apps.get_model(
            "support", "SupportTicket"
        )
        legacy = LegacyTicket.objects.create(
            school_id=uuid.uuid4(),
            title="Synthetic historical question",
            description="No private records",
            priority="medium",
        )
        legacy_id = legacy.pk
        MigrationExecutor(connection).migrate(after)
        restored = SupportTicket.objects.get(pk=legacy_id)
        assert restored.title == "Synthetic historical question"
        assert restored.requester_id is None
        assert restored.resolution_summary == ""
        assert not restored.events.exists()
    finally:
        MigrationExecutor(connection).migrate(after)


@pytest.mark.django_db(transaction=True)
def test_postgresql_parallel_support_resolution_has_one_audit_event():
    """Concurrent managers resolve once without replacing the first receipt."""
    import uuid
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections, connections

    _require_disposable_postgresql()
    school = School.objects.create(name="Synthetic Concurrent Support")
    actor = get_user_model().objects.create_superuser(
        username=f"support-concurrent-{uuid.uuid4().hex}",
        email=f"{uuid.uuid4().hex}@example.invalid",
    )
    ticket = SupportTicket.objects.create(
        school_id=school.pk,
        title="Synthetic concurrency question",
        description="No private records",
        priority="high",
    )
    barrier = Barrier(2)

    def resolve(index):
        close_old_connections()
        try:
            principal = get_user_model().objects.get(pk=actor.pk)
            tenant = School.objects.get(pk=school.pk)
            barrier.wait(timeout=20)
            result = resolve_ticket_for_school(
                actor=principal,
                school=tenant,
                ticket_id=ticket.pk,
                data={"resolution_summary": f"Verified synthetic outcome {index}"},
            )
            return result.resolved_at, result.resolution_summary
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(resolve, (1, 2)))
    ticket.refresh_from_db()
    assert results[0] == results[1]
    assert results[0] == (ticket.resolved_at, ticket.resolution_summary)
    assert ticket.events.filter(action="resolved", actor=actor).count() == 1
