"""
grade_scale_wizard/views.py

Wizard #17 — Grade Scale & Report Card Settings

State machine:
  draft → configured → bands_set → [weights_set →] committed → verified

Endpoints:
  POST   /                         create_session
  POST   /<id>/configure/          configure_session  (draft → configured)
  POST   /<id>/bands/              set_bands          (configured → bands_set)
  POST   /<id>/weights/            set_weights        (bands_set|weights_set → weights_set)
  POST   /<id>/commit/             commit_session     (bands_set|weights_set → committed)
  GET    /<id>/verify/             verify_session     (committed → verified)

Invariants enforced here:
  - Tenant: every lookup filtered on school_id from X-School-Id header
  - AY ownership: AcademicYear.objects.filter(pk=..., school_id=...)
  - Band coverage: [0, 100] with no gaps/overlaps; consecutive max[i]+1 == min[i+1]
  - Weight sum: Σ weight_bp == 10 000
  - Single active: select_for_update + bulk flip to False before get_or_create
  - Idempotent commit: get_or_create scale + update_or_create bands/weights
  - Audit: grade_scale.commit event, non-fatal on failure
"""
import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiTypes, extend_schema
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
    GradeScale,
    GradeScaleBand,
    GradeScaleWizardSession,
    TermWeight,
)

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]
logger = logging.getLogger(__name__)

VALID_SCALE_TYPES = {"LETTER", "PERCENT"}
VALID_ROUNDING    = {"NEAREST", "FLOOR", "CEIL"}
WEIGHT_SUM_BP     = 10_000  # basis points = 100.00 %


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(GradeScaleWizardSession, id=session_id, school_id=school_id)


def _validate_bands(raw_bands):
    """
    Validates and normalises grade bands.

    Rules:
      - At least one band.
      - Each band: label (str), min_pct (int 0-99), max_pct (int 1-100), min < max.
      - No duplicate labels.
      - Sorted by min_pct, bands must cover exactly [0, 100]:
          first.min_pct == 0, last.max_pct == 100,
          consecutive max[i] + 1 == min[i+1]  (integer, inclusive both ends, no gaps)

    Returns (errors: list[str], bands: list[dict] | None)
    """
    errors = []

    if not raw_bands:
        return ["bands: at least one band is required"], None

    seen_labels = {}
    valid = []

    for idx, band in enumerate(raw_bands):
        label = (band.get("label") or "").strip()
        if not label:
            errors.append(f"bands[{idx}].label is required")
            continue
        if label in seen_labels:
            errors.append(f"bands[{idx}].label '{label}' is a duplicate")
            continue
        seen_labels[label] = idx

        try:
            min_pct = int(band["min_pct"])
        except (KeyError, ValueError, TypeError):
            errors.append(f"bands[{idx}].min_pct must be an integer (0–99)")
            continue
        try:
            max_pct = int(band["max_pct"])
        except (KeyError, ValueError, TypeError):
            errors.append(f"bands[{idx}].max_pct must be an integer (1–100)")
            continue

        if min_pct < 0:
            errors.append(f"bands[{idx}].min_pct must be >= 0 (got {min_pct})")
        if max_pct > 100:
            errors.append(f"bands[{idx}].max_pct must be <= 100 (got {max_pct})")
        if min_pct >= max_pct:
            errors.append(f"bands[{idx}].min_pct must be < max_pct ({min_pct} >= {max_pct})")
            continue

        gpa_raw = band.get("gpa_points")
        gpa = None
        if gpa_raw is not None:
            try:
                gpa = float(gpa_raw)
            except (ValueError, TypeError):
                errors.append(f"bands[{idx}].gpa_points must be a number")

        valid.append({
            "label":      label,
            "min_pct":    min_pct,
            "max_pct":    max_pct,
            "gpa_points": gpa,
        })

    if errors:
        return errors, None

    # Sort by min_pct and check full coverage
    valid.sort(key=lambda b: b["min_pct"])
    for i, b in enumerate(valid):
        b["ordering"] = i

    coverage_errors = []
    if valid[0]["min_pct"] != 0:
        coverage_errors.append(
            f"bands: first band must start at 0 for full coverage "
            f"(got min_pct={valid[0]['min_pct']} on '{valid[0]['label']}')"
        )
    if valid[-1]["max_pct"] != 100:
        coverage_errors.append(
            f"bands: last band must end at 100 for full coverage "
            f"(got max_pct={valid[-1]['max_pct']} on '{valid[-1]['label']}')"
        )
    for i in range(len(valid) - 1):
        a, b = valid[i], valid[i + 1]
        if a["max_pct"] + 1 != b["min_pct"]:
            if a["max_pct"] + 1 < b["min_pct"]:
                coverage_errors.append(
                    f"bands: gap between '{a['label']}' (max={a['max_pct']}) "
                    f"and '{b['label']}' (min={b['min_pct']})"
                )
            else:
                coverage_errors.append(
                    f"bands: overlap between '{a['label']}' (max={a['max_pct']}) "
                    f"and '{b['label']}' (min={b['min_pct']})"
                )

    if coverage_errors:
        return coverage_errors, None

    return [], valid


