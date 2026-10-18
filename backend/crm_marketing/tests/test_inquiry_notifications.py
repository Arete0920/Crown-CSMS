from datetime import timedelta
from unittest.mock import Mock
import uuid

import pytest
from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient

from applications.models import Application
from comms.models import NotificationPreference, OutboxMessage
from comms.tasks import drain_outbox
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from core.tenant_models import get_current_school, tenant_context
from crm_marketing.inquiry_notifications import (
    InquiryNotificationSuppressed, inquiry_notification_guard, inquiry_notification_status,
    queue_due_inquiry_followup, queue_inquiry_notifications,
)
from crm_marketing.models import CampaignTouchpoint, LeadStage, MarketingLead
from crm_marketing.tasks import process_inquiry_followups
from households.models import Household


pytestmark = pytest.mark.django_db


@pytest.fixture
def inquiry(monkeypatch, settings):
    settings.GRAPH_FROM_USER = "sender@example.com"
    for suffix in ("TENANT_ID", "CLIENT_ID", "CLIENT_SECRET"):
        monkeypatch.setenv(f"GRAPH_{suffix}", "synthetic-test-value")
        monkeypatch.delenv(f"AZURE_{suffix}", raising=False)
    monkeypatch.delenv("COMMS_SMS_ENABLED", raising=False)
    school = School.objects.create(name="Inquiry School")
    owner = UserAccount.objects.create_user(username=f"owner-{uuid.uuid4()}", email="owner@example.com")
    UserRole.objects.create(user=owner, school=school, role_code="inquiry_owner_test")
    permission, _ = CrownPermission.objects.get_or_create(code="admissions.edit")
    RolePermission.objects.get_or_create(role_code="inquiry_owner_test", permission=permission)
    now = timezone.now()
    return MarketingLead.objects.create(
        school=school, parent_name="Prospective Parent", email="family@example.com", phone="+13025550100",
        contact_preference="email", response_consent=True, follow_up_consent=True,
        family_follow_up_enabled=True, assigned_to_user_id=owner.id,
        inquiry_received_at=now, next_follow_up_at=now + timedelta(days=1),
    )


def _due(lead, days=0):
    lead.next_follow_up_at = timezone.now() - timedelta(days=days)
    lead.save(update_fields=["next_follow_up_at"])
    return lead


def _family_message(lead):
    return OutboxMessage.objects.get(school_id=str(lead.school_id), to=lead.email)


def test_capture_queues_once_atomically_and_never_contacts_provider(inquiry, monkeypatch):
    send = Mock(side_effect=AssertionError("No provider call is allowed during intake"))
    monkeypatch.setattr("integrations.graph_client.requests.post", send)
    first = queue_inquiry_notifications(inquiry)
    second = queue_inquiry_notifications(inquiry)
    assert first["queued"] == 2 and second["queued"] == 0
    assert OutboxMessage.objects.count() == 2
    assert CampaignTouchpoint.objects.filter(lead=inquiry).count() == 1
    message = _family_message(inquiry)
    assert message.status == "PENDING" and message.sent_at is None
    assert "24 hours" not in message.body
    assert "inquiry received" in message.subject
    assert not send.called
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            inquiry.assigned_to_user_id = None
            inquiry.save(update_fields=["assigned_to_user_id"])
            queue_inquiry_notifications(inquiry, event="owner_changed")
            raise RuntimeError("rollback capture")
    assert CampaignTouchpoint.objects.filter(lead=inquiry).count() == 1


def test_unconfigured_capture_stays_actionable_and_can_be_requeued(inquiry, settings):
    settings.GRAPH_FROM_USER = ""
    result = queue_inquiry_notifications(inquiry)
    assert result["queued"] == 0
    assert not OutboxMessage.objects.exists()
    assert inquiry_notification_status(inquiry)["counts"]["not_configured"] == 3
    settings.GRAPH_FROM_USER = "sender@example.com"
    assert queue_inquiry_notifications(inquiry)["queued"] == 2
    assert CampaignTouchpoint.objects.filter(lead=inquiry).count() == 1


def test_worker_recovers_recent_configuration_gap_without_burst_or_stale_welcome(inquiry, settings):
    settings.GRAPH_FROM_USER = ""
    queue_inquiry_notifications(inquiry)
    settings.GRAPH_FROM_USER = "sender@example.com"
    result = process_inquiry_followups.run(school_id=str(inquiry.school_id))
    assert result["intake_notices_queued"] == 2
    assert queue_due_inquiry_followup(_due(inquiry))["queued"] == 1
    assert inquiry_notification_status(inquiry)["counts"]["waiting"] == 1
    old = _family_message(inquiry)
    inquiry.inquiry_received_at = timezone.now() - timedelta(days=30)
    inquiry.save(update_fields=["inquiry_received_at"])
    with pytest.raises(InquiryNotificationSuppressed, match="window elapsed"):
        inquiry_notification_guard(old)
    assert queue_inquiry_notifications(inquiry)["status"] == "manual_follow_up"


