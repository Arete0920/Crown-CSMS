# backend/crown_api/wizard_common.py
"""
Thin shared helpers for wizard views.
Uses the canonical tenant resolver from households.scoping.
"""
from __future__ import annotations

from households.scoping import get_request_school_id  # noqa: F401 — re-exported
from rest_framework.response import Response


def err(msg: str, code: int = 400) -> Response:
    """Return a JSON error response."""
    return Response({"error": msg}, status=code)
