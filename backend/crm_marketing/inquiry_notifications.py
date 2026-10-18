"""Durable inquiry notices and follow-up work using the shared communications outbox.

These helpers enqueue messages; they never contact a provider. Outbox ``SENT``
means provider acceptance, not an inbox delivery receipt or a completed staff task.
"""
from __future__ import annotations

from datetime import timedelta
import hashlib
import os
import re
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape

from comms.models import NotificationPreference, OutboxMessage
from core.models import UserAccount
from core.permissions import user_has_permission
from core.tenant_models import get_current_school, tenant_context

from .models import CampaignTouchpoint, LeadStage, MarketingLead


OUTBOX_PREFIX = "crm-inquiry:v1:"
AUDIT_KIND = "inquiry_notification"
SUPPRESSED_PREFIX = "suppressed:"
STOPPED_STAGES = {
    LeadStage.APPLICATION_SUBMITTED, LeadStage.ACCEPTED, LeadStage.ENROLLED, LeadStage.LOST,
}
FOLLOW_UP_STEPS = (
    (1, 0, "Contact the family personally and confirm their questions and next step."),
    (3, 2, "Follow up on the overdue inquiry and offer appropriate visit or application support."),
    (7, 6, "Review the overdue inquiry with admissions and agree the next action or closure."),
)


class InquiryNotificationSuppressed(Exception):
    """The underlying permission or business reason for this notice no longer holds."""


def inquiry_notifications_enabled():
    return getattr(settings, "CROWN_INQUIRY_NOTIFICATIONS_ENABLED", False) is True


def _disabled_outcome():
    return {
        "status": "disabled", "new_event": False, "queued": 0,
        "notifications": [], "delivery_confirmed": None,
    }


def _iso(value):
    return value.isoformat() if value else None


def _notification_items(metadata):
    items = metadata.get("notifications", []) if isinstance(metadata, dict) else []
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _email_valid(value):
    try:
        validate_email(value)
    except ValidationError:
        return False
    return True


def _email_configured():
    sender = str(getattr(settings, "GRAPH_FROM_USER", "") or "").strip()
    credentials = [
        os.getenv(f"GRAPH_{field}", "").strip() or os.getenv(f"AZURE_{field}", "").strip()
        for field in ("TENANT_ID", "CLIENT_ID", "CLIENT_SECRET")
    ]
    return bool(sender and _email_valid(sender) and all(credentials))


def _sms_configured():
    from comms.sms_service import _sms_config

    try:
        _sms_config()
    except RuntimeError:
        return False
    return True


def _owner(lead):
    if not lead.assigned_to_user_id:
        return None
    user = UserAccount.objects.filter(id=lead.assigned_to_user_id, is_active=True).first()
    if user is None or not user_has_permission(user, "admissions.edit", school=lead.school):
        return None
    return user


def _converted_or_closed(lead):
    if lead.stage in STOPPED_STAGES or lead.application_id:
        return True
    return lead.applications.filter(school_id=lead.school_id).exists()


def _slot(audience, channel, status, reason="", **extra):
    return {"audience": audience, "channel": channel, "status": status, "reason": reason, **extra}


def _purpose(event_type, day=None):
    return f"followup-{day}" if event_type == "followup" else event_type


def _enqueue(lead, event_key, audience, channel, recipient, subject, body, *, event_type, day=None, **extra):
    identity = f"{event_key}|{audience}|{channel}|{recipient}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:40]
    message, created = OutboxMessage.objects.get_or_create(
        idempotency_key=f"{OUTBOX_PREFIX}{lead.id}:{_purpose(event_type, day)}:{audience}:{digest}",
        defaults={
            "school_id": str(lead.school_id), "channel": channel.upper(),
            "to": recipient, "subject": subject, "body": body,
        },
    )
    if message.school_id != str(lead.school_id):
        raise ValueError("Inquiry notification tenant mismatch.")
    return _slot(audience, channel, "queued", outbox_id=str(message.id), **extra), created


