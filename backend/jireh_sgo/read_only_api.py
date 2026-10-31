"""Read-only grantor pilot: active SGO membership, aggregate noncash data only."""
from django.db.models import Count, Q, Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SGOApplication, SGOAward, SGOMembership, SGOProgram
from .services import membership_for


def private(data):
    response = Response(data)
    response["Cache-Control"] = "private, no-store"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizations(request):
    if not request.user.is_active:
        return Response({"detail": "Active SGO account required."}, status=403)
    members = SGOMembership.objects.select_related("organization").filter(
        user=request.user, active=True, organization__active=True
    ).order_by("organization__legal_name", "organization_id")
    return private({"organizations": [
        {"id": str(member.organization_id), "name": member.organization.legal_name,
         "role": member.role} for member in members
    ], "funds_status": "NONCASH_ONLY"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def overview(request, organization_id):
    member = membership_for(request.user, organization_id)
    programs = SGOProgram.objects.filter(organization=member.organization)
    applications = SGOApplication.objects.filter(program__organization=member.organization)
    awards = SGOAward.objects.filter(
        application__program__organization=member.organization,
        status=SGOAward.COMMITTED,
    )
    counts = {row["program_id"]: row for row in applications.values("program_id").annotate(
        total=Count("id"),
        eligible=Count("id", filter=Q(eligibility=SGOApplication.ELIGIBLE)),
        unreviewed=Count("id", filter=Q(eligibility=SGOApplication.UNREVIEWED)),
    )}
    committed = {row["application__program_id"]: row["amount"] for row in awards.values(
        "application__program_id"
    ).annotate(amount=Sum("amount_cents"))}
    rows = [{
        "id": str(program.id), "name": program.name, "year": program.calendar_year,
        "source": program.funding_source, "policy_version": program.eligibility_rule_version,
        "applications": counts.get(program.id, {}).get("total", 0),
        "eligible": counts.get(program.id, {}).get("eligible", 0),
        "unreviewed": counts.get(program.id, {}).get("unreviewed", 0),
        "noncash_committed_cents": committed.get(program.id) or 0,
    } for program in programs.order_by("-calendar_year", "name", "id")]
    return private({
        "organization": {"id": str(member.organization_id), "name": member.organization.legal_name},
        "role": member.role, "programs": rows,
        "totals": {"programs": len(rows), "applications": sum(r["applications"] for r in rows),
                   "noncash_committed_cents": sum(r["noncash_committed_cents"] for r in rows)},
        "funds_status": "NONCASH_ONLY", "status": "PILOT_SOURCE_ONLY",
    })
