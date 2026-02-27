from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.utils import timezone

from core.audit import audit_event
from core.permissions import CrownModulePermission, require_permission
from households.scoping import get_request_school_id
from .models import PDResource, PDSession
from .serializers import PDResourceSerializer, PDSessionSerializer


def _require_school(request):
    school = getattr(request, "school", None)
    if school is None:
        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
    return school


class PDResourceViewSet(viewsets.ModelViewSet):
    serializer_class = PDResourceSerializer
    permission_classes = [CrownModulePermission("pd.view", write_code="pd.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        return PDResource.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        instance = serializer.save(school_id=school.id)
        audit_event("pd.resource.created", user=self.request.user, school=school,
                    extra={"resource_id": str(instance.id)})

    def perform_update(self, serializer):
        instance = serializer.save()
        audit_event("pd.resource.updated", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"resource_id": str(instance.id)})

    def perform_destroy(self, instance):
        audit_event("pd.resource.deleted", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"resource_id": str(instance.id)})
        instance.delete()


class PDSessionViewSet(viewsets.ModelViewSet):
    serializer_class = PDSessionSerializer
    permission_classes = [CrownModulePermission("pd.view", write_code="pd.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        return PDSession.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        instance = serializer.save(school_id=school.id)
        audit_event("pd.session.created", user=self.request.user, school=school,
                    extra={"session_id": str(instance.id)})

    def perform_update(self, serializer):
        instance = serializer.save()
        audit_event("pd.session.updated", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"session_id": str(instance.id)})

    def perform_destroy(self, instance):
        audit_event("pd.session.deleted", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"session_id": str(instance.id)})
        instance.delete()


@require_permission("pd.view")
def pd_metrics(request):
    sid = get_request_school_id(request)
    resources = PDResource.objects.filter(school_id=sid)
    sessions = PDSession.objects.filter(school_id=sid)
    now = timezone.now()
    upcoming = sessions.filter(session_date__gte=now)
    avg_rating = sessions.aggregate(avg=Avg("satisfaction_score"))["avg"]
    return JsonResponse({
        "total_resources":   resources.count(),
        "total_sessions":    sessions.count(),
        "upcoming_sessions": upcoming.count(),
        "average_rating":    round(avg_rating, 2) if avg_rating else None,
    })
