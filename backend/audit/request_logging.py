"""Data-minimized automatic request auditing.

Only server-defined route templates belong in automatic audit records.
Views remain responsible for domain-specific object and authorization evidence.
"""
import logging


logger = logging.getLogger(__name__)
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
UNRESOLVED_ROUTE = "/<unresolved>"
MAX_AUDIT_ROUTE_LENGTH = 255


def request_audit_route(request, *, route_template=None):
    """Use a resolved route or an explicit server-owned label, never raw URLs."""
    if route_template is None:
        match = getattr(request, "resolver_match", None)
        route_template = getattr(match, "route", None)
    if not isinstance(route_template, str):
        return UNRESOLVED_ROUTE
    return ("/" + route_template.lstrip("/"))[:MAX_AUDIT_ROUTE_LENGTH]


def record_request_audit(request, response, *, create, route_template=None):
    """Persist minimal request evidence; report storage failure without raw data."""
    if request.method not in MUTATING_METHODS:
        return False
    try:
        create(
            user_id=getattr(getattr(request, "user", None), "id", None),
            action=request.method,
            model=request_audit_route(request, route_template=route_template),
            metadata={"status_code": response.status_code},
        )
    except Exception as exc:
        # Exception text/tracebacks can contain SQL parameters, URLs or secrets.
        logger.error(
            "Automatic request audit persistence failed",
            extra={
                "audit_event": "request_audit_write_failed",
                "audit_failure_type": type(exc).__name__,
                "audit_method": request.method,
            },
        )
        return False
    return True
