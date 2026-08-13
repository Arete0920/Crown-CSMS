"""
Tenant context resolution for CROWN.

Thin wrapper over the canonical households.scoping resolver.
Provides a typed TenantContext dataclass for callers that want
structured access to the resolved tenant rather than a bare UUID.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from django.http import HttpRequest


@dataclass(frozen=True)
class TenantContext:
    """Resolved tenant for the current request."""

    school_id: uuid.UUID

    @property
    def school_id_str(self) -> str:
        return str(self.school_id)


def get_request_school_id(request: HttpRequest, *, required: bool = True) -> Optional[uuid.UUID]:
    """
    Resolve the school_id from the current request.

    Delegates to the canonical households.scoping resolver.
    Returns None (or raises) if no tenant can be resolved and required=True.
    """
    from households.scoping import get_request_school_id as _resolve  # noqa: PLC0415

    return _resolve(request, required=required)


def resolve_tenant(request: HttpRequest) -> Optional[TenantContext]:
    """
    Return a TenantContext for the current request, or None if no tenant is set.

    Does NOT raise — callers that need a hard failure should call
    get_request_school_id(request, required=True) directly.
    """
    school_id = get_request_school_id(request, required=False)
    if school_id is None:
        return None
    return TenantContext(school_id=school_id)
