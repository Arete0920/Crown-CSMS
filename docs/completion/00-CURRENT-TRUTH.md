# Crown2026 — Current Truth Snapshot

## Snapshot Metadata

- Date: 2026-03-15
- Prepared by: GitHub Copilot (GPT-5.4)
- Repository: tcmegahan/Crown2026
- Purpose: Establish exact current truth for Crown2026 at this moment.

---

## A. Repository Truth

- Current branch: main
- Current HEAD SHA: 550d84b23dbfb85cdbc5a75705110d691ac8eca9
- Current working tree status: clean in the authoritative main follow-up worktree
- Is local `main` clean: Yes
- Is local `main` ahead/behind remote: synced to origin/main
- Current release-relevant branch: main
- Current release-relevant PR(s): none open; PR #577 is merged
- Active RC tag(s): phase6-rc-gate-2026-02-21; phase6-rc-live-probes-2026-02-21; phase6-rc-promotion-gate-2026-02-21; phase6-rc-runbook-2026-02-21; phase6-rc-runbook-gate-2026-02-21; v0.4.0-rc1
- Active RC artifact path(s): frontend/dashboards/dist/release-candidate.json (missing)

### Recent commit history
- HEAD: 550d84b2 feat(frontend): stabilize tracks 24-33 with proof, token, route, and security fixes
- HEAD~1: f8fa1169 fix: sanitize API error and html output paths
- HEAD~2: 5d55832f fix: resolve CodeQL security findings in APIs
- HEAD~3: 5bda1a0e fix(ci): use same-origin api base in gradebook ui proof workflow
- HEAD~4: 013f219d fix(proof): seed role context for gradebook ui proof

---

## B. PR / Branch Truth

### PR 577
- PR state: MERGED
- Head branch: fix/track11-12-write-and-lifecycle-proof
- Merge commit SHA: 550d84b23dbfb85cdbc5a75705110d691ac8eca9
- Base branch: main
- Merged at: 2026-03-15T20:59:18Z
- Draft or ready: ready (merged from ready state)
- Summary: Required merge gates named in the release slice were green, the PR merged, and main now points at the merge commit.

### Other open PRs relevant to release
| PR | Title | Branch | Status | Release-relevant | Notes |
|---|---|---|---|---|---|
| 578 | fix: repair broken signals tests and deprecated CheckConstraint.check usage | copilot/fix-issues-in-active-work | OPEN | Potentially | Adjacent fixes against main |
| 579 | Fix aftercare RBAC stubs: replace always-True stubs with real Crown role checks | copilot/fix-next-issues | OPEN | Potentially | Adjacent runtime/security area |
| 580 | chore: repo hygiene — purge artifact files from git, harden SECRET_KEY guard | copilot/assess-efficiency-and-cleanliness | OPEN | Potentially | Hygiene/security scope |
| 581 | [WIP] Close multiple open pull requests and issues | copilot/close-pull-requests-and-issues | OPEN / DRAFT | Potentially | Triage/meta workflow branch |

---

## C. CI Truth

| Check Name | Status | Last Run ID / URL | Failure Summary | Required for Merge | Notes |
|---|---|---|---|---|---|
| gradebook-proof | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227638/job/67147413098 | None | Yes | Workflow: Proof — Gradebook (UI + API) |
| Proof Smoke (Playwright) | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227658/job/67147413184 | None | Yes | Workflow: UI Proof Gate |
| dashboard-ui-gates | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227607/job/67147413027 | None | Yes | Workflow: UI Proof — Dashboard Gates |
| CodeQL | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/runs/67147473952 | 1 new alert summary shown in check text, but overall check result is success | Yes | Aggregate CodeQL gate is green |
| Analyze (javascript) | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227620/job/67147413022 | None | Supporting | CodeQL analysis job |
| Analyze (python) | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227620/job/67147413019 | None | Supporting | CodeQL analysis job |
| phase1-contract | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227635/job/67147413040 | None | Yes | Workflow: phase1-gate |
| rc-promotion-gate | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227641/job/67147413050 | None | Yes | Workflow: rc-promotion-gate |
| demo-proof-static | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227615/job/67147412983 | None | Yes | Workflow: Phase3 Demo Proof Pack Gate |
| demo-surface-static-gate | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227626/job/67147413021 | None | Yes | Workflow: demo-surface-gate |
| Audit: Secret scan | COMPLETED / SUCCESS | https://github.com/tcmegahan/Crown2026/actions/runs/23118227614/job/67147413055 | None | Yes | Workflow: crown-magus0-gate |

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
- App name: UNPROVEN
- URL: UNPROVEN
- Deployed SHA: UNPROVEN
- Deployed build tag: UNPROVEN
- Matches certified SHA: UNPROVEN
- Verified by: No production backend deploy probe in this snapshot

### Health / runtime truth
- Frontend health result: UNPROVEN
- Backend health result: UNPROVEN for production
- Auth flow verified: PASS for local Playwright proof set (11 passed)
- Demo flow verified: PASS for local proof-smoke + student/parent/executive dashboard tests (11 passed)
- Notes: Evidence from _local_playwright_after_fix.log only; production runtime proof was not refreshed in this pass.

---

## F. Verified Status Summary

### VERIFIED PASS
- PR 577 merged to main
- gradebook-proof is green
- CodeQL plus Analyze (javascript/python) are green
- Proof Smoke (Playwright) and dashboard-ui-gates are green
- phase1-contract, rc-promotion-gate, demo-proof-static, demo-surface-static-gate, and Audit: Secret scan are green

### VERIFIED FAIL
- RC artifact file missing locally

### UNPROVEN
- Production frontend deployed SHA/build tag truth
- Production backend deployed SHA/build tag truth
- Certified RC build identity mapping to current HEAD

---

## G. Immediate Release Blockers

| Blocker ID | Title | Bucket | Severity | Current Status | Exact Evidence |
|---|---|---|---|---|---|
| BLOCKER-008 | RC artifact SHA drift risk (artifact missing) | Release blocker / Production blocker | High | Open | frontend/dashboards/dist/release-candidate.json -> RC_MISSING |
| BLOCKER-010 | Production deploy truth unproven | Production blocker | Critical | Open | No deployed frontend/backend SHA verification linked on merged main |

---

## H. Notes

- Snapshot updated from merged main at 550d84b23dbfb85cdbc5a75705110d691ac8eca9.
- PR truth source: https://github.com/tcmegahan/Crown2026/pull/577.
- Original workspace still contains local, uncommitted gradebook proof spec edits, so authoritative main truth was refreshed from a clean follow-up worktree.
- Branch merge state for PR 577 is now MERGED.
