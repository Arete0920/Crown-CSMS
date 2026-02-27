import uuid
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone


class ApiExceptionMiddleware:
    """
    Wraps the entire request pipeline and converts unhandled exceptions into JSON.

    Contract:
    - Always returns JSON for unhandled exceptions
    - Includes a request_id for correlation
    - In DEBUG: includes detail
    - In non-DEBUG: hides detail
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request_id on the request for use in process_exception
        request.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        
        response = self.get_response(request)
        
        # echo request id back so logs and client correlate
        try:
            response["X-Request-Id"] = request.request_id
        except (TypeError, AttributeError):
            pass  # streaming or non-standard responses may not support header assignment
        
        return response

    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        Returns a JsonResponse with error details.
        """
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        payload = {
            "ok": False,
            "error": "Internal Server Error",
            "ts": timezone.now().isoformat(),
            "request_id": request_id,
        }

        if settings.DEBUG:
            payload["detail"] = f"{type(exception).__name__}: {exception}"

        response = JsonResponse(payload, status=500)
        response["X-Request-Id"] = request_id
        return response
