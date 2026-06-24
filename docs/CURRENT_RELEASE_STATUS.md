# CROWN Current Release Status

Date: 2026-06-23
Purpose: Single canonical repository-level release posture for CROWN.

## Canonical Authority

1. This file is the canonical repository-level release authority.
2. Current controlling posture is **NO-GO / RELEASE FREEZE** until final same-SHA release evidence is current, green, and explicitly promoted here.
3. Historical GO, SHIP, PASS, RELEASE_READY, PARTIAL, prior candidate-SHA documents, local transcript notes, and superseded audit packets are non-authoritative unless this file explicitly promotes them.
4. Product, sandbox, pilot, and production claims must be based on current repository evidence and same-SHA gate settlement, not stale packets or memory.

## Current Decision

Repository-wide decision: NO-GO.
Current controlling posture remains **RELEASE FREEZE**.

Decision meaning:

- Current repository evidence shows substantial completion progress and strong proof coverage.
- Current completion evidence is controlled by `docs/LIVE_EVIDENCE_AUTHORITY_20260622.md`.
- Production release remains blocked until current-head release verification, sandbox-ready evidence, local repo hygiene, and governance evidence are all clean and same-SHA consistent.
- Broad sandbox launch remains blocked until sandbox-ready evidence gates pass on the same current candidate SHA and local worktree hygiene is closed.

## Current GitHub Evidence Snapshot

- Default branch: `main`.
- Candidate SHA: `8097d4c23e847bfaced4d9a49637a3aa0e20617b`.
- Release authority branch: `release/security-runtime-governance-repair-little-lambs-full-build`.
- Current live evidence authority PR: #1161, merged into `main`.
- Current live evidence authority merge commit: `2f405d4`.
- Follow-up release-status PR #1162 was closed unmerged because its candidate branch did not have clean release/sandbox gates.
- Open PR count is not controlled by this static file; verify current PR state live through the GitHub connector when making current-status decisions.

## Current Product Completion Evidence

Use `docs/LIVE_EVIDENCE_AUTHORITY_20260622.md` first for current completion/status work.

| Area | Current verified status | Current authority |
| --- | --- | --- |
| Modules | 51 / 51 PROVEN | `audit-artifacts/module-completion/current/05_completion_scorecard.md` |
| Dashboards | 40 / 40 certified for internal dashboard scope | `audit-artifacts/dashboard-completion/state/dashboard-certification-state.json` |
| Wizards | CERTIFIED | `audit-artifacts/wizard-certification/current/FINAL_WIZARD_CERTIFICATION_20260622.md` |
| Components | CERTIFIED BY PARENT SURFACE COVERAGE | `audit-artifacts/component-widget-certification/current/COMPONENT_CERTIFICATION_MATRIX_20260622.csv` |
| Widgets | CERTIFIED BY PARENT SURFACE COVERAGE | `audit-artifacts/component-widget-certification/current/WIDGET_CERTIFICATION_MATRIX_20260622.csv` |
| Production release | NOT APPROVED | This file plus clean same-SHA release evidence required |

## Current Blocking Conditions

### 1. Same-SHA release verification is not yet clean

A final current-head release-certification packet must show:

- `00_release_certification_summary.json` final status PASS;
- zero RED lanes;
- zero AMBER lanes unless explicitly approved as non-production-blocking;
- branch-protection evidence;
- backend/runtime health, integrity, OpenAPI, migrations, and deploy-check evidence;
- golden path, tenant isolation, and UI evidence;
- phase2 reporting/export/transcript and sandbox role-route regression evidence;
- final signoff packet.

### 2. Candidate frontend gates require hardening

The closed #1162 candidate exposed gate fragility that must be corrected before promotion:

- `Release Verify` failed at frontend smoke.
- `Sandbox Ready Evidence Gate` failed at frontend unit tests.

These failures are release-gate blockers unless a current-main rerun proves they are no longer present.

### 3. Local repo hygiene is not connector-visible

Local worktree state is not visible through the GitHub connector. Current local hygiene remains blocking until a fresh local packet proves:

- `deleted_count=0`;
- `nested_pending=0`;
- root untracked noise quarantined, deleted, or intentionally retained outside product scope;
- all root dirty entries classified;
- no blank triage decisions;
- no unresolved `NEEDS REVIEW` rows;
- no cleanup artifacts mixed into product repair branches.

### 4. Governance must remain accurate

- Solo-developer workaround may be recorded where applicable.
- Do not claim independent human review unless independent review actually occurred.
- Do not ask the project owner to self-review or self-approve their own work.

### 5. Release authority hygiene must stay converged

Only this file controls repository-level release posture. Stale historical release, GO, SHIP, PASS, or certification material must remain explicitly superseded unless promoted here with current same-SHA evidence.

## Allowed Language Now

Allowed:

- "CROWN has current proof-backed completion evidence for modules, dashboards, wizards, components, and widgets within the documented certification scopes. Repository-level posture remains NO-GO pending clean same-SHA release verification, sandbox-ready evidence, local hygiene closure, and governance closure."
- "Validated slices may be described as validated only when their evidence is current and cited."

Not allowed:

- "Repository is production ready."
- "CROWN is unrestricted GO."
- "Sandbox is broadly approved."
- "Latest head is release-certified" unless the current-head release-certification packet proves it.
- "Independent review is complete" unless it is independently evidenced.

## Required Closure Sequence

1. Close local repo-hygiene gate from the main repo root.
2. Reproduce and fix the frontend smoke/unit failures surfaced by the #1162 candidate branch, unless a current-main rerun proves them gone.
3. Generate a clean current-head release-certification packet.
4. Run sandbox-ready evidence gate on the same current candidate SHA.
5. Confirm same-SHA gate settlement: pending=0, failed=0, cancelled=0 for required release gates.
6. Confirm governance language: solo-developer workaround recorded where applicable; no false independent-review claim.
7. Update this file only after the evidence above is current, green, and same-SHA consistent.

## Current Final Status

**NO-GO / RELEASE FREEZE**.
