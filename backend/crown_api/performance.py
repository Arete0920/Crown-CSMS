"""
Performance timing middleware for operational diagnostics.
"""
import time


class PerformanceMiddleware:
    """
    Adds X-Response-Time-ms header to all responses for performance monitoring.
    Real SaaS behavior for production diagnostics.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = round((time.time() - start) * 1000, 2)
        response["X-Response-Time-ms"] = str(duration)
        return response
