"""
Advancement Stage 3 serializers — flat file (no api/ subdirectory package).
"""
from rest_framework import serializers
from django.db.models import Sum

from .models_stage3 import (
    AlumniCohort,
    AlumniCohortMember,
    EventSeating,
    Membership,
    MembershipTier,
    Move,
    Prospect,
    Relationship,
    Seat,
    SeatHold,
    SeatingMap,
    SponsorImpression,
    SponsorshipDeliverable,
    TicketSeat,
    Venue,
)


# ---------------------------------------------------------------------------
# Model serializers (read/list)
# ---------------------------------------------------------------------------

class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relationship
        fields = "__all__"


class ProspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prospect
        fields = "__all__"


class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = "__all__"


class AlumniCohortSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = AlumniCohort
        fields = "__all__"

    def get_member_count(self, obj):
        return obj.members.count()


class AlumniCohortMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlumniCohortMember
        fields = "__all__"


class MembershipTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipTier
        fields = "__all__"


class MembershipSerializer(serializers.ModelSerializer):
    tier_name = serializers.CharField(source="tier.name", read_only=True)

    class Meta:
        model = Membership
        fields = "__all__"


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = "__all__"


class SeatingMapSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source="venue.name", read_only=True)
    seat_count = serializers.SerializerMethodField()

    class Meta:
        model = SeatingMap
        fields = "__all__"

    def get_seat_count(self, obj):
        return obj.seats.count()


class EventSeatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSeating
        fields = "__all__"


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = "__all__"


class SeatHoldSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatHold
        fields = "__all__"


class TicketSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketSeat
        fields = "__all__"


class SponsorshipDeliverableSerializer(serializers.ModelSerializer):
    impression_count = serializers.SerializerMethodField()

    class Meta:
        model = SponsorshipDeliverable
        fields = "__all__"

    def get_impression_count(self, obj):
        return obj.impressions.aggregate(total=Sum("count"))["total"] or 0


class SponsorImpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsorImpression
        fields = "__all__"


# ---------------------------------------------------------------------------
# Action input serializers
# ---------------------------------------------------------------------------

class TransitionStageSerializer(serializers.Serializer):
    prospect_id = serializers.UUIDField()
    new_stage = serializers.CharField(max_length=30)
    action_type = serializers.CharField(max_length=30, default="other", required=False)
    summary = serializers.CharField(max_length=255, default="", allow_blank=True, required=False)
    notes = serializers.CharField(default="", allow_blank=True, required=False)


class SeatingLayoutSerializer(serializers.Serializer):
    seating_map_id = serializers.UUIDField()
    layout_json = serializers.JSONField()


class HoldSeatsSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    seat_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)
    email = serializers.EmailField()
    hold_minutes = serializers.IntegerField(default=10, min_value=1, max_value=60, required=False)


class AssignSeatSerializer(serializers.Serializer):
    ticket_id = serializers.UUIDField()
    seat_id = serializers.UUIDField()


class LogImpressionsSerializer(serializers.Serializer):
    deliverable_id = serializers.UUIDField()
    channel = serializers.CharField(max_length=40, default="unknown", allow_blank=True, required=False)
    count = serializers.IntegerField(default=1, min_value=1, required=False)
    metadata = serializers.JSONField(default=dict, required=False)
