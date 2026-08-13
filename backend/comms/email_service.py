"""
Microsoft Graph email service for Crown2026.

Sends email on behalf of the sender via the Graph /sendMail endpoint using
client-credentials (app token), not delegated auth.
"""
from __future__ import annotations

import logging
import os

import requests
from django.utils import timezone

from .models import MessageLog

logger = logging.getLogger(__name__)

_TENANT_ID     = os.getenv("AZURE_TENANT_ID", "")
_CLIENT_ID     = os.getenv("AZURE_CLIENT_ID", "")
_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")

_TOKEN_URL = f"https://login.microsoftonline.com/{_TENANT_ID}/oauth2/v2.0/token"


def _get_graph_token() -> str:
    """Obtain an app-only access token for Microsoft Graph."""
    resp = requests.post(
        _TOKEN_URL,
        data={
            "client_id":     _CLIENT_ID,
            "client_secret": _CLIENT_SECRET,
            "scope":         "https://graph.microsoft.com/.default",
            "grant_type":    "client_credentials",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def send_email(sender, recipient, subject: str, body_html: str) -> MessageLog:
    """
    Send an HTML email from `sender` to `recipient` via Microsoft Graph.

    Args:
        sender:    UserAccount instance — must have a valid M365 mailbox.
        recipient: UserAccount instance.
        subject:   Email subject line.
        body_html: HTML body content.

    Returns:
        MessageLog record (delivery_status="sent" or "failed").
    """
    log = MessageLog.objects.create(
        sender=sender,
        recipient=recipient,
        channel="email",
        subject=subject,
        body=body_html,
        delivery_status="pending",
    )

    try:
        token = _get_graph_token()
        url = f"https://graph.microsoft.com/v1.0/users/{sender.email}/sendMail"
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json={
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content":     body_html,
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": recipient.email}}
                    ],
                }
            },
            timeout=15,
        )
        resp.raise_for_status()
        log.delivery_status = "sent"
        log.delivered_at    = timezone.now()
        logger.info("Email sent: %s → %s", sender.email, recipient.email)
    except Exception as exc:
        log.delivery_status = "failed"
        log.error_message   = str(exc)
        logger.error("Email failed %s → %s: %s", sender.email, recipient.email, exc)

    log.save()
    return log
