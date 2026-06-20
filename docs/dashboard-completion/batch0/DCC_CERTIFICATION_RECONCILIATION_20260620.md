# DCC Certification Reconciliation (2026-06-20)

Status: FACTORY_RULES_FIXED_FOR_STATE_ALIGNMENT

Scope:
- Reconcile dashboard certification factory behavior with canonical state register semantics.
- Keep Dashboard Certification Center (DCC) blocked unless required proof gates are satisfied.

Why this change:
- Pre-fix loop: state register declared one certified dashboard (Release Reliability) while factory output reported `CERTIFIED=0`.
- This mismatch created repeated churn: local pass, CI pass, matrix candidate, factory blocked.

What was changed:
- Updated `scripts/dashboard_certification_factory.py` to:
  - parse JSON with UTF-8 BOM tolerance (`utf-8-sig`),
  - accept certified-equivalent decision/state pairing for workaround-governed certified dashboards,
  - support proof key alias reconciliation,
  - avoid false packet-reference failures for legacy single-file markdown evidence packets (existence gate).

Validation command:

```powershell
python scripts/dashboard_certification_factory.py \
  --manifest docs/dashboard-completion/dashboard-batch-manifest.json \
  --state audit-artifacts/dashboard-completion/state/dashboard-certification-state.json \
  --output audit-artifacts/dashboard-completion/factory/dashboard-certification-factory-report.json
```

Observed output after fix:
- `DASHBOARDS_TOTAL=40`
- `CERTIFIED=1`
- `BLOCKED=39`
- `STATUS=verification_report_not_certification`

Reconciliation result:
- Outcome B satisfied: factory/state rules were defective and are now fixed.
- DCC remains blocked (not falsely promoted) until its own proof gates are complete.

Non-claims:
- This does not certify DCC.
- This does not approve release or production GO.
