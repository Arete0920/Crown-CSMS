# CROWN Release Authority Integrity Hold - Progress Tracker

> Superseded Authority Notice (2026-05-29)
>
> This document is a historical hold-era tracker and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Date: 2026-05-19
State: INTEGRITY HOLD (unchanged - see INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md)

## Purpose

This document tracks progress against each requirement needed before
the INTEGRITY HOLD can be formally lifted. It does not modify the hold
state. State changes in the canonical hold document require complete
evidence for all items below.

## Lift criteria summary

All 5 blocker lanes must be CLOSED and all 10 required evidence items
must exist, be committed, and accurately describe the underlying proof.

---

## Blocker Lane Status

| # | Lane | Status | Notes |
|---|------|--------|-------|
| 1 | Release-authority contradiction closure | OPEN | Correction plan exists (RELEASE_AUTHORITY_CORRECTION_PLAN_20260506.md). All files must use consistent integrity-hold language. |
| 2 | Compliance/customer-readiness packet | OPEN | 10 required evidence documents listed below; committed in-repo; completion and review still pending. |
| 3 | Controlled pilot entry proof | OPEN | Entry criteria not yet met. No pilot school onboarded. |
| 4 | Controlled pilot exit proof | OPEN | Depends on lane 3 completing first. |
| 5 | Final founder/product-owner acceptance | IN PROGRESS | Template created in docs/release/FOUNDER_ACCEPTANCE.md (PR #830). Requires founder signature (human action). |

---

## Required Evidence Documents (10 items)

| # | Document | Status | File Path (when created) |
|---|----------|--------|--------------------------|
| 1 | FERPA position | OPEN | docs/compliance/FERPA_POSITION.md |
| 2 | COPPA position | OPEN | docs/compliance/COPPA_POSITION.md |
| 3 | DPA template | OPEN | docs/compliance/DPA_TEMPLATE.md |
| 4 | Data retention policy | OPEN | docs/compliance/DATA_RETENTION_POLICY.md |
| 5 | Support access policy | OPEN | docs/compliance/SUPPORT_ACCESS_POLICY.md |
| 6 | Incident response policy | OPEN | docs/compliance/INCIDENT_RESPONSE_POLICY.md |
| 7 | Subprocessor register | OPEN | docs/compliance/SUBPROCESSOR_REGISTER.md |
| 8 | Backup/restore policy | OPEN | docs/compliance/BACKUP_RESTORE_POLICY.md |
| 9 | Sandbox/no-real-data policy | OPEN | docs/compliance/SANDBOX_DATA_POLICY.md |
| 10 | Controlled pilot entry criteria | OPEN | docs/compliance/PILOT_ENTRY_CRITERIA.md |

---

## Gate 5 (Release Authority Hold) - Closeout Proof Gate Check

Gate 5 in `scripts/release_closeout_proof_gate.ps1` checks for the
string `State: INTEGRITY HOLD` in the canonical hold document.

Integrity Hold release criteria (governance definition of done; Gate 5 script logic remains canonical):
1. All 5 blocker lanes above are CLOSED.
2. All 10 evidence documents above are committed.
3. The canonical hold document is updated to remove `State: INTEGRITY HOLD`
   (and replaced with `State: RESOLVED` or similar) by the authorized owner.

**Do not edit the canonical hold document to remove the hold state
without complete evidence in place. This would constitute a false
governance claim.**

---

## Gate 6 (Founder Acceptance) - Closeout Proof Gate Check

Gate 6 checks for `SIGNED` in `docs/release/FOUNDER_ACCEPTANCE.md`.

Gate 6 will PASS only when the founder/product-owner:
1. Reviews the acceptance declaration in docs/release/FOUNDER_ACCEPTANCE.md.
2. Replaces `<!-- PENDING_FOUNDER_SIGNATURE -->` with `SIGNED`.
3. The PR containing that change is merged.

**Agent must not sign on the founder's behalf.**

---

## Minimum steps to unblock Gate 5 and Gate 6

1. (Human) Author the 10 compliance documents in docs/compliance/.
2. (Human) Conduct and document a controlled pilot with at least one school.
3. (Human) Author pilot entry proof and pilot exit proof.
4. (Human) Verify release-authority files use consistent hold language.
5. (Human) Update INTEGRITY_HOLD_RELEASE_AUTHORITY_20260506.md to RESOLVED.
6. (Human) Sign docs/release/FOUNDER_ACCEPTANCE.md.

---

## Current Closeout Proof Gate Status (historical capture point-in-time)

- PASS: 17
- FAIL: 6
- Decision at capture: NO-GO

Related failing gates tracked by this document (not direct gate inputs):
- Gate 5: INTEGRITY HOLD active
- Gate 6: FOUNDER_ACCEPTANCE.md not signed (template pending PR #830)

Other failing gates at capture time (historical snapshot):
- Working tree had uncommitted changes (cleared in later cleanup)
- Main sync drift (cleared in later cleanup)
- Open PR backlog (tracked separately)
- Production build_sha mismatch (requires authorized production deploy)

