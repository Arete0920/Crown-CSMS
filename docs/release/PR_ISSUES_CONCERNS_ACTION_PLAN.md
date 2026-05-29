# PR, Issues, and Concerns Action Plan

> Authority Scope Notice (2026-05-29)
>
> This document is an operational action-plan artifact and not a controlling repository-level release authority source.
>
> Current controlling release-authority sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Generated: 2026-04-02
Branch: `chore/github-cleanup-phase3-investor-evidence`

Purpose: provide one canonical, execution-ready cleanup plan for open PR backlog,
open production-risk issues, and governance concerns discovered in Phase 2/3.

## A) Open PR Backlog (Current Snapshot)

Open PRs currently observed: **16**

### Priority 1: Merge Next (release hygiene/security unblock)

1. [#637](https://github.com/tcmegahan/Crown2026/pull/637) `fix(ci): repair malformed heredoc in prod-health-watch.yml`
2. [#638](https://github.com/tcmegahan/Crown2026/pull/638) `fix(security): remove continue-on-error from CodeQL — now blocking`
3. [#639](https://github.com/tcmegahan/Crown2026/pull/639) `feat(ci): add blocking pip-audit + npm audit dependency workflow`
4. [#640](https://github.com/tcmegahan/Crown2026/pull/640) `docs: commit governance and documentation package for investor review`

### Priority 2: Feature PRs (needs review and/or rebase)

1. [#629](https://github.com/tcmegahan/Crown2026/pull/629) `feat(financial-aid): complete all 5 director actions + application intake`
2. [#630](https://github.com/tcmegahan/Crown2026/pull/630) `feat(billing): automated invoicing + CompuWerx webhook + late fees`
3. [#632](https://github.com/tcmegahan/Crown2026/pull/632) `feat: parent portal my-student consolidation`
4. [#625](https://github.com/tcmegahan/Crown2026/pull/625) `feat(security): complete security hardening`
5. [#626](https://github.com/tcmegahan/Crown2026/pull/626) `feat(audit-roadmap): phases 3-5 quality, operations, and feature completeness`
6. [#628](https://github.com/tcmegahan/Crown2026/pull/628) `feat(little-lambs): complete Little Lambs daycare module`
7. [#618](https://github.com/tcmegahan/Crown2026/pull/618) `fix: restore deploy test contracts`

### Priority 3: Conflict Resolution Required

1. [#611](https://github.com/tcmegahan/Crown2026/pull/611) `ci: guard CodeQL and dependency review when security features are unavailable` (DIRTY)
2. [#600](https://github.com/tcmegahan/Crown2026/pull/600) `chore(ci): harden production deploy trigger and environment protections` (DIRTY)

### Priority 4: High-Risk Agent PRs (manual review only)

1. [#635](https://github.com/tcmegahan/Crown2026/pull/635) `enforce: lock down main branch protection and repo policies`
2. [#636](https://github.com/tcmegahan/Crown2026/pull/636) `chore: bulk remove tracked generated artifacts and non-canonical root files`

Rule: do not merge either PR without line-by-line review of `.github/`, branch protection,
workflow, and root file deletion deltas.

### Close Candidate

1. [#641](https://github.com/tcmegahan/Crown2026/pull/641) `chore: remove stale operational debris from repo root`
Reason: superseded by cleanup sequence delivered in Phase 1/2/3 branches.

---

## B) Open Issues of Concern (Current Snapshot)

### High Priority Operational Issues

1. [#512](https://github.com/tcmegahan/Crown2026/issues/512) Frontend production deploy missing `AZURE_SWA_TOKEN`
2. [#511](https://github.com/tcmegahan/Crown2026/issues/511) DEV auth smoke returns 401 after reset workflow
3. [#518](https://github.com/tcmegahan/Crown2026/issues/518) Verify dashboard protected endpoint
4. [#520](https://github.com/tcmegahan/Crown2026/issues/520) Verify finance protected endpoint
5. [#521](https://github.com/tcmegahan/Crown2026/issues/521) Verify admissions protected endpoint

### Concern Mapping

| Concern | Related issue/PR | Impact if unresolved | Required evidence to close |
|---|---|---|---|
| Deploy token/config mismatch | #512 | Frontend prod deploy instability | Successful deploy run + settings screenshot/log |
| Auth regression after reset | #511 | Smoke gates unreliable; false negatives | Green reset+auth smoke run artifact |
| Protected endpoint coverage gaps | #518 #520 #521 | Security/compliance confidence gap | Endpoint proof logs and tests |
| Security gates not proven blocking | #638 #639 + release docs | Branch protection confidence gap | Blocking screenshots + required-check export |

---

## C) Concern Closure SLA

1. Priority 1 PRs merged within 24 hours
2. Conflict PRs (#611/#600) either resolved or closed within 48 hours
3. High-priority issues (#511/#512/#518/#520/#521) moved to evidence-backed status within 72 hours
4. Agent PRs (#635/#636) explicitly approved or closed within 72 hours

---

## D) Exit Criteria for "PR/Issues Concerns Cleaned"

Mark this area complete only when:

1. Open PR count reduced below 8 and no PR remains in DIRTY state
2. Priority 1 PRs (#637 #638 #639 #640) are merged
3. #641 is closed as superseded
4. High-priority issues (#511 #512 #518 #520 #521) each have one committed proof artifact or closure note
5. `docs/release/FINAL_RELEASE_GATE.md` PR backlog row updated to PASS or PARTIAL with current evidence link
