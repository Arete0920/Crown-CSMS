# backend/crown_api/tenant_guards.py
"""
Gate 1C: Unskippable tenant enforcement guards.

Provides base classes and mixins for DRF views/viewsets to ensure
tenant enforcement cannot be bypassed by forgetting a decorator.
"""
from rest_framework.exceptions import ValidationError
from households.scoping import get_request_school_id


class TenantRequiredMixin:
    """
    Mixin for DRF ViewSets/APIViews that enforces tenant requirement.
    
    Usage:
        class MyViewSet(TenantRequiredMixin, viewsets.ModelViewSet):
            ...
    
    This ensures tenant validation happens automatically on every
    request, making it impossible to bypass by forgetting @require_tenant.
    
    Raises ValidationError (400) if tenant is missing or invalid.
    Raises NotFound (404) if school doesn't exist or cross-tenant access denied.
    """
    
    def initial(self, request, *args, **kwargs):
        """
        Override DRF's initial() to inject tenant validation before
        any action method runs. This happens AFTER authentication but
        BEFORE permission checks.
        """
        super().initial(request, *args, **kwargs)
        
        # Force tenant resolution with required=True
        # This will raise 400/404 via DRF exceptions if tenant invalid
        get_request_school_id(request, required=True)


class TenantOptionalMixin:
    """
    Mixin for DRF ViewSets/APIViews where tenant is optional but still validated.
    
    Usage:
        class MyViewSet(TenantOptionalMixin, viewsets.ModelViewSet):
            ...
    
    This validates tenant header if present, but doesn't require it.
    Useful for endpoints that can work with or without tenant context.
    """
    
    def initial(self, request, *args, **kwargs):
        """
        Override DRF's initial() to validate tenant if present.
        """
        super().initial(request, *args, **kwargs)
        
        # Validate tenant but don't require it
        # This will raise 400/404 if tenant header is invalid
        get_request_school_id(request, required=False)
