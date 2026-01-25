from __future__ import annotations
from typing import Optional
from uuid import UUID

from django.db.models import QuerySet


def get_request_school_id(request) -> Optional[UUID]:
    """
    Hard rule: never leak cross-school data.
    We only return a school_id if we can derive it from the authenticated user or request.
    If we cannot, we return None and the caller must return an empty queryset.
    """
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        # common patterns
        sid = getattr(user, "school_id", None)
        if sid:
            return sid

        school = getattr(user, "school", None)
        if school and getattr(school, "id", None):
            return school.id

    # optional: some stacks attach school_id at middleware
    sid = getattr(request, "school_id", None)
    if sid:
        return sid

    return None


def scope_to_school(request, qs: QuerySet) -> QuerySet:
    sid = get_request_school_id(request)
    if not sid:
        return qs.none()
    return qs.filter(school_id=sid)
