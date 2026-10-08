from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import School
from core.permissions import CrownModulePermission
from households.scoping import get_request_school_id
from spiritual_life.formation_models import (
    BiblicalIntegrationRecord,
    BiblicalWorldviewPriority,
    CallingPathwayEvent,
    ChristianEducationSundayCampaign,
    ChurchEngagementEvent,
    ChurchPartner,
    CommunityOrganizationPartner,
    DevotionalContent,
    FamilyFormationEvent,
    FormationArtifact,
    FormationCampaign,
    PastorContact,
    PortraitDomain,
    SpeakerVettingRecord,
    SpiritualCareCase,
    SpiritualDomainRating,
    StaffFormationEvent,
    StudentLeadershipEvent,
    StudentSpiritualLeadershipRole,
)
from spiritual_life.api.formation_serializers import (
    BiblicalIntegrationRecordSerializer,
    BiblicalWorldviewPrioritySerializer,
    CallingPathwayEventSerializer,
    ChristianEducationSundayCampaignSerializer,
    ChurchEngagementEventSerializer,
    ChurchPartnerSerializer,
    CommunityOrganizationPartnerSerializer,
    DevotionalContentSerializer,
    FamilyFormationEventSerializer,
    FormationArtifactSerializer,
    FormationCampaignSerializer,
    PastorContactSerializer,
    PortraitDomainSerializer,
    SpeakerVettingRecordSerializer,
    SpiritualCareCaseSerializer,
    SpiritualDomainRatingSerializer,
    StaffFormationEventSerializer,
    StudentLeadershipEventSerializer,
    StudentSpiritualLeadershipRoleSerializer,
)


def _get_school(request) -> School:
    sid = get_request_school_id(request, required=True)
    return School.objects.get(pk=sid)


def _assign_owner_fields(serializer, request):
    """Set common owner/reviewer fields when present on a model."""
    model = serializer.Meta.model
    kwargs = {"school": _get_school(request)}
    for field_name in [
        "owner",
        "created_by",
        "reviewed_by",
        "relationship_owner",
        "speaker",
        "mentor",
        "facilitator",
        "reviewer",
    ]:
        try:
            model._meta.get_field(field_name)
        except Exception:
            continue
        kwargs[field_name] = request.user
    return serializer.save(**kwargs)


