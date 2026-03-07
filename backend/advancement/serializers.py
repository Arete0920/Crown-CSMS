from rest_framework import serializers
from .models import (
    Donor,
    Campaign,
    SponsorshipPackage,
    Event,
    Ticket,
    StoreItem,
    AdvancementTransaction,
    Gift,
    Pledge,
    SponsorshipAgreement,
    TicketScan,
)


class DonorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = "__all__"


class CampaignSerializer(serializers.ModelSerializer):
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = "__all__"

    def get_progress_percent(self, obj):
        return obj.progress_percent()


class SponsorshipPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsorshipPackage
        fields = "__all__"


class EventSerializer(serializers.ModelSerializer):
    attendance_percent = serializers.SerializerMethodField()
    seats_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = "__all__"

    def get_attendance_percent(self, obj):
        return obj.attendance_percent()

    def get_seats_remaining(self, obj):
        return obj.seats_remaining()


class TicketSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source="event.name", read_only=True)

    class Meta:
        model = Ticket
        fields = "__all__"


class StoreItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreItem
        fields = "__all__"


class AdvancementTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvancementTransaction
        fields = "__all__"


# ---------------------------------------------------------------------------
# Ticket purchase input serializer
# ---------------------------------------------------------------------------

class TicketPurchaseSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    purchaser_name = serializers.CharField(max_length=255)
    purchaser_email = serializers.EmailField()


# ---------------------------------------------------------------------------
# Store purchase input serializer
# ---------------------------------------------------------------------------

class StorePurchaseSerializer(serializers.Serializer):
    item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)


# ---------------------------------------------------------------------------
# Stage 2 model serializers
# ---------------------------------------------------------------------------

class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = "__all__"


class PledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pledge
        fields = "__all__"


class SponsorshipAgreementSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source="package.name", read_only=True)

    class Meta:
        model = SponsorshipAgreement
        fields = "__all__"


class TicketScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketScan
        fields = "__all__"


# ---------------------------------------------------------------------------
# Stage 2 input serializers
# ---------------------------------------------------------------------------

class GiftCheckoutSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value="0.01")
    donor_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    campaign_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    restricted = serializers.BooleanField(default=False)
    restriction_label = serializers.CharField(max_length=255, default="", allow_blank=True)
    memo = serializers.CharField(max_length=255, default="", allow_blank=True)


class PledgeCreateSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value="0.01")
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True, default=None)
    frequency = serializers.ChoiceField(
        choices=["one_time", "monthly", "quarterly", "annual"],
        default="monthly",
    )
    donor_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    campaign_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    external_subscription_id = serializers.CharField(
        max_length=255, default="", allow_blank=True, required=False
    )


class SponsorshipCheckoutSerializer(serializers.Serializer):
    package_id = serializers.UUIDField()
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True, default=None)
    sponsor_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    campaign_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class QRCheckInSerializer(serializers.Serializer):
    qr_code = serializers.CharField(max_length=255)
