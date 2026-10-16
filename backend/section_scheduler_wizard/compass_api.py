"""Authenticated, read-only Compass metrics from existing published Kairos records.

No new canonical tables, publication rights, or student-level response values.
This endpoint only reads an explicitly authorized school/year/term and preserves
small-cell suppression. It does not assert transactional publication attestation.
"""
from __future__ import annotations

from dataclasses import asdict

from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.permissions import CrownModulePermission
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from households.scoping import get_request_school_id
from section_scheduler_wizard.models import SectionPlacement

from .canonical_snapshot import build_canonical_planning_snapshot
from .compass_published import MAX_MEETINGS, PublishedScheduleCard, summarize_published_kairos


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([CrownModulePermission("scheduling.view")])
def published_scheduling_metrics(request):
    school_id = get_request_school_id(request, required=True)
    year_id = request.query_params.get("academic_year_id")
    term_code = request.query_params.get("term_code")
    if not year_id or not term_code:
        raise ValidationError("Explicit academic year and term required.")

    snapshot = build_canonical_planning_snapshot(
        actor=request.user, school_id=school_id,
        academic_year_id=year_id, term_code=term_code,
    )
    section_ids = list(snapshot.section_inputs)
    # A section must not be projected as safe while an active placement
    # attribute disagrees with its school or academic-year ownership.
    known_rows = SectionPlacement.objects.filter(
        section_id__in=section_ids, is_active=True,
    )
    if known_rows.exclude(
        school_id=snapshot.school_id, academic_year_id=snapshot.academic_year_id,
    ).exists():
        raise ValidationError("Cross-school or cross-year published section attribution.")

    raw = list(known_rows.filter(
        school_id=snapshot.school_id, academic_year_id=snapshot.academic_year_id,
    ).order_by("id")[:MAX_MEETINGS + 1])
    if len(raw) > MAX_MEETINGS:
        raise ValidationError("Published section placements exceed the bounded reporting limit.")

    cards = [
        PublishedScheduleCard(
            placement_id=str(row.id),
            school_id=str(row.school_id),
            academic_year_id=str(row.academic_year_id),
            section_id=str(row.section_id),
            period_id=str(row.period_block_id),
            day_template_id=str(row.day_template_id),
            room_id=str(row.room_id) if row.room_id is not None else None,
        )
        for row in raw
    ]
    try:
        summary = summarize_published_kairos(snapshot, cards)
    except ValueError as exc:
        raise ValidationError("Published scheduling records failed canonical safety validation.") from exc

    # There may have been another write between reading the first snapshot and
    # the schedule cards. Never return a stale canonical roster projection.
    fresh = build_canonical_planning_snapshot(
        actor=request.user, school_id=school_id,
        academic_year_id=year_id, term_code=term_code,
    )
    if fresh.source_fingerprint != snapshot.source_fingerprint:
        response = Response(
            {"status": "STALE", "publication_allowed": False},
            status=409,
        )
        response["Cache-Control"] = "private, no-store"
        return response

    body = asdict(summary)
    body["status"] = "READ_ONLY_PUBLISHED_SUMMARY"
    body["publication_allowed"] = False
    response = Response(body)
    response["Cache-Control"] = "private, no-store"
    return response
