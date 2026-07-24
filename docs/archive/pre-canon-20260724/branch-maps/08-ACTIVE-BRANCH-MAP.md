> SUPERSEDED — HISTORICAL RECORD ONLY
>
> Archived: 2026-07-24
> Former path: `docs/completion/08-ACTIVE-BRANCH-MAP.md`
> Current governing authority: `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md`
> Do not use for current branch, pull-request, release, completion, or buyer-readiness decisions.

# Crown2026 — Active Branch Map

## Purpose

This file tracks the branches that still matter to release truth.

---

## Branch Table

| Branch Name | Purpose | PR Number | Current HEAD SHA | Status | Merged | Superseded | Release-Relevant | Notes |
|---|---|---|---|---|---|---|---|---|
| main | Default integration branch | n/a | 550d84b23dbfb85cdbc5a75705110d691ac8eca9 | active | n/a | No | Yes | Synced to origin/main; contains merged PR 577 work |
| fix/track11-12-write-and-lifecycle-proof | Merged release-proof branch | 577 | 550d84b23dbfb85cdbc5a75705110d691ac8eca9 (via merge commit on main) | MERGED | Yes | Yes | Historical only | Branch achieved merge objective on 2026-03-15 |
| copilot/fix-issues-in-active-work | Adjacent runtime fix branch | 578 | UNPROVEN | OPEN | No | No | Potentially | Could carry overlapping release-impact fixes |
| copilot/fix-next-issues | Adjacent RBAC fix branch | 579 | UNPROVEN | OPEN | No | No | Potentially | Could affect auth/role behavior |
| copilot/assess-efficiency-and-cleanliness | Hygiene/security branch | 580 | UNPROVEN | OPEN | No | No | Potentially | Repo hygiene and secret-hardening scope |
| copilot/close-pull-requests-and-issues | PR/issue triage branch | 581 | UNPROVEN | OPEN / DRAFT | No | No | Potentially | Meta workflow branch |

---

## Branch Notes

### main
- Purpose: Canonical default branch for release merges
- Current status: Synced to origin/main at 550d84b23dbfb85cdbc5a75705110d691ac8eca9
- Release relevance: High
- Notes: PR 577 is now incorporated into main.

### fix/track11-12-write-and-lifecycle-proof
- Purpose: Proof shell backend write/lifecycle and route integrity stabilization branch
- Current status: PR #577 merged
- Release relevance: Historical; no longer the canonical active branch
- Notes: Merge commit is 550d84b23dbfb85cdbc5a75705110d691ac8eca9.

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
- PR #577 is merged and no longer an active branch-level blocker.
- Additional open PRs should be marked release-relevant only after triage.
