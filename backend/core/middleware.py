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
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "CROWN_DEMO_MODE", False):
            if request.method in self.MUTATING_METHODS:
                if not request.path.startswith(self.EXEMPT_PREFIXES):
                    return JsonResponse(
                        {"detail": "Writes disabled in demo mode."},
                        status=403
                    )
        return self.get_response(request)
