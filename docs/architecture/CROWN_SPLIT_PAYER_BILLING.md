# CROWN Split-Payer Billing

Status: implementation authority
Scope: payer responsibility inside one canonical household receivable

## Principle

The household invoice and ledger charge remain CROWN's accounting source of truth. Split-payer support must not create parallel receivables, duplicate charges, or separate accounting ledgers for co-parents or third parties.

## Responsibility model

A billing payer may be:

- a linked guardian;
- another authenticated individual;
- a church, employer, scholarship organization, grandparent, or other third party.

Responsibility is expressed in basis points and may be configured at household level or overridden for an individual student and charge type. Active rules that apply to a billed line must total exactly 10,000 basis points.

Student-specific rules take precedence over household defaults for that student. If no rules exist, existing household billing behavior remains unchanged.

## Invoice snapshot

Responsibility rules are configuration. When an invoice is created, the resulting payer amounts are snapshotted into payer-share records. Later rule changes must not rewrite historical invoices.

Cent rounding is deterministic. Earlier payer shares round down to cents and the final payer receives the remainder, so payer shares always equal the canonical invoice amount.

## Payment attribution

Ledger payments and allocations remain canonical. A payer attribution may identify which payer share a canonical allocation satisfied, but it must reference the same school and the invoice's canonical ledger charge.

## Privacy and access

A payer may see only the share explicitly assigned to that payer, related payment/receipt facts, and school-approved explanatory data. Split-payer support must not reveal another payer's contact details, payment method, private notes, or unrelated family financial information.

School finance roles may configure payer responsibility and review the full household receivable under existing authorization and audit controls.

## Required follow-up proof

Before this capability is certified:

1. migration and model checks pass;
2. 60/40 and other cent-rounding cases pass;
3. student-specific overrides pass;
4. invalid percentages roll back atomically;
5. tenant and household mismatch attempts fail closed;
6. payer-facing balance queries are scoped to the authenticated payer;
7. payment attribution cannot exceed either the canonical allocation or payer share balance;
8. refunds and reversals restore the correct payer responsibility;
9. statements and notices do not leak co-payer information;
10. runtime evidence is retained on the exact release head.

## Refund, reversal, and presentation controls (PR #119)

- Payer responsibility configuration and snapshots validate school and household relationships on ordinary model saves. Invoice generation also validates rules read from existing/imported data and rolls back the complete run on a mismatch.
- `PayerRefundAttribution` links restored responsibility to the existing Finance refund's canonical ledger debit and original payment attribution. It never posts an additional receivable. Partial and full refunds consume the original payer's attributions in stable creation order; unknown/mismatched payer identity or insufficient attributable responsibility fails atomically.
- Active canonical refund debits reduce payer-paid amounts. Voiding that debit cancels the restoration while retaining history. A payment with an active attributed refund cannot also be voided until its refund debit is reversed.
- Voiding attributed payments retains protected allocations and attribution history. Payer balances exclude void payments/charges; ordinary non-attributed allocation cleanup is unchanged. Split-payer reversals require a school finance role.
- Full household statements require finance authorization. Payer self-service statements use an explicit field allowlist without co-payer contacts, payment references, payment methods, or private notes.
- The notice-content builder binds the recipient to the assigned payer in the same school and uses the same allowlisted statement facts. This branch does not enable notice delivery, external refunds, or payment-processor behavior. A future sender must use this builder and separately prove recipient routing and delivery before certification of that integration.
- Refund attribution serializes with canonical ledger-payment locking. Historical allocations cannot acquire new payer attributions after an active refund debit exists.

### Audit and certification boundary

Segregation of duties: The product owner is the solo developer and cannot self-review or self-approve this work.

Control path used: Solo-developer approved workaround, GitHub required checks, and CI release gate evidence. Engineering support, architecture review, and evidence audit are advisory; repository authority remains under this control path.

The branch was refreshed against `main` at `a0e5a2de71d8c81b1b21e6b666f91a7f5819854b` (including Home Academy #117). Local regression and migration results belong to this source revision; they do not certify a later head, a deployed environment, notification delivery, or a processor integration. Merge and final certification remain NO-GO until the refreshed exact head has terminal-green required evidence against current main. No required check, authorization, tenant-isolation control, or canonical household-AR ownership was relaxed.

Local validation on October 5: billing, billing API, ledger, and Finance service regression suite — 168 passed, 2 pre-existing demo-school smoke tests skipped because no demo-school ID was configured. Migration drift check — no changes detected. Existing duplicate `crownpass` URL namespace warning remains outside this billing scope. Final payment/attribution lock-order adjustment receives a separate split-payer API rerun before publication. PostgreSQL concurrency, deployed runtime, and sender delivery remain subject to exact-head CI/runtime proof.
