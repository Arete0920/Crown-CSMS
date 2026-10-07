"""Permission-preserving fail-closed targets for deferred payment routes."""

from django.http import HttpResponseNotFound
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from core.permissions import CrownModulePermission
from payments.hold import payment_hold_response

from .api import _require_school


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def authenticated_post_payment_on_hold(request, *args, **kwargs):
    """Preserve authentication, tenant context, and POST-only behavior."""

    _require_school(request)
    return payment_hold_response()


@api_view(["POST"])
@permission_classes([CrownModulePermission("advancement.view", write_code="advancement.view")])
def advancement_view_post_payment_on_hold(request, *args, **kwargs):
    """Preserve Advancement view permission, tenant context, and POST-only behavior."""

    _require_school(request)
    return payment_hold_response()


@api_view(["GET"])
@permission_classes([CrownModulePermission("advancement.view")])
def advancement_view_get_payment_on_hold(request, *args, **kwargs):
    """Preserve Advancement view permission, tenant context, and GET-only behavior."""

    _require_school(request)
    return payment_hold_response()


@api_view(["POST"])
@permission_classes([CrownModulePermission("advancement.edit", write_code="advancement.edit")])
def advancement_edit_post_payment_on_hold(request, *args, **kwargs):
    """Preserve Advancement edit permission, tenant context, and POST-only behavior."""

    _require_school(request)
    return payment_hold_response()


def provider_webhook_not_configured(request, *args, **kwargs):
    """Do not expose a provider-specific webhook while no provider is active."""

    return HttpResponseNotFound()
