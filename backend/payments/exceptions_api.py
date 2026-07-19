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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_exceptions_list(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    rows = [
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
        }
        for row in PaymentSupportException.objects.filter(school_id=school_id).order_by("-id")
    ]
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

    item = PaymentSupportException.objects.filter(school_id=school_id, id=exception_id).first()
    if not item:
        return Response({"detail": "Exception not found."}, status=status.HTTP_404_NOT_FOUND)

    item.status = PaymentExceptionStatus.IGNORED
    item.resolved_at = timezone.now()
    item.resolved_by = request.user
    item.save(update_fields=["status", "resolved_at", "resolved_by", "updated_at"])

    return Response({"ok": True})
