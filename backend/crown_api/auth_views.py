# backend/crown_api/auth_views.py
import uuid

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password

from crown_api.auth_models import CrownUser
from crown_api.auth_middleware import require_auth
from crown_api.jwt_utils import build_access_token, build_refresh_token, decode_refresh
from crown_api.request_parsing import parse_json_object


def _json_body(request):
    return parse_json_object(request)


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

    user = CrownUser.objects.filter(email=email, is_active=True).first()
    if not user:
        return JsonResponse({"ok": False, "error": "invalid_credentials"}, status=401)

    if not check_password(password, user.password_hash):
        return JsonResponse({"ok": False, "error": "invalid_credentials"}, status=401)

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

    res = decode_refresh(token)
    if not res.ok or not res.payload:
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    if res.payload.get("typ") != "refresh":
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    user_id = res.payload.get("sub")
    try:
        user_uuid = uuid.UUID(str(user_id))
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    user = CrownUser.objects.filter(pk=user_uuid, is_active=True).first()
    if not user:
        return JsonResponse({"ok": False, "error": "invalid_refresh"}, status=401)

    access = build_access_token(
        user_id=str(user.id),
        email=user.email,
        role=str(user.role).strip().lower(),
        school_id=str(user.school_id) if user.school_id else None,
        ttl_seconds=900,
    )
    return JsonResponse({"ok": True, "access": access})


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
