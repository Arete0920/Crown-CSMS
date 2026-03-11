"""
term_structure_wizard/views.py

Wizard #18 — Term & Marking Period Setup

State machine:
  draft → configured → periods_set → committed → verified

Endpoints:
  POST   /                         create_session
  POST   /<id>/configure/          configure_session  (draft → configured)
  POST   /<id>/periods/            set_periods        (configured → periods_set)
  POST   /<id>/commit/             commit_session     (periods_set → committed)
  GET    /<id>/verify/             verify_session     (committed → verified)

Invariants enforced here:
  - Tenant: every lookup filtered on school_id from X-School-Id header
  - AY ownership: AcademicYear.objects.filter(id=..., school_id=...)
  - Period coverage: periods[0].start_date == ay.start_date,
                     periods[-1].end_date == ay.end_date,
                     consecutive periods[i].end_date + 1 day == periods[i+1].start_date
  - Overlap: implied by adjacency check (start_before_expected → overlap)
  - Gap: implied by adjacency check (start_after_expected → gap)
  - Ordering: sort by start_date, assign ordering = index
  - Single active: select_for_update + is_active flip at commit; UniqueConstraint
                   guarantees at most one structure per (school, ay) so flip is a no-op
                   but pattern is retained for consistency with #14–#17
  - Term code lock: at commit time, set(TermWeight.term_code) ⊆ set(MarkingPeriod.code)
                    checked cross-app against grade_scale_wizard.models
  - Idempotent commit: update_or_create MarkingPeriod by (term_structure, code); delete stale
  - Audit: term_structure.commit event, non-fatal on failure
"""

from datetime import date, timedelta
import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.models import AcademicYear, School
from households.scoping import get_request_school_id

from .models import (
    MarkingPeriod,
    TermStructure,
    TermStructureWizardSession,
    VALID_STRUCTURE_TYPES,
)

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(TermStructureWizardSession, id=session_id, school_id=school_id)


def _validate_periods(raw_periods, ay):
    """
    Validates and normalises marking periods against an AcademicYear.

    Rules:
      - At least one period.
      - Each period: code (str), name (str), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD).
      - No duplicate codes.
      - start_date <= end_date (per period).
      - Sorted by start_date; ordering = index.
      - Full calendar coverage:
          periods[0].start_date == ay.start_date
          periods[-1].end_date  == ay.end_date
      - Strict adjacency (no gaps, no overlaps):
          periods[i].end_date + 1 day == periods[i+1].start_date

    Returns (errors: list[str], periods: list[dict] | None)
    """
    errors = []

    if not raw_periods:
        return ["periods: at least one period is required"], None

    seen_codes: dict[str, int] = {}
    valid = []

    for idx, p in enumerate(raw_periods):
        code = (p.get("code") or "").strip()
        name = (p.get("name") or "").strip()
        sd_str = (p.get("start_date") or "").strip()
        ed_str = (p.get("end_date") or "").strip()
        is_grade_term = bool(p.get("is_grade_term", True))

        if not code:
            errors.append(f"periods[{idx}].code is required")
            continue
        if not name:
            errors.append(f"periods[{idx}].name is required")
            continue
        if not sd_str:
            errors.append(f"periods[{idx}].start_date is required")
            continue
        if not ed_str:
            errors.append(f"periods[{idx}].end_date is required")
            continue

        if code in seen_codes:
            errors.append(f"periods[{idx}].code '{code}' is a duplicate")
            continue
        seen_codes[code] = idx

        try:
            sd = date.fromisoformat(sd_str)
        except ValueError:
            errors.append(f"periods[{idx}] ({code}): start_date must be YYYY-MM-DD, got {sd_str!r}")
            continue
        try:
            ed = date.fromisoformat(ed_str)
        except ValueError:
            errors.append(f"periods[{idx}] ({code}): end_date must be YYYY-MM-DD, got {ed_str!r}")
            continue

        if sd > ed:
            errors.append(
                f"periods[{idx}] ({code}): start_date ({sd}) must be <= end_date ({ed})"
            )
            continue

        valid.append({
            "code":          code,
            "name":          name,
            "start_date":    sd,
            "end_date":      ed,
            "is_grade_term": is_grade_term,
        })

    if errors:
        return errors, None

    # Sort by start_date and assign ordering.
    valid.sort(key=lambda p: p["start_date"])
    for i, p in enumerate(valid):
        p["ordering"] = i

    # Full calendar coverage.
    ay_start: date = ay.start_date
    ay_end:   date = ay.end_date

    coverage_errors = []

    if valid[0]["start_date"] != ay_start:
        coverage_errors.append(
            f"periods: first period must start on academic year start date "
            f"({ay_start}); got {valid[0]['start_date']} ('{valid[0]['code']}')"
        )

    if valid[-1]["end_date"] != ay_end:
        coverage_errors.append(
            f"periods: last period must end on academic year end date "
            f"({ay_end}); got {valid[-1]['end_date']} ('{valid[-1]['code']}')"
        )

    for i in range(len(valid) - 1):
        a = valid[i]
        b = valid[i + 1]
        expected_next = a["end_date"] + timedelta(days=1)
        if b["start_date"] != expected_next:
            if b["start_date"] < expected_next:
                coverage_errors.append(
                    f"periods: overlap between '{a['code']}' (ends {a['end_date']}) "
                    f"and '{b['code']}' (starts {b['start_date']}); "
                    f"expected '{b['code']}' to start {expected_next}"
                )
            else:
                coverage_errors.append(
                    f"periods: gap between '{a['code']}' (ends {a['end_date']}) "
                    f"and '{b['code']}' (starts {b['start_date']}); "
                    f"expected '{b['code']}' to start {expected_next}"
                )

    if coverage_errors:
        return coverage_errors, None

    return [], valid


