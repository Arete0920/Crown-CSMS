"""Authenticated, read-only Kairos feasibility preview over canonical authority.

This endpoint deliberately does not persist or publish schedules. Teacher
availability, preparation policy, and cycle-frequency parameters supplied by
the caller are *unverified assumptions* until separately governed policy
ownership exists; results are therefore always PROVISIONAL. No solver result
confers publication authorization.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.permissions import CrownModulePermission
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from households.scoping import get_request_school_id

from .bounded_feasibility import (
    DEFAULT_NODE_LIMIT, FEASIBLE, MAX_CHOICES_PER_SECTION, MAX_SECTIONS,
    solve_section_meetings,
)
from .canonical_snapshot import build_canonical_planning_snapshot
from .planning_inputs import TeacherPlanningRule
from .preflight import CandidatePlacement
from .what_if_preview import InvalidPreview, freeze_what_if_preview

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERMISSION = [CrownModulePermission("scheduling.view", write_code="scheduling.configure")]


def _invalid(reason):
    raise ValidationError({"error": reason})


def _policy_inputs(raw, snapshot):
    if not isinstance(raw, list) or len(raw) > 1000:
        _invalid("Bounded teacher_rules array required.")
    staff = snapshot.assigned_staff_ids
    if len(raw) != len(staff):
        _invalid("One explicit assumption policy per canonical assigned staff member required.")
    rules = {}
    periods = frozenset(snapshot.period_inputs)
    for item in raw:
        if not isinstance(item, dict):
            _invalid("Teacher policy entries must be objects.")
        key = item.get("staff_id")
        unavailable = item.get("unavailable_period_ids")
        workload = item.get("max_instructional_minutes_per_cycle")
        prep = item.get("minimum_preparation_minutes_per_cycle")
        if (
            not isinstance(key, str) or key not in staff or key in rules
            or not isinstance(unavailable, list) or len(unavailable) > 256
            or any(not isinstance(v, str) for v in unavailable)
            or len(set(unavailable)) != len(unavailable)
            or not set(unavailable) <= periods
            or type(workload) is not int or not 0 <= workload <= 1440 * 14
            or type(prep) is not int or not 0 <= prep <= 1440 * 14
        ):
            _invalid("Invalid, duplicate or foreign teacher policy assumption.")
        rules[key] = TeacherPlanningRule(
            key, snapshot.school_id, snapshot.academic_year_id,
            snapshot.term_code, frozenset(unavailable), workload, prep,
        )
    if set(rules) != staff:
        _invalid("Unverified teacher policy coverage.")
    return rules


def _candidate_inputs(raw, snapshot):
    if not isinstance(raw, dict) or len(raw) > MAX_SECTIONS:
        _invalid("Bounded candidate_domains object required.")
    sections = snapshot.section_inputs
    if set(raw) != set(sections):
        _invalid("Candidate domains must cover all and only canonical sections.")
    domains = {}
    total = 0
    for section_id, candidates in raw.items():
        if not isinstance(candidates, list) or not 1 <= len(candidates) <= MAX_CHOICES_PER_SECTION:
            _invalid("Each section requires a bounded candidate list.")
        total += len(candidates)
        if total > 512:
            _invalid("Candidate limit exceeded.")
        options = []
        for item in candidates:
            if not isinstance(item, dict):
                _invalid("Candidate entries must be objects.")
            period_id = item.get("period_id")
            room_id = item.get("room_id")
            if (
                not isinstance(period_id, str)
                or period_id not in snapshot.period_inputs
                or (room_id is not None and (not isinstance(room_id, str) or room_id not in snapshot.room_inputs))
            ):
                _invalid("Unknown or foreign period/room in proposed candidate.")
            options.append(CandidatePlacement(section_id, period_id, room_id))
        domains[section_id] = tuple(options)
    return domains


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes([CrownModulePermission("scheduling.view")])
def preview_options(request):
    """Expose an authorized opaque-ID planning contract, without student PII."""
    school_id = get_request_school_id(request, required=True)
    year_id = request.query_params.get("academic_year_id")
    term_code = request.query_params.get("term_code")
    if not year_id or not term_code:
        _invalid("Academic year and term required.")
    snapshot = build_canonical_planning_snapshot(
        actor=request.user, school_id=school_id,
        academic_year_id=year_id, term_code=term_code,
    )
    if not 1 <= len(snapshot.section_inputs) <= MAX_SECTIONS:
        _invalid("The school exceeds this bounded planning preview scope.")
    return Response({
        "status": "READY_FOR_PROVISIONAL_PREVIEW",
        "publication_allowed": False,
        "source_fingerprint": snapshot.source_fingerprint,
        "scope": {
            "school_id": snapshot.school_id,
            "academic_year_id": snapshot.academic_year_id,
            "term_code": snapshot.term_code,
        },
        "section_ids": sorted(snapshot.section_inputs),
        "assigned_staff_ids": sorted(snapshot.assigned_staff_ids),
        "periods": [
            {"period_id": key, "day_template_id": p.template_id,
             "start_minute": p.start_minute, "end_minute": p.end_minute,
             "instructional": p.instructional}
            for key, p in sorted(snapshot.period_inputs.items())
        ],
        "rooms": [
            {"room_id": key, "capacity": room.capacity}
            for key, room in sorted(snapshot.room_inputs.items())
        ],
        "missing_policy_authority": "Teacher availability, cycle rotation and preparation rules are provisional caller assumptions.",
    })


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERMISSION)
def preview(request):
    """Compute a provisional proposal, never a publishable schedule receipt."""
    if not isinstance(request.data, dict):
        _invalid("JSON object required.")
    data = request.data
    school_id = get_request_school_id(request, required=True)
    ay = data.get("academic_year_id")
    term = data.get("term_code")
    fingerprint = data.get("expected_source_fingerprint")
    if not isinstance(ay, str) or not isinstance(term, str) or not term or not isinstance(fingerprint, str):
        _invalid("Academic year, term and expected source fingerprint required.")

    # Snapshot performs an additional school-granted permission check and all
    # student/core identity bridge, term and active bell schedule validations.
    snapshot = build_canonical_planning_snapshot(
        actor=request.user, school_id=school_id,
        academic_year_id=ay, term_code=term,
    )
    if fingerprint != snapshot.source_fingerprint:
        return Response(
            {"error": "STALE_SOURCE", "status": "STALE", "publication_allowed": False},
            status=status.HTTP_409_CONFLICT,
        )
    if not 1 <= len(snapshot.section_inputs) <= MAX_SECTIONS:
        _invalid("This bounded preview cannot process the school's selected section count.")
    rules = _policy_inputs(data.get("teacher_rules"), snapshot)
    domains = _candidate_inputs(data.get("candidate_domains"), snapshot)
    occurrences = data.get("template_occurrences")
    if (
        not isinstance(occurrences, dict)
        or set(occurrences) != {p.template_id for p in snapshot.period_inputs.values()}
        or any(type(v) is not int or not 1 <= v <= 14 for v in occurrences.values())
        or sum(occurrences.values()) > 14
    ):
        _invalid("Explicit bounded day-template recurrence assumptions required.")
    node_limit = data.get("node_limit", DEFAULT_NODE_LIMIT)
    # An authenticated web request must never monopolize application workers.
    # Larger research searches belong in an independently governed worker.
    if type(node_limit) is not int or not 1 <= node_limit <= DEFAULT_NODE_LIMIT:
        _invalid("Synchronous node limit must be an integer from 1 to 2500.")

    result = solve_section_meetings(
        school_id=snapshot.school_id,
        academic_year_id=snapshot.academic_year_id,
        term_code=snapshot.term_code,
        sections=snapshot.section_inputs,
        periods=snapshot.period_inputs,
        rooms=snapshot.room_inputs,
        candidate_domains=domains, teacher_rules=rules,
        template_occurrences=occurrences, node_limit=node_limit,
    )
    # The underlying roster, terms, staff and bell schedule may change while
    # a bounded search executes. Never return a stale plan as even provisional.
    refreshed = build_canonical_planning_snapshot(
        actor=request.user, school_id=school_id,
        academic_year_id=ay, term_code=term,
    )
    if refreshed.source_fingerprint != snapshot.source_fingerprint:
        return Response(
            {"error": "SOURCE_CHANGED_DURING_PREVIEW",
             "status": "STALE", "publication_allowed": False},
            status=status.HTTP_409_CONFLICT,
        )
    payload = {
        "status": result.status,
        "nodes_visited": result.nodes_visited,
        "diagnostics": list(result.diagnostics),
        "source_fingerprint": snapshot.source_fingerprint,
        "authority": "PROVISIONAL_INPUT_ASSUMPTIONS",
        "publication_allowed": False,
        "placements": [],
        "preview_digest": None,
    }
    if result.status == FEASIBLE:
        try:
            frozen = freeze_what_if_preview(
                school_id=snapshot.school_id,
                academic_year_id=snapshot.academic_year_id,
                term_code=snapshot.term_code,
                source_fingerprint=snapshot.source_fingerprint,
                sections=snapshot.section_inputs,
                periods=snapshot.period_inputs,
                rooms=snapshot.room_inputs,
                result=result,
                teacher_rules=rules,
                template_occurrences=occurrences,
            )
        except InvalidPreview:
            _invalid("Independent hard-constraint preview validation failed.")
        payload["preview_digest"] = frozen.preview_digest
        payload["placements"] = [
            {"section_id": p.section_id, "period_id": p.period_id, "room_id": p.room_id}
            for p in frozen.placements
        ]
    return Response(payload)
