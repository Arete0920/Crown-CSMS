"""Behavioral evidence for Notifications Framework module 5.

These tests exercise the real communications outbox persistence contract, not
module-description keywords or unrelated API health checks. They establish
idempotent enqueue, school-separated message identities, and rollback of queued
work when the enclosing business transaction fails.

Provider delivery, request authorization, and cross-school API isolation require
their own integration evidence; these tests do not claim to certify them.
"""

from django.db import transaction
from django.test import TestCase

from comms.models import OutboxMessage
from comms.outbox_service import enqueue_email, enqueue_sms
from core.models import School


MODULE_ID = 5
MODULE_NAME = "Notifications Framework"


class NotificationsOutboxIntegrityTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name="Notification Evidence School A")
        self.school_b = School.objects.create(name="Notification Evidence School B")
        self.recipient = "fictional.parent@example.test"

    def _email(self, school, *, body="Synthetic enrollment update"):
        return enqueue_email(
            school_id=str(school.pk),
            to=self.recipient,
            subject="Enrollment update",
            body=body,
        )

    def test_repeated_email_enqueue_creates_only_one_persisted_delivery(self):
        first = self._email(self.school_a)
        repeated = self._email(self.school_a)

        self.assertEqual(first.pk, repeated.pk)
        self.assertEqual(OutboxMessage.objects.count(), 1)

        persisted = OutboxMessage.objects.get(pk=first.pk)
        self.assertEqual(persisted.school_id, str(self.school_a.pk))
        self.assertEqual(persisted.channel, "EMAIL")
        self.assertEqual(persisted.to, self.recipient)
        self.assertEqual(persisted.status, OutboxMessage.STATUS_PENDING)
        self.assertEqual(persisted.attempts, 0)

    def test_identical_emails_at_different_schools_have_distinct_outbox_ids(self):
        school_a_message = self._email(self.school_a)
        school_b_message = self._email(self.school_b)

        self.assertNotEqual(school_a_message.pk, school_b_message.pk)
        self.assertNotEqual(
            school_a_message.idempotency_key,
            school_b_message.idempotency_key,
        )
        self.assertEqual(
            OutboxMessage.objects.filter(school_id=str(self.school_a.pk)).count(),
            1,
        )
        self.assertEqual(
            OutboxMessage.objects.filter(school_id=str(self.school_b.pk)).count(),
            1,
        )

    def test_changed_message_content_produces_new_delivery_identity(self):
        first = self._email(self.school_a, body="First synthetic notice")
        changed = self._email(self.school_a, body="Corrected synthetic notice")

        self.assertNotEqual(first.pk, changed.pk)
        self.assertEqual(OutboxMessage.objects.count(), 2)

    def test_failed_business_transaction_does_not_leave_queued_email(self):
        with self.assertRaisesRegex(RuntimeError, "rollback example"):
            with transaction.atomic():
                self._email(self.school_a)
                raise RuntimeError("rollback example")

        self.assertFalse(OutboxMessage.objects.exists())

    def test_repeated_sms_enqueue_is_durable_and_idempotent(self):
        kwargs = {
            "school_id": str(self.school_a.pk),
            "to": "+15555550123",
            "body": "Synthetic attendance reminder",
        }
        first = enqueue_sms(**kwargs)
        repeated = enqueue_sms(**kwargs)

        self.assertEqual(first.pk, repeated.pk)
        self.assertEqual(OutboxMessage.objects.count(), 1)
        persisted = OutboxMessage.objects.get(pk=first.pk)
        self.assertEqual(persisted.channel, "SMS")
        self.assertEqual(persisted.school_id, str(self.school_a.pk))
        self.assertEqual(persisted.status, OutboxMessage.STATUS_PENDING)
