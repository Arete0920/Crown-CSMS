# Financial Invariants — Engineering Contract

> **Purpose:** Canonical list of enforced ledger/journal invariants.  
> **Authority:** This document is generated from tests; if a test and this doc disagree, the test wins.  
> **Phase:** 7.3 — Ledger Invariant Hardening (PR #430)

---

## Ledger Invariants

| # | Invariant | Why | Enforcement Layer | Guard Location | Test |
|---|-----------|-----|-------------------|---------------|------|
| L-1 | Allocations must not exceed charge face value | Over-allocation creates negative receivable balance; produces phantom credit | API + DB | `ledger/api.py:record_payment` (allow_overpay guard); `GET /api/v1/ledger/invariants/` (checker) | `test_ledger_invariants.py::test_invariants_detects_over_allocation` |
| L-2 | FIFO allocator must skip voided charges (`is_void=True`) | Voided charges are no longer collectable; allocating to them corrupts the AR balance | Service | `ledger/services.py:allocate_payment_fifo` (queryset filter `is_void=False`) | `test_ledger_invariants.py::test_allocation_on_voided_charge_skipped` |
| L-3 | Allocations must not cross school tenants | Cross-tenant allocation leaks funds between schools | Service | `ledger/services.py:allocate_payment_fifo` (`payment.school_id != school_id → ValueError`) | `test_ledger_invariants.py::test_allocation_cross_tenant_guard` |
| L-4 | Voiding a charge via API must not allocate to it | API-layer guard before service; prevents race where payment is recorded on a concurrently-voided charge | API | `ledger/api.py:record_payment` (line ~319: `is_void → 400`) | `test_ledger_void_endpoints_api.py::test_void_charge_removes_allocations` |
| L-5 | `void_charge` must be idempotent (200 on repeat) | Retry safety; network/client retries must not error | API | `ledger/api.py:void_charge` (early return if `ch.is_void`) | `test_ledger_void_endpoints_api.py::test_void_charge_is_idempotent` |
| L-6 | `void_payment` must be idempotent (200 on repeat) | Same as L-5 for payments | API | `ledger/api.py:void_payment` (early return if `pay.is_void`) | `test_ledger_void_endpoints_api.py::test_void_payment_is_idempotent` |
| L-7 | Voiding a charge twice must create exactly one reversal JournalEntry | Duplicate reversal JEs corrupt the GL (double-reversal = net zero on original but double entry noise) | Signal + Service | `ledger/signals.py:_charge_create_void_reversal` (only fires on `is_void` flip False→True); `journal/services.py:create_reversal_entry` (idempotent via `reversal_of` OneToOne) | `test_ledger_void_endpoints_api.py::test_void_charge_no_duplicate_reversal_entry` |
| L-8 | Ledger tenant isolation — invariant checker must not expose other schools' violations | Privacy + correctness; school_a violations must not appear in school_b's invariant report | API | `ledger/api.py:invariants` (all queries scoped `school_id=sid`) | `test_ledger_invariants.py::test_invariants_tenant_isolation` |

---

## Journal Invariants

| # | Invariant | Why | Enforcement Layer | Guard Location | Test |
|---|-----------|-----|-------------------|---------------|------|
| J-1 | Every JournalEntry must balance (Σ debit = Σ credit) | Double-entry accounting requirement; unbalanced entries corrupt trial balance | Service | `journal/services.py:post_journal_entry` (sum before create) | `test_journal_invariants.py::test_balanced_entry_succeeds` / `test_unbalanced_entry_fails` |
| J-2 | Every JournalEntry must have at least 2 lines | Single-line entry cannot balance; indicates data path error | Service | `journal/services.py:post_journal_entry` (`len(lines) < 2 → ValidationError`) | `test_journal_invariants.py::test_single_line_entry_fails` |
| J-3 | JournalEntry lines must not carry negative debit/credit amounts | Negative amounts invert balance logic; use reversals instead | Service | `journal/services.py:post_journal_entry` (`debit < 0 or credit < 0 → ValidationError`) | `test_journal_invariants.py::test_negative_line_value_fails` |
| J-4 | JournalEntry lines must not have both debit and credit > 0 | A line is either a debit or a credit, never both | Service | `journal/services.py:post_journal_entry` (`debit > 0 and credit > 0 → ValidationError`) | `test_journal_invariants.py::test_single_line_entry_fails` (covered via balance check) |
| J-5 | JournalEntry GL accounts must belong to the same school as the entry | Cross-tenant GL references corrupt each school's trial balance | Service | `journal/services.py:post_journal_entry` (`account.school_id != school.id → ValidationError`) | `test_journal_invariants.py::test_cross_tenant_account_fails` |
| J-6 | JournalEntry reversals must be idempotent (OneToOne `reversal_of`) | Calling `create_reversal_entry` twice must not produce two reversal entries | Service + DB | `journal/services.py:create_reversal_entry` (fast-path `reversal_entry_id` check + DB OneToOne constraint) | `test_ledger_void_endpoints_api.py::test_void_charge_no_duplicate_reversal_entry` (end-to-end signal path) |
| J-7 | Reversal entry must swap DR/CR lines from the original | Incorrect swap produces a net-non-zero combined position; must cancel original exactly | Service | `journal/services.py:create_reversal_entry` (`debit=line.credit, credit=line.debit`) | `test_gate2b_charge_void_reversal.py` (ORM signal path) |
| J-8 | JournalEntry is immutable once locked | Prevents retroactive edits to posted GL entries; audit integrity | Model | `journal/models.py:JournalEntry` (`ImmutableMoneyMixin` / `full_clean` raises `ValidationError` if locked) | Covered by model-level unit tests in journal app |

---

## Enforcement Matrix (by layer)

```
DB constraints       ← OneToOne reversal_of (J-6), school FK on GLAccount (J-5)
Model validation     ← JournalEntry immutability when locked (J-8)
Service layer        ← Balance check (J-1), line count (J-2), negative amounts (J-3),
                       cross-tenant account (J-5), reversal idempotency (J-6),
                       DR/CR swap (J-7), is_void filter in FIFO (L-2),
                       cross-tenant payment guard (L-3)
API layer            ← void_charge/void_payment idempotency (L-5, L-6),
                       is_void allocation block (L-4), over-allocation guard (L-1)
Signal layer         ← Reversal JE creation on void flip (L-7, J-6)
Invariant endpoint   ← GET /api/v1/ledger/invariants/ post-hoc checker (L-1, L-8)
```

---

## Test Files

| Test File | Covers |
|-----------|--------|
| `backend/ledger/tests/test_ledger_invariants.py` | L-1, L-2, L-3, L-8 |
| `backend/ledger/tests/test_ledger_void_endpoints_api.py` | L-4, L-5, L-6, L-7, J-6 |
| `backend/ledger/tests/test_gate2b_charge_void_reversal.py` | L-5 (ORM), J-7 |
| `backend/ledger/tests/test_ledger_payments_correctness_api.py` | L-1, L-4 (API path) |
| `backend/journal/tests/test_journal_invariants.py` | J-1, J-2, J-3, J-4, J-5 |

---

*Last updated: Phase 7.3 — branch `phase/7.3-ledger-invariants`*
