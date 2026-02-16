import time


class PerformanceMiddleware:
    """
    Adds an X-Response-Time-ms header to every HTTP response.

    - Does not log
    - Does not change response body
    - Safe for all environments
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000.0

        # Avoid any weirdness if response is non-standard
        try:
            response["X-Response-Time-ms"] = f"{duration_ms:.2f}"
        except Exception:
            pass

        return response
