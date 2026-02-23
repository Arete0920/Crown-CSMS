from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count

from .models import Donor, Campaign
from .serializers import DonorSerializer, CampaignSerializer


def _school_id(request):
    return request.headers.get("X-School-Id") or request.headers.get("X-School-ID")


class DonorViewSet(viewsets.ModelViewSet):
    serializer_class = DonorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = _school_id(self.request)
        if not school_id:
            return Donor.objects.none()
        return Donor.objects.filter(school_id=school_id)

    def perform_create(self, serializer):
        serializer.save(school_id=_school_id(self.request))


class CampaignViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = _school_id(self.request)
        if not school_id:
            return Campaign.objects.none()
        return Campaign.objects.filter(school_id=school_id)

    def perform_create(self, serializer):
        serializer.save(school_id=_school_id(self.request))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def advancement_metrics(request):
    school_id = _school_id(request)
    if not school_id:
        return Response({"error": "X-School-Id required"}, status=400)

    donors_qs = Donor.objects.filter(school_id=school_id, active=True)
    campaigns_qs = Campaign.objects.filter(school_id=school_id)
    active_campaigns = campaigns_qs.filter(status="active")

    # Campaign progress: avg raised/goal across active campaigns
    campaign_progress_pct = 0
    if active_campaigns.exists():
        total_goal = active_campaigns.aggregate(g=Sum("goal"))["g"] or 0
        total_raised = active_campaigns.aggregate(r=Sum("raised"))["r"] or 0
        if total_goal:
            campaign_progress_pct = round(float(total_raised) / float(total_goal) * 100)

    top_sources = list(
        donors_qs.values("source")
        .annotate(amount=Sum("lifetime_giving"))
        .order_by("-amount")
        .values("source", "amount")[:5]
    )

    campaigns_serialized = [
        {
            "name": c.name,
            "goal": float(c.goal),
            "raised": float(c.raised),
            "donors": c.donors_count,
            "status": c.status,
        }
        for c in campaigns_qs[:10]
    ]

    return Response({
        "donors_active": donors_qs.count(),
        "campaign_progress_pct": campaign_progress_pct,
        "pledges_outstanding": 0,
        "thankyous_due": 0,
        "campaigns": campaigns_serialized,
        "top_sources": [{"source": r["source"] or "Unknown", "amount": float(r["amount"] or 0)} for r in top_sources],
        "tasks": [],
        "alerts": [],
    })
