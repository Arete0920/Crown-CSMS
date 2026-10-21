from datetime import date as _date

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from core.permissions import CrownModulePermission
from rest_framework.response import Response
from crown_api.tenant_authentication import TenantJWTAuthentication

from finance.models import FinanceInvoice, FinanceInvoiceLine, FinanceObligation, MoneyStatus
from households.scoping import get_request_school_id

from .models import InvoiceRunWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [TenantJWTAuthentication, SessionAuthentication]
_PERM = [CrownModulePermission("finance.edit", write_code="finance.edit")]


def _get_session(session_id, school_id):
    return get_object_or_404(InvoiceRunWizardSession, id=session_id, school__id=school_id)


def _parse_date(value, field_name):
    if not value:
        return None, f"{field_name} is required"
    try:
        return _date.fromisoformat(str(value)), None
    except ValueError:
        return None, f"{field_name} must be a valid ISO date (YYYY-MM-DD)"


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = InvoiceRunWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response({"session_id": str(session.id), "status": session.status}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# 2. Configure (period_start, period_end, due_date)
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
@transaction.atomic
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = get_object_or_404(
        InvoiceRunWizardSession.objects.select_for_update(), id=session_id, school_id=school_id,
    )
    if session.status in (InvoiceRunWizardSession.STATUS_COMMITTED, InvoiceRunWizardSession.STATUS_VERIFIED):
        return Response(
            {"error": "Committed or verified invoice run sessions are immutable"},
            status=status.HTTP_409_CONFLICT,
        )

    errors = []
    period_start, e = _parse_date(request.data.get("period_start"), "period_start")
    if e:
        errors.append(e)
    period_end, e = _parse_date(request.data.get("period_end"), "period_end")
    if e:
        errors.append(e)
    due_date, e = _parse_date(request.data.get("due_date"), "due_date")
    if e:
        errors.append(e)
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    if period_start and period_end and period_end < period_start:
        return Response({"error": "period_end must be on or after period_start"}, status=status.HTTP_400_BAD_REQUEST)

    session.period_start = period_start
    session.period_end = period_end
    session.due_date = due_date
    session.status = InvoiceRunWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "period_start": str(period_start),
        "period_end": str(period_end),
        "due_date": str(due_date),
    })


# ---------------------------------------------------------------------------
# 3. Load obligations
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
@transaction.atomic
def load_obligations(request, session_id):
    school_id = get_request_school_id(request)
    session = get_object_or_404(
        InvoiceRunWizardSession.objects.select_for_update(), id=session_id, school_id=school_id,
    )

    if session.status not in (
        InvoiceRunWizardSession.STATUS_CONFIGURED,
        InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED,
    ):
        return Response(
            {"error": f"Cannot load obligations from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = FinanceObligation.objects.filter(
        school_id=school_id,
        status=MoneyStatus.OPEN,
        due_date__gte=session.period_start,
        due_date__lte=session.period_end,
    )
    obligation_ids = [str(o.id) for o in qs]

    session.obligation_ids = obligation_ids
    session.status = InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "obligation_count": len(obligation_ids),
    })


