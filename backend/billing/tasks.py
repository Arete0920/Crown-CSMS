"""
Celery tasks for the billing app.
"""
from crown_api.celery_app import app


@app.task(name="billing.tasks.enforce_grace_period", bind=True, max_retries=2, default_retry_delay=120)
def enforce_grace_period(self):
    """Suspend households whose grace period has expired."""
    try:
        from billing.services_grace import enforce_grace_period as _enforce

        result = _enforce()
        return result
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)
