# backend/crown_api/auth_middleware.py
import json
from types import SimpleNamespace

from django.http import JsonResponse

from crown_api.jwt_utils import decode_access, _b64url_decode


def _is_crown_access_token(token: str) -> bool:
    """
    Quick check if this is one of our access tokens (typ=access in payload).
    Returns False if it's a SimpleJWT or other token format.
    Does NOT verify signature - just peeks at payload structure.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False
        payload_bytes = _b64url_decode(parts[1])
        payload = json.loads(payload_bytes)
        return payload.get("typ") == "access"
    except Exception:
        return False


class JwtAuthMiddleware:
    """
    Minimal JWT auth middleware:
      - Reads Authorization: Bearer <access>
      - Verifies token
      - Sets request.user with {id, email, role, school_id, is_authenticated=True}
    Does NOT block requests by default; views enforce auth via decorators/helpers.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = getattr(request, "user", None)  # preserve if already set

        auth = request.META.get("HTTP_AUTHORIZATION") or ""
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            
            #Only process tokens that are definitely ours (typ=access in payload)
            # This allows SimpleJWT and other auth systems to coexist
            if not _is_crown_access_token(token):
                return self.get_response(request)
            
            res = decode_access(token)
            if res.ok and res.payload:
                p = res.payload
                request.user = SimpleNamespace(
                    id=p.get("sub"),
                    email=p.get("email"),
                    role=p.get("role"),
                    school_id=p.get("school_id"),
                    is_authenticated=True,
                    is_active=True,
                )
                request.auth = p

        return self.get_response(request)


def require_auth(view_func):
    """
    Decorator for endpoints that require a valid JWT access token.
    """
    def _wrapped(request, *args, **kwargs):
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return JsonResponse({"ok": False, "error": "Unauthorized"}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped
