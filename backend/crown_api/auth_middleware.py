# backend/crown_api/auth_middleware.py
import json

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from crown_api.jwt_utils import decode_access, _b64url_decode
from crown_api.auth_models import CrownUser


def _is_crown_access_token(token: str) -> bool:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False
        payload_bytes = _b64url_decode(parts[1])
        payload = json.loads(payload_bytes.decode("utf-8"))
        return payload.get("typ") == "access"
    except Exception:
        return False


def _extract_bearer_token(auth_header: str) -> str | None:
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer":
        return None
    cleaned_token = token.strip()
    return cleaned_token or None


def _user_from_crown_payload(payload: dict):
    user_id = str(payload.get("sub") or "").strip()
    if not user_id:
        return None

    user_model = get_user_model()
    try:
        user = user_model.objects.filter(pk=user_id).first()
    except (TypeError, ValueError):
        user = None
    if user and getattr(user, "is_active", False):
        if payload.get("school_id"):
            setattr(user, "school_id", payload.get("school_id"))
        if payload.get("role"):
            setattr(user, "role", payload.get("role"))
        return user

    # Legacy fallback: /api/auth/* token flow still issues tokens for CrownUser.
    try:
        legacy_user = CrownUser.objects.filter(pk=user_id).first()
    except (TypeError, ValueError):
        return None
    if not legacy_user or not getattr(legacy_user, "is_active", False):
        return None

    if payload.get("school_id"):
        setattr(legacy_user, "school_id", payload.get("school_id"))
    if payload.get("role"):
        setattr(legacy_user, "role", payload.get("role"))

    # require_auth checks user.is_authenticated, which CrownUser does not define.
    setattr(legacy_user, "is_authenticated", True)
    return legacy_user


def authenticate_crown_access_token(token: str):
    if not _is_crown_access_token(token):
        return None

    result = decode_access(token)
    if not result.ok or not result.payload:
        raise AuthenticationFailed(result.error or "invalid_crown_access_token")

    user = _user_from_crown_payload(result.payload)
    if user is None:
        raise AuthenticationFailed("crown_access_user_not_found")

    return user, result.payload


class CrownAccessTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = _extract_bearer_token(request.META.get("HTTP_AUTHORIZATION") or "")
        if not token:
            return None
        authenticated = authenticate_crown_access_token(token)
        if authenticated is None:
            return None
        return authenticated

    def authenticate_header(self, request):
        return 'Bearer realm="api"'


class JwtAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = getattr(request, "user", None)

        token = _extract_bearer_token(request.META.get("HTTP_AUTHORIZATION") or "")
        if token:
            try:
                authenticated = authenticate_crown_access_token(token)
            except AuthenticationFailed:
                authenticated = None
            if authenticated is not None:
                user, payload = authenticated
                request.user = user
                request.auth = payload
                request.META["HTTP_AUTHORIZATION"] = ""

        return self.get_response(request)


def require_auth(view_func):
    def _wrapped(request, *args, **kwargs):
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return JsonResponse({"ok": False, "error": "Unauthorized"}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped
