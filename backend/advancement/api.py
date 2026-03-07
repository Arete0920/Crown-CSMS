from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.utils import timezone

from core.audit import audit_event
from core.permissions import CrownModulePermission, require_permission
from households.scoping import get_request_school_id
from .models import (
    Donor, Campaign, SponsorshipPackage, Event, Ticket, StoreItem, AdvancementTransaction,
    Gift, Pledge, SponsorshipAgreement, TicketScan,
)
from .serializers import (
    DonorSerializer, CampaignSerializer, SponsorshipPackageSerializer,
    EventSerializer, TicketSerializer, StoreItemSerializer,
    AdvancementTransactionSerializer, TicketPurchaseSerializer, StorePurchaseSerializer,
    GiftSerializer, PledgeSerializer, SponsorshipAgreementSerializer, TicketScanSerializer,
    GiftCheckoutSerializer, PledgeCreateSerializer, SponsorshipCheckoutSerializer, QRCheckInSerializer,
)
from .services import (
    create_ticket_purchase, create_store_purchase,
    record_donation, create_sponsorship_sale,
)
from .services_stage2 import (
    create_gift_checkout, mark_gift_paid,
    create_pledge, cancel_pledge,
    create_sponsorship_checkout, mark_sponsorship_paid,
    check_in_ticket_by_qr,
)
from .models_stage3 import (
    Relationship, Prospect, Move,
    AlumniCohort, AlumniCohortMember,
    MembershipTier, Membership,
    Venue, SeatingMap, EventSeating, Seat, SeatHold, TicketSeat,
    SponsorshipDeliverable, SponsorImpression,
)
from .serializers_stage3 import (
    RelationshipSerializer, ProspectSerializer, MoveSerializer,
    AlumniCohortSerializer, AlumniCohortMemberSerializer,
    MembershipTierSerializer, MembershipSerializer,
    VenueSerializer, SeatingMapSerializer, EventSeatingSerializer,
    SeatSerializer, SeatHoldSerializer, TicketSeatSerializer,
    SponsorshipDeliverableSerializer, SponsorImpressionSerializer,
    TransitionStageSerializer, SeatingLayoutSerializer,
    HoldSeatsSerializer, AssignSeatSerializer, LogImpressionsSerializer,
)
from .services_stage3 import (
    transition_move_stage,
    create_or_replace_seats_from_layout,
    hold_seats,
    assign_seat_to_ticket,
    log_impressions,
)


def _require_school(request):
    school = getattr(request, "school", None)
    if school is None:
        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
    return school


# ---------------------------------------------------------------------------
# Donor ViewSet
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Campaign ViewSet
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# SponsorshipPackage ViewSet
# ---------------------------------------------------------------------------

class SponsorshipPackageViewSet(viewsets.ModelViewSet):
    serializer_class = SponsorshipPackageSerializer
    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        return SponsorshipPackage.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        instance = serializer.save(school_id=school.id)
        audit_event("advancement.sponsorship.created", user=self.request.user, school=school,
                    extra={"package_id": str(instance.id)})


# ---------------------------------------------------------------------------
# Event ViewSet
# ---------------------------------------------------------------------------

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = Event.objects.filter(school_id=school.id)
        if self.request.query_params.get("active") == "true":
            qs = qs.filter(active=True)
        return qs

    def perform_create(self, serializer):
        school = _require_school(self.request)
        instance = serializer.save(school_id=school.id)
        audit_event("advancement.event.created", user=self.request.user, school=school,
                    extra={"event_id": str(instance.id)})


# ---------------------------------------------------------------------------
# Ticket ViewSet (with check-in action)
# ---------------------------------------------------------------------------

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = Ticket.objects.filter(school_id=school.id).select_related("event")
        event_id = self.request.query_params.get("event_id")
        if event_id:
            qs = qs.filter(event_id=event_id)
        return qs

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request, pk=None):
        ticket = self.get_object()
        if ticket.checked_in:
            return Response({"detail": "Ticket already checked in."}, status=status.HTTP_409_CONFLICT)
        ticket.checked_in = True
        ticket.checked_in_at = timezone.now()
        ticket.save(update_fields=["checked_in", "checked_in_at"])
        audit_event("advancement.ticket.checkin", user=request.user,
                    school=getattr(request, "school", None),
                    extra={"ticket_id": str(ticket.id)})
        return Response({"status": "checked_in", "ticket_id": str(ticket.id)})


# ---------------------------------------------------------------------------
# StoreItem ViewSet
# ---------------------------------------------------------------------------

class StoreItemViewSet(viewsets.ModelViewSet):
    serializer_class = StoreItemSerializer
    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = StoreItem.objects.filter(school_id=school.id)
        if self.request.query_params.get("active") == "true":
            qs = qs.filter(active=True)
        return qs

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


