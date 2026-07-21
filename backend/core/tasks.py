"""Celery tasks for the core app."""

from crown_api.celery_app import app


@app.task(
    name="core.tasks.purge_expired_records",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def purge_expired_records(
    self,
    *,
    execute=False,
    confirmation=None,
    approved_by=None,
    tenant_id=None,
    batch_size=500,
    allow_global=False,
):
    """Preview retention by default; execute only with explicit safeguards."""
    from core.services.retention_service import (
        RetentionAuthorizationError,
        purge_expired_records as _purge,
    )

    try:
        return _purge(
            execute=execute,
            confirmation=confirmation,
            approved_by=approved_by,
            tenant_id=tenant_id,
            batch_size=batch_size,
            allow_global=allow_global,
        )
    except (RetentionAuthorizationError, ValueError):
        # Deterministic input or authorization failures cannot succeed on retry.
        raise
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)
