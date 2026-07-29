from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_070_enrollment_reconciliation_job_exists():
    script = _read("scripts/release/phase2_release_truth_reconciliation.ps1")
    assert "reconciliation" in script.lower()


def test_071_billing_ledger_reconciliation_jobs_and_tests_exist():
    ops_code = _read("backend/payments/reconciliation_ops.py")
    assert "auto_match_payout_batches_for_school" in ops_code

    _read("backend/payments/tests/test_bank_reconciliation.py")
    _read("backend/ledger/tests/test_revenue_integrity.py")


def test_072_idempotency_tests_for_payment_and_invoice_writes_exist():
    pay_tests = _read("backend/crown_api/tests/test_idempotency_keys.py")
    assert "idempotency_key" in pay_tests

    invoice_tests = _read("backend/applications/tests/test_admissions_endpoints.py")
    assert "idempotency" in invoice_tests.lower()


def test_073_immutable_audit_trail_tests_for_financial_mutations_exist():
    audit_contract = _read("backend/crown_api/tests/test_audit_log_contract.py")
    assert "immutable audit trail" in audit_contract.lower()

    ledger_immutability = _read("backend/ledger/tests/test_ledger_immutability.py")
    assert "immutable" in ledger_immutability.lower()


def test_074_migration_compatibility_tests_for_transitional_models_exist():
    ownership_map = _read(
        "docs/release/CANONICAL_OWNERSHIP_MAP_STUDENT_HOUSEHOLD_GUARDIAN_ENROLLMENT_20260530.md"
    )
    assert "transitional read-only" in ownership_map.lower()

    overlap_map = _read("docs/release/DUPLICATE_TRUTH_REGISTER_20260530.md")
    assert "legacy" in overlap_map.lower()
