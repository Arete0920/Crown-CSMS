import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("crown.audit")


class DemoWriteBlockMiddleware:
    """
    Blocks all mutating HTTP methods when CROWN_DEMO_MODE=True.
    Auth/token endpoints are exempt so login still works in demo mode.
    """

    MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # Paths that must remain writable even in demo mode (auth, health, key admin actions)
    EXEMPT_PREFIXES = (
        "/api/dev/token",
        "/api/token",
        "/api/v1/auth",
        "/api/v1/health",
        "/api/admissions/enroll/",
        "/api/v1/billing/payments/",  # Lane 2: payment record + apply
        "/api/v1/ledger/accounts/ensure/",  # Lane 2: ensure ledger account
        "/api/v1/ledger/charges/",  # Lane 2: create charge
        "/api/v1/ledger/payments/",  # Lane 2: record + allocate payment
    )

    # Path suffixes that must remain writable in demo mode (used when UUID is in the path)
    EXEMPT_SUFFIXES = (
        "/attendance/",  # Lane 3: teacher attendance submit
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "CROWN_DEMO_MODE", False):
            if request.method in self.MUTATING_METHODS:
                path = request.path
                is_exempt = path.startswith(self.EXEMPT_PREFIXES) or any(
                    path.endswith(s) for s in self.EXEMPT_SUFFIXES
                )
                if not is_exempt:
                    return JsonResponse(
                        {"detail": "Writes disabled in demo mode."},
                        status=403,
                    )
        return self.get_response(request)


class TenantIsolationMiddleware(MiddlewareMixin):
    EXEMPT_PATHS = [
        "/api/health/",
        "/api/schema/",
        "/api/docs/",
        "/admin/",
        "/api/auth/",
    ]

    def process_request(self, request):
        request.tenant_school = None
        if not request.user.is_authenticated:
            return None
        if request.user.is_superuser:
            return None
        for path in self.EXEMPT_PATHS:
            if request.path.startswith(path):
                return None
        try:
            request.tenant_school = request.user.profile.school
        except AttributeError:
            pass
        return None


class TenantQuerySetMixin:
    tenant_field = "school"

    def get_queryset(self):
        qs = super().get_queryset()
        school = getattr(self.request, "tenant_school", None)
        if school is None:
            if self.request.user.is_superuser:
                return qs
            return qs.none()
        return qs.filter(**{self.tenant_field: school})


class AuditLogMixin:
    def perform_create(self, serializer):
        instance = serializer.save()
        self._audit_log("CREATE", instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._audit_log("UPDATE", instance)

    def perform_destroy(self, instance):
        self._audit_log("DESTROY", instance)
        instance.delete()

    def _audit_log(self, action, instance):
        school = getattr(self.request, "tenant_school", None)
        logger.info(
            "AUDIT | action=%s | model=%s | pk=%s | school=%s | user=%s | ip=%s",
            action,
            instance.__class__.__name__,
            instance.pk,
            school.id if school else "superuser",
            self.request.user.id,
            self._get_client_ip(),
        )

    def _get_client_ip(self):
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR", "unknown")
