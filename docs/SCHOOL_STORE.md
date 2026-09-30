# Crown School Store

## Current implementation

The Finance dashboard includes a school store panel for product creation, stock adjustment, and server-priced cart quotations. Products carry a school-specific SKU, optional barcode, USD price in cents, configured tax rate in basis points, active flag, and quantity. Store endpoints require authenticated finance operators and canonical tenant resolution. The existing finance dashboard guard remains in force.

- `GET/POST /api/v1/payments/store/products/`: list (100 per page) or create.
- `PATCH /api/v1/payments/store/products/{id}/`: update price, name, SKU, barcode, tax rate, or active flag. Stock is read-only here.
- `GET/POST /api/v1/payments/store/products/{id}/stock/`: latest 100 audit entries or adjustment. POST requires integer `delta`, `reason`, and `idempotency_key`. Retry the same adjustment reference; conflicting reuse fails.
- `POST /api/v1/payments/store/quote/`: `{ "items": [{ "product_id": 1, "quantity": 2 }] }`. Product prices and taxes come from the school catalog. Duplicate products are aggregated; insufficient stock fails. Tax rounds half up per product line. Quotes are informational, do not reserve stock, and expire conceptually whenever the catalog or inventory changes.
- `POST /api/v1/payments/store/checkout/`: canonical payment hold (503); no payment, order, or inventory mutation.

Apply Payments migration 0008 before using the panel. Inventory changes use a database transaction and product row lock; production concurrency requires PostgreSQL. Initial product stock is zero and all API stock changes create immutable adjustment records. Retire products instead of deleting them. School administrators must configure applicable tax rates; this is not an automated jurisdiction tax engine.

## Remaining work before POS launch

This release is store preparation, not a completed POS. No cash sales, family charges, payment terminal sessions, orders, receipts, refunds, or online ordering are enabled.

1. Obtain the processor's supported terminal hardware and API contract, school merchant onboarding requirements, card-present pricing, credential ownership, signed notification contract, duplicate handling, refunds, and settlement/reconciliation specifications.
2. Add persistent order and line snapshots, stock reservations and expiration, cashier sessions, and explicit fulfillment states. Recalculate on checkout; never trust client prices or treat a quote as a purchase.
3. Integrate sales with canonical Payments and Finance allocations and journal posting. Payment confirmation must be verified, matched to school/merchant, amount, currency, and order, and idempotent. Authorization is not settlement. Keep each school's proceeds and records isolated.
4. Add cash tender/change, drawer closing, refund approval, immutable receipts, and daily sales/deposit reconciliation with independently verified accounting results.
5. Add store-specific cashier permissions before granting access to volunteers or students. Family charging requires guardian consent, spending caps, approved merchandise, and a supported billing obligation. Do not use stored tuition payment credentials as blanket purchasing consent.
6. Verify overselling protection on PostgreSQL, duplicate/delayed processor events, partial refunds, stock returns, failed and interrupted checkouts, terminal disconnection, cross-school attacks, and school-specific ledger/deposit totals before removing the payment hold.

Processor collection must preserve the repository's existing payment hold until the provider integration is implemented and certified. No terminal capability, settlement time, or processor revenue share is assumed by this implementation.

## Student-ID purchasing requirement

A student number or scanned school-issued barcode may identify the student at checkout, but must never authorize a charge by itself. The number is an identifier, not a secret or a payment credential. Resolve it only within the cashier's authorized school; ambiguous, inactive, or unrecognized identities must fail without exposing household balances or personal information.

Preferred student purchase flow: parent explicitly opts in, funds store credit or authorizes a limited family billing arrangement, sets daily/weekly limits and permitted categories, and receives a purchase notification. The cashier confirms the student's identity through the school's approved method; a lost badge can be revoked. The student sees only the permitted store balance, never tuition balances, payment tokens, or sibling records. Student ID alone cannot debit a saved card or bank account.

Parent purchases can use the student ID for lookup, followed by the parent's own card payment or authenticated guardian authorization. Guardian relationships must be verified in the current school. Student IDs must not appear in public receipts, URLs, or logs where unnecessary.

Prepaid store credit requires its own immutable balance ledger and reconciliation, with atomic debit, overdraft prevention, idempotent purchases, refunds to the original funding source/credit balance under policy, and clear handling of withdrawals and school departure. It is a later implementation dependency; this release has no wallet or student-ID charging endpoint. Do not represent family-account billing as a settled payment.
