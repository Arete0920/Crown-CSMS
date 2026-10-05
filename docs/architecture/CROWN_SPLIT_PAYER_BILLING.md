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
