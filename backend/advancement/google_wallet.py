"""
Stage 3.4 – Google Wallet JWT "Save to Wallet" link generator.

Generates a signed JWT that, when embedded in a "Add to Google Wallet" URL,
lets a buyer save a Generic Pass (event ticket shape) directly to their Google
Wallet without any additional REST provisioning.

Required settings:
    GOOGLE_WALLET_ISSUER_ID         – Issuer ID from Google Pay & Wallet Console
    GOOGLE_WALLET_SERVICE_ACCOUNT_JSON – JSON string or file path to service-account key
    GOOGLE_WALLET_BASE_URL          – "https://pay.google.com/gp/v/save/" (default)

Deps (add to requirements.txt if not present):
    PyJWT>=2.8.0
    cryptography>=42.0  (already present via Django)
"""
from __future__ import annotations

import json
import time

from django.conf import settings


def _load_service_account() -> dict:
    """Load service-account JSON from setting (raw JSON string OR file path)."""
    raw = getattr(settings, "GOOGLE_WALLET_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError("GOOGLE_WALLET_SERVICE_ACCOUNT_JSON is not configured.")
    if raw.startswith("{"):
        return json.loads(raw)
    with open(raw, "r", encoding="utf-8") as fh:
        return json.load(fh)


def make_google_wallet_save_url(*, ticket_object_payload: dict) -> str:
    """
    Sign a JWT with the service-account private key and return the Google
    Wallet "Save" URL.

    ticket_object_payload should be a dict with a top-level key like
    "genericObjects" or "eventTicketObjects", matching the Google Wallet
    JWT payload spec.
    """
    try:
        import jwt  # PyJWT
    except ImportError as exc:
        raise RuntimeError(
            "PyJWT is required for Google Wallet pass generation. "
            "Add PyJWT to requirements.txt."
        ) from exc

    sa = _load_service_account()
    private_key: str = sa["private_key"]
    client_email: str = sa["client_email"]

    now = int(time.time())
    claims = {
        "iss": client_email,
        "aud": "google",
        "typ": "savetowallet",
        "iat": now,
        "payload": ticket_object_payload,
    }

    token = jwt.encode(claims, private_key, algorithm="RS256")
    # jwt.encode returns str in PyJWT >=2.x
    if isinstance(token, bytes):
        token = token.decode("ascii")

    base = getattr(settings, "GOOGLE_WALLET_BASE_URL", "https://pay.google.com/gp/v/save/")
    if not base.endswith("/"):
        base += "/"
    return f"{base}{token}"
