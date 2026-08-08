"""Fail-closed authorization proof for high-risk internally prefixed routes."""

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import uuid

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from analytics.api_health import export_school
from onboarding.api_onboarding import mark_task_complete
from support.api_support import resolve_ticket, run_escalation
from support.models import SupportTicket


class HighRiskPrefixedRouteAuthorizationTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.school_id = uuid.UUID("00000000-0000-0000-0000-000000000061")
        self.school = SimpleNamespace(id=self.school_id)
        self.ordinary_user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        self.staff_user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )

    def authenticated(self, request, user=None):
        force_authenticate(request, user=user or self.ordinary_user)
        request.school = self.school
        return request

    def test_onboarding_completion_denies_before_task_lookup_without_admin_authority(self):
        request = self.authenticated(self.factory.post("/onboarding/tasks/7/complete/", {}))

        with (
            patch(
                "onboarding.api_onboarding.get_request_school_id",
                return_value=self.school_id,
            ),
            patch(
                "onboarding.api_onboarding.user_has_permission",
                return_value=False,
            ),
            patch("onboarding.api_onboarding.OnboardingTask.objects.get") as task_get,
        ):
            response = mark_task_complete(
                request,
                school_id=str(self.school_id),
                task_id=7,
            )

        self.assertEqual(response.status_code, 403)
        task_get.assert_not_called()

    def test_onboarding_completion_allows_tenant_admin_and_mutates_only_scoped_task(self):
        request = self.authenticated(self.factory.post("/onboarding/tasks/7/complete/", {}))
        task = MagicMock(id=7)

        with (
            patch(
                "onboarding.api_onboarding.get_request_school_id",
                return_value=self.school_id,
            ),
            patch(
                "onboarding.api_onboarding.user_has_permission",
                return_value=True,
            ) as permission_check,
            patch(
                "onboarding.api_onboarding.OnboardingTask.objects.get",
                return_value=task,
            ) as task_get,
        ):
            response = mark_task_complete(
                request,
                school_id=str(self.school_id),
                task_id=7,
            )

        self.assertEqual(response.status_code, 200)
        permission_check.assert_called_once_with(
            self.ordinary_user,
            "admin.view",
            school=self.school,
        )
        task_get.assert_called_once_with(pk=7, school_id=str(self.school_id))
        task.save.assert_called_once_with(update_fields=["status", "completed_at"])

    def test_ticket_resolution_denies_before_ticket_lookup_without_admin_authority(self):
        request = self.authenticated(self.factory.post("/support/tickets/19/resolve/", {}))

        with (
            patch("support.api_support.get_request_school_id", return_value=self.school_id),
            patch("support.api_support.user_has_permission", return_value=False),
            patch("support.api_support.SupportTicket.objects.get") as ticket_get,
        ):
            response = resolve_ticket(request, ticket_id=19)

        self.assertEqual(response.status_code, 403)
        ticket_get.assert_not_called()

    def test_ticket_resolution_allows_tenant_admin_and_keeps_tenant_filter(self):
        request = self.authenticated(self.factory.post("/support/tickets/19/resolve/", {}))
        ticket = MagicMock(id=19)

        with (
            patch("support.api_support.get_request_school_id", return_value=self.school_id),
            patch("support.api_support.user_has_permission", return_value=True),
            patch(
                "support.api_support.SupportTicket.objects.get",
                return_value=ticket,
            ) as ticket_get,
        ):
            response = resolve_ticket(request, ticket_id=19)

        self.assertEqual(response.status_code, 200)
        ticket_get.assert_called_once_with(pk=19, school_id=self.school_id)
        self.assertEqual(ticket.status, SupportTicket.STATUS_CLOSED)
        ticket.save.assert_called_once_with(update_fields=["status", "resolved_at"])

    def test_global_escalation_denies_tenant_user_before_cross_tenant_service(self):
        request = self.authenticated(self.factory.post("/support/escalation/run/", {}))

        with patch("support.api_support.escalate_overdue_tickets") as escalate:
            response = run_escalation(request)

        self.assertEqual(response.status_code, 403)
        escalate.assert_not_called()

    def test_global_escalation_allows_platform_staff(self):
        request = self.authenticated(
            self.factory.post("/support/escalation/run/", {}),
            user=self.staff_user,
        )

        with (
            patch("support.api_support.get_request_school_id", return_value=self.school_id),
            patch(
                "support.api_support.escalate_overdue_tickets",
                return_value={"escalated": [3]},
            ) as escalate,
        ):
            response = run_escalation(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"escalated": [3]})
        escalate.assert_called_once_with(school_id=self.school_id)

    def test_school_export_denies_before_export_service_without_admin_authority(self):
        request = self.authenticated(self.factory.post("/analytics/export/", {}))

        with (
            patch("analytics.api_health.get_request_school_id", return_value=self.school_id),
            patch("analytics.api_health.user_has_permission", return_value=False),
            patch("analytics.api_health.export_school_data") as export_data,
        ):
            response = export_school(request)

        self.assertEqual(response.status_code, 403)
        export_data.assert_not_called()

    def test_school_export_allows_tenant_admin_and_exports_only_caller_school(self):
        request = self.authenticated(self.factory.post("/analytics/export/", {}))

        with (
            patch("analytics.api_health.get_request_school_id", return_value=self.school_id),
            patch("analytics.api_health.user_has_permission", return_value=True),
            patch(
                "analytics.api_health.export_school_data",
                return_value=BytesIO(b"zip-proof"),
            ) as export_data,
        ):
            response = export_school(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"zip-proof")
        export_data.assert_called_once_with(self.school_id)
