# backend/athletics/api/views.py
from __future__ import annotations

from django.http import Http404
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
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
from athletics.api.permissions import IsAthleticDirector, IsCoachOrAD, has_athletics_view
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
from core.models import Student

# Crown canonical tenant helper
from households.scoping import get_request_school_id


def _require_same_school(obj, school_id, field_name):
    if obj is not None and getattr(obj, "school_id", None) != school_id:
        raise ValidationError({field_name: "Related object must belong to the requested school."})


def _require_same_school_id(model, object_id, school_id, field_name):
    if object_id is not None and not model.objects.filter(pk=object_id, school_id=school_id).exists():
        raise ValidationError({field_name: "Related object must belong to the requested school."})


def _user_belongs_to_school(user, school_id) -> bool:
    if user is None:
        return True
    direct_school_id = getattr(user, "school_id", None)
    if direct_school_id is not None:
        return direct_school_id == school_id
    roles = getattr(user, "roles", None)
    if roles is None:
        return False
    school_ids = list(
        roles.exclude(school_id__isnull=True)
        .values_list("school_id", flat=True)
        .distinct()[:2]
    )
    return len(school_ids) == 1 and school_ids[0] == school_id


class SchoolScopedQuerysetMixin:
    def get_school_id(self):
        return get_request_school_id(self.request)

    def filter_school(self, qs):
        return qs.filter(school_id=self.get_school_id())


class SportViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = SportSerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return self.filter_school(Sport.objects.order_by("name", "gender")).order_by("name", "gender")

    def perform_create(self, serializer):
        serializer.save(school_id=self.get_school_id())


class SeasonViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = SeasonSerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return self.filter_school(Season.objects.order_by("-start_date")).order_by("-start_date")

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

    def _validate_relations(self, serializer):
        school_id = self.get_school_id()
        _require_same_school_id(Sport, serializer.validated_data.get("sport_id"), school_id, "sport_id")
        _require_same_school_id(Season, serializer.validated_data.get("season_id"), school_id, "season_id")

    def perform_create(self, serializer):
        self._validate_relations(serializer)
        serializer.save(school_id=self.get_school_id())

    def perform_update(self, serializer):
        self._validate_relations(serializer)
        serializer.save()


class FacilityViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = FacilitySerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return self.filter_school(Facility.objects.order_by("name")).order_by("name")

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

    def _validate_relations(self, serializer):
        school_id = self.get_school_id()
        _require_same_school(serializer.validated_data.get("team"), school_id, "team")
        _require_same_school(serializer.validated_data.get("student"), school_id, "student")

    def perform_create(self, serializer):
        self._validate_relations(serializer)
        # NOTE: Phase 2 — add ledger charge hook here when finance.services
        # exposes a stable post_charge(school_id, student_id, amount_cents, ...) API.
        serializer.save(school_id=self.get_school_id())

    def perform_update(self, serializer):
        self._validate_relations(serializer)
        serializer.save()


class TeamCoachViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = TeamCoachSerializer
    permission_classes = [IsAthleticDirector]

    def get_queryset(self):
        return (
            self.filter_school(TeamCoach.objects.select_related("team", "user"))
            .order_by("-is_head_coach", "user__last_name")
        )

    def _validate_relations(self, serializer):
        school_id = self.get_school_id()
        _require_same_school(serializer.validated_data.get("team"), school_id, "team")
        user = serializer.validated_data.get("user")
        if user is not None and not _user_belongs_to_school(user, school_id):
            raise ValidationError({"user": "Coach user must belong unambiguously to the requested school."})

    def perform_create(self, serializer):
        self._validate_relations(serializer)
        serializer.save(school_id=self.get_school_id())

    def perform_update(self, serializer):
        self._validate_relations(serializer)
        serializer.save()


class EventViewSet(viewsets.ModelViewSet, SchoolScopedQuerysetMixin):
    serializer_class = EventSerializer
    permission_classes = [IsCoachOrAD]

    def get_queryset(self):
        school_id = self.get_school_id()
        qs = Event.objects.select_related("team", "facility").filter(school_id=school_id)

        # Persistent CROWN Athletics authority sees all tenant events. Coaches
        # without that grant are restricted to their verified active assignments.
        if not has_athletics_view(self.request):
            coached_team_ids = TeamCoach.objects.filter(
                school_id=school_id, user=self.request.user, is_active=True
            ).values_list("team_id", flat=True)
            qs = qs.filter(team_id__in=coached_team_ids)

        team_id = self.request.query_params.get("team_id")
        if team_id:
            qs = qs.filter(team_id=team_id)

        return qs.order_by("starts_at")

    def _validate_relations(self, serializer):
        school_id = self.get_school_id()
        _require_same_school(serializer.validated_data.get("team"), school_id, "team")
        _require_same_school(serializer.validated_data.get("facility"), school_id, "facility")

    def _require_team_mutation_authority(self, serializer):
        if has_athletics_view(self.request):
            return

        team = serializer.validated_data.get("team")
        if team is None and serializer.instance is not None:
            team = serializer.instance.team
        if team is None:
            raise PermissionDenied("A team assignment is required for coach event changes.")

        if not TeamCoach.objects.filter(
            school_id=self.get_school_id(),
            team=team,
            user=self.request.user,
            is_active=True,
        ).exists():
            raise PermissionDenied("Coaches may change events only for teams they are actively assigned to.")

    def perform_create(self, serializer):
        self._validate_relations(serializer)
        self._require_team_mutation_authority(serializer)
        serializer.save(school_id=self.get_school_id())

    def perform_update(self, serializer):
        self._validate_relations(serializer)
        self._require_team_mutation_authority(serializer)
        serializer.save()

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
        student = Student.objects.filter(pk=student_id, school_id=school_id).first()
        if student is None:
            raise Http404

        if AthleteClearance.objects.filter(student=student).exclude(school_id=school_id).exists():
            raise Http404

        obj, _ = AthleteClearance.objects.get_or_create(
            school_id=school_id,
            student=student,
        )
        return obj

    def perform_update(self, serializer):
        school_id = self.get_school_id()
        student = serializer.validated_data.get("student")
        _require_same_school(student, school_id, "student")
        if student is not None and student.pk != self.get_object().student_id:
            raise ValidationError({"student": "Clearance student cannot be reassigned."})
        serializer.save()


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