def _family_notice(lead, *, event_key, event_type, day=None):
    channel = lead.contact_preference
    if not lead.response_consent:
        return _slot("family", channel, "consent_missing", "Family response consent is required."), False
    if event_type == "followup":
        if not lead.follow_up_consent or not lead.family_follow_up_enabled:
            return _slot("family", channel, "not_enabled", "Automatic family follow-up is not enabled with family consent."), False
        if lead.stage not in {LeadStage.INQUIRY, LeadStage.APPLICATION_STARTED}:
            return _slot("family", channel, "manual_follow_up", "Confirm visit details and attendance before sending a tour follow-up."), False
        recent_ack = OutboxMessage.objects.filter(
            school_id=str(lead.school_id),
            idempotency_key__startswith=f"{OUTBOX_PREFIX}{lead.id}:created:family:",
            created_at__gt=timezone.now() - timedelta(days=1),
        ).exists()
        if recent_ack:
            return _slot("family", channel, "waiting", "The next family reminder waits at least a day after its acknowledgement was queued."), False
    if channel == "phone":
        return _slot("family", channel, "manual_follow_up", "The family selected a personal phone call."), False
    if channel not in {"email", "sms"}:
        return _slot("family", channel, "invalid_recipient", "Select a supported contact method."), False

    recipient = lead.email.strip() if channel == "email" else lead.phone.strip()
    valid = _email_valid(recipient) if channel == "email" else bool(re.fullmatch(r"\+[1-9]\d{6,14}", recipient))
    if not valid:
        return _slot("family", channel, "invalid_recipient", "A valid email address or international SMS number is required."), False
    configured = _email_configured() if channel == "email" else _sms_configured()
    if not configured:
        return _slot("family", channel, "not_configured", "Configure and verify the selected delivery provider before sending."), False

    school_name = lead.school.name
    if event_type == "created":
        subject = f"{school_name}: inquiry received"
        text = f"Thank you for contacting {school_name}. We received your admissions inquiry. "
        text += "Admissions can help with school information, a visit and application steps."
    else:
        subject = f"{school_name}: admissions follow-up"
        prompts = {
            1: "Do you have questions about the school or your next admissions step?",
            3: "If you would like a visit or help with your application, please contact admissions.",
            7: "If you are still considering our school, please contact admissions with any remaining questions.",
        }
        text = f"Admissions follow-up from {school_name}. {prompts[day]}"
        text += " You can ask admissions to stop these reminders at any time."
    owner = _owner(lead)
    if owner is not None and _email_valid(owner.email):
        text += f" Admissions contact: {owner.email}."
    text += f" Inquiry reference: {lead.id}."
    body = f"<p>{escape(text)}</p>" if channel == "email" else text
    return _enqueue(lead, event_key, "family", channel, recipient, subject, body, event_type=event_type, day=day)


def _owner_notice(lead, *, event_key, event_type, action, day=None):
    if _converted_or_closed(lead):
        return _slot("owner", "email", "suppressed", "The inquiry has moved into the application workflow or closed."), False
    owner = _owner(lead)
    if owner is None:
        return _slot("owner", "email", "owner_unassigned", "Assign an active admissions owner with permission in this school."), False
    opted_in = NotificationPreference.objects.filter(user=owner).values_list("email_enabled", flat=True).first()
    if opted_in is False:
        return _slot("owner", "email", "not_enabled", "The owner's email notifications are disabled."), False
    if not _email_valid(owner.email):
        return _slot("owner", "email", "invalid_recipient", "The admissions owner needs a valid email address."), False
    if not _email_configured():
        return _slot("owner", "email", "not_configured", "Configure and verify Microsoft 365 email delivery; the inquiry remains in the admissions queue."), False
    subject = f"{lead.school.name}: {'inquiry follow-up due' if event_type == 'followup' else 'inquiry assigned'}"
    text = f"{action} Open the admissions inquiry queue and review inquiry {lead.id}."
    return _enqueue(lead, event_key, "owner", "email", owner.email, subject,
                    f"<p>{escape(text)}</p>", event_type=event_type, day=day, owner_id=str(owner.id))


