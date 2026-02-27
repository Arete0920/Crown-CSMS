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


class TeamCoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamCoach
        fields = ["id", "team", "user", "is_head_coach", "is_active"]


class TeamRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamRoster
        fields = ["id", "team", "student", "joined_at", "left_at"]


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

    def get_is_eligible(self, obj: AthleteEligibility) -> bool:
        return obj.is_eligible
