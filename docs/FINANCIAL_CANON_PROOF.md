# Financial Canon Proof – Crown2026

**Stage 2: Financial Invariant Lock**
Branch: `stage2/financial-invariant-lock`

---

## Purpose

This document records every financial invariant that has been formally proved via automated tests.
It is the authoritative reference for audit, QA, and future engineering reviews.

---

## Scope

| Domain | Module | Test File |
|--------|--------|-----------|
| Aid Award Ledger | `aid/models.py` | `aid/tests/test_aid_award_invariants.py` |
| Installment Proration | `billing/services.py` | `billing/tests/test_split_proration.py` |
| Ledger Integrity | `core/models.py`, `ledger/` | `ledger/tests/test_ledger_invariants.py` (pre-existing) |

---

## Invariant Registry

### INV-AID-01: Ledger Credit Sign

**Statement:** A posted Aid Award always creates a `LedgerEntry` with `amount_cents < 0` (a credit).

**Code path:** `AidAward.mark_accepted_and_post()` → `amount_cents = -abs(int(self.awarded_cents))`

**Tests:** `TestAidLedgerSign::test_amount_cents_is_negative`, `test_full_sign_and_magnitude_combined`

**Why it matters:** Positive `amount_cents` on an aid award would inflate student balances instead of reducing them.

---

### INV-AID-02: Magnitude Preserved

**Statement:** `abs(ledger_entry.amount_cents) == award.awarded_cents` exactly.

**Code path:** `amount_cents = -abs(int(self.awarded_cents))` — integer cast, no rounding.

**Tests:** `TestAidLedgerSign::test_magnitude_matches_awarded_cents`, `test_full_sign_and_magnitude_combined`

**Why it matters:** Any cent discrepancy between awarded amount and posted amount is an accounting error.

---

### INV-AID-03: Double-Post Prevention (Idempotency)

**Statement:** Calling `mark_accepted_and_post()` on the same `AidAward` more than once creates exactly **one** `LedgerEntry`.

**Code path:** Guard: `if self.ledger_entry_id: return self.ledger_entry` (early return without creating a new entry).

**Tests:** `TestAidDoublePostPrevented::test_second_call_returns_same_entry`, `test_exactly_one_ledger_entry_after_two_calls`

**Why it matters:** Double-posting would double the credit on the ledger, understating the student's balance.

---

### INV-AID-04: Reversal Nets to Zero

**Statement:** After `mark_accepted_and_post()` followed by `mark_declined_and_reverse()`, the sum of all `LedgerEntry.amount_cents` for that student equals **0**.

**Code path:** `LedgerEntry.create_reversal(original)` → `amount_cents = -original.amount_cents`. Net: `(-X) + X = 0`.

**Tests:** `TestAidReversalNetsToZero::test_net_balance_is_zero_after_reversal`, `test_two_entries_exist_total`

**Why it matters:** A declined award must leave the student's ledger at the same state as before the award was posted.

---

### INV-AID-05: Reversal Entry Flagged

**Statement:** The reversal `LedgerEntry` has `is_reversal=True`.

**Code path:** `LedgerEntry.create_reversal()` sets `is_reversal=True` on the new entry.

**Tests:** `TestAidReversalNetsToZero::test_reversal_entry_flagged_is_reversal_true`

**Why it matters:** Auditors must be able to identify reversal entries distinctly from original postings.

---

### INV-AID-06: Audit Trail — Post

**Statement:** Calling `mark_accepted_and_post()` produces both an `AWARD_ACCEPTED` and a `LEDGER_POSTED` `AidAuditEvent`.

**Tests:** `TestAidAuditTrail::test_post_emits_accepted_and_ledger_posted_events`

**Why it matters:** Every financial state change must have a tamper-evident log record.

---

### INV-AID-07: Audit Trail — Reversal

**Statement:** Calling `mark_declined_and_reverse()` after posting produces both an `AWARD_DECLINED` and a `LEDGER_REVERSED` `AidAuditEvent`.

**Tests:** `TestAidAuditTrail::test_decline_emits_declined_and_ledger_reversed_events`, `test_full_lifecycle_event_count`

**Why it matters:** Reversal without audit logging would be an invisible financial change.

---

### INV-BILL-01: Installment Sum Invariant

**Statement:** `_split_amount_evenly(total, n)` returns exactly `n` parts whose sum equals `total` to the cent.

**Code path:** Base = `ROUND_DOWN(total / n)`. Last part = `total - (base × (n-1))`. Absorbs all rounding remainder.

**Tests:** `TestSumInvariant` — 5 parameterized cases covering 3-way, 4-way, 7-way, 12-way, 11-way splits.

**Why it matters:** Any penny discrepancy between the sum of installments and the household's total balance is an irrecoverable accounting error.

---

### INV-BILL-02: No Negative Parts

**Statement:** Every element of the returned list is `>= Decimal("0.00")`.

**Tests:** `TestNoNegativeParts::test_penny_split_three_ways_no_negative`

**Why it matters:** A negative installment would credit a student's account unexpectedly.

---

### INV-BILL-03: Zero-Parts Guard

**Statement:** Calling `_split_amount_evenly(total, 0)` raises `ValueError("parts must be > 0")`.

**Tests:** `TestInvalidParts::test_zero_parts_raises_value_error`, `test_negative_parts_raises_value_error`

**Why it matters:** Prevents a division-by-zero from silently producing an empty installment plan.

---

## Pre-existing Proofs (from prior phases)

These invariants were proven before Stage 2 and are recorded here for completeness.

| Invariant | File | Key Test |
|-----------|------|----------|
| Ledger over-allocation detection | `ledger/tests/test_ledger_invariants.py` | `test_over_allocation_detected` |
| Negative charge rejected | `ledger/tests/test_ledger_invariants.py` | `test_negative_charge_rejected` |
| Tenant isolation | `ledger/tests/test_ledger_invariants.py` | `test_tenant_isolation` |
| LedgerEntry immutability (delete raises) | `core/models.py` | runtime guard (model-level) |

---

## How to Run

```powershell
# From repo root (venv at .venv/)
& ".venv\Scripts\python.exe" -m pytest `
  backend/aid/tests/test_aid_award_invariants.py `
  backend/billing/tests/test_split_proration.py `
  backend/ledger/tests/test_ledger_invariants.py `
  -v --tb=short 2>&1
```

Expected: all tests pass, no warnings about missing migrations (SQLite in-memory for CI).

---

## Stage 1 Regression Guard

A CI step in `.github/workflows/dashboards-build-gate.yml` prevents re-introduction of silent empty catch handlers (`.catch(() => {})`) in `frontend/dashboards/src/`. This guard fires on every PR touching frontend files.

---

_Document generated as part of Stage 2: Financial Invariant Lock. Last updated by audit toolchain._
