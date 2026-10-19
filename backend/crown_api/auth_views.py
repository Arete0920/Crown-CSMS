# backend/crown_api/auth_views.py
import uuid
from datetime import datetime, timezone
from hashlib import sha256

from django.db import DatabaseError, IntegrityError, transaction

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password

from crown_api.auth_models import CrownUser, LegacyRefreshConsumption
from crown_api.auth_middleware import require_auth
from crown_api.auth_rate_limit import (
    AuthRateLimitBackendUnavailable,
    check_auth_rate_limit,
    clear_auth_identity_failures,
    record_auth_failure,
)
from crown_api.jwt_utils import build_access_token, build_refresh_token, decode_refresh
from crown_api.request_parsing import parse_json_object


# Perform a real password-hash check for unknown accounts so invalid-login timing
# does not trivially disclose whether an email exists.
_DUMMY_PASSWORD_HASH = make_password("crown-invalid-credential-sentinel")


def _json_body(request):
    return parse_json_object(request)


def _rate_limit_unavailable(retry_after_seconds=60):
    response = JsonResponse(
        {"ok": False, "error": "auth_temporarily_unavailable"},
        status=503,
    )
    response["Retry-After"] = str(retry_after_seconds)
    return response


def _record_failure_or_unavailable(request, *, scope, identity):
    try:
        record_auth_failure(request, scope=scope, identity=identity)
    except AuthRateLimitBackendUnavailable:
        return _rate_limit_unavailable()
    return None


@csrf_exempt
@require_POST
def login(request):
    body = _json_body(request)
    if body is None:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", ""))

    if not email or not password:
        return JsonResponse({"ok": False, "error": "missing_credentials"}, status=400)

    rate = check_auth_rate_limit(request, scope="crown-login", identity=email)
    if not rate.backend_available:
        return _rate_limit_unavailable(rate.retry_after_seconds)
    if not rate.allowed:
        response = JsonResponse({"ok": False, "error": "rate_limited"}, status=429)
        response["Retry-After"] = str(rate.retry_after_seconds)
        return response

    user = CrownUser.objects.filter(email=email, is_active=True).first()
    if not user:
        check_password(password, _DUMMY_PASSWORD_HASH)
        unavailable = _record_failure_or_unavailable(
            request, scope="crown-login", identity=email,
        )
        if unavailable is not None:
            return unavailable
        return JsonResponse({"ok": False, "error": "invalid_credentials"}, status=401)

    if not check_password(password, user.password_hash):
        unavailable = _record_failure_or_unavailable(
            request, scope="crown-login", identity=email,
        )
        if unavailable is not None:
            return unavailable
        return JsonResponse({"ok": False, "error": "invalid_credentials"}, status=401)

    clear_auth_identity_failures(request, scope="crown-login", identity=email)

    access = build_access_token(
        user_id=str(user.id),
        email=user.email,
        role=str(user.role).strip().lower(),
        school_id=str(user.school_id) if user.school_id else None,
        ttl_seconds=900,  # 15m
    )
    refresh = build_refresh_token(user_id=str(user.id), ttl_seconds=60 * 60 * 24 * 7)  # 7d

    return JsonResponse({"ok": True, "access": access, "refresh": refresh})


@csrf_exempt
@require_POST
def refresh(request):
    body = _json_body(request)
    if body is None:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    token = str(body.get("refresh", "")).strip()
    if not token:
        return JsonResponse({"ok": False, "error": "missing_refresh"}, status=400)

    rate = check_auth_rate_limit(request, scope="crown-refresh", identity=token)
    if not rate.backend_available:
        return _rate_limit_unavailable(rate.retry_after_seconds)
    if not rate.allowed:
        response = JsonResponse({"ok": False, "error": "rate_limited"}, status=429)
        response["Retry-After"] = str(rate.retry_after_seconds)
        return response

    res = decode_refresh(token)
    if not res.ok or not res.payload:
        unavailable = _record_failure_or_unavailable(
            request, scope="crown-refresh", identity=token,
        )
        if unavailable is not None:
            return unavailable
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    if not isinstance(res.payload, dict):
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    if res.payload.get("typ") != "refresh":
        unavailable = _record_failure_or_unavailable(
            request, scope="crown-refresh", identity=token,
        )
        if unavailable is not None:
            return unavailable
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    user_id = res.payload.get("sub")
    try:
        user_uuid = uuid.UUID(str(user_id))
    except Exception:
        unavailable = _record_failure_or_unavailable(
            request, scope="crown-refresh", identity=token,
        )
        if unavailable is not None:
            return unavailable
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    user = CrownUser.objects.filter(pk=user_uuid, is_active=True).first()
    if not user:
        unavailable = _record_failure_or_unavailable(
            request, scope="crown-refresh", identity=token,
        )
        if unavailable is not None:
            return unavailable
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    # The signed legacy refresh must have a bounded expiry. Older issued
    # tokens have no jti; the SHA-256 digest still gives them replay identity.
    exp = res.payload.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, int):
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)
    try:
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)
    if expires_at <= datetime.now(timezone.utc):
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    # Preserve the existing stateless refresh contract until schema and clients
    # have independently passed the reviewed activation process.
    from django.conf import settings
    if not settings.CROWN_LEGACY_REFRESH_ONE_USE_ENABLED:
        access = build_access_token(
            user_id=str(user.id), email=user.email,
            role=str(user.role).strip().lower(),
            school_id=str(user.school_id) if user.school_id else None,
            ttl_seconds=900,
        )
        clear_auth_identity_failures(request, scope="crown-refresh", identity=token)
        return JsonResponse({"ok": True, "access": access})

    try:
        with transaction.atomic():
            # Lock the user so deactivation, role and school changes cannot
            # race credential issuance. The unique digest arbitrates replay.
            user = CrownUser.objects.select_for_update().get(pk=user_uuid, is_active=True)
            # Store only the digest, never the bearer token itself.
            LegacyRefreshConsumption.objects.create(
                user=user,
                token_digest=sha256(token.encode("utf-8")).hexdigest(),
                expires_at=expires_at,
            )
            access = build_access_token(
                user_id=str(user.id),
                email=user.email,
                role=str(user.role).strip().lower(),
                school_id=str(user.school_id) if user.school_id else None,
                ttl_seconds=900,
            )
            replacement = build_refresh_token(user_id=str(user.id))
    except CrownUser.DoesNotExist:
        unavailable = _record_failure_or_unavailable(
            request, scope="crown-refresh", identity=token,
        )
        if unavailable is not None:
            return unavailable
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)
    except IntegrityError:
        unavailable = _record_failure_or_unavailable(
            request, scope="crown-refresh", identity=token,
        )
        if unavailable is not None:
            return unavailable
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)
    except DatabaseError:
        # Never issue an access credential when replay persistence fails.
        return _rate_limit_unavailable()

    clear_auth_identity_failures(request, scope="crown-refresh", identity=token)
    return JsonResponse({"ok": True, "access": access, "refresh": replacement})


@require_GET
@require_auth
def me(request):
    u = request.user
    return JsonResponse(
        {
            "ok": True,
            "user": {
                "id": getattr(u, "id", None),
                "email": getattr(u, "email", None),
                "role": getattr(u, "role", None),
                "school_id": getattr(u, "school_id", None),
            },
        }
    )
