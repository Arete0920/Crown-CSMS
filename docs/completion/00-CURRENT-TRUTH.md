# Crown2026 — Current Truth Snapshot

## Snapshot Metadata

- Date: 2026-03-15
- Prepared by: GitHub Copilot (GPT-5.3-Codex)
- Repository: tcmegahan/Crown2026
- Purpose: Establish exact current truth for Crown2026 at this moment.

---

## A. Repository Truth

- Current branch: fix/track11-12-write-and-lifecycle-proof
- Current HEAD SHA: 5b9e09d34333f2b57d32708ff0a4dcde621039da
- Current working tree status: dirty (untracked: _tmp_completion_pr577.json, docs/completion/)
- Is local `main` clean: UNPROVEN (not checked out during this snapshot)
- Is local `main` ahead/behind remote: ahead 8, behind 4 versus origin/main
- Current release-relevant branch: fix/track11-12-write-and-lifecycle-proof
- Current release-relevant PR(s): #577
- Active RC tag(s): phase6-rc-gate-2026-02-21; phase6-rc-live-probes-2026-02-21; phase6-rc-promotion-gate-2026-02-21; phase6-rc-runbook-2026-02-21; phase6-rc-runbook-gate-2026-02-21; v0.4.0-rc1
- Active RC artifact path(s): frontend/dashboards/dist/release-candidate.json (missing)

### Recent commit history
- HEAD: 5b9e09d3 chore: update blocker ledger with live codeql evidence
- HEAD~1: 34ca98d3 chore: sync certification ledger to latest head sha
- HEAD~2: 0d275d6a chore: lock certification governance and stabilize proof contracts
- HEAD~3: c9991a48 fix(frontend): finish proof route contract and harden gradebook token request
- HEAD~4: 3e325e6e fix(frontend): stabilize proof gates and token readiness contract

---

## B. PR / Branch Truth

### PR 577
- PR state: OPEN
- Head branch: fix/track11-12-write-and-lifecycle-proof
- Head SHA: 5b9e09d34333f2b57d32708ff0a4dcde621039da
- Base branch: main
- Mergeable: BLOCKED (mergeStateStatus)
- Draft or ready: ready (isDraft=false)
- Summary: Required checks are mixed; gradebook-proof and CodeQL are failing, other listed required checks are passing.

### Other open PRs relevant to release
| PR | Title | Branch | Status | Release-relevant | Notes |
|---|---|---|---|---|---|
| 577 | Proof shell backend write/lifecycle and route integrity fixes | fix/track11-12-write-and-lifecycle-proof | OPEN / BLOCKED | Yes | Active release branch PR |
| 578 | fix: repair broken signals tests and deprecated CheckConstraint.check usage | copilot/fix-issues-in-active-work | OPEN | Potentially | Adjacent fixes against main |
| 579 | Fix aftercare RBAC stubs: replace always-True stubs with real Crown role checks | copilot/fix-next-issues | OPEN | Potentially | Adjacent runtime/security area |
| 580 | chore: repo hygiene — purge artifact files from git, harden SECRET_KEY guard | copilot/assess-efficiency-and-cleanliness | OPEN | Potentially | Hygiene/security scope |

---

## C. CI Truth

| Check Name | Status | Last Run ID / URL | Failure Summary | Required for Merge | Notes |
|---|---|---|---|---|---|
| gradebook-proof | COMPLETED / FAILURE | https://github.com/tcmegahan/Crown2026/actions/runs/23117229036/job/67144801513 | Check run failed | Yes | Workflow: Proof — Gradebook (UI + API) |
| Proof Smoke (Playwright) | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23117229040/job/67144801498 | None | Yes | Workflow: UI Proof Gate |
| dashboard-ui-gates | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23117229017/job/67144801413 | None | Yes | Workflow: UI Proof — Dashboard Gates |
| CodeQL | COMPLETED / FAILURE | https://github.com/tcmegahan/Crown2026/runs/67144861882 | CodeQL check run failed | Yes | Also includes Analyze (python/javascript) jobs |
| phase1-contract | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23117229062/job/67144801508 | None | Yes | Workflow: phase1-gate |
| rc-promotion-gate | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23117229031/job/67144801429 | None | Yes | Workflow: rc-promotion-gate |
| demo-proof-static | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23117229064/job/67144801441 | None | Yes | Workflow: Phase3 Demo Proof Pack Gate |
| demo-surface-static-gate | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23117229030/job/67144801411 | None | Yes | Workflow: demo-surface-gate |
| Audit: Secret scan | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23117229109/job/67144801857 | None | Yes | Workflow: crown-magus0-gate |

---

## D. Artifact Truth

- RC artifact path: frontend/dashboards/dist/release-candidate.json
- RC `build_sha`: UNPROVEN (artifact missing)
- RC `build_tag`: UNPROVEN (artifact missing)
- RC `verified_at`: 2026-03-15 snapshot
- Does RC `build_sha` match current HEAD: UNPROVEN
- Are there multiple RC artifacts present: No evidence of multiple artifacts in local tree
- Notes: RC_MISSING during snapshot command.

---

## E. Deployment Truth

### Frontend deployment
- App name: UNPROVEN
- URL: UNPROVEN
- Deployed SHA: UNPROVEN
- Deployed build tag: UNPROVEN
- Matches certified SHA: UNPROVEN
- Verified by: No live frontend deploy probe in this snapshot

### Backend deployment
- App name: Local dev Django server (observed)
- URL: http://127.0.0.1:8000
- Deployed SHA: local-dev (from /api/health payload)
- Deployed build tag: empty string (from /api/health payload)
- Matches certified SHA: No
- Verified by: Local /api/health probe

### Health / runtime truth
- Frontend health result: UNPROVEN
- Backend health result: /api/health OK; /api/v1/health 404; /api/integrity 400
- Auth flow verified: PASS for local Playwright proof set (11 passed)
- Demo flow verified: PASS for local proof-smoke + student/parent/executive dashboard tests (11 passed)
- Notes: Evidence from _local_playwright_after_fix.log and local endpoint probes.

---

## F. Verified Status Summary

### VERIFIED PASS
- Proof Smoke (Playwright) check is green
- dashboard-ui-gates check is green
- phase1-contract, rc-promotion-gate, demo-proof-static, demo-surface-static-gate, and Audit: Secret scan are green

### VERIFIED FAIL
- gradebook-proof check failed
- CodeQL check failed
- RC artifact file missing locally

### UNPROVEN
- Production frontend deployed SHA/build tag truth
- Production backend deployed SHA/build tag truth
- Certified RC build identity mapping to current HEAD

---

## G. Immediate Release Blockers

| Blocker ID | Title | Bucket | Severity | Current Status | Exact Evidence |
|---|---|---|---|---|---|
| BLOCKER-001 | gradebook-proof check failing | Branch blocker | Critical | Open | https://github.com/tcmegahan/Crown2026/actions/runs/23117229036/job/67144801513 |
| BLOCKER-004 | CodeQL check failing | Branch blocker / Production blocker | High | Open | https://github.com/tcmegahan/Crown2026/runs/67144861882 |
| BLOCKER-008 | RC artifact SHA drift risk (artifact missing) | Branch blocker / Production blocker | High | Open | frontend/dashboards/dist/release-candidate.json -> RC_MISSING |

---

## H. Notes

- Snapshot built from live git and gh CLI on 2026-03-15.
- Latest PR rollup source for this pass: _tmp_completion_pr577_latest.json.
- Local worktree contains untracked docs/completion updates and _tmp_completion_pr577.json.
- Branch merge state is BLOCKED until failing required checks are resolved.
