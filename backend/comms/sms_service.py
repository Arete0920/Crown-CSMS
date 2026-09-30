"""SMS delivery service for Crown."""
from __future__ import annotations

import logging
import os

from django.utils import timezone

from .models import MessageLog

logger = logging.getLogger(__name__)


def sms_delivery_configured() -> bool:
    """Return True only when all required delivery credentials are present."""
    return bool(
        os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        and os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        and os.getenv("TWILIO_PHONE_NUMBER", "").strip()
    )


def send_sms_to_number(phone: str, message: str) -> str:
    """Send one SMS to a raw phone number and return the external message id."""
    phone = str(phone or "").strip()
    if not phone:
        raise ValueError("SMS recipient phone number is required.")
    if not sms_delivery_configured():
        raise RuntimeError("SMS delivery is not configured.")

    from twilio.rest import Client

    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID", "").strip(),
        os.getenv("TWILIO_AUTH_TOKEN", "").strip(),
    )
    sent = client.messages.create(
        body=str(message or "")[:1600],
        from_=os.getenv("TWILIO_PHONE_NUMBER", "").strip(),
        to=phone,
    )
    return str(sent.sid)


def send_sms(sender, recipient, message: str) -> MessageLog:
    """Send an opt-in SMS to a user account and persist delivery evidence."""
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
        log.error_message = "Recipient has no phone_number"
        log.save(update_fields=["delivery_status", "error_message"])
        logger.warning("SMS skipped - no phone_number for recipient_id=%s", getattr(recipient, "id", None))
        return log

    try:
        external_id = send_sms_to_number(phone, message)
        log.external_id = external_id
        log.delivery_status = "sent"
        log.delivered_at = timezone.now()
        logger.info("SMS sent external_id=%s recipient_id=%s", external_id, getattr(recipient, "id", None))
    except Exception as exc:
        log.delivery_status = "failed"
        log.error_message = str(exc)[:1000]
        logger.exception("SMS delivery failed recipient_id=%s", getattr(recipient, "id", None))

    log.save()
    return log
