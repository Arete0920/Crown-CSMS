# Crown2026 — Completion Contract

## Purpose

This file defines the only authorized meanings of completion-related language for Crown2026.

No one may use the words **done**, **complete**, **finished**, **ready**, or **production-ready** unless the item is explicitly mapped to one of the states below.

---

## 1. LOCALLY VERIFIED

### Definition
An item is **LOCALLY VERIFIED** only if:
- required local tests pass
- required local build passes
- required local artifacts are produced if applicable
- local working tree is clean or intentionally documented

### Minimum evidence
- command outputs
- local SHA
- artifact path if applicable

### Not included
- CI pass
- PR merge readiness
- deployment truth
- production truth
- investor readiness

---

## 2. CI VERIFIED

### Definition
An item is **CI VERIFIED** only if:
- required CI checks pass on the exact branch SHA
- no required check is red or pending
- the check set is tied to the exact tested commit

### Minimum evidence
- PR number
- SHA
- passing check list
- run IDs / URLs

### Not included
- merge completion
- deployed truth
- production truth
- investor readiness

---

## 3. MERGE READY

### Definition
An item is **MERGE READY** only if:
- CI VERIFIED is true
- required PR checks are green
- branch is up to date or mergeable under repo policy
- no unresolved branch blockers remain
- working tree is clean

### Minimum evidence
- PR number
- mergeable state
- exact passing checks
- blocker ledger shows no open branch blockers for this PR

### Not included
- deployed truth
- production truth
- investor readiness

---

## 4. DEPLOYED VERIFIED

### Definition
An item is **DEPLOYED VERIFIED** only if:
- exact certified SHA is deployed
- exact build tag / release tag matches deployed truth
- health endpoints pass
- target environment is confirmed
- deployment was checked after promotion

### Minimum evidence
- deployed URL(s)
- deployed SHA
- certified SHA
- build tag
- health check output

### Not included
- full production readiness
- investor readiness

---

## 5. PRODUCTION CERTIFIED

### Definition
An item is **PRODUCTION CERTIFIED** only if:
- DEPLOYED VERIFIED is true
- security checks passed or documented dispositions exist
- monitoring/logging/backups/rollback are confirmed
- required module acceptance is signed off
- supportability requirements are met

### Minimum evidence
- production certification checklist
- deployment truth
- module acceptance matrix
- blocker ledger clear for production blockers

### Not included
- investor readiness by default

---

## 6. INVESTOR READY

### Definition
An item is **INVESTOR READY** only if:
- PRODUCTION CERTIFIED is true, or a demo-only baseline is explicitly labeled
- investor demo script is stable and passes
- demo data is coherent
- known limitations are documented
- evidence packet exists and is current

### Minimum evidence
- investor readiness checklist
- current truth snapshot
- module acceptance matrix
- blocker ledger
- known limitations list
- demo script

---

## Forbidden language

The following words may not be used without mapping to one of the six states above:
- done
- complete
- finished
- ready
- production-ready
- investor-ready

Examples:
- Wrong: “Crown is done.”
- Right: “The current branch is CI VERIFIED.”
- Wrong: “The module is complete.”
- Right: “The Attendance module is LOCALLY VERIFIED but UNPROVEN for production.”

---

## Reporting rule

Every future status report must use exactly one or more of these states:
- LOCALLY VERIFIED
- CI VERIFIED
- MERGE READY
- DEPLOYED VERIFIED
- PRODUCTION CERTIFIED
- INVESTOR READY

No other completion language is allowed.

---

## Notes

- This contract is normative for all status reporting in docs/completion.
- If evidence is missing or stale, the required label is UNPROVEN.
- For current PR 577 snapshot, CI VERIFIED and MERGE READY are not allowed claims.
