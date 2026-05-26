# CROWN Current Authority Brief - Executive One-Page (2026-05-26)

## Executive Decision
- Release authority posture for this slice is `FINAL GO`.
- Runtime governance + dashboard truth closure was merged via PR #854.
- Signoff reconciliation was merged via PR #855.
- `origin/main` reflects `FINAL GO` in `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md`.

## Release Truth (Verified)
- PR #854 merge commit: `865bb5d4f2e88bf41b07fad66725403a19529f72`.
- PR #855 merge commit: `a397a47c33d1c8ddc7f7b29b5303ba2a33a96938`.
- Hosted gates confirmed on merged release state:
  - `contract-gate` success
  - `Release Verify` success

## Product Operating Model (Non-Negotiable)
- Layer 1: Core = system-of-record truth, policy, identity, tenancy, release controls.
- Layer 2: Modules = domain workflows that consume canonical Core contracts.
- Layer 3: Add-ons = optional capabilities and integrations; never truth owners.
- Rule: no module/add-on may fork canonical truth.

## Reset / Purge Doctrine (Current)
- Reset is an operational control, not product behavior.
- Sandbox reset allowed only with deterministic credentials and local endpoints.
- No production secrets/data in sandbox/reset workflows.
- Reset-capable surfaces require explicit policy ownership and rationale.

## 30-Day Sprint Operating System (Control Slice)
- Week 1: canonical state machine + checklist model.
- Week 2: family checklist UI + admissions timeline.
- Week 3: scheduling + decision rubric + conversion hardening.
- Week 4: analytics + SLA alerts + mission-fit pilot flag.

Definition of Done (strict): migration rollback tested, permission matrix verified, contract tests complete, parent/staff smoke green, audit trail present, dashboard truth explicit, CI gates green/no stuck required checks.

## Team Ownership Map (Authority View)
- Control lanes:
  - Release Authority
  - Architecture
  - Security
  - Product/Operations
- Domain/platform ownership signals:
  - Platform Security, Admissions Platform, Governance Platform, Identity Platform, Advancement Payments, Platform Engineering
- Open ownership items to resolve:
  - Teams preview endpoint production usage (`UNKNOWN`)
  - aid vs financial_aid ownership split (`PARTIAL`)

## High-Risk Verification Command Set
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

## Immediate Next Actions (Repo Truth + Production Readiness)
1. Freeze this brief as authority baseline for this cycle.
2. Resolve ownership unknowns with named owners + due dates.
3. Publish single route ownership canon for Core vs Modules.
4. Run high-risk verification set each release-candidate cut and archive outputs.
5. Enforce evidence-first authority updates only.
6. Keep competitor benchmarking pattern-only (no code import, no uncontrolled scope expansion).
7. Start next readiness review by diffing evidence after merge `a397a47c33d1c8ddc7f7b29b5303ba2a33a96938`.

## Source of Truth Documents
- `audit-artifacts/runtime-release-closure/20260418_070051/CROWN_CURRENT_AUTHORITY_BRIEF_20260526.md`
- `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md`
- `docs/release/LIVE_HOSTED_CI_HANDOFF_20260526.md`
- `docs/release/GITHUB_ACTIONS_ESCALATION_PACKET_PR854_20260526.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/ASSUMPTIONS_REGISTER.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/PUBLIC_ENDPOINT_POLICY_MATRIX.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/CSRF_EXCEPTION_POLICY_MATRIX.md`
