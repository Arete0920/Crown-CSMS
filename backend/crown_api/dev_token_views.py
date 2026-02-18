"""
Demo-only dev token endpoint (fail-closed).

Provides deterministic JWT tokens for local development without password typing.
Hard guards: CROWN_DEMO_MODE=true, localhost only, X-Demo-Key header required.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework_simplejwt.tokens import RefreshToken


def _demo_fail(msg="Not Found", status=404):
    """Fail-closed: return 404 for all unauthorized requests."""
    return JsonResponse({"detail": msg}, status=status)


def _is_local_request(request) -> bool:
    """Check if request originates from localhost (127.0.0.1 or ::1)."""
    ip = request.META.get("REMOTE_ADDR", "")
    host = request.get_host().split(":")[0]
    return ip in ("127.0.0.1", "::1") or host in ("localhost", "127.0.0.1")


@csrf_exempt
@require_POST
def dev_token(request):
    """
    POST /api/dev/token/
    
    Returns deterministic JWT for demo user (fail-closed outside demo mode).
    
    Guards:
    - CROWN_DEMO_MODE=true required
    - Must be localhost request
    - X-Demo-Key header must match CROWN_DEMO_KEY
    
    Returns:
    {
        "access": "JWT token",
        "school_id": "demo school UUID",
        "user": {"username": "head@crown-demo.local"}
    }
    """
    # 1) Must be demo mode
    demo_mode = getattr(settings, "CROWN_DEMO_MODE", False)
    import sys
    print(f"DEBUG: CROWN_DEMO_MODE={demo_mode} (type={type(demo_mode).__name__})", file=sys.stderr)
    if not demo_mode:
        return _demo_fail("Demo mode not enabled")

    # 2) Must be local
    if not _is_local_request(request):
        return _demo_fail()

    # 3) Must present demo key
    expected = getattr(settings, "CROWN_DEMO_KEY", "")
    provided = request.headers.get("X-Demo-Key", "")
    if not expected or provided != expected:
        return _demo_fail()

    # 4) Deterministic demo user
    username = "head@crown-demo.local"
    U = get_user_model()
    user = U.objects.filter(username=username).first()
    if not user or not user.is_active:
        return JsonResponse({"detail": "Demo user missing/inactive"}, status=500)

    # 5) Mint JWT using SimpleJWT
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    # 6) Deterministic demo school ID (single source of truth)
    demo_school_id = getattr(settings, "CROWN_DEMO_SCHOOL_ID", "19801b59-8c05-4c84-9312-5d792e4e839d")

    return JsonResponse(
        {
            "access": access,
            "school_id": demo_school_id,
            "user": {"username": user.username},
        },
        status=200,
    )
