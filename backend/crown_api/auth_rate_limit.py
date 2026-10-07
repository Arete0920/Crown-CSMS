import hashlib
from dataclasses import dataclass

from django.core.cache import cache


@dataclass(frozen=True)
class AuthRateLimitDecision:
    allowed: bool
    retry_after_seconds: int


def _client_ip(request) -> str:
    # REMOTE_ADDR is supplied by the application server/proxy boundary and is
    # not taken directly from a caller-controlled forwarding header.
    return str(request.META.get("REMOTE_ADDR") or "unknown").strip()


def _digest(*parts: str) -> str:
    material = "|".join(parts).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _identity_key(scope: str, request, identity: str) -> str:
    return (
        f"crown:auth-rate:{scope}:identity:"
        f"{_digest(_client_ip(request), identity.strip().lower())}"
    )


def _ip_key(scope: str, request) -> str:
    return f"crown:auth-rate:{scope}:ip:{_digest(_client_ip(request))}"


def _get_count(key: str) -> int:
    try:
        return int(cache.get(key, 0) or 0)
    except Exception:
        # A cache outage must not turn into an authentication outage.
        return 0


def _increment(key: str, window_seconds: int) -> int:
    try:
        if cache.add(key, 1, timeout=window_seconds):
            return 1
        return int(cache.incr(key))
    except Exception:
        return 0


def check_auth_rate_limit(
    request,
    *,
    scope: str,
    identity: str,
    identity_limit: int = 10,
    ip_limit: int = 50,
    window_seconds: int = 60,
) -> AuthRateLimitDecision:
    """Check recent authentication failures without counting successful logins."""
    identity_count = _get_count(_identity_key(scope, request, identity))
    ip_count = _get_count(_ip_key(scope, request))
    return AuthRateLimitDecision(
        identity_count < identity_limit and ip_count < ip_limit,
        window_seconds,
    )


def record_auth_failure(
    request,
    *,
    scope: str,
    identity: str,
    window_seconds: int = 60,
) -> None:
    """Count a failed authentication attempt against identity+IP and IP buckets."""
    _increment(_identity_key(scope, request, identity), window_seconds)
    _increment(_ip_key(scope, request), window_seconds)


def clear_auth_identity_failures(request, *, scope: str, identity: str) -> None:
    """Clear only the identity bucket after a valid login.

    The IP-wide bucket is intentionally retained so successful requests cannot
    erase evidence of credential-stuffing attempts against other identities.
    """
    try:
        cache.delete(_identity_key(scope, request, identity))
    except Exception:
        pass
