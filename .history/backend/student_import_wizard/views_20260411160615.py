"""
student_import_wizard/views.py

Steps:
  POST   /sessions/                             → create_session
  POST   /sessions/<uuid>/configure/            → configure_session  (column map)
  POST   /sessions/<uuid>/preview/              → preview_session    (dry-run rows)
  POST   /sessions/<uuid>/commit/               → commit_session     (write students)
  GET    /sessions/<uuid>/verify/               → verify_session
"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from households.scoping import get_request_school_id

from .models import StudentImportWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


def _get_session(session_id, school_id):
    return get_object_or_404(StudentImportWizardSession, id=session_id, school__id=school_id)


# ---------------------------------------------------------------------------
# Step 1: Create session
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="student_import_create_session",
    tags=["Students"],
    responses={201: OpenApiTypes.OBJECT},
)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = StudentImportWizardSession.objects.create(
        school=school,
        created_by=request.user,
    )
    return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Step 2: Configure (column map)
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="student_import_configure_session",
    tags=["Students"],
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == StudentImportWizardSession.STATUS_COMMITTED:
        return Response({"error": "Session already committed"}, status=status.HTTP_400_BAD_REQUEST)

    column_map = request.data.get("column_map")
    if not isinstance(column_map, dict) or not column_map:
        return Response({"error": "column_map must be a non-empty object"}, status=status.HTTP_400_BAD_REQUEST)

    staged_rows = request.data.get("staged_rows")
    if not isinstance(staged_rows, list) or len(staged_rows) == 0:
        return Response({"error": "staged_rows must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    session.column_map = column_map
    session.staged_rows = staged_rows
    session.status = StudentImportWizardSession.STATUS_CONFIGURED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "row_count": len(staged_rows),
    })


# ---------------------------------------------------------------------------
# Step 3: Preview (dry-run)
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="student_import_preview_session",
    tags=["Students"],
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def preview_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status != StudentImportWizardSession.STATUS_CONFIGURED:
        return Response(
            {"error": f"Session must be in 'configured' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Dry-run validation: check required mapped fields exist
    required_fields = {"first_name", "last_name", "grade_level"}
    mapped_targets = set(session.column_map.values())
    missing = required_fields - mapped_targets
    if missing:
        return Response(
            {"error": f"column_map missing required targets: {sorted(missing)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid = 0
    errors = []
    for i, row in enumerate(session.staged_rows):
        row_errors = []
        for csv_col, field in session.column_map.items():
            if field in required_fields and not str(row.get(csv_col, "")).strip():
                row_errors.append(f"row {i}: '{csv_col}' ({field}) is blank")
        if row_errors:
            errors.extend(row_errors)
        else:
            valid += 1

    preview_result = {"valid": valid, "errors": errors}
    session.preview_result = preview_result
    session.status = StudentImportWizardSession.STATUS_PREVIEWED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **preview_result,
    })


# ---------------------------------------------------------------------------
# Step 4: Commit
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="student_import_commit_session",
    tags=["Students"],
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == StudentImportWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})

    if session.status != StudentImportWizardSession.STATUS_PREVIEWED:
        return Response(
            {"error": f"Session must be in 'previewed' state (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    from academics.models import Student

    created = 0
    updated = 0
    skipped = 0
    errors = []

    with transaction.atomic():
        for i, row in enumerate(session.staged_rows):
            try:
                mapped = {field: str(row.get(csv_col, "")).strip()
                          for csv_col, field in session.column_map.items()}
                first_name = mapped.get("first_name", "")
                last_name = mapped.get("last_name", "")
                grade_level = mapped.get("grade_level", "")
                external_id = mapped.get("external_id", "")

                if not first_name or not last_name:
                    skipped += 1
                    continue

                defaults = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "grade_level": grade_level,
                }

                if external_id:
                    obj, was_created = Student.objects.update_or_create(
                        school_id=school_id,
                        external_id=external_id,
                        defaults=defaults,
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1
                else:
                    Student.objects.create(school_id=school_id, **defaults)
                    created += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"row {i}: {exc}")

        result = {"created": created, "updated": updated, "skipped": skipped, "errors": errors}
        session.commit_result = result
        session.status = StudentImportWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"session_id": str(session.id), "status": session.status, **result})


# ---------------------------------------------------------------------------
# Step 5: Verify
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="student_import_verify_session",
    tags=["Students"],
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        StudentImportWizardSession.STATUS_COMMITTED,
        StudentImportWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Session must be committed before verify (current: {session.status})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if session.status == StudentImportWizardSession.STATUS_COMMITTED:
        session.status = StudentImportWizardSession.STATUS_VERIFIED
        session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **(session.commit_result or {}),
    })