class TenantScopedListCreateView(APIView):
    """Small generic list/create view for Spiritual Life formation records."""

    permission_classes = [CrownModulePermission("spiritual_life.view", write_code="spiritual_life.edit")]
    model = None
    serializer_class = None
    allowed_filters = []
    select_related = []
    prefetch_related = []
    order_by = None
    limit = 500

    def get_queryset(self, request):
        school = _get_school(request)
        qs = self.model.objects.filter(school=school)
        for field in self.allowed_filters:
            value = request.query_params.get(field)
            if value not in (None, ""):
                qs = qs.filter(**{field: value})
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        if self.prefetch_related:
            qs = qs.prefetch_related(*self.prefetch_related)
        if self.order_by:
            qs = qs.order_by(*self.order_by)
        return qs

    def get(self, request):
        qs = self.get_queryset(request)[: self.limit]
        return Response(self.serializer_class(qs, many=True).data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        instance = _assign_owner_fields(serializer, request)
        return Response(self.serializer_class(instance).data, status=status.HTTP_201_CREATED)


class TenantScopedDetailView(APIView):
    """Small generic retrieve/update view for Spiritual Life formation records."""

    permission_classes = [CrownModulePermission("spiritual_life.view", write_code="spiritual_life.edit")]
    model = None
    serializer_class = None

    def get_object(self, request, pk):
        return get_object_or_404(self.model, pk=pk, school=_get_school(request))

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        return Response(self.serializer_class(obj).data)

    def patch(self, request, pk):
        obj = self.get_object(request, pk)
        serializer = self.serializer_class(obj, data=request.data or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.serializer_class(instance).data)


class PortraitDomainListCreate(TenantScopedListCreateView):
    model = PortraitDomain
    serializer_class = PortraitDomainSerializer
    allowed_filters = ["is_active"]
    order_by = ["sort_order", "name"]


class PortraitDomainDetail(TenantScopedDetailView):
    model = PortraitDomain
    serializer_class = PortraitDomainSerializer


class BiblicalWorldviewPriorityListCreate(TenantScopedListCreateView):
    model = BiblicalWorldviewPriority
    serializer_class = BiblicalWorldviewPrioritySerializer
    allowed_filters = ["is_active", "school_year", "grade_band"]
    order_by = ["school_year", "title"]


class BiblicalWorldviewPriorityDetail(TenantScopedDetailView):
    model = BiblicalWorldviewPriority
    serializer_class = BiblicalWorldviewPrioritySerializer


class FormationCampaignListCreate(TenantScopedListCreateView):
    model = FormationCampaign
    serializer_class = FormationCampaignSerializer
    allowed_filters = ["status"]
    prefetch_related = ["portrait_domains", "worldview_priorities"]
    order_by = ["-start_date", "name"]


class FormationCampaignDetail(TenantScopedDetailView):
    model = FormationCampaign
    serializer_class = FormationCampaignSerializer


class FormationArtifactListCreate(TenantScopedListCreateView):
    model = FormationArtifact
    serializer_class = FormationArtifactSerializer
    allowed_filters = ["artifact_type"]
    prefetch_related = ["campaigns", "portrait_domains", "worldview_priorities"]
    order_by = ["-artifact_date", "-created_at"]


class FormationArtifactDetail(TenantScopedDetailView):
    model = FormationArtifact
    serializer_class = FormationArtifactSerializer


class DevotionalContentListCreate(TenantScopedListCreateView):
    model = DevotionalContent
    serializer_class = DevotionalContentSerializer
    allowed_filters = ["audience", "grade_band", "status", "is_published"]
    prefetch_related = ["portrait_domains", "worldview_priorities"]
    order_by = ["-publish_date", "audience", "title"]


class DevotionalContentDetail(TenantScopedDetailView):
    model = DevotionalContent
    serializer_class = DevotionalContentSerializer


class BiblicalIntegrationRecordListCreate(TenantScopedListCreateView):
    model = BiblicalIntegrationRecord
    serializer_class = BiblicalIntegrationRecordSerializer
    allowed_filters = ["grade_label", "subject"]
    order_by = ["-integration_date", "-created_at"]


class SpiritualDomainRatingListCreate(TenantScopedListCreateView):
    model = SpiritualDomainRating
    serializer_class = SpiritualDomainRatingSerializer
    allowed_filters = ["student_id", "domain_id"]
    order_by = ["-rating_date", "-created_at"]


class SpiritualCareCaseListCreate(TenantScopedListCreateView):
    model = SpiritualCareCase
    serializer_class = SpiritualCareCaseSerializer
    allowed_filters = ["status", "priority", "case_type", "student_id"]
    order_by = ["-updated_at", "-created_at"]


class SpiritualCareCaseDetail(TenantScopedDetailView):
    model = SpiritualCareCase
    serializer_class = SpiritualCareCaseSerializer


class ChurchPartnerListCreate(TenantScopedListCreateView):
    model = ChurchPartner
    serializer_class = ChurchPartnerSerializer
    allowed_filters = ["is_active_partner"]
    order_by = ["name"]


class ChurchPartnerDetail(TenantScopedDetailView):
    model = ChurchPartner
    serializer_class = ChurchPartnerSerializer


class PastorContactListCreate(TenantScopedListCreateView):
    model = PastorContact
    serializer_class = PastorContactSerializer
    allowed_filters = ["church_id", "contact_type", "is_primary"]
    select_related = ["church"]
    order_by = ["church__name", "name"]


class PastorContactDetail(TenantScopedDetailView):
    model = PastorContact
    serializer_class = PastorContactSerializer


class ChurchEngagementEventListCreate(TenantScopedListCreateView):
    model = ChurchEngagementEvent
    serializer_class = ChurchEngagementEventSerializer
    allowed_filters = ["event_type", "status", "church_partner_id"]
    order_by = ["-event_date", "title"]


class ChurchEngagementEventDetail(TenantScopedDetailView):
    model = ChurchEngagementEvent
    serializer_class = ChurchEngagementEventSerializer


class ChristianEducationSundayCampaignListCreate(TenantScopedListCreateView):
    model = ChristianEducationSundayCampaign
    serializer_class = ChristianEducationSundayCampaignSerializer
    allowed_filters = ["school_year"]
    prefetch_related = ["churches"]
    order_by = ["-campaign_date", "name"]


class CommunityOrganizationPartnerListCreate(TenantScopedListCreateView):
    model = CommunityOrganizationPartner
    serializer_class = CommunityOrganizationPartnerSerializer
    allowed_filters = ["partner_type", "is_active"]
    order_by = ["name"]


class StudentSpiritualLeadershipRoleListCreate(TenantScopedListCreateView):
    model = StudentSpiritualLeadershipRole
    serializer_class = StudentSpiritualLeadershipRoleSerializer
    allowed_filters = ["role_type", "active", "student_id"]
    order_by = ["student__last_name", "student__first_name", "role_type"]


class StudentLeadershipEventListCreate(TenantScopedListCreateView):
    model = StudentLeadershipEvent
    serializer_class = StudentLeadershipEventSerializer
    allowed_filters = ["event_type"]
    prefetch_related = ["attendees"]
    order_by = ["-event_date", "title"]


class CallingPathwayEventListCreate(TenantScopedListCreateView):
    model = CallingPathwayEvent
    serializer_class = CallingPathwayEventSerializer
    allowed_filters = ["event_type"]
    order_by = ["-event_date", "title"]


class FamilyFormationEventListCreate(TenantScopedListCreateView):
    model = FamilyFormationEvent
    serializer_class = FamilyFormationEventSerializer
    order_by = ["-event_date", "title"]


class StaffFormationEventListCreate(TenantScopedListCreateView):
    model = StaffFormationEvent
    serializer_class = StaffFormationEventSerializer
    allowed_filters = ["event_type"]
    order_by = ["-event_date", "title"]


class SpeakerVettingRecordListCreate(TenantScopedListCreateView):
    model = SpeakerVettingRecord
    serializer_class = SpeakerVettingRecordSerializer
    allowed_filters = ["status"]
    order_by = ["-updated_at", "speaker_name"]


class FormationMissionControlSummary(APIView):
    """Aggregate mission-control snapshot for the Spiritual Life dashboard."""

    permission_classes = [CrownModulePermission("spiritual_life.view", write_code="spiritual_life.edit")]

    def get(self, request):
        school = _get_school(request)
        return Response(
            {
                "portrait_domains": PortraitDomain.objects.filter(school=school, is_active=True).count(),
                "worldview_priorities": BiblicalWorldviewPriority.objects.filter(school=school, is_active=True).count(),
                "published_devotions": DevotionalContent.objects.filter(school=school, is_published=True).count(),
                "devotions_in_review": DevotionalContent.objects.filter(school=school, status="review").count(),
                "open_spiritual_care_cases": SpiritualCareCase.objects.filter(school=school, status="open").count(),
                "urgent_spiritual_care_cases": SpiritualCareCase.objects.filter(school=school, priority="urgent").exclude(status="closed").count(),
                "active_church_partners": ChurchPartner.objects.filter(school=school, is_active_partner=True).count(),
                "church_engagements_follow_up": ChurchEngagementEvent.objects.filter(school=school, status="follow_up_needed").count(),
                "student_spiritual_leaders": StudentSpiritualLeadershipRole.objects.filter(school=school, active=True).count(),
                "student_leadership_events": StudentLeadershipEvent.objects.filter(school=school).count(),
                "calling_pathway_events": CallingPathwayEvent.objects.filter(school=school).count(),
                "family_formation_events": FamilyFormationEvent.objects.filter(school=school).count(),
                "staff_formation_events": StaffFormationEvent.objects.filter(school=school).count(),
                "speaker_vetting_pending": SpeakerVettingRecord.objects.filter(school=school, status__in=["proposed", "under_review"]).count(),
                "formation_artifacts": FormationArtifact.objects.filter(school=school).count(),
                "source": "live_db",
            }
        )
