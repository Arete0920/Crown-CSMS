import secrets
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from households.scoping import get_request_school_id
from outreach.models import (
    PartnerOrganization,
    Opportunity,
    ServiceLog,
    ServiceGoal,
    ReflectionPrompt,
    Badge,
    BadgeAward,
    VerificationToken,
    STATUS_DRAFT,
    STATUS_SUBMITTED,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_NEEDS_INFO,
)
from outreach.api.serializers import (
    PartnerOrganizationSerializer,
    OpportunitySerializer,
    ServiceLogSerializer,
    ServiceGoalSerializer,
    ReflectionPromptSerializer,
    BadgeSerializer,
    BadgeAwardSerializer,
)
from outreach.api.permissions import IsStudentOrStaff, IsStaffOnly, IsServiceApprover, _is_coordinator
from core.models import StudentIdentityLink


def _school_id(request):
    return get_request_school_id(request, required=True)


class TenantViewSetMixin:
    """Filters all querysets to the request's school and injects school_id on create."""

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(school_id=_school_id(self.request))

    def perform_create(self, serializer):
        serializer.save(school_id=_school_id(self.request))


# ---------------------------------------------------------------------------
# PartnerOrganization
# ---------------------------------------------------------------------------
class PartnerOrganizationViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = PartnerOrganization.objects.order_by("name")
    serializer_class = PartnerOrganizationSerializer
    permission_classes = [IsStaffOnly]


# ---------------------------------------------------------------------------
# Opportunity
# ---------------------------------------------------------------------------
class OpportunityViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        Opportunity.objects.select_related("partner").order_by("-start_at", "title")
    )
    serializer_class = OpportunitySerializer
    permission_classes = [IsStaffOnly]


# ---------------------------------------------------------------------------
# ReflectionPrompt
# ---------------------------------------------------------------------------
class ReflectionPromptViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = ReflectionPrompt.objects.order_by("title")
    serializer_class = ReflectionPromptSerializer
    permission_classes = [IsStaffOnly]


# ---------------------------------------------------------------------------
# ServiceGoal
# ---------------------------------------------------------------------------
class ServiceGoalViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = ServiceGoal.objects.order_by("-school_year", "grade", "program_tag")
    serializer_class = ServiceGoalSerializer
    permission_classes = [IsStaffOnly]


# ---------------------------------------------------------------------------
# Badge
# ---------------------------------------------------------------------------
class BadgeViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = Badge.objects.order_by("threshold_hours", "name")
    serializer_class = BadgeSerializer
    permission_classes = [IsStaffOnly]


# ---------------------------------------------------------------------------
# BadgeAward
# ---------------------------------------------------------------------------
class BadgeAwardViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        BadgeAward.objects.select_related("badge", "student").order_by("-awarded_at")
    )
    serializer_class = BadgeAwardSerializer
    permission_classes = [IsStaffOnly]