# ---------------------------------------------------------------------------
# 4. Commit — create FinanceInvoice + FinanceInvoiceLine per payer
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
@transaction.atomic
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    from core.models import School
    # Serialize invoice runs for this school even when two distinct wizard
    # sessions target the same payer and period. FinanceInvoice has no
    # uniqueness constraint for that tuple, so get_or_create alone is unsafe.
    school = get_object_or_404(School.objects.select_for_update(), id=school_id)
    session = get_object_or_404(
        InvoiceRunWizardSession.objects.select_for_update(),
        id=session_id, school_id=school_id,
    )

    if session.status not in (
        InvoiceRunWizardSession.STATUS_OBLIGATIONS_LOADED,
        InvoiceRunWizardSession.STATUS_COMMITTED,
    ):
        return Response(
            {"error": f"Cannot commit from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    # A confirmed retry must preserve the original result and not rewrite the
    # session or attempt to create additional invoice lines.
    if session.status == InvoiceRunWizardSession.STATUS_COMMITTED:
        return Response({"status": session.status, **(session.commit_result or {})})

    # Revalidate the loaded snapshot under row locks at commit. An obligation
    # cannot be billed after payment or after changing out of this period.
    obligations = list(FinanceObligation.objects.select_for_update().filter(
        id__in=session.obligation_ids,
        school_id=school_id,
        status=MoneyStatus.OPEN,
        due_date__gte=session.period_start,
        due_date__lte=session.period_end,
    ))
    if len(obligations) != len(session.obligation_ids):
        return Response(
            {"error": "Selected obligations no longer belong to this school"},
            status=status.HTTP_409_CONFLICT,
        )

    # Group by payer_user_id
    by_payer: dict = {}
    for obl in obligations:
        by_payer.setdefault(obl.payer_user_id, []).append(obl)

    # An obligation already associated with another invoice/period cannot
    # be billed again through an overlapping wizard run.
    from django.db.models import F
    conflicting_lines = FinanceInvoiceLine.objects.select_for_update().filter(
        obligation_id__in=session.obligation_ids,
    ).exclude(
        invoice__school_id=school_id,
        invoice__payer_user_id=F("obligation__payer_user_id"),
        invoice__period_start=session.period_start,
        invoice__period_end=session.period_end,
    )
    if conflicting_lines.exists():
        return Response(
            {"error": "An obligation is already billed to another invoice or period"},
            status=status.HTTP_409_CONFLICT,
        )

    # Lock existing payer/period invoices and fail before modifying finalized
    # records or ambiguous duplicate invoices.
    previously = FinanceInvoice.objects.select_for_update().filter(
        school=school, payer_user_id__in=by_payer,
        period_start=session.period_start, period_end=session.period_end,
    )
    matched_payers = set()
    for existing in previously:
        if (existing.payer_user_id in matched_payers
            or existing.status not in (MoneyStatus.OPEN, MoneyStatus.DRAFT)):
            return Response(
                {"error": "Existing invoice cannot be safely updated"},
                status=status.HTTP_409_CONFLICT,
            )
        matched_payers.add(existing.payer_user_id)

    invoices_created = 0
    lines_created = 0

    with transaction.atomic():
        for payer_id, obls in by_payer.items():
            total_cents = sum(o.amount_cents for o in obls)
            invoice, inv_created = FinanceInvoice.objects.get_or_create(
                school=school,
                payer_user_id=payer_id,
                period_start=session.period_start,
                period_end=session.period_end,
                defaults={
                    "due_date": session.due_date,
                    "subtotal_cents": total_cents,
                    "total_cents": total_cents,
                    "created_by": request.user if request.user.is_authenticated else None,
                },
            )
            if inv_created:
                invoices_created += 1

            for obl in obls:
                _, line_created = FinanceInvoiceLine.objects.get_or_create(
                    invoice=invoice,
                    obligation=obl,
                    defaults={
                        "amount_cents": obl.amount_cents,
                        "description": obl.description,
                    },
                )
                if line_created:
                    lines_created += 1

            # New sessions may append lines to an existing open invoice.
            # Reconcile cached totals to the authoritative persisted lines.
            actual_total = (FinanceInvoiceLine.objects.filter(invoice=invoice)
                            .aggregate(total=Sum("amount_cents"))["total"] or 0)
            if invoice.subtotal_cents != actual_total or invoice.total_cents != actual_total:
                invoice.subtotal_cents = actual_total
                invoice.total_cents = actual_total
                invoice.save(update_fields=["subtotal_cents", "total_cents", "updated_at"])

        result = {
            "invoices_created": invoices_created,
            "lines_created": lines_created,
            "obligation_count": len(obligations),
        }
        session.commit_result = result
        session.status = InvoiceRunWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"status": session.status, **result})


# ---------------------------------------------------------------------------
# 5. Verify
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
@transaction.atomic
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = (
        get_object_or_404(
            InvoiceRunWizardSession.objects.select_for_update(), id=session_id, school_id=school_id,
        ) if request.method == "POST" else _get_session(session_id, school_id)
    )

    if session.status not in (
        InvoiceRunWizardSession.STATUS_COMMITTED,
        InvoiceRunWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Cannot verify from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    invoice_count = FinanceInvoice.objects.filter(
        school__id=school_id,
        period_start=session.period_start,
        period_end=session.period_end,
    ).count()

    if request.method == "POST" and session.status == InvoiceRunWizardSession.STATUS_COMMITTED:
        session.status = InvoiceRunWizardSession.STATUS_VERIFIED
        session.save(update_fields=["status", "updated_at"])

    return Response({
        "status": session.status,
        "invoice_count": invoice_count,
        "period_start": str(session.period_start),
        "period_end": str(session.period_end),
        "commit_result": session.commit_result,
    })
