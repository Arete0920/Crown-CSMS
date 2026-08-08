from ledger.tasks import run_daily_payout_audit, run_dunning_cycle


def test_dunning_cycle_is_fail_closed_while_payment_integration_is_on_hold():
    result = run_dunning_cycle.run()

    assert result == {
        "task": "ledger.tasks.run_dunning_cycle",
        "status": "payment_integration_on_hold",
        "provider_configured": False,
        "provider": None,
        "mutated": False,
    }


def test_daily_payout_audit_is_fail_closed_while_payment_integration_is_on_hold():
    result = run_daily_payout_audit.run()

    assert result == {
        "task": "ledger.tasks.run_daily_payout_audit",
        "status": "payment_integration_on_hold",
        "provider_configured": False,
        "provider": None,
        "mutated": False,
    }