def _record_event(lead, *, event_key, event_type, action, day=None):
    audit = CampaignTouchpoint.objects.filter(
        school_id=lead.school_id, lead=lead,
        metadata_json__kind=AUDIT_KIND, metadata_json__event_key=event_key,
    ).first()
    previous = _notification_items(audit.metadata_json) if audit else []
    queued = 0
    notifications = []
    for audience in (["family", "owner"] if event_type != "owner_changed" else ["owner"]):
        existing = next((item for item in previous if item.get("audience") == audience and item.get("outbox_id")), None)
        if existing is not None:
            try:
                valid = OutboxMessage.objects.filter(
                    id=UUID(str(existing["outbox_id"])), school_id=str(lead.school_id),
                    idempotency_key__startswith=f"{OUTBOX_PREFIX}{lead.id}:{_purpose(event_type, day)}:{audience}:",
                ).exists()
            except ValueError:
                valid = False
            if valid:
                notifications.append(existing)
                continue
        if audience == "family":
            notice, created = _family_notice(lead, event_key=event_key, event_type=event_type, day=day)
        else:
            notice, created = _owner_notice(lead, event_key=event_key, event_type=event_type, action=action, day=day)
        notifications.append(notice)
        queued += int(created)
    notifications.append(_slot("owner", "teams", "not_configured", "A school-specific Teams destination has not been configured."))
    metadata = {
        "kind": AUDIT_KIND, "event_key": event_key, "event": event_type,
        "cadence_day": day, "next_action": action,
        "follow_up_due_at": _iso(lead.next_follow_up_at), "last_touch_at": _iso(lead.last_touch_at),
        "stage": lead.stage, "notifications": notifications,
    }
    new_event = audit is None
    if audit is None:
        CampaignTouchpoint.objects.create(
            school_id=lead.school_id, campaign_id=lead.campaign_id, lead=lead,
            channel="system", summary=action[:240], outcome="notification_recorded",
            metadata_json=metadata, occurred_at=timezone.now(),
        )
    elif audit.metadata_json != metadata:
        audit.metadata_json = metadata
        audit.save(update_fields=["metadata_json"])
    return {"new_event": new_event, "queued": queued, "notifications": notifications}


def _locked_lead(lead):
    current = get_current_school()
    if current is not None and str(current.pk) != str(lead.school_id):
        raise ValueError("Inquiry notification tenant mismatch.")
    return MarketingLead.objects.select_for_update().select_related("school").get(
        pk=lead.pk, school_id=lead.school_id,
    )


@transaction.atomic
def queue_inquiry_notifications(lead, *, event="created"):
    """Record an acknowledgement/assignment outcome atomically, without network I/O."""
    if event not in {"created", "owner_changed"}:
        raise ValueError("Unsupported inquiry notification event.")
    lead = _locked_lead(lead)
    if not inquiry_notifications_enabled():
        return _disabled_outcome()
    if not lead.school.is_active or lead.stage in {LeadStage.LOST, LeadStage.ENROLLED}:
        return {"status": "suppressed", "notifications": [], "delivery_confirmed": None}
    if event == "created" and lead.inquiry_received_at and lead.inquiry_received_at < timezone.now() - timedelta(days=1):
        return {"status": "manual_follow_up", "notifications": [], "delivery_confirmed": None}
    event_key = event if event == "created" else f"owner_changed:{lead.assigned_to_user_id}"
    with tenant_context(lead.school):
        result = _record_event(lead, event_key=event_key, event_type=event,
                               action="Review the new inquiry, confirm the preferred contact method and make the next contact.")
    return {"status": "queued" if result["queued"] else "recorded", **result, "delivery_confirmed": None}


