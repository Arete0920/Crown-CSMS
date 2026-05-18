import json
import logging
import time
import uuid

logger = logging.getLogger("crown.request")


class RequestCorrelationMiddleware:
    """Adds request correlation and tenant-aware structured request logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )
        request.correlation_id = correlation_id

        response = self.get_response(request)

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        tenant = getattr(request, "tenant", None)
        user = getattr(request, "user", None)

        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "correlation_id": correlation_id,
                    "tenant_id": str(getattr(tenant, "id", "")) if tenant else None,
                    "user_id": str(getattr(user, "id", "")) if user and getattr(user, "is_authenticated", False) else None,
                }
            )
        )

        response["X-Correlation-ID"] = correlation_id
        return response
