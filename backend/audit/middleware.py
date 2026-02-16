"""
Audit middleware for automatic logging of state-changing requests.
"""
from .models import AuditLog


class AuditMiddleware:
    """
    Logs POST, PUT, PATCH, DELETE requests automatically.
    Provides production accountability and compliance foundation.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            try:
                AuditLog.objects.create(
                    user_id=getattr(request.user, "id", None) if hasattr(request, "user") else None,
                    action=request.method,
                    model=request.path,
                    metadata={
                        "status_code": response.status_code
                    }
                )
            except Exception:
                # Don't break requests if audit logging fails
                pass

        return response
