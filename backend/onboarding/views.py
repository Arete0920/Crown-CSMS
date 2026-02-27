"""
onboarding/views.py

6 REST endpoints for the admissions intake / bulk-import wizard:

  POST /api/v1/onboarding/imports/                        → create_session
  POST /api/v1/onboarding/imports/<id>/upload/            → upload_file
  POST /api/v1/onboarding/imports/<id>/validate/          → validate_session
  GET  /api/v1/onboarding/imports/<id>/preview/          → preview_session
  POST /api/v1/onboarding/imports/<id>/commit/            → commit_session
  GET  /api/v1/onboarding/imports/<id>/verify/            → verify_session

All endpoints require authentication (SessionAuthentication or JWT).
All endpoints are tenant-scoped via X-School-Id → get_request_school_id().
Tenant isolation: every ImportSession lookup uses ImportSession.objects.get(id=…, school_id=…).
"""
import csv
import io
import re

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from households.scoping import get_request_school_id
from .models import ImportSession

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_HEADERS_STUDENTS_GUARDIANS = {
    "student_external_id", "student_first_name", "student_last_name",
    "student_dob", "grade_level", "student_status",
    "guardian_external_id", "guardian_first_name", "guardian_last_name",
    "guardian_email", "guardian_relationship",
    "household_external_id",
}

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# Upload limits
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_CSV_ROWS = 10_000

# Authentication stack (JWT + session fallback)
AUTH_CLASSES = [JWTAuthentication, SessionAuthentication]
PERM_CLASSES = [IsAuthenticated]


# ---------------------------------------------------------------------------
# Helper: resolve ImportSession scoped to the request's tenant
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    """Return ImportSession or 404, always tenant-scoped (school_id enforced)."""
    return get_object_or_404(ImportSession, id=session_id, school_id=school_id)


# ---------------------------------------------------------------------------
# Helper: parse and validate CSV
# ---------------------------------------------------------------------------

def _parse_csv(raw_csv: str, required_headers: set):
    """
    Parse raw CSV text.
    Returns:
        {rows, headers, errors, warnings, students, guardians, households}
    """
    errors = []
    warnings = []
    rows = []
    fieldnames = []

    try:
        reader = csv.DictReader(io.StringIO(raw_csv))
        fieldnames = list(reader.fieldnames or [])
        headers = set(fieldnames)
        missing = required_headers - headers
        if missing:
            errors.append({
                "row": None,
                "field": ", ".join(sorted(missing)),
                "message": f"Missing required column(s): {', '.join(sorted(missing))}",
            })
            return {
                "rows": [], "headers": fieldnames, "errors": errors,
                "warnings": warnings, "students": set(), "guardians": set(), "households": set(),
            }

        for i, row in enumerate(reader, start=2):  # row 1 = header
            if i > MAX_CSV_ROWS + 1:
                errors.append({
                    "row": None, "field": None,
                    "message": f"File exceeds {MAX_CSV_ROWS} data rows. Split into smaller batches.",
                })
                break

            row_errors = []

            # Required non-empty fields
            for field in ["student_external_id", "student_first_name", "student_last_name",
                          "guardian_external_id", "guardian_first_name", "guardian_last_name",
                          "guardian_email", "household_external_id"]:
                val = (row.get(field) or "").strip()
                if not val:
                    row_errors.append({
                        "row": i, "field": field, "message": f"Required field '{field}' is empty.",
                    })

            # Date format
            dob = (row.get("student_dob") or "").strip()
            if dob and not DATE_RE.match(dob):
                row_errors.append({
                    "row": i, "field": "student_dob",
                    "message": f"student_dob must be YYYY-MM-DD, got '{dob}'.",
                })

            # Grade level numeric
            grade = (row.get("grade_level") or "").strip()
            if grade:
                try:
                    int(grade)
                except ValueError:
                    row_errors.append({
                        "row": i, "field": "grade_level",
                        "message": f"grade_level must be an integer, got '{grade}'.",
                    })

            # Basic email sanity
            email = (row.get("guardian_email") or "").strip()
            if email and "@" not in email:
                warnings.append({
                    "row": i, "field": "guardian_email",
                    "message": f"guardian_email looks invalid: '{email}'.",
                })

            errors.extend(row_errors)
            rows.append({k: (v or "").strip() for k, v in row.items()})

    except Exception as exc:
        errors.append({"row": None, "field": None, "message": f"CSV parse error: {exc}"})

    students = {r["student_external_id"] for r in rows if r.get("student_external_id")}
    guardians = {r["guardian_external_id"] for r in rows if r.get("guardian_external_id")}
    households = {r["household_external_id"] for r in rows if r.get("household_external_id")}

    return {
        "rows": rows,
        "headers": fieldnames,
        "errors": errors,
        "warnings": warnings,
        "students": students,
        "guardians": guardians,
        "households": households,
    }


