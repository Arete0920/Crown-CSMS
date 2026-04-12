"""
reenrollment/views.py

6 REST endpoints for the re-enrollment wizard:

  POST /api/v1/reenrollment/sessions/                          → create_session
  POST /api/v1/reenrollment/sessions/<id>/configure/           → configure_session
  GET  /api/v1/reenrollment/sessions/<id>/candidates/          → list_candidates
  POST /api/v1/reenrollment/sessions/<id>/select/              → select_students
  POST /api/v1/reenrollment/sessions/<id>/commit/              → commit_session
  GET  /api/v1/reenrollment/sessions/<id>/verify/              → verify_session

All endpoints require JWT or session authentication.
All endpoints are tenant-scoped via X-School-Id → get_request_school_id().
Tenant isolation: every ReenrollmentSession lookup uses school=school on the FK.
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from billing.models import BillingRun, Invoice, InvoiceLine
from households.models import Household, Student as HouseholdStudent
from households.scoping import get_request_school_id

from .models import ReenrollmentSession

# ---------------------------------------------------------------------------
# Auth stack — mirrors onboarding wizard exactly
# ---------------------------------------------------------------------------

AUTH_CLASSES = [JWTAuthentication, SessionAuthentication]
PERM_CLASSES = [IsAuthenticated]


class ReenrollmentErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ReenrollmentSessionResponseSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    status = serializers.CharField()


class ReenrollmentConfigureRequestSerializer(serializers.Serializer):
    target_year_label = serializers.CharField()
    enrollment_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class ReenrollmentConfigureResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    target_year_label = serializers.CharField()
    enrollment_fee = serializers.CharField()
    candidates_total = serializers.IntegerField()


class ReenrollmentCandidateSerializer(serializers.Serializer):
    id = serializers.CharField()
    first_name = serializers.CharField(allow_blank=True, required=False)
    last_name = serializers.CharField(allow_blank=True, required=False)
    grade_level = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    household_id = serializers.CharField()
    excluded = serializers.BooleanField()


class ReenrollmentCandidatesResponseSerializer(serializers.Serializer):
    candidates = ReenrollmentCandidateSerializer(many=True)
    total = serializers.IntegerField()
    selected = serializers.IntegerField()
    excluded = serializers.IntegerField()


class ReenrollmentSelectRequestSerializer(serializers.Serializer):
    excluded_ids = serializers.ListField(child=serializers.CharField(), required=False)


class ReenrollmentSelectResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    selected_count = serializers.IntegerField()
    excluded_count = serializers.IntegerField()


class ReenrollmentCommitRequestSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()


class ReenrollmentCommitResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    already_committed = serializers.BooleanField(required=False)
    billing_run_id = serializers.CharField(required=False)
    students_reenrolled = serializers.IntegerField(required=False)
    households_invoiced = serializers.IntegerField(required=False)
    invoices_created = serializers.IntegerField(required=False)
    total_amount = serializers.CharField(required=False)


class ReenrollmentVerifyResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    status = serializers.CharField()
    target_year_label = serializers.CharField()
    enrollment_fee = serializers.CharField()
    students_reenrolled = serializers.IntegerField(required=False, allow_null=True)
    households_invoiced = serializers.IntegerField(required=False, allow_null=True)
    total_amount = serializers.CharField(required=False, allow_null=True)
    billing_run_id = serializers.CharField(required=False, allow_null=True)


# ---------------------------------------------------------------------------
# Tenant-scoped session helper
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    """Return ReenrollmentSession scoped to school; 404 if not found or wrong school."""
    return get_object_or_404(ReenrollmentSession, id=session_id, school__id=school_id)


# ---------------------------------------------------------------------------
# 1. Create session
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="reenrollment_create_session",
    tags=["Enrollment"],
    responses={201: ReenrollmentSessionResponseSerializer},
)
@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def create_session(request):
    """POST /api/v1/reenrollment/sessions/  — create a new ReenrollmentSession."""
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)

    session = ReenrollmentSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response({
        "session_id": str(session.id),
        "status": session.status,
    }, status=201)


# ---------------------------------------------------------------------------
# 2. Configure session
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="reenrollment_configure_session",
    tags=["Enrollment"],
    request=ReenrollmentConfigureRequestSerializer,
    responses={200: ReenrollmentConfigureResponseSerializer, 400: ReenrollmentErrorSerializer},
)
@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def configure_session(request, session_id):
    """
    POST /api/v1/reenrollment/sessions/<id>/configure/
    Body: { "target_year_label": "2026-2027", "enrollment_fee": "500.00" }
    Sets year + fee, snapshots ACTIVE students, advances status → configured.
    Idempotent: calling again with new settings re-snapshots and overwrites.
    """
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    target_year_label = (request.data.get("target_year_label") or "").strip()
    if not target_year_label:
        return Response({"detail": "target_year_label is required."}, status=400)
    if len(target_year_label) > 24:
        return Response({"detail": "target_year_label must be 24 characters or fewer."}, status=400)

    raw_fee = request.data.get("enrollment_fee", "0")
    try:
        enrollment_fee = Decimal(str(raw_fee))
    except (InvalidOperation, TypeError):
        return Response({"detail": "enrollment_fee must be a valid decimal number."}, status=400)
    if enrollment_fee < Decimal("0"):
        return Response({"detail": "enrollment_fee cannot be negative."}, status=400)

    # Snapshot active students for this school
    students_qs = HouseholdStudent.objects.filter(
        school_id=school_id,
        is_active=True,
    ).order_by("last_name", "first_name")

    snapshot = [
        {
            "id": str(s.id),
            "first_name": s.first_name,
            "last_name": s.last_name,
            "grade_level": s.grade_level,
            "household_id": str(s.household_id),
        }
        for s in students_qs
    ]

    session.target_year_label = target_year_label
    session.enrollment_fee = enrollment_fee
    session.candidates_snapshot = snapshot
    session.excluded_ids = []  # reset exclusions when re-configuring
    session.status = ReenrollmentSession.STATUS_CONFIGURED
    session.save()

    return Response({
        "ok": True,
        "target_year_label": session.target_year_label,
        "enrollment_fee": str(session.enrollment_fee),
        "candidates_total": len(snapshot),
    })


# ---------------------------------------------------------------------------
# 3. List candidates
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="reenrollment_list_candidates",
    tags=["Enrollment"],
    responses={200: ReenrollmentCandidatesResponseSerializer, 400: ReenrollmentErrorSerializer},
)
@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def list_candidates(request, session_id):
    """
    GET /api/v1/reenrollment/sessions/<id>/candidates/
    Returns the snapshotted candidate list with excluded flag per student.
    """
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == ReenrollmentSession.STATUS_DRAFT:
        return Response({"detail": "Session must be configured before listing candidates."}, status=400)

    snapshot = session.candidates_snapshot or []
    excluded_set = set(session.excluded_ids or [])

    candidates = [
        {**s, "excluded": s["id"] in excluded_set}
        for s in snapshot
    ]

    return Response({
        "candidates": candidates,
        "total": len(candidates),
        "selected": sum(1 for c in candidates if not c["excluded"]),
        "excluded": len(excluded_set),
    })


# ---------------------------------------------------------------------------
# 4. Select students (update exclusion list)
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="reenrollment_select_students",
    tags=["Enrollment"],
    request=ReenrollmentSelectRequestSerializer,
    responses={200: ReenrollmentSelectResponseSerializer, 400: ReenrollmentErrorSerializer},
)
@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def select_students(request, session_id):
    """
    POST /api/v1/reenrollment/sessions/<id>/select/
    Body: { "excluded_ids": ["uuid1", "uuid2", ...] }
    Saves the director's exclusion list. Idempotent.
    """
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        ReenrollmentSession.STATUS_CONFIGURED,
    ):
        return Response(
            {"detail": "Session must be in 'configured' status to update selection."},
            status=400,
        )

    raw_excluded = request.data.get("excluded_ids", [])
    if not isinstance(raw_excluded, list):
        return Response({"detail": "excluded_ids must be a list of UUID strings."}, status=400)

    # Validate all provided IDs exist in the snapshot
    snapshot_ids = {s["id"] for s in (session.candidates_snapshot or [])}
    invalid = [eid for eid in raw_excluded if eid not in snapshot_ids]
    if invalid:
        return Response(
            {"detail": f"Unknown student IDs: {invalid[:5]}"},
            status=400,
        )

    session.excluded_ids = list(raw_excluded)
    session.save(update_fields=["excluded_ids", "updated_at"])

    total = len(snapshot_ids)
    excluded = len(session.excluded_ids)
    return Response({
        "ok": True,
        "selected_count": total - excluded,
        "excluded_count": excluded,
    })


# ---------------------------------------------------------------------------
# 5. Commit
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="reenrollment_commit_session",
    tags=["Enrollment"],
    request=ReenrollmentCommitRequestSerializer,
    responses={200: ReenrollmentCommitResponseSerializer, 400: ReenrollmentErrorSerializer},
)
@api_view(["POST"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def commit_session(request, session_id):
    """
    POST /api/v1/reenrollment/sessions/<id>/commit/
    Body: { "confirm": true }
    Creates BillingRun + Invoice (per household) + InvoiceLine (per student).
    Idempotent: second call on status=committed returns existing result.
    """
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    # Idempotency guard — must check BEFORE confirm flag
    if session.status == ReenrollmentSession.STATUS_COMMITTED:
        return Response({"ok": True, "already_committed": True, **session.commit_result})

    if session.status != ReenrollmentSession.STATUS_CONFIGURED:
        return Response(
            {"detail": "Session must be configured before committing."},
            status=400,
        )

    if not request.data.get("confirm"):
        return Response({"detail": "Set confirm=true to execute the re-enrollment commit."}, status=400)

    excluded_set = set(session.excluded_ids or [])
    snapshot = session.candidates_snapshot or []

    # Determine selected students from snapshot (re-query DB for FK integrity)
    selected_ids = [s["id"] for s in snapshot if s["id"] not in excluded_set]

    if not selected_ids:
        return Response({"detail": "No students selected for re-enrollment."}, status=400)

    # Fetch actual Student objects (needed for FK in InvoiceLine)
    students = list(
        HouseholdStudent.objects.filter(
            school_id=school_id,
            is_active=True,
            id__in=selected_ids,
        ).select_related("household")
    )

    if not students:
        return Response({"detail": "No active students found matching selection."}, status=400)

    enrollment_fee = session.enrollment_fee

    # Group students by household
    by_household: dict = {}
    for student in students:
        hid = student.household_id
        if hid not in by_household:
            by_household[hid] = {"household": student.household, "students": []}
        by_household[hid]["students"].append(student)

    with transaction.atomic():
        # Create one BillingRun for this re-enrollment cycle
        billing_run = BillingRun.objects.create(
            school_id=school_id,
            term=session.target_year_label,
            run_type="ENROLLMENT_FEE",
            description=f"Re-enrollment {session.target_year_label}",
            amount_per_student=enrollment_fee,
        )

        invoices_created = 0
        total_amount = Decimal("0.00")

        for hid, group in by_household.items():
            household = group["household"]
            household_students = group["students"]
            household_total = enrollment_fee * len(household_students)

            invoice = Invoice.objects.create(
                school_id=school_id,
                billing_run=billing_run,
                household=household,
                total_amount=household_total,
            )
            invoices_created += 1
            total_amount += household_total

            for student in household_students:
                InvoiceLine.objects.create(
                    school_id=school_id,
                    invoice=invoice,
                    student=student,
                    description=f"Enrollment Fee {session.target_year_label}",
                    amount=enrollment_fee,
                )

        commit_result = {
            "billing_run_id": str(billing_run.id),
            "students_reenrolled": len(students),
            "households_invoiced": len(by_household),
            "invoices_created": invoices_created,
            "total_amount": str(total_amount),
        }

        session.commit_result = commit_result
        session.status = ReenrollmentSession.STATUS_COMMITTED
        session.save(update_fields=["commit_result", "status", "updated_at"])

    return Response({"ok": True, **commit_result})


# ---------------------------------------------------------------------------
# 6. Verify
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="reenrollment_verify_session",
    tags=["Enrollment"],
    responses={200: ReenrollmentVerifyResponseSerializer, 400: ReenrollmentErrorSerializer},
)
@api_view(["GET"])
@authentication_classes(AUTH_CLASSES)
@permission_classes(PERM_CLASSES)
def verify_session(request, session_id):
    """
    GET /api/v1/reenrollment/sessions/<id>/verify/
    Advances status committed→verified on the first call.
    Subsequent calls return the same result without mutating the session.
    """
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        ReenrollmentSession.STATUS_COMMITTED,
        ReenrollmentSession.STATUS_VERIFIED,
    ):
        return Response(
            {"detail": "Session must be committed before verifying."},
            status=400,
        )

    # Transition once: committed → verified
    if session.status == ReenrollmentSession.STATUS_COMMITTED:
        session.status = ReenrollmentSession.STATUS_VERIFIED
        session.save(update_fields=["status", "updated_at"])

    return Response({
        "ok": True,
        "status": session.status,
        "target_year_label": session.target_year_label,
        "enrollment_fee": str(session.enrollment_fee),
        "students_reenrolled": session.commit_result.get("students_reenrolled"),
        "households_invoiced": session.commit_result.get("households_invoiced"),
        "total_amount": session.commit_result.get("total_amount"),
        "billing_run_id": session.commit_result.get("billing_run_id"),
    })
