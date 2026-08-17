# CROWN Release Notes

## Current Crown-CSMS turnover source — 2026-08-17

- **Repository:** `Arete-Advisory-Group/Crown-CSMS`
- **Handoff-refresh base `main`:** `f9bf6b4143e707f93ec8d6ce319327ddc7d3e2a0`
- **Security hardening:** PRs #97 and #98 merged
- **Current control:** Crown-CSMS issue #14 and `docs/CURRENT_RELEASE_STATUS.md`

This source identity is the current repository authority for the turnover sequence. It is **not automatically a deployed production identity**. Deployment/runtime, immutable rollback, operational restore, monitoring, successor account control, and final acceptance remain separate evidence gates.

### Current security/repository progress

- persistent RBAC and tenant-integrity hardening merged across Transportation, Athletics, Spiritual Life, Student Records, Student Care, and Communications;
- duplicate unsafe Communications mutation routes retired from production routing;
- open P0 security issues reconciled where merged evidence supported closure;
- remaining roadmap/architecture/process issues reclassified so they are not presented as unresolved production P0 defects;
- external payment processing remains disabled and fail closed.

## Historical predecessor/bounded production evidence — 2026-08-08

The following records are preserved as historical predecessor/provenance evidence and must not be represented as current Crown-CSMS turnover authority:

- source `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`;
- immutable tag `prod-deploy-20260808-ce12c95`;
- production deployment run `31287503791`;
- dashboard deployment/certification run `31289219093`;
- dashboard source `a3f89db677857a220b322b3f1bf094b3fdef3fa2`;
- prior bounded Heritage/persona and runtime evidence recorded in predecessor release material.

That historical evidence remains useful provenance. It does not establish current Crown-CSMS deployment, recovery readiness, universal persona coverage, or completed owner turnover.

## Release identity rule

Later `main` commits never inherit a prior deployment or certification automatically. A production release requires one exact selected source identity and corresponding build, deployment, runtime-health, monitoring, rollback/recovery, and authorization evidence appropriate to the release.

## Historical milestones

### `crown-0.3.1-prod-pipeline-fix` — 2026-01-27
Historical pipeline milestone at `a1c4c42a381e03587c784bd995ec8fd6c33aeee9`.

### `crown-0.3.0-spine-complete` — 2026-01-27
Historical tenant-isolation and CI foundation at `340c7e3fbb882eb4886fbfbbe8e648f3866e5178`.

The immutable mapping for historical tags is `docs/RELEASE_TAGS.json`.

## Authority rule

If a historical release note conflicts with `docs/CURRENT_RELEASE_STATUS.md`, Crown-CSMS issue #14, exact current repository identity, or verified runtime evidence, the current Crown-CSMS authority wins.
