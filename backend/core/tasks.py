"""
Celery tasks for the core app.
"""
from crown_api.celery_app import app


@app.task(name="core.tasks.purge_expired_records", bind=True, max_retries=2, default_retry_delay=120)
def purge_expired_records(self):
    """Delete records that have exceeded their DataRetentionPolicy retention window."""
    try:
        from core.services.retention_service import purge_expired_records as _purge

        result = _purge()
        return result
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)
