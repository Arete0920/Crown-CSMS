"""Signed, tenant-scoped cursor for a lightweight admissions work queue.

The request's authenticated school is resolved by the caller. Family histories are fetched only from a separate authorized detail read.
"""
from __future__ import annotations

from uuid import UUID

from django.core import signing
from django.db.models import F, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime



PAGE_SIZE = 100
MAX_PAGE_SIZE = 100
CURSOR_SALT = "crown-crm-inquiries-v1"
CURSOR_MAX_AGE_SECONDS = 24 * 60 * 60


def _filters(params):
    return {
        "stage": params.get("stage") or "",
        "unassigned": params.get("unassigned") == "1",
        "overdue": params.get("overdue") == "1",
    }


def _decode_cursor(token, *, school_id, filters, limit):
    try:
        data = signing.loads(token, salt=CURSOR_SALT, max_age=CURSOR_MAX_AGE_SECONDS)
        if (not isinstance(data, dict)
                or data.get("school_id") != str(school_id)
                or data.get("filters") != filters
                or data.get("limit") != limit):
            raise ValueError("The inquiry page cursor does not match this request.")
        created = parse_datetime(data["created_at"])
        due = parse_datetime(data["next_follow_up_at"]) if data["next_follow_up_at"] is not None else None
        lead_id = UUID(data["id"])
        if (created is None or timezone.is_naive(created)
                or (due is not None and timezone.is_naive(due))):
            raise ValueError("Invalid inquiry page cursor.")
    except (signing.BadSignature, TypeError, KeyError, AttributeError, ValueError) as exc:
        raise ValueError("Invalid, expired, or mismatched inquiry page cursor.") from exc

    position = Q(created_at__gt=created) | Q(created_at=created, id__gt=lead_id)
    if due is None:
        return Q(next_follow_up_at__isnull=True) & position
    return (
        Q(next_follow_up_at__gt=due)
        | Q(next_follow_up_at=due) & position
        | Q(next_follow_up_at__isnull=True)
    )


def _encode_cursor(lead, *, school_id, filters, limit):
    return signing.dumps({
        "school_id": str(school_id),
        "filters": filters,
        "limit": limit,
        "id": str(lead.id),
        "created_at": lead.created_at.isoformat(),
        "next_follow_up_at": lead.next_follow_up_at.isoformat() if lead.next_follow_up_at else None,
    }, salt=CURSOR_SALT)


def paginate_inquiries(queryset, *, school_id, params):
    """Return a bounded page of school-authorized rows without related histories."""
    raw_limit = params.get("limit") or str(PAGE_SIZE)
    if (not isinstance(raw_limit, str) or len(raw_limit) > 3
            or not raw_limit.isascii() or not raw_limit.isdecimal()):
        raise ValueError("limit must be an integer from 1 through 100.")
    limit = int(raw_limit)
    if not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError("limit must be an integer from 1 through 100.")
    filters = _filters(params)
    total = queryset.count()
    token = params.get("cursor")
    if token:
        if len(token) > 4096:
            raise ValueError("Invalid inquiry page cursor.")
        queryset = queryset.filter(_decode_cursor(
            token, school_id=school_id, filters=filters, limit=limit,
        ))
    selected = list(queryset.order_by(
        F("next_follow_up_at").asc(nulls_last=True), "created_at", "id",
    )[:limit + 1])
    more = len(selected) > limit
    page = selected[:limit]
    next_token = _encode_cursor(
        page[-1], school_id=school_id, filters=filters, limit=limit,
    ) if more else None
    return page, total, next_token, limit
