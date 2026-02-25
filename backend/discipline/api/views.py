from __future__ import annotations

from django.db.models import Count
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import School
from discipline.models import DisciplineIncident, DisciplineAction
from discipline.api.serializers import (
    DisciplineIncidentListSerializer,
    DisciplineIncidentDetailSerializer,
    DisciplineActionCreateSerializer,
)
from households.scoping import get_request_school_id


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
    return School.objects.get(id=sid)

class DisciplineIncidentsListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)

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

        data = DisciplineIncidentListSerializer(qs[:500], many=True).data
        return Response(data)

    def post(self, request):
        school = _get_school(request)

        # Minimal create: accept student UUID + basic fields
        payload = request.data or {}
        required = ["student", "occurred_at", "summary"]
        for r in required:
            if r not in payload:
                return Response({"detail": f"Missing field: {r}"}, status=400)

        from core.models import Student
        try:
            student = Student.objects.get(id=payload["student"], school=school)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found in school"}, status=404)

        incident = DisciplineIncident.objects.create(
            school=school,
            student=student,
            reported_by=request.user,
            assigned_to=None,
            occurred_at=payload["occurred_at"],
            location=payload.get("location",""),
            category=payload.get("category","other"),
            severity=payload.get("severity","minor"),
            status=payload.get("status","open"),
            summary=payload["summary"],
            details=payload.get("details",""),
        )
        DisciplineAction.objects.create(
            incident=incident,
            actor=request.user,
            action_type="created",
            note="Incident created"
        )
        return Response(DisciplineIncidentDetailSerializer(incident).data, status=201)

class DisciplineIncidentDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, incident_id):
        school = _get_school(request)

        try:
            inc = DisciplineIncident.objects.get(id=incident_id, school=school)
        except DisciplineIncident.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        return Response(DisciplineIncidentDetailSerializer(inc).data)

class DisciplineIncidentActions(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, incident_id):
        school = _get_school(request)

        try:
            inc = DisciplineIncident.objects.get(id=incident_id, school=school)
        except DisciplineIncident.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        ser = DisciplineActionCreateSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        action_type = d["action_type"]
        note = d.get("note","")

        if action_type == "assigned":
            assigned_to = d.get("assigned_to")
            if not assigned_to:
                return Response({"detail":"assigned_to required"}, status=400)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                u = User.objects.get(id=assigned_to)
            except User.DoesNotExist:
                return Response({"detail":"assigned_to user not found"}, status=404)
            inc.assigned_to = u
            inc.save(update_fields=["assigned_to"])

        if action_type == "parent_notified":
            inc.parent_notified = True
            inc.parent_notified_at = timezone.now()
            inc.save(update_fields=["parent_notified","parent_notified_at"])

        if action_type in ("status_changed","closed"):
            new_status = d.get("status") or ("closed" if action_type=="closed" else None)
            if new_status:
                inc.status = new_status
                inc.save(update_fields=["status"])

        DisciplineAction.objects.create(
            incident=inc,
            actor=request.user,
            action_type=action_type,
            note=note
        )

        return Response(DisciplineIncidentDetailSerializer(inc).data, status=200)

class DisciplineMetrics(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)

        qs = DisciplineIncident.objects.filter(school=school)
        by_status = list(qs.values("status").annotate(count=Count("id")).order_by("status"))
        by_severity = list(qs.values("severity").annotate(count=Count("id")).order_by("severity"))
        by_category = list(qs.values("category").annotate(count=Count("id")).order_by("category"))

        return Response({
            "total": qs.count(),
            "by_status": by_status,
            "by_severity": by_severity,
            "by_category": by_category,
        })
