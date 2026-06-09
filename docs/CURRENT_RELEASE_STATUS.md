# CROWN Current Release Status

Date: 2026-06-09
Purpose: Single canonical repository-level release posture for CROWN.

## Canonical Authority

1. This file is the canonical repository-level release authority.
2. Current controlling posture is **NO-GO / RELEASE FREEZE** until the required evidence gates below pass on the same current candidate SHA.
3. Historical GO, SHIP, PASS, RELEASE_READY, PARTIAL, or prior candidate-SHA documents are non-authoritative unless this file explicitly promotes them.
4. Product, sandbox, and production claims must be based on current-head evidence, not stale packets or local transcript memory.

## Current Decision

Repository-wide decision: NO-GO.

Decision meaning:

- CROWN has substantial architecture and verification infrastructure.
- Recent release-certification harness fixes are merged into `main`.
- Production release is blocked until current-head release-certification evidence, live-data proof, dashboard/runtime proof, and repo-hygiene proof are all current and green.
- Broad sandbox launch is blocked until sandbox evidence gates pass on the same current candidate SHA and local worktree hygiene is closed.

## Current GitHub Evidence Snapshot

- Latest inspected main SHA: `56f2d784fd6b4dd0c261245c0f603d508cf09861`.
- Candidate SHA: `8097d4c23e847bfaced4d9a49637a3aa0e20617b`
- Release authority branch: `release/security-runtime-governance-repair-little-lambs-full-build`
- Candidate/branch metadata above is retained to keep ready-entry evidence contracts parseable; it is not a current production-release approval and does not override the repository-wide NO-GO decision.
- PR #950: merged; current release authority refresh preserving NO-GO / RELEASE FREEZE.
- PR #949: merged; wizard backend contract parity matrix.
- PR #948: merged; guarded runtime wizard route and sandbox regression alignment.
- PR #947: merged; parallel-work synchronization protocol.
- PR #946: merged; Windows command-wrapper capture diagnostic gate.
- PR #945: merged; repo hygiene gate packet generator.
- PR #944: merged; frontend/backend wizard parity verifier.
- PR #941: merged; one-file release-certification step01 fallback hardening.
- PR #940: merged; earlier step01 branch-protection 404 fallback repair.
- PR #939: merged; release-certification step06 deterministic finalization.
- PR #938: merged; release-certification step02 supplemental orchestration hardening.
- PR #933: merged; clean two-file wizard shell-readiness/auth integrity repair.
- PR #909: closed unmerged; remains historical no-go/release-freeze evidence and must not be treated as a current release lane.

## Current Blocking Conditions

### 1. Current-head release-certification proof is missing

A current release-certification packet must be generated from a clean current main or approved release branch and must show:

- `00_release_certification_summary.json` final status PASS;
- zero RED lanes;
- zero AMBER lanes unless explicitly approved as non-production-blocking;
- branch-protection evidence;
- backend/runtime health, integrity, OpenAPI, migrations, and deploy check evidence;
- golden path, tenant isolation, and UI evidence;
- phase2 reporting/export/transcript and sandbox role-route regression evidence;
- final signoff packet.

### 2. Local repo hygiene is not closed

Local worktree state is not visible through GitHub. Current local hygiene remains blocking until a fresh local packet proves:

- `deleted_count=0`;
- `nested_pending=0`;
- root untracked noise quarantined or intentionally retained outside product scope;
- all root dirty entries classified;
- no blank triage decisions;
- no unresolved `NEEDS REVIEW` rows;
- no cleanup artifacts mixed into product repair branches.

### 3. Dashboard live-data completion remains blocked

Dashboard registry coverage is not equivalent to live operational completion. Production/full-completion claims remain blocked until every production-visible dashboard has live service/API-backed data provenance or is accurately marked unavailable/non-production-visible.

### 4. Wizard completion is not yet all-wizard proven

Wizard architecture exists, but all-wizard completion requires current evidence for each production-visible wizard:

- frontend route registered;
- backend registry entry present;
- frontend `apiPrefix` matches backend URL prefix;
- component renders;
- role access enforced;
- tenant boundary enforced;
- session create/load/save/resume works;
- submit/commit persists expected records;
- failure states are handled;
- tests and/or UI proof artifacts are current.

### 5. Release authority hygiene must stay converged

Only this file controls repository-level release posture. Any stale historical release, GO, SHIP, PASS, or certification document must remain explicitly superseded unless promoted here with current evidence.

## Allowed Language Now

Allowed:

- "CROWN has substantial architecture and verification infrastructure. Repository-level posture is NO-GO pending current-head evidence, live-data proof, wizard/runtime proof, and local hygiene closure."
- "Validated slices may be described as validated only when their evidence is current and cited."

Not allowed:

- "Repository is production ready."
- "CROWN is unrestricted GO."
- "All dashboards are complete."
- "All wizards work."
- "Sandbox is broadly approved."
- "Latest head is release-certified" unless the current-head release-certification packet proves it.

## Required Closure Sequence

1. Close local repo-hygiene gate from the main repo root.
2. Generate a clean current-head release-certification packet.
3. Generate frontend/backend wizard parity and runtime matrix.
4. Close dashboard live-data/template blockers for production-visible surfaces.
5. Run sandbox-ready evidence gate on current head.
6. Update this file only after the evidence above is current, green, and same-SHA consistent.

## Current Final Status

**NO-GO / RELEASE FREEZE**.
