# CROWN Repository Maintenance Candidates

**Status:** Controlled supporting inventory for review; not a deletion order, release decision, or replacement for repository authority.
**Evidence snapshot:** `main` at `79d490946a6549c9aef4f11cc0f77727eaa0ecce` on October 19, 2026. Recheck exact GitHub source, open work, and consumers before acting.
**Owner:** CROWN engineering, with acceptance governed by [Repository Workflow](REPOSITORY_WORKFLOW.md).

This is a bounded first-pass classification of concrete maintenance candidates. Git tree enumeration establishes that a path exists; it does not prove that a file is unused. Current authority remains the [Canonical Document Index](../canonical/CANONICAL_DOCUMENT_INDEX.md), [Current Release Status](../CURRENT_RELEASE_STATUS.md), and [Repository Manifest](../canonical/REPOSITORY_MANIFEST.md).

## Immediately confirmed documentation defects

| Path | Verified evidence | Disposition in the associated documentation change |
| --- | --- | --- |
| `docs/LOCAL_QUICKSTART.md` | Claimed Node.js 20; current `.nvmrc` specifies 22.23.3. Named an outdated sales-package source SHA; the installer defines a different pin. | Align supported toolchain and direct users to the package manifest and current installer pin. |
| `docs/engineering/ONBOARDING_GUIDE.md` | Suggested `npm install` and an absent `local.secrets.ps1.example`; referenced missing `FILE_INDEX.md` and `INTEGRATION_GUIDE.md`. The file is required by `scripts/verification/verify_day1_foundation_truth.sh`. | Replace stale duplicated setup blocks with current canonical links; retain the file and its `DEV_SETUP.md` reference. |
| `scripts/README.md` | Referenced nonexistent `scripts/ops/root_legacy/`; `scripts/ops/` exists. | Correct the navigation; retain secure-operations guidance. |
| `docs/DEPRECATION_AUDIT.md` | January 2026 workflow/version observations are not current execution authority. | Mark the retained report historical; do not silently rewrite its prior findings. |

## Candidates requiring consumer or retention proof

