# CROWN DevSecOps Maturity Assessment and Improvement Register

**Status:** PROVISIONAL / SOURCE AND DOCUMENT REVIEW ONLY / NO OPERATIONAL CERTIFICATION  
**Date:** 2026-10-09  
**Repository snapshot:** `4ba450a8c25b1cb1bf6caa5999a486e65b38ea7b` (historical identity; recheck exact head for subsequent release claims)  
**Machine-readable source:** [assessment register](../../config/security/devsecops_maturity_assessment.json)  
**Control validator:** `python tools/ci/verify_devsecops_maturity.py`  
**Related assurance:** [SOC 2 evidence register](../compliance/SOC2_EVIDENCE_REGISTER_20261008.md); [source vs. production release authority](../CURRENT_RELEASE_STATUS.md)

## Purpose and boundary

Assess six complementary DevSecOps competencies: culture, plan/develop, build/test, release/deploy, operate, and observe/respond. The progression labels are Beginner, Intermediate, Advanced, and Expert. A fifth label, **Not assessed**, means no defensible maturity level has yet been assigned. These are **planning assessments**, not a compliance certification or external assessment. A repository-controlled file or a workflow definition never proves live operation.

The paper's central method is assess current state, select an appropriate target, and close the weakest proven gap incrementally. CROWN targets **Advanced practices where justified by operational needs**, not automatic Expert classification, and is not committing to a subscription or release-cadence target merely to raise a score. A safe, controlled release may be slower than multiple daily releases.

## Current evidence-limited scorecard

| Competency | Provisional level | Repository evidence classification | Operational proof | Tracked items |
| --- | --- | --- | --- | --- |
| Culture and accountability | Not assessed | DESIGNED | Not verified | #173 |
| Plan and develop | Intermediate (provisional) | DESIGNED | Not verified | #173 |
| Build and test | Intermediate (provisional) | IMPLEMENTED_SOURCE | Not verified | #104, #173 |
| Release and deploy | Intermediate (provisional) | IMPLEMENTED_SOURCE | Not verified | #173 |
| Operate and recover | Not assessed | DESIGNED | Not verified | #173 |
| Observe and respond | Not assessed | DESIGNED | Not verified | #173 |

**Overall maturity level: NOT ASSIGNED.** An arithmetic average would be misleading while operation and observation remain unassessed. The level shown for a competency is a diagnostic judgment from inspected repository evidence, not a verified capability rating. Prior dated tests at a prior SHA do not automatically verify the latest head.

## Domain-by-domain corrective work

### 1. Culture and accountability

