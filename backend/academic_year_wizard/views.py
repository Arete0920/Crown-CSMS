"""
academic_year_wizard/views.py

5 endpoints for the Academic Year Rollover Wizard (Wizard #15):

  POST /api/v1/academic-year-wizard/sessions/                         → create_session
  POST /api/v1/academic-year-wizard/sessions/<id>/configure/          → configure_session
  POST /api/v1/academic-year-wizard/sessions/<id>/terms/              → set_terms
  POST /api/v1/academic-year-wizard/sessions/<id>/commit/             → commit_session
  GET  /api/v1/academic-year-wizard/sessions/<id>/verify/             → verify_session

Auth: JWT or Session. All endpoints tenant-scoped via X-School-Id.

Commit semantics:
  - AcademicYear: get_or_create by (school, name). Set is_current=True; deactivate all others.
  - Term: update_or_create by (academic_year, code). Sets all fields from terms_config.
"""
import datetime
import logging
import re

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from academics.models import Term
from audit.models import AuditLog
from core.models import AcademicYear, School
from households.scoping import get_request_school_id

from .models import AcademicYearWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]
logger = logging.getLogger(__name__)

_CODE_RE = re.compile(r'^[A-Za-z0-9_-]{1,24}$')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(AcademicYearWizardSession, id=session_id, school_id=school_id)


def _parse_date(value, field_name):
    """Returns (date, error_str) — date is None on error."""
    try:
        return datetime.date.fromisoformat(value), None
    except (ValueError, TypeError):
        return None, f"{field_name} must be a valid date (YYYY-MM-DD)"


def _validate_term(term, idx):
    errors = []
    code = (term.get("code") or "").strip()
    name = (term.get("name") or "").strip()

    if not code:
        errors.append(f"terms[{idx}].code is required")
    elif not _CODE_RE.match(code):
        errors.append(f"terms[{idx}].code must be 1-24 alphanumeric/underscore/hyphen chars")

    if not name:
        errors.append(f"terms[{idx}].name is required")

    for date_field in ("start_date", "end_date"):
        raw = (term.get(date_field) or "").strip()
        if raw:
            _, err = _parse_date(raw, f"terms[{idx}].{date_field}")
            if err:
                errors.append(err)

    ordering = term.get("ordering", 0)
    try:
        if int(ordering) < 0:
            errors.append(f"terms[{idx}].ordering must be a non-negative integer")
    except (TypeError, ValueError):
        errors.append(f"terms[{idx}].ordering must be an integer")

    return errors


# ---------------------------------------------------------------------------
# 1. Create session
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school    = get_object_or_404(School, id=school_id)
    session   = AcademicYearWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# 2. Configure — year name, start_date, end_date
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    year_name  = (request.data.get("year_name")  or "").strip()
    start_raw  = (request.data.get("start_date") or "").strip()
    end_raw    = (request.data.get("end_date")   or "").strip()

    errors = []
    if not year_name:
        errors.append("year_name is required")

    start_date = end_date = None
    if not start_raw:
        errors.append("start_date is required (YYYY-MM-DD)")
    else:
        start_date, err = _parse_date(start_raw, "start_date")
        if err:
            errors.append(err)

    if not end_raw:
        errors.append("end_date is required (YYYY-MM-DD)")
    else:
        end_date, err = _parse_date(end_raw, "end_date")
        if err:
            errors.append(err)

    if start_date and end_date and end_date <= start_date:
        errors.append("end_date must be after start_date")

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.year_name  = year_name
    session.start_date = start_raw
    session.end_date   = end_raw
    session.status     = AcademicYearWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({"session_id": str(session.id), "status": session.status})