def _validate_weights(raw_weights):
    """
    Validates term weights.

    Rules:
      - At least one weight.
      - Each weight: term_code (str), weight_bp (int 1-10000).
      - No duplicate term_codes.
      - Σ weight_bp == 10 000.

    Returns (errors: list[str], weights: list[dict] | None)
    """
    errors = []

    if not raw_weights:
        return ["weights: at least one weight entry is required"], None

    seen_codes = {}
    valid = []
    total_bp = 0

    for idx, w in enumerate(raw_weights):
        code = (w.get("term_code") or "").strip()
        if not code:
            errors.append(f"weights[{idx}].term_code is required")
            continue
        if code in seen_codes:
            errors.append(f"weights[{idx}].term_code '{code}' is a duplicate")
            continue
        seen_codes[code] = idx

        try:
            bp = int(w["weight_bp"])
        except (KeyError, ValueError, TypeError):
            errors.append(f"weights[{idx}].weight_bp must be a positive integer (basis points)")
            continue

        if bp <= 0:
            errors.append(f"weights[{idx}].weight_bp must be > 0 (got {bp})")
            continue
        if bp > WEIGHT_SUM_BP:
            errors.append(f"weights[{idx}].weight_bp must be <= {WEIGHT_SUM_BP} (got {bp})")
            continue

        total_bp += bp
        valid.append({"term_code": code, "weight_bp": bp})

    if errors:
        return errors, None

    if total_bp != WEIGHT_SUM_BP:
        return (
            [f"weights: basis points must sum to {WEIGHT_SUM_BP} (= 100 %). Got {total_bp}."],
            None,
        )

    return [], valid