- **Accountability:** Founder / product owner (role proposed; actual delegated coverage not certified)
- **Observed source/documentation:** Written accountability requirements exist; operational owner/deputy assignment, acknowledgments and cadence are not yet evidenced.
- **Evidence paths:** `docs/compliance/SECURITY_OPERATING_POLICY.md`; `docs/engineering/ENGINEERING_ACCOUNTABILITY_POLICY.md`
- **Gap:** No dated adopted security governance records or independently demonstrated alternate technical coverage.
- **Next acceptance proof:** Record management adoption, named primary and deputy, monthly evidence-review minutes and continuity exercise.
- **Tracking:** [Issue #173](https://github.com/Arete0920/Crown-CSMS/issues/173)

### 2. Plan and develop

- **Accountability:** Founder / engineering lead (role proposed; actual delegated coverage not certified)
- **Observed source/documentation:** A scored draft risk register, technical governance, and code-review processes exist; current assessment is not approved.
- **Evidence paths:** `docs/compliance/SOC2_RISK_ASSESSMENT_20261008.md`; `docs/compliance/SECURITY_OPERATING_POLICY.md`; `docs/engineering/REPOSITORY_WORKFLOW.md`
- **Gap:** No repeatable approved threat-model evidence for all material new features or signed-off residual-risk decisions.
- **Next acceptance proof:** Approve baseline risk register, attach threat model and mitigation decision to the next high-risk feature, and review technical debt monthly.
- **Tracking:** [Issue #173](https://github.com/Arete0920/Crown-CSMS/issues/173)

### 3. Build and test

- **Accountability:** Engineering / security (role proposed; actual delegated coverage not certified)
- **Observed source/documentation:** Automated tests and security scanning run in repository workflows; historical SHA-bound tests passed on 2026-10-08.
- **Evidence paths:** `.github/workflows/tests.yml`; `.github/workflows/codeql.yml`; `.github/workflows/dependency-audit.yml`; `.github/workflows/secret-scan.yml`; `.github/workflows/tenant-isolation-gate.yml`
- **Gap:** Individual test-to-control mapping, full dynamic scan scope, supply-chain artifact provenance, and latest-head acceptance require evidence.
- **Next acceptance proof:** Retain current exact-head run/job receipts, map critical negative authorization tests to objectives, and verify build artifacts and signing.
- **Tracking:** [Issue #104](https://github.com/Arete0920/Crown-CSMS/issues/104); [Issue #173](https://github.com/Arete0920/Crown-CSMS/issues/173)

### 4. Release and deploy

- **Accountability:** Founder / release administrator (role proposed; actual delegated coverage not certified)
- **Observed source/documentation:** Repo release authority and operational-certification workflow definitions exist; production admission requires separate evidence.
- **Evidence paths:** `docs/CURRENT_RELEASE_STATUS.md`; `.github/workflows/crown-release-authority-gates.yml`; `.github/workflows/production-certification-evidence.yml`
- **Gap:** Actual deployed revision, rollback, active resource inventory, and environment security validation remain unverified.
- **Next acceptance proof:** For the actual selected environment, capture deployment identity, migration/rollback rehearsal, approval and exact-source run receipts.
- **Tracking:** [Issue #173](https://github.com/Arete0920/Crown-CSMS/issues/173)

### 5. Operate and recover

- **Accountability:** Founder / Azure administrator (role proposed; actual delegated coverage not certified)
- **Observed source/documentation:** Runbooks and infrastructure verification workflows exist, but their existence does not prove current Azure or backup operation.
- **Evidence paths:** `docs/compliance/BACKUP_RESTORE_POLICY.md`; `docs/operations/AZURE_CLASSROOM_FIRST_RELEASE.md`; `.github/workflows/isolated-postgres-restore-drill.yml`; `.github/workflows/azure-drift-watchdog.yml`
- **Gap:** No verified live hosting inventory, current operational backups, measured RTO/RPO, responder deputy, or recovery approval.
- **Next acceptance proof:** After Azure access is established, inventory actual assets, run a measured isolated restore from an operational backup, and sign off RTO/RPO.
- **Tracking:** [Issue #173](https://github.com/Arete0920/Crown-CSMS/issues/173)

### 6. Observe and respond

- **Accountability:** Founder / incident commander (role proposed; actual delegated coverage not certified)
- **Observed source/documentation:** Incident policy and manually dispatched health-watch workflow exist; alert delivery and live SLOs have not been verified.
- **Evidence paths:** `docs/compliance/INCIDENT_RESPONSE_POLICY.md`; `docs/operations/CROWN_OBSERVABILITY_AND_INCIDENT_READINESS_20260529.md`; `.github/workflows/prod-health-watch.yml`
- **Gap:** No demonstrated production telemetry population, tested paging/alert path, measured MTTD/MTTR or completed participant tabletop.
- **Next acceptance proof:** Define user-journey SLOs, run end-to-end alert test and participant tabletop, retain sanitized incident and postmortem receipts.
- **Tracking:** [Issue #173](https://github.com/Arete0920/Crown-CSMS/issues/173)

## Priority and completion sequence

1. **P0 — Credential trust boundary:** resolve the separately tracked [history/key-retirement blocker #104](https://github.com/Arete0920/Crown-CSMS/issues/104). No source-only validator can authorize key rotation, rewrite shared history or attest secret retirement.
2. **P0 — Operational authorization:** complete management decisions, primary/deputy assignments and actual hosting inventory in [#173](https://github.com/Arete0920/Crown-CSMS/issues/173). Preserve approval identity and sensitive credentials outside the public repository.
3. **P1 — Environment-backed tests:** retain exact deployed-SHA proof, negative access tests, central logs and actual alert delivery. Do not convert a manual workflow definition into a claim of monitored production service.
4. **P1 — Recovery and response:** restore from the real approved backup in isolation; measure RTO and RPO; perform a staffed incident tabletop with dated closure actions.
5. **P2 — Continuous improvement:** monthly evidence and risk review, quarterly reassessment, explicit acceptance criteria and issue closure only against completed receipts.

## Enforcement and evidence rules

- A small, standard-library-only check validates that all six competencies are present, named evidence files exist, and every unverified operational condition remains explicitly labeled. It runs in the existing Repository Policy workflow on pull requests; it **does not run cloud probes or consume credentials**.
- The guard fails if maturity registry entries are deleted, evidence paths disappear, a level is asserted as verified without separately developed proof controls, or an operational certification is silently set to true. These are registry-integrity checks, **not proof that the underlying control is effective**.
- Every operational control requires a timestamp, selected environment, tested control objective, operator, independent reviewer where mandated, sanitized result, and restricted-location evidence reference. External legal/CPA reviews cannot be self-certified by source CI.
- On failed checks, repair the defect and rerun against the exact proposed commit. Do not waive existing release or security gates to make this assessment green.
- Do not schedule live Azure watchdogs, production health polls or simulated recovery probes against non-existent/unverified resources. Current operational workflows remain manual and fail closed.

## Ongoing operating metrics after an environment exists

Track monthly: applicable release-gate pass rate at exact SHA; regressions and escaped defects; high/critical finding age against approved SLA; change failure and rollback rate; measured restore duration and data-loss window; alert delivery/acknowledgment time; mean time to detect (MTTD), mean time to restore (MTTR); and school-critical journey SLO/error budgets. Mark each metric **NOT MEASURED** until an owner, system of record, observation window and receipts exist. Do not invent baselines, targets or outcomes.

## Closure contract

A competency is only reassessed after its listed proof is linked to a specific date, owner, environment, outcome and review. Resolving a tracking issue requires its own acceptance criteria; an approved document, PR merge or clean static scan cannot close a missing operational/independent assurance requirement.
