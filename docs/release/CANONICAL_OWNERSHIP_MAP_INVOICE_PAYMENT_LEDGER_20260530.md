# Canonical Ownership Map - Invoice/Payment/Ledger (2026-05-30)

Purpose: establish canonical financial ownership boundaries for invoice/payment/ledger records.

## Canonical Owners

| Domain Entity | Canonical Owner | Write Authority | Read Compatibility | Notes |
| --- | --- | --- | --- | --- |
| Obligation | finance.FinanceObligation | finance app only | reporting adapters | Canonical amount-due unit. |
| Invoice | finance.FinanceInvoice + finance.FinanceInvoiceLine | finance app only | reporting adapters | Canonical invoice presentation and line binding. |
| Payment | finance.FinancePayment | finance app only | payments gateway adapters | Canonical received/settled payment record. |
| Allocation | finance.FinanceAllocation | finance app only | reporting adapters | Canonical payment-to-obligation linkage. |
| Refund | finance.FinanceRefund | finance app only | payments gateway adapters | Canonical reversal intent and settlement state. |
| Ledger Posting | core.LedgerEntry | finance posting services only | analytics/reporting reads | Canonical immutable accounting posting surface. |

## Controlled Integration Surfaces

- payments.PaymentIntentRecord (gateway intent telemetry, non-canonical for ledger truth)
- payments.GatewayEvent (processor event telemetry, non-canonical for ledger truth)
- payments.ProviderDispute (processor dispute telemetry, non-canonical for ledger truth)

## Guardrail

- Canonical invoice/payment truth must remain in finance models.
- Payments app remains integration telemetry and processor event capture, not accounting source of truth.