def _periods_to_json(validated):
    """Convert date objects to ISO strings for JSON storage."""
    return [
        {
            "code":          p["code"],
            "name":          p["name"],
            "start_date":    p["start_date"].isoformat(),
            "end_date":      p["end_date"].isoformat(),
            "ordering":      p["ordering"],
            "is_grade_term": p["is_grade_term"],
        }
        for p in validated
    ]


def _periods_from_json(stored):
    """Convert ISO date strings back to date objects."""
    return [
        {
            **p,
            "start_date": date.fromisoformat(p["start_date"]),
            "end_date":   date.fromisoformat(p["end_date"]),
        }
        for p in stored
    ]


# ---------------------------------------------------------------------------
# 1. Create Session
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school = get_object_or_404(School, id=school_id)

    session = TermStructureWizardSession.objects.create(
        school=school,
        created_by=request.user,
        status=TermStructureWizardSession.STATUS_DRAFT,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# 2. Configure
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    errors = []

    ay_id = request.data.get("academic_year_id")
    if not ay_id:
        errors.append("academic_year_id is required")

    structure_type = (request.data.get("structure_type") or "").strip().upper()
    if not structure_type:
        errors.append("structure_type is required")
    elif structure_type not in VALID_STRUCTURE_TYPES:
        errors.append(
            f"structure_type must be one of {sorted(VALID_STRUCTURE_TYPES)}; got {structure_type!r}"
        )

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    ay = get_object_or_404(AcademicYear, id=ay_id, school_id=school_id)

    session.academic_year   = ay
    session.structure_config = {"structure_type": structure_type}
    session.status           = TermStructureWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({
        "session_id":      str(session.id),
        "status":          session.status,
        "academic_year_id": str(ay.id),
        "structure_type":  structure_type,
    })


# ---------------------------------------------------------------------------
# 3. Set Periods
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def set_periods(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == TermStructureWizardSession.STATUS_DRAFT:
        return Response(
            {"error": "Session must be configured before setting periods (currently draft)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw_periods = request.data
    if not isinstance(raw_periods, list):
        return Response(
            {"error": "Request body must be a JSON array of period objects."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ay = session.academic_year
    errors, validated = _validate_periods(raw_periods, ay)
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.periods_config = _periods_to_json(validated)
    session.status         = TermStructureWizardSession.STATUS_PERIODS_SET
    session.save()

    return Response({
        "session_id":    str(session.id),
        "status":        session.status,
        "periods_count": len(validated),
        "period_codes":  [p["code"] for p in validated],
    })


# ---------------------------------------------------------------------------
# 4. Commit
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != TermStructureWizardSession.STATUS_PERIODS_SET:
        return Response(
            {
                "error": (
                    f"Session must be in periods_set state to commit "
                    f"(current: {session.status})."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    school = get_object_or_404(School, id=school_id)
    ay     = session.academic_year
    cfg    = session.structure_config
    periods = _periods_from_json(session.periods_config)

    # Term code lock (cross-app, read-only — perform before entering the write transaction).
    try:
        from grade_scale_wizard.models import GradeScale  # noqa: PLC0415
        from grade_scale_wizard.models import TermWeight as GradeScaleTermWeight  # noqa: PLC0415

        existing_scales = GradeScale.objects.filter(school=school, academic_year=ay)
        term_weight_codes = set(
            GradeScaleTermWeight.objects.filter(
                scale__in=existing_scales
            ).values_list("term_code", flat=True)
        )
        period_codes = {p["code"] for p in periods}
        missing_codes = term_weight_codes - period_codes
        if missing_codes:
            return Response(
                {
                    "error": (
                        f"Term code lock: the following term codes are referenced by existing "
                        f"grade scale weights but are not present in the new marking periods: "
                        f"{', '.join(sorted(missing_codes))}. "
                        f"Either update the grade scale weights to remove those codes, "
                        f"or add matching marking periods."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    except ImportError:
        pass  # grade_scale_wizard not installed — lock skipped

    ts_created     = False
    periods_created = periods_updated = 0

    with transaction.atomic():
        # Lock any existing TermStructure rows for this school+year.
        list(TermStructure.objects.select_for_update().filter(school=school, academic_year=ay))

        # get_or_create — UniqueConstraint(school, ay) guarantees at most one row.
        ts, ts_created = TermStructure.objects.get_or_create(
            school=school,
            academic_year=ay,
            defaults={
                "structure_type": cfg["structure_type"],
                "is_active":      True,
            },
        )
        if not ts_created:
            ts.structure_type = cfg["structure_type"]
            ts.is_active      = True
            ts.save()

        # Upsert MarkingPeriod rows keyed by (term_structure, code).
        for p in periods:
            _, period_new = MarkingPeriod.objects.update_or_create(
                term_structure=ts,
                code=p["code"],
                defaults={
                    "name":         p["name"],
                    "start_date":   p["start_date"],
                    "end_date":     p["end_date"],
                    "ordering":     p["ordering"],
                    "is_grade_term": p["is_grade_term"],
                },
            )
            if period_new:
                periods_created += 1
            else:
                periods_updated += 1

        # Delete stale periods (re-commit with a different set of codes).
        current_codes = {p["code"] for p in periods}
        MarkingPeriod.objects.filter(term_structure=ts).exclude(code__in=current_codes).delete()

    # Audit (non-fatal).
    try:
        from audit.models import AuditLog  # noqa: PLC0415
        AuditLog.objects.create(
            school=school,
            actor=request.user,
            action="term_structure.commit",
            metadata={
                "term_structure_id": str(ts.id),
                "structure_type":    ts.structure_type,
                "created":           ts_created,
                "periods":           len(periods),
            },
        )
    except Exception as exc:
        logger.warning("term_structure.commit audit log skipped: %s", exc)

    result = {
        "term_structure_id":  str(ts.id),
        "structure_type":     ts.structure_type,
        "is_active":          ts.is_active,
        "academic_year_id":   str(ay.id),
        "academic_year_name": ay.name,
        "created":            ts_created,
        "periods_created":    periods_created,
        "periods_updated":    periods_updated,
        "period_codes":       sorted(current_codes),
        "message": (
            f"Term structure '{ts.structure_type}' {'created' if ts_created else 'updated'} "
            f"with {len(periods)} marking periods."
        ),
    }

    session.commit_result = result
    session.status = TermStructureWizardSession.STATUS_COMMITTED
    session.save()

    return Response(result)


# ---------------------------------------------------------------------------
# 5. Verify
# ---------------------------------------------------------------------------

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != TermStructureWizardSession.STATUS_COMMITTED:
        return Response(
            {
                "error": (
                    f"Session must be committed before verification "
                    f"(current: {session.status})."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    ay = session.academic_year
    try:
        ts = TermStructure.objects.get(school_id=school_id, academic_year=ay)
    except TermStructure.DoesNotExist:
        return Response(
            {"error": "TermStructure not found in DB after commit — something went wrong."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    period_count = MarkingPeriod.objects.filter(term_structure=ts).count()
    period_codes = list(
        MarkingPeriod.objects.filter(term_structure=ts).order_by("ordering").values_list("code", flat=True)
    )

    session.status = TermStructureWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "term_structure_id": str(ts.id),
        "structure_type":    ts.structure_type,
        "is_active":         ts.is_active,
        "academic_year_id":  str(ay.id),
        "period_count":      period_count,
        "period_codes":      period_codes,
        "status":            session.status,
    })
