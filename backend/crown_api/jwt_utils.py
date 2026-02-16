# backend/crown_api/jwt_utils.py
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.conf import settings


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))


def _json_dumps(obj: Any) -> bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _sign(message: bytes, key: bytes) -> str:
    sig = hmac.new(key, message, hashlib.sha256).digest()
    return _b64url_encode(sig)


def encode_jwt(payload: Dict[str, Any], *, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(_json_dumps(header))
    payload_b64 = _b64url_encode(_json_dumps(payload))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature_b64 = _sign(signing_input, secret.encode("utf-8"))
    return f"{header_b64}.{payload_b64}.{signature_b64}"


@dataclass(frozen=True)
class JwtDecodeResult:
    ok: bool
    payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def decode_jwt(token: str, *, secret: str) -> JwtDecodeResult:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return JwtDecodeResult(ok=False, error="invalid_token_format")

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = _sign(signing_input, secret.encode("utf-8"))

        if not hmac.compare_digest(expected_sig, sig_b64):
            return JwtDecodeResult(ok=False, error="invalid_signature")

        payload_raw = _b64url_decode(payload_b64)
        payload = json.loads(payload_raw.decode("utf-8"))

        now = int(time.time())
        exp = payload.get("exp")
        if exp is not None and int(exp) < now:
            return JwtDecodeResult(ok=False, error="token_expired")

        return JwtDecodeResult(ok=True, payload=payload)
    except Exception:
        return JwtDecodeResult(ok=False, error="token_decode_failed")


def _now() -> int:
    return int(time.time())


def build_access_token(*, user_id: str, email: str, role: str, school_id: Optional[str], ttl_seconds: int = 900) -> str:
    iat = _now()
    payload = {
        "typ": "access",
        "sub": user_id,
        "email": email,
        "role": role,
        "school_id": school_id,
        "iat": iat,
        "exp": iat + int(ttl_seconds),
    }
    return encode_jwt(payload, secret=settings.SECRET_KEY)


def build_refresh_token(*, user_id: str, ttl_seconds: int = 60 * 60 * 24 * 7) -> str:
    """
    Stateless refresh token (phase 1). No server-side revocation yet.
    """
    iat = _now()
    payload = {
        "typ": "refresh",
        "sub": user_id,
        "iat": iat,
        "exp": iat + int(ttl_seconds),
    }
    # refresh secret derived from SECRET_KEY (separate signing key)
    secret = settings.SECRET_KEY + "|refresh"
    return encode_jwt(payload, secret=secret)


def decode_access(token: str) -> JwtDecodeResult:
    return decode_jwt(token, secret=settings.SECRET_KEY)


def decode_refresh(token: str) -> JwtDecodeResult:
    secret = settings.SECRET_KEY + "|refresh"
    return decode_jwt(token, secret=secret)
