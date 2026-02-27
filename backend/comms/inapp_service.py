"""
In-app messaging for Crown2026.

Creates a MessageLog record visible to the recipient inside the platform.
No external delivery — always succeeds unless the DB write fails.
"""
from __future__ import annotations

import logging

from .models import MessageLog

logger = logging.getLogger(__name__)


def send_inapp(sender, recipient, message: str, subject: str = "") -> MessageLog:
    """
    Create an in-app message from `sender` to `recipient`.

    Args:
        sender:    UserAccount instance.
        recipient: UserAccount instance.
        message:   Message body.
        subject:   Optional subject/title.

    Returns:
        MessageLog record with delivery_status="sent".
    """
    log = MessageLog.objects.create(
        sender=sender,
        recipient=recipient,
        channel="inapp",
        subject=subject,
        body=message,
        delivery_status="sent",
    )
    logger.info("In-app message created: %s → %s", sender, recipient)
    return log