| Candidate | Observed source / known consumer | Proposed disposition | Evidence required before changing |
| --- | --- | --- | --- |
| `frontend/src/` | 83 tracked files outside the canonical `frontend/dashboards/` app. A historical release proof refers to this tree; active runtime imports have not been comprehensively assessed. | Review for migration or retirement, **not** immediate deletion. | Frontend bundler entrypoints, imports, wizard/route registrations, packaging, tests, build, and visual/role verification. |
| `backend/quarantine_old_tests/` | Five test files. `.coveragerc`, a surface-discovery script, and an active test refer to the quarantine path. | Preserve pending test-equivalence assessment. | Test collection, current replacement coverage, references and any policy exclusions; confirm no regression gap. |
| `backend/curriculum/` and `backend/curricula/` | Both are present Django application trees with migrations; current settings register both. | Retain and document ownership before any consolidation. | Dependency, model/foreign-key, migration-history, API, import and data-ownership analysis with reversible transition design. Never cosmetically rename an applied app label. |
| `docs/canon/`, `docs/canons/`, `docs/canonical/` | Three distinct directories (5, 3, and 3 tracked files). Only `docs/canonical/` houses the current authority index. | Classify, link and potentially relocate controlled support; no bulk merge. | Canonical-index authority, citation and runtime reference graph, unique policy content, preserved Git references. |
| `docs/release/` | 125 tracked documents, many dated or provenance-oriented. | Separate historical records from active procedures. | Current canonical index, release/CI references, retained evidence obligations, link and archive checks. |
| `docs/Crown_Master_Binder/` | 44 tracked files under a standalone binder hierarchy. | Review for duplicate navigation versus unique retained requirements. | Compare to controlling architecture, operations and product records; verify intended readership and references. |
| `docs/51x51/` | 31 tracked files. Current consumer role not established in this review. | Investigate; retain until ownership is established. | References from UI, help/source corpus, scripts, tests and packaging. |
| `docs/demo-proof/pp-003/proof/RUN1_PROOF.log`, `RUN2_PROOF.log` | Both logs are tracked even though `.gitignore` excludes generated `docs/demo-proof/**/proof/` output. | Assess controlled artifact retention versus source-tree removal. | Hashes, provenance, reference search, retention schedule and immutable artifact availability; do not discard unique acceptance evidence. |
| Root-level `scripts/manual_*.py` | Several stand-alone manual diagnostic helpers remain alongside active automation. | Classify as active, reference-only, or retired. | Exact invocation references in workflows, runbooks, tests and supported maintenance procedures. |
| `solomon_governance_c1/` | 171 tracked files, including governance and verification material. | Preserve until independently reviewed; not a general cleanup target. | Frozen digest references, runtime imports, candidate-source lineage, retention and operational gates. |
| `solomon-source-corpus/` | Source metadata and corpus manifests are tracked. | Retain subject to provenance review. | Consumer inventory, license and content-use authority, integrity and retention requirements. |
| `.gitleaksignore` | Hundreds of nonempty lines of fingerprint-specific exclusions and adjudication notes. | Separate security-governed review only. | Each exclusion's finding type, exact fingerprint, recorded false-positive rationale and owner approval; never remove or broaden exclusions mechanically. |
| `Start-Heritage.cmd`, `Start-Heritage-Demo.cmd` and their launchers | The ZIP sales starter intentionally pins a source revision; the current-checkout launcher runs the checked-out revision. The package has contract tests. | Keep distinct launch modes; simplify operator instructions instead of deleting an entrypoint. | `scripts/demo/package_heritage_sales.py`, `backend/tests/test_heritage_sales_package.py`, Windows rehearsal, exact bundle manifest and SHA. |
| `scripts/demo/start_heritage_local.py` | Launcher accepts Node.js 22.12+; `frontend/dashboards/package.json` requires at least 22.22.2 on the 22.x line. | Align version admission with the supported frontend engines in a separate code PR. | Focused launcher version tests, supported Windows demo rehearsal and package install/build proof. |
| `.github/workflows/deploy-prod.yml` and `deploy-prod-dispatch.yml` | Two substantial deployment entrypoints with similar build/candidate stages and distinct dispatch/authorization semantics. | Investigate shared reusable implementation; do not remove either trigger. | Job-by-job permission and environment diff, immutable identity, schema gate, approvals, negative-path, rollback and deployment parity. |
| `.github/workflows/ci.yml`, `tests.yml`, `pytest-gate.yml`, `backend-gate.yml`, `tenant-isolation-gate.yml` | Multiple test/install workflows; some have distinct required gates and concurrency rules. | Review duplicate setup and unnecessary execution only after mapping terminal checks. | Required branch-protection status contexts, workflow triggers, test coverage, retained artifacts, cancellation rules and equivalence runs. |

## Admission standard for retirement

1. Record the current default-branch SHA, all open PRs affecting the path, and its owner.
2. Search tracked references, dynamic entrypoints, imports, management commands, tests, deployment workflows, and documentation links. A missing text match is not sufficient proof of no consumer.
3. Identify the replacement authority or explain why the file has no present purpose; retain unique contractual, historical, legal, audit and migration information.
4. For code, migrations, security and release surfaces, obtain risk-specific acceptance, focused and broad verification, rollback, and an explicit human decision.
5. Keep independently reversible changes in narrow PRs. Do not retire tests by reducing governed coverage, or simplify CI by making a required status disappear.
6. Confirm merged source at the exact accepted revision. Any deployment, credential retirement, restore or operational claim requires separate environment proof.

**Excluded from routine cleanup:** credential retirement and history remediation under issues [#269](https://github.com/Arete0920/Crown-CSMS/issues/269) and [#104](https://github.com/Arete0920/Crown-CSMS/issues/104), and refresh-token security work under [#350](https://github.com/Arete0920/Crown-CSMS/issues/350). These require their own approved security and operational procedures.
