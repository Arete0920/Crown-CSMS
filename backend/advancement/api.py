from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count

from core.audit import audit_event
from core.permissions import CrownModulePermission
from .models import Donor, Campaign
from .serializers import DonorSerializer, CampaignSerializer


def _require_school(request):
    school = getattr(request, "school", None)
    if school is None:
        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
    return school


class DonorViewSet(viewsets.ModelViewSet):
    serializer_class = DonorSerializer
    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        return Donor.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        instance = serializer.save(school_id=school.id)
        audit_event("advancement.donor.created", user=self.request.user, school=school,
                    extra={"donor_id": str(instance.id)})

    def perform_update(self, serializer):
        instance = serializer.save()
        audit_event("advancement.donor.updated", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"donor_id": str(instance.id)})

    def perform_destroy(self, instance):
        audit_event("advancement.donor.deleted", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"donor_id": str(instance.id)})
        instance.delete()


class CampaignViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        return Campaign.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        instance = serializer.save(school_id=school.id)
        audit_event("advancement.campaign.created", user=self.request.user, school=school,
                    extra={"campaign_id": str(instance.id)})

    def perform_update(self, serializer):
        instance = serializer.save()
        audit_event("advancement.campaign.updated", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"campaign_id": str(instance.id)})

    def perform_destroy(self, instance):
        audit_event("advancement.campaign.deleted", user=self.request.user,
                    school=getattr(self.request, "school", None),
                    extra={"campaign_id": str(instance.id)})
        instance.delete()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def advancement_metrics(request):
    school = _require_school(request)
    donors = Donor.objects.filter(school_id=school.id)
    campaigns = Campaign.objects.filter(school_id=school.id)
    total_raised = donors.aggregate(total=Sum("total_donated"))["total"] or 0
    return Response({
        "total_donors":   donors.count(),
        "total_raised":   float(total_raised),
        "active_campaigns": campaigns.filter(active=True).count(),
        "total_campaigns":  campaigns.count(),
    })
