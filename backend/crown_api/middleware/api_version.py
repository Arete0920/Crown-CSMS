"""
API Version Governance Middleware.

Adds deprecation signal headers to versioned API responses.
Consumers (SDKs, frontends) should observe X-API-Deprecated-After and migrate
before that date.

Deprecation schedule (see docs/API_VERSION_POLICY.md):
    /api/v1/  →  deprecated after 2027-01-01  (18-month window from v1 GA)
"""


class APIVersionMiddleware:
    """
    Injects deprecation headers on versioned API responses.

    Does NOT block requests — informational only.
    """

    # Map path prefix → deprecation date (ISO 8601)
    _DEPRECATION_MAP: dict[str, str] = {
        "/api/v1/": "2027-01-01",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        for prefix, eol_date in self._DEPRECATION_MAP.items():
            if request.path.startswith(prefix):
                response["X-API-Deprecated-After"] = eol_date
                response["X-API-Version"] = prefix.strip("/")
                break

        return response
