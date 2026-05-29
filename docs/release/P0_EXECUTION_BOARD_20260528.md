# P0 Execution Board - 2026-05-29

Purpose: close only the blockers that prevent transition from CONDITIONAL GO to unrestricted GO.

Canonical authority baseline:

- Repository-wide decision is CONDITIONAL GO (`docs/CURRENT_RELEASE_STATUS.md`).
- Deploy SHA parity is PARTIAL / NOT YET CLOSED (`docs/CURRENT_RELEASE_STATUS.md`).
- Current scorecard marks Deploy SHA parity and Release authority convergence as PARTIAL (`docs/release/CURRENT_RELEASE_SCORECARD_20260528.md`).
- Supporting ranked closure backlog: `docs/release/PRODUCTION_RELEASE_TOP_10_REMAINING_TASKS_20260528.md`.

## Scope and Guardrails

- No net-new feature work.
- No broad refactors.
- Minimal, surgical edits with explicit evidence capture.
- Every task closes with a committed artifact proving pass/fail.

## Dates

- Sandbox readiness target: 2026-06-01
- Production readiness target: 2026-07-01

## P0 Workboard

| ID | Priority | Work Item | Owner | Due | Acceptance Criteria | Required Evidence Artifact | Status |
|---|---|---|---|---|---|---|---|
| P0-1 | Critical | Close deploy SHA parity for release target | Solo owner | 2026-05-30 | Canonical authority packet proves release target SHA equals approved source SHA, with verification command outputs included and timestamped. | `docs/release/DEPLOY_SHA_PARITY_PACKET_YYYYMMDD.md` updated and linked from `docs/CURRENT_RELEASE_STATUS.md` | OPEN |
| P0-2 | Critical | Canonicalize release authority and supersede conflicting historical docs | Solo owner | 2026-05-31 | Exactly one controlling authority source for repository-wide go/no-go is explicit. All legacy GO/PARTIAL/FAIL docs are labeled historical/superseded with clear forward pointer. | `docs/CURRENT_RELEASE_STATUS.md` updated + supersession notes in each legacy authority doc | OPEN |
| P0-3 | Critical | Re-run authoritative runtime + policy gate on release candidate SHA | Solo owner | 2026-05-31 | Runtime protected-spine packet and policy gates are green on the exact candidate SHA that parity packet references. | Runtime packet in `audit-artifacts/runtime-release-closure/...` + policy gate evidence in `docs/security/...` | OPEN |
| P0-4 | High | Parent360 silent-failure hardening (observability-only) | Solo owner | 2026-06-01 | Broad exception paths retain graceful degradation but emit structured, stage-specific warning/error context for triage. No behavioral regression in response contract. | Diff + targeted test evidence for `backend/parent360/api/views.py` | COMPLETE (2026-05-28) |
| P0-5 | High | Parent360 continuity regression guardrail tests | Solo owner | 2026-06-01 | Tests assert admissions continuity payload shape, degraded optional-import behavior, and key summary counters. | New/updated pytest outputs committed under release evidence packet | COMPLETE (2026-05-28) |
| P0-6 | Critical | Final unrestricted-GO gate decision packet | Solo owner | 2026-06-01 | Unrestricted GO declared only if all P0 criteria are passed with zero contradictory authority statements. | `docs/CURRENT_RELEASE_STATUS.md` final gate update + updated scorecard | OPEN |

## Definition of Done (P0)

All items below must be true simultaneously:

1. Deploy SHA parity: CLOSED.
2. Authority convergence: CLOSED (no contradictory live authority statements).
3. Runtime and policy proof: GREEN on release-candidate SHA.
4. Parent360 critical observability and regression guardrails: GREEN.
5. Canonical status and scorecard reflect the same final state.

## Verification Checklist for 2026-06-01 Sandbox Gate

- [ ] `python manage.py check` passes.
- [ ] Authoritative protected-spine packet on candidate SHA is green.
- [ ] Policy gates (public surface and CSRF exception controls) are green.
- [ ] SHA parity packet references exact candidate SHA and is signed in authority docs.
- [ ] No contradictory release authority docs remain unsuperseded.

## Verification Checklist for 2026-07-01 Production Gate

- [ ] All sandbox gate checks remain green after final release candidate freeze.
- [ ] No high-severity regressions in targeted backend/frontend gate suites.
- [ ] Final release notes and public status docs match canonical authority.
- [ ] Post-deploy proof path is pre-declared and owner-confirmed.

## Escalation Rule

If any P0 acceptance criterion fails, release posture remains CONDITIONAL GO and cannot be advanced by narrative justification.

## Execution Updates

### 2026-05-28 - P0-4 completion evidence

- File updated: `backend/parent360/api/views.py`
- Added centralized degraded-path instrumentation helper and wired broad exception handlers to stage-specific warnings.
- Validation evidence:
  - `python manage.py check` -> `System check identified no issues (0 silenced).`
  - `python -m pytest parent360 -q` -> `4 passed in 75.24s`.

### 2026-05-28 - P0-5 completion evidence

- File updated: `backend/parent360/tests/test_parent_overview_api.py`
- Added regression tests covering:
  - admissions continuity payload shape and zero-state summary counters,
  - degraded optional-import behavior for admissions dependencies.
- Validation evidence:
  - `python -m pytest parent360 -q` -> `6 passed in 82.66s`.

### 2026-05-29 - P0-1 execution evidence (status remains OPEN)

- Runner executed: `pwsh -File scripts/release/44_capture_deploy_sha_parity.ps1 -HealthJsonPath audit-artifacts/release-certification/20260513_223241/02_health.json -IntegrityJsonPath audit-artifacts/release-certification/20260513_223241/02_integrity.json`
- Output artifacts:
  - `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260529_022049.md`
  - `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260529_022049.json`
- Evaluation result:
  - `parity_status=OPEN`
  - `matches_approved_release_sha=false`
  - `matches_local_head_sha=false`
  - `evidence_count=2`

### 2026-05-29 - Ranked closure backlog artifact added

- Added: `docs/release/PRODUCTION_RELEASE_TOP_10_REMAINING_TASKS_20260528.md`
- Purpose: ranked, evidence-oriented closure queue aligned to P0 blockers and 95+ readiness controls.
- Scope guardrail: no production claim expansion to draft/unmerged modules.

### 2026-05-29 - P0-1 rerun evidence (status remains OPEN)

- Runner executed: `pwsh -File scripts/release/44_capture_deploy_sha_parity.ps1 -HealthJsonPath audit-artifacts/release-certification/20260513_223241/02_health.json -IntegrityJsonPath audit-artifacts/release-certification/20260513_223241/02_integrity.json -DeployTargetSha d793766b6640d88a4bfdb87c999f429e06cd87ec -ApprovedReleaseSha d793766b6640d88a4bfdb87c999f429e06cd87ec`
- Output artifacts:
  - `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260529_081638.md`
  - `docs/release/live-audit/deploy-sha-parity/deploy_sha_parity_20260529_081638.json`
- Evaluation result:
  - `parity_status=OPEN`
  - `matches_approved_release_sha=false`
  - `matches_local_head_sha=false`
  - `evidence_count=3`

### 2026-05-29 - P0-3 first-blocker evidence (status remains OPEN)

- Runner attempted:
  - `pwsh -File audit-artifacts/runtime-release-closure/20260418_070051/72_run_protected_spine_subbatches.ps1 -RepoRoot C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr -EvidenceRoot C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr/audit-artifacts/runtime-release-closure/20260418_070051 -TimeoutSeconds 1200`
  - direct auth/security batch run with explicit target list and stdout capture.
- Output artifacts:
  - `docs/release/live-audit/protected-spine/protected_spine_hang_triage_20260529_042753.md`
  - `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_AUTH_SECURITY_MANUAL_20260529_042753.txt`
  - `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_SUBBATCH_TARGETS_auth_security_baseline_20260529_042439.txt`
- Evaluation result:
  - protected-spine auth/security baseline stalls immediately after Django early diagnostics.
  - no new protected-spine packet produced for current run stamp.
  - P0-3 remains OPEN and is currently blocked by runtime hang isolation.
