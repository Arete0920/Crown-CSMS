"""
Centralized exception handling middleware for production stability.
"""
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


def api_exception_handler(get_response):
    """
    Middleware to catch all unhandled exceptions and return structured JSON errors.
    Eliminates raw tracebacks in production and provides consistent error responses.
    """
    def middleware(request):
        try:
            return get_response(request)
        except Exception:
            # Log the full exception for debugging
            logger.exception("Unhandled exception in %s", request.path)

            return JsonResponse({
                "ok": False,
                "error": "Internal Server Error",
                "detail": "An error occurred",
            }, status=500)
    return middleware
