"""Celery tasks for the billing app."""

from crown_api.celery_app import app


@app.task(name="billing.tasks.enforce_grace_period", bind=True, max_retries=2, default_retry_delay=120)
def enforce_grace_period(self):
    """Suspend expired delinquency records one school tenant at a time."""
    try:
        from billing.services_grace import enforce_grace_period as _enforce
        from core.models import School
        from core.tenant_models import tenant_context

        results = {}
        for school in School.objects.filter(is_active=True).iterator():
            with tenant_context(school):
                results[str(school.id)] = _enforce(school_id=school.id)
        return {"schools": results, "count": len(results)}
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)
