# CROWN Repository Noise Inventory

**Date:** 2026-07-28  
**Repository:** `tcmegahan/Crown2026`  
**Operating state:** owner-directed freeze / production NO-GO

## Purpose

This inventory records verified repository-noise dispositions after the production-readiness program was terminated. It is a cleanup and preservation record, not production evidence or release authorization.

## Disposition model

- `KEEP — CURRENT`: active authority or required source.
- `KEEP — HISTORICAL`: useful lineage or decision record; not current authority.
- `RESTRICT — SENSITIVE`: retained only under controlled access.
- `ARCHIVE`: useful but removed from normal onboarding/operation.
- `CONSOLIDATE`: duplicate or conflicting material to reconcile into a named authority.
- `DISABLE`: retained but prevented from executing.
- `DELETE`: verified obsolete, generated, duplicate, or misleading material with no current dependency.
- `REVIEW REQUIRED`: insufficient evidence for safe deletion.

## Verified cleanup completed

| Item | Disposition | Reason |
|---|---|---|
| `.github/workflows/p0-go-readiness.yml` | DELETE | Retired certification workflow; automatic issue posting and Azure/release activity no longer valid under freeze. |
| `.github/workflows/live-runtime-certification.yml` | DELETE | Deployment-triggered runtime certification no longer active; retained entry created Actions-menu noise. |
| `scripts/ci/publish_live_evidence_result.py` | DELETE | Sole purpose was posting automated evidence to closed/superseded issues. |
| `scripts/execution/997_azure_p0_current_parity_probe.ps1` | DELETE | Unreferenced one-time P0 Azure parity machinery after workflow retirement. |
| `scripts/execution/999_finish_right_4h_gauntlet.ps1` | DELETE | Unreferenced release-gauntlet orchestrator after workflow retirement. |
| Closed issues #1619, #1620, #1626–#1632 | KEEP — HISTORICAL / LOCKED | Preserve controlling program history and explicit NO-GO disposition; remove stale `release-blocker` labeling. |
| `README.md` | KEEP — CURRENT | Updated canonical freeze orientation. |
| `docs/CURRENT_RELEASE_STATUS.md` | KEEP — CURRENT | Updated canonical release/freeze authority. |

## Current authoritative areas

| Area | Disposition | Boundary |
|---|---|---|
| `backend/` | KEEP — CURRENT | Runtime and domain source; no broad cleanup without code-level dependency proof. |
| `frontend/` | KEEP — CURRENT | Runtime and browser source; generated build/test output remains excluded by `.gitignore`. |
| `docs/canonical/` | KEEP — CURRENT | Document authority and repository classification. |
| `docs/operations/` | KEEP — CURRENT | Canonical operations home, subject to freeze-status consistency. |
| `docs/engineering/` | KEEP — CURRENT | Setup and engineering controls; stale release instructions require file-level review. |
| `SECURITY.md`, `CONTRIBUTING.md`, `CODEOWNERS`, `AGENTS.md` | KEEP — CURRENT | Governance and security controls, with successor updates deferred. |

## Historical and evidence areas

| Area | Disposition | Boundary |
|---|---|---|
| `audit-artifacts/` | REVIEW REQUIRED | Mixed generated and intentionally retained evidence. Delete only after file-level uniqueness and sensitivity review. |
| `docs/release/evidence/` | KEEP — HISTORICAL / REVIEW REQUIRED | May contain unique exact-SHA or diligence evidence; not current authority. |
| `docs/release/live-audit/` | KEEP — HISTORICAL / REVIEW REQUIRED | Generated/runtime history; verify sensitive data before archive or deletion. |
| `docs/completion/` | CONSOLIDATE / REVIEW REQUIRED | Mixed-age completion claims; must not override current freeze authority. |
| `docs/status/` | REVIEW REQUIRED | Ignored for new generation, but any committed records require file-level classification. |
| `docs/repo-cleanup/` | KEEP — HISTORICAL | Cleanup records only; not release authority. |
| `docs/ops/` | CONSOLIDATE / REVIEW REQUIRED | Legacy operations material; no new documents should be added. |
| `solomon_governance_c1/governance/c1/runtime/audit_pack/` | RESTRICT — SENSITIVE | Historical private-key exposure boundary; not a distributable clean artifact. |

## Generated and local noise controls verified

`.gitignore` excludes logs, local secrets, environment files, certificates/private keys, virtual environments, dependency/build output, local databases, scratch files, test output, screenshots outside controlled locations, worktrees, ZIP bundles, Azure evidence, war-room output, and most generated audit artifacts.

These ignore rules prevent new local noise but do not prove that previously committed material is absent from history or retained refs.

The following root-level generated files named by `.gitignore` were checked directly and were not present on `main`:

- `workflow-inventory-report.json`
- `release-scorecard.json`
- `workflow-permissions-audit.json`

Repository code search also returned no references to the removed workflow filenames:

- `p0-go-readiness.yml`
- `live-runtime-certification.yml`

Because private-repository code and branch searches returned incomplete or empty results and the local authenticated `gh` environment failed before inventory could run, those negative results are recorded as limited verification, not proof of repository-wide absence.

## Items not deleted without further proof

1. Branches and tags: complete ref inventory and unique-commit comparison were not available through the current connector.
2. GitHub releases and release assets: no complete reliable inventory/deletion interface was available.
3. GitHub Actions historical artifacts: may contain unique evidence or sensitive pre-remediation material; deletion requires run-by-run inventory.
4. Broad documentation directories: directory-level deletion would risk removing unique provenance, security, contractual, or diligence records.
5. Gauntlet support modules under `scripts/execution/modules/`: require file-level dependency and reuse inspection before deletion.
6. Historical Ed25519 material: must remain restricted until key retirement and all-ref history remediation are separately verified.
7. Full tracked-file, duplicate-content, dead-code, dependency, large-object, and broken-link census: requires a successful authenticated full clone or equivalent complete tree API.

## Current noise-control rule

No file, process, branch, tag, artifact, or document may be deleted solely because it is old or verbose. Deletion requires evidence that it is:

1. non-authoritative;
2. not uniquely referenced;
3. not required for security, legal, provenance, recovery, or diligence purposes;
4. not the only copy of a decision or operational fact; and
5. not part of the unresolved historical-key evidence boundary.

## Current result

- Open issues: 0
- Open pull requests: 0
- Automatic P0/runtime certification workflows: removed
- Automated closed-issue evidence publisher: removed
- Unreferenced P0 release orchestrators: removed
- Known ignored root reports checked: absent
- Removed workflow-name references checked through repository search: none returned
- Canonical freeze authority: current
- Production authorization: not granted
- History remediation: not verified complete
- Full authenticated hygiene census: not yet technically available in this environment
