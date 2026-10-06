from __future__ import annotations
from django.db.models import Sum
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import School, Student, StudentIdentityLink
from core.permissions import user_has_permission
from servicehours.models import ServiceEntry
from servicehours.api.serializers import ServiceEntrySerializer, ServiceApprovalSerializer


def _get_school_from_request(request):
    school = getattr(request, "school", None)
    if school:
        return school
    school_id = request.headers.get("X-School-Id")
    if not school_id:
        return None
    try:
        return School.objects.get(pk=school_id)
    except School.DoesNotExist:
        return None


def _own_core_student(request, school):
    links = list(
        StudentIdentityLink.objects.select_related("core_student")
        .filter(
            school=school,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            core_student__school=school,
            compatibility_student__school_id=school.id,
            compatibility_student__account=request.user,
        )[:2]
    )
    if len(links) != 1:
        return None
    return links[0].core_student


def _service_scope(request, school):
    if user_has_permission(request.user, "service.manage", school=school):
        return "manage", None
    if user_has_permission(request.user, "service.self", school=school):
        return "self", _own_core_student(request, school)
    return "none", None


def _forbidden():
    return Response({"detail": "Permission denied."}, status=403)


class ServiceEntriesListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)

        scope, own_student = _service_scope(request, school)
        if scope == "none" or (scope == "self" and own_student is None):
            return _forbidden()

        qs = ServiceEntry.objects.filter(school=school)
        if scope == "self":
            qs = qs.filter(student=own_student)

        status_q = request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)

        student_id = request.query_params.get("student")
        if student_id:
            if scope == "self" and str(own_student.id) != str(student_id):
                return _forbidden()
            qs = qs.filter(student_id=student_id)

        return Response(ServiceEntrySerializer(qs[:1000], many=True).data)

    def post(self, request):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)

        scope, own_student = _service_scope(request, school)
        if scope == "none" or (scope == "self" and own_student is None):
            return _forbidden()

        payload = request.data or {}
        if "student" not in payload:
            return Response({"detail":"Missing student"}, status=400)

        try:
            student = Student.objects.get(pk=payload["student"], school=school)
        except Student.DoesNotExist:
            return Response({"detail":"Student not found in school"}, status=404)

        if scope == "self" and student.id != own_student.id:
            return _forbidden()

        entry = ServiceEntry.objects.create(
            school=school,
            student=student,
            date=payload.get("date"),
            hours=payload.get("hours", 1.0),
            category=payload.get("category","Community Service"),
            organization=payload.get("organization","Local Partner"),
            supervisor_name=payload.get("supervisor_name",""),
            supervisor_contact=payload.get("supervisor_contact",""),
            notes=payload.get("notes",""),
            status="pending",
        )
        return Response(ServiceEntrySerializer(entry).data, status=201)


class ServiceStudentSummary(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)

        scope, own_student = _service_scope(request, school)
        if scope == "none" or (scope == "self" and own_student is None):
            return _forbidden()
        if scope == "self" and str(own_student.id) != str(student_id):
            return _forbidden()

        try:
            Student.objects.get(pk=student_id, school=school)
        except Student.DoesNotExist:
            return Response({"detail":"Student not found"}, status=404)

        qs = ServiceEntry.objects.filter(school=school, student_id=student_id)
        approved = qs.filter(status="approved").aggregate(total=Sum("hours"))["total"] or 0
        pending = qs.filter(status="pending").aggregate(total=Sum("hours"))["total"] or 0
        lifetime = qs.aggregate(total=Sum("hours"))["total"] or 0

        return Response({
            "student": str(student_id),
            "approved_hours": float(approved),
            "pending_hours": float(pending),
            "lifetime_hours": float(lifetime),
        })


class ServiceApprovalQueue(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)
        if not user_has_permission(request.user, "service.approve", school=school):
            return _forbidden()

        qs = ServiceEntry.objects.filter(school=school, status="pending").order_by("-created_at")[:300]
        return Response(ServiceEntrySerializer(qs, many=True).data)


class ServiceApproveReject(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, entry_id):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)
        if not user_has_permission(request.user, "service.approve", school=school):
            return _forbidden()

        try:
            entry = ServiceEntry.objects.get(pk=entry_id, school=school)
        except ServiceEntry.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)

        ser = ServiceApprovalSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        new_status = ser.validated_data["status"]

        entry.status = new_status
        entry.approved_by = request.user
        entry.approved_at = timezone.now()
        entry.save(update_fields=["status","approved_by","approved_at"])

        return Response(ServiceEntrySerializer(entry).data, status=200)
