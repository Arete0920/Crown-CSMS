"""
Celery tasks for the ledger app.

External payment processing is currently deferred. Payment-dependent scheduled
jobs therefore fail closed and perform no state mutation until a future owner
selects, implements, authorizes, and certifies a provider-specific path.
"""

from crown_api.celery_app import app
from payments.hold import PAYMENT_INTEGRATION_ON_HOLD


def _payment_hold_task_result(*, task: str) -> dict:
    return {
        "task": task,
        "status": PAYMENT_INTEGRATION_ON_HOLD["code"],
        "provider_configured": PAYMENT_INTEGRATION_ON_HOLD["provider_configured"],
        "provider": PAYMENT_INTEGRATION_ON_HOLD["provider"],
        "mutated": False,
    }


@app.task(name="ledger.tasks.run_dunning_cycle", bind=True, max_retries=3, default_retry_delay=60)
def run_dunning_cycle(self):
    """Fail closed while provider-dependent payment retry is deferred."""
    return _payment_hold_task_result(task="ledger.tasks.run_dunning_cycle")


@app.task(name="ledger.tasks.run_daily_payout_audit", bind=True, max_retries=2, default_retry_delay=300)
def run_daily_payout_audit(self):
    """Fail closed while provider payout reconciliation is deferred."""
    return _payment_hold_task_result(task="ledger.tasks.run_daily_payout_audit")