# ---------------------------------------------------------------------------
# 1. Create session
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school = get_object_or_404(School, id=school_id)

    session = GradeScaleWizardSession.objects.create(
        school=school,
        created_by=request.user,
        status=GradeScaleWizardSession.STATUS_DRAFT,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# 2. Configure session: academic_year + scale metadata
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    data = request.data

    errors = []

    # Scale name
    name = (data.get("name") or "").strip()
    if not name:
        errors.append("name is required")

    # Scale type
    scale_type = (data.get("scale_type") or "").strip().upper()
    if not scale_type:
        errors.append("scale_type is required (LETTER or PERCENT)")
    elif scale_type not in VALID_SCALE_TYPES:
        errors.append(f"scale_type must be one of {sorted(VALID_SCALE_TYPES)}")

    # Rounding (optional, defaults to NEAREST)
    rounding_raw = (data.get("rounding") or "NEAREST").strip().upper()
    if rounding_raw not in VALID_ROUNDING:
        errors.append(f"rounding must be one of {sorted(VALID_ROUNDING)}")

    # Academic year — must belong to request school
    ay_id = (data.get("academic_year_id") or "").strip()
    if not ay_id:
        errors.append("academic_year_id is required")

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    ay = AcademicYear.objects.filter(pk=ay_id, school_id=school_id).first()
    if ay is None:
        return Response(
            {"error": "academic_year_id not found for this school"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.academic_year = ay
    session.scale_config = {
        "name":       name,
        "scale_type": scale_type,
        "rounding":   rounding_raw,
    }
    session.status = GradeScaleWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({
        "session_id":      str(session.id),
        "status":          session.status,
        "academic_year_id": str(ay.id),
        "name":            name,
        "scale_type":      scale_type,
        "rounding":        rounding_raw,
    })


# ---------------------------------------------------------------------------
# 3. Set bands
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def set_bands(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == GradeScaleWizardSession.STATUS_DRAFT:
        return Response(
            {"error": "Session must be in 'configured' state before setting bands."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw_bands = request.data.get("bands")
    if not isinstance(raw_bands, list):
        return Response(
            {"error": "'bands' must be a list"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    errors, validated = _validate_bands(raw_bands)
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.bands_config = validated
    session.status = GradeScaleWizardSession.STATUS_BANDS_SET
    session.save()

    return Response({
        "session_id":   str(session.id),
        "status":       session.status,
        "bands_count":  len(validated),
    })


# ---------------------------------------------------------------------------
# 4. Set weights (optional; callable from bands_set or weights_set)
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def set_weights(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        GradeScaleWizardSession.STATUS_BANDS_SET,
        GradeScaleWizardSession.STATUS_WEIGHTS_SET,
    ):
        return Response(
            {"error": "Weights can only be set after bands are configured."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw_weights = request.data.get("weights")
    if not isinstance(raw_weights, list):
        return Response(
            {"error": "'weights' must be a list"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    errors, validated = _validate_weights(raw_weights)
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.weights_config = validated
    session.status = GradeScaleWizardSession.STATUS_WEIGHTS_SET
    session.save()

    return Response({
        "session_id":     str(session.id),
        "status":         session.status,
        "weights_count":  len(validated),
        "total_bp":       sum(w["weight_bp"] for w in validated),
    })


# ---------------------------------------------------------------------------
# 5. Commit
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in GradeScaleWizardSession.COMMITTABLE_STATUSES:
        return Response(
            {
                "error": (
                    f"Session must be in bands_set or weights_set state to commit "
                    f"(current: {session.status})."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    school = get_object_or_404(School, id=school_id)
    ay = session.academic_year

    cfg   = session.scale_config
    bands = session.bands_config
    weights = session.weights_config or []

    with transaction.atomic():
        # Lock all existing scales for this school+year to serialize concurrent commits.
        list(GradeScale.objects.select_for_update().filter(school=school, academic_year=ay))

        # Flip all currently-active scales for this year to inactive.
        GradeScale.objects.filter(
            school=school, academic_year=ay, is_active=True
        ).exclude(name=cfg["name"]).update(is_active=False)

        # Upsert the target scale.
        scale, created = GradeScale.objects.get_or_create(
            school=school,
            academic_year=ay,
            name=cfg["name"],
            defaults={
                "scale_type": cfg["scale_type"],
                "rounding":   cfg["rounding"],
                "is_active":  True,
            },
        )
        if not created:
            scale.scale_type = cfg["scale_type"]
            scale.rounding   = cfg["rounding"]
            scale.is_active  = True
            scale.save()

        # Upsert bands keyed by (scale, label).
        bands_created = bands_updated = 0
        for b in bands:
            _, band_new = GradeScaleBand.objects.update_or_create(
                scale=scale,
                label=b["label"],
                defaults={
                    "min_pct":    b["min_pct"],
                    "max_pct":    b["max_pct"],
                    "ordering":   b["ordering"],
                    "gpa_points": b.get("gpa_points"),
                },
            )
            if band_new:
                bands_created += 1
            else:
                bands_updated += 1

        # Remove bands no longer in config (re-commit with different bands).
        current_labels = {b["label"] for b in bands}
        GradeScaleBand.objects.filter(scale=scale).exclude(label__in=current_labels).delete()

        # Upsert weights (if configured).
        weights_created = weights_updated = 0
        for w in weights:
            _, w_new = TermWeight.objects.update_or_create(
                scale=scale,
                term_code=w["term_code"],
                defaults={"weight_bp": w["weight_bp"]},
            )
            if w_new:
                weights_created += 1
            else:
                weights_updated += 1

    # Audit (non-fatal).
    try:
        from audit.models import AuditLog
        AuditLog.objects.create(
            school=school,
            actor=request.user,
            action="grade_scale.commit",
            metadata={
                "scale_id":   str(scale.id),
                "scale_name": scale.name,
                "created":    created,
            },
        )
    except Exception:
        logger.exception("commit_session: grade scale audit log create failed")

    result = {
        "scale_id":        str(scale.id),
        "scale_name":      scale.name,
        "scale_type":      scale.scale_type,
        "rounding":        scale.rounding,
        "academic_year_id": str(ay.id),
        "academic_year_name": ay.name,
        "created":         created,
        "bands_created":   bands_created,
        "bands_updated":   bands_updated,
        "weights_created": weights_created,
        "weights_updated": weights_updated,
        "message": (
            f"Grade scale '{scale.name}' {'created' if created else 'updated'} "
            f"with {len(bands)} bands"
            + (f" and {len(weights)} term weights." if weights else ".")
        ),
    }

    session.commit_result = result
    session.status = GradeScaleWizardSession.STATUS_COMMITTED
    session.save()

    return Response({"session_id": str(session.id), "status": session.status, "result": result})


# ---------------------------------------------------------------------------
# 6. Verify
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != GradeScaleWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": f"Session must be committed before verification (current: {session.status})."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ay = session.academic_year
    scale = GradeScale.objects.filter(
        school_id=school_id,
        academic_year=ay,
        name=session.scale_config["name"],
    ).first()

    scale_exists  = scale is not None
    band_count    = GradeScaleBand.objects.filter(scale=scale).count() if scale else 0
    weight_count  = TermWeight.objects.filter(scale=scale).count() if scale else 0

    session.status = GradeScaleWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "session_id":      str(session.id),
        "status":          session.status,
        "scale_exists":    scale_exists,
        "scale_id":        str(scale.id) if scale else None,
        "band_count":      band_count,
        "weight_count":    weight_count,
        "academic_year_id": str(ay.id) if ay else None,
    })
