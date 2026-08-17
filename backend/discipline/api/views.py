from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import School
from core.permissions import user_has_permission
from discipline.models import DisciplineIncident, DisciplineAction
from discipline.api.serializers import (
    DisciplineIncidentListSerializer,
    DisciplineIncidentDetailSerializer,
    DisciplineActionCreateSerializer,
)
from households.scoping import get_request_school_id

STUDENT_CARE_VIEW = "student-care.view"
STUDENT_CARE_VIEW_RESTRICTED = "student-care.view_restricted"
STUDENT_CARE_CREATE = "student-care.create"
STUDENT_CARE_EDIT = "student-care.edit"
STUDENT_CARE_CLOSE = "student-care.close"

VALID_STATUS_TRANSITIONS = {
    "open": {"investigating", "closed"},
    "investigating": {"open", "closed"},
    "closed": set(),
}


def _get_school(request) -> School:
    """
    Canonical tenant resolver for discipline views.

    Delegates to get_request_school_id() which enforces:
      - Missing or invalid X-School-Id header  -> MissingSchoolContext (HTTP 400)
      - Non-staff user with wrong-school header -> NotFound (HTTP 404)
      - Staff users                             -> pass-through (header wins)

    Raises MissingSchoolContext or NotFound; DRF converts them to 400/404
    automatically — callers do not need null checks.
    """
    sid = get_request_school_id(request, required=True)
    return School.objects.get(pk=sid)


def _has_permission(request, school, code):
    return user_has_permission(request.user, code, school=school)


def _permission_denied():
    return Response({"detail": "Permission denied."}, status=403)


def _user_is_valid_assignee(user, school) -> bool:
    """Require an active same-school staff member or non-portal school role."""
    if user is None or not getattr(user, "is_active", False):
        return False

    staff = getattr(user, "staff", None)
    if (
        staff is not None
        and getattr(staff, "school_id", None) == school.pk
        and getattr(staff, "status", None) == "ACTIVE"
    ):
        return True

    return user.roles.filter(school=school).exclude(role_code__in=("PARENT", "STUDENT")).exists()


def _required_action_permission(action_type: str, requested_status: str | None) -> str:
    if action_type == "closed" or (action_type == "status_changed" and requested_status == "closed"):
        return STUDENT_CARE_CLOSE
    return STUDENT_CARE_EDIT


class DisciplineIncidentsListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)
        if not _has_permission(request, school, STUDENT_CARE_VIEW):
            return _permission_denied()

        qs = DisciplineIncident.objects.filter(school=school)

        status_q = request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)

        severity = request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity)

        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)

        include_restricted = _has_permission(request, school, STUDENT_CARE_VIEW_RESTRICTED)
        data = DisciplineIncidentListSerializer(
            qs[:500], many=True, context={"include_restricted": include_restricted}
        ).data
        return Response(data)

    def post(self, request):
        school = _get_school(request)
        if not _has_permission(request, school, STUDENT_CARE_CREATE):
            return _permission_denied()

        payload = request.data or {}
        required = ["student", "occurred_at", "summary"]
        for field_name in required:
            if field_name not in payload:
                return Response({"detail": f"Missing field: {field_name}"}, status=400)

        requested_status = payload.get("status", "open")
        if requested_status != "open":
            return Response({"detail": "New incidents must start with status=open."}, status=400)

        from core.models import Student

        try:
            student = Student.objects.get(pk=payload["student"], school=school)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found in school"}, status=404)

        with transaction.atomic():
            incident = DisciplineIncident.objects.create(
                school=school,
                student=student,
                reported_by=request.user,
                assigned_to=None,
                occurred_at=payload["occurred_at"],
                location=payload.get("location", ""),
                category=payload.get("category", "other"),
                severity=payload.get("severity", "minor"),
                status="open",
                summary=payload["summary"],
                details=payload.get("details", ""),
            )
            DisciplineAction.objects.create(
                incident=incident,
                actor=request.user,
                action_type="created",
                note="Incident created",
            )

        include_restricted = _has_permission(request, school, STUDENT_CARE_VIEW_RESTRICTED)
        return Response(
            DisciplineIncidentDetailSerializer(
                incident, context={"include_restricted": include_restricted}
            ).data,
            status=201,
        )


class DisciplineIncidentDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, incident_id):
        school = _get_school(request)
        if not _has_permission(request, school, STUDENT_CARE_VIEW):
            return _permission_denied()

        try:
            inc = DisciplineIncident.objects.get(pk=incident_id, school=school)
        except DisciplineIncident.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        include_restricted = _has_permission(request, school, STUDENT_CARE_VIEW_RESTRICTED)
        return Response(
            DisciplineIncidentDetailSerializer(
                inc, context={"include_restricted": include_restricted}
            ).data
        )


class DisciplineIncidentActions(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, incident_id):
        school = _get_school(request)

        ser = DisciplineActionCreateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        action_type = data["action_type"]
        requested_status = data.get("status")
        note = data.get("note", "")

        if action_type == "status_changed" and requested_status is None:
            return Response({"detail": "status required for status_changed"}, status=400)
        if action_type == "closed" and requested_status not in (None, "closed"):
            return Response({"detail": "closed action may only set status=closed"}, status=400)

        permission_code = _required_action_permission(action_type, requested_status)
        if not _has_permission(request, school, permission_code):
            return _permission_denied()

        with transaction.atomic():
            try:
                inc = DisciplineIncident.objects.select_for_update().get(
                    pk=incident_id, school=school
                )
            except DisciplineIncident.DoesNotExist:
                return Response({"detail": "Not found"}, status=404)

            if action_type == "assigned":
                assigned_to = data.get("assigned_to")
                if not assigned_to:
                    return Response({"detail": "assigned_to required"}, status=400)

                User = get_user_model()
                assignee = User.objects.filter(pk=assigned_to, is_active=True).first()
                if not _user_is_valid_assignee(assignee, school):
                    return Response({"detail": "assigned_to user not found"}, status=404)

                inc.assigned_to = assignee
                inc.save(update_fields=["assigned_to"])

            if action_type == "parent_notified":
                inc.parent_notified = True
                inc.parent_notified_at = timezone.now()
                inc.save(update_fields=["parent_notified", "parent_notified_at"])

            if action_type in ("status_changed", "closed"):
                new_status = requested_status or "closed"
                allowed = VALID_STATUS_TRANSITIONS.get(inc.status, set())
                if new_status not in allowed:
                    return Response(
                        {"detail": f"Invalid status transition: {inc.status} -> {new_status}"},
                        status=400,
                    )
                inc.status = new_status
                inc.save(update_fields=["status"])

            DisciplineAction.objects.create(
                incident=inc,
                actor=request.user,
                action_type=action_type,
                note=note,
            )

        include_restricted = _has_permission(request, school, STUDENT_CARE_VIEW_RESTRICTED)
        return Response(
            DisciplineIncidentDetailSerializer(
                inc, context={"include_restricted": include_restricted}
            ).data,
            status=200,
        )


class DisciplineMetrics(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)
        if not (
            _has_permission(request, school, STUDENT_CARE_VIEW)
            and _has_permission(request, school, STUDENT_CARE_VIEW_RESTRICTED)
        ):
            return _permission_denied()

        qs = DisciplineIncident.objects.filter(school=school)
        by_status = list(qs.values("status").annotate(count=Count("id")).order_by("status"))
        by_severity = list(qs.values("severity").annotate(count=Count("id")).order_by("severity"))
        by_category = list(qs.values("category").annotate(count=Count("id")).order_by("category"))

        return Response(
            {
                "total": qs.count(),
                "by_status": by_status,
                "by_severity": by_severity,
                "by_category": by_category,
            }
        )
