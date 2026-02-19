from django.conf import settings
from django.http import JsonResponse

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
        "/api/v1/billing/payments/",    # Lane 2: payment record + apply
        "/api/v1/ledger/accounts/ensure/",  # Lane 2: ensure ledger account
        "/api/v1/ledger/charges/",      # Lane 2: create charge
        "/api/v1/ledger/payments/",     # Lane 2: record + allocate payment
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
                is_exempt = (
                    path.startswith(self.EXEMPT_PREFIXES)
                    or any(path.endswith(s) for s in self.EXEMPT_SUFFIXES)
                )
                if not is_exempt:
                    return JsonResponse(
                        {"detail": "Writes disabled in demo mode."},
                        status=403
                    )
        return self.get_response(request)
