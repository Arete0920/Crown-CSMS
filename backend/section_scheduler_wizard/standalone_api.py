"""Read-only standalone Kairos CSV preview/export under school scheduling authority."""
from __future__ import annotations

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.permissions import CrownModulePermission
from households.scoping import get_request_school_id

from .canonical_snapshot import build_canonical_planning_snapshot
from .preflight import CandidatePlacement
from .standalone_interchange import (
    StandaloneInterchangeError, export_standalone_csv, validate_standalone_csv,
)

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [CrownModulePermission("scheduling.view")]


def _snapshot(request):
    data = request.data if request.method == "POST" else request.query_params
    if not isinstance(data, dict) and request.method == "POST":
        raise ValidationError("JSON object required.")
    year, term, digest = (
        data.get("academic_year_id"), data.get("term_code"),
        data.get("expected_source_fingerprint"),
    )
    if not all(isinstance(v, str) and v for v in (year, term, digest)):
        raise ValidationError("Academic year, term, and expected fingerprint required.")
    snapshot = build_canonical_planning_snapshot(
        actor=request.user, school_id=get_request_school_id(request, required=True),
        academic_year_id=year, term_code=term,
    )
    if snapshot.source_fingerprint != digest:
        return None, (year, term, digest)
    return snapshot, (year, term, digest)


def _stale():
    response = Response(
        {"status": "STALE", "publication_allowed": False},
        status=status.HTTP_409_CONFLICT,
    )
    response["Cache-Control"] = "private, no-store"
    return response


def _fresh(request, scope, original_fingerprint):
    year, term, _ = scope
    current = build_canonical_planning_snapshot(
        actor=request.user, school_id=get_request_school_id(request, required=True),
        academic_year_id=year, term_code=term,
    )
    return current.source_fingerprint == original_fingerprint


@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def standalone_import_preview(request):
    """Preflight a bounded CSV text payload; no writes or publishing."""
    snapshot, scope = _snapshot(request)
    if snapshot is None:
        return _stale()
    csv_text = request.data.get("csv_text")
    try:
        report = validate_standalone_csv(
            snapshot=snapshot,
            expected_source_fingerprint=snapshot.source_fingerprint,
            content=csv_text,
        )
    except StandaloneInterchangeError:
        raise ValidationError("Standalone CSV or canonical identifiers invalid.") from None
    if not _fresh(request, scope, snapshot.source_fingerprint):
        return _stale()
    response = Response({
        "status": report.status,
        "source_fingerprint": report.source_fingerprint,
        "file_digest": report.file_digest,
        "candidate_count": report.candidate_count,
        "error_codes": list(report.error_codes),
        "placements": [
            {"section_id": p.section_id, "period_id": p.period_id, "room_id": p.room_id}
            for p in report.placements
        ],
        "publication_allowed": False,
    })
    response["Cache-Control"] = "private, no-store"
    return response


@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def standalone_export_preview(request):
    """Export an authorized proposed section placement set as canonical-ID CSV."""
    snapshot, scope = _snapshot(request)
    if snapshot is None:
        return _stale()
    supplied = request.data.get("placements")
    if not isinstance(supplied, list) or len(supplied) > 2000:
        raise ValidationError("Bounded placement list required.")
    placements = []
    for item in supplied:
        if not isinstance(item, dict) or set(item) != {"section_id", "period_id", "room_id"}:
            raise ValidationError("Exact canonical placement fields required.")
        if any(not isinstance(item[k], str) for k in ("section_id", "period_id")):
            raise ValidationError("Canonical identifiers must be strings.")
        if item["room_id"] is not None and not isinstance(item["room_id"], str):
            raise ValidationError("Room identifier must be a string or null.")
        placements.append(CandidatePlacement(item["section_id"], item["period_id"], item["room_id"]))
    try:
        csv_text = export_standalone_csv(
            snapshot=snapshot,
            expected_source_fingerprint=snapshot.source_fingerprint,
            placements=placements,
        )
    except StandaloneInterchangeError:
        raise ValidationError("Placement export failed hard canonical validation.") from None
    if not _fresh(request, scope, snapshot.source_fingerprint):
        return _stale()
    response = Response({
        "status": "VALID_EXPORT_PREVIEW_ONLY",
        "csv_text": csv_text,
        "source_fingerprint": snapshot.source_fingerprint,
        "publication_allowed": False,
    })
    response["Cache-Control"] = "private, no-store"
    return response
