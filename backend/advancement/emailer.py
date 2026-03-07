"""
Stage 3.3 – Transactional email delivery.

Reads EmailOutbox rows and delivers them via Django's email backend.
Called by the `send_outbox` management command.
"""
from __future__ import annotations

import base64
import logging
from email.mime.base import MIMEBase
from email import encoders

from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_outbox_email(outbox_row) -> bool:
    """
    Attempt to deliver one EmailOutbox row.

    Marks the row as "sent" on success or "failed" after updating last_error.
    Returns True on success, False on failure.

    ``outbox_row`` is an EmailOutbox model instance (not imported at module level
    to avoid circular imports during app startup).
    """
    outbox_row.attempts += 1
    try:
        msg = EmailMultiAlternatives(
            subject=outbox_row.subject,
            body=outbox_row.body_text or "",
            to=[outbox_row.to_email],
        )

        if outbox_row.body_html:
            msg.attach_alternative(outbox_row.body_html, "text/html")

        for att in outbox_row.attachments_json or []:
            filename = att.get("filename", "attachment")
            content_b64 = att.get("content_b64", "")
            mime_type = att.get("mime_type", "application/octet-stream")
            raw_bytes = base64.b64decode(content_b64)

            maintype, subtype = mime_type.split("/", 1) if "/" in mime_type else ("application", "octet-stream")
            part = MIMEBase(maintype, subtype)
            part.set_payload(raw_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)

        msg.send(fail_silently=False)

        outbox_row.status = "sent"
        outbox_row.sent_at = timezone.now()
        outbox_row.last_error = ""
        outbox_row.save(update_fields=["status", "sent_at", "last_error", "attempts"])
        return True

    except Exception as exc:
        error_msg = str(exc)[:1000]
        logger.error("EmailOutbox delivery failed id=%s: %s", outbox_row.id, error_msg)
        outbox_row.last_error = error_msg
        # Keep as "pending" so it can be retried; mark "failed" after max attempts
        if outbox_row.attempts >= 3:
            outbox_row.status = "failed"
        outbox_row.save(update_fields=["status", "last_error", "attempts"])
        return False
