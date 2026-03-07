"""
Celery tasks for the ledger app.
Thin wrappers that call service-layer functions so they can be run via Celery beat.
"""
from crown_api.celery_app import app


@app.task(name="ledger.tasks.run_dunning_cycle", bind=True, max_retries=3, default_retry_delay=60)
def run_dunning_cycle(self):
    """Process all overdue failed-payment retry records."""
    try:
        from ledger.services_dunning import process_failed_payments

        result = process_failed_payments()
        return result
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)


@app.task(name="ledger.tasks.run_daily_payout_audit", bind=True, max_retries=2, default_retry_delay=300)
def run_daily_payout_audit(self):
    """Record the previous day's payout audit snapshot for all active schools."""
    try:
        import datetime
        from core.models import School
        from ledger.services_reconciliation import record_daily_payout_audit

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        school_ids = School.objects.values_list("id", flat=True)
        results = {}
        for school_id in school_ids:
            # processor_transactions is [] until real processor API is wired
            audit = record_daily_payout_audit(
                school_id=school_id,
                audit_date=yesterday,
                processor_transactions=[],
            )
            results[str(school_id)] = audit.id
        return results
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)
