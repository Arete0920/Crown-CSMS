from __future__ import annotations

import os
import time

import requests

from .models import M365SchoolConfig

_TOKEN_CACHE: dict = {"token": None, "exp": 0, "tenant": "", "client_id": ""}


class GraphClient:
    GRAPH_ROOT = "https://graph.microsoft.com/v1.0"

    def __init__(self, school_id):
        self.school_id = str(school_id or "")
        self.config = M365SchoolConfig.objects.filter(school_id=school_id, enabled=True).first()
        self.tenant_id = (
            self.config.tenant_id
            if self.config
            else os.getenv("M365_DEFAULT_TENANT_ID")
            or os.getenv("GRAPH_TENANT_ID")
            or os.getenv("AZURE_TENANT_ID", "")
        ).strip()
        self.client_id = (
            self.config.client_id
            if self.config
            else os.getenv("M365_DEFAULT_CLIENT_ID")
            or os.getenv("GRAPH_CLIENT_ID")
            or os.getenv("AZURE_CLIENT_ID", "")
        ).strip()
        self.client_secret = (
            os.getenv("M365_CLIENT_SECRET")
            or os.getenv("GRAPH_CLIENT_SECRET")
            or os.getenv("AZURE_CLIENT_SECRET", "")
        ).strip()
        self.drive_id = (self.config.default_drive_id if self.config else os.getenv("M365_DEFAULT_DRIVE_ID", "")).strip()
        self.site_id = (self.config.sharepoint_site_id if self.config else os.getenv("M365_SHAREPOINT_SITE_ID", "")).strip()

    def _access_token(self) -> str:
        now = int(time.time())
        if (
            _TOKEN_CACHE["token"]
            and now < int(_TOKEN_CACHE["exp"]) - 60
            and _TOKEN_CACHE["tenant"] == self.tenant_id
            and _TOKEN_CACHE["client_id"] == self.client_id
        ):
            return str(_TOKEN_CACHE["token"])

        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise EnvironmentError("Microsoft Graph credentials are not configured")

        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }
        response = requests.post(url, data=data, timeout=15)
        response.raise_for_status()
        payload = response.json()
        token = payload["access_token"]
        _TOKEN_CACHE.update(
            {
                "token": token,
                "exp": now + int(payload.get("expires_in", 3600)),
                "tenant": self.tenant_id,
                "client_id": self.client_id,
            }
        )
        return token

    def _headers(self, content_type: str = "application/json") -> dict:
        return {
            "Authorization": f"Bearer {self._access_token()}",
            "Content-Type": content_type,
        }

    def get_drive_item(self, item_id: str):
        if not self.drive_id:
            return {}
        url = f"{self.GRAPH_ROOT}/drives/{self.drive_id}/items/{item_id}"
        response = requests.get(url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def upload_small_file(self, folder_path: str, filename: str, content: bytes, content_type: str):
        if not self.drive_id:
            return {"id": "", "webUrl": "", "name": filename}
        clean_folder = folder_path.strip("/")
        url = f"{self.GRAPH_ROOT}/drives/{self.drive_id}/root:/{clean_folder}/{filename}:/content"
        response = requests.put(url, headers=self._headers(content_type), data=content, timeout=60)
        response.raise_for_status()
        return response.json()

    def sharepoint_deeplink(self, folder_path: str = ""):
        if self.site_id and folder_path:
            return f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root:/{folder_path}"
        if self.site_id:
            return f"https://graph.microsoft.com/v1.0/sites/{self.site_id}"
        return ""
