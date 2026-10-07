SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-demo-key",
    "x-csrf-token",
    "x-csrftoken",
}


def _redact_headers(headers):
    if isinstance(headers, dict):
        return {
            key: ("[Filtered]" if str(key).lower() in SENSITIVE_HEADER_NAMES else value)
            for key, value in headers.items()
        }
    return headers


def before_send(event, hint):
    """Minimize request data before telemetry leaves the CROWN runtime."""
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("data", None)
        request.pop("cookies", None)
        request.pop("query_string", None)
        if "headers" in request:
            request["headers"] = _redact_headers(request.get("headers"))

    user = event.get("user")
    if isinstance(user, dict):
        # Retain only a non-identifying internal id if one is already present.
        event["user"] = {"id": user.get("id")} if user.get("id") is not None else {}

    return event