def _due_step(lead, now):
    due = lead.next_follow_up_at
    if due is None or due > now:
        return None
    # A real contact resets the reminder window even if an older due date remains.
    if lead.last_touch_at and lead.last_touch_at >= due:
        due = lead.last_touch_at + timedelta(days=1)
    eligible = [(day, action) for day, offset, action in FOLLOW_UP_STEPS if due + timedelta(days=offset) <= now]
    return eligible[-1] if eligible else None


@transaction.atomic
def queue_due_inquiry_followup(lead, *, now=None):
    """Queue the latest due cadence step once; preserve the staff's overdue obligation."""
    lead = _locked_lead(lead)
    if not inquiry_notifications_enabled():
        return _disabled_outcome()
    step = _due_step(lead, now or timezone.now())
    if not lead.school.is_active or step is None or _converted_or_closed(lead):
        return {"new_event": False, "queued": 0, "notifications": []}
    day, action = step
    if lead.stage == LeadStage.TOUR_SCHEDULED:
        action = "Confirm the scheduled visit and whether it occurred before choosing the family's next step."
    snapshot = f"{_iso(lead.next_follow_up_at)}|{_iso(lead.last_touch_at)}|{lead.stage}|{day}"
    event_key = f"followup:{hashlib.sha256(snapshot.encode('utf-8')).hexdigest()[:40]}"
    with tenant_context(lead.school):
        return _record_event(lead, event_key=event_key, event_type="followup", action=action, day=day)


def _message_state(message):
    if message.status == OutboxMessage.STATUS_SENT:
        return "provider_accepted"
    if message.status == OutboxMessage.STATUS_DEAD and message.last_error.startswith(SUPPRESSED_PREFIX):
        return "suppressed"
    if message.status in {OutboxMessage.STATUS_DEAD, OutboxMessage.STATUS_FAILED}:
        return "failed"
    return "retrying" if message.attempts else "queued"


def inquiry_notification_status(lead):
    """Read truthful channel outcomes from their tenant-scoped durable outbox records."""
    rows = list(CampaignTouchpoint.objects.filter(
        school_id=lead.school_id, lead=lead, metadata_json__kind=AUDIT_KIND,
    ).order_by("-occurred_at", "-id")[:100])
    ids = []
    for row in rows:
        for item in _notification_items(row.metadata_json):
            try:
                ids.append(UUID(str(item.get("outbox_id"))))
            except ValueError:
                continue
    messages = {str(item.pk): item for item in OutboxMessage.objects.filter(school_id=str(lead.school_id), pk__in=ids)}
    notifications = []
    counts = {}
    for row in rows:
        for item in _notification_items(row.metadata_json):
            notice = {**item, "event": row.metadata_json.get("event"), "recorded_at": _iso(row.occurred_at)}
            if item.get("outbox_id"):
                message = messages.get(str(item["outbox_id"]))
                prefix = f"{OUTBOX_PREFIX}{lead.id}:{_purpose(row.metadata_json.get('event'), row.metadata_json.get('cadence_day'))}:{item.get('audience')}:"
                if (message is None or not message.idempotency_key.startswith(prefix)
                        or item.get("channel") != message.channel.lower()):
                    notice.update(status="unavailable", reason="The linked delivery record is unavailable.")
                else:
                    state = _message_state(message)
                    notice.update(status=state, attempts=message.attempts,
                                  provider_accepted_at=_iso(message.sent_at), delivery_confirmed=None)
                    if state == "suppressed":
                        notice["reason"] = message.last_error[len(SUPPRESSED_PREFIX):].strip()
                    elif state in {"retrying", "failed"}:
                        notice["reason"] = "Provider delivery has not succeeded; review communications delivery status."
            elif notice.get("status") not in {"not_configured", "not_enabled", "consent_missing", "owner_unassigned", "manual_follow_up", "invalid_recipient", "waiting", "suppressed"}:
                notice.update(status="unavailable", reason="A durable outbox record is required to establish delivery status.")
            notifications.append(notice)
            counts[notice["status"]] = counts.get(notice["status"], 0) + 1
    return {
        "enabled": inquiry_notifications_enabled(), "notifications": notifications,
        "counts": counts, "delivery_confirmed": None,
    }


