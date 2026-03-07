"""
support/tasks.py — Celery tasks for the support app.
"""
from crown_api.celery_app import app


@app.task(name="support.tasks.escalate_overdue_tickets", bind=True, max_retries=2, default_retry_delay=60)
def escalate_overdue_tickets(self):
    """Find and escalate SLA-breached tickets."""
    try:
        from support.services_escalation import escalate_overdue_tickets as _escalate
        return _escalate()
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)
