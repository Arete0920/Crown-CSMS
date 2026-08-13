"""
Notification dispatcher for CROWN.

Checks per-user NotificationPreference and routes to each enabled channel.
Always delivers in-app. Other channels are opt-in.

Usage:
    from comms.dispatcher import dispatch_message
    dispatch_message(sender=request.user, recipient=target_user,
                     subject="Grade posted", body="<p>Your grade is ready.</p>")
"""
from __future__ import annotations

import logging

from .email_service import send_email
from .inapp_service import send_inapp
from .models import NotificationPreference
from .sms_service import send_sms
from .teams_service import post_to_teams_channel

logger = logging.getLogger(__name__)


def dispatch_message(
    sender,
    recipient,
    subject: str,
    body: str,
) -> None:
    """
    Dispatch a message to all channels the recipient has enabled.

    Args:
        sender:    UserAccount instance (message author).
        recipient: UserAccount instance (message target).
        subject:   Subject/title used for email and in-app header.
        body:      HTML-safe message body.
    """
    prefs, _ = NotificationPreference.objects.get_or_create(user=recipient)

    # In-app is always delivered
    send_inapp(sender, recipient, body, subject=subject)

    if prefs.email_enabled:
        try:
            send_email(sender, recipient, subject, body)
        except Exception:
            logger.exception("Email dispatch error for %s", recipient)

    if prefs.sms_enabled:
        try:
            send_sms(sender, recipient, _html_to_plain(body))
        except Exception:
            logger.exception("SMS dispatch error for %s", recipient)

    if prefs.teams_enabled:
        team_id    = getattr(recipient, "teams_team_id",    None)
        channel_id = getattr(recipient, "teams_channel_id", None)
        if team_id and channel_id:
            try:
                post_to_teams_channel(sender, team_id, channel_id, body)
            except Exception:
                logger.exception("Teams dispatch error for %s", recipient)
        else:
            logger.debug(
                "Teams enabled for %s but team_id/channel_id not set — skipping",
                recipient,
            )


def _html_to_plain(html: str) -> str:
    """Minimal HTML → plain text for SMS (strips tags, trims whitespace)."""
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    return " ".join(text.split())