def inquiry_notification_guard(message):
    """Recheck contact consent, workflow and owner authority immediately before delivery."""
    if not message.idempotency_key.startswith(OUTBOX_PREFIX):
        return
    if not inquiry_notifications_enabled():
        raise InquiryNotificationSuppressed("Inquiry notifications are disabled by deployment configuration.")
    parts = message.idempotency_key.split(":")
    if len(parts) != 6 or parts[3] not in {"created", "owner_changed", "followup-1", "followup-3", "followup-7"} or parts[4] not in {"family", "owner"}:
        raise InquiryNotificationSuppressed("Unrecognized inquiry notification purpose.")
    purpose, audience = parts[3:5]
    is_followup = purpose.startswith("followup-")
    try:
        lead = MarketingLead.objects.select_related("school").filter(pk=parts[2], school_id=message.school_id).first()
    except (IndexError, ValueError, ValidationError):
        lead = None
    if lead is None:
        raise InquiryNotificationSuppressed("Inquiry is unavailable in the message's school.")
    if purpose == "created" and lead.inquiry_received_at and lead.inquiry_received_at < timezone.now() - timedelta(days=1):
        raise InquiryNotificationSuppressed("The acknowledgement window elapsed; follow up through the current admissions task.")
    records = CampaignTouchpoint.objects.filter(school_id=lead.school_id, lead=lead, metadata_json__kind=AUDIT_KIND)
    matched = next(((row.metadata_json, item) for row in records
                    for item in _notification_items(row.metadata_json)
                    if item.get("outbox_id") == str(message.id)), None)
    if matched is None:
        raise InquiryNotificationSuppressed("Inquiry notification audit linkage is unavailable.")
    event, notice = matched
    if notice.get("audience") != audience or notice.get("channel") != message.channel.lower():
        raise InquiryNotificationSuppressed("Inquiry notification channel or audience does not match its delivery record.")
    if lead.stage in {LeadStage.LOST, LeadStage.ENROLLED}:
        raise InquiryNotificationSuppressed("Inquiry is closed.")
    if is_followup:
        if _converted_or_closed(lead):
            raise InquiryNotificationSuppressed("Inquiry converted or closed before follow-up delivery.")
        if (event.get("follow_up_due_at") != _iso(lead.next_follow_up_at)
                or event.get("last_touch_at") != _iso(lead.last_touch_at)
                or event.get("stage") != lead.stage):
            raise InquiryNotificationSuppressed("Inquiry follow-up changed after this reminder was queued.")
        step = _due_step(lead, timezone.now())
        if step is None or purpose != f"followup-{step[0]}":
            raise InquiryNotificationSuppressed("A later follow-up step superseded this queued reminder.")
    if audience == "family":
        if not lead.response_consent:
            raise InquiryNotificationSuppressed("Family response consent was withdrawn.")
        if is_followup and (not lead.follow_up_consent or not lead.family_follow_up_enabled):
            raise InquiryNotificationSuppressed("Automatic family follow-up was disabled or consent withdrawn.")
        expected = lead.email.strip() if message.channel == "EMAIL" else lead.phone.strip()
        if lead.contact_preference != message.channel.lower() or expected != message.to:
            raise InquiryNotificationSuppressed("The family contact details or preference changed.")
    elif audience == "owner":
        if _converted_or_closed(lead):
            raise InquiryNotificationSuppressed("Inquiry moved into the application workflow or closed.")
        owner = _owner(lead)
        if owner is None or str(owner.pk) != notice.get("owner_id") or owner.email != message.to:
            raise InquiryNotificationSuppressed("The assigned admissions owner changed or lost school authority.")
        if NotificationPreference.objects.filter(user=owner, email_enabled=False).exists():
            raise InquiryNotificationSuppressed("The owner's email notifications were disabled.")
    else:
        raise InquiryNotificationSuppressed("Unrecognized inquiry notification audience.")
