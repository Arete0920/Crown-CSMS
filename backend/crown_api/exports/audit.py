import logging

from .models import ExportAuditLog

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_export(request, export_name: str, status_code: int = 200, school_id: str = "", row_count=None):
    """Best-effort audit logger. Must never break exports."""

    try:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            user = None

        ExportAuditLog.objects.create(
            user=user,
            export_name=export_name,
            path=getattr(request, "path", ""),
            method=getattr(request, "method", "GET"),
            status_code=int(status_code or 0),
            school_id=str(school_id or ""),
            school_override_id=str(getattr(request, "_crown_school_override_id", "") or ""),
            row_count=row_count,
            ip=_get_client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT", "") or "")[:1000],
        )
    except Exception:
        logger.error("Export audit log write failed — exports are unaffected", exc_info=True)
