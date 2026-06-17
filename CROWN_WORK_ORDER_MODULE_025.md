# CROWN Work Order: Module 025 - Nutrition & Food Services Proof

**Status:** OPEN  
**Work Order ID:** MODULE-025-PROOF-20260617  
**Branch:** feat/module-025-nutrition-proof-20260617  
**Based on Main SHA:** 23104c1c19a059dfcfebf492c65678a953e22729  
**Work Type:** Proof closure for NOT_PROVEN module  
**Authority:** Support lane only; no self-approval; final canonical reconciliation requires separate evidence-backed PR.

---

## Live Canonical Basis

The current canonical scorecard shows 51 modules with 44 PROVEN and 7 NOT_PROVEN. Module 025 is one of the remaining operational gaps.

Module 025 current blocker:

> Nutrition & Food Services requires meal plan and dietary accommodation tests.

This work order exists to close only that proof gap with focused implementation/test evidence.

---

## Scope

Allowed targets:

1. Discover existing nutrition, meal, food-service, student, household, billing, and health/dietary code.
2. Add or complete Module 025 proof evidence for:
   - meal plan model/service coverage;
   - dietary accommodation model/service coverage;
   - student/household association;
   - tenant/school isolation;
   - unauthorized/forbidden access behavior where APIs exist;
   - audit/searchable evidence file.
3. Add focused tests only where current implementation exists or minimal proof scaffolding is required.
4. Produce evidence output under `audit-artifacts/module-completion/module-025-nutrition-food-services/`.

Forbidden targets:

- No dashboard live-data certification.
- No wizard functional-flow certification.
- No production-ready or release-ready claim.
- No broad Food Services rewrite.
- No Module 035 scorecard mutation in this lane.
- No canonical matrix/scorecard update in this PR unless a separate reconciliation step is explicitly opened after proof passes.

---

## Initial Connector Findings

- `audit-artifacts/module-completion/current/05_completion_scorecard.md` lists Module 025 as NOT_PROVEN.
- `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv` lists Module 025 blocker as meal plan and dietary accommodation tests required.
- Direct repository search did not find an existing Module 025 evidence test file by `test_51x51_evidence_25` or obvious Nutrition/Food Services implementation names.
- Module 035 has a metadata-only `backend/tests/test_51x51_evidence_35_food_services.py`; this must not be mistaken for Module 025 closure.

---

## Required Proof Before PR

The Module 025 PR may be opened only after:

- [ ] Worktree is clean before changes.
- [ ] Main includes PR #1060 merge commit `23104c1c19a059dfcfebf492c65678a953e22729`.
- [ ] Existing code inventory is captured.
- [ ] Module 025 proof test exists and passes locally.
- [ ] Tenant/school isolation is tested or explicitly marked NOT IMPLEMENTED with evidence.
- [ ] Meal plan proof is tested or explicitly marked NOT IMPLEMENTED with evidence.
- [ ] Dietary accommodation proof is tested or explicitly marked NOT IMPLEMENTED with evidence.
- [ ] No unrelated files are changed.

---

## Gate 1 Exit Criteria

Gate 1 may be marked PASSED only if:

1. `python -m pytest backend/tests/test_51x51_evidence_25*.py -v --nomigrations` passes.
2. Any app-specific tests added for nutrition/meal/dietary behavior pass.
3. Evidence packet records exact command output.
4. Changed-file list is limited to Module 025 proof scope.
5. Claims remain bounded to Module 025 proof closure.

---

## Gate 2 Merge Criteria

Before merge:

- PR open and non-draft.
- Same head SHA confirmed.
- Pending = 0.
- Failed = 0.
- Cancelled = 0.
- Head-locked merge only.

---

## Current Status

OPEN. VS Code lane should now create a local worktree from this remote branch and run the inventory/proof script.
