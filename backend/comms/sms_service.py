"""
SMS delivery service for CROWN.

Recipient UserAccount must have a `phone_number` field. SMS is opt-in only and
provider delivery also requires the explicit COMMS_SMS_ENABLED feature flag.
"""
from __future__ import annotations

import logging
import os

from django.utils import timezone

from .models import MessageLog

logger = logging.getLogger(__name__)


def _env_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _sms_config() -> tuple[str, str, str]:
    """Return validated provider configuration or fail closed."""
    if not _env_enabled("COMMS_SMS_ENABLED"):
        raise RuntimeError("SMS delivery is disabled. Set COMMS_SMS_ENABLED=true to enable it.")

    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
    missing = [
        name
        for name, value in (
            ("TWILIO_ACCOUNT_SID", account_sid),
            ("TWILIO_AUTH_TOKEN", auth_token),
            ("TWILIO_PHONE_NUMBER", from_number),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"SMS provider configuration is incomplete: missing {', '.join(missing)}")
    return account_sid, auth_token, from_number


def send_sms_to_number(to_number: str, message: str) -> str:
    """
    Deliver one SMS to a normalized destination and return the provider message id.

    Provider/configuration failures are intentionally raised so durable outbox
    delivery can retry and ultimately dead-letter rather than falsely mark sent.
    """
    to_number = (to_number or "").strip()
    if not to_number:
        raise ValueError("SMS destination phone number is required.")

    message = str(message or "")
    if not message.strip():
        raise ValueError("SMS message body is required.")
    if len(message) > 1600:
        raise ValueError("SMS message body exceeds the 1600 character provider limit.")

    account_sid, auth_token, from_number = _sms_config()

    from twilio.rest import Client  # lazy import; provider dependency is optional until enabled

    provider_message = Client(account_sid, auth_token).messages.create(
        body=message,
        from_=from_number,
        to=to_number,
    )
    provider_id = str(getattr(provider_message, "sid", "") or "").strip()
    if not provider_id:
        raise RuntimeError("SMS provider returned no message identifier.")
    return provider_id


def send_sms(sender, recipient, message: str) -> MessageLog:
    """
    Send an SMS to `recipient` and retain a user-linked delivery audit record.

    Args:
        sender: UserAccount instance (logged for audit).
        recipient: UserAccount instance with a `phone_number` attribute.
        message: Plain-text message body (max 1600 chars).
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
        log.error_message = "Recipient has no phone_number"
        log.save(update_fields=["delivery_status", "error_message"])
        logger.warning("SMS skipped - no phone_number for recipient_id=%s", getattr(recipient, "id", None))
        return log

    try:
        provider_id = send_sms_to_number(str(phone), message)
        log.external_id = provider_id
        log.delivery_status = "sent"
        log.delivered_at = timezone.now()
        log.error_message = ""
        logger.info("SMS sent sid=%s recipient_id=%s", provider_id, getattr(recipient, "id", None))
    except Exception as exc:
        log.delivery_status = "failed"
        log.error_message = str(exc)
        logger.error("SMS failed recipient_id=%s: %s", getattr(recipient, "id", None), exc)

    log.save()
    return log
