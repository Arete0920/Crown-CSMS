"""Automatic, data-minimized auditing of state-changing requests."""
from .models import AuditLog
from .request_logging import record_request_audit


class AuditMiddleware:
    """Record actor, registered route template, method and response status."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        record_request_audit(request, response, create=AuditLog.objects.create)
        return response