def test_consent_and_same_school_owner_permission_are_required(inquiry):
    inquiry.response_consent = False
    inquiry.save(update_fields=["response_consent"])
    other = School.objects.create(name="Other School")
    UserRole.objects.filter(user_id=inquiry.assigned_to_user_id, school=inquiry.school).update(school=other)
    queue_inquiry_notifications(inquiry)
    counts = inquiry_notification_status(inquiry)["counts"]
    assert counts["consent_missing"] == 1 and counts["owner_unassigned"] == 1
    assert not OutboxMessage.objects.exists()


@pytest.mark.parametrize("preference,expected", [("phone", "manual_follow_up"), ("sms", "not_configured")])
def test_family_contact_preference_is_honored(inquiry, preference, expected):
    inquiry.contact_preference = preference
    inquiry.save(update_fields=["contact_preference"])
    result = queue_inquiry_notifications(inquiry)
    assert next(item for item in result["notifications"] if item["audience"] == "family")["status"] == expected
    assert list(OutboxMessage.objects.values_list("to", flat=True)) == ["owner@example.com"]


def test_sms_needs_provider_configuration_and_valid_international_number(inquiry, monkeypatch):
    for key in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"):
        monkeypatch.setenv(key, "synthetic-test-value")
    monkeypatch.setenv("COMMS_SMS_ENABLED", "true")
    inquiry.contact_preference = "sms"
    inquiry.phone = "3025550100"
    inquiry.save(update_fields=["contact_preference", "phone"])
    queue_inquiry_notifications(inquiry)
    assert not OutboxMessage.objects.filter(channel="SMS").exists()
    inquiry.phone = "+13025550100"
    inquiry.save(update_fields=["phone"])
    queue_inquiry_notifications(inquiry)
    assert OutboxMessage.objects.filter(channel="SMS", to=inquiry.phone).count() == 1


def test_day_one_three_seven_steps_are_idempotent_and_do_not_complete_staff_work(inquiry):
    _due(inquiry)
    due = inquiry.next_follow_up_at
    for offset in (0, 2, 6):
        now = due + timedelta(days=offset, seconds=1)
        assert queue_due_inquiry_followup(inquiry, now=now)["queued"] == 2
        assert queue_due_inquiry_followup(inquiry, now=now)["queued"] == 0
    inquiry.refresh_from_db()
    assert inquiry.next_follow_up_at == due and inquiry.last_touch_at is None
    assert OutboxMessage.objects.count() == 6
    assert queue_due_inquiry_followup(inquiry, now=due + timedelta(days=20))["queued"] == 0


def test_delayed_worker_only_queues_latest_step_and_respects_followup_opt_in(inquiry):
    _due(inquiry, days=8)
    inquiry.follow_up_consent = False
    inquiry.save(update_fields=["follow_up_consent"])
    assert queue_due_inquiry_followup(inquiry)["queued"] == 1
    row = CampaignTouchpoint.objects.get(lead=inquiry)
    assert row.metadata_json["cadence_day"] == 7
    assert list(OutboxMessage.objects.values_list("to", flat=True)) == ["owner@example.com"]


def test_tour_scheduled_does_not_send_post_tour_message(inquiry):
    _due(inquiry)
    inquiry.stage = LeadStage.TOUR_SCHEDULED
    inquiry.save(update_fields=["stage"])
    result = queue_due_inquiry_followup(inquiry)
    assert result["queued"] == 1
    assert "whether it occurred" in OutboxMessage.objects.get().body
    assert next(item for item in result["notifications"] if item["audience"] == "family")["status"] == "manual_follow_up"


def test_old_queued_cadence_step_is_suppressed_after_worker_outage(inquiry, monkeypatch):
    _due(inquiry)
    queue_due_inquiry_followup(inquiry)
    old_message = _family_message(inquiry)
    later = inquiry.next_follow_up_at + timedelta(days=3)
    monkeypatch.setattr("crm_marketing.inquiry_notifications.timezone.now", lambda: later)
    assert queue_due_inquiry_followup(inquiry)["queued"] == 2
    with pytest.raises(InquiryNotificationSuppressed, match="superseded"):
        inquiry_notification_guard(old_message)


