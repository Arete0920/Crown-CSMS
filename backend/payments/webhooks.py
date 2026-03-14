import hashlib
import hmac

from django.conf import settings


def verify_compuwerx_signature(raw_body: bytes, signature: str) -> bool:
    secret = getattr(settings, "COMPUWERX_WEBHOOK_SECRET", "")
    if not secret or not signature:
        return False

    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(digest, signature)