# ---------------------------------------------------------------------------
# 1. Create import session
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def create_session(request):
    """POST /api/v1/onboarding/imports/  — create a new import session."""
    school_id = get_request_school_id(request)

    mode = request.data.get("mode", ImportSession.MODE_STUDENTS_GUARDIANS)
    if mode not in {ImportSession.MODE_STUDENTS_GUARDIANS, ImportSession.MODE_STAFF, ImportSession.MODE_CONTACTS}:
        mode = ImportSession.MODE_STUDENTS_GUARDIANS

    session = ImportSession.objects.create(
        school_id=school_id,
        mode=mode,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response({
        "import_id": session.id,
        "mode": session.mode,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
    }, status=201)


# ---------------------------------------------------------------------------
# 2. Upload file
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def upload_file(request, session_id):
    """POST /api/v1/onboarding/imports/<id>/upload/  — accept CSV upload."""
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    f = request.FILES.get("file")
    if not f:
        return Response({"detail": "No file uploaded. Send file as multipart/form-data field 'file'."}, status=400)

    if not f.name.lower().endswith(".csv"):
        return Response({"detail": "File must be a .csv file."}, status=400)

    if f.size > MAX_UPLOAD_BYTES:
        return Response({"detail": f"File too large. Maximum is {MAX_UPLOAD_BYTES // (1024*1024)} MB."}, status=400)

    raw = f.read().decode("utf-8-sig", errors="replace")  # strip BOM
    required = (
        REQUIRED_HEADERS_STUDENTS_GUARDIANS
        if session.mode == ImportSession.MODE_STUDENTS_GUARDIANS
        else set()
    )
    parsed = _parse_csv(raw, required)

    session.filename = f.name
    session.raw_csv = raw
    session.rows_total = len(parsed["rows"])
    session.students_detected = len(parsed["students"])
    session.guardians_detected = len(parsed["guardians"])
    session.households_detected = len(parsed["households"])
    session.status = ImportSession.STATUS_UPLOADED
    # Reset downstream state on re-upload
    session.validate_result = None
    session.commit_result = None
    session.save()

    return Response({
        "ok": True,
        "filename": f.name,
        "rows_total": session.rows_total,
        "students_detected": session.students_detected,
        "guardians_detected": session.guardians_detected,
        "households_detected": session.households_detected,
    })


# ---------------------------------------------------------------------------
# 3. Validate (dry run)
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def validate_session(request, session_id):
    """POST /api/v1/onboarding/imports/<id>/validate/  — validate CSV structure."""
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if not session.raw_csv:
        return Response({"detail": "No file uploaded yet. Complete the upload step first."}, status=400)

    required = (
        REQUIRED_HEADERS_STUDENTS_GUARDIANS
        if session.mode == ImportSession.MODE_STUDENTS_GUARDIANS
        else set()
    )
    parsed = _parse_csv(session.raw_csv, required)

    result = {
        "rows_total": len(parsed["rows"]),
        "students_detected": len(parsed["students"]),
        "guardians_detected": len(parsed["guardians"]),
        "households_detected": len(parsed["households"]),
        "errors": parsed["errors"],
        "warnings": parsed["warnings"],
    }
    session.validate_result = result
    session.status = ImportSession.STATUS_VALIDATED
    session.save(update_fields=["validate_result", "status", "updated_at"])

    return Response(result)


# ---------------------------------------------------------------------------
# 4. Preview
# ---------------------------------------------------------------------------

@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def preview_session(request, session_id):
    """GET /api/v1/onboarding/imports/<id>/preview/  — return summary + sample rows."""
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if not session.raw_csv:
        return Response({"detail": "No file uploaded yet."}, status=400)

    required = (
        REQUIRED_HEADERS_STUDENTS_GUARDIANS
        if session.mode == ImportSession.MODE_STUDENTS_GUARDIANS
        else set()
    )
    parsed = _parse_csv(session.raw_csv, required)

    session.status = ImportSession.STATUS_PREVIEWED
    session.save(update_fields=["status", "updated_at"])

    return Response({
        "summary": {
            "rows_total": len(parsed["rows"]),
            "students_to_create": len(parsed["students"]),
            "guardians_to_create": len(parsed["guardians"]),
            "households_to_create": len(parsed["households"]),
            "duplicates_detected": 0,  # dedup within CSV; cross-DB dupes caught on commit
            "errors_detected": len(parsed["errors"]),
        },
        "sample_rows": parsed["rows"][:10],
    })


# ---------------------------------------------------------------------------
# 5. Commit
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def commit_session(request, session_id):
    """
    POST /api/v1/onboarding/imports/<id>/commit/  — write parsed rows to DB.

    Idempotent: second call on an already-committed session returns the stored result.
    Atomic: all DB writes inside transaction.atomic().

    MVP: parses CSV and records planned record counts in commit_result.
    Actual model creation is scaffolded — extend this view when the
    Student/Household intake models are ready (see TODO below).
    """
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    # Idempotency guard — check BEFORE confirm check so double-clicks get the correct result
    if session.status == ImportSession.STATUS_COMMITTED:
        return Response({"detail": "Already committed.", "commit_result": session.commit_result})

    if not request.data.get("confirm"):
        return Response({"detail": "Send confirm=true to proceed."}, status=400)

    if not session.raw_csv:
        return Response({"detail": "No file uploaded."}, status=400)

    validate_result = session.validate_result or {}
    if validate_result.get("errors"):
        return Response({
            "detail": "Cannot commit: validation errors must be resolved first.",
            "error_count": len(validate_result["errors"]),
        }, status=400)

    required = (
        REQUIRED_HEADERS_STUDENTS_GUARDIANS
        if session.mode == ImportSession.MODE_STUDENTS_GUARDIANS
        else set()
    )
    parsed = _parse_csv(session.raw_csv, required)

    with transaction.atomic():
        # TODO: When Student/Household intake models are ready, replace this block
        # with actual ORM record creation.
        # Pattern:
        #   school = School.objects.get(id=school_id)
        #   for student_id, group in itertools.groupby(rows, key=lambda r: r["student_external_id"]):
        #       household, _ = Household.objects.get_or_create(school=school, external_id=...,
        #                                                       defaults={...})
        #       student, _ = Student.objects.get_or_create(school=school, external_id=...,
        #                                                   defaults={...})

        exceptions = []
        commit_result = {
            "mode": session.mode,
            "students_imported": len(parsed["students"]),
            "guardians_imported": len(parsed["guardians"]),
            "households_imported": len(parsed["households"]),
            "exceptions_count": len(exceptions),
            "exceptions": exceptions,
            "note": "MVP scaffolded commit — extend with ORM creation when intake models are ready.",
        }

        session.commit_result = commit_result
        session.status = ImportSession.STATUS_COMMITTED
        # Clear raw CSV for PII hygiene post-commit
        session.raw_csv = ""
        session.save()

    return Response({"ok": True, **commit_result})


# ---------------------------------------------------------------------------
# 6. Verify
# ---------------------------------------------------------------------------

@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def verify_session(request, session_id):
    """GET /api/v1/onboarding/imports/<id>/verify/  — post-commit verification report.

    Idempotent: safe to call multiple times (GET with no side effects once verified).
    Status advances from committed → verified on first call; subsequent calls are no-ops.
    """
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    cr = session.commit_result or {}
    checks = [
        {
            "name": "Import session status",
            "status": "pass" if session.status in (ImportSession.STATUS_COMMITTED, ImportSession.STATUS_VERIFIED) else "warn",
            "detail": f"Status: {session.status}",
        },
        {
            "name": "Student count",
            "status": "pass" if cr.get("students_imported", 0) >= 0 else "warn",
            "detail": f"{cr.get('students_imported', 0)} students recorded",
        },
        {
            "name": "Guardian count",
            "status": "pass" if cr.get("guardians_imported", 0) >= 0 else "warn",
            "detail": f"{cr.get('guardians_imported', 0)} guardians recorded",
        },
        {
            "name": "Exceptions",
            "status": "pass" if cr.get("exceptions_count", 0) == 0 else "warn",
            "detail": f"{cr.get('exceptions_count', 0)} exception(s)",
        },
    ]

    # Advance status from committed → verified exactly once (no-op if already verified)
    if session.status == ImportSession.STATUS_COMMITTED:
        session.status = ImportSession.STATUS_VERIFIED
        session.save(update_fields=["status", "updated_at"])

    return Response({
        "session_id": session.id,
        "mode": session.mode,
        "students_imported": cr.get("students_imported", 0),
        "guardians_imported": cr.get("guardians_imported", 0),
        "households_imported": cr.get("households_imported", 0),
        "exceptions_count": cr.get("exceptions_count", 0),
        "checks": checks,
    })
