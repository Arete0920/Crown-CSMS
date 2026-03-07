"""
analytics/tasks.py — Celery tasks for the analytics app.
"""
from crown_api.celery_app import app


@app.task(name="analytics.tasks.refresh_all_health_scores", bind=True, max_retries=2, default_retry_delay=120)
def refresh_all_health_scores(self):
    """Recompute and persist CustomerHealth for every active school."""
    try:
        from core.models import School
        from analytics.services_health import upsert_customer_health

        school_ids = School.objects.values_list("id", flat=True)
        results = {}
        for school_id in school_ids:
            record = upsert_customer_health(school_id)
            results[str(school_id)] = record.overall_score
        return results
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)
