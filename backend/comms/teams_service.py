"""
Microsoft Teams channel messaging via Graph API.

Requires the app to have ChannelMessage.Send application permission
with admin consent granted.
"""
from __future__ import annotations

import logging

import requests
from django.utils import timezone

from .email_service import _get_graph_token
from .models import MessageLog

logger = logging.getLogger(__name__)


def post_to_teams_channel(
    sender,
    team_id: str,
    channel_id: str,
    message: str,
) -> MessageLog:
    """
    Post an HTML message to a specific Teams channel.

    Args:
        sender:     UserAccount instance (logged for audit; Graph call is app-auth).
        team_id:    Microsoft Teams team GUID.
        channel_id: Teams channel GUID within the team.
        message:    HTML message body.

    Returns:
        MessageLog record.
    """
    log = MessageLog.objects.create(
        sender=sender,
        channel="teams",
        body=message,
        delivery_status="pending",
    )

    try:
        token = _get_graph_token()
        url = (
            f"https://graph.microsoft.com/v1.0/teams/{team_id}"
            f"/channels/{channel_id}/messages"
        )
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json={"body": {"contentType": "html", "content": message}},
            timeout=15,
        )
        resp.raise_for_status()
        log.external_id     = resp.json().get("id")
        log.delivery_status = "sent"
        log.delivered_at    = timezone.now()
        logger.info("Teams message posted to %s/%s", team_id, channel_id)
    except Exception as exc:
        log.delivery_status = "failed"
        log.error_message   = str(exc)
        logger.error("Teams post failed %s/%s: %s", team_id, channel_id, exc)

    log.save()
    return log
