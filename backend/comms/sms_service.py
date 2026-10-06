"""
Twilio SMS service for CROWN.

Recipient UserAccount must have a `phone_number` field.
SMS is opt-in only — check NotificationPreference before calling.
"""
from __future__ import annotations

import logging
import os

from django.utils import timezone

from .models import MessageLog

logger = logging.getLogger(__name__)

_ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID", "")
_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN", "")
_FROM_NUMBER  = os.getenv("TWILIO_PHONE_NUMBER", "")


def send_sms(sender, recipient, message: str) -> MessageLog:
    """
    Send an SMS to `recipient` via Twilio.

    Args:
        sender:    UserAccount instance (logged for audit).
        recipient: UserAccount instance — must have `phone_number` attribute.
        message:   Plain-text message body (max 1600 chars).

    Returns:
        MessageLog record.
    """
    log = MessageLog.objects.create(
        sender=sender,
        recipient=recipient,
        channel="sms",
        body=message,
        delivery_status="pending",
    )

    phone = getattr(recipient, "phone_number", None)
    if not phone:
        log.delivery_status = "failed"
        log.error_message   = "Recipient has no phone_number"
        log.save()
        logger.warning("SMS skipped — no phone_number for %s", recipient)
        return log

    try:
        from twilio.rest import Client  # lazy import; Twilio optional
        client = Client(_ACCOUNT_SID, _AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=_FROM_NUMBER,
            to=phone,
        )
        log.external_id     = msg.sid
        log.delivery_status = "sent"
        log.delivered_at    = timezone.now()
        logger.info("SMS sent sid=%s recipient_id=%s", msg.sid, getattr(recipient, "id", None))
    except Exception as exc:
        log.delivery_status = "failed"
        log.error_message   = str(exc)
        logger.error("SMS failed recipient_id=%s: %s", getattr(recipient, "id", None), exc)

    log.save()
    return log


def send_sms_to_number(to: str, message: str) -> str:
    """Send an outbox SMS to an already-authorized raw phone number.

    The caller owns consent/entitlement checks before enqueueing. This transport
    validates provider configuration at delivery time and raises on provider
    failure so the durable outbox can retry rather than falsely marking sent.
    """
    phone = str(to or "").strip()
    if not phone:
        raise ValueError("SMS recipient phone number is required")
    if not (_ACCOUNT_SID and _AUTH_TOKEN and _FROM_NUMBER):
        raise RuntimeError("SMS provider credentials are not configured")

    from twilio.rest import Client

    client = Client(_ACCOUNT_SID, _AUTH_TOKEN)
    sent = client.messages.create(
        body=str(message or "")[:1600],
        from_=_FROM_NUMBER,
        to=phone,
    )
    sid = str(getattr(sent, "sid", "") or "").strip()
    if not sid:
        raise RuntimeError("SMS provider returned no delivery identifier")
    return sid