# ---------------------------------------------------------------------------
# 3. Terms — define academic terms
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def set_terms(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    if session.status == AcademicYearWizardSession.STATUS_DRAFT:
        return Response(
            {"error": "session must be configured before setting terms"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    terms = request.data.get("terms")
    if not isinstance(terms, list) or len(terms) == 0:
        return Response(
            {"error": "terms must be a non-empty list"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate all terms; collect all errors before returning
    all_errors = []
    for idx, term in enumerate(terms):
        all_errors.extend(_validate_term(term, idx))

    if all_errors:
        return Response({"errors": all_errors}, status=status.HTTP_400_BAD_REQUEST)

    # Batch dedup check on code
    codes = [(t.get("code") or "").strip() for t in terms]
    if len(codes) != len(set(codes)):
        return Response(
            {"error": "duplicate codes in terms — each code must be unique within an academic year"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.terms_config = terms
    session.status       = AcademicYearWizardSession.STATUS_TERMS_SET
    session.save()

    return Response({
        "session_id":  str(session.id),
        "status":      session.status,
        "terms_count": len(terms),
    })


# ---------------------------------------------------------------------------
# 4. Commit — create/update AcademicYear + Term records
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    if session.status != AcademicYearWizardSession.STATUS_TERMS_SET:
        return Response(
            {"error": f"session must be in terms_set state before commit (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        # Serialize concurrent year-flip operations for this school.
        # Evaluating the queryset acquires row-level locks before any reads/writes.
        list(AcademicYear.objects.select_for_update().filter(school_id=school_id))

        academic_year, ay_created = AcademicYear.objects.get_or_create(
            school_id=school_id,
            name=session.year_name,
            defaults={
                "start_date": session.start_date,
                "end_date":   session.end_date,
                "is_current": True,
            },
        )

        # Ensure the committed year is current (covers idempotent re-commit)
        if not academic_year.is_current:
            academic_year.is_current = True
            academic_year.save(update_fields=["is_current"])

        # Single-current enforcement: exactly one current AcademicYear per school
        deactivated_count = (
            AcademicYear.objects
            .filter(school_id=school_id)
            .exclude(pk=academic_year.pk)
            .update(is_current=False)
        )

        terms_created = 0
        terms_updated = 0
        for idx, tc in enumerate(session.terms_config):
            code = (tc.get("code") or "").strip()
            update_defaults = {
                "name": (tc.get("name") or "").strip(),
                "school_year": (tc.get("school_year") or "").strip(),
                "start_date": tc.get("start_date") or None,
                "end_date": tc.get("end_date") or None,
                "ordering": int(tc.get("ordering", idx)),
                "active": True,
            }
            create_defaults = {
                "school_id": school_id,
                **update_defaults,
            }
            _, term_created = Term.objects.update_or_create(
                academic_year=academic_year,
                code=code,
                defaults=update_defaults,
                create_defaults=create_defaults,
            )
            if term_created:
                terms_created += 1
            else:
                terms_updated += 1

        result = {
            "academic_year_id":   str(academic_year.pk),
            "year_name":          academic_year.name,
            "is_current":         academic_year.is_current,
            "created":            ay_created,
            "terms_created":      terms_created,
            "terms_updated":      terms_updated,
            "deactivated_count":  deactivated_count,
            "message": (
                "Academic year '{}' created with {} term(s).".format(
                    academic_year.name, terms_created + terms_updated
                )
                if ay_created
                else "Academic year '{}' already existed; {} term(s) updated, {} new.".format(
                    academic_year.name, terms_updated, terms_created
                )
            ),
        }
        session.commit_result = result
        session.status        = AcademicYearWizardSession.STATUS_COMMITTED
        session.save()

    # Audit log — non-fatal
    try:
        AuditLog.objects.create(
            user_id=getattr(request.user, "id", None),
            action="academic_year.commit",
            model="AcademicYear",
            object_id=result["academic_year_id"],
            metadata={
                "year_name":         result["year_name"],
                "created":           result["created"],
                "terms_created":     result["terms_created"],
                "terms_updated":     result["terms_updated"],
                "deactivated_count": result["deactivated_count"],
                "school_id":         str(school_id),
                "session_id":        str(session.id),
            },
        )
    except Exception as exc:
        logger.warning("academic_year.commit audit log skipped: %s", exc)

    return Response({"session_id": str(session.id), "status": session.status, "result": result})


# ---------------------------------------------------------------------------
# 5. Verify — confirm AcademicYear + term count
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session   = _get_session(session_id, school_id)

    if session.status != AcademicYearWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": "session must be committed before verify"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    year_exists = AcademicYear.objects.filter(
        school_id=school_id, name=session.year_name
    ).exists()

    term_count = 0
    if year_exists:
        ay = AcademicYear.objects.get(school_id=school_id, name=session.year_name)
        term_count = Term.objects.filter(academic_year=ay).count()

    session.status = AcademicYearWizardSession.STATUS_VERIFIED
    session.save(update_fields=["status", "updated_at"])

    return Response({
        "session_id":       str(session.id),
        "status":           session.status,
        "year_exists":      year_exists,
        "year_name":        session.year_name,
        "term_count":       term_count,
    })
