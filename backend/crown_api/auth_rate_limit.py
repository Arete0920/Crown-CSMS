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


def _cache_key(scope: str, request, identity: str) -> str:
    material = f"{scope}|{_client_ip(request)}|{identity.strip().lower()}".encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()
    return f"crown:auth-rate:{scope}:{digest}"


def check_auth_rate_limit(
    request,
    *,
    scope: str,
    identity: str,
    limit: int = 10,
    window_seconds: int = 60,
) -> AuthRateLimitDecision:
    """Fixed-window auth abuse limiter.

    The key combines server-observed remote address with the normalized login
    identity. Raw addresses and identities are not persisted in cache keys.
    Failure to increment the cache fails closed for the current request only
    when the existing counter is already present; a cache outage itself is not
    allowed to take down authentication.
    """
    key = _cache_key(scope, request, identity)
    try:
        if cache.add(key, 1, timeout=window_seconds):
            count = 1
        else:
            count = cache.incr(key)
    except Exception:
        # Authentication availability must not depend on a cache backend.
        return AuthRateLimitDecision(True, window_seconds)

    return AuthRateLimitDecision(count <= limit, window_seconds)