@pytest.mark.parametrize("change", ["consent", "pause", "lost", "contact", "due", "touch", "stage"])
def test_queued_reminder_rechecks_live_consent_and_workflow(inquiry, change):
    queue_due_inquiry_followup(_due(inquiry))
    message = _family_message(inquiry)
    if change == "consent":
        inquiry.follow_up_consent = False
    elif change == "pause":
        inquiry.family_follow_up_enabled = False
    elif change == "lost":
        inquiry.stage = LeadStage.LOST
    elif change == "contact":
        inquiry.email = "updated@example.com"
    elif change == "due":
        inquiry.next_follow_up_at = timezone.now() + timedelta(days=2)
    elif change == "touch":
        inquiry.last_touch_at = timezone.now()
    else:
        inquiry.stage = LeadStage.TOUR_SCHEDULED
    inquiry.save()
    with pytest.raises(InquiryNotificationSuppressed):
        inquiry_notification_guard(message)


def test_conversion_link_stops_reminders_but_does_not_falsify_receipt_ack(inquiry):
    queue_due_inquiry_followup(_due(inquiry))
    reminder = _family_message(inquiry)
    household = Household.objects.create(school_id=inquiry.school_id, name="Prospect")
    application = Application.objects.create(school_id=inquiry.school_id, household=household, status="SUBMITTED")
    inquiry.applications.add(application)
    assert queue_due_inquiry_followup(inquiry)["queued"] == 0
    with pytest.raises(InquiryNotificationSuppressed):
        inquiry_notification_guard(reminder)
    queue_inquiry_notifications(inquiry)
    acknowledgement = OutboxMessage.objects.get(to=inquiry.email, subject__contains="inquiry received")
    inquiry_notification_guard(acknowledgement)


def test_staff_withdrawal_suppresses_pending_reminders_and_cannot_restore_consent(inquiry, monkeypatch):
    queue_due_inquiry_followup(_due(inquiry))
    message = _family_message(inquiry)
    client = APIClient()
    client.force_authenticate(user=UserAccount.objects.get(id=inquiry.assigned_to_user_id))
    url = f"/api/v1/crm/inquiries/{inquiry.id}/"
    headers = {"format": "json", "HTTP_X_SCHOOL_ID": str(inquiry.school_id)}
    assert client.patch(url, {"follow_up_consent": False, "family_follow_up_enabled": True}, **headers).status_code == 400
    inquiry.refresh_from_db()
    assert inquiry.follow_up_consent and inquiry.family_follow_up_enabled
    assert client.patch(url, {"follow_up_consent": False}, **headers).status_code == 200
    inquiry.refresh_from_db()
    assert not inquiry.follow_up_consent and not inquiry.family_follow_up_enabled
    audit = CampaignTouchpoint.objects.get(lead=inquiry, summary="Admissions inquiry updated")
    assert audit.metadata_json == {
        "before": {"follow_up_consent": "True", "family_follow_up_enabled": "True"},
        "after": {"follow_up_consent": "False", "family_follow_up_enabled": "False"},
    }
    send = Mock()
    monkeypatch.setattr("comms.tasks._send", send)
    drain_outbox.run(batch_size=2)
    message.refresh_from_db()
    assert message.status == "DEAD" and message.last_error.startswith("suppressed:")
    assert all(call.args[0].to != inquiry.email for call in send.call_args_list)
    for payload in ({"follow_up_consent": True, "stage": "lost"},
                    {"family_follow_up_enabled": True}, {"follow_up_consent": 0}):
        assert client.patch(url, payload, **headers).status_code == 400
    inquiry.refresh_from_db()
    assert not inquiry.follow_up_consent and not inquiry.family_follow_up_enabled
    assert inquiry.stage == LeadStage.INQUIRY
    assert CampaignTouchpoint.objects.filter(lead=inquiry, summary="Admissions inquiry updated").count() == 1


def test_old_owner_or_revoked_permission_cannot_receive_pending_notice(inquiry):
    queue_inquiry_notifications(inquiry)
    message = OutboxMessage.objects.get(to="owner@example.com")
    UserRole.objects.filter(user_id=inquiry.assigned_to_user_id, school=inquiry.school).delete()
    with pytest.raises(InquiryNotificationSuppressed):
        inquiry_notification_guard(message)


