# Canonical Ownership Map - Invoice / Payment / Ledger

**Option A reconciliation:** 2026-08-11  
**Repository:** `tcmegahan/Crown-CSMS`  
**Migration rule:** COPY/MIGRATE FIRST -> COMPARE -> PROVE -> CUT OVER -> RETIRE LAST

This document supersedes the May 30 payment/refund ownership assignment for the Option A replacement architecture. It does not authorize legacy deletion or payment-provider activation.

## Canonical Owners

| Domain Entity / Responsibility | Canonical Owner | Current Option A Write Authority | Compatibility During Migration | Notes |
| --- | --- | --- | --- | --- |
| Charge / Credit / Adjustment | Student Accounts / Billing | operational `ledger` / controlled Student Accounts services | legacy billing/finance readers as required | AR financial effects belong to Student Accounts, not Payments or Accounting. |
| Invoice / Installment / Payment Plan | Student Accounts / Billing | billing/Student Accounts services | legacy finance presentation where still consumed | Parent-facing receivable presentation remains separate from external money movement. |
| Allocation | Student Accounts / Billing | controlled AR allocation services | `finance.FinanceAllocation` bridge until consumers and data are proven migrated | Allocation answers which receivable a settled payment satisfies. |
| Payment Intent / Attempt | Payments | `payments` | none as accounting authority | Provider-neutral initiation and attempt state; no Accounting effect before settlement. |
| Payment | Payments | `payments.Payment` as canonical money-movement fact | `finance.FinancePayment` and operational `ledger.Payment` remain compatibility/projection surfaces until reconciliation proof | External money received is owned by Payments; Student Accounts reflects the AR effect. |
| Settlement | Payments | Payments settlement service | existing Finance -> Ledger bridge invoked only as a controlled compatibility path | Settlement requires explicit allocation facts and must be idempotent. |
| Refund | Payments | `payments.Refund` as canonical refund lifecycle fact | `finance.FinanceRefund` remains a compatibility bridge until reconciliation proof | REQUESTED/PENDING do not post Student Accounts or Accounting effects; provider-confirmed SETTLED triggers the financial reversal path. |
| Dispute / Chargeback / Payout / Provider Event / Payment Exception | Payments | `payments` | legacy/reporting adapters only where still required | Provider-specific normalization belongs at the adapter boundary. |
| Student Accounts posting effect | Student Accounts / Billing | operational `ledger` services | compatibility readers | Cash settlement/refund affects AR only after the canonical Payments lifecycle reaches the appropriate confirmed state. |
| Ledger / Journal Posting | Accounting | `journal` canonical posting/reversal services | `apps.accounting`, `finance`, and historical `core.LedgerEntry` paths only until their consumers are migrated and proven | Accounting owns immutable financial posting; Payments does not write GL truth directly. |
| Financial Aid award | Financial Aid | `aid` | legacy `financial_aid` bridge until migrated | Approved aid creates Student Accounts Credit; it is not payment activity. |
| Gift / Pledge / Campaign / Fund | Advancement | Advancement | shared Payments and Accounting contracts | Advancement owns donor/giving intent; Payments owns external money movement; Accounting owns posting. |

## Controlled Integration Surfaces

- `payments.PaymentIntentRecord` - gateway intent telemetry and compatibility correlation.
- `payments.GatewayEvent` - provider event telemetry and idempotent event processing.
- `payments.ProviderDispute`, payout, saved-method, exception, and reconciliation models - Payments-owned operational/provider evidence.
- `finance.FinancePayment` / `finance.FinanceRefund` - temporary compatibility bridge only after canonical Payments facts are introduced; not the target external money-movement authority.
- `ledger.Payment` / allocation records - Student Accounts reflection of settled money movement; not the provider/payment-system authority.

## Payment / Refund Lifecycle Guardrails

1. No provider-specific production architecture is activated until a merchant provider is selected and verified.
2. Existing payment hold/fail-closed behavior remains in force during architecture work.
3. Payment settlement requires explicit allocation facts; empty-allocation settlement is rejected.
4. Payment/provider identifiers have explicit ownership and must not be overloaded across intent, payment, client-reference, or refund identifiers.
5. Unmatched provider events fail durably and create exception evidence; they are not silently treated as processed financial facts.
6. Refund REQUESTED and PENDING states reserve refund capacity but create no Student Accounts or Accounting reversal.
7. Only provider-confirmed refund SETTLED may invoke the compatibility reversal path.
8. Requested, pending, and settled refunds all count toward over-refund prevention; failed/canceled requests release capacity.
9. No legacy payment/refund path is retired until consumer inventory, data comparison, reconciliation, rollback, exact-head tests, runtime proof, and review evidence are complete.

## Authority Rule

For Option A, **Payments owns external money movement; Student Accounts owns receivable effects; Accounting owns financial posting.** Any older document or code path assigning canonical Payment/Refund ownership to `finance` is a migration-era compatibility state unless a later evidence-backed authority explicitly supersedes this map.
