# backend/core/audit.py
#
# Structured audit log helper for Crown expansion modules.
# Writes to the "crown.audit" logger — wired in settings.py LOGGING config.
# Never raises; audit failures must not break the request path.

import logging

_logger = logging.getLogger("crown.audit")


def audit_event(event: str, *, user=None, school=None, extra: dict | None = None) -> None:
    """
    Emit a structured audit log line.

    Args:
        event:  Short description string, e.g. "hr.employee.created"
        user:   UserAccount instance or None
        school: School instance or None
        extra:  Optional dict of additional key=value metadata
    """
    try:
        parts = [f"AUDIT event={event}"]
        if user is not None:
            uid = getattr(user, "pk", None) or getattr(user, "id", None) or str(user)
            parts.append(f"user={uid}")
        if school is not None:
            sid = getattr(school, "id", None) or str(school)
            parts.append(f"school={sid}")
        if extra:
            for k, v in extra.items():
                parts.append(f"{k}={v}")
        _logger.info(" | ".join(parts))
    except Exception:
        # Audit must not crash the request.
        pass
