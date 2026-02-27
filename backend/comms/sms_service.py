"""
Twilio SMS service for Crown2026.

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
        logger.info("SMS sent to %s sid=%s", phone, msg.sid)
    except Exception as exc:
        log.delivery_status = "failed"
        log.error_message   = str(exc)
        logger.error("SMS failed to %s: %s", phone, exc)

    log.save()
    return log
