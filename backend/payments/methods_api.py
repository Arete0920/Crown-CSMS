from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from households.scoping import get_request_school_id
from payments.access import user_can_access_household_finance
from payments.models import GatewayProvider, SavedPaymentMethod
from payments.providers import get_gateway


def _customer_reference(school_id, household_id) -> str:
    return f"school-{school_id}-household-{household_id}"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_saved_payment_methods(request, household_id):
    school_id = get_request_school_id(request, required=True)

    if not user_can_access_household_finance(request.user, household_id):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    rows = [
        {
            "id": row.id,
            "provider_method_id": row.provider_method_id,
            "method_type": row.method_type,
            "brand": row.brand,
            "last4": row.last4,
            "exp_month": row.exp_month,
            "exp_year": row.exp_year,
            "is_default": row.is_default,
            "is_active": row.is_active,
        }
        for row in SavedPaymentMethod.objects.filter(
            school_id=school_id,
            household_id=household_id,
            is_active=True,
        ).order_by("-is_default", "-id")
    ]

    return Response({"results": rows})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_method_setup(request, household_id):
    school_id = get_request_school_id(request, required=True)

    if not user_can_access_household_finance(request.user, household_id):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    provider = request.data.get("provider", GatewayProvider.COMPUWERX)
    return_url = request.data.get("return_url", "")
    gateway = get_gateway(provider)

    result = gateway.create_payment_method_setup(
        customer_reference=_customer_reference(school_id, household_id),
        return_url=return_url,
        metadata={
            "school_id": str(school_id),
            "household_id": str(household_id),
        },
    )

    if not result.ok:
        return Response({"ok": False, "error": result.error}, status=status.HTTP_502_BAD_GATEWAY)

    return Response(
        {
            "ok": True,
            "setup_id": result.setup_id,
            "setup_url": result.setup_url,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_default_payment_method(request, household_id, method_id: int):
    school_id = get_request_school_id(request, required=True)

    if not user_can_access_household_finance(request.user, household_id):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    method = SavedPaymentMethod.objects.filter(
        id=method_id,
        school_id=school_id,
        household_id=household_id,
        is_active=True,
    ).first()

    if not method:
        return Response({"detail": "Payment method not found."}, status=status.HTTP_404_NOT_FOUND)

    SavedPaymentMethod.objects.filter(
        school_id=school_id,
        household_id=household_id,
    ).update(is_default=False)

    method.is_default = True
    method.save(update_fields=["is_default", "updated_at"])

    return Response({"ok": True})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def detach_payment_method(request, household_id, method_id: int):
    school_id = get_request_school_id(request, required=True)

    if not user_can_access_household_finance(request.user, household_id):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    method = SavedPaymentMethod.objects.filter(
        id=method_id,
        school_id=school_id,
        household_id=household_id,
    ).first()

    if not method:
        return Response({"detail": "Payment method not found."}, status=status.HTTP_404_NOT_FOUND)

    gateway = get_gateway(method.provider)
    result = gateway.detach_payment_method(provider_method_id=method.provider_method_id)
    if not result.ok:
        return Response({"ok": False, "error": result.error}, status=status.HTTP_502_BAD_GATEWAY)

    method.is_active = False
    method.is_default = False
    method.save(update_fields=["is_active", "is_default", "updated_at"])

    return Response({"ok": True})
