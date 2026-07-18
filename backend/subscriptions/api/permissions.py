"""
DRF permission helpers for entitlement-gated views.

Usage:
    from subscriptions.api.permissions import RequiresEntitlement

    @api_view(["GET"])
    @permission_classes([IsAuthenticated, RequiresEntitlement("admissions.pipeline")])
    def my_view(request): ...

Note: RequiresEntitlement must be instantiated with the feature key.
Since DRF permission_classes expects classes (not instances), wrap with
a factory function or use the class-based decorator pattern shown above.

For function-based views that need declarative gates, prefer calling
EntitlementsService.assert_enabled() inside the view body.
"""
from rest_framework.permissions import BasePermission

from crown_api.tenant import get_tenant_school_id
from subscriptions.services import EntitlementsService


def RequiresEntitlement(feature_key: str):
    """
    Factory that returns a DRF BasePermission subclass gated on `feature_key`.

    Usage in permission_classes:
        permission_classes = [IsAuthenticated, RequiresEntitlement("comms.sms")]
    """

    class _RequiresEntitlement(BasePermission):
        def has_permission(self, request, view) -> bool:
            try:
                school_id = get_tenant_school_id(request, required=True)
                EntitlementsService.assert_enabled(school_id, feature_key)
                return True
            except Exception:
                return False

    _RequiresEntitlement.__name__ = f"RequiresEntitlement({feature_key!r})"
    return _RequiresEntitlement
