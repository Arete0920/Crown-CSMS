# CROWN Current Authority Brief (2026-05-26)

## 1) Verified Release / Governance Status

### Authoritative state
- PR #854 (Runtime Governance Gate + Dashboard Truth Disclosure Closure) is merged to `main`.
- Merge commit: `865bb5d4f2e88bf41b07fad66725403a19529f72`.
- Hosted gates for that merge commit were reported green for:
  - `contract-gate`
  - `Release Verify`
- PR #855 (signoff reconciliation) was merged by squash.
- Merge commit: `a397a47c33d1c8ddc7f7b29b5303ba2a33a96938`.
- `origin/main` release authority memo now reflects `FINAL GO`:
  - `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md`

### Governance evidence anchors
- `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md`
- `docs/release/LIVE_HOSTED_CI_HANDOFF_20260526.md`
- `docs/release/GITHUB_ACTIONS_ESCALATION_PACKET_PR854_20260526.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/ALL_PRIORITIES_EXECUTION_STATUS_20260526.md`

## 2) Product Model: Core / Modules / Add-ons (Strict)

### Canon model
- Layer 1: Core (platform/system-of-record controls)
- Layer 2: Modules (domain workflows on canonical truth)
- Layer 3: Add-ons (optional surfaces, never truth owners)

### Operating rule
- Core defines canonical state, policy, identity, tenant boundaries, and release truth.
- Modules consume and extend Core contracts, but do not fork truth models.
- Add-ons may integrate and visualize, but cannot mutate authoritative state outside Core governance.

### Source references
- `audit-artifacts/runtime-release-closure/20260418_070051/LAYER_ALIGNMENT_AUDIT.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/CURRENT_STATE_VERIFICATION.md`

## 3) Current Reset Doctrine

### Guardrails
- Reset/purge actions are controlled operational tools, not product behavior.
- Sandbox/demo reset is allowed only with deterministic local credentials and local endpoints.
- No production secrets or production data exports in sandbox/reset workflows.
- Every reset-capable surface requires explicit policy ownership and rationale.

### Policy/operational controls
- Public/auth exception surfaces are policy-inventory controlled and owner-tagged.
- Demo/system reset paths are designated temporary operational utilities.
- Teams channel remains UI-only; final approval truth persists only in CROWN entities.

### Source references
- `audit-artifacts/runtime-release-closure/20260418_070051/PARENT_SANDBOX_ISOLATION_RUNBOOK_20260522.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/CSRF_EXCEPTION_POLICY_MATRIX.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/PUBLIC_ENDPOINT_POLICY_MATRIX.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/TEAMS_APPROVAL_WORKFLOW_PLAN.md`

## 4) 30-Day Sprint Operating System

### Weekly control slice
- Week 1: canonical admissions state machine + checklist data model
- Week 2: family checklist UI + admissions timeline
- Week 3: interview scheduling + decision rubric enforcement + conversion hardening
- Week 4: funnel analytics + SLA aging alerts + mission-fit module pilot flag

### Definition of Done (strict)
A change closes only when all are true:
1. Migration and rollback tested.
2. Permission matrix verified by role.
3. API contract tests cover happy + negative + tenant isolation.
4. Parent and staff runtime-smoke verified.
5. Audit trail exists for state changes/decisions.
6. Dashboards tied to live sources or explicitly fallback-labeled.
7. CI gates green with no stuck required checks.

### Source references
- `audit-artifacts/runtime-release-closure/20260418_070051/ADMISSIONS_FUNNEL_RECOMMENDATIONS_REVIEW_20260522.md`

## 5) Team Ownership Map (Current Authority View)

### Lane owners (control plane)
- Release Authority lane: release decision and publication authority
- Architecture lane: canonical model boundaries and module integrity
- Security lane: public/auth exception policy control
- Product/Operations lane: scope, rollout controls, and operational readiness

