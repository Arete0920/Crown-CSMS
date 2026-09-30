from unittest.mock import patch

from django.test import TestCase

from comms.models import OutboxMessage
from comms.tasks import drain_outbox
from core.models import School
from core.tenant_models import get_current_school


class OutboxTenantContextTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Task Tenant School")
        self.message = OutboxMessage.objects.create(
            school_id=str(self.school.id),
            channel="EMAIL",
            to="recipient@example.com",
            subject="Subject",
            body="Body",
            idempotency_key="tenant-task-proof",
        )

    @patch("comms.tasks._send")
    def test_delivery_binds_message_school_and_clears_after_success(self, send_mock):
        observed = []

        def capture_context(_message):
            observed.append(get_current_school())

        send_mock.side_effect = capture_context

        result = drain_outbox.run(batch_size=1)

        self.message.refresh_from_db()
        self.assertEqual(result, {"sent": 1, "failed": 0, "dead": 0})
        self.assertEqual(observed, [self.school])
        self.assertEqual(self.message.status, OutboxMessage.STATUS_SENT)
        self.assertIsNone(get_current_school())

    @patch("comms.tasks._send")
    def test_delivery_clears_context_after_channel_failure(self, send_mock):
        def fail_inside_context(_message):
            self.assertEqual(get_current_school(), self.school)
            raise RuntimeError("delivery failed")

        send_mock.side_effect = fail_inside_context

        result = drain_outbox.run(batch_size=1)

        self.message.refresh_from_db()
        self.assertEqual(result, {"sent": 0, "failed": 1, "dead": 0})
        self.assertIn("delivery failed", self.message.last_error)
        self.assertIsNone(get_current_school())

    @patch("comms.tasks._send")
    def test_unknown_school_fails_before_channel_dispatch(self, send_mock):
        self.message.school_id = "00000000-0000-0000-0000-000000000000"
        self.message.save(update_fields=["school_id"])

        result = drain_outbox.run(batch_size=1)

        self.message.refresh_from_db()
        self.assertEqual(result, {"sent": 0, "failed": 1, "dead": 0})
        self.assertIn("unknown or inactive school", self.message.last_error)
        send_mock.assert_not_called()
        self.assertIsNone(get_current_school())


    @patch("comms.sms_service.send_sms_to_number")
    def test_sms_outbox_uses_number_delivery(self, send_sms_mock):
        self.message.channel = "SMS"
        self.message.to = "+15555550123"
        self.message.save(update_fields=["channel", "to"])

        result = drain_outbox.run(batch_size=1)

        self.message.refresh_from_db()
        self.assertEqual(result, {"sent": 1, "failed": 0, "dead": 0})
        self.assertEqual(self.message.status, OutboxMessage.STATUS_SENT)
        send_sms_mock.assert_called_once_with("+15555550123", "Body")

    def test_unsupported_channel_is_dead_after_one_attempt(self):
        self.message.channel = "PUSH"
        self.message.save(update_fields=["channel"])

        result = drain_outbox.run(batch_size=1)

        self.message.refresh_from_db()
        self.assertEqual(result, {"sent": 0, "failed": 0, "dead": 1})
        self.assertEqual(self.message.attempts, 1)
        self.assertEqual(self.message.status, OutboxMessage.STATUS_DEAD)
        self.assertIn("not configured", self.message.last_error)
