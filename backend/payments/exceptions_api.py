from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.billing_api.permissions import has_finance_runtime_role
from households.scoping import get_request_school_id
from payments.hold import payment_hold_response
from payments.models import PaymentExceptionStatus, PaymentSupportException


def _finance_only(user):
    return has_finance_runtime_role(user)


def _resolution_reason(request):
    reason = str(request.data.get("reason") or request.data.get("note") or "").strip()
    if len(reason) < 3:
        return None
    return reason


def _resolve_exception(*, item, user, action, reason, status_value):
    now = timezone.now()
    payload = dict(item.payload or {})
    history = list(payload.get("operator_resolution_history") or [])
    history.append(
        {
            "action": action,
            "reason": reason,
            "resolved_by_id": user.pk,
            "resolved_at": now.isoformat(),
        }
    )
    payload["operator_resolution_history"] = history
    item.payload = payload
    item.status = status_value
    item.resolved_at = now
    item.resolved_by = user
    item.save(
        update_fields=[
            "payload",
            "status",
            "resolved_at",
            "resolved_by",
            "updated_at",
        ]
    )
    return item


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_exceptions_list(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    rows = []
    for row in PaymentSupportException.objects.filter(school_id=school_id).order_by("-id"):
        resolution_history = (row.payload or {}).get("operator_resolution_history") or []
        rows.append(
            {
                "id": row.id,
                "category": row.category,
                "severity": row.severity,
                "status": row.status,
                "message": "Internal processing error. See server logs with exception ID." if row.message else "",
                "retry_count": row.retry_count,
                "gateway_event_id": row.gateway_event_id,
                "household_id": row.household_id,
                "created_at": row.created_at,
                "resolved_at": row.resolved_at,
                "resolved_by_id": row.resolved_by_id,
                "last_operator_resolution": resolution_history[-1] if resolution_history else None,
            }
        )
    return Response({"results": rows})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_exception_retry(request, exception_id: int):
    get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    # Retrying a retained gateway event can settle or refund a finance payment,
    # update saved methods, or change dispute state. Return before loading the
    # exception or event while no external provider is authorized.
    return payment_hold_response()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_exception_ignore(request, exception_id: int):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    reason = _resolution_reason(request)
    if reason is None:
        return Response(
            {"detail": "A documented reason is required to ignore a payment exception."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    item = PaymentSupportException.objects.filter(school_id=school_id, id=exception_id).first()
    if not item:
        return Response({"detail": "Exception not found."}, status=status.HTTP_404_NOT_FOUND)

    _resolve_exception(
        item=item,
        user=request.user,
        action="ignore",
        reason=reason,
        status_value=PaymentExceptionStatus.IGNORED,
    )
    return Response({"ok": True, "status": item.status})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_exception_resolve(request, exception_id: int):
    """Document a manual operational resolution without retrying a provider event."""
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    reason = _resolution_reason(request)
    if reason is None:
        return Response(
            {"detail": "A documented resolution is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    item = PaymentSupportException.objects.filter(school_id=school_id, id=exception_id).first()
    if not item:
        return Response({"detail": "Exception not found."}, status=status.HTTP_404_NOT_FOUND)

    _resolve_exception(
        item=item,
        user=request.user,
        action="resolve",
        reason=reason,
        status_value=PaymentExceptionStatus.RESOLVED,
    )
    return Response({"ok": True, "status": item.status})
