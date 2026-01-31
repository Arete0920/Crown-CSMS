import uuid
from rest_framework.exceptions import ValidationError

def require_school_id(request) -> uuid.UUID:
    raw = request.headers.get("X-School-Id")
    if not raw:
        raise ValidationError({"detail": "Missing required header: X-School-Id"})
    try:
        return uuid.UUID(raw)
    except Exception:
        raise ValidationError({"detail": "Invalid X-School-Id (must be UUID)"})
