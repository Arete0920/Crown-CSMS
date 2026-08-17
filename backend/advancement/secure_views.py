import logging

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.audit import audit_event
from core.permissions import CrownModulePermission
from .models import Campaign, Donor, Event, Pledge, StoreItem, Ticket, AdvancementTransaction, SponsorshipAgreement
from .models import TicketScan
from .serializers import PledgeSerializer, TicketScanSerializer, QRCheckInSerializer
from .services_stage2 import cancel_pledge, check_in_ticket_by_qr

logger = logging.getLogger(__name__)


def _require_school(request):
    school = getattr(request, "school", None)
    if school is None:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Tenant context required (X-School-Id header missing).")
    return school


@api_view(["GET"])
@permission_classes([CrownModulePermission("advancement.view")])
def advancement_summary(request):
    school = _require_school(request)
    sid = school.id
    txn_qs = AdvancementTransaction.objects.filter(school_id=sid)
    ticket_revenue = txn_qs.filter(category="event_ticket").aggregate(t=Sum("amount"))["t"] or 0
    sponsorship_revenue = txn_qs.filter(category="sponsorship").aggregate(t=Sum("amount"))["t"] or 0
    store_revenue = txn_qs.filter(category="store_purchase").aggregate(t=Sum("amount"))["t"] or 0
    donation_revenue = txn_qs.filter(category="donation").aggregate(t=Sum("amount"))["t"] or 0
    total_advancement_revenue = float(ticket_revenue) + float(sponsorship_revenue) + float(store_revenue) + float(donation_revenue)

    active_campaigns = list(
        Campaign.objects.filter(school_id=sid, status="active").values("id", "name", "goal", "raised")
    )
    for campaign in active_campaigns:
        goal = float(campaign["goal"]) if campaign["goal"] else 0
        raised = float(campaign["raised"]) if campaign["raised"] else 0
        campaign["progress_percent"] = round(raised / goal * 100, 1) if goal else 0
        campaign["id"] = str(campaign["id"])

    top_donors = list(
        Donor.objects.filter(school_id=sid, active=True)
        .order_by("-lifetime_giving")
        .values("id", "name", "email", "lifetime_giving", "donor_type")[:10]
    )
    for donor in top_donors:
        donor["id"] = str(donor["id"])
        donor["lifetime_giving"] = float(donor["lifetime_giving"])

    event_list = []
    for event in Event.objects.filter(school_id=sid, active=True):
        event_list.append({
            "id": str(event.id),
            "name": event.name,
            "date": event.date.isoformat(),
            "tickets_sold": event.tickets_sold,
            "capacity": event.capacity,
            "attendance_percent": event.attendance_percent(),
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


@api_view(["POST"])
@permission_classes([CrownModulePermission("advancement.edit")])
def pledge_cancel(request, pledge_id):
    school = _require_school(request)
    try:
        pledge = cancel_pledge(pledge_id=pledge_id, school_id=school.id)
    except Pledge.DoesNotExist:
        return Response({"detail": "Pledge not found."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        logger.exception("Pledge cancel failed")
        return Response({"detail": "Request failed."}, status=status.HTTP_400_BAD_REQUEST)
    audit_event("advancement.pledge.cancelled", user=request.user, school=school, extra={"pledge_id": str(pledge.id)})
    return Response(PledgeSerializer(pledge).data)


@api_view(["POST"])
@permission_classes([CrownModulePermission("advancement.edit")])
def qr_checkin(request):
    school = _require_school(request)
    serializer = QRCheckInSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    scan = check_in_ticket_by_qr(
        school_id=school.id,
        qr_code=serializer.validated_data["qr_code"],
        scanned_by_id=request.user.id,
    )
    audit_event(
        "advancement.qr.checkin",
        user=request.user,
        school=school,
        extra={"scan_id": str(scan.id), "result": scan.result},
    )
    return Response(TicketScanSerializer(scan).data)
