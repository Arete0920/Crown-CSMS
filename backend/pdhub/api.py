from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from .models import PDResource, PDSession
from .serializers import PDResourceSerializer, PDSessionSerializer


def _school_id(request):
    return request.headers.get("X-School-Id") or request.headers.get("X-School-ID")


class PDResourceViewSet(viewsets.ModelViewSet):
    serializer_class = PDResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = _school_id(self.request)
        if not school_id:
            return PDResource.objects.none()
        return PDResource.objects.filter(school_id=school_id)

    def perform_create(self, serializer):
        serializer.save(school_id=_school_id(self.request))


class PDSessionViewSet(viewsets.ModelViewSet):
    serializer_class = PDSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = _school_id(self.request)
        if not school_id:
            return PDSession.objects.none()
        return PDSession.objects.filter(school_id=school_id)

    def perform_create(self, serializer):
        serializer.save(school_id=_school_id(self.request))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def pd_metrics(request):
    school_id = _school_id(request)
    if not school_id:
        return Response({"error": "X-School-Id required"}, status=400)

    sessions_qs = PDSession.objects.filter(school_id=school_id)
    now = timezone.now()
    this_month = sessions_qs.filter(
        session_date__month=now.month,
        session_date__year=now.year,
    )
    completed = sessions_qs.filter(status="completed")
    staff_hours = float(
        PDResource.objects.filter(school_id=school_id)
        .aggregate(h=Sum("credit_hours"))["h"]
        or 0
    )
    satisfaction_avg = completed.aggregate(avg=Avg("satisfaction_score"))["avg"]

    upcoming = list(
        sessions_qs.filter(status="upcoming").order_by("session_date")[:5].values(
            "title", "presenter", "department", "session_date", "status"
        )
    )

    by_dept = list(
        sessions_qs.values("department")
        .annotate(count=Count("id"))
        .order_by("-count")
        .values("department", "count")
    )

    return Response({
        "sessions_this_month": this_month.count(),
        "staff_hours_logged": staff_hours,
        "certifications_expiring": 0,
        "satisfaction_avg": round(float(satisfaction_avg), 2) if satisfaction_avg else 0,
        "upcoming_sessions": [
            {
                "title": s["title"],
                "presenter": s["presenter"] or "",
                "dept": s["department"] or "",
                "date": str(s["session_date"]) if s["session_date"] else "",
                "status": s["status"],
            }
            for s in upcoming
        ],
        "certifications": [],
        "completion_by_dept": [{"dept": r["department"] or "Unknown", "count": r["count"]} for r in by_dept],
        "alerts": [],
        "snapshot_date": str(now.date()),
    })
