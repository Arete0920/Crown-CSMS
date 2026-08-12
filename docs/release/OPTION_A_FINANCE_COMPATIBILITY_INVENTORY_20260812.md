# Option A Finance Compatibility Inventory - 2026-08-12

## Decision

Canonical external money-movement authority is `payments.Payment` / `payments.Refund`.
`finance.FinancePayment` / `finance.FinanceRefund` and operational ledger payment/allocation rows are compatibility or projection surfaces only.

Legacy data structures are **not authorized for physical deletion** until the strict runtime compatibility audit passes against the target database and the remaining consumers are migrated or intentionally retained as read-only projections.

## Verified repository consumers

Repository code search against the migration baseline found 20 `FinancePayment` references and 7 `FinanceRefund` references. Relevant runtime or compatibility consumers include:

- `backend/finance/models.py` - compatibility schema.
- `backend/finance/services.py` - controlled projection/allocation/refund bridge used by canonical authority services.
- `backend/finance/api_views.py` - legacy implementation retained in source, but payment write URLs are no longer routed here.
- `backend/finance/payment_compat_api.py` - compatibility URL adapter that writes through canonical Payments authority.
- `backend/payments/authority_services.py` - canonical settlement/refund authority and controlled Finance bridge.
- `backend/payments/services.py` - compatibility/payment operational services.
- `backend/analytics/services_health.py` - finance/payment health reporting consumer.
- `backend/sandbox_demo/services.py` - sandbox demonstration data consumer.
- Finance/payment serializers, tests, migrations, and historical release documentation.

## API authority cutover

The existing compatibility URL contract remains available:

- `POST /api/finance/payments/intent/`
- `POST /api/finance/payments/<id>/settle/`
- `POST /api/finance/payments/<id>/refund/`

Those routes are bound by `backend/finance/api_urls.py` to `finance.payment_compat_api`, which creates or adopts canonical `payments.Payment` facts, settles through `payments.authority_services.settle_payment`, and creates/settles refunds through canonical `payments.Refund` authority.

Provider-backed requests remain fail closed while payment-provider selection and certification are unresolved. Manual/internal compatibility operations remain available through the canonical authority bridge.

## Data reconciliation gate

`python manage.py audit_payment_compatibility` performs a read-only comparison of canonical and compatibility payment/refund facts. It fails on:

- missing canonical-to-Finance links;
- missing compatibility records;
- school, amount, currency, or settlement-state mismatches;
- settled canonical refunds without matching settled `FinanceRefund` facts; or
- legacy-only `FinancePayment` rows.

`--school-id <uuid>` scopes the audit to one tenant. `--allow-orphans` exists only for migration inventory/reporting and must **not** be used as retirement proof.

## Retirement gate

Physical retirement of `FinancePayment`, `FinanceRefund`, or related compatibility paths requires all of the following on the exact candidate identity:

1. strict `audit_payment_compatibility` PASS on the target runtime database with zero mismatches and zero legacy-only payments;
2. exact-head automated tests and backend coverage PASS;
3. canonical runtime payment/allocation/Student Accounts/GL/refund proof PASS;
4. bank and payout reconciliation proof PASS where provider evidence exists;
5. remaining runtime consumers migrated, converted to read-only projections, or explicitly retained with a documented compatibility purpose;
6. rollback and migration recovery evidence;
7. independent review and governed merge.

Until those conditions are all proven, compatibility tables remain retained but are not canonical authority.