### Domain/platform ownership signals (from policy matrices)
- Platform Security: public health and governance-safe exposures
- Admissions Platform: admissions public config/submit surfaces
- Governance Platform: public roadmap/release notes surfaces
- Identity Platform: auth login/refresh CSRF exception surfaces
- Advancement Payments: payment webhook exception surfaces
- Platform Engineering: temporary operational utilities (demo reset, schema diagnostics/fixes, CI helpers)

### Explicit unresolved ownership/authority items
- Teams preview endpoint production usage level: `UNKNOWN`
- Aid vs financial_aid active ownership split: `PARTIAL`

### Source references
- `audit-artifacts/runtime-release-closure/20260418_070051/BINDER_SIGNOFF_PACKET.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/PILOT_AUTHORIZATION_CLOSURE_CHECKLIST_20260507.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/PUBLIC_ENDPOINT_POLICY_MATRIX.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/CSRF_EXCEPTION_POLICY_MATRIX.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/ASSUMPTIONS_REGISTER.md`

## 6) High-Risk Verification Commands (Authoritative Run Set)

### Full release verification sequence
```powershell
powershell -ExecutionPolicy Bypass -File scripts/release/verify_all_15_phases.ps1
powershell -ExecutionPolicy Bypass -File scripts/release/11_verify_import_and_migrations.ps1
powershell -ExecutionPolicy Bypass -File scripts/release/12_verify_backend_urls_and_health.ps1
powershell -ExecutionPolicy Bypass -File scripts/release/13_verify_workflows_and_deploy_risk.ps1
.venv/Scripts/python.exe tools/verify_backend_gate.py
.venv/Scripts/python.exe tools/verify_url_surface.py
.venv/Scripts/python.exe tools/audit_backend_integrity.py
.venv/Scripts/python.exe tools/verify_workflow_policy.py
```

### Runtime closure convenience wrappers (this folder)
```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\release\11_verify_import_and_migrations.ps1
powershell.exe -ExecutionPolicy Bypass -File .\scripts\release\12_verify_backend_urls_and_health.ps1
powershell.exe -ExecutionPolicy Bypass -File .\scripts\release\13_verify_workflows_and_deploy_risk.ps1
```

### Recent release-truth spot checks
```powershell
gh pr view 855 --repo tcmegahan/Crown2026 --json state,mergedAt,mergeCommit,headRefName,baseRefName,url
git fetch origin main
git show origin/main:docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md | Select-String -Pattern "## Decision","FINAL GO" -CaseSensitive
```

### Source references
- `audit-artifacts/runtime-release-closure/20260418_070051/CURRENT_INTEGRITY_ASSESSMENT_20260523.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/11.ps1`
- `audit-artifacts/runtime-release-closure/20260418_070051/12.ps1`
- `audit-artifacts/runtime-release-closure/20260418_070051/13.ps1`
- `audit-artifacts/runtime-release-closure/20260418_070051/15.ps1`

## 7) Immediate Next Actions (Repo Truth + Production-Readiness Review)

1. Freeze this brief as current authority baseline for this cycle.
2. Resolve open ownership unknowns in `ASSUMPTIONS_REGISTER.md` with named owners and due dates.
3. Publish/confirm a single route ownership canon for Core vs Modules boundaries.
4. Run the high-risk verification set once per release-candidate cut and archive outputs under `audit-artifacts/verify-high-risk/`.
5. Enforce evidence-first updates: no authority statement changes without matching hosted gate evidence and artifact references.
6. Continue competitor review as pattern-only input (no code import, no scope expansion) under controlled benchmark guardrails.
7. Start next production-readiness review from this brief, then diff only new evidence since merge commit `a397a47c33d1c8ddc7f7b29b5303ba2a33a96938`.

## 8) Authority Statement

As of 2026-05-26, current authority posture for this release slice is `FINAL GO`, with PR #854 and PR #855 merged and release signoff reconciled on `main`.
