import logging
import time

logger = logging.getLogger("crown.performance")

# Requests slower than this threshold are logged at WARNING level.
_SLOW_REQUEST_THRESHOLD_S = 1.0


class PerformanceMiddleware:
    """
    Adds an X-Response-Time-ms header to every HTTP response.
    Logs a WARNING for requests that exceed the slow-request threshold (P95 signal).

    - Safe for all environments
    - Does not change response body
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_s = time.perf_counter() - start
        duration_ms = duration_s * 1000.0

        # Avoid any weirdness if response is non-standard
        try:
            response["X-Response-Time-ms"] = f"{duration_ms:.2f}"
        except (TypeError, AttributeError):
            pass  # streaming or non-standard responses may not support header assignment

        if duration_s > _SLOW_REQUEST_THRESHOLD_S:
            logger.warning(
                "SLOW_REQUEST path=%s method=%s status=%s duration_ms=%.0f",
                request.path,
                request.method,
                getattr(response, "status_code", "?"),
                duration_ms,
            )

        return response
