"""Bounded, tenant-scoped reads for the admissions inquiry work queue.

The request's authenticated school is resolved by the caller. Every related-record
query repeats that school scope so malformed legacy relations cannot leak records.
"""
from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from django.core import signing
from django.db.models import F, Prefetch, Q, Window, prefetch_related_objects
from django.db.models.functions import RowNumber
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from applications.models import Application
from crm_marketing.inquiry_notifications import inquiry_notification_statuses
from crm_marketing.models import CampaignTouchpoint, MarketingLead


PAGE_SIZE = 25
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


def _touchpoints_by_lead(*, school_id, lead_ids):
    """Fetch only ten newest school-owned touchpoints per selected lead."""
    results = defaultdict(list)
    if not lead_ids:
        return results
    rows = (
        CampaignTouchpoint.objects.filter(school_id=school_id, lead_id__in=lead_ids)
        .annotate(_queue_position=Window(
            expression=RowNumber(),
            partition_by=[F("lead_id")],
            order_by=[F("occurred_at").desc(), F("id").desc()],
        ))
        .filter(_queue_position__lte=10)
        .order_by("lead_id", "-occurred_at", "-id")
        .values("id", "lead_id", "channel", "summary", "outcome", "occurred_at")
    )
    for row in rows:
        results[row["lead_id"]].append({
            field: row[field] for field in ("id", "channel", "summary", "outcome", "occurred_at")
        })
    return results


def _duplicates_by_email(*, school_id, emails):
    """The newest six per email suffice for five others after excluding self."""
    results = defaultdict(list)
    if not emails:
        return results
    rows = (
        MarketingLead.objects.filter(
            school_id=school_id, email__in=emails, inquiry_received_at__isnull=False,
        )
        .annotate(_email_position=Window(
            expression=RowNumber(),
            partition_by=[F("email")],
            order_by=[F("updated_at").desc(), F("id").desc()],
        ))
        .filter(_email_position__lte=6)
        .order_by("email", "-updated_at", "-id")
        .values("id", "email", "parent_name", "stage")
    )
    for row in rows:
        results[row["email"]].append(row)
    return results


def build_inquiry_page(queryset, *, school_id, params):
    """Return (page, total count, next cursor, preloaded serializer relations)."""
    try:
        limit = int(params.get("limit") or PAGE_SIZE)
    except (TypeError, ValueError) as exc:
        raise ValueError("limit must be an integer from 1 through 100.") from exc
    if not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError("limit must be an integer from 1 through 100.")

    filters = _filters(params)
    total = queryset.count()
    cursor = params.get("cursor")
    if cursor:
        queryset = queryset.filter(_decode_cursor(
            cursor, school_id=school_id, filters=filters, limit=limit,
        ))

    selected = list(queryset.order_by(
        F("next_follow_up_at").asc(nulls_last=True), "created_at", "id",
    )[:limit + 1])
    more = len(selected) > limit
    selected = selected[:limit]
    next_cursor = _encode_cursor(
        selected[-1], school_id=school_id, filters=filters, limit=limit,
    ) if more else None
    if not selected:
        return selected, total, next_cursor, {}

    # This filtered prefetch is deliberate: an invalid cross-school M2M row must
    # never become a readable application by joining through an inquiry.
    prefetch_related_objects(selected, Prefetch(
        "applications",
        queryset=Application.objects.filter(school_id=school_id).only("id", "school_id").order_by("id"),
        to_attr="_queue_school_applications",
    ))

    ids = [lead.id for lead in selected]
    touches = _touchpoints_by_lead(school_id=school_id, lead_ids=ids)
    duplicates = _duplicates_by_email(school_id=school_id, emails={lead.email for lead in selected})
    notifications = inquiry_notification_statuses(selected)

    relations = {}
    for lead in selected:
        relations[lead.id] = {
            "scoped_applications": lead._queue_school_applications,
            "duplicate_candidates": [
                {field: row[field] for field in ("id", "parent_name", "email", "stage")}
                for row in duplicates.get(lead.email, ())
                if row["id"] != lead.id
            ][:5],
            "scoped_touchpoints": touches.get(lead.id, []),
            "notification_status": notifications[lead.id],
        }
    return selected, total, next_cursor, relations
