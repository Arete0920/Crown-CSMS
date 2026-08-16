# backend/athletics/api/serializers.py
from __future__ import annotations

from rest_framework import serializers

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


def _request_school(serializer):
    """Return the already-authorized request school for relation validation."""
    request = serializer.context.get("request")
    context = getattr(request, "crown_tenant", None)
    school = getattr(context, "school", None)
    if school is None:
        school = getattr(request, "school", None) or getattr(request, "tenant_school", None)
    if school is None:
        raise serializers.ValidationError({"school": "Tenant context is required."})
    return school


def _relation_value(serializer, attrs, field_name):
    if field_name in attrs:
        return attrs[field_name]
    if serializer.instance is not None:
        return getattr(serializer.instance, field_name, None)
    return None


def _require_same_school(obj, school, field_name):
    if obj is not None and getattr(obj, "school_id", None) != school.pk:
        raise serializers.ValidationError(
            {field_name: "Related object must belong to the requested school."}
        )


def _user_belongs_to_school(user, school) -> bool:
    """Mirror the canonical principal-school rule without granting ambiguity."""
    direct_school_id = getattr(user, "school_id", None)
    if direct_school_id is not None:
        return direct_school_id == school.pk

    roles = getattr(user, "roles", None)
    if roles is None:
        return False

    school_ids = list(
        roles.exclude(school_id__isnull=True)
        .values_list("school_id", flat=True)
        .distinct()[:2]
    )
    return len(school_ids) == 1 and school_ids[0] == school.pk


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ["id", "name", "gender", "is_active"]


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ["id", "name", "start_date", "end_date", "is_published"]


class TeamSerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)
    sport_id = serializers.IntegerField(write_only=True)
    season = SeasonSerializer(read_only=True)
    season_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Team
        fields = [
            "id",
            "sport",
            "sport_id",
            "season",
            "season_id",
            "level",
            "display_name",
            "is_active",
            "participation_fee_cents",
        ]

    def validate(self, attrs):
        school = _request_school(self)
        sport_id = _relation_value(self, attrs, "sport_id")
        season_id = _relation_value(self, attrs, "season_id")
        if sport_id is not None and not Sport.objects.filter(pk=sport_id, school=school).exists():
            raise serializers.ValidationError(
                {"sport_id": "Sport must belong to the requested school."}
            )
        if season_id is not None and not Season.objects.filter(pk=season_id, school=school).exists():
            raise serializers.ValidationError(
                {"season_id": "Season must belong to the requested school."}
            )
        return attrs


class TeamCoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamCoach
        fields = ["id", "team", "user", "is_head_coach", "is_active"]

    def validate(self, attrs):
        school = _request_school(self)
        team = _relation_value(self, attrs, "team")
        user = _relation_value(self, attrs, "user")
        _require_same_school(team, school, "team")
        if user is not None and not _user_belongs_to_school(user, school):
            raise serializers.ValidationError(
                {"user": "Coach user must belong unambiguously to the requested school."}
            )
        return attrs


class TeamRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamRoster
        fields = ["id", "team", "student", "joined_at", "left_at"]

    def validate(self, attrs):
        school = _request_school(self)
        _require_same_school(_relation_value(self, attrs, "team"), school, "team")
        _require_same_school(_relation_value(self, attrs, "student"), school, "student")
        return attrs


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "name", "address", "notes"]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "team",
            "facility",
            "event_type",
            "title",
            "starts_at",
            "ends_at",
            "opponent",
            "is_home",
            "notes",
        ]

    def validate(self, attrs):
        school = _request_school(self)
        _require_same_school(_relation_value(self, attrs, "team"), school, "team")
        _require_same_school(_relation_value(self, attrs, "facility"), school, "facility")
        return attrs


class AthleteClearanceSerializer(serializers.ModelSerializer):
    physical_is_valid = serializers.SerializerMethodField()

    class Meta:
        model = AthleteClearance
        fields = [
            "student",
            "consent_signed_at",
            "physical_expires_on",
            "physical_is_valid",
            "insurance_on_file",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate(self, attrs):
        school = _request_school(self)
        _require_same_school(_relation_value(self, attrs, "student"), school, "student")
        return attrs

    def get_physical_is_valid(self, obj: AthleteClearance) -> bool:
        return obj.physical_is_valid()


class AthleteEligibilitySerializer(serializers.ModelSerializer):
    is_eligible = serializers.SerializerMethodField()

    class Meta:
        model = AthleteEligibility
        fields = [
            "team",
            "student",
            "is_medically_cleared",
            "is_academically_eligible",
            "is_behaviorally_eligible",
            "is_attendance_eligible",
            "is_eligible",
            "computed_at",
        ]
        read_only_fields = ["computed_at", "is_eligible"]

    def validate(self, attrs):
        school = _request_school(self)
        _require_same_school(_relation_value(self, attrs, "team"), school, "team")
        _require_same_school(_relation_value(self, attrs, "student"), school, "student")
        return attrs

    def get_is_eligible(self, obj: AthleteEligibility) -> bool:
        return obj.is_eligible
