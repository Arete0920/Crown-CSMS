from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count, Min
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AcademicYear
from .models import Application, Applicant, ApplicationEvent


STAGES = [
    "inquiry",
    "tour_scheduled",
    "tour_completed",
    "application_started",
    "application_submitted",
    "in_review",
    "accepted",
    "waitlisted",
    "declined",
    "enrolled",
]

SOURCES = [
    "church_referral",
    "facebook",
    "instagram",
    "google",
    "direct_mail_qr",
    "website",
    "word_of_mouth",
    "other",
]


def _d2(x: Decimal) -> str:
    """Decimal to string with exactly 2 decimals."""
    return str(x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _rate(numer: int, denom: int) -> str:
    if denom <= 0:
        return "0.00"
    return _d2(Decimal(numer) / Decimal(denom))


def _get_school_id(request) -> str:
    school_id = request.headers.get("X-School-Id")
    if not school_id:
        # Match your Financial Aid behavior
        return ""
    return school_id


def _normalize_ay_name(name: str) -> str:
    """Normalize academic year name: en-dash (–) and em-dash (—) to hyphen (-)."""
    return (name or "").strip().replace("\u2013", "-").replace("\u2014", "-")


def _get_academic_year_window(school_id: str, academic_year: str | None):
    """
    Returns: (academic_year_name, start_date, end_date, is_explicit)
    If academic_year is None, use current AcademicYear for the school.
    is_explicit: True if academic_year param was provided (indicates date filtering should apply).
    """
    qs = AcademicYear.objects.filter(school_id=school_id)
    is_explicit = academic_year is not None

    if academic_year:
        # Normalize the lookup name (hyphen vs en-dash)
        ay_norm = _normalize_ay_name(academic_year)
        # Try exact match first
        ay = qs.filter(name=academic_year).first()
        # If not found, try with normalization
        if not ay:
            # Fall back to checking all names with normalization
            for candidate in qs:
                if _normalize_ay_name(candidate.name) == ay_norm:
                    ay = candidate
                    break
        if not ay:
            ay = None
    else:
        ay = qs.filter(is_current=True).first() or qs.order_by("-start_date").first()

    if not ay:
        # No AY configured: treat as unbounded
        return (academic_year or "unknown", None, None, is_explicit)

    return (ay.name, ay.start_date, ay.end_date, is_explicit)


def _compute_stage(
    app: Application,
    has_inquiry: bool,
    has_tour_scheduled: bool,
    has_tour_completed: bool,
    decision: str | None,
    enrolled: bool,
) -> str:
    """Deterministically compute stage from Application status + events."""
    # Highest precedence: enrolled
    if enrolled:
        return "enrolled"

    # Decisions (from events)
    if decision == "accepted":
        return "accepted"
    if decision == "waitlisted":
        return "waitlisted"
    if decision == "declined":
        return "declined"

    # Review/submission
    if app.status == "IN_REVIEW":
        return "in_review"
    if app.status == "SUBMITTED":
        return "application_submitted"
    if app.status == "DRAFT":
        # If inquiry exists, show earlier funnel stage if available
        if has_tour_completed:
            return "tour_completed"
        if has_tour_scheduled:
            return "tour_scheduled"
        if has_inquiry:
            return "inquiry"
        return "application_started"
    if app.status == "DECIDED":
        # If DECIDED but no decision event exists, treat as declined (strictness avoids "mystery accepted").
        return "declined"

    return "application_started"


def _decision_from_payload(payload: dict) -> str | None:
    """Extract decision from ApplicationEvent payload."""
    d = (payload or {}).get("decision")
    if d in ("accepted", "waitlisted", "declined"):
        return d
    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_summary(request):
    """GET /api/v1/admissions/summary/ - Pipeline KPIs for admissions director."""
    from core.permissions import user_has_permission
    school = getattr(request, "school", None)
    if not user_has_permission(request.user, "admissions.view", school=school):
        return Response({"detail": "Permission denied."}, status=403)
    school_id = _get_school_id(request)
    if not school_id:
        return Response({"detail": "Missing required header: X-School-Id"}, status=400)

    academic_year = request.query_params.get("academic_year")
    date_from = (
        parse_date(request.query_params.get("date_from"))
        if request.query_params.get("date_from")
        else None
    )
    date_to = (
        parse_date(request.query_params.get("date_to"))
        if request.query_params.get("date_to")
        else None
    )

    ay_name, ay_start, ay_end, ay_explicit = _get_academic_year_window(school_id, academic_year)

    apps = Application.objects.filter(school_id=school_id)

    # Academic year date filter only if academic_year param was explicitly provided
    # This prevents "seeded data but shows 0" when data.created_at is outside AY window
    if ay_explicit and ay_start and ay_end:
        apps = apps.filter(created_at__date__gte=ay_start, created_at__date__lte=ay_end)

    # Optional date window override
    if date_from:
        apps = apps.filter(created_at__date__gte=date_from)
    if date_to:
        apps = apps.filter(created_at__date__lte=date_to)

    app_ids = list(apps.values_list("id", flat=True))
    pipeline_total = len(app_ids)

    # Pull event facts in one sweep
    events = ApplicationEvent.objects.filter(school_id=school_id, application_id__in=app_ids)

    # Precompute sets for stage signals
    inquiry_app_ids = set(
        events.filter(event_type="inquiry_created").values_list("application_id", flat=True)
    )
    tour_scheduled_app_ids = set(
        events.filter(event_type="tour_scheduled").values_list("application_id", flat=True)
    )
    tour_completed_app_ids = set(
        events.filter(event_type="tour_completed").values_list("application_id", flat=True)
    )
    enrolled_app_ids = set(
        events.filter(event_type="enrollment_confirmed").values_list("application_id", flat=True)
    )

    decision_events = events.filter(event_type="decision_made").values("application_id", "payload")
    decision_by_app = {}
    for r in decision_events:
        decision = _decision_from_payload(r.get("payload") or {})
        if decision:
            decision_by_app[r["application_id"]] = decision

    # Count stages
    stage_counts = {k: 0 for k in STAGES}
    for app in apps:
        stage = _compute_stage(
            app=app,
            has_inquiry=(app.id in inquiry_app_ids),
            has_tour_scheduled=(app.id in tour_scheduled_app_ids),
            has_tour_completed=(app.id in tour_completed_app_ids),
            decision=decision_by_app.get(app.id),
            enrolled=(app.id in enrolled_app_ids),
        )
        stage_counts[stage] += 1

    # Conversions
    inquiry = stage_counts["inquiry"]
    submitted = stage_counts["application_submitted"]
    accepted = stage_counts["accepted"]
    enrolled = stage_counts["enrolled"]

    conversion = {
        "inquiry_to_submitted": _rate(submitted, inquiry),
        "submitted_to_accepted": _rate(accepted, submitted),
        "accepted_to_enrolled": _rate(enrolled, accepted),
    }

    # Velocity (avg days) using MIN timestamp per event type per app
    def _avg_days(a_type: str, b_type: str) -> str:
        # For each app, earliest a and earliest b
        a_times = dict(
            events.filter(event_type=a_type)
            .values("application_id")
            .annotate(t=Min("created_at"))
            .values_list("application_id", "t")
        )
        b_times = dict(
            events.filter(event_type=b_type)
            .values("application_id")
            .annotate(t=Min("created_at"))
            .values_list("application_id", "t")
        )
        deltas = []
        for app_id, at in a_times.items():
            bt = b_times.get(app_id)
            if at and bt and bt >= at:
                deltas.append((bt - at).days + (bt - at).seconds / 86400.0)
        if not deltas:
            return "0.00"
        return _d2(Decimal(sum(deltas)) / Decimal(len(deltas)))

    velocity = {
        "inquiry_to_tour_completed_avg": _avg_days("inquiry_created", "tour_completed"),
        "tour_completed_to_submitted_avg": _avg_days("tour_completed", "application_submitted"),
        "submitted_to_decision_avg": _avg_days("application_submitted", "decision_made"),
    }

    # Top sources — from Applicant.source (canonical)
    applicants = Applicant.objects.filter(school_id=school_id, application_id__in=app_ids)
    top_sources_qs = (
        applicants.values("source")
        .annotate(total=Count("id"))
        .order_by("-total", "source")[:10]
    )
    top_sources = [{"source": r["source"], "total": r["total"]} for r in top_sources_qs]

    return Response(
        {
            "academic_year": ay_name,
            "date_from": request.query_params.get("date_from"),
            "date_to": request.query_params.get("date_to"),
            "pipeline": {"total": pipeline_total, "by_stage": stage_counts},
            "conversion": conversion,
            "velocity_days": velocity,
            "top_sources": top_sources,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_drilldown(request):
    """GET /api/v1/admissions/drilldown/ - Paginated lead details."""
    from core.permissions import user_has_permission
    school = getattr(request, "school", None)
    if not user_has_permission(request.user, "admissions.view", school=school):
        return Response({"detail": "Permission denied."}, status=403)
    school_id = _get_school_id(request)
    if not school_id:
        return Response({"detail": "Missing required header: X-School-Id"}, status=400)

    academic_year = request.query_params.get("academic_year")
    stage = request.query_params.get("stage")
    source = request.query_params.get("source")

    try:
        limit = int(request.query_params.get("limit", "25"))
        offset = int(request.query_params.get("offset", "0"))
    except ValueError:
        return Response({"detail": "limit and offset must be integers"}, status=400)

    if limit < 1 or limit > 200 or offset < 0:
        return Response(
            {"detail": "limit must be 1..200 and offset must be >= 0"}, status=400
        )

    if stage is not None and stage != "" and stage not in STAGES:
        return Response(
            {"detail": f"Invalid stage '{stage}'. Must be one of: {', '.join(STAGES)}."}, 
            status=400
        )

    ay_name, ay_start, ay_end, ay_explicit = _get_academic_year_window(school_id, academic_year)

    apps = Application.objects.filter(school_id=school_id)
    if ay_explicit and ay_start and ay_end:
        apps = apps.filter(created_at__date__gte=ay_start, created_at__date__lte=ay_end)

    app_ids = list(apps.values_list("id", flat=True))

    # Load event signals
    events = ApplicationEvent.objects.filter(school_id=school_id, application_id__in=app_ids)
    inquiry_app_ids = set(
        events.filter(event_type="inquiry_created").values_list("application_id", flat=True)
    )
    tour_scheduled_app_ids = set(
        events.filter(event_type="tour_scheduled").values_list("application_id", flat=True)
    )
    tour_completed_app_ids = set(
        events.filter(event_type="tour_completed").values_list("application_id", flat=True)
    )
    enrolled_app_ids = set(
        events.filter(event_type="enrollment_confirmed").values_list("application_id", flat=True)
    )

    decision_by_app = {}
    for r in events.filter(event_type="decision_made").values("application_id", "payload"):
        d = _decision_from_payload(r.get("payload") or {})
        if d:
            decision_by_app[r["application_id"]] = d

    # Query Applicants as the canonical "lead rows"
    qs = Applicant.objects.filter(school_id=school_id, application_id__in=app_ids)

    if source:
        qs = qs.filter(source=source)

    # Compute stage per row in Python (MVP).
    rows_all = []
    apps_by_id = {a.id: a for a in apps}

    for ap in qs.select_related("application"):
        app = apps_by_id.get(ap.application_id)
        if not app:
            continue

        st = _compute_stage(
            app=app,
            has_inquiry=(app.id in inquiry_app_ids),
            has_tour_scheduled=(app.id in tour_scheduled_app_ids),
            has_tour_completed=(app.id in tour_completed_app_ids),
            decision=decision_by_app.get(app.id),
            enrolled=(app.id in enrolled_app_ids),
        )

        if stage and st != stage:
            continue

        flags = ap.flags or {}
        rows_all.append(
            {
                "lead_id": str(ap.id),
                "application_id": str(app.id),
                "student_id": str(ap.student_id) if ap.student_id else None,
                "stage": st,
                "source": ap.source or "other",
                "grade_applying_for": ap.grade_applying_for,
                "created_at": app.created_at.isoformat(),
                "updated_at": app.updated_at.isoformat(),
                "flags": {
                    "duplicate_suspected": bool(flags.get("duplicate_suspected", False)),
                    "bot_suspected": bool(flags.get("bot_suspected", False)),
                },
            }
        )

    total = len(rows_all)
    page = rows_all[offset : offset + limit]

    response = Response(
        {
            "academic_year": ay_name,
            "stage": stage or None,
            "source": source or None,
            "total": total,
            "limit": limit,
            "offset": offset,
            "rows": page,  # DEPRECATED: use 'results' instead
            "results": page,
        }
    )
    
    # Add deprecation warning header for clients still checking 'rows'
    response["X-Deprecated-Field"] = "rows; use results instead; sunset 2026-06-01"
    
    return response
