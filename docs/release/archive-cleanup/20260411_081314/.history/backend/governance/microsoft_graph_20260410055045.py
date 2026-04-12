from __future__ import annotations

import os

from django.utils import timezone

from integrations.m365.graph_client import GraphClient


def _configured(*names: str) -> bool:
    return all(bool(os.getenv(name, "").strip()) for name in names)


def build_board_delivery_channels(school_id, *, packet_id: int | None = None, meeting_date=None) -> dict:
    """Return delivery metadata for portal, email, SharePoint, and Teams.

    This keeps governance delivery automation executable and non-manual while
    remaining safe in local/test environments where Microsoft credentials may
    not be configured.
    """
    meeting_label = str(meeting_date or timezone.localdate())
    folder_path = f"BoardPackets/{meeting_label}"

    try:
        client = GraphClient(school_id)
    except Exception:
        client = None

    try:
        sharepoint_url = client.sharepoint_deeplink(folder_path) if client else ""
    except Exception:
        sharepoint_url = ""

    teams_configured = bool(
        client
        and client.tenant_id
        and client.client_id
        and (os.getenv("M365_CLIENT_SECRET") or os.getenv("GRAPH_CLIENT_SECRET"))
    )
    sharepoint_configured = bool(client and (client.site_id or client.drive_id))
    email_configured = _configured("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET") or _configured(
        "M365_DEFAULT_TENANT_ID", "M365_DEFAULT_CLIENT_ID", "M365_CLIENT_SECRET"
    )

    return {
        "manual_only": False,
        "channels": [
            {
                "channel": "portal",
                "status": "ready",
                "url": f"/board/pack/{packet_id}" if packet_id else "/board/dashboard",
            },
            {
                "channel": "email",
                "status": "configured" if email_configured else "not_configured",
                "provider": "microsoft_graph",
            },
            {
                "channel": "sharepoint",
                "status": "configured" if sharepoint_configured else "not_configured",
                "url": sharepoint_url or None,
                "folder_path": folder_path,
            },
            {
                "channel": "teams",
                "status": "configured" if teams_configured else "not_configured",
                "target": "microsoft_teams",
            },
        ],
    }
