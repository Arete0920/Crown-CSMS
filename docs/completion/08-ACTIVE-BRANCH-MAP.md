# Crown2026 — Active Branch Map

## Purpose

This file tracks the branches that still matter to release truth.

---

## Branch Table

| Branch Name | Purpose | PR Number | Current HEAD SHA | Status | Merged | Superseded | Release-Relevant | Notes |
|---|---|---|---|---|---|---|---|---|
| main | Default integration branch | n/a | local ref diverged from origin/main | active | n/a | No | Yes | ahead 8 / behind 4 vs origin/main |
| fix/track11-12-write-and-lifecycle-proof | Active release-proof branch | 577 | 5b9e09d34333f2b57d32708ff0a4dcde621039da | OPEN/BLOCKED | No | No | Yes | Required checks include failures (gradebook-proof, CodeQL) |
| copilot/fix-issues-in-active-work | Adjacent runtime fix branch | 578 | UNPROVEN | OPEN | No | No | Potentially | Could carry overlapping release-impact fixes |
| copilot/fix-next-issues | Adjacent RBAC fix branch | 579 | UNPROVEN | OPEN | No | No | Potentially | Could affect auth/role behavior |

---

## Branch Notes

### main
- Purpose: Canonical default branch for release merges
- Current status: Exists locally/remotely; local ref is ahead/behind origin/main
- Release relevance: High
- Notes: Do not declare release complete without reconciling main branch divergence policy.

### fix/track11-12-write-and-lifecycle-proof
- Purpose: Current active branch for proof shell backend write/lifecycle and route integrity fixes
- Current status: PR #577 open, mergeStateStatus BLOCKED
- Release relevance: Highest (current active PR)
- Notes: Head SHA is 5b9e09d34333f2b57d32708ff0a4dcde621039da.

### Additional release branches
- Branch: copilot/fix-issues-in-active-work (PR #578)
- Purpose: runtime/test repairs that may overlap release stability
- Status: OPEN
- Notes: Release relevance is potential, not currently designated canonical.

---

## Branch Policy

- No branch may be called release-relevant without this file being updated.
- No release-relevant branch may be merged without:
  - Current Truth Snapshot updated
  - Blocker Ledger updated
  - RC artifact SHA aligned
- Superseded branches must be marked explicitly.

---

## Notes

- This map prioritizes active and potentially release-impacting branches only.
- PR #577 remains the only explicitly designated release-relevant active PR.
- Additional open PRs should be marked release-relevant only after triage.