def test_outbox_truth_reports_acceptance_retry_failure_and_terminal_suppression(inquiry, monkeypatch):
    queue_due_inquiry_followup(_due(inquiry))
    message = _family_message(inquiry)
    send = Mock(side_effect=RuntimeError("synthetic provider failure"))
    monkeypatch.setattr("comms.tasks._send", send)
    drain_outbox.run(batch_size=2)
    assert inquiry_notification_status(inquiry)["counts"]["retrying"] == 2
    message.refresh_from_db()
    message.next_attempt_at = timezone.now()
    message.save(update_fields=["next_attempt_at"])
    inquiry.follow_up_consent = False
    inquiry.save(update_fields=["follow_up_consent"])
    send.reset_mock()
    drain_outbox.run(batch_size=1)
    assert not send.called
    message.refresh_from_db()
    assert message.status == "DEAD" and message.last_error.startswith("suppressed:")
    assert inquiry_notification_status(inquiry)["counts"]["suppressed"] == 1
    owner_message = OutboxMessage.objects.get(to="owner@example.com")
    owner_message.status = "SENT"
    owner_message.sent_at = timezone.now()
    owner_message.save(update_fields=["status", "sent_at"])
    status = inquiry_notification_status(inquiry)
    assert status["counts"]["provider_accepted"] == 1 and status["delivery_confirmed"] is None
    owner_message.status = "DEAD"
    owner_message.last_error = "Provider retries exhausted"
    owner_message.save(update_fields=["status", "last_error"])
    assert inquiry_notification_status(inquiry)["counts"]["failed"] == 1
    assert get_current_school() is None


def test_scheduler_scopes_school_and_does_not_starve_after_handled_lead(inquiry):
    _due(inquiry)
    queue_inquiry_notifications(inquiry)
    assert process_inquiry_followups.run(school_id=str(inquiry.school_id), batch_size=1)["events"] == 1
    other = School.objects.create(name="Do not process")
    untouched = MarketingLead.objects.create(school=other, inquiry_received_at=timezone.now(), next_follow_up_at=timezone.now())
    later = MarketingLead.objects.create(school=inquiry.school, inquiry_received_at=timezone.now(), next_follow_up_at=timezone.now())
    result = process_inquiry_followups.run(school_id=str(inquiry.school_id), batch_size=1)
    assert result["events"] == 1
    assert CampaignTouchpoint.objects.filter(lead=later).exists()
    assert not CampaignTouchpoint.objects.filter(lead=untouched).exists()
    assert get_current_school() is None
    with tenant_context(other), pytest.raises(ValueError, match="tenant mismatch"):
        queue_inquiry_notifications(inquiry)


def test_owner_preferences_are_checked_before_enqueue_and_delivery(inquiry):
    preference = NotificationPreference.objects.create(user_id=inquiry.assigned_to_user_id, email_enabled=False)
    queue_inquiry_notifications(inquiry)
    assert not OutboxMessage.objects.filter(to="owner@example.com").exists()
    preference.email_enabled = True
    preference.save(update_fields=["email_enabled"])
    queue_inquiry_notifications(inquiry)
    message = OutboxMessage.objects.get(to="owner@example.com")
    preference.email_enabled = False
    preference.save(update_fields=["email_enabled"])
    with pytest.raises(InquiryNotificationSuppressed):
        inquiry_notification_guard(message)


def test_staff_status_never_borrows_another_school_outbox_record(inquiry):
    queue_inquiry_notifications(inquiry)
    message = _family_message(inquiry)
    message.school_id = str(School.objects.create(name="Different delivery school").id)
    message.save(update_fields=["school_id"])
    assert inquiry_notification_status(inquiry)["counts"]["unavailable"] == 1
    with pytest.raises(InquiryNotificationSuppressed):
        inquiry_notification_guard(message)


def test_mutable_audit_metadata_cannot_downgrade_a_reminder_to_an_acknowledgement(inquiry):
    queue_due_inquiry_followup(_due(inquiry))
    message = _family_message(inquiry)
    audit = CampaignTouchpoint.objects.get(lead=inquiry)
    audit.metadata_json["event"] = "created"
    audit.save(update_fields=["metadata_json"])
    inquiry.follow_up_consent = False
    inquiry.save(update_fields=["follow_up_consent"])
    with pytest.raises(InquiryNotificationSuppressed, match="consent withdrawn"):
        inquiry_notification_guard(message)


def test_delivery_status_requires_correct_durable_notice_and_not_metadata_claims(inquiry):
    queue_inquiry_notifications(inquiry)
    audit = CampaignTouchpoint.objects.get(lead=inquiry)
    audit.metadata_json["notifications"].append({"audience": "family", "channel": "email", "status": "provider_accepted"})
    audit.save(update_fields=["metadata_json"])
    state = inquiry_notification_status(inquiry)
    assert state["counts"]["unavailable"] == 1
    assert "provider_accepted" not in state["counts"]
