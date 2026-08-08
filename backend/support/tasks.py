"""support/tasks.py — Celery tasks for the support app."""

from crown_api.celery_app import app


@app.task(name="support.tasks.escalate_overdue_tickets", bind=True, max_retries=2, default_retry_delay=60)
def escalate_overdue_tickets(self):
    """Find and escalate SLA-breached tickets one school tenant at a time."""
    try:
        from core.models import School
        from core.tenant_models import tenant_context
        from support.services_escalation import escalate_overdue_tickets as _escalate

        results = {}
        for school in School.objects.filter(is_active=True).iterator():
            with tenant_context(school):
                results[str(school.id)] = _escalate(school_id=school.id)
        return {"schools": results, "count": len(results)}
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)
