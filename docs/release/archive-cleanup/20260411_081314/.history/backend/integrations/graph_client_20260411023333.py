"""
Microsoft Graph API client — server-to-server (client credentials flow).

Requires either the `GRAPH_*` variables or the standard `AZURE_*`
application credentials already used elsewhere in Crown2026.

The token is cached in memory and refreshed automatically before expiry.
"""
from __future__ import annotations

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

_TOKEN_CACHE: dict = {"ts": 0, "token": None, "exp": 0}


def _get_graph_token() -> str:
    now = int(time.time())
    if _TOKEN_CACHE["token"] and now < _TOKEN_CACHE["exp"] - 60:
        return _TOKEN_CACHE["token"]  # type: ignore[return-value]

    tenant = (
        os.getenv("GRAPH_TENANT_ID")
        or os.getenv("AZURE_TENANT_ID")
        or os.getenv("M365_DEFAULT_TENANT_ID", "")
    ).strip()
    client_id = (
        os.getenv("GRAPH_CLIENT_ID")
        or os.getenv("AZURE_CLIENT_ID")
        or os.getenv("M365_DEFAULT_CLIENT_ID", "")
    ).strip()
    client_secret = (
        os.getenv("GRAPH_CLIENT_SECRET")
        or os.getenv("AZURE_CLIENT_SECRET")
        or os.getenv("M365_CLIENT_SECRET", "")
    ).strip()

    if not all([tenant, client_id, client_secret]):
        raise EnvironmentError(
            "Microsoft Graph credentials are not configured. "
            "Set GRAPH_* or AZURE_* application settings."
        )

    url  = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = {
        "client_id":     client_id,
        "client_secret": client_secret,
        "grant_type":    "client_credentials",
        "scope":         "https://graph.microsoft.com/.default",
    }

    resp = requests.post(url, data=data, timeout=10)
    resp.raise_for_status()
    payload = resp.json()

    token = payload["access_token"]
    exp   = now + int(payload.get("expires_in", 3600))
    _TOKEN_CACHE.update({"ts": now, "token": token, "exp": exp})
    return token


def send_mail(from_user: str, to: str, subject: str, body_html: str) -> None:
    """
    Send an email via Microsoft Graph as `from_user`.
    Requires Mail.Send application permission on the App Registration.
    """
    token = _get_graph_token()
    url   = f"https://graph.microsoft.com/v1.0/users/{from_user}/sendMail"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }
    payload = {
        "message": {
            "subject": subject,
            "body":    {"contentType": "HTML", "content": body_html},
            "toRecipients": [{"emailAddress": {"address": to}}],
        },
        "saveToSentItems": "false",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    logger.info("Graph sendMail → %s (subject=%r)", to, subject)
