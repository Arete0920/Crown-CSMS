# backend/athletics/api/views.py
from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from athletics.models import (
    AthleteClearance,
    AthleteEligibility,
    Event,
    Facility,
    Season,
    Sport,
    Team,
    TeamCoach,
    TeamRoster,
)
from athletics.api.permissions import IsAthleticDirector, IsCoachOrAD
from athletics.api.serializers import (
    AthleteClearanceSerializer,
    AthleteEligibilitySerializer,
    EventSerializer,
    FacilitySerializer,
    SeasonSerializer,
    SportSerializer,
    TeamCoachSerializer,
    TeamRosterSerializer,
    TeamSerializer,
)

# Crown canonical tenant helper
from households.scoping import get_request_school_id


class SchoolScopedQuerysetMixin:
    def get_school_id(self):
        return get_request_school_id(self.request)

    def filter_school(self, qs):
        return qs.filter(school_id=self.get_school_id())


class SportViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = SportSerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return self.filter_school(Sport.objects.all()).order_by("name", "gender")

    def perform_create(self, serializer):
        serializer.save(school_id=self.get_school_id())


class SeasonViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = SeasonSerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return self.filter_school(Season.objects.all()).order_by("-start_date")

    def perform_create(self, serializer):
        serializer.save(school_id=self.get_school_id())


class TeamViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = TeamSerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return (
            self.filter_school(Team.objects.select_related("sport", "season"))
            .order_by("season__start_date", "display_name")
        )

    def perform_create(self, serializer):
        serializer.save(school_id=self.get_school_id())


class FacilityViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = FacilitySerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return self.filter_school(Facility.objects.all()).order_by("name")

    def perform_create(self, serializer):
        serializer.save(school_id=self.get_school_id())


class TeamRosterViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = TeamRosterSerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return (
            self.filter_school(TeamRoster.objects.select_related("team", "student"))
            .order_by("-joined_at")
        )

    def perform_create(self, serializer):
        # NOTE: Phase 2 — add ledger charge hook here when finance.services
        # exposes a stable post_charge(school_id, student_id, amount_cents, ...) API.
        serializer.save(school_id=self.get_school_id())


class TeamCoachViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = TeamCoachSerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return (
            self.filter_school(TeamCoach.objects.select_related("team", "user"))
            .order_by("-is_head_coach", "user__last_name")
        )

    def perform_create(self, serializer):
        serializer.save(school_id=self.get_school_id())


class EventViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = EventSerializer
    permission_classes = [IsCoachOrAD]

    def get_queryset(self):
        school_id = self.get_school_id()
        qs = Event.objects.select_related("team", "facility").filter(school_id=school_id)

        user = self.request.user
        # ADs and staff see all events; coaches see only their teams' events.
        is_ad = getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)
        if not is_ad:
            coached_team_ids = TeamCoach.objects.filter(
                school_id=school_id, user=user, is_active=True
            ).values_list("team_id", flat=True)
            qs = qs.filter(team_id__in=coached_team_ids)

        team_id = self.request.query_params.get("team_id")
        if team_id:
            qs = qs.filter(team_id=team_id)

        return qs.order_by("starts_at")

    def perform_create(self, serializer):
        serializer.save(school_id=self.get_school_id())

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        qs = self.get_queryset()
        return Response(self.get_serializer(qs, many=True).data)


class AthleteClearanceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
    SchoolScopedQuerysetMixin,
):
    serializer_class = AthleteClearanceSerializer
    permission_classes = [IsCoachOrAD]

    def get_queryset(self):
        return self.filter_school(AthleteClearance.objects.select_related("student"))

    def get_object(self):
        school_id = self.get_school_id()
        student_id = self.kwargs["pk"]
        obj, _ = AthleteClearance.objects.get_or_create(
            student_id=student_id,
            defaults={"school_id": school_id},
        )
        return obj


class AthleteEligibilityViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
    SchoolScopedQuerysetMixin,
):
    serializer_class = AthleteEligibilitySerializer
    permission_classes = [IsCoachOrAD]

    def get_queryset(self):
        qs = self.filter_school(
            AthleteEligibility.objects.select_related("team", "student")
        )
        team_id = self.request.query_params.get("team_id")
        if team_id:
            qs = qs.filter(team_id=team_id)
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs.order_by("team_id", "student_id")
