"""Default-off, website-only access to the existing fictional presenter school.

Not a buyer invitation, sandbox-open-session bypass, provisioning API, or
school selector. The server issues only short-lived DEV-scoped access tokens.
"""
import time
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.db import connection

from django.conf import settings
from django.core.management.base import CommandError

from core.models import UserAccount, UserRole
from crown_api.jwt_utils import encode_jwt
from .catalog import SANDBOX_PERSONAS
from .models import SandboxEvent
from .universal_demo import _owned_school
from .universal_identity import presenter_username
from .universal_runtime import require_hosted_presenter

DEMO_SCOPE = "website_presenter_v1"
DEMO_ORIGIN = "https://yellow-forest-0eecc8b0f-devcertification.eastus2.7.azurestaticapps.net"
ACCESS_SECONDS = 60 * 60

# Public viewing only; global ops, account management, payment-provider,
# external communication and ALL state-changing routes are excluded.
READ_PREFIXES = (
    "/api/system/whoami/",
    "/api/v1/dashboards/",
    "/api/v1/presenter/",
    "/api/v1/academics/",
    "/api/v1/aftercare/",
    "/api/v1/summer-camp/",
    "/api/v1/admissions/",
    "/api/v1/aid/",
    "/api/v1/finance/",
    "/api/v1/gradebook/",
    "/api/v1/aid-wizard/",
    "/api/finance/",
    "/api/ledger/accounts/",
    "/api/admissions/",
)
DISALLOWED_PATH_PARTS = frozenset({
    "ops", "platform", "payments", "webhooks", "credentials", "secrets",
    "provisioning", "export", "exports", "tokens", "api-keys",
})

def website_demo_school():
    """Read-only, fail-closed readiness check; never seeds or grants anything."""
    if getattr(settings, "CROWN_WEBSITE_DEMO_ENABLED", False) is not True:
        return None
    try:
        require_hosted_presenter(str(getattr(settings, "BUILD_SHA", "") or ""))
        school = _owned_school()
        if school is None:
            return None
        users = list(UserAccount.objects.filter(school=school).values(
            "id", "username", "is_active", "is_staff", "is_superuser",
        ))
        expected_names = {
            presenter_username(key, school.pk): key for key in SANDBOX_PERSONAS
        }
        if (len(users) != len(expected_names)
                or {u["username"] for u in users} != set(expected_names)
                or any(not u["is_active"] or u["is_staff"] or u["is_superuser"]
                       for u in users)):
            return None
        assigned = {
            (str(user_id), str(school_id), role_code)
            for user_id, school_id, role_code in UserRole.objects.filter(
                user_id__in=[u["id"] for u in users]
            ).values_list("user_id", "school_id", "role_code")
        }
        expected = {
            (str(u["id"]), str(school.pk),
             SANDBOX_PERSONAS[expected_names[u["username"]]].role_code)
            for u in users
        }
        if assigned != expected:
            return None
        return school
    except (CommandError, ValueError, TypeError):
        return None


def website_demo_rate_limit(school, role):
    """Bound issuance atomically in the existing database, without Redis."""
    if not connection.in_atomic_block:
        raise CommandError("Presenter session issuance requires a transaction.")
    # Lock one registered school row; concurrent issuers serialize across hosts.
    school.__class__.objects.select_for_update().get(pk=school.pk, is_active=True)
    recent = SandboxEvent.objects.filter(
        event="website_presenter_session_issued_v1",
        school=str(school.pk),
        occurred_at__gte=timezone.now() - timedelta(seconds=60),
    ).count()
    if recent >= 12:
        return False
    SandboxEvent.objects.create(
        event="website_presenter_session_issued_v1",
        track="school", guidance="website", persona=role,
        school=str(school.pk), tour="", route="",
    )
    return True

def issue_website_demo_session(school, role):
    """Issue an ordinary verified JWT with a separately enforced demo scope."""
    persona = SANDBOX_PERSONAS[role]
    account = UserAccount.objects.get(
        school=school, username=presenter_username(role, school.pk),
        is_active=True, is_staff=False, is_superuser=False,
    )
    now = int(time.time())
    access = encode_jwt({
        "typ": "access", "sub": str(account.pk), "email": account.email,
        "role": role, "school_id": str(school.pk), "demo_scope": DEMO_SCOPE,
        "iat": now, "exp": now + ACCESS_SECONDS,
    }, secret=settings.SECRET_KEY)
    return {
        "access": access, "school_id": str(school.pk),
        "school_name": school.name, "role": role,
        "role_code": persona.role_code, "email": account.email,
        "username": account.username, "route": persona.route,
        "guidance": "guided", "demo_scope": DEMO_SCOPE,
        "expires_in": ACCESS_SECONDS,
        "command_center": {
            "track": "school", "guidance": "guided",
            "persona": {"key": role, "name": persona.label},
            "school": {"id": str(school.pk), "name": school.name},
        },
    }


def website_demo_request_allowed(request, actor, claims):
    """Revalidate source, school, role and API scope on every demo-token call."""
    if not isinstance(claims, dict) or claims.get("demo_scope") != DEMO_SCOPE:
        return False
    school = website_demo_school()
    if school is None:
        return False
    key = claims.get("role")
    persona = SANDBOX_PERSONAS.get(key)
    if (persona is None or not isinstance(actor, UserAccount)
            or not actor.is_active or actor.is_staff or actor.is_superuser
            or actor.username != presenter_username(key, school.pk)
            or str(claims.get("sub")) != str(actor.pk)
            or str(claims.get("school_id")) != str(school.pk)):
        return False
    stored = UserAccount.objects.filter(pk=actor.pk).values(
        "school_id", "is_active", "is_staff", "is_superuser",
    ).first()
    if (stored is None or not stored["is_active"]
            or stored["is_staff"] or stored["is_superuser"]
            or str(stored["school_id"]) != str(school.pk)):
        return False
    if not UserRole.objects.filter(
        user=actor, school=school, role_code=persona.role_code
    ).exists():
        return False
    for selector in ("HTTP_X_SCHOOL_ID", "HTTP_X_CROWN_SCHOOL_ID"):
        value = request.META.get(selector)
        if value and value.lower() != str(school.pk).lower():
            return False

    path = request.path
    if not path.startswith("/api/"):
        return False
    if DISALLOWED_PATH_PARTS.intersection(path.strip("/").split("/")):
        return False
    method = request.method
    if method in {"GET", "HEAD", "OPTIONS"}:
        return any(path.startswith(prefix) for prefix in READ_PREFIXES)
    # Public website sessions are read-only. Transactional demonstration
    # remains exclusively on the separately authenticated presenter path.
    return False


class WebsitePresenterSessionGuardMiddleware:
    """Never let a loginless presenter identity cross into ordinary APIs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .buyer_workspace import hosted_buyer_mode
        if not hosted_buyer_mode():
            return self.get_response(request)

        authenticated = getattr(request, "_crown_authenticated", None)
        claims = authenticated[1] if authenticated else {}
        actor = getattr(request, "user", None)
        is_presenter = str(getattr(actor, "username", "") or "").startswith("presenter.")
        has_demo_scope = bool(isinstance(claims, dict) and claims.get("demo_scope"))
        if not (is_presenter or has_demo_scope):
            return self.get_response(request)
        try:
            allowed = website_demo_request_allowed(request, actor, claims)
        except Exception:
            allowed = False
        if not allowed:
            return JsonResponse({
                "detail": "Demonstration session is not authorized for this operation.",
                "code": "website_presenter_scope_denied",
            }, status=403)
        return self.get_response(request)
