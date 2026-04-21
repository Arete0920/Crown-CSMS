from __future__ import annotations

import os

from django.utils import timezone


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

    # Keep this helper import-free from optional M365 client classes so URL loading
    # remains stable in local/test environments without extra integration modules.
    sharepoint_url = ""

    teams_configured = _configured("M365_DEFAULT_TENANT_ID", "M365_DEFAULT_CLIENT_ID", "M365_CLIENT_SECRET") or _configured(
        "GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_SECRET"
    )
    sharepoint_configured = bool(os.getenv("M365_SHAREPOINT_SITE_ID") or os.getenv("M365_DEFAULT_DRIVE_ID"))
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
