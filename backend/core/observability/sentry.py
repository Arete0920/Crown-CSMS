SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-demo-key",
    "x-csrf-token",
    "x-csrftoken",
    "x-admin-ops-secret",
    "x-ops-secret",
    "x-devops-secret",
    "x-crown-ops-secret",
    # URLs can carry sensitive path identifiers and query values.
    "referer",
    "referrer",
    "x-original-url",
    "x-original-uri",
    "x-rewrite-url",
    "x-forwarded-uri",
}


def _redact_headers(headers):
    if isinstance(headers, dict):
        return {
            key: ("[Filtered]" if str(key).lower() in SENSITIVE_HEADER_NAMES else value)
            for key, value in headers.items()
        }
    # Unknown header representations must never bypass privacy filtering.
    return {}


def before_send(event, hint):
    """Minimize request data before telemetry leaves the CROWN runtime."""
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("data", None)
        request.pop("cookies", None)
        request.pop("query_string", None)
        # Even without query_string, the raw URL can expose tokens or record IDs.
        request.pop("url", None)
        if "headers" in request:
            request["headers"] = _redact_headers(request.get("headers"))

    user = event.get("user")
    if isinstance(user, dict):
        # Retain only a non-identifying internal id if one is already present.
        event["user"] = {"id": user.get("id")} if user.get("id") is not None else {}

    return event