# ---------------------------------------------------------------------------
# ServiceLog
# ---------------------------------------------------------------------------
class ServiceLogViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        ServiceLog.objects.select_related("student", "opportunity", "partner")
        .order_by("-service_date", "-created_at")
    )
    serializer_class = ServiceLogSerializer
    permission_classes = [IsStudentOrStaff]

    def _own_student_id(self):
        school_id = _school_id(self.request)
        links = list(StudentIdentityLink.objects.filter(
            school_id=school_id,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            core_student__school_id=school_id,
            compatibility_student__school_id=school_id,
            compatibility_student__account=self.request.user,
        ).values_list('core_student_id', flat=True)[:2])
        return links[0] if len(links) == 1 else None

    def get_queryset(self):
        qs = super().get_queryset()
        if not _is_coordinator(self.request):
            student_id = self._own_student_id()
            if student_id is None:
                return qs.none()
            return qs.filter(student_id=student_id)
        # Coordinator: optional filters
        status_q = self.request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def perform_create(self, serializer):
        school_id = _school_id(self.request)
        if _is_coordinator(self.request):
            student = serializer.validated_data.get('student')
            if student is not None and str(student.school_id) != str(school_id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Student is outside the active school.')
        else:
            student_id = self._own_student_id()
            if student_id is None or str(serializer.validated_data.get('student_id', getattr(serializer.validated_data.get('student'), 'id', ''))) != str(student_id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Verified student ownership required.')
        serializer.save(school_id=school_id)

    def perform_update(self, serializer):
        if 'status' in serializer.validated_data:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Use the authorized workflow transition actions.')
        if not _is_coordinator(self.request) and serializer.instance.status not in (STATUS_DRAFT, STATUS_NEEDS_INFO):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only editable drafts may be changed.')
        student = serializer.validated_data.get('student', serializer.instance.student)
        if student is not None and str(student.school_id) != str(_school_id(self.request)):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Student is outside the active school.')
        if not _is_coordinator(self.request) and str(getattr(student, 'id', '')) != str(self._own_student_id()):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Student ownership cannot change.')
        serializer.save()

    def perform_destroy(self, instance):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Service-log history must be retained.')

    # ------------------------------------------------------------------
    # Workflow transitions
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        log = self.get_object()
        if log.status not in (STATUS_DRAFT, STATUS_NEEDS_INFO):
            return Response(
                {"detail": "Only draft/needs-info logs can be submitted."}, status=400
            )
        log.status = STATUS_SUBMITTED
        log.submitted_at = timezone.now()
        log.save(update_fields=["status", "submitted_at", "updated_at"])
        return Response(ServiceLogSerializer(log).data)

    @action(
        detail=True, methods=["post"], url_path="approve",
        permission_classes=[IsServiceApprover]
    )
    def approve(self, request, pk=None):
        log = self.get_object()
        if log.status != STATUS_SUBMITTED:
            return Response(
                {"detail": "Only submitted logs can be approved."}, status=400
            )
        log.status = STATUS_APPROVED
        log.reviewed_at = timezone.now()
        log.reviewed_by = request.user if request.user.is_authenticated else None
        log.reviewer_notes = request.data.get("reviewer_notes", "")
        log.save(
            update_fields=["status", "reviewed_at", "reviewed_by", "reviewer_notes", "updated_at"]
        )
        return Response(ServiceLogSerializer(log).data)

    @action(
        detail=True, methods=["post"], url_path="reject",
        permission_classes=[IsStaffOnly]
    )
    def reject(self, request, pk=None):
        log = self.get_object()
        if log.status != STATUS_SUBMITTED:
            return Response(
                {"detail": "Only submitted logs can be rejected."}, status=400
            )
        log.status = STATUS_REJECTED
        log.reviewed_at = timezone.now()
        log.reviewed_by = request.user if request.user.is_authenticated else None
        log.reviewer_notes = request.data.get("reviewer_notes", "")
        log.save(
            update_fields=["status", "reviewed_at", "reviewed_by", "reviewer_notes", "updated_at"]
        )
        return Response(ServiceLogSerializer(log).data)

    @action(
        detail=True, methods=["post"], url_path="needs-info",
        permission_classes=[IsStaffOnly]
    )
    def needs_info(self, request, pk=None):
        log = self.get_object()
        if log.status != STATUS_SUBMITTED:
            return Response(
                {"detail": "Only submitted logs can be marked needs-info."}, status=400
            )
        log.status = STATUS_NEEDS_INFO
        log.reviewed_at = timezone.now()
        log.reviewed_by = request.user if request.user.is_authenticated else None
        log.reviewer_notes = request.data.get("reviewer_notes", "")
        log.save(
            update_fields=["status", "reviewed_at", "reviewed_by", "reviewer_notes", "updated_at"]
        )
        return Response(ServiceLogSerializer(log).data)

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    @action(
        detail=False, methods=["get"], url_path="report/summary",
        permission_classes=[IsStaffOnly]
    )
    def report_summary(self, request):
        sid = _school_id(request)
        qs = ServiceLog.objects.filter(school_id=sid, status=STATUS_APPROVED)
        total_hours = qs.aggregate(x=Sum("hours"))["x"] or Decimal("0")
        by_partner = list(
            qs.values("partner__name").annotate(hours=Sum("hours")).order_by("-hours")[:10]
        )
        by_grade = list(
            qs.values("student__current_grade_level__code")
            .annotate(hours=Sum("hours"))
            .order_by("student__current_grade_level__code")
        )
        return Response(
            {
                "total_hours": str(total_hours),
                "top_partners": by_partner,
                "hours_by_grade": by_grade,
            }
        )

    @action(detail=False, methods=["get"], url_path="report/student-progress")
    def report_student_progress(self, request):
        sid = _school_id(request)
        student_id = request.query_params.get("student_id")
        if not student_id:
            return Response({"detail": "student_id is required."}, status=400)
        if not _is_coordinator(request) and str(student_id) != str(self._own_student_id()):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Verified student ownership required.")

        approved = ServiceLog.objects.filter(
            school_id=sid, student_id=student_id, status=STATUS_APPROVED
        )
        hours = approved.aggregate(x=Sum("hours"))["x"] or Decimal("0")

        # Resolve student grade as integer from GradeLevel.code if available
        grade = None
        try:
            from core.models import Student as CoreStudent
            student_obj = CoreStudent.objects.select_related("current_grade_level").get(
                id=student_id
            )
            if student_obj.current_grade_level:
                code = student_obj.current_grade_level.code
                if code and code.isdigit():
                    grade = int(code)
        except Exception:
            grade = None

        # Find matching goal: grade-specific first, then schoolwide
        goal = None
        if grade is not None:
            goal = (
                ServiceGoal.objects.filter(school_id=sid, active=True, grade=grade)
                .order_by("-school_year")
                .first()
            )
        if not goal:
            goal = (
                ServiceGoal.objects.filter(school_id=sid, active=True, grade__isnull=True)
                .order_by("-school_year")
                .first()
            )

        required = goal.required_hours if goal else Decimal("0")
        pct = float(hours / required * 100) if required and required > 0 else 0.0

        return Response(
            {
                "student_id": student_id,
                "grade_level": grade,
                "approved_hours": str(hours),
                "required_hours": str(required),
                "progress_pct": round(pct, 1),
                "goal": ServiceGoalSerializer(goal).data if goal else None,
            }
        )

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------
    @action(
        detail=True, methods=["post"], url_path="verification/send",
        permission_classes=[IsStaffOnly]
    )
    def send_verification(self, request, pk=None):
        log = self.get_object()
        if not log.external_verifier_email:
            return Response(
                {"detail": "external_verifier_email is required on the log."}, status=400
            )

        vt, _ = VerificationToken.objects.get_or_create(
            school_id=_school_id(request),
            service_log=log,
            defaults={"token": secrets.token_hex(24)},
        )
        vt.sent_at = timezone.now()
        vt.verified_at = None
        vt.verified_by_email = ""
        vt.save(update_fields=["sent_at", "verified_at", "verified_by_email", "updated_at"])

        if getattr(request, "DEMO_MODE", False):
            return Response({"detail": "token generated (demo)", "token": vt.token})
        return Response({"detail": "verification request sent"})