# ---------------------------------------------------------------------------
# Purchase endpoints (functional views)
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def purchase_ticket(request):
    """
    POST /advancement/purchase/ticket/
    Body: { event_id, purchaser_name, purchaser_email }
    Creates a Ticket + AdvancementTransaction.
    """
    school = _require_school(request)
    ser = TicketPurchaseSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    try:
        event = Event.objects.get(pk=ser.validated_data["event_id"], school_id=school.id)
    except Event.DoesNotExist:
        return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        ticket = create_ticket_purchase(
            school_id=school.id,
            event=event,
            purchaser_name=ser.validated_data["purchaser_name"],
            purchaser_email=ser.validated_data["purchaser_email"],
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def purchase_store_item(request):
    """
    POST /advancement/purchase/store/
    Body: { item_id, quantity }
    Decrements inventory + creates AdvancementTransaction.
    """
    school = _require_school(request)
    ser = StorePurchaseSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    try:
        item = StoreItem.objects.get(pk=ser.validated_data["item_id"], school_id=school.id)
    except StoreItem.DoesNotExist:
        return Response({"detail": "Store item not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        txn = create_store_purchase(
            school_id=school.id,
            item=item,
            quantity=ser.validated_data["quantity"],
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(AdvancementTransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Advancement summary / dashboard feed
# ---------------------------------------------------------------------------

@require_permission("advancement.view")
def advancement_metrics(request):
    sid = get_request_school_id(request)
    donors = Donor.objects.filter(school_id=sid)
    campaigns = Campaign.objects.filter(school_id=sid)
    total_raised = donors.aggregate(total=Sum("lifetime_giving"))["total"] or 0
    return JsonResponse({
        "total_donors":     donors.count(),
        "total_raised":     float(total_raised),
        "active_campaigns": campaigns.filter(status="active").count(),
        "total_campaigns":  campaigns.count(),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def advancement_summary(request):
    """
    GET /advancement/summary/
    Full KPI summary for AdvancementDashboard.
    """
    school = _require_school(request)
    sid = school.id

    txn_qs = AdvancementTransaction.objects.filter(school_id=sid)
    ticket_revenue = txn_qs.filter(category="event_ticket").aggregate(t=Sum("amount"))["t"] or 0
    sponsorship_revenue = txn_qs.filter(category="sponsorship").aggregate(t=Sum("amount"))["t"] or 0
    store_revenue = txn_qs.filter(category="store_purchase").aggregate(t=Sum("amount"))["t"] or 0
    donation_revenue = txn_qs.filter(category="donation").aggregate(t=Sum("amount"))["t"] or 0
    total_advancement_revenue = float(ticket_revenue) + float(sponsorship_revenue) + float(store_revenue) + float(donation_revenue)

    campaigns = Campaign.objects.filter(school_id=sid)
    active_campaigns = list(
        campaigns.filter(status="active").values("id", "name", "goal", "raised")
    )
    for c in active_campaigns:
        goal = float(c["goal"]) if c["goal"] else 0
        raised = float(c["raised"]) if c["raised"] else 0
        c["progress_percent"] = round(raised / goal * 100, 1) if goal else 0
        c["id"] = str(c["id"])

    top_donors = list(
        Donor.objects.filter(school_id=sid, active=True)
        .order_by("-lifetime_giving")
        .values("id", "name", "email", "lifetime_giving", "donor_type")[:10]
    )
    for d in top_donors:
        d["id"] = str(d["id"])
        d["lifetime_giving"] = float(d["lifetime_giving"])

    events = Event.objects.filter(school_id=sid, active=True)
    event_list = []
    for e in events:
        event_list.append({
            "id": str(e.id),
            "name": e.name,
            "date": e.date.isoformat(),
            "tickets_sold": e.tickets_sold,
            "capacity": e.capacity,
            "attendance_percent": e.attendance_percent(),
        })

    return Response({
        "total_advancement_revenue": total_advancement_revenue,
        "donation_revenue": float(donation_revenue),
        "ticket_revenue": float(ticket_revenue),
        "sponsorship_revenue": float(sponsorship_revenue),
        "store_revenue": float(store_revenue),
        "total_donors": Donor.objects.filter(school_id=sid).count(),
        "active_campaigns": active_campaigns,
        "top_donors": top_donors,
        "active_events": event_list,
        "tickets_sold_total": Ticket.objects.filter(school_id=sid).count(),
        "store_items_active": StoreItem.objects.filter(school_id=sid, active=True).count(),
    })


# ---------------------------------------------------------------------------
# Stage 2: Gift ViewSet (read-only CRUD)
# ---------------------------------------------------------------------------

class GiftViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GiftSerializer
    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = Gift.objects.filter(school_id=school.id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


# ---------------------------------------------------------------------------
# Stage 2: Pledge ViewSet
# ---------------------------------------------------------------------------

class PledgeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PledgeSerializer
    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = Pledge.objects.filter(school_id=school.id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


# ---------------------------------------------------------------------------
# Stage 2: SponsorshipAgreement ViewSet
# ---------------------------------------------------------------------------

class SponsorshipAgreementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SponsorshipAgreementSerializer
    permission_classes = [CrownModulePermission("advancement.view", write_code="advancement.edit")]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = SponsorshipAgreement.objects.filter(school_id=school.id).select_related("package")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


# ---------------------------------------------------------------------------
# Stage 2: functional views — gift checkout + payment confirmation
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def gift_checkout(request):
    """
    POST /advancement/gift/checkout/
    Body: { amount, donor_id?, campaign_id?, restricted?, restriction_label?, memo? }
    Creates a pending Gift and opens a provider checkout session.
    """
    school = _require_school(request)
    ser = GiftCheckoutSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    gift = create_gift_checkout(
        school_id=school.id,
        amount=d["amount"],
        donor_id=d.get("donor_id"),
        campaign_id=d.get("campaign_id"),
        restricted=d.get("restricted", False),
        restriction_label=d.get("restriction_label", ""),
        memo=d.get("memo", ""),
    )
    return Response(GiftSerializer(gift).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def gift_mark_paid(request, gift_id):
    """
    POST /advancement/gift/<gift_id>/mark-paid/
    Confirms payment — transitions Gift pending → paid, records AdvancementTransaction.
    """
    school = _require_school(request)
    try:
        gift = mark_gift_paid(gift_id=gift_id, school_id=school.id)
    except Gift.DoesNotExist:
        return Response({"detail": "Gift not found."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(GiftSerializer(gift).data)


# ---------------------------------------------------------------------------
# Stage 2: functional views — pledge create + cancel
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pledge_create(request):
    """
    POST /advancement/pledges/create/
    Body: { total_amount, start_date, frequency?, end_date?, donor_id?, campaign_id? }
    """
    school = _require_school(request)
    ser = PledgeCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    pledge = create_pledge(
        school_id=school.id,
        total_amount=d["total_amount"],
        start_date=d["start_date"],
        end_date=d.get("end_date"),
        frequency=d.get("frequency", "monthly"),
        donor_id=d.get("donor_id"),
        campaign_id=d.get("campaign_id"),
        external_subscription_id=d.get("external_subscription_id", ""),
    )
    return Response(PledgeSerializer(pledge).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pledge_cancel(request, pledge_id):
    """
    POST /advancement/pledges/<pledge_id>/cancel/
    """
    school = _require_school(request)
    try:
        pledge = cancel_pledge(pledge_id=pledge_id, school_id=school.id)
    except Pledge.DoesNotExist:
        return Response({"detail": "Pledge not found."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(PledgeSerializer(pledge).data)


# ---------------------------------------------------------------------------
# Stage 2: functional views — sponsorship checkout + payment confirmation
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sponsorship_checkout(request):
    """
    POST /advancement/sponsorship/checkout/
    Body: { package_id, start_date, end_date?, sponsor_id?, campaign_id? }
    """
    school = _require_school(request)
    ser = SponsorshipCheckoutSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        agreement = create_sponsorship_checkout(
            school_id=school.id,
            package_id=d["package_id"],
            start_date=d["start_date"],
            end_date=d.get("end_date"),
            sponsor_id=d.get("sponsor_id"),
            campaign_id=d.get("campaign_id"),
        )
    except SponsorshipPackage.DoesNotExist:
        return Response({"detail": "Sponsorship package not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(SponsorshipAgreementSerializer(agreement).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sponsorship_mark_paid(request, agreement_id):
    """
    POST /advancement/sponsorship/<agreement_id>/mark-paid/
    Transitions SponsorshipAgreement pending → active.
    """
    school = _require_school(request)
    try:
        agreement = mark_sponsorship_paid(agreement_id=agreement_id, school_id=school.id)
    except SponsorshipAgreement.DoesNotExist:
        return Response({"detail": "Agreement not found."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(SponsorshipAgreementSerializer(agreement).data)


# ---------------------------------------------------------------------------
# Stage 2: QR check-in (body-based, distinct from URL-based TicketViewSet action)
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def qr_checkin(request):
    """
    POST /advancement/qr-checkin/
    Body: { qr_code: str }
    Creates a TicketScan audit record — result is "accepted" | "duplicate" | "invalid".
    Always returns 200 with the scan record (never 404 on invalid QR).
    """
    school = _require_school(request)
    ser = QRCheckInSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    scan = check_in_ticket_by_qr(
        school_id=school.id,
        qr_code=ser.validated_data["qr_code"],
        scanned_by_id=request.user.id if request.user else None,
    )
    audit_event(
        "advancement.qr.checkin",
        user=request.user,
        school=getattr(request, "school", None),
        extra={"scan_id": str(scan.id), "result": scan.result},
    )
    return Response(TicketScanSerializer(scan).data)


# ===========================================================================
# Stage 3: Moves Management ViewSets
# ===========================================================================

_PERM_S3 = CrownModulePermission("advancement.view", write_code="advancement.edit")


class RelationshipViewSet(viewsets.ModelViewSet):
    serializer_class = RelationshipSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        return Relationship.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


class ProspectViewSet(viewsets.ModelViewSet):
    serializer_class = ProspectSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = Prospect.objects.filter(school_id=school.id)
        if self.request.query_params.get("active") == "true":
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


class MoveViewSet(viewsets.ModelViewSet):
    serializer_class = MoveSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = Move.objects.filter(school_id=school.id).order_by("-created_at")
        if self.request.query_params.get("prospect_id"):
            qs = qs.filter(prospect_id=self.request.query_params["prospect_id"])
        return qs

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


# ===========================================================================
# Stage 3: Alumni Cohort ViewSets
# ===========================================================================

class AlumniCohortViewSet(viewsets.ModelViewSet):
    serializer_class = AlumniCohortSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        return AlumniCohort.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


class AlumniCohortMemberViewSet(viewsets.ModelViewSet):
    serializer_class = AlumniCohortMemberSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = AlumniCohortMember.objects.filter(school_id=school.id)
        if self.request.query_params.get("cohort_id"):
            qs = qs.filter(cohort_id=self.request.query_params["cohort_id"])
        return qs

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


# ===========================================================================
# Stage 3: Membership ViewSets
# ===========================================================================

class MembershipTierViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipTierSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = MembershipTier.objects.filter(school_id=school.id)
        if self.request.query_params.get("active") == "true":
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = Membership.objects.filter(school_id=school.id).select_related("tier")
        status_f = self.request.query_params.get("status")
        if status_f:
            qs = qs.filter(status=status_f)
        return qs

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


# ===========================================================================
# Stage 3: Seating ViewSets
# ===========================================================================

class VenueViewSet(viewsets.ModelViewSet):
    serializer_class = VenueSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        return Venue.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


class SeatingMapViewSet(viewsets.ModelViewSet):
    serializer_class = SeatingMapSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        return SeatingMap.objects.filter(school_id=school.id).select_related("venue")

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


class EventSeatingViewSet(viewsets.ModelViewSet):
    serializer_class = EventSeatingSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        return EventSeating.objects.filter(school_id=school.id)

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


class SeatViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SeatSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = Seat.objects.filter(school_id=school.id)
        map_id = self.request.query_params.get("seating_map_id")
        if map_id:
            qs = qs.filter(seating_map_id=map_id)
        return qs


class SeatHoldViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SeatHoldSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        return SeatHold.objects.filter(school_id=school.id)


# ===========================================================================
# Stage 3: Sponsorship Deliverable ViewSets
# ===========================================================================

class SponsorshipDeliverableViewSet(viewsets.ModelViewSet):
    serializer_class = SponsorshipDeliverableSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = SponsorshipDeliverable.objects.filter(school_id=school.id)
        agreement_id = self.request.query_params.get("agreement_id")
        if agreement_id:
            qs = qs.filter(agreement_id=agreement_id)
        return qs

    def perform_create(self, serializer):
        school = _require_school(self.request)
        serializer.save(school_id=school.id)


class SponsorImpressionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SponsorImpressionSerializer
    permission_classes = [_PERM_S3]

    def get_queryset(self):
        school = _require_school(self.request)
        qs = SponsorImpression.objects.filter(school_id=school.id).order_by("-happened_at")
        deliverable_id = self.request.query_params.get("deliverable_id")
        if deliverable_id:
            qs = qs.filter(deliverable_id=deliverable_id)
        return qs


# ===========================================================================
# Stage 3: Action endpoints
# ===========================================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def moves_transition(request):
    """
    POST /advancement/moves/transition/
    Body: { prospect_id, new_stage, action_type?, summary?, notes? }
    Inserts a Move row (history preserved). Returns the new Move record.
    """
    school = _require_school(request)
    ser = TransitionStageSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        move = transition_move_stage(
            school_id=school.id,
            prospect_id=d["prospect_id"],
            new_stage=d["new_stage"],
            user=request.user,
            action_type=d.get("action_type", "other"),
            summary=d.get("summary", ""),
            notes=d.get("notes", ""),
        )
    except Prospect.DoesNotExist:
        return Response({"detail": "Prospect not found."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    audit_event(
        "advancement.moves.transition",
        user=request.user,
        school=getattr(request, "school", None),
        extra={"move_id": str(move.id), "stage": move.stage},
    )
    return Response(MoveSerializer(move).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def seating_set_layout(request):
    """
    POST /advancement/seating/set-layout/
    Body: { seating_map_id, layout_json }
    Replaces layout_json on the map + regenerates all Seat rows.
    """
    school = _require_school(request)
    ser = SeatingLayoutSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        created = create_or_replace_seats_from_layout(
            school_id=school.id,
            seating_map_id=d["seating_map_id"],
            layout=d["layout_json"],
        )
    except SeatingMap.DoesNotExist:
        return Response({"detail": "Seating map not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response({"ok": True, "seats_created": created})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def seating_hold(request):
    """
    POST /advancement/seating/hold/
    Body: { event_id, seat_ids, email, hold_minutes? }
    Attempts to hold seats for a checkout session.
    Returns ok=True with hold details, or ok=False with message.
    """
    school = _require_school(request)
    ser = HoldSeatsSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        result = hold_seats(
            school_id=school.id,
            event_id=d["event_id"],
            seat_ids=d["seat_ids"],
            email=d["email"],
            hold_minutes=d.get("hold_minutes", 10),
        )
    except (Event.DoesNotExist, Seat.DoesNotExist) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    if not result.get("ok"):
        return Response(result, status=status.HTTP_409_CONFLICT)
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def seating_assign(request):
    """
    POST /advancement/seating/assign/
    Body: { ticket_id, seat_id }
    Assigns a purchased Ticket to a Seat (post-checkout confirmation).
    """
    school = _require_school(request)
    ser = AssignSeatSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        ts = assign_seat_to_ticket(
            school_id=school.id,
            ticket_id=d["ticket_id"],
            seat_id=d["seat_id"],
        )
    except (Ticket.DoesNotExist, Seat.DoesNotExist):
        return Response({"detail": "Ticket or Seat not found."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

    return Response(TicketSeatSerializer(ts).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sponsorship_log_impressions(request):
    """
    POST /advancement/sponsorship/impressions/log/
    Body: { deliverable_id, channel?, count?, metadata? }
    Appends a SponsorImpression record.
    """
    school = _require_school(request)
    ser = LogImpressionsSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        imp = log_impressions(
            school_id=school.id,
            deliverable_id=d["deliverable_id"],
            channel=d.get("channel", "unknown"),
            count=d.get("count", 1),
            metadata=d.get("metadata", {}),
        )
    except SponsorshipDeliverable.DoesNotExist:
        return Response({"detail": "Deliverable not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response({"ok": True, "impression_id": str(imp.id)}, status=status.HTTP_201_CREATED)

# ===========================================================================
# Stage 3.1 – Live seat availability + strict holds + purchase of held seats
# ===========================================================================

@api_view(["GET"])
@permission_classes([CrownModulePermission("advancement.view")])
def seating_availability(request):
    """GET ?event_id=<uuid> → live availability grid for buyer seat picker."""
    school = _require_school(request)
    event_id_str = request.query_params.get("event_id", "")
    if not event_id_str:
        return Response({"detail": "event_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        import uuid as _uuid
        event_id = _uuid.UUID(event_id_str)
    except ValueError:
        return Response({"detail": "Invalid event_id."}, status=status.HTTP_400_BAD_REQUEST)

    from .services_stage3_1 import build_availability_grid
    grid = build_availability_grid(school_id=school.id, event_id=event_id)
    if not grid:
        return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(grid)


@api_view(["POST"])
@permission_classes([CrownModulePermission("advancement.view")])
def seating_hold_strict(request):
    """
    POST { event_id, seat_ids: [uuid], email, hold_minutes? }
    → hold a set of seats for the given email.
    """
    school = _require_school(request)
    data = request.data
    try:
        import uuid as _uuid
        event_id = _uuid.UUID(str(data.get("event_id", "")))
        seat_ids = [_uuid.UUID(str(s)) for s in data.get("seat_ids", [])]
    except (ValueError, TypeError):
        return Response({"detail": "Invalid event_id or seat_ids."}, status=status.HTTP_400_BAD_REQUEST)

    email = data.get("email", "")
    hold_minutes = int(data.get("hold_minutes", 10))

    if not seat_ids:
        return Response({"detail": "seat_ids must be non-empty."}, status=status.HTTP_400_BAD_REQUEST)
    if not email:
        return Response({"detail": "email is required."}, status=status.HTTP_400_BAD_REQUEST)

    from .services_stage3_1 import hold_seats_strict
    result = hold_seats_strict(
        school_id=school.id,
        event_id=event_id,
        seat_ids=seat_ids,
        email=email,
        hold_minutes=hold_minutes,
    )
    if result.get("ok"):
        return Response(result, status=status.HTTP_200_OK)
    return Response(result, status=status.HTTP_409_CONFLICT)


@api_view(["POST"])
@permission_classes([CrownModulePermission("advancement.edit")])
def seating_purchase_held(request):
    """
    POST { event_id, email, purchaser_name, seat_ids: [uuid] }
    → convert active SeatHolds → Ticket + TicketSeat rows.
    """
    school = _require_school(request)
    data = request.data
    try:
        import uuid as _uuid
        event_id = _uuid.UUID(str(data.get("event_id", "")))
        seat_ids = [_uuid.UUID(str(s)) for s in data.get("seat_ids", [])]
    except (ValueError, TypeError):
        return Response({"detail": "Invalid event_id or seat_ids."}, status=status.HTTP_400_BAD_REQUEST)

    email = data.get("email", "")
    purchaser_name = data.get("purchaser_name", "")
    if not email or not purchaser_name:
        return Response({"detail": "email and purchaser_name are required."}, status=status.HTTP_400_BAD_REQUEST)

    from .services_stage3_1 import purchase_held_seats
    result = purchase_held_seats(
        school_id=school.id,
        event_id=event_id,
        email=email,
        purchaser_name=purchaser_name,
        seat_ids=seat_ids,
    )
    if result.get("ok"):
        return Response(result, status=status.HTTP_201_CREATED)
    return Response(result, status=status.HTTP_409_CONFLICT)


# ===========================================================================
# Stage 3.2 – Stripe Checkout + webhook + order status polling
# ===========================================================================

@api_view(["POST"])
@permission_classes([CrownModulePermission("advancement.view")])
def seating_checkout(request):
    """
    POST { event_id, purchaser_name, purchaser_email, seat_ids, amount_cents, currency? }
    → create Stripe Checkout session for held seats.
    """
    school = _require_school(request)
    data = request.data
    try:
        import uuid as _uuid
        event_id = _uuid.UUID(str(data.get("event_id", "")))
        seat_ids = [_uuid.UUID(str(s)) for s in data.get("seat_ids", [])]
        amount_cents = int(data.get("amount_cents", 0))
    except (ValueError, TypeError):
        return Response({"detail": "Invalid event_id, seat_ids, or amount_cents."}, status=status.HTTP_400_BAD_REQUEST)

    purchaser_name = data.get("purchaser_name", "")
    purchaser_email = data.get("purchaser_email", "")
    if not purchaser_name or not purchaser_email:
        return Response({"detail": "purchaser_name and purchaser_email are required."}, status=status.HTTP_400_BAD_REQUEST)

    from .services_stage3_2 import create_seat_checkout_session
    order = create_seat_checkout_session(
        school_id=school.id,
        event_id=event_id,
        purchaser_name=purchaser_name,
        purchaser_email=purchaser_email,
        seat_ids=seat_ids,
        amount_cents=amount_cents,
        currency=data.get("currency"),
    )
    return Response({
        "order_id": str(order.id),
        "checkout_url": order.checkout_url,
        "provider": order.provider,
        "provider_session_id": order.provider_session_id,
        "status": order.status,
    }, status=status.HTTP_201_CREATED)


def _ticket_ids_for_order(order) -> list[str]:
    """
    Return ticket UUIDs linked to fulfilled order seats.
    Used to surface wallet-pass endpoints in the status API response.
    """
    if order.status != "fulfilled":
        return []
    try:
        import uuid as _uuid
        from .models_stage3 import TicketSeat
        seat_uuids = [_uuid.UUID(str(s)) for s in (order.seat_ids or [])]
        if not seat_uuids:
            return []
        ts_qs = TicketSeat.objects.filter(
            school_id=order.school_id,
            event_id=order.event_id,
            seat_id__in=seat_uuids,
        ).values_list("ticket_id", flat=True)
        return [str(tid) for tid in ts_qs]
    except Exception:
        return []


@api_view(["GET"])
@permission_classes([CrownModulePermission("advancement.view")])
def order_status(request, order_id):
    """GET /orders/<uuid>/status/ → poll order fulfillment status."""
    from .models_stage3_2 import PendingSeatOrder
    try:
        order = PendingSeatOrder.objects.get(id=order_id, school_id=school.id)
    except PendingSeatOrder.DoesNotExist:
        return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response({
        "order_id": str(order.id),
        "status": order.status,
        "purchaser_email": order.purchaser_email,
        "seat_ids": order.seat_ids,
        "amount_cents": order.amount_cents,
        "currency": order.currency,
        "updated_at": order.updated_at.isoformat(),
        # Stage 3.4: include ticket UUIDs when fulfilled (needed by wallet pass buttons)
        "ticket_ids": _ticket_ids_for_order(order),
    })


def _create_receipt_and_queue_email(*, order, totals: dict | None, provider_payment_intent_id: str) -> None:
    """
    Internal helper – called from stripe_webhook after successful fulfillment.

    Creates a Receipt row and queues an EmailOutbox receipt email with a PDF
    attachment.  Sponsor logos are embedded as names only (server-side PDF; the
    frontend renders actual images).

    This is best-effort: any exception is caught by the caller.
    """
    from decimal import Decimal
    from .models_stage3_4 import Receipt, EventSponsorPlacement
    from .models_stage3_3 import EmailOutbox
    from .receipt_render import make_receipt_pdf_bytes, to_b64
    from advancement.models import Event, Ticket  # noqa: F811

    # Compute totals: prefer Stripe line-item data; fall back to order amount
    if totals:
        subtotal = totals["subtotal"]
        donation = totals["donation"]
        total = totals["total"]
    else:
        subtotal = (Decimal(int(order.amount_cents)) / Decimal(100)).quantize(Decimal("0.01"))
        donation = Decimal("0.00")
        total = subtotal

    # Idempotent: skip if receipt already exists for this order
    if Receipt.objects.filter(order_id=order.id).exists():
        return

    receipt_no = f"R-{str(order.id)[:8].upper()}-{int(order.updated_at.timestamp())}"

    receipt = Receipt.objects.create(
        school_id=order.school_id,
        order_id=order.id,
        event_id=order.event_id,
        purchaser_email=order.purchaser_email,
        receipt_number=receipt_no,
        subtotal=subtotal,
        donation=donation,
        total=total,
        provider=order.provider or "stripe",
        provider_payment_intent_id=provider_payment_intent_id,
    )

    # Sponsor names for receipt PDF
    placements = (
        EventSponsorPlacement.objects
        .filter(school_id=order.school_id, event_id=order.event_id)
        .select_related("sponsor")
        .order_by("sort_order")
    )
    sponsor_names = [p.sponsor.sponsor_name for p in placements if p.sponsor.is_active]

    # Seat labels for receipt
    seat_labels: list[str] = []
    from .models_stage3 import Seat, TicketSeat
    for seat_id_str in (order.seat_ids or []):
        try:
            import uuid as _uuid
            seat = Seat.objects.get(id=_uuid.UUID(str(seat_id_str)), school_id=order.school_id)
            seat_labels.append(f"{seat.section}-{seat.row}-{seat.number}")
        except Exception:
            pass

    # Event name
    event_name = str(order.event_id)
    try:
        evt = Event.objects.get(id=order.event_id, school_id=order.school_id)
        event_name = evt.name
    except Exception:
        pass

    pdf = make_receipt_pdf_bytes(
        school_name="School",           # school name not denormalised on order; use simple default
        receipt_no=receipt.receipt_number,
        event_name=event_name,
        purchaser_name=order.purchaser_name,
        purchaser_email=order.purchaser_email,
        subtotal=str(receipt.subtotal),
        donation=str(receipt.donation),
        total=str(receipt.total),
        seat_labels=seat_labels,
        sponsor_names=sponsor_names,
    )

    EmailOutbox.objects.create(
        school_id=order.school_id,
        kind="receipt_email",
        to_email=order.purchaser_email,
        subject=f"Your receipt – {event_name}",
        body_text=(
            f"Thank you for your purchase, {order.purchaser_name}.\n"
            f"Receipt #{receipt.receipt_number} is attached.\n"
            f"Total: ${receipt.total}"
        ),
        body_html=(
            f"<p>Thank you, <strong>{order.purchaser_name}</strong>.</p>"
            f"<p>Receipt <strong>#{receipt.receipt_number}</strong> is attached.</p>"
            f"<p>Total paid: <strong>${receipt.total}</strong></p>"
        ),
        attachments_json=[{
            "filename": f"receipt-{receipt.receipt_number}.pdf",
            "mime": "application/pdf",
            "content_b64": to_b64(pdf),
        }],
        status="pending",
    )


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


@csrf_exempt
def stripe_webhook(request):
    """
    POST (no auth, raw body) – receive Stripe webhook events.
    Handles: checkout.session.completed → fulfill_paid_order()
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    from django.conf import settings as _s
    from .payments.service import get_checkout_provider
    from .services_stage3_2 import already_processed_event, mark_event_processed, fulfill_paid_order
    import json

    payload = request.body
    signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    webhook_secret = getattr(_s, "STRIPE_WEBHOOK_SECRET", "")

    provider = get_checkout_provider()
    try:
        event = provider.verify_webhook(
            payload=payload,
            signature=signature,
            webhook_secret=webhook_secret,
        )
    except Exception as exc:
        return HttpResponse(f"Webhook verification failed: {exc}", status=400)

    provider_name = getattr(provider, "name", "unknown")
    event_type = event.get("type", "")
    event_id = event.get("id", "")

    # Idempotency guard
    if already_processed_event(provider=provider_name, event_id=event_id):
        return HttpResponse("already processed", status=200)

    if event_type == "checkout.session.completed":
        session_data = event.get("data", {}).get("object", event.get("data", {}))
        metadata = session_data.get("metadata", {})
        order_id_str = metadata.get("order_id", "")
        school_id_str = metadata.get("school_id", "")

        if order_id_str:
            try:
                import uuid as _uuid
                order_id = _uuid.UUID(order_id_str)
                school_id = _uuid.UUID(school_id_str) if school_id_str else None

                # ── Fetch Stripe line items for accurate donation accounting ──
                # Stripe documents retrieving line items separately post-session
                # to capture optional items the buyer may have selected. :contentReference[oaicite:0]{index=0}
                totals = None
                if hasattr(provider, "fetch_checkout_line_items"):
                    try:
                        session_id = session_data.get("id", "")
                        if session_id:
                            line_items = provider.fetch_checkout_line_items(session_id, limit=20)
                            from .stripe_helpers import compute_totals_from_line_items
                            totals = compute_totals_from_line_items(line_items)
                    except Exception:
                        totals = None   # non-fatal; receipt falls back to order.amount_cents

                order = fulfill_paid_order(order_id=order_id)
                mark_event_processed(provider=provider_name, event_id=event_id, school_id=school_id)

                # ── Receipt + email outbox ──────────────────────────────────
                try:
                    _create_receipt_and_queue_email(
                        order=order,
                        totals=totals,
                        provider_payment_intent_id=str(session_data.get("payment_intent") or ""),
                    )
                except Exception:
                    pass  # receipt creation is best-effort; fulfillment already succeeded

            except Exception as exc:
                return HttpResponse(f"Fulfillment error: {exc}", status=500)
        else:
            mark_event_processed(provider=provider_name, event_id=event_id, school_id=None)
    else:
        mark_event_processed(provider=provider_name, event_id=event_id, school_id=None)

    return HttpResponse("ok", status=200)


# ===========================================================================
# Stage 3.3 – Section pricing + best-available checkout
# ===========================================================================

@api_view(["GET", "POST"])
@permission_classes([CrownModulePermission("advancement.view")])
def event_section_prices(request, event_id):
    """
    GET  → list section prices for an event.
    POST { section, price_cents } → upsert a section price (requires advancement.edit).
    """
    school = _require_school(request)
    from .models_stage3_3 import EventSectionPrice

    if request.method == "GET":
        prices = list(
            EventSectionPrice.objects.filter(school_id=school.id, event_id=event_id)
            .values("section", "price_cents")
        )
        return Response({"event_id": str(event_id), "prices": prices})

    # POST – require write permission
    require_permission(request, "advancement.edit")
    data = request.data
    section = data.get("section", "").strip()
    price_cents_raw = data.get("price_cents", 0)
    if not section:
        return Response({"detail": "section is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        price_cents = int(price_cents_raw)
    except (TypeError, ValueError):
        return Response({"detail": "price_cents must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

    obj, created = EventSectionPrice.objects.update_or_create(
        school_id=school.id,
        event_id=event_id,
        section=section,
        defaults={"price_cents": price_cents},
    )
    return Response(
        {"section": section, "price_cents": obj.price_cents, "created": created},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([CrownModulePermission("advancement.view")])
def seating_best_available_checkout(request):
    """
    POST { event_id, purchaser_name, purchaser_email, count, preferred_sections? }
    → select best available seats + create Stripe Checkout session.
    """
    school = _require_school(request)
    data = request.data
    try:
        import uuid as _uuid
        event_id = _uuid.UUID(str(data.get("event_id", "")))
        count = int(data.get("count", 1))
    except (ValueError, TypeError):
        return Response({"detail": "Invalid event_id or count."}, status=status.HTTP_400_BAD_REQUEST)

    purchaser_name = data.get("purchaser_name", "")
    purchaser_email = data.get("purchaser_email", "")
    if not purchaser_name or not purchaser_email:
        return Response({"detail": "purchaser_name and purchaser_email are required."}, status=status.HTTP_400_BAD_REQUEST)

    preferred_sections = data.get("preferred_sections") or None
    if preferred_sections and not isinstance(preferred_sections, list):
        preferred_sections = [preferred_sections]

    from .services_stage3_3 import create_checkout_for_best_available
    result = create_checkout_for_best_available(
        school_id=school.id,
        event_id=event_id,
        purchaser_name=purchaser_name,
        purchaser_email=purchaser_email,
        count=count,
        preferred_sections=preferred_sections,
    )
    if result.get("ok"):
        return Response(result, status=status.HTTP_201_CREATED)
    return Response(result, status=status.HTTP_409_CONFLICT)


# ===========================================================================
# Stage 3.4 – Receipts, Sponsor placements, Apple Wallet, Google Wallet
# ===========================================================================

@api_view(["GET"])
@permission_classes([CrownModulePermission("advancement.view")])
def event_sponsors(request, event_id):
    """
    GET /events/<uuid:event_id>/sponsors/
    → list active sponsor placements for a given event (for pre-checkout UI tile display).
    """
    school = _require_school(request)
    import uuid as _uuid
    try:
        eid = _uuid.UUID(str(event_id))
    except (ValueError, TypeError):
        return Response({"detail": "Invalid event_id."}, status=status.HTTP_400_BAD_REQUEST)

    from .models_stage3_4 import EventSponsorPlacement

    placements = (
        EventSponsorPlacement.objects
        .filter(school_id=school.id, event_id=eid)
        .select_related("sponsor")
        .order_by("sort_order", "tier")
    )

    return Response([
        {
            "sponsor_name": p.sponsor.sponsor_name,
            "logo_url": p.sponsor.logo_url,
            "tier": p.tier,
        }
        for p in placements
        if p.sponsor.is_active
    ], status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([CrownModulePermission("advancement.view")])
def apple_wallet_pass(request, ticket_id):
    """
    GET /wallet/apple/tickets/<uuid:ticket_id>.pkpass
    → proxy to the Apple pass microservice and stream the .pkpass file.
    Returns 501 if APPLE_PASS_SERVICE_URL / cert settings are not configured.
    """
    from django.conf import settings as _s
    from django.http import HttpResponse as _HR, JsonResponse as _JR

    svc_url = getattr(_s, "APPLE_PASS_SERVICE_URL", "").strip()
    if not svc_url:
        return _JR({"ok": False, "message": "Apple Wallet not configured."}, status=501)

    school = _require_school(request)

    from advancement.models import Ticket
    from .models_stage3 import TicketSeat, Seat

    try:
        import uuid as _uuid
        t = Ticket.objects.get(id=_uuid.UUID(str(ticket_id)), school_id=school.id)
    except Exception:
        return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        ts = TicketSeat.objects.get(ticket_id=t.id, school_id=school.id)
        seat = Seat.objects.get(id=ts.seat_id, school_id=school.id)
        seat_label = f"{seat.section}-{seat.row}-{seat.number}"
    except Exception:
        seat_label = "See ticket"

    payload = {
        "serialNumber": str(t.id),
        "eventName": t.event.name,
        "ticketId": str(t.id),
        "purchaserEmail": t.purchaser_email,
        "seatLabel": seat_label,
        "qrValue": t.qr_code,
    }

    try:
        import requests as _req
        r = _req.post(svc_url, json=payload, timeout=15)
        if r.status_code != 200:
            return _JR({"ok": False, "message": f"Pass service error: {r.text[:300]}"}, status=502)
        resp = _HR(r.content, content_type="application/vnd-apple.pkpass")
        resp["Content-Disposition"] = f'attachment; filename="ticket-{t.id}.pkpass"'
        return resp
    except ImportError:
        return _JR({"ok": False, "message": "requests package required for Apple Wallet proxy."}, status=501)
    except Exception as exc:
        return _JR({"ok": False, "message": str(exc)}, status=502)


@api_view(["GET"])
@permission_classes([CrownModulePermission("advancement.view")])
def google_wallet_link(request, ticket_id):
    """
    GET /wallet/google/tickets/<uuid:ticket_id>/link/
    → returns { ok, save_url } containing a signed JWT "Add to Google Wallet" link.
    Returns 501 if GOOGLE_WALLET_ISSUER_ID / service-account JSON not configured.
    """
    from django.conf import settings as _s

    issuer_id = getattr(_s, "GOOGLE_WALLET_ISSUER_ID", "").strip()
    sa_json = getattr(_s, "GOOGLE_WALLET_SERVICE_ACCOUNT_JSON", "").strip()
    if not issuer_id or not sa_json:
        return Response({"ok": False, "message": "Google Wallet not configured."}, status=501)

    school = _require_school(request)

    from advancement.models import Ticket
    from .models_stage3 import TicketSeat, Seat

    try:
        import uuid as _uuid
        t = Ticket.objects.get(id=_uuid.UUID(str(ticket_id)), school_id=school.id)
    except Exception:
        return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        ts = TicketSeat.objects.get(ticket_id=t.id, school_id=school.id)
        seat = Seat.objects.get(id=ts.seat_id, school_id=school.id)
        seat_label = f"{seat.section}-{seat.row}-{seat.number}"
    except Exception:
        seat_label = "See ticket"

    object_id = f"{issuer_id}.ticket_{str(t.id).replace('-', '_')}"

    ticket_object_payload = {
        "genericObjects": [{
            "id": object_id,
            "classId": f"{issuer_id}.crown_event_generic",
            "state": "ACTIVE",
            "textModulesData": [
                {"header": "Event", "body": t.event.name, "id": "event"},
                {"header": "Seat", "body": seat_label, "id": "seat"},
                {"header": "Ticket ID", "body": str(t.id)[:8].upper(), "id": "tid"},
            ],
            "barcode": {"type": "QR_CODE", "value": t.qr_code},
        }]
    }

    try:
        from .google_wallet import make_google_wallet_save_url
        save_url = make_google_wallet_save_url(ticket_object_payload=ticket_object_payload)
        return Response({"ok": True, "save_url": save_url}, status=status.HTTP_200_OK)
    except Exception as exc:
        return Response({"ok": False, "message": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)